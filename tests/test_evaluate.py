import numpy as np
import pandas as pd

from swatad.evaluate import alarm_segments, event_metrics, point_metrics, smooth

IDX = pd.date_range("2026-03-11 10:00:00", periods=1000, freq="s")


def _events(*spans):
    return pd.DataFrame({"event_id": [str(i + 1) for i in range(len(spans))],
                         "start": [IDX[a] for a, _ in spans], "end": [IDX[b] for _, b in spans]})


def test_alarm_segments_merge_gap():
    a = np.zeros(1000, bool)
    a[100:110] = a[140:150] = True     # 30 s apart -> merged
    a[400:405] = True                  # separate event
    segs = alarm_segments(a, IDX, merge_gap_s=60)
    assert len(segs) == 2
    assert (segs.i0.iloc[0], segs.i1.iloc[0]) == (100, 149)


def test_event_recall_requires_onset():
    ev = _events((200, 260), (600, 650))
    a = np.zeros(1000, bool)
    a[210:230] = True                  # onset inside attack 1 -> detected
    a[500:700] = True                  # starts before attack 2 -> onset rule says missed
    m = event_metrics(a, IDX, ev, tol_s=60)
    assert m["events_detected"] == 1 and m["detected_ids"] == "1"
    assert m["event_recall_overlap"] == 1.0
    assert m["median_delay_s"] == 10
    assert m["alarm_events"] == 2 and m["false_alarm_events"] == 0


def test_false_alarm_counted():
    ev = _events((200, 260))
    a = np.zeros(1000, bool)
    a[800:810] = True
    m = event_metrics(a, IDX, ev, tol_s=60)
    assert m["event_recall"] == 0 and m["false_alarm_events"] == 1 and m["event_precision"] == 0


def test_point_metrics_perfect_and_random():
    y = np.r_[np.zeros(900), np.ones(100)].astype(int)
    m = point_metrics(y.astype(float), y, 0.5)
    assert m["auc_roc"] == 1 and m["f1"] == 1 and m["fpr_normal"] == 0
    rnd = np.random.default_rng(0).random(1000)
    assert 0.4 < point_metrics(rnd, y, 0.5)["auc_roc"] < 0.6


def test_smooth_removes_single_spike():
    s = np.zeros(50)
    s[25] = 10
    assert smooth(s, 5).max() == 0
