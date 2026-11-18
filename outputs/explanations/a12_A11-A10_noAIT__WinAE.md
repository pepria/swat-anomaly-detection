# Explanations: a12_A11-A10_noAIT, detector WinAE (+rules)

Backend: template. 10 events. Ground-truth lines are added for evaluation only; the explainer never sees them.

### a12-WinAE-001  (13:25:00 - 13:32:26)

Between 13:25:00 and 13:32:26 (447 s) the WinAE detector and the rule layer flagged an anomaly in P2 (chemical dosing), P5 (reverse osmosis (RO)), P6 (product water and UF backwash); peak score 25.0x the threshold. Most likely interpretation: illegal combination of actuator states (actuator manipulation).

**Evidence**
- MV501 (RO permeate valve (paired with MV502)): values [0.0, 1.0, 2.0] (normal [0.0, 1.0, 2.0])
- LSLL203 (NaOCl tank low-low level switch): values [1.0] (normal [0.0, 1.0])
- LIT602 (UF backwash water tank T602 level): 561.5 to 577.7 mm vs normal 562 to 988.7 -> low
- Rule: P501 took value(s) [8.5600004196167] never seen in normal operation (normal [0.0, 10.0]).

**Similar known attacks:** A12 attack 5: Stage 5 valve manipulation (repeat); A12 attack 1: Stage 5 valve manipulation: MV503/504 open, MV501/502 close
**Matching pattern:** Actuator manipulation (illegal valve or pump combination)

**Relevant physical rules**
- Constant in the steady-state part of the normal A11 data (start-up excluded): P102, P2_STATE, P202, P204, P206, P207, P208, LS201, LS202, LSL203, LSLL203, MV301, MV303, P302, P4_STATE, AIT401, P401, P402, P403, P404, UV401, LS401, P5_STATE, PIT502, P501, P502, MV501, MV502, MV503, MV504, P6_STATE, P602, P603, LSH602, LSL602, LSH603, LSL603. Any change of these tags is suspicious: standby pumps, bypass valves or alarms that should stay quiet.
- In normal operation these groups are identical more than 99.9% of the time: P201, P203; P401, P403, UV401; MV501, MV502; MV503, MV504. If one member of a group differs from the others, an actuator was operated individually (manual command or attack).

**Recommended checks**
- Compare commanded and actual valve/pump positions.
- Check the PLC mode (auto/manual) and recent operator commands.
- Check downstream flows and levels for the expected reaction.

Confidence: high. Sources: 02_tag_dictionary#65, 02_tag_dictionary#24, 02_tag_dictionary#71, 02_tag_dictionary#61, 02_tag_dictionary#62, 03_attack_and_fault_patterns#4, 04_a12_attack_catalog#5, 04_a12_attack_catalog#1, 05_mined_invariants#13, 05_mined_invariants#12, 01_process_overview#7
_Ground truth (evaluation only, not given to the explainer): #1 Stage 5 valve manipulation: MV503/504 open, MV501/502 close_

### a12-WinAE-002  (14:05:09 - 14:12:00)

Between 14:05:09 and 14:12:00 (412 s) the WinAE detector and the rule layer flagged an anomaly in P1 (raw water supply), P2 (chemical dosing); peak score 2.0x the threshold. Most likely interpretation: process variable outside its normal range.

**Evidence**
- FIT201 (Flow through chemical dosing section): 0 to 2.358 m3/h vs normal 0 to 2.686 -> in-range
- P101 (Raw water transfer pump (duty) P1->P2): values [1.0, 2.0] (normal [1.0, 2.0])
- FIT101 (Raw water inflow to T101): 0 to 3.893 m3/h vs normal 0 to 5.942 -> high
- Rule: LIT101 left its normal range [408.182, 911.064] (observed 911.292 to 960.436).

**Similar known attacks:** A12 attack 2: Stage 1 flow disruption: MV101 open, P101 & P102 stop; A12 attack 6: Tank overflow via LIT101 spoofing (Schneider demo attack 01)
**Matching pattern:** Sensor spoofing with an out-of-range constant value

**Relevant physical rules**
- When P101 is ON/open (2), FIT201 is normally between 2.34 and 2.39; when P101 is OFF/closed (1), FIT201 is between 0 and 0 (effect size 12.9).
- When MV101 is ON/open (2), FIT101 is normally between 2.56 and 2.58; when MV101 is OFF/closed (1), FIT101 is between 0 and 0 (effect size 27.5).

**Recommended checks**
- Check whether a real process excursion is happening (overflow, pressure).
- Check the actuators that control this variable.

Confidence: medium. Sources: 02_tag_dictionary#8, 02_tag_dictionary#5, 02_tag_dictionary#3, 02_tag_dictionary#2, 03_attack_and_fault_patterns#1, 04_a12_attack_catalog#2, 04_a12_attack_catalog#6, 05_mined_invariants#7, 05_mined_invariants#1, 01_process_overview#2
_Ground truth (evaluation only, not given to the explainer): #2 Stage 1 flow disruption: MV101 open, P101 & P102 stop_

### a12-WinAE-003  (14:19:19 - 14:19:37)

Between 14:19:19 and 14:19:37 (19 s) the WinAE detector flagged an anomaly in P3 (ultrafiltration (UF)), P6 (product water and UF backwash); peak score 1.1x the threshold. Most likely interpretation: gradual drift or in-range deviation (drift fault or in-range spoofing).

**Evidence**
- LIT301 (UF feed tank T301 level): 818 to 828.2 mm vs normal 794.3 to 1013 -> low
- LSH601 (T601 high level switch): values [0.0] (normal [0.0, 1.0])
- FIT301 (UF feed flow): 0 to 0 m3/h vs normal 0 to 1.989 -> low

**Similar known attacks:** A12 attack 6: Tank overflow via LIT101 spoofing (Schneider demo attack 01); A12 attack 9: Forced backwash trigger via DPIT301 spoofing (Ensign pre-UAT attack 1)
**Matching pattern:** Sensor spoofing within the normal range

**Relevant physical rules**
- When MV302 is ON/open (2), FIT301 is normally between 1.76 and 1.79; when MV302 is OFF/closed (1), FIT301 is between 0 and 0.000384 (effect size 8.2).
- When MV302 is ON/open (2), LIT301 is normally between 801 and 975; when MV302 is OFF/closed (1), LIT301 is between 906 and 1.01e+03 (effect size 2.5).

**Recommended checks**
- Check the instrument calibration and compare with a reference measurement.
- Check the mass balance between inflow, outflow and level.

Confidence: low. Sources: 02_tag_dictionary#29, 02_tag_dictionary#77, 02_tag_dictionary#30, 03_attack_and_fault_patterns#2, 04_a12_attack_catalog#6, 04_a12_attack_catalog#9, 05_mined_invariants#10, 05_mined_invariants#11, 01_process_overview#4
_Ground truth (evaluation only, not given to the explainer): none (false alarm)_

### a12-WinAE-004  (14:45:26 - 14:51:21)

Between 14:45:26 and 14:51:21 (356 s) the WinAE detector and the rule layer flagged an anomaly in P2 (chemical dosing), P6 (product water and UF backwash); peak score 1.4x the threshold. Most likely interpretation: activation of standby or unused equipment.

**Evidence**
- LSH601 (T601 high level switch): values [0.0, 1.0] (normal [0.0, 1.0])
- P205 (NaOCl dosing pump (duty)): values [1.0, 2.0] (normal [1.0, 2.0])
- LIT601 (RO permeate (product) tank T601 level): 542.9 to 616.9 mm vs normal 72.48 to 617.1 -> high
- Rule: P202 took value(s) [2.0] never seen in normal operation (normal [1.0]).
- Rule: P204 took value(s) [2.0] never seen in normal operation (normal [1.0]).
- Rule: P206 took value(s) [2.0] never seen in normal operation (normal [1.0]).

**Similar known attacks:** A12 attack 3: Florida water plant scenario: dosing pump activation & sensor spoofing; A12 attack 10: Multi-value level oscillation: LIT601 spoofing (Ensign pre-UAT attack 3)
**Matching pattern:** Activation of standby or unused equipment

**Relevant physical rules**
- Constant in the steady-state part of the normal A11 data (start-up excluded): P102, P2_STATE, P202, P204, P206, P207, P208, LS201, LS202, LSL203, LSLL203, MV301, MV303, P302, P4_STATE, AIT401, P401, P402, P403, P404, UV401, LS401, P5_STATE, PIT502, P501, P502, MV501, MV502, MV503, MV504, P6_STATE, P602, P603, LSH602, LSL602, LSH603, LSL603. Any change of these tags is suspicious: standby pumps, bypass valves or alarms that should stay quiet.

**Recommended checks**
- Check the HMI/PLC command log for who switched the equipment and whether maintenance was scheduled.
- Verify physically that the standby unit is running.
- If it is a dosing pump, check chemical concentrations immediately (AIT201-203).

Confidence: medium. Sources: 02_tag_dictionary#77, 02_tag_dictionary#17, 02_tag_dictionary#70, 02_tag_dictionary#14, 03_attack_and_fault_patterns#5, 04_a12_attack_catalog#3, 04_a12_attack_catalog#10, 05_mined_invariants#13, 01_process_overview#7
_Ground truth (evaluation only, not given to the explainer): #3 Florida water plant scenario: dosing pump activation & sensor spoofing_

### a12-WinAE-005  (14:54:50 - 15:02:41)

Between 14:54:50 and 15:02:41 (472 s) the WinAE detector and the rule layer flagged an anomaly in P1 (raw water supply), P3 (ultrafiltration (UF)); peak score 2.0x the threshold. Most likely interpretation: sensor value forced outside its normal range (spoofing or stuck sensor).

**Evidence**
- LIT101 (Raw water tank T101 level): 400 to 980.8 mm vs normal 494 to 833.6 -> low
- LIT301 (UF feed tank T301 level): 809.3 to 891.7 mm vs normal 794.3 to 1013 -> low
- FIT101 (Raw water inflow to T101): 0 to 3.888 m3/h vs normal 0 to 5.942 -> high
- Rule: LIT101 left its normal range [408.182, 911.064] (observed 400.0 to 980.769).

**Similar known attacks:** A12 attack 4: Tank overflow via LIT101 spoofing (Schneider demo attack 01); A12 attack 9: Forced backwash trigger via DPIT301 spoofing (Ensign pre-UAT attack 1)
**Matching pattern:** Sensor spoofing with an out-of-range constant value

**Relevant physical rules**
- When MV101 is ON/open (2), FIT101 is normally between 2.56 and 2.58; when MV101 is OFF/closed (1), FIT101 is between 0 and 0 (effect size 27.5).
- When MV302 is ON/open (2), LIT301 is normally between 801 and 975; when MV302 is OFF/closed (1), LIT301 is between 906 and 1.01e+03 (effect size 2.5).

**Recommended checks**
- Compare the reading with physically related tags (flows, connected tank levels, pump states).
- Inspect the transmitter locally and check PLC register writes.
- Put the affected control loop in manual if the value drives an actuator.

Confidence: medium. Sources: 02_tag_dictionary#2, 02_tag_dictionary#29, 02_tag_dictionary#3, 03_attack_and_fault_patterns#1, 04_a12_attack_catalog#4, 04_a12_attack_catalog#9, 05_mined_invariants#1, 05_mined_invariants#11, 01_process_overview#2
_Ground truth (evaluation only, not given to the explainer): #3 Florida water plant scenario: dosing pump activation & sensor spoofing; #4 Tank overflow via LIT101 spoofing (Schneider demo attack 01)_

### a12-WinAE-006  (15:04:55 - 15:12:16)

Between 15:04:55 and 15:12:16 (442 s) the WinAE detector and the rule layer flagged an anomaly in P2 (chemical dosing), P5 (reverse osmosis (RO)); peak score 24.8x the threshold. Most likely interpretation: sensor value forced outside its normal range (spoofing or stuck sensor).

**Evidence**
- MV501 (RO permeate valve (paired with MV502)): values [0.0, 1.0, 2.0] (normal [0.0, 1.0, 2.0])
- FIT504 (RO recirculation flow): 0.0176 to 0.0717 m3/h vs normal 0.0211 to 0.0576 -> high
- LSLL203 (NaOCl tank low-low level switch): values [1.0] (normal [0.0, 1.0])
- Rule: P501 took value(s) [8.760000228881836] never seen in normal operation (normal [0.0, 10.0]).
- Rule: FIT504 left its normal range [-0.012, 0.07] (observed 0.07 to 0.072).

**Similar known attacks:** A12 attack 4: Tank overflow via LIT101 spoofing (Schneider demo attack 01); A12 attack 9: Forced backwash trigger via DPIT301 spoofing (Ensign pre-UAT attack 1)
**Matching pattern:** Sensor spoofing with an out-of-range constant value

**Relevant physical rules**
- Constant in the steady-state part of the normal A11 data (start-up excluded): P102, P2_STATE, P202, P204, P206, P207, P208, LS201, LS202, LSL203, LSLL203, MV301, MV303, P302, P4_STATE, AIT401, P401, P402, P403, P404, UV401, LS401, P5_STATE, PIT502, P501, P502, MV501, MV502, MV503, MV504, P6_STATE, P602, P603, LSH602, LSL602, LSH603, LSL603. Any change of these tags is suspicious: standby pumps, bypass valves or alarms that should stay quiet.
- In normal operation these groups are identical more than 99.9% of the time: P201, P203; P401, P403, UV401; MV501, MV502; MV503, MV504. If one member of a group differs from the others, an actuator was operated individually (manual command or attack).

**Recommended checks**
- Compare the reading with physically related tags (flows, connected tank levels, pump states).
- Inspect the transmitter locally and check PLC register writes.
- Put the affected control loop in manual if the value drives an actuator.

Confidence: high. Sources: 02_tag_dictionary#65, 02_tag_dictionary#53, 02_tag_dictionary#24, 02_tag_dictionary#61, 02_tag_dictionary#62, 03_attack_and_fault_patterns#1, 04_a12_attack_catalog#4, 04_a12_attack_catalog#9, 05_mined_invariants#13, 05_mined_invariants#12, 01_process_overview#6
_Ground truth (evaluation only, not given to the explainer): #4 Tank overflow via LIT101 spoofing (Schneider demo attack 01); #5 Stage 5 valve manipulation (repeat)_

### a12-WinAE-007  (15:25:19 - 15:31:40)

Between 15:25:19 and 15:31:40 (382 s) the WinAE detector and the rule layer flagged an anomaly in P1 (raw water supply), P2 (chemical dosing), P3 (ultrafiltration (UF)), P4 (dechlorination (UV + NaHSO3)); peak score 1.6x the threshold. Most likely interpretation: activation of standby or unused equipment.

**Evidence**
- LIT301 (UF feed tank T301 level): 913.3 to 981.4 mm vs normal 794.3 to 1013 -> in-range
- P205 (NaOCl dosing pump (duty)): values [1.0, 2.0] (normal [1.0, 2.0])
- LIT401 (RO feed tank T401 level): 812.5 to 865.4 mm vs normal 788.4 to 1001 -> low
- Rule: P102 took value(s) [2.0] never seen in normal operation (normal [1.0]).

**Similar known attacks:** A12 attack 7: Stage 2 parallel pump override: MV201 open, P101 & P102 run; A12 attack 3: Florida water plant scenario: dosing pump activation & sensor spoofing
**Matching pattern:** Activation of standby or unused equipment

**Relevant physical rules**
- When MV302 is ON/open (2), LIT301 is normally between 801 and 975; when MV302 is OFF/closed (1), LIT301 is between 906 and 1.01e+03 (effect size 2.5).

**Recommended checks**
- Check the HMI/PLC command log for who switched the equipment and whether maintenance was scheduled.
- Verify physically that the standby unit is running.
- If it is a dosing pump, check chemical concentrations immediately (AIT201-203).

Confidence: medium. Sources: 02_tag_dictionary#29, 02_tag_dictionary#17, 02_tag_dictionary#39, 02_tag_dictionary#6, 03_attack_and_fault_patterns#5, 04_a12_attack_catalog#7, 04_a12_attack_catalog#3, 05_mined_invariants#11, 01_process_overview#2
_Ground truth (evaluation only, not given to the explainer): #6 Tank overflow via LIT101 spoofing (Schneider demo attack 01); #7 Stage 2 parallel pump override: MV201 open, P101 & P102 run_

### a12-WinAE-008  (15:45:01 - 15:55:01)

Between 15:45:01 and 15:55:01 (601 s) the WinAE detector and the rule layer flagged an anomaly in P3 (ultrafiltration (UF)), P6 (product water and UF backwash); peak score 7.3x the threshold. Most likely interpretation: activation of standby or unused equipment.

**Evidence**
- DPIT301 (Differential pressure across the UF membrane (triggers backwash)): 0.0064 to 20.56 kPa vs normal 2.58 to 16.22 -> low
- P301 (UF feed pump (duty)): values [1.0, 2.0] (normal [1.0, 2.0])
- FIT301 (UF feed flow): 0 to 2.27 m3/h vs normal 0 to 1.989 -> low
- Rule: P3_STATE took value(s) [9.0, 10.0, 12.0, 14.0, 15.0, 16.0] never seen in normal operation (normal [2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 99.0]).
- Rule: MV301 took value(s) [0.0, 2.0] never seen in normal operation (normal [1.0]).
- Rule: MV303 took value(s) [0.0, 2.0] never seen in normal operation (normal [1.0]).
- Rule: P602 took value(s) [2.0] never seen in normal operation (normal [1.0]).
- Rule: DPIT301 left its normal range [-0.256, 19.239] (observed 19.291 to 20.555).
- Rule: FIT601 left its normal range [-0.001, 0.003] (observed 0.004 to 1.784).

**Similar known attacks:** A12 attack 8: RO backwash diversion: MV302 close, MV303 open; A12 attack 9: Forced backwash trigger via DPIT301 spoofing (Ensign pre-UAT attack 1)
**Matching pattern:** Activation of standby or unused equipment

**Relevant physical rules**
- When P301 is ON/open (2), FIT301 is normally between 1.76 and 1.79; when P301 is OFF/closed (1), FIT301 is between 0 and 0.000256 (effect size 14.1).
- When P301 is ON/open (2), DPIT301 is normally between 15.5 and 15.9; when P301 is OFF/closed (1), DPIT301 is between 2.55 and 2.67 (effect size 9.3).

**Recommended checks**
- Check the HMI/PLC command log for who switched the equipment and whether maintenance was scheduled.
- Verify physically that the standby unit is running.
- If it is a dosing pump, check chemical concentrations immediately (AIT201-203).

Confidence: high. Sources: 02_tag_dictionary#31, 02_tag_dictionary#36, 02_tag_dictionary#30, 02_tag_dictionary#25, 03_attack_and_fault_patterns#5, 04_a12_attack_catalog#8, 04_a12_attack_catalog#9, 05_mined_invariants#6, 05_mined_invariants#9, 01_process_overview#4
_Ground truth (evaluation only, not given to the explainer): #8 RO backwash diversion: MV302 close, MV303 open_

### a12-WinAE-009  (16:09:52 - 16:16:39)

Between 16:09:52 and 16:16:39 (408 s) the WinAE detector and the rule layer flagged an anomaly in P3 (ultrafiltration (UF)); peak score 7.7x the threshold. Most likely interpretation: sensor value forced outside its normal range (spoofing or stuck sensor).

**Evidence**
- DPIT301 (Differential pressure across the UF membrane (triggers backwash)): 3.124 to 45 kPa vs normal 2.58 to 16.22 -> high
- FIT301 (UF feed flow): 0 to 0.0004 m3/h vs normal 0 to 1.989 -> low
- P301 (UF feed pump (duty)): values [1.0] (normal [1.0, 2.0])
- Rule: DPIT301 left its normal range [-0.256, 19.239] (observed 45.0 to 45.0).

**Similar known attacks:** A12 attack 9: Forced backwash trigger via DPIT301 spoofing (Ensign pre-UAT attack 1); A12 attack 4: Tank overflow via LIT101 spoofing (Schneider demo attack 01)
**Matching pattern:** Sensor spoofing with an out-of-range constant value

**Relevant physical rules**
- When P301 is ON/open (2), FIT301 is normally between 1.76 and 1.79; when P301 is OFF/closed (1), FIT301 is between 0 and 0.000256 (effect size 14.1).
- When P301 is ON/open (2), DPIT301 is normally between 15.5 and 15.9; when P301 is OFF/closed (1), DPIT301 is between 2.55 and 2.67 (effect size 9.3).

**Recommended checks**
- Compare the reading with physically related tags (flows, connected tank levels, pump states).
- Inspect the transmitter locally and check PLC register writes.
- Put the affected control loop in manual if the value drives an actuator.

Confidence: high. Sources: 02_tag_dictionary#31, 02_tag_dictionary#30, 02_tag_dictionary#36, 03_attack_and_fault_patterns#1, 04_a12_attack_catalog#9, 04_a12_attack_catalog#4, 05_mined_invariants#6, 05_mined_invariants#9, 01_process_overview#4
_Ground truth (evaluation only, not given to the explainer): #9 Forced backwash trigger via DPIT301 spoofing (Ensign pre-UAT attack 1)_

### a12-WinAE-010  (16:35:38 - 16:39:52)

Between 16:35:38 and 16:39:52 (255 s) the WinAE detector and the rule layer flagged an anomaly in P2 (chemical dosing), P6 (product water and UF backwash); peak score 1.1x the threshold. Most likely interpretation: oscillating / multi-value sensor values (spoofing or noise).

**Evidence**
- LIT601 (RO permeate (product) tank T601 level): 100 to 1000 mm vs normal 72.48 to 617.1 -> high
- MV201 (Valve from dosing section to UF feed tank T301): values [0.0, 1.0, 2.0] (normal [0.0, 1.0, 2.0])
- FIT201 (Flow through chemical dosing section): 0 to 2.363 m3/h vs normal 0 to 2.686 -> high
- Rule: LIT601 left its normal range [-54.505, 735.036] (observed 800.0 to 1000.0).

**Similar known attacks:** A12 attack 10: Multi-value level oscillation: LIT601 spoofing (Ensign pre-UAT attack 3); A12 attack 3: Florida water plant scenario: dosing pump activation & sensor spoofing
**Matching pattern:** Oscillating or multi-value spoofing

**Relevant physical rules**
- When MV201 is ON/open (2), FIT201 is normally between 2.34 and 2.39; when MV201 is OFF/closed (1), FIT201 is between 0 and 0 (effect size 16.4).
- When P101 is ON/open (2), FIT201 is normally between 2.34 and 2.39; when P101 is OFF/closed (1), FIT201 is between 0 and 0 (effect size 12.9).

**Recommended checks**
- Check whether the rate of change is physically possible for the tank/process.
- Inspect wiring, grounding and PLC tag writes.

Confidence: medium. Sources: 02_tag_dictionary#70, 02_tag_dictionary#12, 02_tag_dictionary#8, 03_attack_and_fault_patterns#3, 04_a12_attack_catalog#10, 04_a12_attack_catalog#3, 05_mined_invariants#5, 05_mined_invariants#7, 01_process_overview#3
_Ground truth (evaluation only, not given to the explainer): #10 Multi-value level oscillation: LIT601 spoofing (Ensign pre-UAT attack 3)_
