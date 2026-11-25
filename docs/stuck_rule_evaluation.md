# Frozen-sensor rule: evaluation

The optional rule `RuleMonitor(stuck_s=...)` (off by default) flags a continuous sensor that keeps exactly the same value for longer than
`stuck_s` seconds and longer than 1.2 times its longest flat run in the training data. It targets the case that no model detects
(RESULTS section 3). It was evaluated with `stuck_s = 120` on the synthetic injections and on the real A12 recording.

## Two problems found and fixed first

1. **False alarms during communication gaps.** The loader forward-fills the values of a communication gap, so the sensor looks frozen, but the
   training data (which excludes gap rows) never contained such a run. A simulated 300 s outage was flagged in 181 rows. Rows with `_gap == 1`
   now break a run and are never reported; a real frozen sensor is still detected (tests in `tests/test_review_fixes.py`).
2. **The explainer crashed on a stuck hit** (`KeyError: 'normal_range'`, the hit has `frozen_value` and `limit_s` instead). There is now a
   category `frozen_sensor`, an evidence line ("stayed at exactly X for longer than N s"), recommended checks, and a test.

## Results

**Synthetic injections** (40 injections, `scripts/run_synthetic.py --stuck-rule 120`, model + rules):

| | stuck recall off -> on | all types recall off -> on |
|---|---|---|
| AE | 0.00 -> 0.17 | 0.68 -> 0.70 |
| GMM | 0.00 -> 0.17 | 0.60 -> 0.62 |
| WinAE | 0.00 -> 0.17 | 0.60 -> 0.65 |
| LSTM-AE | 0.00 -> 0.17 | 0.52 -> 0.55 |
| IForest | 0.33 -> 0.50 | 0.45 -> 0.48 |

The rule catches 1 of 6 frozen injections (3 of 6 for IForest). Many sensors have long natural flat runs in training, so the limit
(1.2 x the longest run, at least 120 s) is often longer than the 120-300 s injections; tags that are flat for more than an hour are not monitored at all.
(Other types change by +-0.17 between the two runs because the networks are retrained; only the stuck row is a rule effect.)

**Explanation of the stuck injections** (`scripts/run_synthetic_explain.py --stuck-rule 120`): AE and WinAE detect 1 of 10 stuck injections each; both are
explained as `frozen_sensor` with the right tag (found through the rule hit, not through the model contributions).

**Real A12 recording** (6.5 h, 11 attacks): with the stuck rule on, **no extra rule hit at all** (checked tag by tag), so no new false alarm. The two
frozen attacks of A12 (#4 LIT101 at 400 mm, #9 DPIT301 at 45 kPa) leave the normal range and are already caught by the range rule, so the rule
adds nothing there. The rule-only result is identical (10 of 11 attacks, 0 false alarms). A first run showed WinAE + rules at 0.82 instead of 0.91
event recall with the rule on; this is not a rule effect: the same configuration without the rule gave 0.82 in one run and 0.91 in another (training noise of
one seed, one attack).

## Conclusion

The rule is safe to enable on A12 (no false alarms) and detects some frozen sensors, but with the current limit it misses most of them. It cannot
be validated on real frozen sensors, because A12 has none inside the normal range. Possible improvements: a limit from a high quantile of the flat runs
instead of 1.2 x the maximum, a per-tag minimum (for example 3 times the sampling resolution), and merging with the range rule.
