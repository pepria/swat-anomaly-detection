# Explanation quality on synthetic injections

Script: `scripts/run_synthetic_explain.py` (outputs in `outputs/synthetic_explain/`, not tracked).

Setup: 5 random realisations of 7 injection types (spike, bias, drift, noise, stuck, actuator flip, replay;
10 injections per type, 67 per model) into the clean part of A12 (10:35-13:15). Detector trained on A11+A10 (noAIT),
thresholds calibrated on A12 09:30-10:30, as in the main setup. Every alarm event (model + rules) is exported to the
anomaly-event JSON and explained with the **template** backend, then checked against what was injected.
Unlike the A12 attacks, the root-cause tag and type are known exactly and the number of cases is larger.
The signature classifier was written knowing the A12 attacks, not these injections, so this is the less biased test.

Checks (rates are among *detected* injections):
- **tag_top3_or_rules**: the injected tag is among the 3 strongest model contributors or among the new rule violations.
- **category_ok**: the signature category is one of the acceptable categories of the type
  (spike: out-of-range / spoof / oscillation; bias: out-of-range / spoof / drift; drift: drift / out-of-range;
  noise: oscillation / drift; stuck: spoof / drift / multivariate; replay: multivariate / drift;
  actuator flip: actuator manipulation / standby). These sets are my judgement.
- **pattern_ok**: the generic pattern retrieved from `03_attack_and_fault_patterns.md` is the one for that type.
- **fully_ok**: tag_top3_or_rules and category_ok.

## Results

(Numbers after the code-review fixes of `docs/review_fixes.md`: injection sigma from valid training rows, contiguous-block
early stopping, consistent contribution normalisation. The first version of this report gave slightly higher recall.)

| Model | Detected | Tag rank 1 | Tag in top 3 or rules | Category ok | Pattern ok | Fully ok |
|---|---|---|---|---|---|---|
| AE | 0.64 | 0.79 | **1.00** | 0.84 | 0.33 | 0.84 |
| WinAE | 0.54 | **0.89** | 0.97 | 0.86 | 0.31 | 0.86 |

By type (WinAE; fully ok among the detected): actuator flip 0.71, bias 0.89, drift 0.78, noise 1.00. **Spikes**: only 1 of 10
detected by WinAE (6 of 10 by AE, fully ok 0.67). **Stuck and replay**: never detected by WinAE; AE detects 2 of 7 replays
and none of the 10 stuck injections, and the 2 replays are not explained as such.

Confidence (calibrated, `confidence`) against correctness (fully_ok):

| Model | high | medium | low |
|---|---|---|---|
| AE | 18 events, 0.72 correct (includes 2 false alarms) | 29 events, 0.69 | 3 events, 1.00 |
| WinAE | 11 events, **1.00** | 18 events, 0.78 | 7 events, 0.86 |

## Findings

1. **The input to the explainer is good when the anomaly is detected**: the injected tag is in the top 3 / rule hits in 97-100% of
   the cases (A12 real attacks: 0.90). This is higher than on A12 because injections touch a single tag.
2. **For the WinAE, "high" confidence was reliable** (11 of 11 correct); for the AE it was not (0.72, two false alarms were
   labelled "high"). The calibration does not separate the levels well: WinAE "low" (0.86) is as good as "medium" (0.78), AE "low" is
   better than "high". It caps over-confidence but is not a ranking of correctness.
3. **Pattern retrieval is the weak spot** (0.31-0.33): the generic pattern follows the signature category, so drift, noise and
   spike never retrieve their specific pattern ("Sensor drift", "Increased noise", "Spike or glitch"). Retrieving the top 2
   patterns or using the signal shape would fix this.
4. **Short spikes** are almost invisible to the WinAE (window of 2 minutes) and only partly detected by the AE.
5. **Stuck and replay are invisible to the detectors** (see RESULTS section 3); a "zero variance for N minutes" rule is the natural fix
   (a proposal for it is in the open pull request of the other team member).

## Limits

Single tag per injection, magnitudes 2-10 sigma, template backend only (the LLM was not run on these events), judgement-based
acceptable categories, one seed of the detectors, and the confidence rules were designed with the A12 events in mind.

## With the frozen-sensor rule (`--stuck-rule 120`)

Results in `outputs/synthetic_explain_stuck` (not tracked). Everything above stays within +-0.05 (the networks are retrained). The stuck injections:
AE and WinAE detect 1 of 10 each, and both are explained as `frozen_sensor` with the right tag, found through the rule hit (the model contributions do not
rank it). Details and the check on real A12 data: [stuck_rule_evaluation.md](stuck_rule_evaluation.md).
