# SWaT tag dictionary (2026 tag names)

Generated from SWaT.A11 normal operation (19-20 Feb 2026, start-up excluded) by scripts/build_kb.py. Ranges are the 1st-99th percentile of normal data. Descriptions follow public SWaT documentation; (?) marks items to confirm with iTrust.

## P1_STATE (P1_STATE)
Tag P1_STATE belongs to stage P1 (raw water supply). Type: state. Meaning: PLC state machine of stage P1. Unit: code.
Values observed in normal operation: 2 (92%), 3 (8%).

## LIT101 (LIT101.Pv)
Tag LIT101 belongs to stage P1 (raw water supply). Type: sensor. Meaning: Raw water tank T101 level. Unit: mm.
Normal range 486 to 826 mm, median 768, min 480, max 827, std 111.

## FIT101 (FIT101.Pv)
Tag FIT101 belongs to stage P1 (raw water supply). Type: sensor. Meaning: Raw water inflow to T101. Unit: m3/h.
Normal range 0 to 2.57 m3/h, median 0, min 0, max 2.62, std 0.878.

## MV101 (MV101.Status)
Tag MV101 belongs to stage P1 (raw water supply). Type: actuator. Meaning: Raw water inlet valve to T101. Unit: status.
Values observed in normal operation: 0 (0%), 1 (86%), 2 (13%).

## P101 (P101.Status)
Tag P101 belongs to stage P1 (raw water supply). Type: actuator. Meaning: Raw water transfer pump (duty) P1->P2. Unit: status.
Values observed in normal operation: 1 (59%), 2 (41%).

## P102 (P102.Status)
Tag P102 belongs to stage P1 (raw water supply). Type: actuator. Meaning: Raw water transfer pump (standby). Unit: status.
Values observed in normal operation: 1 (100%).
P102 never changes in normal operation; any change is suspicious (standby or unused equipment activated).

## P2_STATE (P2_STATE)
Tag P2_STATE belongs to stage P2 (chemical dosing). Type: state. Meaning: PLC state machine of stage P2. Unit: code.
Values observed in normal operation: 2 (100%).
P2_STATE never changes in normal operation; any change is suspicious (standby or unused equipment activated).

## FIT201 (FIT201.Pv)
Tag FIT201 belongs to stage P2 (chemical dosing). Type: sensor. Meaning: Flow through chemical dosing section. Unit: m3/h.
Normal range 0 to 2.39 m3/h, median 0, min 0, max 2.42, std 1.16.

## AIT201 (AIT201.Pv)
Tag AIT201 belongs to stage P2 (chemical dosing). Type: sensor. Meaning: Conductivity analyser after dosing (NaCl). Unit: uS/cm.
Normal range 30.2 to 89.6 uS/cm, median 67.3, min 29.7, max 92.1, std 16.5.
Water-quality analyser: drifts from day to day and week to week; a moderate shift alone is weak evidence of an attack.

## AIT202 (AIT202.Pv)
Tag AIT202 belongs to stage P2 (chemical dosing). Type: sensor. Meaning: pH analyser (HCl dosing). Unit: pH.
Normal range 9.2 to 10.8 pH, median 10.2, min 8.99, max 10.9, std 0.343.
Water-quality analyser: drifts from day to day and week to week; a moderate shift alone is weak evidence of an attack.

## AIT203 (AIT203.Pv)
Tag AIT203 belongs to stage P2 (chemical dosing). Type: sensor. Meaning: ORP analyser (NaOCl dosing). Unit: mV.
Normal range 114 to 174 mV, median 133, min 113, max 182, std 12.1.
Water-quality analyser: drifts from day to day and week to week; a moderate shift alone is weak evidence of an attack.

## MV201 (MV201.Status)
Tag MV201 belongs to stage P2 (chemical dosing). Type: actuator. Meaning: Valve from dosing section to UF feed tank T301. Unit: status.
Values observed in normal operation: 0 (1%), 1 (59%), 2 (41%).

## P201 (P201.Status)
Tag P201 belongs to stage P2 (chemical dosing). Type: actuator. Meaning: NaCl dosing pump (duty). Unit: status.
Values observed in normal operation: 1 (60%), 2 (40%).

## P202 (P202.Status)
Tag P202 belongs to stage P2 (chemical dosing). Type: actuator. Meaning: NaCl dosing pump (standby). Unit: status.
Values observed in normal operation: 1 (100%).
P202 never changes in normal operation; any change is suspicious (standby or unused equipment activated).

## P203 (P203.Status)
Tag P203 belongs to stage P2 (chemical dosing). Type: actuator. Meaning: HCl dosing pump (duty). Unit: status.
Values observed in normal operation: 1 (60%), 2 (40%).

## P204 (P204.Status)
Tag P204 belongs to stage P2 (chemical dosing). Type: actuator. Meaning: HCl dosing pump (standby). Unit: status.
Values observed in normal operation: 1 (100%).
P204 never changes in normal operation; any change is suspicious (standby or unused equipment activated).

## P205 (P205.Status)
Tag P205 belongs to stage P2 (chemical dosing). Type: actuator. Meaning: NaOCl dosing pump (duty). Unit: status.
Values observed in normal operation: 1 (79%), 2 (21%).

## P206 (P206.Status)
Tag P206 belongs to stage P2 (chemical dosing). Type: actuator. Meaning: NaOCl dosing pump (standby). Unit: status.
Values observed in normal operation: 1 (100%).
P206 never changes in normal operation; any change is suspicious (standby or unused equipment activated).

## P207 (P207.Status)
Tag P207 belongs to stage P2 (chemical dosing). Type: actuator. Meaning: NaOCl dosing pump for UF cleaning (duty). Unit: status.
Values observed in normal operation: 1 (100%).
P207 never changes in normal operation; any change is suspicious (standby or unused equipment activated).

## P208 (P208.Status)
Tag P208 belongs to stage P2 (chemical dosing). Type: actuator. Meaning: NaOCl dosing pump for UF cleaning (standby). Unit: status.
Values observed in normal operation: 1 (100%).
P208 never changes in normal operation; any change is suspicious (standby or unused equipment activated).

## LS201 (LS201.Alarm)
Tag LS201 belongs to stage P2 (chemical dosing). Type: alarm. Meaning: NaCl tank level switch. Unit: alarm.
Values observed in normal operation: 0 (100%).
LS201 never changes in normal operation; any change is suspicious (standby or unused equipment activated).

## LS202 (LS202.Alarm)
Tag LS202 belongs to stage P2 (chemical dosing). Type: alarm. Meaning: HCl tank level switch. Unit: alarm.
Values observed in normal operation: 0 (100%).
LS202 never changes in normal operation; any change is suspicious (standby or unused equipment activated).

## LSL203 (LSL203.Alarm)
Tag LSL203 belongs to stage P2 (chemical dosing). Type: alarm. Meaning: NaOCl tank low level switch. Unit: alarm.
Values observed in normal operation: 0 (100%).
LSL203 never changes in normal operation; any change is suspicious (standby or unused equipment activated).

## LSLL203 (LSLL203.Alarm)
Tag LSLL203 belongs to stage P2 (chemical dosing). Type: alarm. Meaning: NaOCl tank low-low level switch. Unit: alarm.
Values observed in normal operation: 1 (100%).
LSLL203 never changes in normal operation; any change is suspicious (standby or unused equipment activated).

## P3_STATE (P3_STATE)
Tag P3_STATE belongs to stage P3 (ultrafiltration (UF)). Type: state. Meaning: PLC state machine of stage P3. Unit: code.
Values observed in normal operation: 2 (0%), 3 (0%), 4 (1%), 5 (0%), 6 (0%), 7 (58%), 99 (40%).

## AIT301 (AIT301.Pv)
Tag AIT301 belongs to stage P3 (ultrafiltration (UF)). Type: sensor. Meaning: UF feed water pH (inferred, not in the official equipment list). Unit: pH.
Normal range 7.71 to 8.28 pH, median 8.07, min 7.18, max 8.32, std 0.106.
Water-quality analyser: drifts from day to day and week to week; a moderate shift alone is weak evidence of an attack.

## AIT302 (AIT302.Pv)
Tag AIT302 belongs to stage P3 (ultrafiltration (UF)). Type: sensor. Meaning: UF feed water ORP (inferred, not in the official equipment list). Unit: mV.
Normal range 111 to 204 mV, median 130, min 110, max 238, std 19.
Water-quality analyser: drifts from day to day and week to week; a moderate shift alone is weak evidence of an attack.

## AIT303 (AIT303.Pv)
Tag AIT303 belongs to stage P3 (ultrafiltration (UF)). Type: sensor. Meaning: UF feed water conductivity (inferred, not in the official equipment list). Unit: uS/cm.
Normal range 18.9 to 29.3 uS/cm, median 23, min 17.8, max 35.8, std 1.88.
Water-quality analyser: drifts from day to day and week to week; a moderate shift alone is weak evidence of an attack.

## LIT301 (LIT301.Pv)
Tag LIT301 belongs to stage P3 (ultrafiltration (UF)). Type: sensor. Meaning: UF feed tank T301 level. Unit: mm.
Normal range 794 to 1.01e+03 mm, median 946, min 789, max 1.01e+03, std 72.8.

## FIT301 (FIT301.Pv)
Tag FIT301 belongs to stage P3 (ultrafiltration (UF)). Type: sensor. Meaning: UF feed flow. Unit: m3/h.
Normal range 0 to 1.98 m3/h, median 1.77, min 0, max 2.13, std 0.872.

## DPIT301 (DPIT301.Pv)
Tag DPIT301 belongs to stage P3 (ultrafiltration (UF)). Type: sensor. Meaning: Differential pressure across the UF membrane (triggers backwash). Unit: kPa.
Normal range 2.54 to 16 kPa, median 15.7, min 2.53, max 16.1, std 6.43.

## MV301 (MV301.Status)
Tag MV301 belongs to stage P3 (ultrafiltration (UF)). Type: actuator. Meaning: UF backwash valve. Unit: status.
Values observed in normal operation: 1 (100%).
MV301 never changes in normal operation; any change is suspicious (standby or unused equipment activated).

## MV302 (MV302.Status)
Tag MV302 belongs to stage P3 (ultrafiltration (UF)). Type: actuator. Meaning: UF outlet valve to dechlorination T401. Unit: status.
Values observed in normal operation: 0 (1%), 1 (41%), 2 (58%).

## MV303 (MV303.Status)
Tag MV303 belongs to stage P3 (ultrafiltration (UF)). Type: actuator. Meaning: UF backwash drain valve. Unit: status.
Values observed in normal operation: 1 (100%).
MV303 never changes in normal operation; any change is suspicious (standby or unused equipment activated).

## MV304 (MV304.Status)
Tag MV304 belongs to stage P3 (ultrafiltration (UF)). Type: actuator. Meaning: UF drain valve. Unit: status.
Values observed in normal operation: 0 (1%), 1 (98%), 2 (2%).

## P301 (P301.Status)
Tag P301 belongs to stage P3 (ultrafiltration (UF)). Type: actuator. Meaning: UF feed pump (duty). Unit: status.
Values observed in normal operation: 1 (40%), 2 (60%).

## P302 (P302.Status)
Tag P302 belongs to stage P3 (ultrafiltration (UF)). Type: actuator. Meaning: UF feed pump (standby). Unit: status.
Values observed in normal operation: 1 (100%).
P302 never changes in normal operation; any change is suspicious (standby or unused equipment activated).

## P4_STATE (P4_STATE)
Tag P4_STATE belongs to stage P4 (dechlorination (UV + NaHSO3)). Type: state. Meaning: PLC state machine of stage P4. Unit: code.
Values observed in normal operation: 4 (100%).
P4_STATE never changes in normal operation; any change is suspicious (standby or unused equipment activated).

## LIT401 (LIT401.Pv)
Tag LIT401 belongs to stage P4 (dechlorination (UV + NaHSO3)). Type: sensor. Meaning: RO feed tank T401 level. Unit: mm.
Normal range 788 to 1e+03 mm, median 895, min 783, max 1e+03, std 62.5.

## FIT401 (FIT401.Pv)
Tag FIT401 belongs to stage P4 (dechlorination (UV + NaHSO3)). Type: sensor. Meaning: RO feed flow (after UV dechlorination). Unit: m3/h.
Normal range 1.01 to 1.04 m3/h, median 1.03, min 1, max 1.05, std 0.0087.

## AIT401 (AIT401.Pv)
Tag AIT401 belongs to stage P4 (dechlorination (UV + NaHSO3)). Type: sensor. Meaning: Hardness monitor (constant 0 in 2026, probably not connected). Unit: ppm.
Normal range 0 to 0 ppm, median 0, min 0, max 0, std 0.
AIT401 is constant in normal operation (sensor probably not connected).
Water-quality analyser: drifts from day to day and week to week; a moderate shift alone is weak evidence of an attack.

## AIT402 (AIT402.Pv)
Tag AIT402 belongs to stage P4 (dechlorination (UV + NaHSO3)). Type: sensor. Meaning: ORP analyser controlling NaHSO3 dosing. Unit: mV.
Normal range 147 to 160 mV, median 150, min 147, max 169, std 2.39.
Water-quality analyser: drifts from day to day and week to week; a moderate shift alone is weak evidence of an attack.

## P401 (P401.Status)
Tag P401 belongs to stage P4 (dechlorination (UV + NaHSO3)). Type: actuator. Meaning: RO feed pump (duty). Unit: status.
Values observed in normal operation: 2 (100%).
P401 never changes in normal operation; any change is suspicious (standby or unused equipment activated).

## P402 (P402.Status)
Tag P402 belongs to stage P4 (dechlorination (UV + NaHSO3)). Type: actuator. Meaning: RO feed pump (standby). Unit: status.
Values observed in normal operation: 1 (100%).
P402 never changes in normal operation; any change is suspicious (standby or unused equipment activated).

## P403 (P403.Status)
Tag P403 belongs to stage P4 (dechlorination (UV + NaHSO3)). Type: actuator. Meaning: NaHSO3 dosing pump (duty). Unit: status.
Values observed in normal operation: 2 (100%).
P403 never changes in normal operation; any change is suspicious (standby or unused equipment activated).

## P404 (P404.Status)
Tag P404 belongs to stage P4 (dechlorination (UV + NaHSO3)). Type: actuator. Meaning: NaHSO3 dosing pump (standby). Unit: status.
Values observed in normal operation: 1 (100%).
P404 never changes in normal operation; any change is suspicious (standby or unused equipment activated).

## UV401 (UV401.Status)
Tag UV401 belongs to stage P4 (dechlorination (UV + NaHSO3)). Type: actuator. Meaning: UV dechlorinator. Unit: status.
Values observed in normal operation: 2 (100%).
UV401 never changes in normal operation; any change is suspicious (standby or unused equipment activated).

## LS401 (LS401.Alarm)
Tag LS401 belongs to stage P4 (dechlorination (UV + NaHSO3)). Type: alarm. Meaning: NaHSO3 tank level switch. Unit: alarm.
Values observed in normal operation: 0 (100%).
LS401 never changes in normal operation; any change is suspicious (standby or unused equipment activated).

## P5_STATE (P5_STATE)
Tag P5_STATE belongs to stage P5 (reverse osmosis (RO)). Type: state. Meaning: PLC state machine of stage P5. Unit: code.
Values observed in normal operation: 12 (100%).
P5_STATE never changes in normal operation; any change is suspicious (standby or unused equipment activated).

## FIT501 (FIT501.Pv)
Tag FIT501 belongs to stage P5 (reverse osmosis (RO)). Type: sensor. Meaning: RO feed flow. Unit: m3/h.
Normal range 1.01 to 1.05 m3/h, median 1.03, min 1.01, max 1.05, std 0.00869.

## FIT502 (FIT502.Pv)
Tag FIT502 belongs to stage P5 (reverse osmosis (RO)). Type: sensor. Meaning: RO permeate flow. Unit: m3/h.
Normal range 0.681 to 0.761 m3/h, median 0.73, min 0.662, max 0.781, std 0.0171.

## FIT503 (FIT503.Pv)
Tag FIT503 belongs to stage P5 (reverse osmosis (RO)). Type: sensor. Meaning: RO reject flow. Unit: m3/h.
Normal range 0.22 to 0.228 m3/h, median 0.223, min 0.219, max 0.23, std 0.00164.

## FIT504 (FIT504.Pv)
Tag FIT504 belongs to stage P5 (reverse osmosis (RO)). Type: sensor. Meaning: RO recirculation flow. Unit: m3/h.
Normal range 0.055 to 0.0579 m3/h, median 0.0571, min 0.0541, max 0.0583, std 0.00108.

## AIT501 (AIT501.Pv)
Tag AIT501 belongs to stage P5 (reverse osmosis (RO)). Type: sensor. Meaning: RO feed pH. Unit: pH.
Normal range 9.1 to 9.32 pH, median 9.21, min 9.08, max 9.34, std 0.0517.
Water-quality analyser: drifts from day to day and week to week; a moderate shift alone is weak evidence of an attack.

## AIT502 (AIT502.Pv)
Tag AIT502 belongs to stage P5 (reverse osmosis (RO)). Type: sensor. Meaning: RO feed ORP. Unit: mV.
Normal range 234 to 250 mV, median 237, min 232, max 263, std 3.06.
Water-quality analyser: drifts from day to day and week to week; a moderate shift alone is weak evidence of an attack.

## AIT503 (AIT503.Pv)
Tag AIT503 belongs to stage P5 (reverse osmosis (RO)). Type: sensor. Meaning: RO feed conductivity. Unit: uS/cm.
Normal range 116 to 161 uS/cm, median 126, min 116, max 161, std 11.6.
Water-quality analyser: drifts from day to day and week to week; a moderate shift alone is weak evidence of an attack.

## AIT504 (AIT504.Pv)
Tag AIT504 belongs to stage P5 (reverse osmosis (RO)). Type: sensor. Meaning: RO permeate conductivity. Unit: uS/cm.
Normal range 9.81 to 15.2 uS/cm, median 11.1, min 9.54, max 15.6, std 1.35.
Water-quality analyser: drifts from day to day and week to week; a moderate shift alone is weak evidence of an attack.

## PIT501 (PIT501.Pv)
Tag PIT501 belongs to stage P5 (reverse osmosis (RO)). Type: sensor. Meaning: RO feed (high) pressure. Unit: kPa.
Normal range 242 to 247 kPa, median 244, min 241, max 248, std 1.32.

## PIT502 (PIT502.Pv)
Tag PIT502 belongs to stage P5 (reverse osmosis (RO)). Type: sensor. Meaning: RO permeate pressure. Unit: kPa.
Normal range 0 to 0 kPa, median 0, min 0, max 0, std 0.
PIT502 is constant in normal operation (sensor probably not connected).

## PIT503 (PIT503.Pv)
Tag PIT503 belongs to stage P5 (reverse osmosis (RO)). Type: sensor. Meaning: RO reject pressure. Unit: kPa.
Normal range 202 to 208 kPa, median 204, min 202, max 208, std 1.5.

## P501 (P501.Status)
Tag P501 belongs to stage P5 (reverse osmosis (RO)). Type: actuator. Meaning: RO high-pressure pump (duty). Unit: status/speed.
Values observed in normal operation: 2 (100%).
P501 never changes in normal operation; any change is suspicious (standby or unused equipment activated).

## P501 (P501.Speed)
Tag P501 belongs to stage P5 (reverse osmosis (RO)). Type: actuator. Meaning: RO high-pressure pump (duty). Unit: status/speed.
Values observed in normal operation: 10 (100%).
P501 never changes in normal operation; any change is suspicious (standby or unused equipment activated).

## P502 (P502.Status)
Tag P502 belongs to stage P5 (reverse osmosis (RO)). Type: actuator. Meaning: RO high-pressure pump (standby). Unit: status/speed.
Values observed in normal operation: 1 (100%).
P502 never changes in normal operation; any change is suspicious (standby or unused equipment activated).

## P502 (P502.Speed)
Tag P502 belongs to stage P5 (reverse osmosis (RO)). Type: actuator. Meaning: RO high-pressure pump (standby). Unit: status/speed.
Values observed in normal operation: 0 (100%).
P502 never changes in normal operation; any change is suspicious (standby or unused equipment activated).

## MV501 (MV501.Status)
Tag MV501 belongs to stage P5 (reverse osmosis (RO)). Type: actuator. Meaning: RO permeate valve (paired with MV502). Unit: status.
Values observed in normal operation: 2 (100%).
MV501 never changes in normal operation; any change is suspicious (standby or unused equipment activated).

## MV502 (MV502.Status)
Tag MV502 belongs to stage P5 (reverse osmosis (RO)). Type: actuator. Meaning: RO permeate valve (paired with MV501). Unit: status.
Values observed in normal operation: 2 (100%).
MV502 never changes in normal operation; any change is suspicious (standby or unused equipment activated).

## MV503 (MV503.Status)
Tag MV503 belongs to stage P5 (reverse osmosis (RO)). Type: actuator. Meaning: RO reject/flush valve (paired with MV504). Unit: status.
Values observed in normal operation: 1 (100%).
MV503 never changes in normal operation; any change is suspicious (standby or unused equipment activated).

## MV504 (MV504.Status)
Tag MV504 belongs to stage P5 (reverse osmosis (RO)). Type: actuator. Meaning: RO reject/flush valve (paired with MV503). Unit: status.
Values observed in normal operation: 1 (100%).
MV504 never changes in normal operation; any change is suspicious (standby or unused equipment activated).

## P6_STATE (P6_STATE)
Tag P6_STATE belongs to stage P6 (product water and UF backwash). Type: state. Meaning: PLC state machine of stage P6. Unit: code.
Values observed in normal operation: 2 (100%).
P6_STATE never changes in normal operation; any change is suspicious (standby or unused equipment activated).

## LIT601 (LIT601.Pv)
Tag LIT601 belongs to stage P6 (product water and UF backwash). Type: sensor. Meaning: RO permeate (product) tank T601 level. Unit: mm.
Normal range 75.5 to 618 mm, median 417, min 63.9, max 620, std 143.

## LIT602 (LIT602.Pv)
Tag LIT602 belongs to stage P6 (product water and UF backwash). Type: sensor. Meaning: UF backwash water tank T602 level. Unit: mm.
Normal range 561 to 568 mm, median 564, min 557, max 572, std 1.39.

## FIT601 (FIT601.Pv)
Tag FIT601 belongs to stage P6 (product water and UF backwash). Type: sensor. Meaning: UF backwash flow. Unit: m3/h.
Normal range 0 to 0 m3/h, median 0, min 0, max 6.41e-05, std 9.19e-07.

## FIT602 (FIT602.Pv)
Tag FIT602 belongs to stage P6 (product water and UF backwash). Type: sensor. Meaning: Product water outflow. Unit: m3/h.
Normal range 0.771 to 2.92 m3/h, median 0.848, min 0.748, max 2.97, std 0.78.

## P601 (P601.Status)
Tag P601 belongs to stage P6 (product water and UF backwash). Type: actuator. Meaning: RO permeate transfer pump (from T601). Unit: status.
Values observed in normal operation: 1 (81%), 2 (19%).

## P602 (P602.Status)
Tag P602 belongs to stage P6 (product water and UF backwash). Type: actuator. Meaning: UF backwash pump. Unit: status.
Values observed in normal operation: 1 (100%).
P602 never changes in normal operation; any change is suspicious (standby or unused equipment activated).

## P603 (P603.Status)
Tag P603 belongs to stage P6 (product water and UF backwash). Type: actuator. Meaning: CIP (clean-in-place) pump for UF/RO cleaning, draws from the CIP tank. Unit: status.
Values observed in normal operation: 1 (100%).
P603 never changes in normal operation; any change is suspicious (standby or unused equipment activated).

## LSH601 (LSH601.Alarm)
Tag LSH601 belongs to stage P6 (product water and UF backwash). Type: alarm. Meaning: T601 high level switch. Unit: alarm.
Values observed in normal operation: 0 (90%), 1 (10%).

## LSL601 (LSL601.Alarm)
Tag LSL601 belongs to stage P6 (product water and UF backwash). Type: alarm. Meaning: T601 low level switch. Unit: alarm.
Values observed in normal operation: 0 (100%), 1 (0%).

## LSH602 (LSH602.Alarm)
Tag LSH602 belongs to stage P6 (product water and UF backwash). Type: alarm. Meaning: T602 high level switch. Unit: alarm.
Values observed in normal operation: 1 (100%).
LSH602 never changes in normal operation; any change is suspicious (standby or unused equipment activated).

## LSL602 (LSL602.Alarm)
Tag LSL602 belongs to stage P6 (product water and UF backwash). Type: alarm. Meaning: T602 low level switch. Unit: alarm.
Values observed in normal operation: 0 (100%).
LSL602 never changes in normal operation; any change is suspicious (standby or unused equipment activated).

## LSH603 (LSH603.Alarm)
Tag LSH603 belongs to stage P6 (product water and UF backwash). Type: alarm. Meaning: CIP tank high level switch. Unit: alarm.
Values observed in normal operation: 0 (100%).
LSH603 never changes in normal operation; any change is suspicious (standby or unused equipment activated).

## LSL603 (LSL603.Alarm)
Tag LSL603 belongs to stage P6 (product water and UF backwash). Type: alarm. Meaning: CIP tank low level switch. Unit: alarm.
Values observed in normal operation: 1 (100%).
LSL603 never changes in normal operation; any change is suspicious (standby or unused equipment activated).
