# SWaT 2015: detection and explanation on 36 real attacks

Data: iTrust SWaT 2015 (A1/A2), `SWaT_Dataset_Normal_v1.xlsx` (7 days, 495,000 rows) and `SWaT_Dataset_Attack_v0.xlsx`
(449,919 rows, 35 labelled segments for 36 attacks), converted with `scripts/convert_2015_xlsx.py`. The attack list
(`List_of_attacks_Final.xlsx`) gives the tags and the action of each attack; 5 more rows have no physical impact and
no description and are not used. All 36 listed attack intervals lie inside the labelled segments of the data (alignment check).
Attacks 37-41 are dated 2015-01-02 in the list, which is a typo for 2016.

Setup: the 2015 setup of the project (train on the first 6.5 days of normal data, calibrate on the last 12 hours,
threshold = 99.5% quantile, AIT kept), one seed. Scripts: `scripts/eval_2015_explain.py` for the explanations (template backend,
`04_swat2015_attack_catalog.md` as the own catalog, A12 catalog as the second one, no attack times in the catalog).

## 1. Detection (event level, whole attack file)

| Model | AUC | Attacks detected (of 35 segments) | False-alarm events | Median delay |
|---|---|---|---|---|
| IForest | 0.84 | 19 (0.54) | 243 | 392 s |
| GMM | 0.86 | 5 (0.14) | 70 | 271 s |
| AE | 0.81 | 8 (0.23) | 108 | 162 s |
| WinAE | 0.83 | 8 (0.23) | 63 | 103 s |
| Rules only | 0.53 | 16 (0.46) | 104 | 200 s |

The detectors are much weaker than on A12 (WinAE + rules: 10 of 11 attacks): the 2015 attacks are mostly
single-sensor changes that stay in a normal range, and the evaluation covers 4 days with drift, so there are many false alarms.
No model dominates; IForest finds the most attacks and WinAE has the fewest false alarms among the neural models.

## 2. Explanations of the detected attacks

| | IForest | WinAE |
|---|---|---|
| Attacks detected | 18 of 36 | 7 of 36 |
| Attacked tag in the top 3 contributors | 0.50 | 0.29 |
| Top 3 or a new rule violation | 0.61 | 0.43 |
| Category reasonable (single-point attacks only) | 0.62 (n=13) | 0.50 (n=6) |
| Right 2015 attack among the top 2 retrieved | 0.28 | 0.14 |
| Leave-one-out: top-1 has the same category | 0.33 | 0.14 |

By true category (IForest, detected attacks): in-range sensor spoofing 3 of 3 found, actuator manipulation 3 of 5, multi-point 3 of 5,
**out-of-range sensor spoofing only 2 of 5**. The numbers per group are tiny.

These scores are clearly lower than on A12 (0.9 for the tag, 0.8-0.9 for the retrieved attack) and lower than on the
synthetic injections (0.98-1.0). Reasons: many 2015 attacks only set a value the PLC sees, so the process hardly reacts and the
model contributions point elsewhere; adjacent and overlapping attacks produce merged events; the signature classifier was designed
on A12; and the knowledge base had no 2015 information when the classifier was built.

## 3. Confidence

There are 296 alarm events for IForest and 75 for WinAE, almost all of them false alarms (the attack file lasts 4 days).

| Model, calibrated confidence | events | of which attacks |
|---|---|---|
| IForest low | 189 | 10 (5%) |
| IForest medium | 107 | 8 (7%) |
| WinAE high | 7 | 3 (43%) |
| WinAE medium | 20 | 2 (10%) |
| WinAE low | 48 | 2 (4%) |

- The calibration keeps almost every false alarm at "low" or "medium" (IForest: no "high" at all), but it only weakly separates
  attacks from false alarms: IForest "low" and "medium" have about the same attack share.
- WinAE "high" has the best attack share (3 of 7) but also 4 false alarms, so "high" is not as reliable as on the synthetic data.

## 4. Limits and what to do next

- One seed, one split, template backend only; the detectors were not tuned for 2015.
- The category sets that count as "reasonable" are my judgement, as for the synthetic data; multi-point attacks have no category check.
- The detection layer is the bottleneck here (half of the attacks are not detected, and false alarms dominate the event list).
  A 2015-specific detector setup (e.g. drift handling, alarm merging) would raise all explanation numbers.
- The explanation side could use the 36 attacks to improve the classifier, but they should not be used to tune and evaluate the same
  rules (hold out some attacks).
