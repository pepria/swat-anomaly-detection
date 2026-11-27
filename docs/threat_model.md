# Threat model and security notes

Scope: the research code in this repository (detectors, rule layer, explanation layer). It is not a hardened product; this
page lists what an attacker (or a careless user) could do, what the code does about it, and what is left open. Chinese
summary: RESULTS_zh.md section 6.

## 1. Explanation layer and the LLM

| Property | How it is enforced |
|---|---|
| The LLM cannot change the detection | the explainer runs after the detector; the events and the alarm times are fixed before it is called |
| The LLM cannot choose the category | `category` and `sources` are set by the rule-based classifier / the retriever and overwrite anything the model returns |
| The confidence cannot be inflated | `calibrate_confidence` caps the reported confidence with an evidence score computed from the event |
| The LLM never sees the ground truth | `ground_truth_eval_only` is removed before the event is explained |
| The text of the LLM is data, not markup | `sanitize_llm_output` keeps only the fields of `docs/explanation.schema.json`, limits their length, escapes HTML and breaks markdown links and images, and falls back to `low` confidence for unknown values (tests in `tests/test_review_fixes.py`) |
| Nothing leaves the machine by accident | the default back-end is the local template; `auto` uses Claude only if `ANTHROPIC_API_KEY` **and** `SWAT_ALLOW_EXTERNAL_LLM=1` are set; the Claude back-end prints a notice that the event is sent out |

**Data leaving the plant.** The Claude back-end sends the anomaly event (tag names, values, signal features, rule hits) and knowledge-base excerpts to an
external API. For the public SWaT testbed this is harmless; in a real plant it is a confidentiality problem and the argument for a local small model
(the template back-end is the local fallback). Raw recordings are never sent.

**Prompt injection.** The event text contains tag names and numbers produced by the pipeline, the knowledge base is ours, so there is no free text
from an untrusted source in the prompt in this setting. If the prompt ever included operator comments or other free text, the checks above
(category and confidence taken from rules, validated and escaped output) are what limits the damage, but an injected instruction could still distort the
wording of the summary.

## 2. Stored state

The fitted feature space and rule monitor of a run were pickled; unpickling a file from somebody else runs arbitrary code. The run state is now JSON
(`swatad.persist`, `feature_space.json`), no pickle file is ever loaded, and `scripts/convert_run_state.py` converts pickles that you produced yourself.

## 3. Rule layer and detectors: what an attacker can still do

These are properties of the design, not bugs; they do not change any published number.

1. **Alarm latch.** `RuleMonitor.alarm(ack_s=600)`: a tag that keeps violating its rule raises an alarm only for the first 10 minutes (as if an operator
   acknowledged it). A persistent violation is silent afterwards; a new tag, or the same tag after it returned to normal, alarms again.
2. **Poisoned calibration window.** The thresholds and the tags that the rule layer disables (those that already fire on the calibration hour, hit rate
   > 0.1%) come from a recording assumed to be normal. An attacker active during the calibration hour raises the thresholds and switches rules off for the
   tags it manipulates. The calibration hour must be checked by a person.
3. **Communication gaps.** Rows of a gap (`_gap == 1`) are forward-filled, excluded from training and ignored by the frozen-sensor rule; the gap itself does
   not raise an alarm. A link that drops often is therefore not reported. (The frozen-sensor rule used to reset its count at a gap, so that a sensor
   frozen for 15 minutes with a 3 s dropout every 100 s produced no hit; the count now pauses instead, 0 -> 484 flagged rows in that test.) A
   "too many or too long gaps" alarm is still open.
4. **Frozen sensors.** The frozen-sensor rule catches only a part of them (1 of 6 injected, `docs/stuck_rule_evaluation.md`); a plausible replay of earlier
   values is not detected by any model.
5. **Water-quality analysers (AIT)** are excluded from the models and from the range rule because they drift, so a spoofed AIT is missed (A12 attack 11).
6. **Adaptive attacker.** All thresholds are fixed quantiles of normal scores; an attacker who knows them can stay below them (slow drift, in-range
   changes). In-range spoofing (A12 attack 6) is already missed by the detection layer.

## 4. Evaluation leaks that are not attacks but weaken the results

- The attack catalogs of the knowledge base give no clock times, but they give **durations**; three A12 attacks have a unique one (#6 161 s, #7 331 s, #11 70 s,
  while 8 of 11 last 341 s). A very careful explainer could use it; the effect is small because event durations are not attack durations.
- The configuration and the hyper-parameters were chosen on A12; the signature classifier was written knowing the A12 attacks (README, Limitations).
- The results depend on the training data: removing 16 hours of A10 from the training changes the GMM event recall from 0.73 to 0.42 and the AE
  false-alarm events from 6.7 to 10.7 (`docs/review_fixes.md`); the window AE stays at 0.91. The held-out blocks of that experiment come only from A10,
  not from A11.
