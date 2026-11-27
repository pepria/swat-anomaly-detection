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


def test_stuck_rule_ignores_forward_filled_communication_gaps():
    import pandas as pd
    from swatad.rules import RuleMonitor
    rng = np.random.default_rng(0)
    idx = pd.date_range("2026-03-11 09:00:00", periods=4000, freq="s")

    def frame(gap=None, frozen=None):
        df = pd.DataFrame({"LIT101.Pv": np.round(rng.normal(500, 5, len(idx)), 1)}, index=idx)
        df["_gap"] = 0
        if gap:       # outage: the loader forward-fills the value and flags the rows (and 15 s around)
            a, b = gap
            df.iloc[a:b, 0] = df.iloc[a - 1, 0]
            df.iloc[a - 15:b + 15, df.columns.get_loc("_gap")] = 1
        if frozen:    # a real frozen sensor: same value, not flagged as a gap
            a, b = frozen
            df.iloc[a:b, 0] = df.iloc[a - 1, 0]
        return df
    rm = RuleMonitor(stuck_s=120).fit(frame())
    _, h = rm.alarm(frame(gap=(2000, 2300)))
    assert int(h.values.sum()) == 0                                   # outage is not a frozen sensor
    _, h = rm.alarm(frame(frozen=(2000, 2300)))
    assert h.values[2200:2300].all() and h.values[:1900].sum() == 0    # a real frozen sensor still is


def test_explainer_handles_a_stuck_sensor_hit():
    import json
    from swatad.rag.explainer import Explainer, classify
    ev = json.loads((Path(__file__).resolve().parents[1] / "outputs/anomalies/a12_A11-A10_noAIT__WinAE.json").read_text())[2]
    ev.pop("ground_truth_eval_only", None)
    ev["rule_hits"] = [{"rule": "stuck", "tag": "LIT301.Pv", "kind": "sensor", "frozen_value": 812.5, "limit_s": 140,
                        "first_seen": ev["start"], "stage": "P3", "description": "UF feed tank T301 level",
                        "already_active_before": False}]
    ev["top_contributors"] = [t for t in ev["top_contributors"] if t["kind"] == "sensor"][:3] or ev["top_contributors"]
    category, reasons = classify(ev)
    assert category == "frozen_sensor" and "812.5" in reasons[0]
    ex = Explainer(backend="template").explain(ev)
    assert any("stayed at exactly 812.5" in e for e in ex["evidence"])
    assert ex["confidence"] in ("low", "medium", "high")


def test_stuck_rule_is_not_evaded_by_short_repeated_dropouts_of_the_link():
    import pandas as pd
    from swatad.rules import RuleMonitor
    rng = np.random.default_rng(1)
    idx = pd.date_range("2026-03-11 09:00:00", periods=4000, freq="s")

    def frame(frozen=False):
        df = pd.DataFrame({"LIT101.Pv": np.round(rng.normal(500, 5, len(idx)), 1)}, index=idx)
        df["_gap"] = 0
        if frozen:       # frozen for 15 minutes; every 100 s a 3 s dropout, flagged +-15 s like the loader does
            df.iloc[1000:1900, 0] = df.iloc[999, 0]
            for t in range(1050, 1900, 100):
                df.iloc[t:t + 3, 0] = df.iloc[t - 1, 0]
                df.iloc[t - 15:t + 18, df.columns.get_loc("_gap")] = 1
        return df
    rm = RuleMonitor(stuck_s=120).fit(frame())
    _, h = rm.alarm(frame(frozen=True))
    assert h.values[1500:1890].sum() > 100            # still detected: the count pauses at a gap, it is not reset


def test_run_state_round_trips_through_json(tmp_path):
    from swatad.features import FeatureSpace
    from swatad.persist import load_run_state, save_run_state
    from swatad.rules import RuleMonitor
    import pandas as pd
    rng = np.random.default_rng(0)
    df = pd.DataFrame({"LIT101.Pv": rng.normal(500, 5, 500), "FIT101.Pv": rng.normal(2, 0.1, 500),
                       "P101.Status": rng.choice([1.0, 2.0], 500)})
    fs, rm = FeatureSpace().fit(df), RuleMonitor(stuck_s=60).fit(df)
    save_run_state(tmp_path, fs, rm)
    fs2, rm2 = load_run_state(tmp_path)
    assert fs2.cols == fs.cols and np.allclose(fs2.transform(df), fs.transform(df))
    assert rm2.seen == rm.seen and rm2.lo == rm.lo and rm2.stuck_limit == rm.stuck_limit
    assert (rm2.hits(df).values == rm.hits(df).values).all()


def test_a_pickle_is_never_loaded(tmp_path):
    import pickle
    import pytest
    from swatad.persist import load_run_state
    (tmp_path / "feature_space.pkl").write_bytes(pickle.dumps({"fs": 1}))
    with pytest.raises(FileNotFoundError, match="not loaded"):
        load_run_state(tmp_path)


def test_llm_output_is_validated_and_neutralised():
    from swatad.rag.explainer import sanitize_llm_output
    out = sanitize_llm_output({"summary": "<script>x</script> [a](http://evil) ![i](http://e/p.png)",
                               "evidence": ["a\nb", 3, None, "x" * 5000], "confidence": "HIGH!",
                               "category": "hacked", "sources": ["x"], "extra": "dropped"})
    assert set(out) == {"summary", "evidence", "confidence"}          # unknown fields and category/sources dropped
    assert "<" not in out["summary"] and "](" not in out["summary"] and "![" not in out["summary"]
    assert out["confidence"] == "low"                                   # not one of low/medium/high
    assert out["evidence"][0] == "a b" and len(out["evidence"][-1]) <= 800
    assert sanitize_llm_output("not a dict", "plain text")["summary"] == "plain text"
    assert sanitize_llm_output({"summary": "ok", "confidence": "Medium"})["confidence"] == "medium"


def test_auto_backend_does_not_send_data_out_without_explicit_opt_in(monkeypatch):
    from swatad.rag.explainer import Explainer
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.delenv("SWAT_ALLOW_EXTERNAL_LLM", raising=False)
    assert Explainer(backend="auto").backend.name == "template"
