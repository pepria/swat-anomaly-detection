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

| Model | FPR on clean normal data before -> after | False-alarm events before -> after | Event recall before -> after |
|---|---|---|---|
| GMM | 0.979 -> 0.082 | 1.7 -> 19.3 | 0.06 -> 0.33 |
| AE | 0.834 -> 0.048 | 5.3 -> 20.3 | 0.03 -> 0.73 |
| WinAE | 0.000 -> 0.039 | 0.0 -> 16.0 | 0.70 -> 0.79 |
| LSTM-AE | 0.000 -> 0.061 | 0.3 -> 18.3 | 0.76 -> 0.73 |

The old values (FPR 83-98% for GMM and AE) were an artefact of the biased training threshold. After the fix, the training-time
threshold gives 16-20 false-alarm events instead of 5-7 with the calibration window, and 4-8% instead of 0.3% FPR on clean data.
Re-calibration still helps by a factor of about 3-4, but it is not the dramatic failure shown before. **The statements in RESULTS.md
(sections 1-2, "GMM 24%, AE 61%, LSTM-AE 93% FPR clean") and the README note on thresholds that do not transfer should be updated
accordingly.**

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
- The `outputs/` tables and the numbers in RESULTS.md were produced by the code before these fixes. They are not updated in this
  change, to avoid conflicts with the open documentation pull request; the new numbers are in this file.
