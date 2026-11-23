# Data dictionary: every field of the raw SWaT CSV

(Chinese version: [data_dictionary_zh.md](data_dictionary_zh.md))

Source: Historian CSVs of SWaT.A10 / A11 / A12 (one row per second, 87 columns). Meanings come mainly from the official
*SWaT equipment list & glossary.pdf*, supplemented by the hand-written descriptions in `swatad/rag/tags.py`. Entries marked (?) are inferred
from the value ranges. "Normal segment" means the first 4.4 hours of A12 (before the first attack at 13:24); the value ranges are computed on it.

## Naming rules

- The part before the dot is the **tag**: `letters + stage digit + index`. The first digit is the stage (1 to 6).
- The part after the dot is the **field type**: `.Pv` (process value, sensor reading), `.Status` (actuator state), `.Alarm` (alarm / switch), `.Speed` (variable-frequency drive speed). Names ending in `_STATE` are PLC state-machine steps.
- Letters: LIT level, FIT flow, AIT water-quality analyser, DPIT differential pressure, PIT pressure, MV motorised valve, P pump, UV ultraviolet, LS/LSH/LSL/LSLL level or pressure switch (H high, L low, LL low-low).
- Actuator `.Status` encoding: **1 = off/closed, 2 = on/open, 0 = valve in transition**.

## Time column

| Field | Meaning |
|---|---|
| `t_stamp` | Record time, format `11-Mar-2026 09:00:00`, one row per second. A10 is only accurate to the minute; the code rebuilds the seconds from the row order. |

## P1 Raw water supply

| Field | Meaning | Unit / encoding | A12 normal-segment values |
|---|---|---|---|
| `P1_STATE` | Current step of the P1 PLC state machine | codes 1-3 | values 1, 2, 3 |
| `LIT101.Pv` | Raw water tank T101 level (ultrasonic, 1.8 m³ tank) | mm | 486.9 – 830.4 (mean 728.6) |
| `FIT101.Pv` | Raw water flow into T101 (electromagnetic) | m³/h | 0 – 3.92 (mean 0.466) |
| `MV101.Status` | T101 inlet motorised valve | 0 moving / 1 closed / 2 open | values 0, 1, 2 |
| `P101.Status` | Raw water transfer pump (duty, P1→P2) | 1 off / 2 on | values 1, 2 |
| `P102.Status` | Raw water transfer pump (standby) | 1 off / 2 on | value 1; **only seen during attacks:** 2 |

## P2 Chemical dosing

| Field | Meaning | Unit / encoding | A12 normal-segment values |
|---|---|---|---|
| `P2_STATE` | Step of the P2 (chemical dosing) PLC state machine | codes 1-2 | values 1, 2 |
| `FIT201.Pv` | Flow towards the UF feed tank (through the dosing section) | m³/h | 0 – 2.378 (mean 0.9594) |
| `AIT201.Pv` | Conductivity analyser (after NaCl dosing) | µS/cm | 52.55 – 118.3 (mean 87.55) |
| `AIT202.Pv` | pH analyser (HCl dosing) | pH | 8.273 – 11.06 (mean 10.32) |
| `AIT203.Pv` | ORP (redox potential) analyser (NaOCl dosing) | mV | 103.5 – 451.7 (mean 127.8) |
| `MV201.Status` | Outlet valve from the raw water tank to UF feed tank T301 | 0 moving / 1 closed / 2 open | values 0, 1, 2 |
| `P201.Status` | NaCl dosing pump (duty) | 1 off / 2 on | values 1, 2 |
| `P202.Status` | NaCl dosing pump (standby) | 1 off / 2 on | value 1; **only seen during attacks:** 2 |
| `P203.Status` | HCl dosing pump (duty) | 1 off / 2 on | values 1, 2 |
| `P204.Status` | HCl dosing pump (standby) | 1 off / 2 on | value 1; **only seen during attacks:** 2 |
| `P205.Status` | NaOCl dosing pump (duty, free available chlorine FAC) | 1 off / 2 on | values 1, 2 |
| `P206.Status` | NaOCl dosing pump (standby) | 1 off / 2 on | value 1; **only seen during attacks:** 2 |
| `P207.Status` | NaOCl dosing pump for UF cleaning (65 L/h) [official list] | 1 off / 2 on | value 1 |
| `P208.Status` | NaOCl dosing pump for UF cleaning, second unit [official list] | 1 off / 2 on | value 1 |
| `LS201.Alarm` | NaCl tank low level switch | 0/1 switch | value 0 |
| `LS202.Alarm` | HCl tank low level switch | 0/1 switch | value 0 |
| `LSL203.Alarm` | NaOCl tank low level switch | 0/1 switch | value 0 |
| `LSLL203.Alarm` | NaOCl tank low-low level switch | 0/1 switch | values 0, 1 |

## P3 Ultrafiltration (UF)

| Field | Meaning | Unit / encoding | A12 normal-segment values |
|---|---|---|---|
| `P3_STATE` | Step of the P3 (UF) PLC state machine, many values (up to 99) | codes | 1 – 99 (mean 43.18) |
| `AIT301.Pv` | UF-stage water quality, range looks like pH (not in the official list, inferred) | pH(?) | 7.66 – 8.44 (mean 8.186) |
| `AIT302.Pv` | UF-stage water quality, range looks like ORP (not in the official list, inferred) | mV(?) | 114 – 196 (mean 142.7) |
| `AIT303.Pv` | UF-stage water quality, range looks like conductivity (not in the official list, inferred) | µS/cm(?) | 28.62 – 37.13 (mean 32.63) |
| `LIT301.Pv` | UF feed tank T301 level | mm | 654.3 – 1013 (mean 920.2) |
| `FIT301.Pv` | UF feed flow | m³/h | 0 – 2.127 (mean 1.025) |
| `DPIT301.Pv` | Differential pressure across the UF membrane (too high triggers a backwash) | kPa | 2.964 – 16.59 (mean 10.49) |
| `MV301.Status` | UF backwash valve 1 | 0 moving / 1 closed / 2 open | value 1; **only seen during attacks:** 0, 2 |
| `MV302.Status` | UF backwash valve 2 (outlet to dechlorination tank T401) | 0 moving / 1 closed / 2 open | values 0, 1, 2 |
| `MV303.Status` | UF backwash valve 3 (backwash drain) | 0 moving / 1 closed / 2 open | value 1; **only seen during attacks:** 0, 2 |
| `MV304.Status` | UF backwash valve 4 (drain) | 0 moving / 1 closed / 2 open | values 0, 1, 2 |
| `P301.Status` | UF feed pump (duty) | 1 off / 2 on | values 1, 2 |
| `P302.Status` | UF feed pump (standby) | 1 off / 2 on | value 1 |
| `PSH301.Alarm` | UF high pressure switch (all Bad Input in the 2026 data) | 0/1 switch | all Bad Input (empty) |
| `DPSH301.Alarm` | UF differential pressure high switch (all Bad Input in the 2026 data) | 0/1 switch | all Bad Input (empty) |

## P4 Dechlorination

| Field | Meaning | Unit / encoding | A12 normal-segment values |
|---|---|---|---|
| `P4_STATE` | Step of the P4 (dechlorination) PLC state machine | codes 1-4 | values 1, 2, 3, 4 |
| `LIT401.Pv` | RO feed tank T401 level | mm | 783.6 – 1007 (mean 895.9) |
| `FIT401.Pv` | RO feed flow (after UV dechlorination) | m³/h | 0 – 1.058 (mean 1.017) |
| `AIT401.Pv` | Hardness monitor (0-10 ppm). Constant 0 in the 2026 data, probably not connected | ppm | value 0 |
| `AIT402.Pv` | ORP analyser (controls NaHSO3 dosing) | mV | 133.2 – 204.2 (mean 142.8) |
| `P401.Status` | RO feed pump (duty) | 1 off / 2 on | values 1, 2 |
| `P402.Status` | RO feed pump (standby) | 1 off / 2 on | value 1 |
| `P403.Status` | NaHSO3 dosing pump (duty) | 1 off / 2 on | values 1, 2 |
| `P404.Status` | NaHSO3 dosing pump (standby) | 1 off / 2 on | value 1 |
| `UV401.Status` | UV dechlorinator (removes residual chlorine) | 1 off / 2 on | values 1, 2 |
| `LS401.Alarm` | NaHSO3 tank low level switch | 0/1 switch | value 0 |

## P5 Reverse osmosis (RO)

| Field | Meaning | Unit / encoding | A12 normal-segment values |
|---|---|---|---|
| `P5_STATE` | Step of the P5 (RO) PLC state machine (1-12) | codes | 1 – 12 (mean 11.62) |
| `FIT501.Pv` | RO feed flow | m³/h | 0.002307 – 1.064 (mean 1.024) |
| `FIT502.Pv` | RO permeate flow | m³/h | 0.001793 – 0.9639 (mean 0.7276) |
| `FIT503.Pv` | RO reject (concentrate) flow | m³/h | 0.001408 – 0.2221 (mean 0.2094) |
| `FIT504.Pv` | RO recirculation flow | m³/h | 0 – 0.06546 (mean 0.06211) |
| `AIT501.Pv` | RO feed pH | pH | 8.81 – 9.472 (mean 9.353) |
| `AIT502.Pv` | RO feed ORP | mV | 226.3 – 305.6 (mean 236.5) |
| `AIT503.Pv` | RO feed conductivity (range up to 1000 µS/cm) | µS/cm | 162 – 189.4 (mean 177.6) |
| `AIT504.Pv` | RO permeate conductivity (range 0.02-20 µS/cm) | µS/cm | 16.11 – 121.7 (mean 20.33) |
| `PIT501.Pv` | RO feed pressure after the high-pressure pump (range 0-10 bar) | kPa | 6.809 – 248.1 (mean 235) |
| `PIT502.Pv` | RO permeate pressure | kPa | 0 – 3.092 (mean 0.003239) |
| `PIT503.Pv` | RO reject (concentrate) pressure | kPa | 4.55 – 208.3 (mean 196.2) |
| `P501.Status` | RO high-pressure pump (duty, with VSD) | 1 off / 2 on | values 1, 2 |
| `P501.Speed` | VSD speed reading of P501; only 0 / 8.56 / 8.76 / 10.0 occur, the official list gives no unit | number, unit unknown | values 0, 10; **only seen during attacks:** 8.56, 8.76 |
| `P502.Status` | RO high-pressure pump (standby) | 1 off / 2 on | value 1 |
| `P502.Speed` | VSD speed of the standby pump P502, always 0 | number, unit unknown | value 0 |
| `MV501.Status` | RO permeate valve (moves together with MV502) | 0 moving / 1 closed / 2 open | values 0, 1, 2 |
| `MV502.Status` | RO permeate valve (moves together with MV501) | 0 moving / 1 closed / 2 open | values 0, 1, 2 |
| `MV503.Status` | RO reject/flush valve (moves together with MV504) | 0 moving / 1 closed / 2 open | values 0, 1, 2 |
| `MV504.Status` | RO reject/flush valve (moves together with MV503) | 0 moving / 1 closed / 2 open | values 0, 1, 2 |
| `PSH501.Alarm` | High pressure switch after the high-pressure pump (all Bad Input in the 2026 data) | 0/1 switch | all Bad Input (empty) |
| `PSL501.Alarm` | Low pressure switch before the high-pressure pump (all Bad Input in the 2026 data) | 0/1 switch | all Bad Input (empty) |

## P6 Product water and UF backwash

| Field | Meaning | Unit / encoding | A12 normal-segment values |
|---|---|---|---|
| `P6_STATE` | Step of the P6 PLC state machine | codes 1-2 | values 1, 2 |
| `LIT601.Pv` | RO permeate tank T601 level (1.2 m³) | mm | 60.05 – 619.7 (mean 445.9) |
| `LIT602.Pv` | UF backwash tank T602 level | mm | 548.5 – 571.1 (mean 563.5) |
| `FIT601.Pv` | UF backwash flow, almost always 0 | m³/h | values 0, 6.40759e-05, 0.000128152 |
| `FIT602.Pv` | Product water outflow (pulse-like) | m³/h | 0.7679 – 2.999 (mean 1.194) |
| `P601.Status` | RO permeate transfer pump (sends water back to the raw water tank or to WaDi) | 1 off / 2 on | values 1, 2 |
| `P602.Status` | UF backwash pump | 1 off / 2 on | value 1; **only seen during attacks:** 2 |
| `P603.Status` | CIP (clean-in-place) pump, not a standby pump [official list] | 1 off / 2 on | value 1 |
| `LSH601.Alarm` | T601 high level switch | 0/1 switch | values 0, 1 |
| `LSL601.Alarm` | T601 low level switch | 0/1 switch | values 0, 1 |
| `LSH602.Alarm` | T602 high level switch (always 1 in A12) | 0/1 switch | value 1 |
| `LSL602.Alarm` | T602 low level switch (always 0 in A12) | 0/1 switch | value 0 |
| `LSH603.Alarm` | CIP tank high level switch (always 0 in A12) | 0/1 switch | value 0 |
| `LSL603.Alarm` | CIP tank low level switch (always 1 in A12) | 0/1 switch | value 1 |

## Helper columns added by the project (not raw data, prefixed with an underscore)

| Field | Meaning |
|---|---|
| `_label` | 0/1, whether this second is inside an attack (from the label file; all 0 for normal data) |
| `_attack_id` | Attack number, "0" means normal |
| `_gap` | 1 means this row had a missing value (Bad Input) that was forward-filled; about 15 s before and after are flagged too and excluded from training |
| `_warmup` | 1 means the morning start-up phase (until PIT501 exceeds 200 kPa, plus 15 minutes); excluded from training |
| `_day` | Date of the row, used to split by day |
| `_mode` | A10 only: `closed` (first 5 hours, closed loop) or `cross` (afterwards, CrossOver mode exchanging water with WaDi) |

## Things to watch out for when reading the data

1. **4 columns are entirely invalid**: `PSH301.Alarm`, `DPSH301.Alarm`, `PSH501.Alarm`, `PSL501.Alarm` are all `Bad Input` in every 2026 file. The code drops them, so **82 numeric columns** remain usable.
2. **Many columns are constant**: for example `AIT401.Pv` is always 0, and the standby pumps P102/P202/P204/P206/P302/P402/P404/P502, plus the pumps that normally do not run, P207/P208 (UF-cleaning dosing) and P603 (CIP pump), stay at 1 (off) in the normal segment. Any of them switching to 2 is therefore a strong anomaly signal (this is what the `unseen_state` rule catches).
3. **Some switches are constantly 1** (e.g. `LSH602`, `LSL603`). Their polarity is inverted or the sensor rests at 1; do not read them as "1 = alarm".
4. **Duplicate columns**: P201 and P203, P401/P403/UV401, MV501 and MV502, MV503 and MV504 are perfectly synchronous in A11. The code keeps only the first of each group.
5. **Water-quality AIT readings drift**: the readings shift as a whole between days and weeks, which is why the best configuration drops all AIT columns (`noAIT`).
6. **The meaning of each `_STATE` value is not documented officially.** Treat it only as "the step number the PLC is currently in".
