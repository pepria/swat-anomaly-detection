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
| AE | 0.82 | 6 (0.17) | 96 | 132 s |
| WinAE | 0.83 | 7 (0.20) | 51 | 71 s |
| Rules only | 0.53 | 16 (0.46) | 104 | 200 s |

(Numbers after the code-review fixes; the neural models changed slightly, e.g. WinAE 8 -> 7 attacks and 63 -> 51 false alarms.)
The detectors are much weaker than on A12 (WinAE + rules: 10 of 11 attacks): the 2015 attacks are mostly
single-sensor changes that stay in a normal range, and the evaluation covers 4 days with drift, so there are many false alarms.
No model dominates; IForest finds the most attacks and WinAE has the fewest false alarms among the neural models.

## 2. Explanations of the detected attacks

| | IForest | WinAE |
|---|---|---|
| Attacks detected | 18 of 36 | 6 of 36 |
| Attacked tag in the top 3 contributors | 0.50 | 0.33 |
| Top 3 or a new rule violation | 0.61 | 0.50 |
| Category reasonable (single-point attacks only) | 0.69 (n=13) | 0.40 (n=5) |
| Right 2015 attack among the top 2 retrieved | 0.22 | 0.00 |
| Leave-one-out: top-1 has the same category | 0.28 | 0.00 |

By true category (IForest, detected attacks): in-range sensor spoofing 3 of 3 found, actuator manipulation 3 of 5, multi-point 3 of 5,
**out-of-range sensor spoofing only 2 of 5**. The WinAE numbers rest on 6 attacks and the groups are tiny.

These scores are clearly lower than on A12 (0.9 for the tag, 0.8-0.9 for the retrieved attack) and lower than on the
synthetic injections (0.97-1.0). Reasons: many 2015 attacks only set a value the PLC sees, so the process hardly reacts and the
model contributions point elsewhere; adjacent and overlapping attacks produce merged events; the signature classifier was designed
on A12; and the knowledge base had no 2015 information when the classifier was built.

## 3. Confidence

There are 296 alarm events for IForest and 63 for WinAE, almost all of them false alarms (the attack file lasts 4 days).

| Model, calibrated confidence | events | of which attacks |
|---|---|---|
| IForest low | 183 | 8 (4%) |
| IForest medium | 113 | 10 (9%) |
| WinAE high | 7 | 1 (14%) |
| WinAE medium | 14 | 3 (21%) |
| WinAE low | 42 | 2 (5%) |

- The calibration keeps almost every false alarm at "low" or "medium" (IForest: no "high" at all), but it separates attacks from
  false alarms only weakly: IForest "low" and "medium" differ by a few percentage points.
- On 2015 the WinAE "high" is not more reliable than "medium" (1 of 7 events is an attack), so the "high" level of the
  synthetic data does not carry over. Confidence should not be used to filter alarms on this dataset.

## 4. Limits and what to do next

- One seed, one split, template backend only; the detectors were not tuned for 2015.
- The category sets that count as "reasonable" are my judgement, as for the synthetic data; multi-point attacks have no category check.
- The detection layer is the bottleneck here (half of the attacks are not detected, and false alarms dominate the event list).
  A 2015-specific detector setup (e.g. drift handling, alarm merging) would raise all explanation numbers.
- The explanation side could use the 36 attacks to improve the classifier, but they should not be used to tune and evaluate the same
  rules (hold out some attacks).
