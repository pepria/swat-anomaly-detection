"""Build the data-derived parts of the RAG knowledge base from normal data (A11).

Writes knowledge_base/02_tag_dictionary.md, 04_a12_attack_catalog.md and
05_mined_invariants.md. The hand-written documents (01, 03, 06) are kept as is.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from swatad import config as C  # noqa: E402
from swatad import data as D  # noqa: E402
from swatad.features import base_tag, is_discrete, tag_kind, tag_stage  # noqa: E402
from swatad.pipeline import valid_mask  # noqa: E402
from swatad.rag.tags import STAGE_NAMES, describe  # noqa: E402

a11 = D.load_a11()
a11 = a11[valid_mask(a11)]
cols = D.feature_cols(a11)

# ------------------------------------------------------------------ tag dictionary
lines = ["# SWaT tag dictionary (2026 tag names)", "",
         "Generated from SWaT.A11 normal operation (19-20 Feb 2026, start-up excluded) by "
         "scripts/build_kb.py. Ranges are the 1st-99th percentile of normal data. Descriptions "
         "follow public SWaT documentation; (?) marks items to confirm with iTrust.", ""]
for c in cols:
    s = a11[c]
    desc, unit = describe(c)
    st = tag_stage(c)
    lines.append(f"## {base_tag(c)} ({c})")
    lines.append(f"Tag {base_tag(c)} belongs to stage {st} ({STAGE_NAMES.get(st, '?')}). "
                 f"Type: {tag_kind(c)}. Meaning: {desc}. Unit: {unit}.")
    if is_discrete(c):
        vc = s.value_counts(normalize=True).sort_index()
        vals = ", ".join(f"{v:g} ({p:.0%})" for v, p in vc.items())
        lines.append(f"Values observed in normal operation: {vals}.")
        if len(vc) == 1:
            lines.append(f"{base_tag(c)} never changes in normal operation; any change is suspicious "
                         "(standby or unused equipment activated).")
    else:
        p1, p50, p99 = s.quantile([0.01, 0.5, 0.99])
        lines.append(f"Normal range {p1:.3g} to {p99:.3g} {unit}, median {p50:.3g}, "
                     f"min {s.min():.3g}, max {s.max():.3g}, std {s.std():.3g}.")
        if s.nunique() == 1:
            lines.append(f"{base_tag(c)} is constant in normal operation (sensor probably not connected).")
        if base_tag(c).startswith("AIT"):
            lines.append("Water-quality analyser: drifts from day to day and week to week; a moderate "
                         "shift alone is weak evidence of an attack.")
    lines.append("")
(C.KB_DIR / "02_tag_dictionary.md").write_text("\n".join(lines))

# ------------------------------------------------------------------ attack catalog
OBS = {
    "1": ("actuator manipulation", "MV501-MV504 flip at the same time (MV503/504 open, MV501/502 close) "
          "for about 5 min; RO permeate is diverted, FIT502/PIT502 react. After this attack P401, P403 "
          "and UV401 stayed off for the rest of the day."),
    "2": ("actuator manipulation", "MV101 opens and P101 stops: raw water keeps entering T101 but is not "
          "transferred, LIT101 rises to about 960 mm (normal max about 830), overflow risk."),
    "3": ("standby equipment activation", "Standby dosing pumps P202, P204 and P206 start (never on in "
          "normal operation) together with sensor spoofing: chemical overdosing scenario modelled on "
          "the 2021 Oldsmar (Florida) water plant incident."),
    "4": ("sensor spoofing out of range", "LIT101 is frozen at 400 mm (below the normal minimum of about "
          "480 mm); the controller keeps MV101 open and the real level reaches about 980 mm: tank overflow."),
    "5": ("actuator manipulation", "Repeat of attack 1: MV501-MV504 flip together for about 5 min."),
    "6": ("sensor spoofing in range", "LIT101 is spoofed to fall by about 77 mm in 2 minutes while staying "
          "inside the normal range; only the rate of change and the inconsistency with MV101/P101 reveal it."),
    "7": ("standby equipment activation", "Standby pump P102 is started together with MV201 opening "
          "(parallel pump override); overlaps attack 6."),
    "8": ("standby equipment activation", "MV303 (always in the same position in normal operation) opens "
          "and MV302 closes, diverting UF backwash; valves cycle for minutes and DPIT301 behaves abnormally."),
    "9": ("sensor spoofing out of range", "DPIT301 is frozen at 45 kPa (normal max about 16.5 kPa), "
          "which forces the PLC to start unnecessary UF backwash cycles."),
    "10": ("oscillating spoofing", "LIT601 jumps between about 100 and 1000 mm, faster than the tank "
           "can physically change, confusing control of P601/P602."),
    "11": ("contextual spoofing", "AIT402 is forced to about 200 mV by a script. The value is similar "
           "to real AIT402 readings right after start-up, so a context-free model may miss it."),
}
al = D.a12_attacks()
lines = ["# Known attack catalog: SWaT.A12 (11 March 2026)", "",
         "From the iTrust A12 dataset information sheet (attack list), with the effects observed in "
         "the data (EDA report, section 4). The clock times of the attacks are deliberately not part "
         "of the knowledge base (they are in labels/A12_attack_list.csv), so that an explainer cannot "
         "identify an attack by the time of an event; only the durations are given.", ""]
for _, r in al.iterrows():
    cat, obs = OBS[str(r.attack_id)]
    lines += [f"## A12 attack {r.attack_id}: {r['name']}",
              f"Targets: {r.targets}. Category: {cat}. Duration: {r.seconds_in_data} s. "
              f"Observed effect: {obs}", ""]
(C.KB_DIR / "04_a12_attack_catalog.md").write_text("\n".join(lines))

# ------------------------------------------------------------------ mined invariants
act = [c for c in cols if tag_kind(c) == "actuator" and a11[c].isin([1, 2]).mean() > 0.99
       and a11[c].nunique() > 1]
sens = [c for c in cols if tag_kind(c) == "sensor" and a11[c].nunique() > 10]
inv = []
for a in act:
    on, off = a11[a] == 2, a11[a] == 1
    if on.mean() < 0.02 or off.mean() < 0.02:
        continue
    for s in sens:
        if abs(int(tag_stage(a)[1]) - int(tag_stage(s)[1])) > 1:
            continue
        x_on, x_off = a11.loc[on, s], a11.loc[off, s]
        pooled = np.sqrt((x_on.var() + x_off.var()) / 2) + 1e-9
        d = (x_on.mean() - x_off.mean()) / pooled
        if abs(d) > 2.5:
            inv.append((abs(d), a, s, x_on.quantile([.05, .95]).values, x_off.quantile([.05, .95]).values))
inv.sort(reverse=True)
lines = ["# Physical invariants mined from normal data (A11)", "",
         "Each rule links an actuator state to the range of a physically related sensor (same or "
         "adjacent stage). Mined automatically by scripts/build_kb.py (effect size > 2.5 standard "
         "deviations). A violation means the actuator state and the measurement disagree: a spoofed "
         "sensor, a manipulated actuator, or a fault.", ""]
for d, a, s, r_on, r_off in inv[:40]:
    lines += [f"## Invariant {base_tag(a)} -> {base_tag(s)}",
              f"When {base_tag(a)} is ON/open (2), {base_tag(s)} is normally between {r_on[0]:.3g} and "
              f"{r_on[1]:.3g}; when {base_tag(a)} is OFF/closed (1), {base_tag(s)} is between {r_off[0]:.3g} "
              f"and {r_off[1]:.3g} (effect size {d:.1f}).", ""]
groups = [", ".join(dict.fromkeys(base_tag(c) for c in g)) for g in C.REDUNDANT_GROUPS]
groups = [g for g in groups if "," in g]
lines += ["## Actuators that always move together",
          "In normal operation these groups are identical more than 99.9% of the time: "
          + "; ".join(groups) + ". If one member of a group differs from the others, an actuator was "
          "operated individually (manual command or attack).", ""]
const = list(dict.fromkeys(base_tag(c) for c in cols if a11[c].nunique() == 1))
lines += ["## Tags that never change in normal operation",
          "Constant in the steady-state part of the normal A11 data (start-up excluded): " + ", ".join(const) + ". Any change of these tags is "
          "suspicious: standby pumps, bypass valves or alarms that should stay quiet.", ""]
(C.KB_DIR / "05_mined_invariants.md").write_text("\n".join(lines))
print("invariants", len(inv), "kb files written")
