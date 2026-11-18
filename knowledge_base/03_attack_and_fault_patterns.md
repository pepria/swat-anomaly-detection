# Attack and fault patterns in industrial control systems

General knowledge used to interpret anomalies. Each pattern lists the typical signature in the
data and checks an operator can do. Sources: SWaT attack lists (Goh et al. 2016; iTrust A12 info
sheet), ICS security literature (Adepu & Mathur on SWaT invariants), standard condition
monitoring practice.

## Sensor spoofing with an out-of-range constant value

Signature: one sensor jumps to a value outside its normal range and stays flat (very low
variance), while physically related sensors keep behaving normally or start drifting because the
controller reacts to the false value. Example: LIT101 forced to 400 mm while the real tank fills
up; DPIT301 forced to 45 kPa. Checks: compare with redundant measurements (flows, level of
connected tanks, pump status); inspect the field instrument locally; check PLC/HMI write logs.

## Sensor spoofing within the normal range

Signature: values stay inside the normal range, but the rate of change or the relation with
other tags is wrong (e.g. a tank level falling while the inlet valve is open and the outlet pump
is off). Only models that use temporal context or cross-sensor relations can find it. Checks:
mass balance between inflow, outflow and level; compare with the expected control response.

## Oscillating or multi-value spoofing

Signature: a sensor jumps between two or more values (e.g. 100 and 1000 mm) at a rate the
physical process cannot follow. High variance and many direction changes inside the window.
Checks: physical plausibility of the slope, sensor wiring, PLC tag writes.

## Actuator manipulation (illegal valve or pump combination)

Signature: each actuator value is legal on its own (open/closed, on/off), but the combination
never occurs in normal operation, e.g. stage-5 permeate valves closed and reject valves open at
the same time, or the raw water inlet valve open while the transfer pumps stop. Downstream flows
and levels react within seconds to minutes. Checks: HMI command history, PLC mode
(manual/auto), physical valve position indicators.

## Activation of standby or unused equipment

Signature: a pump or valve that never changes in normal operation (standby pump, bypass valve)
switches state. In SWaT 2026 this includes P102, P202, P204, P206, P302, P402, P404, P502, P602,
P603, MV301 and MV303. A rule "constant-in-normal tag changed" catches it immediately. Checks:
was maintenance planned? who issued the command? Standby dosing pumps (P202/P204/P206) are
safety critical because they change chemical dosing.

## Replay attack

Signature: sensor values are replaced by a recording of earlier normal values. Each value looks
normal and even the dynamics look normal, but they are inconsistent with current actuator states
and with other sensors (lost correlation). Checks: correlation between replayed tag and its
physically coupled tags; timestamp/sequence checks in the network.

## Sensor drift (fault)

Signature: slow monotonic deviation of one sensor away from its usual relation with the others,
over minutes to days. Typical for fouled or ageing analysers (AIT pH/ORP/conductivity probes) and
pressure transmitters. Usually not an attack. Checks: calibration date, compare with a portable
reference instrument.

## Stuck or frozen sensor (fault)

Signature: a normally varying signal becomes exactly constant (zero variance) for minutes, while
related tags continue to move. Can be a failed transmitter, a frozen PLC register or a
communication problem, and is also the effect of a constant-value spoofing attack. Checks: device
health status, communication diagnostics, compare with redundant tags.

## Increased noise (fault)

Signature: the variance of one signal increases sharply without a change in its mean. Typical of
loose wiring, electromagnetic interference, failing transmitter, air bubbles in flow meters.
Checks: wiring and grounding, instrument diagnostics.

## Spike or glitch (data quality)

Signature: one to a few samples far from the normal value, then back to normal. Often caused by
communication restarts or A/D glitches. A single spike rarely matters for the process.
Checks: look for "Bad Input" or communication errors around the same time.

## Operating-mode change (not an anomaly)

Signature: many tags of one stage change together in a way that matches a known procedure:
morning start-up (PIT501 rising from 0 to 245 kPa), UF backwash (DPIT301 square wave,
MV301-MV304 moves), CrossOver with WaDi (AIT shifts). Checks: operator log, PLC state variables
(P1_STATE ... P6_STATE).

## Attack after-effects and recovery

Signature: after an attack ends the plant needs minutes to return to normal (tank levels
returning, valves cycling, pumps restarting). Some changes can persist: in SWaT A12, P401, P403
and UV401 stayed off for the rest of the day after the first attack. Alarms during recovery are
expected and should be linked to the preceding event.
