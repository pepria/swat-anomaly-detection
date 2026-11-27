"""Rebuild the per-second A12 label file that the project needs (it is not in the repository).

    python scripts/rebuild_a12_labels.py [output dir]       # default: <SWAT_RAW_DIR>/swat_eda

Reads labels/A12_attack_list.csv (the attack windows in the time of the recording) and the timestamps
of the A12 CSV, and writes A12_labels_shifted.csv (t_stamp, label, attack_id; one row per second).
Where two attacks overlap (6 and 7), the seconds go to the attack that started first. Expected
result: 11 attacks, 3,139 attack seconds. The attack times are not taken from the knowledge base.
"""
import io
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402

from swatad import config as C  # noqa: E402

out = Path(sys.argv[1]) if len(sys.argv) > 1 else C.A12_LABELS.parent
out.mkdir(parents=True, exist_ok=True)

al = pd.read_csv(C.A12_ATTACKS, dtype=str)
attacks = [(r.attack_id, r["name"], r.targets, r.label_start, r.label_end, r.seconds_in_data) for _, r in al.iterrows()]
assert len(attacks) == 11, f"expected 11 attacks in {C.A12_ATTACKS}, found {len(attacks)}"

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
