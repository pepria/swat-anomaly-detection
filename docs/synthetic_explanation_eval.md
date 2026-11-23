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

| Model | Detected | Tag rank 1 | Tag in top 3 or rules | Category ok | Pattern ok | Fully ok |
|---|---|---|---|---|---|---|
| AE | 0.61 | 0.85 | **1.00** | 0.95 | 0.34 | 0.95 |
| WinAE | 0.60 | **0.92** | 0.98 | 0.85 | 0.40 | 0.82 |

By type (WinAE; AE is similar except for spikes): actuator flip 0.88, bias 0.89, drift 0.78, noise 1.00 fully ok;
**spike 0.25** (only 40% detected; the 5-second spikes give events whose signature scatters over
drift / multivariate / actuator); **stuck and replay are never detected** (0 of 17 for both models), so there is nothing to explain.

Confidence (calibrated, `confidence`) against correctness (fully_ok):

| Model | high | medium | low |
|---|---|---|---|
| AE | 9 events, 1.00 correct | 29 events, 0.93 | 7 events, 0.43 (includes all 4 false alarms) |
| WinAE | 17 events, 1.00 | 15 events, 0.67 | 8 events, 0.75 |

## Findings

1. **The input to the explainer is good when the anomaly is detected**: the injected tag is in the top 3 / rule hits in 98-100% of
   the cases (A12 real attacks: 0.90). This is higher than on A12 because injections touch a single tag.
2. **"High" confidence is reliable** (all 26 "high" events were correct), which is what an operator needs. All 4 false alarms of AE are "low".
3. **Calibration does not separate "medium" from "low" for WinAE** (0.67 vs 0.75, small samples). It is a cap on over-confidence,
   not a ranking of correctness.
4. **Pattern retrieval is the weak spot** (0.34-0.40): the generic pattern follows the signature category, so drift, noise and
   spike never retrieve their specific pattern ("Sensor drift", "Increased noise", "Spike or glitch"). Retrieving the top 2
   patterns or using the signal shape would fix this.
5. **Spikes** and the 5 s window are a weak point of the WinAE (detected 0.40) and of the classifier (category scatter).
6. **Stuck and replay are invisible to the detectors** (see RESULTS section 3); a "zero variance for N minutes" rule is the natural fix.

## Limits

Single tag per injection, magnitudes 2-10 sigma, template backend only (the LLM was not run on these events), judgement-based
acceptable categories, and the confidence rules were designed with the A12 events in mind.
