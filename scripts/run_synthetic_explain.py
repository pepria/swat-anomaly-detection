"""Evaluate the explanation layer on synthetic injections (known root-cause tag and type).

Same setup as run_synthetic.py (injections into the clean part of A12), but instead of only
checking detection and tag ranking, every alarm event is exported to the anomaly-event JSON and
explained, and the explanation is checked against what was injected:

* tag_top3            the injected tag is among the 3 strongest model contributors
* tag_top3_or_rules   ... or among the new rule violations
* category_ok         the signature category is one of the acceptable categories for the type
* pattern_ok          the retrieved generic pattern (03_attack_and_fault_patterns) fits the type
* confidence          calibrated vs raw confidence against correctness

    python scripts/run_synthetic_explain.py [train_sets] [noAIT|all] [models, comma separated] [--stuck-rule SECONDS]

``--stuck-rule 120`` enables the optional frozen-sensor rule; results then go to outputs/synthetic_explain_stuck/.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from swatad import config as C  # noqa: E402
from swatad.events import EventExporter  # noqa: E402
from swatad.features import tag_kind  # noqa: E402
from swatad.inject import inject  # noqa: E402
from swatad.persist import save_run_state  # noqa: E402
from swatad.pipeline import fit_and_calibrate, score_with, valid_mask  # noqa: E402
from swatad.rag.explainer import Explainer  # noqa: E402

args = sys.argv[1:]
stuck_s = None
if "--stuck-rule" in args:
    i = args.index("--stuck-rule")
    stuck_s = int(args[i + 1])
    del args[i:i + 2]
train_sets = args[0] if len(args) > 0 else "A11+A10"
drop_ait = (args[1] if len(args) > 1 else "noAIT") == "noAIT"
MODELS = tuple((args[2] if len(args) > 2 else "AE,WinAE").split(","))
REALISATIONS = (0, 1, 2, 3, 4)
TOL = pd.Timedelta(seconds=120)

# Categories that count as a reasonable reading of each injection type (my judgement, see report).
ACCEPT = {
    "spike": {"out_of_range_excursion", "spoof_out_of_range", "oscillation"},
    "bias": {"out_of_range_excursion", "spoof_out_of_range", "drift_or_inrange"},
    "drift": {"drift_or_inrange", "out_of_range_excursion"},
    "noise": {"oscillation", "drift_or_inrange"},
    "stuck": {"frozen_sensor", "spoof_out_of_range", "drift_or_inrange", "multivariate"},
    "replay": {"multivariate", "drift_or_inrange"},
    "actuator_flip": {"actuator_manipulation", "standby_activation"},
}
# keywords of the knowledge-base pattern titles that fit each type
PATTERN = {
    "spike": ["spike"], "bias": ["out-of-range constant", "within the normal range"],
    "drift": ["drift"], "noise": ["noise"], "stuck": ["stuck"], "replay": ["replay"],
    "actuator_flip": ["actuator manipulation", "standby"],
}

C.ensure_dirs()
out = C.OUT_DIR / ("synthetic_explain_stuck" if stuck_s else "synthetic_explain")
out.mkdir(exist_ok=True)
F = fit_and_calibrate("a12", train_sets, drop_ait, models=MODELS,
                      rule_kwargs={"stuck_s": stuck_s} if stuck_s else None)
S, fs, rules = F["setup"], F["fs"], F["rules"]
base = S.test[S.test.index.strftime("%H:%M:%S") < "13:20:00"].copy()
train_v = S.train[valid_mask(S.train)]
sensors = [c for c in fs.cols if tag_kind(c) == "sensor"]
actuators = [c for c in fs.cols if tag_kind(c) == "actuator"]
sigma = {c: float(train_v[c].std()) for c in fs.cols}
E = Explainer(backend="template")
title = {c.chunk_id: c.title.lower() for c in E.retriever.chunks}

rows = []
for r in REALISATIONS:
    df, inj = inject(base, ("10:35:00", "13:15:00"), sensors, actuators, sigma, seed=r)
    scored = score_with(F, df)
    rule_alarm, hits = rules.alarm(df)
    em = df.index.strftime("%H:%M:%S") >= "10:30:00"
    run = out / f"run_r{r}"
    run.mkdir(exist_ok=True)
    sc = pd.DataFrame({n: s for n, (s, c, thr) in scored.items()}, index=df.index)
    sc["_label"], sc["_attack_id"] = df["_label"].values, df["_attack_id"].values
    sc["_rule_any"], sc["_eval"] = rule_alarm, em
    sc.to_parquet(run / "scores.parquet")
    hits.to_parquet(run / "rule_hits.parquet")
    for n, (s, c, thr) in scored.items():
        np.save(run / f"contrib_{n}.npy", np.clip(c, 0, 6e4).astype("float16"))
    json.dump({"setup": f"synthetic_r{r}", "thresholds": {n: {"calib": float(v[2])} for n, v in scored.items()}},
              open(run / "meta.json", "w"))
    save_run_state(run, fs, rules)
    gt = pd.DataFrame([{"event_id": j["inj_id"], "name": j["description"], "targets": j["tag"],
                        "start": j["start"], "end": j["end"], "type": j["type"], "tag": j["tag"]} for j in inj])
    exp = EventExporter(run, df, train_v, gt)
    for model in MODELS:
        events = exp.export(model, use_rules=True)
        used = set()
        for ev in events:
            ex = E.explain(ev)
            t0 = pd.Timestamp(ev["start"])
            m = [j for j in inj if j["start"] <= t0 <= j["end"] + TOL]
            top = [t["tag"] for t in ev["top_contributors"]]
            new_rules = [h["tag"].split(".")[0] for h in ev["rule_hits"] if not h.get("already_active_before")]
            row = {"realisation": r, "model": model, "event_id": ev["event_id"], "start": ev["start"],
                   "category": ex["category"], "confidence_raw": ex["confidence_raw"],
                   "confidence": ex["confidence"], "top3": ",".join(top[:3])}
            if m and m[0]["inj_id"] in used:   # a second alarm event for the same injection
                row["kind"] = "duplicate"
                rows.append(row)
                continue
            if m:
                j = m[0]
                used.add(j["inj_id"])
                tag = j["tag"].split(".")[0]
                pats = [title[s] for s in ex["sources"] if s.startswith("03_")]
                row.update(kind="injection", inj_id=j["inj_id"], type=j["type"], tag=tag,
                           tag_rank1=bool(top and top[0] == tag), tag_top3=tag in top[:3],
                           tag_top3_or_rules=tag in top[:3] or tag in new_rules,
                           category_ok=ex["category"] in ACCEPT[j["type"]],
                           pattern_ok=any(k in p for p in pats[:1] for k in PATTERN[j["type"]]))
                row["fully_ok"] = row["tag_top3_or_rules"] and row["category_ok"]
            else:
                row["kind"] = "false_alarm"
            rows.append(row)
        for j in inj:                      # injections without any alarm event
            if j["inj_id"] not in used:
                rows.append({"realisation": r, "model": model, "kind": "missed", "inj_id": j["inj_id"],
                             "type": j["type"], "tag": j["tag"].split(".")[0]})

res = pd.DataFrame(rows)
res.to_csv(out / "detail.csv", index=False)
inj_rows = res[res.kind.isin(["injection", "missed"])].copy()
for c in ("tag_rank1", "tag_top3", "tag_top3_or_rules", "category_ok", "pattern_ok", "fully_ok"):
    inj_rows[c] = inj_rows[c].fillna(False).astype(float)
inj_rows["detected"] = (inj_rows.kind == "injection").astype(float)


def summarise(g):
    d = g[g.detected == 1]
    return pd.Series({"n": len(g), "detected": g.detected.mean(),
                      **{c: d[c].mean() if len(d) else np.nan for c in
                         ("tag_rank1", "tag_top3", "tag_top3_or_rules", "category_ok", "pattern_ok", "fully_ok")}})


summary = pd.concat([inj_rows.groupby(["model", "type"]).apply(summarise, include_groups=False).reset_index(),
                     inj_rows.groupby("model").apply(summarise, include_groups=False).reset_index().assign(type="ALL")])
summary.to_csv(out / "summary.csv", index=False)
print("== explanation quality on detected injections (rates among detected) ==")
print(summary.round(2).to_string(index=False))

ev = res[res.kind.isin(["injection", "false_alarm"])].copy()
ev["fully_ok"] = ev.fully_ok.fillna(False).astype(bool)
print("\n== confidence vs correctness (fully_ok = injected tag found and category acceptable) ==")
for col in ("confidence_raw", "confidence"):
    t = ev.groupby(["model", col]).agg(events=("fully_ok", "size"), injection=("kind", lambda x: (x == "injection").sum()),
                                       false_alarm=("kind", lambda x: (x == "false_alarm").sum()),
                                       fully_ok=("fully_ok", "mean"))
    print(f"\n-- {col}")
    print(t.round(2).to_string())
