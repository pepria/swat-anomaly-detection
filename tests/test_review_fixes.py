"""Regression tests for the fixes that came out of the code review."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402
import torch  # noqa: E402

from swatad import inject, models  # noqa: E402
from swatad.evaluate import score_ratio  # noqa: E402
from swatad.pipeline import train_scores  # noqa: E402
from swatad.rag.explainer import _body  # noqa: E402


def test_score_ratio_positive_threshold_is_the_plain_ratio():
    s = np.array([0.5, 1.0, 2.0, 3.0])
    assert np.allclose(score_ratio(s, 1.0), s / 1.0)
    assert np.allclose(score_ratio(s, 2.0), s / 2.0)


def test_score_ratio_is_monotone_and_one_at_a_negative_threshold():
    s = np.array([-8.0, -4.0, -3.9, 0.0, 5.0])     # negative log-likelihood scores
    r = score_ratio(s, -3.9)
    assert np.all(np.diff(r) > 0)
    assert np.isclose(score_ratio(-3.9, -3.9), 1.0)
    assert r[-1] > 1 > r[0]


def test_actuator_flip_keeps_the_valve_transition_state():
    v = np.array([0.0, 1.0, 2.0, 0.0, 2.0])
    inject._modify(v, "actuator_flip", 0, 5, 1.0, np.random.default_rng(0))
    assert v.tolist() == [0.0, 2.0, 1.0, 0.0, 1.0]


def test_validation_blocks_are_contiguous_and_about_ten_percent():
    n = 4000
    m = models._val_mask(n, seed=0, split="blocks")
    assert 0.08 < m.mean() < 0.12
    runs = np.flatnonzero(np.diff(np.r_[0, m.astype(int), 0]) != 0)
    assert len(runs) <= 4                       # a few long runs, not scattered rows
    assert not models._val_mask(n, 0, "random").tolist() == m.tolist()


def test_training_survives_a_validation_loss_that_never_improves():
    X = np.full((400, 6), np.nan, dtype="float32")        # NaN loss, best_state stays None
    net = models._MLPAE(6, hidden=(8,), latent=2)
    models._train(net, X, epochs=2, lr=1e-3, batch=64, seed=0, log_name="test")


def test_gmm_contribution_matches_the_standardised_deviation_for_independent_features():
    rng = np.random.default_rng(0)
    Z = rng.normal(size=(3000, 3)).astype("float32")
    det = models.GMMDet(k_grid=(1,), sub_every=1).fit(Z, np.ones(len(Z), bool))
    s, c = det.score(Z[:50])
    var = np.diag(det.m.covariances_[0])
    expected = (Z[:50] - det.m.means_[0]) ** 2 / var
    assert np.allclose(c, expected, rtol=0.05, atol=0.05)
    assert (c >= 0).all()


def test_body_of_a_single_line_chunk_is_empty():
    assert _body("only a title") == ""
    assert _body("title\nbody text") == "body text"


class _SumDet:
    def score(self, Z):
        return Z.sum(1), Z


def test_train_scores_selects_valid_rows_of_contiguous_blocks():
    Z = np.arange(100, dtype="float32").reshape(50, 2)
    valid = np.ones(50, bool)
    valid[10:15] = False
    s, c = train_scores(_SumDet(), Z, valid, w=3, n_blocks=2, block=30)
    # blocks are rows 0-29 and 20-49; rows 10-14 are invalid, rows 20-29 are in both blocks
    assert len(s) == len(c) == (30 - 5) + 30
    assert c.shape[1] == 2
