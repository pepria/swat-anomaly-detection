import numpy as np

from swatad.features import FeatureSpace, base_tag, is_discrete, make_windows, tag_kind, tag_stage


def test_tag_helpers():
    assert base_tag("LIT101.Pv") == "LIT101"
    assert tag_kind("LIT101.Pv") == "sensor"
    assert tag_kind("P101.Status") == "actuator"
    assert tag_kind("PSH301.Alarm") == "alarm"
    assert tag_kind("P1_STATE") == "state"
    # 2015 naming: PIT is a sensor even though it starts with P
    assert tag_kind("PIT501") == "sensor" and tag_kind("MV101") == "actuator"
    assert tag_stage("FIT401.Pv") == "P4"
    assert is_discrete("P101.Status") and not is_discrete("LIT101.Pv")


def test_feature_space_drops_constant_and_ait(recording):
    fs = FeatureSpace(drop_ait=True).fit(recording)
    assert "P102.Status" not in fs.cols          # constant -> left to the rule layer
    assert "AIT201.Pv" not in fs.cols
    assert "LIT101.Pv" in fs.cols and "P101.Status" in fs.cols
    Z = fs.transform(recording)
    assert Z.shape == (len(recording), len(fs.cols))
    assert np.allclose(Z.mean(0), 0, atol=0.05)
    assert np.abs(Z).max() <= fs.clip


def test_make_windows_shape_and_validity():
    Z = np.arange(100, dtype="float32")[:, None]
    W, ends = make_windows(Z, win=5, step=10, every=2)
    assert W.shape[1:] == (5, 1)
    # window ending at t holds t-8, t-6, ..., t
    assert np.array_equal(W[0, :, 0], Z[ends[0] - 8:ends[0] + 1:2, 0])
    valid = np.ones(100, bool)
    valid[50] = False
    W2, ends2 = make_windows(Z, win=5, step=1, every=2, valid=valid)
    assert not any(e - 8 <= 50 <= e for e in ends2)
