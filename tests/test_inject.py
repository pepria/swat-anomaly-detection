import numpy as np

from swatad.inject import TYPES, inject
from tests.conftest import make_recording


def test_inject_labels_and_modifies_only_inside_injections():
    base = make_recording(n=7200)
    sigma = {c: float(base[c].std()) for c in ("LIT101.Pv", "FIT101.Pv", "P101.Status")}
    out, inj = inject(base, ("09:40:00", "10:55:00"), ["LIT101.Pv", "FIT101.Pv"], ["P101.Status"],
                      sigma, seed=0)
    assert len(inj) >= 3
    assert {j["type"] for j in inj} <= set(TYPES)
    lab = np.zeros(len(base), bool)
    for j in inj:
        m = (out.index >= j["start"]) & (out.index <= j["end"])
        assert out["_label"].values[m].all()
        lab |= m
    assert not out["_label"].values[~lab].any()
    feats = ["LIT101.Pv", "FIT101.Pv", "P101.Status"]
    assert np.array_equal(out[feats].values[~lab], base[feats].values[~lab])
    assert base["_label"].sum() == 0          # input is not modified in place
