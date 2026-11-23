"""Convert iTrust's SWaT 2015 Excel files to the CSV layout that swatad.data expects.

    python scripts/convert_2015_xlsx.py <dir with the two xlsx> <output dir>

Reads the workbooks row by row (read-only mode, low memory) and writes
SWaT2015_normal_v1.csv and SWaT2015_attack_v0.csv with columns
Timestamp (ISO), the 51 tags (names stripped of spaces) and label (0 normal, 1 attack).
"""
import csv
import sys
from datetime import datetime
from pathlib import Path

import openpyxl

src, dst = Path(sys.argv[1]), Path(sys.argv[2])
dst.mkdir(parents=True, exist_ok=True)
JOBS = [("SWaT_Dataset_Normal_v1.xlsx", "SWaT2015_normal_v1.csv"),
        ("SWaT_Dataset_Attack_v0.xlsx", "SWaT2015_attack_v0.csv")]
for xlsx, name in JOBS:
    wb = openpyxl.load_workbook(src / xlsx, read_only=True, data_only=True)
    rows = wb.worksheets[0].iter_rows(values_only=True)
    next(rows)                                    # group row ("P1", "P2", ...)
    header = [str(c).strip() for c in next(rows)]
    n = bad = 0
    with open(dst / name, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Timestamp"] + header[1:-1] + ["label"])
        for r in rows:
            if r[0] is None or str(r[0]).strip() == "":
                continue
            try:
                t = datetime.strptime(str(r[0]).strip(), "%d/%m/%Y %I:%M:%S %p")
            except ValueError:
                bad += 1
                continue
            lab = 0 if str(r[-1]).strip().lower() == "normal" else 1
            w.writerow([t.isoformat(sep=" ")] + list(r[1:-1]) + [lab])
            n += 1
    print(f"{name}: {n} rows, {bad} unparsable timestamps", flush=True)
