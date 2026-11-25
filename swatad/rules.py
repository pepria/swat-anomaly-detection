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

3. ``stuck`` (optional, off by default) – a continuous sensor keeps exactly the
   same value for longer than ``stuck_s`` seconds *and* longer than any flat run
   seen for that tag in training. Plausible frozen values are invisible to every
   ML model (see RESULTS.md section 3); this rule is the targeted fix. It is
   disabled by default so the published numbers stay reproducible; enable it with
   ``RuleMonitor(stuck_s=120)``.

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
    stuck_s: int | None = None
    stuck_slack: float = 1.2
    stuck_max_s: int = 3600
    stuck_limit: dict = field(default_factory=dict)

    def fit(self, train: pd.DataFrame) -> "RuleMonitor":
        for c in feature_cols(train):
            s = train[c]
            if is_discrete(c):
                self.seen[c] = set(np.unique(s.values).tolist())
            elif not c.split(".")[0].startswith("AIT"):
                lo, hi = float(s.quantile(0.0)), float(s.quantile(1.0))
                pad = max(self.margin * (hi - lo), 0.05 * abs(hi), 1e-3)
                self.lo[c], self.hi[c] = lo - pad, hi + pad
                if self.stuck_s:
                    longest = int(flat_run_length(s.values).max()) if len(s) else 0
                    limit = max(self.stuck_s, int(np.ceil(self.stuck_slack * longest)))
                    # a tag that is naturally flat for very long cannot be checked this way
                    if limit <= self.stuck_max_s:
                        self.stuck_limit[c] = limit
        return self

    def calibrate(self, calib: pd.DataFrame) -> "RuleMonitor":
        rate = self.hits(calib).mean()
        self.disabled = sorted(rate[rate > self.max_calib_rate].index)
        for c in self.disabled:
            self.seen.pop(c, None)
            self.lo.pop(c, None)
            self.hi.pop(c, None)
            self._stuck_limits().pop(c, None)
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
        for c, limit in self._stuck_limits().items():
            if c in df:
                gap = df["_gap"].values if "_gap" in df else None
                st = self._stuck(df[c].values, limit, gap)
                out[c] = out[c] | st if c in out else st
        return pd.DataFrame(out, index=df.index)

    def _stuck_limits(self) -> dict:
        # monitors pickled before the stuck rule existed have no such attribute
        if not hasattr(self, "stuck_limit"):
            self.stuck_limit = {}
        return self.stuck_limit

    @staticmethod
    def _stuck(v: np.ndarray, limit: int, gap: np.ndarray | None = None) -> np.ndarray:
        """True from the moment a flat run exceeds ``limit`` samples until it ends.

        Rows flagged as a communication gap (``_gap == 1``) are forward-filled by the loader and
        look frozen, although the training data (which excludes them) never contained such a run.
        They break a run and are never reported."""
        if gap is None or not np.any(gap):
            return flat_run_length(v) > limit
        g = np.asarray(gap).astype(bool)
        v = np.asarray(v, dtype="float64").copy()
        v[g] = -1e300 - np.arange(int(g.sum()))              # distinct values: runs cannot span a gap row
        return (flat_run_length(v) > limit) & ~g

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
        vmin, vmax = float(np.min(values)), float(np.max(values))
        if c in self._stuck_limits() and self.lo[c] <= vmin and vmax <= self.hi[c]:
            return {"rule": "stuck", "tag": c, "kind": tag_kind(c),
                    "frozen_value": round(vmin, 3), "limit_s": self.stuck_limit[c]}
        return {"rule": "out_of_range", "tag": c, "kind": tag_kind(c),
                "normal_range": [round(self.lo[c], 3), round(self.hi[c], 3)],
                "observed_min": round(float(np.min(values)), 3),
                "observed_max": round(float(np.max(values)), 3)}


def flat_run_length(v: np.ndarray) -> np.ndarray:
    """For each sample, how many consecutive samples (including it) had exactly this value."""
    v = np.asarray(v)
    if len(v) == 0:
        return np.zeros(0, dtype=int)
    new = np.r_[True, v[1:] != v[:-1]]
    starts = np.flatnonzero(new)
    run_start = starts[np.cumsum(new) - 1]
    return np.arange(len(v)) - run_start + 1
