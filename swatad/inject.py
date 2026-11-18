"""Synthetic anomaly injection.

Adds parameterised faults/attacks to a *normal* recording, so detection can be
broken down by anomaly type (A12 has no drift / noise / replay examples) and the
explanation layer can be checked against a known root-cause tag.

Every injection is recorded as a dict
    {inj_id, type, tag, stage, start, end, magnitude_sigma, description}
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .features import tag_kind, tag_stage

TYPES = ["spike", "bias", "drift", "stuck", "noise", "actuator_flip", "replay"]

DESCR = {
    "spike": "short spike of {m:.0f} sigma on {tag}",
    "bias": "constant offset of {m:+.0f} sigma on {tag}",
    "drift": "linear drift reaching {m:+.0f} sigma on {tag}",
    "stuck": "{tag} frozen at its last value",
    "noise": "Gaussian noise of {m:.0f} sigma added to {tag}",
    "actuator_flip": "{tag} status inverted without physical response",
    "replay": "{tag} replaced by a replay of its values 30 min earlier",
}


def _apply(df, kind, col, i0, i1, sigma, rng):
    v = df[col].to_numpy(dtype="float64", copy=True)
    m = _modify(v, kind, i0, i1, sigma, rng)
    df[col] = v.astype(df[col].dtype)
    return m


def _modify(v, kind, i0, i1, sigma, rng):
    n = i1 - i0
    if kind == "spike":
        m = rng.choice([-1, 1]) * rng.uniform(6, 10)
        v[i0:i0 + 5] += m * sigma
        return m
    if kind == "bias":
        m = rng.choice([-1, 1]) * rng.uniform(2, 4)
        v[i0:i1] += m * sigma
        return m
    if kind == "drift":
        m = rng.choice([-1, 1]) * rng.uniform(3, 6)
        v[i0:i1] += np.linspace(0, m, n) * sigma
        return m
    if kind == "stuck":
        v[i0:i1] = v[i0]
        return 0.0
    if kind == "noise":
        m = rng.uniform(2, 4)
        v[i0:i1] += rng.normal(0, m * sigma, n)
        return m
    if kind == "actuator_flip":
        v[i0:i1] = np.where(v[i0:i1] == 2, 1, 2)
        return 0.0
    if kind == "replay":
        v[i0:i1] = v[i0 - 1800:i1 - 1800].copy()
        return 0.0
    raise ValueError(kind)


def inject(df: pd.DataFrame, region: tuple[str, str], sensors: list[str], actuators: list[str],
           sigma: dict, seed: int = 0, dur=(120, 300), gap=420, types=TYPES):
    """Return (modified copy of df, list of injections) inside the time region (HH:MM:SS)."""
    rng = np.random.default_rng(seed)
    out = df.copy()
    hh = out.index.strftime("%H:%M:%S")
    allowed = np.flatnonzero((hh >= region[0]) & (hh < region[1]))
    lo, hi = allowed[0], allowed[-1]
    inj, t = [], lo + rng.integers(0, gap)
    k = 0
    while True:
        n = int(rng.integers(dur[0], dur[1] + 1))
        if t + n >= hi:
            break
        kind = types[k % len(types)]
        k += 1
        pool = actuators if kind == "actuator_flip" else sensors
        col = pool[rng.integers(len(pool))]
        m = _apply(out, kind, col, t, t + n, sigma.get(col, 1.0), rng)
        inj.append({"inj_id": f"S{seed}-{len(inj) + 1:02d}", "type": kind, "tag": col,
                    "stage": tag_stage(col), "kind": tag_kind(col),
                    "start": out.index[t], "end": out.index[t + n - 1],
                    "magnitude_sigma": round(float(m), 2),
                    "description": DESCR[kind].format(m=m, tag=col)})
        out.iloc[t:t + n, out.columns.get_loc("_label")] = 1
        t += n + gap + int(rng.integers(0, 120))
    return out, inj
