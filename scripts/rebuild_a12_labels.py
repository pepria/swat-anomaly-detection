"""Rebuild the two A12 label files that the project needs (they are not in the repository).

    python scripts/rebuild_a12_labels.py [output dir]       # default: <SWAT_RAW_DIR>/swat_eda

* A12_attack_list.csv    one row per attack (attack_id, name, targets, label_start, label_end, seconds_in_data)
* A12_labels_shifted.csv one row per second of the A12 recording (t_stamp, label, attack_id)

Both are derived from knowledge_base/04_a12_attack_catalog.md (attack names, targets and the label
windows in data time, which already include the offset of about 25 minutes between the iTrust
information sheet and the recording) and from the timestamps of the A12 CSV. Where two attacks
overlap (6 and 7), the seconds go to the attack that started first. Expected result: 11 attacks,
3,139 attack seconds.
"""
import csv
import io
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402

from swatad import config as C  # noqa: E402

out = Path(sys.argv[1]) if len(sys.argv) > 1 else C.A12_LABELS.parent
out.mkdir(parents=True, exist_ok=True)

catalog = (C.KB_DIR / "04_a12_attack_catalog.md").read_text()
pat = re.compile(r"## A12 attack (\d+): (.+?)\nTargets: (.+?)\. Category: .+?"
                 r"Time in data: (\d\d:\d\d:\d\d) to (\d\d:\d\d:\d\d) \((\d+) s\)", re.S)
attacks = [m.groups() for m in pat.finditer(catalog)]
assert len(attacks) == 11, f"expected 11 attacks in the catalog, found {len(attacks)}"

with open(out / "A12_attack_list.csv", "w", newline="") as f:
    w = csv.writer(f, lineterminator="\n")
    w.writerow(["attack_id", "name", "targets", "label_start", "label_end", "seconds_in_data"])
    w.writerows(attacks)

with zipfile.ZipFile(C.A12_ZIP) as z:
    name = next(n for n in z.namelist() if n.endswith(".csv"))
    ts = pd.read_csv(io.BytesIO(z.read(name)), usecols=["t_stamp"], dtype=str)["t_stamp"]
t = pd.to_datetime(ts, format="%d-%b-%Y %H:%M:%S")
hms = t.dt.strftime("%H:%M:%S")
label, attack = pd.Series(0, index=t.index), pd.Series("0", index=t.index)
for aid, _, _, a, b, _ in attacks:
    m = (hms >= a) & (hms <= b) & (attack == "0")         # first attack keeps overlapping seconds
    label[m], attack[m] = 1, aid
pd.DataFrame({"t_stamp": ts, "label": label, "attack_id": attack}).to_csv(out / "A12_labels_shifted.csv", index=False)
print(f"{len(attacks)} attacks, {int(label.sum())} attack seconds -> {out}")
