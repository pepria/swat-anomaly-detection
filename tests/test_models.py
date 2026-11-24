import numpy as np
import pytest

from swatad.models import MODELS

FAST = {"IForest": {"n_estimators": 50}, "GMM": {"k_grid": (2, 3)}, "AE": {"epochs": 3},
        "WinAE": {"win": 8, "every": 2, "epochs": 3}, "LSTM-AE": {"win": 8, "every": 2, "epochs": 2}}


@pytest.mark.parametrize("name", list(MODELS))
def test_model_api_and_anomaly_scores_higher(name):
    rng = np.random.default_rng(0)
    T, F = 3000, 4
    t = np.arange(T)
    base = np.sin(2 * np.pi * t / 300)
    Z = np.stack([base, -base, 0.5 * base, np.cos(2 * np.pi * t / 300)], 1)
    Z = (Z + rng.normal(0, 0.05, Z.shape)).astype("float32")
    det = MODELS[name](**FAST[name], seed=0).fit(Z, np.ones(T, bool))
    Zt = Z.copy()
    Zt[2000:2100, 1] += 6.0                       # strong anomaly on feature 1
    s, c = det.score(Zt)
    assert s.shape == (T,) and c.shape == (T, F)
    assert np.isfinite(s).all() and (np.nan_to_num(c) >= 0).all()
    assert np.median(s[2030:2100]) > np.quantile(s[:1900], 0.99)
    if name != "IForest":   # IForest attribution is a crude distance-from-median proxy
        assert np.argmax(np.nanmean(c[2030:2100], 0)) == 1
