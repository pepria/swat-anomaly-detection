"""Build knowledge_base/04_swat2015_attack_catalog.md from iTrust's List_of_attacks_Final.xlsx
(SWaT 2015 A1/A2: 41 rows, 36 attacks with a description, 5 "no physical impact" rows without one).

    python scripts/build_2015_catalog.py path/to/List_of_attacks_Final.xlsx

Wall-clock times are NOT written to the knowledge base (they would let a retriever or an LLM
match an event by its timestamp); only the duration is kept. Categories are assigned by simple
rules from the attack point and the action text, with the same vocabulary as the A12 catalog.
"""
import re
import sys
from datetime import datetime
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
src = Path(sys.argv[1])
rows = list(openpyxl.load_workbook(src, read_only=True, data_only=True).active.iter_rows(values_only=True))[1:]

TAG = re.compile(r"\b(DPIT|DIT|LIT|FIT|AIT|PIT|MV|UV|P)\s*[-‐‑]?\s*(\d{2,3})\b", re.I)


def tags(text: str) -> list[str]:
    out = []
    for p, n in TAG.findall(text):
        p = p.upper()
        p = "DPIT" if p == "DIT" else p
        n = n if len(n) == 3 else f"{n[0]}0{n[1]}"        # UV-01 -> UV401 handled below
        t = f"{p}{n}"
        if p == "UV" and n != "401":
            t = "UV401"
        if t not in out:
            out.append(t)
    return out


def clean(s):
    return re.sub(r"\s+", " ", str(s).replace("‐", "-").replace("‑", "-")).strip() if s else ""


def category(targets, action):
    sensors = [t for t in targets if re.match(r"(LIT|FIT|AIT|DPIT|PIT)", t)]
    acts = [t for t in targets if t not in sensors]
    if sensors and acts:
        return "multi-point attack (actuators and sensor values)"
    if sensors:
        if re.search(r"by [\d.]+ ?mm", action, re.I):
            return "sensor spoofing in range"
        return "sensor spoofing out of range"
    if re.search(r"turn on", action, re.I) and any(t in ("P102", "P302", "P402", "P404", "P502") for t in acts):
        return "standby equipment activation"
    return "actuator manipulation"


def seconds(a, b):
    try:
        t0 = datetime.fromisoformat(str(a))
        h, m, s = (int(x) for x in str(b).split(":"))
        t1 = t0.replace(hour=h, minute=m, second=s)
        return int((t1 - t0).total_seconds()) % 86400
    except Exception:
        return None


out = ["# Known attack catalog: SWaT 2015 (A1/A2, 28 Dec 2015 - 2 Jan 2016)", "",
       "From iTrust's list of attacks of the SWaT 2015 dataset (41 attacks, 5 of them without physical impact "
       "and without description are left out). Wall-clock times are intentionally omitted; the durations "
       "are those of the list. 'Actual change' says whether the attack really changed the process or only "
       "the value seen by the PLC (sensor spoofing).", ""]
n = 0
for r in rows:
    if not r[0] or not str(r[0]).strip().isdigit() or not r[4]:
        continue
    i, start, end, point, state, action, actual, expected, unexpected = (clean(c) if k not in (1,) else c
                                                                        for k, c in enumerate(r[:9]))
    tg = tags(point + " " + action)
    tg = [t for t in tg if t in tags(point)] or tg
    cat = category(tg, action)
    dur = seconds(r[1], r[2])
    out += [f"## SWaT2015 attack {i}: {point}: {action}"[:150],
            f"Targets: {', '.join(tg) or point}. Category: {cat}. Duration: {dur} s. "
            f"Start state: {state}. Actual change in the process: {actual or 'unknown'}. "
            f"Intended impact: {expected or 'not stated'}."
            + (f" Observed outcome: {unexpected}." if unexpected else ""), ""]
    n += 1
dst = ROOT / "knowledge_base" / "04_swat2015_attack_catalog.md"
dst.write_text("\n".join(out))
print(f"{n} attacks written to {dst}")
