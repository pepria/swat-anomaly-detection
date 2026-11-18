"""Feature selection, scaling and windowing (fit on normal training data only)."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from . import config as C
from .data import feature_cols


def base_tag(col: str) -> str:
    """'LIT101.Pv' -> 'LIT101'; 2015 names are already bare."""
    return col.split(".")[0]


def tag_kind(col: str) -> str:
    if col.endswith("_STATE"):
        return "state"
    if col.endswith(".Alarm"):
        return "alarm"
    if col.endswith(".Status") or col.endswith(".Speed"):
        return "actuator"
    if col.endswith(".Pv"):
        return "sensor"
    t = base_tag(col)  # 2015 naming
    return "actuator" if t.startswith(("P", "MV", "UV")) and not t.startswith("PIT") else "sensor"


def tag_stage(col: str) -> str:
    digits = "".join(ch for ch in base_tag(col) if ch.isdigit())
    return f"P{digits[0]}" if digits else "?"


def is_discrete(col: str) -> bool:
    return tag_kind(col) in ("actuator", "alarm", "state")


@dataclass
class FeatureSpace:
    """Which columns go into the ML models and how they are standardised."""
    drop_ait: bool = False
    cols: list[str] = field(default_factory=list)
    mean: np.ndarray | None = None
    std: np.ndarray | None = None
    clip: float = 20.0

    def fit(self, train: pd.DataFrame) -> "FeatureSpace":
        cand = [c for c in feature_cols(train) if tag_kind(c) != "state"]
        redundant = {c for g in C.REDUNDANT_GROUPS for c in g[1:]}
        cand = [c for c in cand if c not in redundant]
        if self.drop_ait:
            cand = [c for c in cand if not base_tag(c).startswith("AIT")]
        X = train[cand]
        # near-constant columns carry no information for density / reconstruction models;
        # they are watched by the rule layer instead (see rules.py)
        nunique = X.nunique()
        frac_mode = X.apply(lambda s: s.value_counts(normalize=True).iloc[0])
        keep = [c for c in cand if nunique[c] > 1 and frac_mode[c] < 0.999]
        self.cols = keep
        self.mean = train[keep].mean().values.astype("float32")
        self.std = (train[keep].std().values + 1e-6).astype("float32")
        # very small std on discrete columns would blow up z-scores
        for i, c in enumerate(keep):
            if is_discrete(c):
                self.std[i] = max(self.std[i], 0.25)
        return self

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        Z = (df[self.cols].values.astype("float32") - self.mean) / self.std
        return np.clip(Z, -self.clip, self.clip)


def make_windows(Z: np.ndarray, win: int, step: int, every: int = 1,
                 valid: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Sliding windows over a 1 Hz matrix.

    Each window has ``win`` samples spaced ``every`` seconds apart and ends at
    index ``t``; windows end every ``step`` seconds. ``valid`` (bool per row)
    drops windows that touch an invalid row (gaps, warm-up, day boundaries).
    Returns (windows [N, win, F], end_index [N]).
    """
    span = (win - 1) * every
    ends = np.arange(span, len(Z), step)
    if valid is not None:
        bad = (~valid).astype(int)
        cs = np.r_[0, np.cumsum(bad)]
        ok = (cs[ends + 1] - cs[ends - span]) == 0
        ends = ends[ok]
    offs = np.arange(-span, 1, every)
    return Z[ends[:, None] + offs[None, :]], ends
