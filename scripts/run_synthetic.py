"""Synthetic anomaly injection on the clean normal part of A12 (10:35-13:20).

Models are trained exactly as in the main A12 setup and calibrated on A12
09:30-10:30. Several random realisations are injected; for each injection we
record whether it was detected (alarm onset within [start, end + 120 s]), the
delay, and whether the injected tag is among the top-k contributing features
(root-cause localisation, used to check the explanation layer).

    python scripts/run_synthetic.py [train_sets] [noAIT|all]
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from swatad import config as C  # noqa: E402
from swatad.evaluate import alarm_segments  # noqa: E402
from swatad.features import tag_kind  # noqa: E402
from swatad.inject import inject  # noqa: E402
from swatad.pipeline import fit_and_calibrate, score_with  # noqa: E402

train_sets = sys.argv[1] if len(sys.argv) > 1 else "A11+A10"
drop_ait = (sys.argv[2] if len(sys.argv) > 2 else "noAIT") == "noAIT"
REALISATIONS = (0, 1, 2)
TOL = pd.Timedelta(seconds=120)

C.ensure_dirs()
out = C.OUT_DIR / "synthetic"
out.mkdir(exist_ok=True)
F = fit_and_calibrate("a12", train_sets, drop_ait)
S, fs, rules = F["setup"], F["fs"], F["rules"]
base = S.test[S.test.index.strftime("%H:%M:%S") < "13:20:00"].copy()
train_v = S.train
sensors = [c for c in fs.cols if tag_kind(c) == "sensor"]
actuators = [c for c in fs.cols if tag_kind(c) == "actuator"]
sigma = {c: float(train_v[c].std()) for c in fs.cols}

rows, all_inj = [], []
for r in REALISATIONS:
    df, inj = inject(base, ("10:35:00", "13:15:00"), sensors, actuators, sigma, seed=r)
    all_inj += inj
    scored = score_with(F, df)
    rule_alarm, _ = rules.alarm(df)
    em = df.index.strftime("%H:%M:%S") >= "10:30:00"
    idx = df.index[em]
    for name, (s, c, thr) in scored.items():
        for variant, alarm in (("model", s > thr), ("model+rules", (s > thr) | rule_alarm)):
            a = alarm[em]
            segs = alarm_segments(a, idx)
            cc = c[em]
            for j in inj:
                win = (idx >= j["start"]) & (idx <= j["end"] + TOL)
                on = segs[(segs.start >= j["start"]) & (segs.start <= j["end"] + TOL)]
                det = len(on) > 0
                pts = win & a if (win & a).any() else win
                order = np.argsort(-np.nan_to_num(cc[pts].astype("float32").mean(0)))
                rank = int(np.flatnonzero(np.array(fs.cols)[order] == j["tag"])[0]) + 1
                rows.append({"realisation": r, "model": name, "variant": variant, **j,
                             "detected": det,
                             "delay_s": (on.start.iloc[0] - j["start"]).total_seconds() if det else np.nan,
                             "tag_rank": rank})
            # false alarm events in the injected region that do not touch any injection
            fa = 0
            for _, sg in segs.iterrows():
                if not any((sg.start <= j["end"] + TOL) and (sg.end >= j["start"]) for j in inj):
                    fa += 1
            rows.append({"realisation": r, "model": name, "variant": variant, "type": "_false_alarms",
                         "detected": fa})

res = pd.DataFrame(rows)
res.to_csv(out / "synthetic_detail.csv", index=False)
det = res[res.type != "_false_alarms"]
summary = det.groupby(["model", "variant", "type"]).agg(
    n=("detected", "size"), recall=("detected", "mean"), median_delay_s=("delay_s", "median"),
    hit_at_1=("tag_rank", lambda x: float((x <= 1).mean())),
    hit_at_3=("tag_rank", lambda x: float((x <= 3).mean()))).reset_index()
overall = det.groupby(["model", "variant"]).agg(
    n=("detected", "size"), recall=("detected", "mean"), median_delay_s=("delay_s", "median"),
    hit_at_1=("tag_rank", lambda x: float((x <= 1).mean())),
    hit_at_3=("tag_rank", lambda x: float((x <= 3).mean()))).reset_index()
fa = res[res.type == "_false_alarms"].groupby(["model", "variant"])["detected"].sum().rename("false_alarm_events")
overall = overall.merge(fa, on=["model", "variant"])
overall["type"] = "ALL"
summary = pd.concat([summary, overall])
summary.to_csv(out / "synthetic_summary.csv", index=False)
pd.DataFrame(all_inj).to_csv(out / "injections.csv", index=False)
with open(out / "meta.json", "w") as f:
    json.dump({"train_sets": train_sets, "drop_ait": drop_ait, "realisations": list(REALISATIONS),
               "n_injections": len(all_inj)}, f, indent=1)
pv = summary[summary.variant == "model"].pivot(index="type", columns="model", values="recall").round(2)
print(pv.to_string())
print(overall.round(3).to_string())
