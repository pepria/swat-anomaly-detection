# Physical invariants mined from normal data (A11)

Each rule links an actuator state to the range of a physically related sensor (same or adjacent stage). Mined automatically by scripts/build_kb.py (effect size > 2.5 standard deviations). A violation means the actuator state and the measurement disagree: a spoofed sensor, a manipulated actuator, or a fault.

## Invariant MV101 -> FIT101
When MV101 is ON/open (2), FIT101 is normally between 2.56 and 2.58; when MV101 is OFF/closed (1), FIT101 is between 0 and 0 (effect size 27.5).

## Invariant MV302 -> DPIT301
When MV302 is ON/open (2), DPIT301 is normally between 15.6 and 15.9; when MV302 is OFF/closed (1), DPIT301 is between 2.55 and 3.39 (effect size 24.4).

## Invariant P203 -> FIT201
When P203 is ON/open (2), FIT201 is normally between 2.34 and 2.39; when P203 is OFF/closed (1), FIT201 is between 0 and 0 (effect size 20.6).

## Invariant P201 -> FIT201
When P201 is ON/open (2), FIT201 is normally between 2.34 and 2.39; when P201 is OFF/closed (1), FIT201 is between 0 and 0 (effect size 20.6).

## Invariant MV201 -> FIT201
When MV201 is ON/open (2), FIT201 is normally between 2.34 and 2.39; when MV201 is OFF/closed (1), FIT201 is between 0 and 0 (effect size 16.4).

## Invariant P301 -> FIT301
When P301 is ON/open (2), FIT301 is normally between 1.76 and 1.79; when P301 is OFF/closed (1), FIT301 is between 0 and 0.000256 (effect size 14.1).

## Invariant P101 -> FIT201
When P101 is ON/open (2), FIT201 is normally between 2.34 and 2.39; when P101 is OFF/closed (1), FIT201 is between 0 and 0 (effect size 12.9).

## Invariant P601 -> FIT602
When P601 is ON/open (2), FIT602 is normally between 2.73 and 2.92; when P601 is OFF/closed (1), FIT602 is between 0.782 and 0.942 (effect size 11.8).

## Invariant P301 -> DPIT301
When P301 is ON/open (2), DPIT301 is normally between 15.5 and 15.9; when P301 is OFF/closed (1), DPIT301 is between 2.55 and 2.67 (effect size 9.3).

## Invariant MV302 -> FIT301
When MV302 is ON/open (2), FIT301 is normally between 1.76 and 1.79; when MV302 is OFF/closed (1), FIT301 is between 0 and 0.000384 (effect size 8.2).

## Invariant MV302 -> LIT301
When MV302 is ON/open (2), LIT301 is normally between 801 and 975; when MV302 is OFF/closed (1), LIT301 is between 906 and 1.01e+03 (effect size 2.5).

## Actuators that always move together
In normal operation these groups are identical more than 99.9% of the time: P201, P203; P401, P403, UV401; MV501, MV502; MV503, MV504. If one member of a group differs from the others, an actuator was operated individually (manual command or attack).

## Tags that never change in normal operation
Constant in the steady-state part of the normal A11 data (start-up excluded): P102, P2_STATE, P202, P204, P206, P207, P208, LS201, LS202, LSL203, LSLL203, MV301, MV303, P302, P4_STATE, AIT401, P401, P402, P403, P404, UV401, LS401, P5_STATE, PIT502, P501, P502, MV501, MV502, MV503, MV504, P6_STATE, P602, P603, LSH602, LSL602, LSH603, LSL603. Any change of these tags is suspicious: standby pumps, bypass valves or alarms that should stay quiet.
