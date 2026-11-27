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
| `tests/` | unit tests on synthetic data (`pytest`, no SWaT files needed) |
| `notebooks/01_walkthrough.ipynb` | guided tour of the pipeline and the results |
| `outputs/` | metrics, scores, anomaly JSON, explanations, figures |
| `docs/anomaly_event.schema.json` | the detector -> explainer contract |

## Data

| Dataset | Use | Notes |
|---|---|---|
| SWaT.A11 (19-20 Feb 2026) | training (normal) | 2 x 8 h, 1 s, 87 columns |
| SWaT.A10 (Dec 2023, 105 h) | extra training (normal) | minute timestamps, seconds rebuilt from row order; CrossOver with WaDi shifts water quality |
| SWaT.A12 (11 Mar 2026) | evaluation | 4.4 h normal then 11 attacks; per-second labels from the EDA (attack sheet is ~25 min early) |
| SWaT 2015 A1/A2 | second, independent benchmark | 7 days normal + 36 attacks, 51 columns, comparable with the literature; the Excel files are converted with `scripts/convert_2015_xlsx.py`, the attack list is in `knowledge_base/04_swat2015_attack_catalog.md` |

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
cached in `data/processed/*.parquet`. The SWaT data is not redistributable (request it from
iTrust, SUTD). `swatad/config.py` expects this layout under `SWAT_RAW_DIR`:

```
SWaT.A11_OTDataset_Feb_26.zip
SWaT.A10_Dec 2023 Historian Data.csv
<A12 zip>                         # set SWAT_A12_ZIP to its path (the default is our shared folder)
swat_eda/A12_labels_shifted.csv   # per-second A12 labels; not in the repository, rebuild them with
                                  #   python scripts/rebuild_a12_labels.py   (11 attacks, 3,139 attack seconds)
swat2015_csv/SWaT2015_normal_v1.csv
swat2015_csv/SWaT2015_attack_v0.csv
```

The attack windows of A12 are in the repository (`labels/A12_attack_list.csv`, override with `SWAT_A12_ATTACKS`), not in the knowledge base: the
attack catalogs the explainer reads contain durations but no clock times, so an event cannot be matched to an attack by its time.

Example: `export SWAT_RAW_DIR=~/swat_raw SWAT_A12_ZIP=~/swat_raw/SWaT.A12.zip`.

## Tests

The unit tests use small synthetic recordings and the stored anomaly JSON, so they run without
the SWaT data (about 10 s on a laptop) and on every push via GitHub Actions
(`.github/workflows/tests.yml`):

```bash
pip install -r requirements-dev.txt
pytest
```

They cover feature selection and windowing, point/event metrics (including the onset rule),
the rule layer (unseen state, out of range, acknowledgement, calibration, frozen sensor),
synthetic injection, the common `fit/score` API of all five detectors, retrieval, and the
template explainer (schema validity, no ground-truth leak).

## Method in short

**Preprocessing.** `Bad Input` -> NaN -> forward fill, flagged as a gap and excluded from training;
the 4 always-missing alarm columns are dropped; the morning start-up (until PIT501 > 200 kPa,
+15 min) is excluded; redundant actuator duplicates are dropped; near-constant columns leave the
ML input but stay in the rule layer; AIT water-quality analysers are optionally removed
(`noAIT`) because they drift between recordings.

**Detectors.** IsolationForest (baseline), GMM with full covariance (number of components by
BIC), point MLP autoencoder, a window autoencoder on the last 2 minutes (30 samples every 4 s,
flattened MLP) and an LSTM sequence autoencoder on the same windows. Each detector returns a
score and a per-feature contribution (GMM: share of the squared Mahalanobis distance to the
responsible component; AE: squared reconstruction error; IForest: distance from the training
median). The autoencoders stop early on a validation set made of contiguous time blocks.

**Thresholds.** 99.5% quantile of the score on a short normal calibration window recorded at
deployment time (A12 09:30-10:30). The alternative, the threshold learnt on the training data
itself, is reported as `model (train thr)`: in the main configuration (A11+A10, noAIT) it gives
4-8% FPR on clean normal data instead of 0.2-0.5% and 16-20 instead of 2-7 false-alarm events, and when
the training data is only A11 or AIT features are used it fails completely (FPR 50-100%).
Re-calibration on a short recent normal window is therefore recommended; how much it matters
depends on how diverse the training data is (see RESULTS section 1, findings 4 and 5, and
[docs/review_fixes.md](docs/review_fixes.md)).

**Rule layer.** (1) a discrete tag takes a value never seen in training (catches standby pumps
and valves that attacks switch on), (2) a non-AIT sensor leaves the training range plus margin.
Tags that already fire on the calibration window are disabled (drift). A persistent violation
alarms for 10 minutes and is then considered acknowledged. An optional third rule, (3) a continuous sensor frozen at
exactly the same value for longer than both `stuck_s` seconds and its longest flat run in
training, targets the frozen-sensor case that no model detects (RESULTS §3). It is off by
default so the published numbers are unchanged. Rows of a communication gap (`_gap == 1`) are ignored by it. It was evaluated in
[docs/stuck_rule_evaluation.md](docs/stuck_rule_evaluation.md): the frozen-sensor recall on the synthetic data rises from 0 to 0.17 and nothing changes on
real A12. Enable it with `RuleMonitor(stuck_s=120)`,
`run(..., rule_kwargs={"stuck_s": 120})` or `python scripts/run_synthetic.py --stuck-rule 120`.

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
and fills a template. Attacks of the dataset being explained are retrieved first (2 entries), plus one
entry of the other attack catalog (A12 and SWaT 2015), with a boost for the attacked tags. The
confidence of an explanation is capped by an evidence score (`calibrate_confidence`).
`Explainer(backend="claude")` sends the same evidence to Claude (`claude-opus-5-5`) instead; it needs
`pip install anthropic` and an API key, and it **sends the event data to an external API** (`python scripts/export_and_explain.py <run> <model> claude`;
`auto` uses Claude only if `SWAT_ALLOW_EXTERNAL_LLM=1` is set as well). The reply is validated against `docs/explanation.schema.json` and escaped; the
category and the sources come from the rules, never from the model (see [docs/threat_model.md](docs/threat_model.md)). It was run on the A12 events; the outputs are in
`outputs/explanations/llm/` and the two back-ends are compared event by event in
[docs/llm_vs_template_report.md](docs/llm_vs_template_report.md)
(Chinese: [llm_vs_template_report_zh.md](docs/llm_vs_template_report_zh.md)). The explanation
layer is also evaluated on synthetic injections
([docs/synthetic_explanation_eval.md](docs/synthetic_explanation_eval.md)) and on the 36 SWaT 2015
attacks ([docs/swat2015_explanation_eval.md](docs/swat2015_explanation_eval.md)); code-review fixes and
their effect on the results are in [docs/review_fixes.md](docs/review_fixes.md).

## Limitations

- A12 has only 11 attacks (1 day); the 2015 benchmark gives statistical weight. The configuration
  (A11+A10, noAIT) and the hyper-parameters (rule margin, acknowledgement time, smoothing windows)
  were chosen by looking at A12, so the A12 numbers are optimistic.
- After A12 attack #1 the dechlorination pumps (P401/P403/UV401) stay off for the rest of the
  day, so "normal" points between later attacks are not truly normal.
- The explanation heuristics were designed knowing the A12 attack types; the synthetic
  injections are the less biased check. The A12 attack catalog is part of the knowledge base, so
  "known attack" matching on A12 is optimistic; a leave-one-out variant is reported too (0.3-0.5,
  the more honest number for the explanation layer). On SWaT 2015 the explanations are much weaker
  than on A12, because the detectors find only about half of the attacks there.
- The training data matters: without 16 hours of A10 in the training the GMM event recall falls from 0.73 to 0.42 and the AE has 10.7 instead of 6.7 false-alarm events
  (window AE unchanged); the held-out blocks of that experiment are all from A10. The attack catalogs give durations but no clock times; three A12 attacks have a
  unique duration. The rule layer has known blind spots (alarm latch, poisoned calibration window, communication gaps), listed in
  [docs/threat_model.md](docs/threat_model.md).
- The run state (`feature_space.json`) is JSON, no pickle is ever loaded.
- The knowledge base is built from public SWaT knowledge; official iTrust tag documentation,
  set points and P&ID would improve it.
