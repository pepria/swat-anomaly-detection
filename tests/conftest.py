"""Shared fixtures: a small synthetic plant recording in the 2026 column format.

The real SWaT data needs an iTrust licence, so the tests build a fake 1 Hz
recording with the same naming conventions (``LIT101.Pv``, ``P101.Status`` ...)
and the bookkeeping columns produced by ``swatad.data``.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def make_recording(n=3600, seed=0, start="2026-03-11 09:00:00"):
    rng = np.random.default_rng(seed)
    t = np.arange(n)
    idx = pd.date_range(start, periods=n, freq="s")
    level = 600 + 100 * np.sin(2 * np.pi * t / 900) + rng.normal(0, 2, n)
    flow = 2.5 + 0.3 * np.cos(2 * np.pi * t / 900) + rng.normal(0, 0.02, n)
    press = 250 + rng.normal(0, 1.5, n)
    pump = np.where(np.sin(2 * np.pi * t / 900) > 0, 2.0, 1.0)
    df = pd.DataFrame({
        "LIT101.Pv": level, "FIT101.Pv": flow, "PIT501.Pv": press,
        "AIT201.Pv": 7 + rng.normal(0, 0.01, n),
        "P101.Status": pump, "P102.Status": np.ones(n),   # P102: standby pump, always off
    }, index=idx).astype("float32")
    df["_label"] = np.int8(0)
    df["_attack_id"] = "0"
    df["_gap"] = np.int8(0)
    df["_warmup"] = np.int8(0)
    df["_day"] = idx.strftime("%Y-%m-%d")
    return df


@pytest.fixture
def recording():
    return make_recording()
