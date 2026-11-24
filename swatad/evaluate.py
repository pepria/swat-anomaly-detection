"""Point-level and event-level evaluation."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, precision_recall_curve, roc_auc_score

from . import config as C


def smooth(score: np.ndarray, w: int = 10) -> np.ndarray:
    if w <= 1:
        return score
    return pd.Series(score).rolling(w, min_periods=1).median().values


def score_ratio(score, thr: float):
    """Score relative to its threshold: 1 at the threshold, > 1 above.

    Equal to score / thr for thr > 0 and still monotone for thr <= 0 (a negative
    log-likelihood threshold), where score / thr would invert the ordering."""
    return (score - thr) / max(abs(thr), 1e-12) + 1.0


def alarm_segments(alarm: np.ndarray, index: pd.DatetimeIndex, merge_gap_s: int = 60,
                   min_len_s: int = 1) -> pd.DataFrame:
    """Group alarm points into alarm events (gaps <= merge_gap_s are merged)."""
    a = alarm.astype(int)
    d = np.diff(np.r_[0, a, 0])
    s, e = list(np.flatnonzero(d == 1)), list(np.flatnonzero(d == -1) - 1)
    segs = []
    for si, ei in zip(s, e):
        if segs and (index[si] - index[segs[-1][1]]).total_seconds() <= merge_gap_s:
            segs[-1][1] = ei
        else:
            segs.append([si, ei])
    segs = [(a_, b_) for a_, b_ in segs if (index[b_] - index[a_]).total_seconds() + 1 >= min_len_s]
    return pd.DataFrame({"i0": [x[0] for x in segs], "i1": [x[1] for x in segs],
                         "start": [index[x[0]] for x in segs], "end": [index[x[1]] for x in segs]})


def event_metrics(alarm: np.ndarray, index: pd.DatetimeIndex, events: pd.DataFrame,
                  tol_s: int = C.EVENT_TOLERANCE_S) -> dict:
    """events: DataFrame with event_id, start, end (ground-truth attacks).

    An attack counts as detected only if an alarm event *starts* inside
    [start, end + tol]. An alarm that is already on before the attack (e.g. it
    never cleared after the previous attack) does not count. ``event_recall_overlap``
    is the looser "any alarm inside the window" variant used in many papers.
    """
    tol = pd.Timedelta(seconds=tol_s)
    t = index
    segs = alarm_segments(alarm, index)
    detected, delays, overlap = [], [], 0
    for _, ev in events.iterrows():
        m = (t >= ev.start) & (t <= ev.end + tol) & alarm
        overlap += bool(m.any())
        on = segs[(segs.start >= ev.start) & (segs.start <= ev.end + tol)]
        if len(on):
            detected.append(str(ev.event_id))
            delays.append((on.start.iloc[0] - ev.start).total_seconds())
    tp_segs = 0
    for _, sg in segs.iterrows():
        if ((events.start <= sg.end) & (events.end + tol >= sg.start)).any():
            tp_segs += 1
    n_seg = len(segs)
    rec = len(detected) / max(len(events), 1)
    prec = tp_segs / n_seg if n_seg else 0.0
    return {"event_recall": rec, "event_recall_overlap": overlap / max(len(events), 1),
            "events_detected": len(detected), "events_total": len(events),
            "detected_ids": ",".join(detected),
            "mean_delay_s": float(np.mean(delays)) if delays else np.nan,
            "median_delay_s": float(np.median(delays)) if delays else np.nan,
            "alarm_events": n_seg, "false_alarm_events": n_seg - tp_segs,
            "event_precision": prec,
            "event_f1": 2 * prec * rec / (prec + rec) if prec + rec else 0.0}


def point_metrics(score: np.ndarray, y: np.ndarray, thr: float) -> dict:
    pred = score > thr
    tp = int((pred & (y == 1)).sum())
    fp = int((pred & (y == 0)).sum())
    fn = int((~pred & (y == 1)).sum())
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    pr, rc, _ = precision_recall_curve(y, score)
    f1s = 2 * pr * rc / np.maximum(pr + rc, 1e-12)
    return {"auc_roc": roc_auc_score(y, score), "auc_pr": average_precision_score(y, score),
            "precision": p, "recall": r, "f1": 2 * p * r / (p + r) if p + r else 0.0,
            "fpr_normal": fp / max(int((y == 0).sum()), 1),
            "best_f1_oracle": float(np.nanmax(f1s))}


def full_report(score, y, thr, index, events, tol_s=C.EVENT_TOLERANCE_S) -> dict:
    out = point_metrics(score, y, thr)
    out.update(event_metrics(score > thr, index, events, tol_s))
    return out
