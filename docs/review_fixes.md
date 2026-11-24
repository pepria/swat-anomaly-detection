# Fixes after the code review

An external review of the repository listed problems in the detection and evaluation code. Each point was checked in the code;
those that were real are fixed (commit "Fix issues found in the code review"), and the experiments were rerun.

## What was fixed

| Problem | Verdict | Fix |
|---|---|---|
| `run_synthetic.py`: injection sigma computed on all training rows (start-up, gaps) | real | sigma from valid rows (`valid_mask`); same in `run_synthetic_explain.py` |
| `s / thr` for the combined score breaks for thresholds <= 0 (negative log-likelihood) | latent: all calibrated thresholds are positive | `evaluate.score_ratio` = `(s - thr) / |thr| + 1`, identical for thr > 0 |
| "Training threshold" row: scores of sampled, non-contiguous rows, smoothed afterwards | real | `pipeline.train_scores`: contiguous blocks, smoothed like a test recording, valid rows selected afterwards |
| Early stopping on random validation rows (overlapping windows, autocorrelation) | real | validation = contiguous time blocks (`SWAT_VAL_SPLIT=random` reproduces the old behaviour) |
| `best_state` stays `None` when the validation loss is NaN | real | keep the current weights, print a warning |
| GMM contribution used only the diagonal of the covariance | real | contribution from the precision matrix (`d_i (P d)_i`, clipped at 0) |
| Contribution normalisation on `[::5]` (main) vs `[::20]` (synthetic) rows | real | one function (`train_scores`) for both |
| `actuator_flip` turned the valve state 0 into 2 | real | 0 is kept |
| `IndexError` for single-line knowledge-base chunks | real | `_body()` helper |
| Pickle file not closed; default A12 path contained an upload id | real | `with open`; default `<raw>/SWaT.A12_OTDataset_Mar_26.zip` |
| A12 label files not in the repository | real | `scripts/rebuild_a12_labels.py` rebuilds them from the attack catalog (identical to the files used so far) |
| No tests | partly | `tests/test_review_fixes.py` (8 tests); the open pull request of the other team member adds 26 more |
| "Claude backend never run" | wrong | it was run; outputs are in `outputs/explanations/llm/` |

Not changed: the first window is filled with values of the following window (no effect, evaluation starts at 10:30); the GMM BIC always
picks the largest k of the grid (16): a larger grid would change the GMM results and the GMM is not the main model.

## Effect on the results (A12, main configuration A11+A10 noAIT, mean of 3 seeds)

| Model | AUC before -> after | Event recall before -> after | False-alarm events before -> after |
|---|---|---|---|
| WinAE | 0.894 -> 0.900 | 0.91 -> 0.91 | 1.0 -> 2.3 |
| AE | 0.880 -> 0.877 | 0.61 -> 0.67 | 5.7 -> 6.7 |
| LSTM-AE | 0.873 -> 0.867 | 0.76 -> 0.82 | 4.3 -> 4.7 |
| GMM | 0.871 -> 0.871 | 0.73 -> 0.73 | 7.0 -> 7.0 |
| IForest | 0.751 -> 0.751 | 0.52 -> 0.52 | 7.3 -> 7.3 |

The ranking and the conclusions of the main experiment do not change; only the neural models move slightly (early stopping).

### Training-time threshold (no re-calibration)

FPR on clean normal data with the threshold learnt on the training data, before -> after (false-alarm events with this
threshold in brackets, after the fix; with the calibration hour they are 2-7):

| Configuration | GMM | AE | WinAE | LSTM-AE | IForest |
|---|---|---|---|---|---|
| A11+A10, noAIT (main) | 0.98 -> 0.08 (19) | 0.83 -> 0.05 (20) | 0.00 -> 0.04 (16) | 0.00 -> 0.06 (18) | 0.11 -> 0.17 (16) |
| A11+A10, all features | 1.00 -> 1.00 | 1.00 -> 0.53 (17) | 0.00 -> 0.51 (18) | 0.00 -> 0.51 (17) | 0.12 -> 0.26 (13) |
| A11 only, noAIT | 1.00 -> 0.95 | 1.00 -> 0.99 | 1.00 -> 1.00 | 1.00 -> 1.00 | 0.08 -> 0.07 (20) |
| A11 only, all features | 1.00 -> 1.00 | 1.00 -> 1.00 | 1.00 -> 1.00 | 1.00 -> 1.00 | 0.08 -> 0.22 (18) |

The old numbers were produced by a biased computation (sampled, non-contiguous rows for the point models; only the first 60,000
training rows for the window models). After the fix the picture is different from both the old table and from a simple
"not dramatic" reading:

- In the **main configuration** the training threshold costs 4-8% FPR and 16-20 false-alarm events instead of 0.2-0.5% and 2-7 with the
  calibration hour; the old 83-98% for GMM and AE was an artefact.
- With **A11 only or with AIT features** the training threshold still fails completely (50-100% FPR: the models alarm on almost all clean
  data), because of the domain shift between recordings. The old statement that only the window models stay at <= 0.1% without
  re-calibration was wrong: they are not more robust (0.00 -> 0.51 with all features).
- Re-calibration on a short recent normal window therefore stays necessary; how much it matters depends on how diverse the training data is.

RESULTS.md (section 1, findings 4 and 5), RESULTS_zh.md and the README now say this.

### Synthetic injections (`run_synthetic.py`, 40 injections)

| | recall before -> after | hit@1 before -> after | hit@3 before -> after | false-alarm events before -> after |
|---|---|---|---|---|
| WinAE | 0.63 -> 0.55 | 0.80 -> 0.60 | 0.90 -> 0.83 | 1 -> 0 |
| AE | 0.73 -> 0.65 | 0.58 -> 0.50 | 0.80 -> 0.78 | 4 -> 17 |
| LSTM-AE | 0.55 -> 0.40 | 0.60 -> 0.73 | 0.80 -> 0.83 | 6 -> 4 |

With the sigma of the valid rows the injections are smaller in raw units, so recall drops, as the review expected; the earlier
numbers were optimistic. The AE false alarms in the clean part (4 -> 17) come from one seed of the retrained network and should not
be over-interpreted.

### Explanations on the synthetic injections and on SWaT 2015

`docs/synthetic_explanation_eval.md` and `docs/swat2015_explanation_eval.md` contain the numbers after the fixes. The main changes:
tag localisation on the synthetic injections stays at 0.97-1.00, the WinAE "high" confidence is still reliable on them (11 of 11) but the AE "high"
is not (0.72), and on SWaT 2015 the WinAE "high" confidence (1 attack among 7 events) does not carry over.

## Methodological points that code cannot fix

- The configuration (A11+A10, noAIT) and the hyper-parameters (rule margin, acknowledgement time, smoothing windows) were chosen
  by looking at A12, which has only 11 attacks. The A12 numbers are therefore optimistic; SWaT 2015 and the synthetic injections are the
  less biased checks.
- The signature classifier and the category mapping were written knowing the A12 attacks. The leave-one-out retrieval score (0.4) is
  the more honest number for the explanation layer than the category accuracy (0.7).
- `outputs/` (metrics, tables, figures, synthetic results, anomaly JSON and explanations) and the numbers in RESULTS.md, RESULTS_zh.md and
  the README were regenerated after these fixes (all A12 configurations and the SWaT 2015 setup with 3 seeds, the synthetic injections
  and the explanations of the main configuration).
