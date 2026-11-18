# SWaT process overview

Source: public descriptions of the Secure Water Treatment (SWaT) testbed at iTrust, SUTD
(Mathur & Tippenhauer 2016, "SWaT: a water treatment testbed for research and training on ICS
security"; Goh et al. 2016, "A dataset to support research in the design of secure water
treatment systems"), plus what is visible in the 2026 data. Items marked (to confirm) are
inferred and should be checked against the official iTrust documentation once available.

## Overall layout

SWaT is a scaled-down six-stage water treatment plant producing about 5 gallons per minute of
treated water. Each stage (P1 to P6) is controlled by its own PLC, connected to a SCADA system and
a Historian that records sensor and actuator values every second. Water flows P1 -> P2 -> P3 -> P4
-> P5 -> P6; P6 sends water back for UF backwash and to the raw water tank. Tags are named
<type><stage digit><index>: LIT = level transmitter, FIT = flow transmitter, AIT = analyser
(water quality), DPIT = differential pressure, PIT = pressure, MV = motorised valve, P = pump,
UV = ultraviolet unit, LS/LSH/LSL = level switches (alarms). Actuator status: 1 = off/closed,
2 = on/open, 0 = valve in transition.

## Stage P1 raw water supply

Raw water enters tank T101 through motorised valve MV101. LIT101 measures the T101 level and
FIT101 the inflow. Pumps P101 (duty) and P102 (standby) transfer raw water to stage P2. The PLC
opens MV101 when LIT101 is low and closes it when LIT101 is high, and runs P101 when the
downstream UF feed tank T301 (LIT301) needs water. In normal 2026 operation LIT101 oscillates
between about 480 and 830 mm and the standby pump P102 is always off. Overflow risk exists if
MV101 stays open or LIT101 is spoofed low.

## Stage P2 chemical dosing

Water from P1 is chemically conditioned before ultrafiltration. Dosing pumps add sodium chloride
(NaCl, P201/P202), hydrochloric acid (HCl, P203/P204) and sodium hypochlorite (NaOCl, P205/P206);
in each pair the first pump is duty and the second standby. P207/P208 are additional dosing
pumps (to confirm). Analysers measure conductivity (AIT201), pH (AIT202) and ORP (oxidation
reduction potential, AIT203); FIT201 is the flow through the dosing section and MV201 the valve
to the UF feed tank T301. In normal 2026 data P202, P204, P206, P207 and P208 are always off.
Starting standby dosing pumps changes the chemistry (the "Florida water plant" style attack in
which a chemical dose is raised to dangerous levels).

## Stage P3 ultrafiltration (UF)

Tank T301 (level LIT301) feeds the UF unit through pumps P301 (duty) and P302 (standby).
DPIT301 is the differential pressure across the UF membrane, FIT301 the UF flow. Valves
MV301-MV304 route water for filtration, backwash and drain. When the membrane fouls, DPIT301
rises; the PLC then starts a backwash using RO permeate pumped back from P6 (P602). In the 2026
data DPIT301 is a square wave between about 2.6 kPa and 16 kPa (filtration/backwash cycles),
MV301 and MV303 are always at the same position, and AIT301-AIT303 measure water quality at the
UF stage (pH, ORP and conductivity, to confirm). Spoofing DPIT301 high forces unnecessary
backwashes; manipulating MV302/MV303 diverts water.

## Stage P4 dechlorination

Tank T401 (level LIT401) feeds the dechlorination section via P401 (duty) and P402 (standby).
The UV dechlorinator UV401 removes residual chlorine, supported by sodium bisulphite (NaHSO3)
dosing pumps P403/P404. AIT401 measures hardness (constant 0 in 2026, probably not connected),
AIT402 measures ORP, FIT401 the flow. In 2026 P401, P403 and UV401 always switch together.
Residual chlorine must be removed before RO, otherwise it damages the RO membrane; a falsely high
or low AIT402 can trigger wrong dosing.

## Stage P5 reverse osmosis (RO)

High-pressure pumps P501 (duty) and P502 (standby) push water through the RO membranes.
PIT501 is the RO feed pressure (about 245 kPa in operation), PIT502 the permeate pressure and
PIT503 the reject pressure. FIT501-FIT504 are feed, permeate, reject and recirculation flows.
AIT501 (pH), AIT502 (ORP), AIT503 (feed conductivity) and AIT504 (permeate conductivity)
monitor water quality. Valves MV501-MV504 route permeate and reject: in normal operation
MV501/MV502 and MV503/MV504 move in pairs. When the RO starts in the morning, PIT501 rises from
near 0 to about 245 kPa within seconds; the first 20 to 30 minutes are a warm-up with unusual
values. Opening MV503/MV504 while closing MV501/MV502 diverts permeate.

## Stage P6 product water and backwash

RO permeate is stored in tank T601 (level LIT601); T602 (LIT602) is the backwash water tank.
P601 sends product water out (back to the raw water tank or, in CrossOver mode, to WaDi), P602
feeds the UF backwash, P603 is a spare pump. FIT601 is the backwash flow (almost always 0 in
2026) and FIT602 a product flow with pulse-like behaviour. LSH601/LSL601 etc. are high/low level
switches. Spoofing LIT601 (for example oscillating between 100 and 1000 mm) confuses the control
of P601/P602.

## Operating modes and normal variability

- Morning start-up: the plant is started each day; the RO (P5) starts last and its first
  minutes look very different from steady state. These periods are excluded from training.
- Water-quality drift: AIT analysers (conductivity, pH, ORP) change slowly from day to day and
  week to week with the incoming water. A shift in AIT values alone is weak evidence of an
  attack.
- CrossOver mode (Dec 2023 data): SWaT exchanges water with the WaDi distribution testbed, which
  changes water chemistry (AIT302, AIT303, AIT503, AIT504 much higher) and keeps the RO running
  continuously.
- Communications glitches: a whole stage can show "Bad Input" for a few seconds when its PLC
  link drops; this is a data-quality issue, not a process anomaly.
