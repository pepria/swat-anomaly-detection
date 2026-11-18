"""Generate notebooks/01_walkthrough.ipynb (run with --execute to also execute it)."""
import sys
from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
cells = []
md = lambda s: cells.append(nbf.v4.new_markdown_cell(s))  # noqa: E731
code = lambda s: cells.append(nbf.v4.new_code_cell(s))  # noqa: E731

md("""# SWaT anomaly detection + explanation: walkthrough

This notebook walks through the pipeline on the main setup (train on **SWaT.A11 + A10**, test on
**SWaT.A12**, AIT water-quality analysers excluded). The heavy experiments (all models x 3 seeds,
SWaT 2015, synthetic injection) are run by the scripts in `scripts/`; here we reuse their outputs
and train one GMM live to show the API.""")
code("""import sys, json
from pathlib import Path
sys.path.insert(0, str(Path.cwd().parent))
import numpy as np, pandas as pd, matplotlib.pyplot as plt
from swatad import config as C, data as D
from swatad.pipeline import make_setup, valid_mask
from swatad.features import FeatureSpace
from swatad.rules import RuleMonitor
from swatad.models import GMMDet
from swatad.evaluate import smooth, full_report
pd.set_option('display.width', 200)""")
md("## 1. Data\nA11 (normal, Feb 2026), A10 (normal, Dec 2023), A12 (11 attacks, Mar 2026). "
   "Bookkeeping columns start with `_`.")
code("""S = make_setup('a12', 'A11+A10')
print('train', S.train.shape, ' test', S.test.shape)
S.events[['event_id', 'name', 'targets', 'start', 'end']]""")
md("## 2. Features, rules and a GMM\nThe feature space is fit on valid normal rows only (no warm-up, "
   "no comms gaps). Rules are calibrated on A12 09:30-10:30, which disables drifted tags.")
code("""v = valid_mask(S.train)
fs = FeatureSpace(drop_ait=True).fit(S.train[v])
rules = RuleMonitor().fit(S.train[v]).calibrate(S.calib_df[S.calib_mask])
print(len(fs.cols), 'model features; rules disabled after calibration:', rules.disabled)
gmm = GMMDet().fit(fs.transform(S.train), v)
print('GMM components (BIC):', gmm.k)""")
code("""s, contrib = gmm.score(fs.transform(S.test))
s = smooth(s, 10)
thr = np.quantile(s[S.calib_mask], 0.995)
em = S.eval_mask
rep = full_report(s[em], S.test['_label'].values[em], thr, S.test.index[em], S.events)
{k: (round(v, 3) if isinstance(v, float) else v) for k, v in rep.items()}""")
code("""fig, ax = plt.subplots(figsize=(11, 3))
ax.semilogy(S.test.index, s / thr, lw=0.7, color='#eb6834'); ax.axhline(1, color='k', ls='--', lw=0.8)
for _, a in S.events.iterrows(): ax.axvspan(a.start, a.end, color='#e34948', alpha=0.15, lw=0)
ax.set_ylabel('GMM score / threshold'); ax.set_title('A12, red = attacks')""")
md("## 3. Results of the full experiment grid (from `scripts/run_experiments.py`)")
code("""m = pd.read_csv(C.OUT_DIR / 'metrics_all.csv')
cols = ['auc_roc', 'auc_pr', 'f1', 'fpr_clean', 'event_recall', 'event_precision', 'mean_delay_s']
(m[m.variant.isin(['model', 'model+rules', 'rules'])]
   .groupby(['run', 'model', 'variant'])[cols].mean().round(3))""")
md("## 4. Per-anomaly JSON (detector -> explainer interface)")
code("""ev = json.load(open(C.OUT_DIR / 'anomalies' / 'a12_A11-A10_noAIT__WinAE.json'))
print(len(ev), 'events'); print(json.dumps(ev[1], indent=1)[:2500])""")
md("## 5. RAG explanation\nRetrieval over `knowledge_base/` + template generation. With an API key, "
   "`Explainer(backend='claude')` sends the same retrieved context to Claude.")
code("""from swatad.rag.explainer import Explainer
E = Explainer(backend='template')
from IPython.display import Markdown
Markdown(E.explain(ev[1])['markdown'])""")
code("""pd.read_csv(C.OUT_DIR / 'explanations' / 'a12_A11-A10_noAIT__WinAE_eval.csv')""")
md("## 6. Synthetic injections (from `scripts/run_synthetic.py`)")
code("""s = pd.read_csv(C.OUT_DIR / 'synthetic' / 'synthetic_summary.csv')
s[s.variant == 'model'].pivot(index='type', columns='model', values='recall').round(2)""")

nb = nbf.v4.new_notebook(cells=cells, metadata={"kernelspec": {"name": "python3", "display_name": "Python 3"}})
out = ROOT / "notebooks" / "01_walkthrough.ipynb"
nbf.write(nb, out)
if "--execute" in sys.argv:
    from nbconvert.preprocessors import ExecutePreprocessor
    ExecutePreprocessor(timeout=1800, kernel_name="python3").preprocess(nb, {"metadata": {"path": str(out.parent)}})
    nbf.write(nb, out)
print("wrote", out)
