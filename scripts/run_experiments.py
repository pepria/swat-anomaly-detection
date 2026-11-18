"""Train + evaluate all detectors on both setups.

    python scripts/run_experiments.py            # everything (~1 h on 4 CPU cores)
    python scripts/run_experiments.py a12        # only the 2026 setup
    python scripts/run_experiments.py s2015      # only the 2015 setup

Results: outputs/runs/<run>/metrics.csv, combined in outputs/metrics_all.csv
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402

from swatad import config as C  # noqa: E402
from swatad.pipeline import run  # noqa: E402

which = sys.argv[1:] or ["a12", "s2015"]
results = []
if "a12" in which:
    for train_sets in ("A11", "A11+A10"):
        for drop_ait in (True, False):
            results.append(run("a12", train_sets, drop_ait))
if "s2015" in which:
    # 2015 is ~10x larger than A11: subsample training data harder and window steps
    # (training rows are subsampled; ~15 min for both feature sets x 3 seeds on 4 cores)
    kw = {"AE": {"sub_every": 10}, "WinAE": {"train_step": 30, "score_step": 5},
          "LSTM-AE": {"train_step": 30, "score_step": 5, "epochs": 25}}
    for drop_ait in (True, False):
        results.append(run("s2015", "normal", drop_ait, model_kwargs=kw, seeds=(0, 1, 2),
                           save_contrib=False))

# merge with any previous runs
allp = C.OUT_DIR / "metrics_all.csv"
new = pd.concat(results)
if allp.exists():
    old = pd.read_csv(allp)
    old = old[~old["run"].isin(new["run"].unique())]
    new = pd.concat([old, new])
new.to_csv(allp, index=False)
print("saved", allp)
