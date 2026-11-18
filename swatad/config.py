"""Paths and global settings.

All raw-data locations can be overridden with environment variables so the
project runs on any machine (e.g. your laptop) without editing code:

    SWAT_RAW_DIR   folder that holds the raw SWaT files (default: /mnt/project-files)
    SWAT_A12_ZIP   path to the A12 zip (default: <raw>/uploads/hearth/<id>)
    SWAT_WORK_DIR  where extracted / cached data is written (default: <project>/data)
"""
from __future__ import annotations

import os
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = Path(os.environ.get("SWAT_RAW_DIR", "/mnt/project-files"))
WORK_DIR = Path(os.environ.get("SWAT_WORK_DIR", PROJECT_DIR / "data"))
OUT_DIR = PROJECT_DIR / "outputs"
KB_DIR = PROJECT_DIR / "knowledge_base"

A11_ZIP = RAW_DIR / "SWaT.A11_OTDataset_Feb_26.zip"
A10_CSV = RAW_DIR / "SWaT.A10_Dec 2023 Historian Data.csv"
A12_ZIP = Path(os.environ.get(
    "SWAT_A12_ZIP", RAW_DIR / "uploads/hearth/b33e8669-1a9c-43e5-9993-8b6d0cefb622"))
A12_LABELS = RAW_DIR / "swat_eda/A12_labels_shifted.csv"
A12_ATTACKS = RAW_DIR / "swat_eda/A12_attack_list.csv"
S2015_NORMAL = RAW_DIR / "swat2015_csv/SWaT2015_normal_v1.csv"
S2015_ATTACK = RAW_DIR / "swat2015_csv/SWaT2015_attack_v0.csv"

SEED = 42

# Columns that are "Bad Input" for the whole recording in every 2026 file.
ALL_BAD_COLS = ["PSH301.Alarm", "DPSH301.Alarm", "PSH501.Alarm", "PSL501.Alarm"]

# Exact / near-exact duplicates found in the EDA (keep the first of each group).
REDUNDANT_GROUPS = [
    ["P201.Status", "P203.Status"],
    ["P401.Status", "P403.Status", "UV401.Status"],
    ["MV501.Status", "MV502.Status"],
    ["MV503.Status", "MV504.Status"],
    ["P501.Status", "P501.Speed"],
]

# Short warm-up after the RO (stage 5) starts in the morning is dropped from training.
WARMUP_EXTRA_S = 15 * 60

# A12: the first part of the normal segment is used to re-calibrate thresholds
# ("deployment calibration"), evaluation starts after it.
A12_SKIP_UNTIL = "09:10:00"
A12_CALIB = ("09:30:00", "10:30:00")
A12_EVAL_FROM = "10:30:00"

# Event-level evaluation: an alarm up to this many seconds after an attack ends
# still counts as a detection (process recovery).
EVENT_TOLERANCE_S = 300


def ensure_dirs() -> None:
    for d in (WORK_DIR, OUT_DIR, OUT_DIR / "figures", OUT_DIR / "anomalies", OUT_DIR / "explanations"):
        d.mkdir(parents=True, exist_ok=True)
