"""Transparent rule layer that complements the ML models.

Two rules, both learnt from the normal training data:

1. ``unseen_state``  – a discrete column (pump / valve status, alarm, PLC state)
   takes a value never observed in training. This covers backup pumps and
   valves that are constant in normal operation but are switched by attacks
   (A12 #3, #7, #8). The EDA showed these columns must not simply be dropped.
2. ``out_of_range``  – a continuous sensor leaves the training range widened by
   a margin (fraction of the range). Water-quality analysers (AIT*) drift from
   week to week and are excluded from this rule.

``calibrate()`` disables any tag whose rule already fires on the (normal)
calibration window: this is how drifted tags are found at deployment time
(A11 -> A12: FIT501/503/504, FIT101 ...). Disabled tags are kept in
``self.disabled`` and reported.

Rule hits are reported per tag so they can be passed to the explanation layer.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .data import feature_cols
from .features import is_discrete, tag_kind


@dataclass
class RuleMonitor:
    margin: float = 0.20
    max_calib_rate: float = 0.001
    seen: dict = field(default_factory=dict)
    disabled: list = field(default_factory=list)
    lo: dict = field(default_factory=dict)
    hi: dict = field(default_factory=dict)

    def fit(self, train: pd.DataFrame) -> "RuleMonitor":
        for c in feature_cols(train):
            s = train[c]
            if is_discrete(c):
                self.seen[c] = set(np.unique(s.values).tolist())
            elif not c.split(".")[0].startswith("AIT"):
                lo, hi = float(s.quantile(0.0)), float(s.quantile(1.0))
                pad = max(self.margin * (hi - lo), 0.05 * abs(hi), 1e-3)
                self.lo[c], self.hi[c] = lo - pad, hi + pad
        return self

    def calibrate(self, calib: pd.DataFrame) -> "RuleMonitor":
        rate = self.hits(calib).mean()
        self.disabled = sorted(rate[rate > self.max_calib_rate].index)
        for c in self.disabled:
            self.seen.pop(c, None)
            self.lo.pop(c, None)
            self.hi.pop(c, None)
        return self

    def hits(self, df: pd.DataFrame) -> pd.DataFrame:
        """Boolean DataFrame (time x tag): True where a rule fires for that tag."""
        out = {}
        for c, seen in self.seen.items():
            if c in df:
                out[c] = ~df[c].isin(seen).values
        for c in self.lo:
            if c in df:
                v = df[c].values
                out[c] = (v < self.lo[c]) | (v > self.hi[c])
        return pd.DataFrame(out, index=df.index)

    def alarm(self, df: pd.DataFrame, ack_s: int = 600) -> tuple[np.ndarray, pd.DataFrame]:
        """Rule alarm with operator acknowledgement.

        A tag that keeps violating its rule raises an alarm only for ``ack_s``
        seconds after the violation starts (as if an operator acknowledged it);
        a *new* tag, or the same tag after it returned to normal, alarms again.
        Returns (alarm [T] bool, raw hits DataFrame).
        """
        h = self.hits(df)
        H = h.values.astype(int)
        latched = np.zeros_like(H, dtype=bool)
        for j in range(H.shape[1]):
            col = H[:, j]
            if not col.any():
                continue
            onset = np.flatnonzero(np.diff(np.r_[0, col]) == 1)
            for o in onset:
                end = o
                while end < len(col) and col[end] and end - o < ack_s:
                    end += 1
                latched[o:end, j] = True
        return latched.any(1), h

    def describe_hit(self, c: str, values: np.ndarray) -> dict:
        if c in self.seen:
            return {"rule": "unseen_state", "tag": c, "kind": tag_kind(c),
                    "normal_values": sorted(self.seen[c]),
                    "observed_values": sorted(set(np.unique(values).tolist()) - self.seen[c])}
        return {"rule": "out_of_range", "tag": c, "kind": tag_kind(c),
                "normal_range": [round(self.lo[c], 3), round(self.hi[c], 3)],
                "observed_min": round(float(np.min(values)), 3),
                "observed_max": round(float(np.max(values)), 3)}
