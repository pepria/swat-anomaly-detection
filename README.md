# SWaT: unsupervised anomaly detection + RAG explanation

Course project, *AI in Industry* (University of Bologna). The system **detects** anomalies in
the SWaT water-treatment testbed with unsupervised models trained on normal data only (GMM,
autoencoders, Isolation Forest baseline) and **explains** each detected anomaly with a
retrieval-augmented layer that looks up process knowledge, tag definitions, physical invariants
and known attack patterns.

Results are summarised in **[RESULTS.md](RESULTS.md)** (Chinese summary: [RESULTS_zh.md](RESULTS_zh.md)).

```
detection (person A)                         interface                 explanation (person B)
raw SWaT CSV -> preprocessing -> models  ->  anomaly event JSON   ->  retrieval over knowledge_base/
             -> rule layer      -> alarm      (docs/anomaly_event      -> signature classifier
                                   events      .schema.json)           -> template / LLM -> report
```

## Repository layout

| Path | Content |
|---|---|
| `swatad/config.py` | paths (override with `SWAT_RAW_DIR`, `SWAT_A12_ZIP`, `SWAT_WORK_DIR`), constants |
| `swatad/data.py` | loaders for A11, A12, A10 and SWaT 2015; cleaning; parquet cache |
| `swatad/features.py` | feature selection, standardisation, sliding windows |
| `swatad/rules.py` | transparent rule layer (unseen actuator state, out of range) with calibration |
| `swatad/models.py` | IsolationForest, GMM, MLP autoencoder, window MLP-AE, LSTM-AE (common `fit/score` API with per-feature contributions) |
| `swatad/evaluate.py` | point metrics (AUC-ROC, AUC-PR, P/R/F1, FPR) and event metrics (recall, precision, delay) |
| `swatad/pipeline.py` | experiment runner for the two setups |
| `swatad/inject.py` | synthetic anomaly injection (spike, bias, drift, stuck, noise, actuator flip, replay) |
| `swatad/events.py` | alarm events -> anomaly JSON (top contributors, rule hits, signal shape) |
| `swatad/rag/` | `retriever.py` (TF-IDF, multi-source), `explainer.py` (classifier, template and Claude back-ends), `tags.py` |
| `knowledge_base/` | RAG documents: process overview, tag dictionary, attack/fault patterns, A12 attack catalog, mined invariants |
| `scripts/` | reproducible entry points (below) |
| `notebooks/01_walkthrough.ipynb` | guided tour of the pipeline and the results |
| `outputs/` | metrics, scores, anomaly JSON, explanations, figures |
| `docs/anomaly_event.schema.json` | the detector -> explainer contract |

## Data

| Dataset | Use | Notes |
|---|---|---|
| SWaT.A11 (19-20 Feb 2026) | training (normal) | 2 x 8 h, 1 s, 87 columns |
| SWaT.A10 (Dec 2023, 105 h) | extra training (normal) | minute timestamps, seconds rebuilt from row order; CrossOver with WaDi shifts water quality |
| SWaT.A12 (11 Mar 2026) | evaluation | 4.4 h normal then 11 attacks; per-second labels from the EDA (attack sheet is ~25 min early) |
| SWaT 2015 A1/A2 | second, independent benchmark | 7 days normal + 36 attacks, 51 columns, comparable with the literature |

The two setups are never mixed: models trained on 2015 are near-random on A12 (EDA §6.3).

## How to run

Python 3.11+; `pip install -r requirements.txt`. Run from any working directory:

```bash
python scripts/run_experiments.py           # all models x 3 seeds, both setups (~45 min on 4 cores; run one job at a time)
python scripts/run_synthetic.py             # synthetic injection on clean A12 normal data
python scripts/build_kb.py                  # data-derived knowledge-base documents
python scripts/export_and_explain.py a12_A11-A10_noAIT WinAE   # anomaly JSON + explanations
python scripts/make_figures.py
python scripts/summarize.py                # outputs/results_tables.md
python scripts/build_notebook.py --execute
```

Raw files are read directly from the original zip/CSV files in `SWAT_RAW_DIR`; cleaned data is
cached in `data/processed/*.parquet`.

## Method in short

**Preprocessing.** `Bad Input` -> NaN -> forward fill, flagged as a gap and excluded from training;
the 4 always-missing alarm columns are dropped; the morning start-up (until PIT501 > 200 kPa,
+15 min) is excluded; redundant actuator duplicates are dropped; near-constant columns leave the
ML input but stay in the rule layer; AIT water-quality analysers are optionally removed
(`noAIT`) because they drift between recordings.

**Detectors.** IsolationForest (baseline), GMM with full covariance (number of components by
BIC), point MLP autoencoder, a window autoencoder on the last 2 minutes (30 samples every 4 s,
flattened MLP) and an LSTM sequence autoencoder on the same windows. Each detector returns a
score and a per-feature contribution (GMM: standardised deviation from the responsible
component; AE: squared reconstruction error; IForest: distance from the training median).

**Thresholds.** 99.5% quantile of the score on a short normal calibration window recorded at
deployment time (A12 09:30-10:30), because thresholds learnt on the training data do not
transfer across weeks (reported as `model (train thr)`).

**Rule layer.** (1) a discrete tag takes a value never seen in training (catches standby pumps
and valves that attacks switch on), (2) a non-AIT sensor leaves the training range plus margin.
Tags that already fire on the calibration window are disabled (drift). A persistent violation
alarms for 10 minutes and is then considered acknowledged.

**Evaluation.** Point level: AUC-ROC, AUC-PR, precision/recall/F1 at the calibrated threshold,
FPR on clean normal data (before the first attack). Event level: an attack counts as detected
only if an alarm **starts** inside [start, end + 5 min] (an alarm that never cleared after the
previous attack does not count); also reported: the looser overlap recall, alarm-event precision,
false-alarm events and detection delay. 3 seeds per model.

**Explanation.** Each alarm event becomes a JSON record (time window, score/threshold, top-k
contributing tags ranked by their increase versus the 2 minutes before, rule hits, signal-shape
features). The explainer classifies the signature (standby activation, out-of-range spoof,
oscillation, actuator manipulation, excursion, drift/in-range, multivariate), retrieves a fixed
budget of chunks per document type (tag dictionary, pattern, known attacks, invariants, process)
and fills a template. `Explainer(backend="claude")` sends the same evidence to Claude
(`claude-opus-5-5`) instead; it needs `pip install anthropic` and an API key, and was not run in
this environment.

## Limitations

- A12 has only 11 attacks (1 day); the 2015 benchmark gives statistical weight.
- After A12 attack #1 the dechlorination pumps (P401/P403/UV401) stay off for the rest of the
  day, so "normal" points between later attacks are not truly normal.
- The explanation heuristics were designed knowing the A12 attack types; the synthetic
  injections are the less biased check. The A12 attack catalog is part of the knowledge base, so
  "known attack" matching on A12 is optimistic; a leave-one-out variant is reported too.
- The knowledge base is built from public SWaT knowledge; official iTrust tag documentation,
  set points and P&ID would improve it.
