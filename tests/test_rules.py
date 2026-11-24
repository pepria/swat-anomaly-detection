import numpy as np

from swatad.rules import RuleMonitor, flat_run_length
from tests.conftest import make_recording


def test_flat_run_length():
    assert flat_run_length(np.array([1, 1, 2, 2, 2, 1])).tolist() == [1, 2, 1, 2, 3, 1]
    assert flat_run_length(np.array([])).size == 0


def test_unseen_state_and_out_of_range(recording):
    rules = RuleMonitor().fit(recording)
    test = make_recording(seed=1)
    test.iloc[1000:1100, test.columns.get_loc("P102.Status")] = 2.0   # standby pump starts
    test.iloc[2000:2050, test.columns.get_loc("LIT101.Pv")] = 2000.0  # spoofed level
    h = rules.hits(test)
    assert h["P102.Status"].iloc[1000:1100].all() and not h["P102.Status"].iloc[:1000].any()
    assert h["LIT101.Pv"].iloc[2000:2050].all()
    assert "AIT201.Pv" not in h.columns                               # analysers excluded
    alarm, _ = rules.alarm(test)
    assert alarm[1000] and alarm[2000] and not alarm[:1000].any()
    d = rules.describe_hit("P102.Status", test["P102.Status"].values[1000:1100])
    assert d["rule"] == "unseen_state" and d["observed_values"] == [2.0]


def test_alarm_is_acknowledged_after_ack_s(recording):
    rules = RuleMonitor().fit(recording)
    test = make_recording(seed=1)
    test.iloc[100:3000, test.columns.get_loc("P102.Status")] = 2.0
    alarm, hits = rules.alarm(test, ack_s=600)
    assert hits["P102.Status"].iloc[100:3000].all()
    assert alarm[100:700].all() and not alarm[700:3000].any()


def test_calibration_disables_drifted_tags(recording):
    rules = RuleMonitor().fit(recording)
    calib = make_recording(seed=2)
    calib["FIT101.Pv"] += 10.0          # drifted flow meter at deployment time
    rules.calibrate(calib)
    assert "FIT101.Pv" in rules.disabled
    assert "FIT101.Pv" not in rules.hits(calib).columns


def test_stuck_rule_is_off_by_default_and_detects_frozen_sensor(recording):
    test = make_recording(seed=1)
    v = float(test["LIT101.Pv"].iloc[1500])
    test.iloc[1500:1800, test.columns.get_loc("LIT101.Pv")] = v        # plausible frozen value
    assert not RuleMonitor().fit(recording).hits(test)["LIT101.Pv"].any()

    rules = RuleMonitor(stuck_s=60).fit(recording)
    h = rules.hits(test)["LIT101.Pv"]
    assert h.iloc[1500 + 61:1800].all()
    assert not h.iloc[:1500].any() and not h.iloc[1800:].any()
    d = rules.describe_hit("LIT101.Pv", test["LIT101.Pv"].values[1561:1800])
    assert d["rule"] == "stuck" and d["frozen_value"] == round(v, 3)
    # the constant standby pump status is not a "stuck sensor"
    assert "P102.Status" not in rules.stuck_limit


def test_old_pickled_monitor_still_works():
    import pickle
    from pathlib import Path
    pkl = Path(__file__).resolve().parents[1] / "outputs/runs/a12_A11-A10_noAIT/feature_space.pkl"
    rules = pickle.load(open(pkl, "rb"))["rules"]
    if hasattr(rules, "stuck_limit"):
        del rules.stuck_limit
    df = make_recording()
    df["LIT101.Pv"] = 2000.0
    assert rules.hits(df)["LIT101.Pv"].all()
