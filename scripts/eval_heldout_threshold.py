"""How well does a threshold learnt on the training data transfer? In-sample vs held-out normal data.

The "train thr" variant of the main experiments takes the 99.5% quantile of the scores of the data the
models were fitted on. Fitted models score their own training data lower than new data, so that
threshold is too tight. Here a few contiguous blocks of the A10 recording are kept out of the training
and the threshold is taken on them. Three thresholds are compared on A12 (main configuration, A11+A10, noAIT):

* calibration  99.5% quantile on the normal calibration hour of A12 (what the project uses)
* in-sample    99.5% quantile on the training rows (as in the "train thr" rows of the main tables)
* held-out     99.5% quantile on the held-out training blocks (never seen during fitting)

    python scripts/eval_heldout_threshold.py [seeds, default 0,1,2]

Writes outputs/heldout_threshold/{detail.csv,summary.csv}. LSTM-AE is only run for the first seed.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from swatad import config as C  # noqa: E402
from swatad import data as D  # noqa: E402
from swatad.evaluate import full_report, smooth  # noqa: E402
from swatad.features import FeatureSpace  # noqa: E402
from swatad.models import MODELS  # noqa: E402
from swatad.pipeline import make_setup, train_scores, valid_mask  # noqa: E402

SEEDS = tuple(int(x) for x in (sys.argv[1] if len(sys.argv) > 1 else "0,1,2").split(","))
Q, BLOCK, BUFFER = 0.995, 14400, 600          # 4 h blocks, 10 min kept away from the fitted rows

S = make_setup("a12", "A11+A10")
vtr = valid_mask(S.train)
fs = FeatureSpace(drop_ait=True).fit(S.train[vtr])
Ztr, Zte = fs.transform(S.train), fs.transform(S.test)
n11 = len(D.load_a11())
starts = [int(n11 + f * (len(S.train) - n11 - BLOCK)) for f in (0.1, 0.35, 0.6, 0.85)]
hold = np.zeros(len(Ztr), bool)
for a in starts:
    hold[a:a + BLOCK] = True
buffered = hold.copy()
for a in starts:
    buffered[max(a - BUFFER, 0):a + BLOCK + BUFFER] = True
vfit = vtr & ~buffered
print(f"{int(vfit.sum())} rows for fitting, {int((vtr & hold).sum())} valid held-out rows in {len(starts)} blocks")

y, em, idx = S.test["_label"].values.astype(int), S.eval_mask, S.test.index[S.eval_mask]
clean = idx < S.events.start.min()
rows = []
for name in ("IForest", "GMM", "AE", "WinAE", "LSTM-AE"):
    for seed in SEEDS[:1] if name == "LSTM-AE" else SEEDS:
        det = MODELS[name](seed=C.SEED + seed).fit(Ztr, vfit)
        w = 10 if name in ("IForest", "GMM", "AE") else 5
        s_te = smooth(det.score(Zte)[0], w)
        thr = {"calibration": float(np.quantile(s_te[S.calib_mask], Q)),
               "in-sample": float(np.quantile(train_scores(det, Ztr, vfit, w)[0], Q))}
        held = []
        for a in starts:
            sl = slice(a, a + BLOCK)
            held.append(smooth(det.score(Ztr[sl])[0], w)[vtr[sl]])
        thr["held-out"] = float(np.quantile(np.concatenate(held), Q))
        for kind, th in thr.items():
            r = full_report(s_te[em], y[em], th, idx, S.events)
            rows.append({"model": name, "seed": seed, "threshold": kind, "value": th,
                         "fpr_clean": float((s_te[em][clean] > th).mean()),
                         "event_recall": r["event_recall"], "false_alarm_events": r["false_alarm_events"]})
        print(f"  {name} seed {seed}: " + ", ".join(f"{k} {v:.3g}" for k, v in thr.items()), flush=True)

out = C.OUT_DIR / "heldout_threshold"
out.mkdir(exist_ok=True)
df = pd.DataFrame(rows)
df.to_csv(out / "detail.csv", index=False)
summ = df.groupby(["model", "threshold"], sort=False).agg(
    fpr_clean=("fpr_clean", "mean"), false_alarm_events=("false_alarm_events", "mean"),
    event_recall=("event_recall", "mean"), seeds=("seed", "nunique")).round(3).reset_index()
summ.to_csv(out / "summary.csv", index=False)
print(summ.to_string(index=False))
