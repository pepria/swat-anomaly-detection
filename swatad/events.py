"""Turn detector output into one JSON record per anomaly event.

This JSON is the interface between the detection part (person A) and the
explanation part (person B). Schema: docs/anomaly_event.schema.json.
"""
from __future__ import annotations

import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd

from . import config as C
from .evaluate import alarm_segments
from .features import base_tag, is_discrete, tag_kind, tag_stage
from .rag.tags import STAGE_NAMES, describe

SCHEMA_VERSION = "1.0"


def _signal_features(x: np.ndarray, sd_train: float) -> dict:
    """Shape descriptors of one tag inside the event window (used by the explainer)."""
    x = x.astype("float64")
    d = np.diff(x)
    sign = np.sign(d[d != 0])
    return {
        "std_ratio": round(float(np.std(x) / (sd_train + 1e-9)), 3),
        "change": round(float(x[-1] - x[0]), 4),
        "slope_per_min": round(float(np.polyfit(np.arange(len(x)), x, 1)[0] * 60) if len(x) > 2 else 0.0, 4),
        "direction_changes_per_min": round(float((np.diff(sign) != 0).sum() / max(len(x) / 60, 1)), 2),
        "max_step": round(float(np.abs(d).max()) if len(d) else 0.0, 4),
        "max_step_sigma": round(float(np.abs(d).max() / (sd_train + 1e-9)) if len(d) else 0.0, 2),
        "flat_fraction": round(float((d == 0).mean()) if len(d) else 1.0, 3),
    }


class EventExporter:
    """Build anomaly-event records from a finished run directory (outputs/runs/<run>)."""

    def __init__(self, run_dir: Path, test: pd.DataFrame, train: pd.DataFrame,
                 events_gt: pd.DataFrame | None = None):
        self.run_dir = Path(run_dir)
        self.meta = json.loads((self.run_dir / "meta.json").read_text())
        obj = pickle.load(open(self.run_dir / "feature_space.pkl", "rb"))
        self.fs, self.rules = obj["fs"], obj["rules"]
        self.scores = pd.read_parquet(self.run_dir / "scores.parquet")
        self.test = test
        self.events_gt = events_gt
        cols = [c for c in test.columns if not c.startswith("_")]
        q = train[cols].quantile([0.01, 0.5, 0.99])
        self.p01, self.p50, self.p99 = q.loc[0.01], q.loc[0.5], q.loc[0.99]
        self.sd = train[cols].std()

    def _tag_entry(self, col, contrib, sl):
        x = self.test[col].values[sl]
        desc, unit = describe(col)
        e = {"tag": base_tag(col), "column": col, "stage": tag_stage(col), "kind": tag_kind(col),
             "description": desc, "unit": unit, "contribution": round(float(contrib), 3)}
        if is_discrete(col):
            e["values_in_event"] = sorted(set(np.unique(x).tolist()))
            e["normal_values"] = sorted(self.rules.seen.get(col, set())) or None
        else:
            e.update({"value_at_start": round(float(x[0]), 4),
                      "value_min": round(float(x.min()), 4), "value_max": round(float(x.max()), 4),
                      "normal_p01": round(float(self.p01[col]), 4),
                      "normal_median": round(float(self.p50[col]), 4),
                      "normal_p99": round(float(self.p99[col]), 4)})
            dev = (np.median(x) - self.p50[col]) / (self.sd[col] + 1e-9)
            e["direction"] = "high" if dev > 0.5 else "low" if dev < -0.5 else "in-range"
            e["signal"] = _signal_features(x, float(self.sd[col]))
        return e

    def export(self, model: str, use_rules: bool = True, top_k: int = 5, merge_gap_s: int = 60,
               min_len_s: int = 10, onset_s: int = 180) -> list[dict]:
        sc = self.scores
        em = sc["_eval"].values.astype(bool)
        thr = self.meta["thresholds"][model]["calib"]
        s = sc[model].values
        alarm = (s > thr) | (use_rules & sc["_rule_any"].values.astype(bool))
        alarm &= em
        contrib = np.load(self.run_dir / f"contrib_{model}.npy").astype("float32")
        hits = pd.read_parquet(self.run_dir / "rule_hits.parquet")
        segs = alarm_segments(alarm, sc.index, merge_gap_s, min_len_s)
        cols = self.fs.cols
        records = []
        for n, sg in enumerate(segs.itertuples(), 1):
            i0, i1 = sg.i0, sg.i1
            on = slice(i0, min(i1, i0 + onset_s) + 1)   # onset window: what changed first
            full = slice(i0, i1 + 1)
            c_mean = np.nan_to_num(contrib[on].mean(0))
            # differential attribution: what got worse compared with the 2 minutes before the
            # event (otherwise tags that are already off-normal, e.g. after an earlier attack,
            # dominate every later event)
            pre = contrib[max(0, i0 - 120):max(0, i0 - 5)]
            base = np.nan_to_num(pre.mean(0)) if len(pre) else np.zeros_like(c_mean)
            delta = np.clip(c_mean - base, 0, None)
            rank_by = delta if delta.sum() > 0 else c_mean
            order = np.argsort(-rank_by)[:top_k]
            share = rank_by / (rank_by.sum() + 1e-9)
            top = [self._tag_entry(cols[j], c_mean[j], full)
                   | {"share": round(float(share[j]), 3),
                      "contribution_increase": round(float(delta[j]), 3)}
                   for j in order]
            # rule hits (tags that violate a rule anywhere in the event)
            h = hits.iloc[full]
            fired = [c for c in h.columns if h[c].values.any()]
            rule_hits = []
            for c in fired:
                first = h.index[np.argmax(h[c].values)]
                xv = self.test[c].values[full]
                entry = self.rules.describe_hit(c, xv[h[c].values]) | {
                    "first_seen": str(first), "stage": tag_stage(c), "description": describe(c)[0]}
                if not is_discrete(c):
                    # shape of the signal from the first violation to the end of the event
                    entry["signal"] = _signal_features(xv[int(np.argmax(h[c].values)):], float(self.sd[c]))
                rule_hits.append(entry)
            # newly-firing tags are more informative than tags already in violation before
            prev = hits.iloc[max(0, i0 - 30):i0]
            for r in rule_hits:
                col = r["tag"]
                r["already_active_before"] = bool(prev[col].values.any()) if len(prev) else False
            peak = i0 + int(np.argmax(s[full]))
            stages = sorted({t["stage"] for t in top[:3]} | {r["stage"] for r in rule_hits
                                                             if not r["already_active_before"]})
            rec = {
                "schema_version": SCHEMA_VERSION,
                "event_id": f"{self.meta['setup']}-{model}-{n:03d}",
                "dataset": self.meta["setup"],
                "model": model,
                "detector_variant": "model+rules" if use_rules else "model",
                "start": str(sc.index[i0]), "end": str(sc.index[i1]),
                "duration_s": int((sc.index[i1] - sc.index[i0]).total_seconds()) + 1,
                "peak_time": str(sc.index[peak]),
                "threshold": round(thr, 4),
                "max_score": round(float(np.max(s[full])), 4),
                "mean_score": round(float(np.mean(s[full])), 4),
                "max_score_ratio": round(float(np.max(s[full]) / thr), 3),
                "triggered_by": ("model+rules" if (s[full] > thr).any() and len(rule_hits)
                                 else "model" if (s[full] > thr).any() else "rules"),
                "stages_involved": stages,
                "stage_names": {st: STAGE_NAMES.get(st, "?") for st in stages},
                "top_contributors": top,
                "rule_hits": rule_hits,
            }
            if self.events_gt is not None:
                tol = pd.Timedelta(seconds=C.EVENT_TOLERANCE_S)
                gt = self.events_gt[(self.events_gt.start <= sc.index[i1]) &
                                    (self.events_gt.end + tol >= sc.index[i0])]
                rec["ground_truth_eval_only"] = [
                    {k: (str(v) if isinstance(v, pd.Timestamp) else v) for k, v in row.items()
                     if k in ("event_id", "name", "targets", "start", "end", "type", "tag")}
                    for row in gt.to_dict("records")]
            records.append(rec)
        return records
