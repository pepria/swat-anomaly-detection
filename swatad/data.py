"""Loading and cleaning of the SWaT recordings.

Every loader returns a DataFrame indexed by a 1-second ``DatetimeIndex`` with
numeric columns plus a few bookkeeping columns that start with ``_``:

    _label      0/1 ground truth (0 everywhere for normal-only recordings)
    _attack_id  attack identifier string ("0" = normal)
    _gap        1 where the raw row had missing values (forward-filled)
    _warmup     1 during morning start-up (RO not yet running + margin)
    _day        recording day (string) – used for per-day splits

Results are cached as parquet files in ``config.WORK_DIR / "processed"``.
Raw files are read directly from the zip archives; nothing is executed.
"""
from __future__ import annotations

import io
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from . import config as C

META = ["_label", "_attack_id", "_gap", "_warmup", "_day"]


def feature_cols(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if not c.startswith("_")]


def _cache(name: str) -> Path:
    p = C.WORK_DIR / "processed"
    p.mkdir(parents=True, exist_ok=True)
    return p / f"{name}.parquet"


def _to_numeric(df: pd.DataFrame) -> pd.DataFrame:
    df = df.replace({"Bad Input": np.nan, "Active": 1, "Inactive": 0, "True": 1, "False": 0})
    return df.apply(pd.to_numeric, errors="coerce").astype("float32")


def _clean_2026(raw: pd.DataFrame, ts: pd.Series) -> pd.DataFrame:
    df = raw.drop(columns=[c for c in C.ALL_BAD_COLS if c in raw.columns])
    df = _to_numeric(df)
    df.index = pd.DatetimeIndex(ts, name="t")
    # drop rows that are entirely missing (export truncation at the end of a file)
    df = df[~df.isna().all(axis=1)]
    gap = df.isna().any(axis=1)
    # a gap also contaminates a few seconds around it (glitches before/after the outage)
    gap = gap.rolling(31, center=True, min_periods=1).max().astype(bool)
    df = df.ffill().bfill()
    df["_gap"] = gap.astype("int8").values
    return df


def _warmup_mask(df: pd.DataFrame) -> np.ndarray:
    """1 before the RO pressure first exceeds 200 kPa each day (+ margin)."""
    mask = np.zeros(len(df), dtype="int8")
    pit = df["PIT501.Pv"].values if "PIT501.Pv" in df else df["PIT501"].values
    for day, idx in df.groupby("_day").indices.items():
        on = np.flatnonzero(pit[idx] > 200)
        first = on[0] if len(on) else len(idx)
        mask[idx[: min(len(idx), first + C.WARMUP_EXTRA_S)]] = 1
    return mask


def _finish(df: pd.DataFrame, label=None, attack=None) -> pd.DataFrame:
    df["_day"] = df.index.strftime("%Y-%m-%d")
    df["_label"] = np.zeros(len(df), "int8") if label is None else np.asarray(label, "int8")
    df["_attack_id"] = "0" if attack is None else np.asarray(attack).astype(str)
    if "_gap" not in df:
        df["_gap"] = np.int8(0)
    df["_warmup"] = _warmup_mask(df)
    return df


# --------------------------------------------------------------------------- 2026
def load_a11(refresh: bool = False) -> pd.DataFrame:
    """SWaT.A11 (19 + 20 Feb 2026), normal operation. Main training set."""
    cp = _cache("a11")
    if cp.exists() and not refresh:
        return pd.read_parquet(cp)
    parts = []
    with zipfile.ZipFile(C.A11_ZIP) as z:
        for name in sorted(n for n in z.namelist() if n.endswith(".csv")):
            raw = pd.read_csv(io.BytesIO(z.read(name)), dtype=str)
            ts = pd.to_datetime(raw.pop("t_stamp"), format="%d-%b-%Y %H:%M:%S")
            parts.append(_clean_2026(raw, ts))
    df = _finish(pd.concat(parts))
    df.to_parquet(cp)
    return df


def load_a12(refresh: bool = False) -> pd.DataFrame:
    """SWaT.A12 (11 Mar 2026): ~4.4 h normal then 11 attacks. Labels from the EDA thread."""
    cp = _cache("a12")
    if cp.exists() and not refresh:
        return pd.read_parquet(cp)
    with zipfile.ZipFile(C.A12_ZIP) as z:
        name = next(n for n in z.namelist() if n.endswith(".csv"))
        raw = pd.read_csv(io.BytesIO(z.read(name)), dtype=str)
    ts = pd.to_datetime(raw.pop("t_stamp"), format="%d-%b-%Y %H:%M:%S")
    df = _clean_2026(raw, ts)
    lab = pd.read_csv(C.A12_LABELS, dtype=str)
    lab.index = pd.to_datetime(lab["t_stamp"], format="%d-%b-%Y %H:%M:%S")
    lab = lab.reindex(df.index)
    df = _finish(df, lab["label"].fillna("0").astype(int).values, lab["attack_id"].fillna("0").values)
    df.to_parquet(cp)
    return df


def load_a10(refresh: bool = False) -> pd.DataFrame:
    """SWaT.A10 (Dec 2023, 105 h normal). First 5 h closed loop, then CrossOver with WaDi.

    The timestamps only have minute resolution; each minute has exactly 60 rows,
    so the seconds are rebuilt from the row order. Column ``_mode`` is
    'closed' or 'cross'.
    """
    cp = _cache("a10")
    if cp.exists() and not refresh:
        return pd.read_parquet(cp)
    raw = pd.read_csv(C.A10_CSV, dtype=str)
    minute = pd.to_datetime(raw.pop("t_stamp"), format="%d/%m/%Y %H:%M")
    sec = minute.groupby(minute).cumcount().clip(upper=59)
    ts = minute + pd.to_timedelta(sec, unit="s")
    df = _clean_2026(raw, ts)
    df = df[~df.index.duplicated()]
    df = _finish(df)
    df["_warmup"] = np.int8(0)  # RO runs continuously, no morning start-up
    t0 = df.index[0]
    df["_mode"] = np.where(df.index < t0 + pd.Timedelta(hours=5), "closed", "cross")
    df.to_parquet(cp)
    return df


# --------------------------------------------------------------------------- 2015
def _load_2015(path: Path) -> pd.DataFrame:
    raw = pd.read_csv(path)
    ts = pd.to_datetime(raw.pop("Timestamp"))
    label = raw.pop("label").astype(int).values
    df = raw.astype("float32")
    df.index = pd.DatetimeIndex(ts, name="t")
    df["_gap"] = np.int8(0)
    df = _finish(df, label)
    # contiguous attack segments get an id 1..N
    seg = (np.diff(np.r_[0, label]) == 1).cumsum() * label
    df["_attack_id"] = seg.astype(str)
    return df


def load_2015_normal(refresh: bool = False) -> pd.DataFrame:
    """SWaT 2015 A1 normal_v1 (7 days). The first 6 h (filling from empty tanks) are flagged as warm-up."""
    cp = _cache("s2015_normal")
    if cp.exists() and not refresh:
        return pd.read_parquet(cp)
    df = _load_2015(C.S2015_NORMAL)
    df["_warmup"] = (df.index < df.index[0] + pd.Timedelta(hours=6)).astype("int8")
    df.to_parquet(cp)
    return df


def load_2015_attack(refresh: bool = False) -> pd.DataFrame:
    """SWaT 2015 A1 attack_v0 (4 days, 36 attacks -> 35 contiguous labelled segments)."""
    cp = _cache("s2015_attack")
    if cp.exists() and not refresh:
        return pd.read_parquet(cp)
    df = _load_2015(C.S2015_ATTACK)
    df["_warmup"] = np.int8(0)
    df.to_parquet(cp)
    return df


def a12_attacks() -> pd.DataFrame:
    """Attack list (one row per attack) with absolute label start/end timestamps."""
    al = pd.read_csv(C.A12_ATTACKS, dtype={"attack_id": str})
    day = "2026-03-11 "
    al["start"] = pd.to_datetime(day + al["label_start"])
    al["end"] = pd.to_datetime(day + al["label_end"])
    return al


def segments_from_labels(df: pd.DataFrame) -> pd.DataFrame:
    """Contiguous label==1 segments -> DataFrame(event_id, start, end)."""
    y = df["_label"].values.astype(int)
    d = np.diff(np.r_[0, y, 0])
    s, e = np.flatnonzero(d == 1), np.flatnonzero(d == -1) - 1
    return pd.DataFrame({"event_id": np.arange(1, len(s) + 1).astype(str),
                         "start": df.index[s], "end": df.index[e]})
