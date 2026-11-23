# LLM backend vs template backend: comparison of the explanations

(Chinese version: [llm_vs_template_report_zh.md](llm_vs_template_report_zh.md))

- Detector: windowed autoencoder (WinAE) plus rule layer, trained on A11+A10 (AIT columns dropped), tested on A12. 10 alarm events covering 11 attacks; 1 event is a false alarm.
- LLM backend: Claude `claude-opus-5-5`, adaptive thinking, one call per event.
- Template backend: `TemplateBackend`, no LLM.
- Raw outputs: `outputs/explanations/a12_A11-A10_noAIT__WinAE.{md,json}` (LLM), `template_...` (template).

## 1. Conclusions

1. **The 5 metrics in the evaluation table are identical for both backends** (0.7 / 0.9 / 0.7 / 0.8 / 0.5). They look at the tags chosen by the detector, the category from `classify()` and the retrieved known attacks, which both backends share. They **do not measure the text the LLM writes**, so they cannot be used to claim the LLM is more accurate.
2. **The LLM is clearly better in text quality**: it explains the attack mechanism, rejects wrong pre-classifications and admits weak evidence. The template gets the category wrong in 2 of 10 events, and gives "high" confidence in one of them.
3. **No numbers were invented**: every number in the LLM text was compared with the event JSON and the knowledge base (tolerance 1%). The 9 numbers that did not match are percentage conversions, range end-points or differences; none came from nowhere.
4. **There is an evaluation-validity issue**: the LLM often matched the answer using the **attack schedule** in the knowledge base (section 4.1). That information would not exist in a real deployment.
5. **The LLM's weak spots come from retrieval, not from the LLM**: attacks 5 and 6 were not mentioned because their catalog entries were not retrieved.

## 2. Event by event

"Ground truth" is the label used only for evaluation; the explainer never sees it. Whether a category is right is my own judgement after reading the text.

| # | Time | Ground truth | Template category / confidence | LLM verdict / confidence | Better |
|---|---|---|---|---|---|
| 0 | 13:25–13:32 | Attack 1: valve manipulation | actuator manipulation, high | actuator manipulation, high. Notes the P501 anomaly as a side effect near the end of the attack and that the other contributors deviate only weakly | LLM (more specific) |
| 1 | 14:05–14:12 | Attack 2: MV101 open, P101 stopped | **out of range, medium (wrong category)** | actuator manipulation; explains that T101 overfills; explicitly rules out "sensor spoofing" (LIT101 is not flat and agrees with the flows) | **LLM** |
| 2 | 14:19–14:20 | false alarm | drift, low | low confidence; judged to be a UF idle phase with the tank refilling, probably benign; states the peak is only 2.2% above the threshold | LLM (better for false alarms) |
| 3 | 14:45–14:51 | Attack 3: dosing pumps started | standby activation, medium | standby activation, high. Names P202/P204/P206 switching to 2, and notes that the top contributor LSH601 only takes values seen in normal operation, so its role is unclear | LLM |
| 4 | 14:54–15:02 | tail of attack 3 plus attack 4 | sensor spoofing, medium | sensor spoofing, high. LIT101 starts at a flat 400 mm (flat fraction 0.74), later rises to 981 mm; links it with MV101 to explain the overflow risk | LLM |
| 5 | 15:04–15:12 | tail of attack 4 plus attack 5: valve manipulation | **sensor spoofing, high (wrong category and overconfident)** | low confidence; judged P5 actuator or operating-state change, and says the "sensor spoofing" pre-classification is doubtful because FIT504 only exceeds the limit by 0.070→0.072 with normal variance | **LLM** (but attack 5 not named) |
| 6 | 15:25–15:31 | attack 6 plus attack 7 | standby activation, medium | recognises P102 starting and matches attack 7; notes that LIT301/LIT401 rise but stay in range. **Attack 6 not found** | tie (both miss attack 6) |
| 7 | 15:45–15:54 | Attack 8: backwash diversion | standby activation, high | splits the event in two: MV303 leaving its fixed position (attack 8), then a full backwash that is the plant reacting to high DPIT301, not a standby-pump attack | LLM (but the label still says "standby activation", which does not fit the text) |
| 8 | 16:09–16:16 | Attack 9: DPIT301 spoofing | sensor spoofing, high | sensor spoofing, high. Gives a physical consistency argument: with the pump off and FIT301≈0, DPIT301 should be about 2.6 kPa, not 45 kPa | LLM |
| 9 | 16:35–16:39 | Attack 10: LIT601 oscillation | oscillation, medium | oscillation, high. About 32 direction changes per minute, single steps of 800 mm; a tank level cannot change like that | LLM |

Summary: the LLM is better in 9 events (the advantage is small in events 0 and 2, and event 7 has a label flaw), 1 is a tie (event 6). The template is better in none.

## 3. Fact check

- **Numbers**: compared with the event JSON and the knowledge base with a 1% tolerance. The LLM text contains no number out of thin air. The 9 values that did not match are:
  - `6.2`, `1.1`: contribution shares, converted from 0.062 and 0.011 to percentages.
  - `38`, `74`: flat fractions, converted from 0.38 and 0.743 to percentages.
  - `4.5`: a time difference computed by the LLM itself (15:00:30 to 15:04:55).
  - `-568`, `-2.39`, `-1010`: ranges "561–568", "2.34–2.39" and "794–1010" in the text, read as negative numbers by my number extractor.
- **Knowledge base content**: "Oldsmar", mentioned by the LLM, is in `04_a12_attack_catalog.md` (description of attack 3); it is not outside knowledge.
- **Pump names in event 3**: "P202 (NaCl), P204 (HCl), P206 (NaOCl)" come from `tags.py` / `02_tag_dictionary.md`. **Those two files contained known errors** (P207/P208 and P603 did not match the official PDF), and the LLM faithfully inherits errors from the knowledge base. These were corrected in a later commit.
- **Self-correction by the LLM**: it repeatedly points out that the event data disagrees with the dictionary ranges (e.g. the `normal_p99` of FIT101 differs from the dictionary maximum) and lowers its confidence accordingly. The template cannot do that.

## 4. Problems

### 4.1 Matching the answer by timestamp (evaluation validity)

In 8 of the 10 events (0, 1, 3, 4, 6, 7, 8, 9) the explanation or the "similar attacks" field explicitly cites the attack time from the catalog, e.g. "the event starts 11 s after attack 8 at 15:44:50". Every attack in `04_a12_attack_catalog.md` carries its A12 clock time, so the LLM can find the match without understanding the physics.

- In a real deployment there is no schedule of future attacks, so these matches do not transfer.
- The LLM does not rely on time alone: events 4 (LIT101 constant at 400 mm), 8 (physical consistency) and 9 (oscillation frequency) also have strong evidence in the data.
- Suggestion: **remove the clock times of the A12 catalog** from what the explainer retrieves (keep mechanism and affected tags) and rerun, to see how much ability remains. This is the most valuable control experiment; it is done in section 7.

### 4.2 Retrieval decides what the LLM can say

- Event 5: retrieval returned only the chunks of attacks 4 and 9, not attack 5 (valve manipulation). The LLM therefore honestly said "no known attack matches", although attack 5 is the answer. In event 0, attack 5 was retrieved.
- Event 6: attack 6 was not retrieved. The LLM writes that attack 6 is not described in the provided excerpts and its contribution cannot be assessed. That is honest, but it means attack 6 is also missed in the LLM version.
- Attack 6 (in-range LIT101 spoofing) is already not localised by the detector, so the LLM cannot make it up.

### 4.3 Confidence is too high

The LLM gives "high" in 8 of 10 events. The text of events 1 and 7 still contains uncertainty (for example event 1 admits that the FIT101 baselines disagree). The confidence is driven more by the time match than by the strength of the evidence.

### 4.4 Other

- In event 7 the `category_label` keeps the classifier's "standby activation" while the text says "not a standby-pump attack".
- Events 4, 5 and 6 are merged events (several attacks or the tail of the previous attack). The LLM covers only part of them; this is an event-segmentation issue in the detection layer.

## 5. Suggested next steps (by value)

1. Remove the clock times from the catalog and rerun the LLM to quantify the time leak (done, section 7).
2. Fix the descriptions in `tags.py` and `02_tag_dictionary.md` that disagree with the official PDF, then rerun (fixed; the rerun is still to do).
3. Improve retrieval: retrieve attack chunks by the affected tags of the event (event 5 should have retrieved attack 5).
4. Constrain the LLM's confidence with rules, for example a time match does not count as evidence, or calibrate with the number of consistent evidence items.
5. Run an automatic faithfulness check on the LLM output (the number comparison used here could become a script in `scripts/`).

## 6. Limitations

- One run, one detector (WinAE), one dataset; LLM output is random and was not repeated.
- Whether a category is right is my own judgement of the text, not an automatic evaluation.
- The number check only covers numbers, not whether the meaning is distorted.

## 7. Follow-up experiment: rerun without the attack times in the knowledge base

Method: copy the knowledge base and change "Time in data: 13:24:50 to 13:30:30 (341 s)" in the attack catalog to "Duration: 341 s", and drop the sentence about the time offset. Everything else (attack mechanism, affected tags, observed effect) is unchanged. Then call Claude 10 times again. The result is in `outputs/explanations/a12_A11-A10_noAIT__WinAE.json`; the first run with times is in `timed_...json`.

| Item | With times | Without times |
|---|---|---|
| Events whose explanation cites the catalog time window | 5 events, 18 mentions | essentially 0 |
| "Most similar attack" found (events 0, 1, 3, 4, 6, 7, 8, 9) | all correct | **all correct, unchanged** |
| Confidence distribution | high 8, low 2 | **high 5, medium 3, low 2** |
| 5 metrics in the evaluation table | 0.7 / 0.9 / 0.7 / 0.8 / 0.5 | same (these metrics do not measure the LLM text) |

**Conclusions:**
1. **Without the times the LLM still recognises the same attacks.** It switches to evidence from the data itself: LIT101 constant at 400 mm with 74% flat steps in event 4, DPIT301 constant at 45 kPa with pump off and flow 0 in event 8, about 32 direction changes per minute of LIT601 in event 9. So the time leak of section 4.1 did not prop up the LLM's recognition; a large part of it comes from the data.
2. **Confidence dropped**: events 0, 1 and 7 went from high to medium, which fits the strength of the evidence better and shows that part of the earlier "high" came from the time match.
3. **The weak spot of event 5 remains**: the LLM writes "no close known attack" and still does not find attack 5. The reason is that retrieval did not give it the attack 5 chunk, regardless of times.
4. **The label of event 1 is more conservative**: it keeps the classifier's `out_of_range_excursion` and adds "possibly stage 1 actuator manipulation", a bit weaker than the plain "actuator manipulation" of the run with times, but the mechanism explanation (MV101 open, P101 stopped, T101 overflow) is still there.
5. Only 10 events and one run, and the LLM is random, so these are directional conclusions, not statistically significant ones.
