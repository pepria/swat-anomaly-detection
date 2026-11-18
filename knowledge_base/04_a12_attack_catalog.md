# Known attack catalog: SWaT.A12 (11 March 2026)

From the iTrust A12 dataset information sheet (attack list), with the effects observed in the data (EDA report, section 4). Times in the data are about 25 minutes later than in the sheet; the label windows below already include this shift.

## A12 attack 1: Stage 5 valve manipulation: MV503/504 open, MV501/502 close
Targets: MV501-504. Category: actuator manipulation. Time in data: 13:24:50 to 13:30:30 (341 s). Observed effect: MV501-MV504 flip at the same time (MV503/504 open, MV501/502 close) for about 5 min; RO permeate is diverted, FIT502/PIT502 react. After this attack P401, P403 and UV401 stayed off for the rest of the day.

## A12 attack 2: Stage 1 flow disruption: MV101 open, P101 & P102 stop
Targets: MV101, P101, P102. Category: actuator manipulation. Time in data: 14:04:50 to 14:10:30 (341 s). Observed effect: MV101 opens and P101 stops: raw water keeps entering T101 but is not transferred, LIT101 rises to about 960 mm (normal max about 830), overflow risk.

## A12 attack 3: Florida water plant scenario: dosing pump activation & sensor spoofing
Targets: P201-P206, MV201. Category: standby equipment activation. Time in data: 14:44:50 to 14:50:30 (341 s). Observed effect: Standby dosing pumps P202, P204 and P206 start (never on in normal operation) together with sensor spoofing: chemical overdosing scenario modelled on the 2021 Oldsmar (Florida) water plant incident.

## A12 attack 4: Tank overflow via LIT101 spoofing (Schneider demo attack 01)
Targets: LIT101. Category: sensor spoofing out of range. Time in data: 14:54:50 to 15:00:30 (341 s). Observed effect: LIT101 is frozen at 400 mm (below the normal minimum of about 480 mm); the controller keeps MV101 open and the real level reaches about 980 mm: tank overflow.

## A12 attack 5: Stage 5 valve manipulation (repeat)
Targets: MV501-504. Category: actuator manipulation. Time in data: 15:04:50 to 15:10:30 (341 s). Observed effect: Repeat of attack 1: MV501-MV504 flip together for about 5 min.

## A12 attack 6: Tank overflow via LIT101 spoofing (Schneider demo attack 01)
Targets: LIT101. Category: sensor spoofing in range. Time in data: 15:24:50 to 15:27:30 (161 s). Observed effect: LIT101 is spoofed to fall by about 77 mm in 2 minutes while staying inside the normal range; only the rate of change and the inconsistency with MV101/P101 reveal it.

## A12 attack 7: Stage 2 parallel pump override: MV201 open, P101 & P102 run
Targets: MV201, P101, P102. Category: standby equipment activation. Time in data: 15:25:00 to 15:30:30 (331 s). Observed effect: Standby pump P102 is started together with MV201 opening (parallel pump override); overlaps attack 6.

## A12 attack 8: RO backwash diversion: MV302 close, MV303 open
Targets: MV302, MV303. Category: standby equipment activation. Time in data: 15:44:50 to 15:50:30 (341 s). Observed effect: MV303 (always in the same position in normal operation) opens and MV302 closes, diverting UF backwash; valves cycle for minutes and DPIT301 behaves abnormally.

## A12 attack 9: Forced backwash trigger via DPIT301 spoofing (Ensign pre-UAT attack 1)
Targets: DPIT301. Category: sensor spoofing out of range. Time in data: 16:09:50 to 16:15:30 (341 s). Observed effect: DPIT301 is frozen at 45 kPa (normal max about 16.5 kPa), which forces the PLC to start unnecessary UF backwash cycles.

## A12 attack 10: Multi-value level oscillation: LIT601 spoofing (Ensign pre-UAT attack 3)
Targets: LIT601. Category: oscillating spoofing. Time in data: 16:34:50 to 16:40:30 (341 s). Observed effect: LIT601 jumps between about 100 and 1000 mm, faster than the tank can physically change, confusing control of P601/P602.

## A12 attack 11: AIT402 high-value spoof (script)
Targets: AIT402. Category: contextual spoofing. Time in data: 16:59:50 to 17:00:59 (70 s). Observed effect: AIT402 is forced to about 200 mV by a script. The value is similar to real AIT402 readings right after start-up, so a context-free model may miss it.
