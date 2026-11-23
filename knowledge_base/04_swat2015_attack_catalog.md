# Known attack catalog: SWaT 2015 (A1/A2, 28 Dec 2015 - 2 Jan 2016)

From iTrust's list of attacks of the SWaT 2015 dataset (41 attacks, 5 of them without physical impact and without description are left out). Wall-clock times are intentionally omitted; the durations are those of the list. 'Actual change' says whether the attack really changed the process or only the value seen by the PLC (sensor spoofing).

## SWaT2015 attack 1: MV-101: Open MV-101
Targets: MV101. Category: actuator manipulation. Duration: 939 s. Start state: MV-101 is closed. Actual change in the process: Yes. Intended impact: Tank overflow.

## SWaT2015 attack 2: P-102: Turn on P-102
Targets: P102. Category: standby equipment activation. Duration: 442 s. Start state: P-101 is on where as P-102 is off. Actual change in the process: Yes. Intended impact: Pipe bursts.

## SWaT2015 attack 3: LIT-101: Increase by 1 mm every second
Targets: LIT101. Category: sensor spoofing in range. Duration: 382 s. Start state: Water level between L and H. Actual change in the process: No. Intended impact: Tank Underflow; Damage P-101.

## SWaT2015 attack 4: MV-504: Open MV-504
Targets: MV504. Category: actuator manipulation. Duration: 389 s. Start state: MV-504 is closed. Actual change in the process: Yes. Intended impact: Halt RO shut down sequence; Reduce life of RO. Observed outcome: No impact.

## SWaT2015 attack 6: AIT-202: Set value of AIT-202 as 6
Targets: AIT202. Category: sensor spoofing out of range. Duration: 195 s. Start state: Value of AIT-202 is >7.05. Actual change in the process: No. Intended impact: P-203 turns off; Change in water quality. Observed outcome: Impact seen on AIT-504 after two hours at around 14:15. It increased above HH but Drainage did not start.

## SWaT2015 attack 7: LIT-301: Water level increased above HH
Targets: LIT301. Category: sensor spoofing out of range. Duration: 428 s. Start state: Water level between L and H. Actual change in the process: No. Intended impact: Stop of inflow; Tank underflow; Damage P-301.

## SWaT2015 attack 8: DPIT-301: Set value of DPIT as >40kpa
Targets: DPIT301. Category: sensor spoofing out of range. Duration: 963 s. Start state: Value of DPIT is <40kpa. Actual change in the process: No. Intended impact: Backwash process is started again and again; Normal operation stops; Decrease in water level of tank 401. Increase in water level of tank 301.

## SWaT2015 attack 10: FIT-401: Set value of FIT-401 as <0.7
Targets: FIT401. Category: sensor spoofing out of range. Duration: 160 s. Start state: Value of FIT-401 above 1. Actual change in the process: No. Intended impact: UV shutdown; P-501 turns off;. Observed outcome: UV did not shutdown; P-501 did not turn off.

## SWaT2015 attack 11: FIT-401: Set value of FIT-401 as 0
Targets: FIT401. Category: sensor spoofing out of range. Duration: 560 s. Start state: Value of FIT-401 above 1. Actual change in the process: No. Intended impact: UV shutdown; P-501 turns off;.

## SWaT2015 attack 13: MV-304: Close MV-304
Targets: MV304. Category: actuator manipulation. Duration: 232 s. Start state: MV-304 is open. Actual change in the process: Yes. Intended impact: Halt of stage 3 because change in the backwash process. Observed outcome: UF Startup did not stop because MV-304 was closed late.

## SWaT2015 attack 14: Mv-303: Do not let MV-303 open
Targets: MV303. Category: actuator manipulation. Duration: 430 s. Start state: MV-303 is closed. Actual change in the process: Yes. Intended impact: Halt of stage 3 because change in the backwash process. Observed outcome: Attack Failed because Startup sequence did not start because Tank 301 was already full.

## SWaT2015 attack 16: LIT-301: Decrease water level by 1mm each second
Targets: LIT301. Category: sensor spoofing in range. Duration: 275 s. Start state: Water level between L and H. Actual change in the process: No. Intended impact: Tank Overflow.

## SWaT2015 attack 17: MV-303: Do not let MV-303 open
Targets: MV303. Category: actuator manipulation. Duration: 716 s. Start state: Closed. Actual change in the process: Yes. Intended impact: Halt of stage 3 because change in the backwash process.

## SWaT2015 attack 19: AIT-504: Set value of AIT-504 to 16 uS/cm
Targets: AIT504. Category: sensor spoofing out of range. Duration: 258 s. Start state: Value of AIT-504 <15 uS/cm. Actual change in the process: No. Intended impact: RO shut down sequence starts after 30 minutes. Water should go to drain.. Observed outcome: RO did not shutdown; Water did not go to drain.

## SWaT2015 attack 20: AIT-504: Set value of AIT-504 to 255 uS/cm
Targets: AIT504. Category: sensor spoofing out of range. Duration: 394 s. Start state: Value of AIT-504 <15 uS/cm. Actual change in the process: No. Intended impact: RO shut down sequence starts after 30 minutes. Water should go to drain.. Observed outcome: RO did not shutdown; Water did not go to drain.

## SWaT2015 attack 21: MV-101, LIT-101: Keep MV-101 on countinuosly; Value of LIT-101 set as 700 mm
Targets: MV101, LIT101. Category: multi-point attack (actuators and sensor values). Duration: 720 s. Start state: MV-101 is open; LIT-101 between L and H. Actual change in the process: Yes. Intended impact: Tank overflow.

## SWaT2015 attack 22: UV-401, AIT-502, P-501: Stop UV-401; Value of AIT502 set as 150; Force P-501 to remain on
Targets: UV401, AIT502, P501. Category: multi-point attack (actuators and sensor values). Duration: 462 s. Start state: UV-01 is on; AIT-502 is <150; P-501 is open. Actual change in the process: Yes. Intended impact: Possible damage to RO. Observed outcome: P501 could not be kept on; Reduced output at FIT-502.

## SWaT2015 attack 23: P-602, DIT-301, MV-302: Value of DPIT-301 set to >0.4 bar; Keep MV-302 open; Keep P-602 closed
Targets: P602, DPIT301, MV302. Category: multi-point attack (actuators and sensor values). Duration: 696 s. Start state: DPIT-301 is <0.4 bar; MV-302 is on; P-602 is closed. Actual change in the process: Yes. Intended impact: System freeze.

## SWaT2015 attack 24: P-203, P-205: Turn of P-203 and P-205
Targets: P203, P205. Category: actuator manipulation. Duration: 320 s. Start state: P-203 is on; P-205 is on. Actual change in the process: Yes. Intended impact: Change in water quality. Observed outcome: Not much impact made due to closure of P-101 because tank T-101 became full.

## SWaT2015 attack 25: LIT-401, P-401: Set value of LIT-401 as 1000; P402 is kept on
Targets: LIT401, P401. Category: multi-point attack (actuators and sensor values). Duration: 611 s. Start state: Value of LIT-401 <1000; P-402 is on. Actual change in the process: Yes. Intended impact: Tank underflow.

## SWaT2015 attack 26: P-101, LIT-301: P-101 is turned on continuosly; Set value of LIT-301 as 801 mm
Targets: P101, LIT301. Category: multi-point attack (actuators and sensor values). Duration: 1444 s. Start state: P-101 is off; P-102 is on; LIT-301 is between L and H. Actual change in the process: Yes. Intended impact: Tank 101 underflow; Tank 301 overflow.

## SWaT2015 attack 27: P-302, LIT-401: Keep P-302 on contineoulsy; Value of LIT401 set as 600 mm till 1:26:01
Targets: P302, LIT401. Category: multi-point attack (actuators and sensor values). Duration: 1690 s. Start state: P302 is on, LIT401 Is between L and H. Actual change in the process: Yes. Intended impact: Tank overflow.

## SWaT2015 attack 28: P-302: Close P-302
Targets: P302. Category: actuator manipulation. Duration: 34208 s. Start state: P302 is on. Actual change in the process: Yes. Intended impact: Stop inflow of tank T-401.

## SWaT2015 attack 29: P-201, P-203, P-205: Turn on P-201; Turn on P-203; Turn on P-205
Targets: P201, P203, P205. Category: actuator manipulation. Duration: 120 s. Start state: P-201 is closed; P-203 is closed; P-205 is closed. Actual change in the process: Yes. Intended impact: Wastage of chemicals. Observed outcome: The three dosing pump did not start because of some mechanical interlock.

## SWaT2015 attack 30: LIT-101, P-101, MV-201: Turn P-101 on continuously; Turn MV-101 on continuously; Set value of LIT-101 as 700 mm; P-102 started 
Targets: LIT101, P101, MV201. Category: multi-point attack (actuators and sensor values). Duration: 1170 s. Start state: P-101 is off; MV-101 is off; MV-201 is off; LIT-101 is between L and H; LIT-301 is between L and H. Actual change in the process: Yes. Intended impact: Tank 101 underflow; Tank 301 overflow.

## SWaT2015 attack 31: LIT-401: Set LIT-401 to less than L
Targets: LIT401. Category: sensor spoofing out of range. Duration: 366 s. Start state: Water level between L and H. Actual change in the process: No. Intended impact: Tank overflow.

## SWaT2015 attack 32: LIT-301: Set LIT-301 to above HH
Targets: LIT301. Category: sensor spoofing out of range. Duration: 600 s. Start state: Water level between L and H. Actual change in the process: No. Intended impact: Tank underflow; Damage P-302.

## SWaT2015 attack 33: LIT-101: Set LIT-101 to above H
Targets: LIT101. Category: sensor spoofing out of range. Duration: 443 s. Start state: Water level between L and H. Actual change in the process: No. Intended impact: Tank underflow; Damage P-101.

## SWaT2015 attack 34: P-101: Turn P-101 off
Targets: P101. Category: actuator manipulation. Duration: 100 s. Start state: P-101 is on. Actual change in the process: Yes. Intended impact: Stops outflow. Observed outcome: Outflow did not stop because the system turned on P-102.

## SWaT2015 attack 35: P-101; P-102: Turn P-101 off; Keep P-102 off
Targets: P101, P102. Category: actuator manipulation. Duration: 480 s. Start state: P-101 is on; P-102 is off. Actual change in the process: Yes. Intended impact: Stops outflow.

## SWaT2015 attack 36: LIT-101: Set LIT-101 to less than LL
Targets: LIT101. Category: sensor spoofing out of range. Duration: 539 s. Start state: Water level between L and H. Actual change in the process: No. Intended impact: Tank overflow.

## SWaT2015 attack 37: P-501, FIT-502: Close P-501; Set value of FIT-502 to 1.29 at 11:18:36
Targets: P501, FIT502. Category: multi-point attack (actuators and sensor values). Duration: 468 s. Start state: P-501 is on; FIT-502 in normal range. Actual change in the process: No. Intended impact: Reduced output. Observed outcome: P-501 did not turn off; FIT-502 decreased to 0.8; Speed of P-501 increased to 28.50 Hz from 10 Hz during attack..

## SWaT2015 attack 38: AIT-402, AIT-502: Set value of AIT402 as 260; Set value of AIT502 to 260
Targets: AIT402, AIT502. Category: sensor spoofing out of range. Duration: 280 s. Start state: In Normal Range. Actual change in the process: No. Intended impact: Water goes to drain because of overdosing. Observed outcome: Water did not go to the drain.

## SWaT2015 attack 39: FIT-401, AIT-502: Set value of FIT-401 as 0.5; Set value of AIT-502 as 140 mV
Targets: FIT401, AIT502. Category: sensor spoofing out of range. Duration: 400 s. Start state: In Normal Range. Actual change in the process: No. Intended impact: UV will shut down and water will go to RO. Observed outcome: UV did not shutdown.

## SWaT2015 attack 40: FIT-401: Set value of FIT-401 as 0
Targets: FIT401. Category: sensor spoofing out of range. Duration: 296 s. Start state: In Normal Range. Actual change in the process: No. Intended impact: UV will shut down and water will go to RO. Observed outcome: P-402 did not close, both should be interlinked.

## SWaT2015 attack 41: LIT-301: decrease value by 0.5 mm per second
Targets: LIT301. Category: sensor spoofing in range. Duration: 1674 s. Start state: Water level between L and H. Actual change in the process: No. Intended impact: Tank overflow. Observed outcome: Rate of decrease in water level reduced after 1:33:25 PM.
