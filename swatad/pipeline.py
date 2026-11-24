"""End-to-end experiment runner: train on normal data, calibrate, score, evaluate.

Two independent setups (never mixed, see EDA report section 6.3):

* ``a12``   train on SWaT.A11 (Feb 2026) [+ A10 Dec 2023], test on SWaT.A12 (Mar 2026)
* ``s2015`` train on SWaT 2015 normal, test on SWaT 2015 attack
"""
from __future__ import annotations

import json
import pickle
import time
from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import config as C
from . import data as D
from .evaluate import full_report, score_ratio, smooth
from .features import FeatureSpace
from .models import MODELS
from .rules import RuleMonitor


@dataclass
class Setup:
    name: str
    train: pd.DataFrame
    test: pd.DataFrame          # full test recording (scored as one sequence)
    calib_mask: np.ndarray      # rows of `calib_df` used for threshold calibration
    calib_df: pd.DataFrame      # recording that contains the calibration rows
    eval_mask: np.ndarray       # rows of `test` that are evaluated
    events: pd.DataFrame        # ground-truth attacks (event_id, start, end, ...)


def valid_mask(df: pd.DataFrame) -> np.ndarray:
    """Rows usable for training: no comms gap, no warm-up, no time discontinuity."""
    v = (df["_gap"].values == 0) & (df["_warmup"].values == 0)
    dt = np.r_[1, np.diff(df.index.values).astype("timedelta64[s]").astype(int)]
    v &= dt == 1
    return v


def train_scores(det, Ztr: np.ndarray, vtr: np.ndarray, w: int, n_blocks: int = 3, block: int = 20000):
    """Smoothed scores and contributions of the (in-sample) training data on contiguous blocks.

    Used for the training-time threshold and for the contribution normalisation. Contiguous
    blocks are scored and smoothed exactly like a test recording (window models need them),
    and the valid rows are selected afterwards."""
    T = len(Ztr)
    starts = list(dict.fromkeys(np.linspace(0, max(T - block, 0), n_blocks).astype(int)))
    ss, cs = [], []
    for a in starts:
        sl = slice(a, min(a + block, T))
        s, c = det.score(Ztr[sl])
        m = vtr[sl]
        ss.append(smooth(s, w)[m])
        cs.append(c[m])
    return np.concatenate(ss), np.concatenate(cs)


def make_setup(setup: str, train_sets: str = "A11+A10") -> Setup:
    if setup == "a12":
        parts = [D.load_a11()]
        if "A10" in train_sets:
            a10 = D.load_a10()
            parts.append(a10.drop(columns=["_mode"]))
        train = pd.concat(parts)
        test = D.load_a12()
        hhmm = test.index.strftime("%H:%M:%S")
        calib = (hhmm >= C.A12_CALIB[0]) & (hhmm < C.A12_CALIB[1])
        ev_mask = hhmm >= C.A12_EVAL_FROM
        events = D.a12_attacks().rename(columns={"attack_id": "event_id"})
        return Setup("a12", train, test, calib, test, ev_mask, events)
    if setup == "s2015":
        normal = D.load_2015_normal()
        cut = normal.index[-1] - pd.Timedelta(hours=12)
        train = normal[normal.index <= cut]
        calib = (normal.index > cut)
        test = D.load_2015_attack()
        events = D.segments_from_labels(test)
        return Setup("s2015", train, test, calib, normal, np.ones(len(test), bool), events)
    raise ValueError(setup)


def run(setup: str = "a12", train_sets: str = "A11+A10", drop_ait: bool = True,
        models=("IForest", "GMM", "AE", "WinAE", "LSTM-AE"), q: float = 0.995,
        tag: str | None = None, save_contrib: bool = True, model_kwargs: dict | None = None,
        seeds=(0, 1, 2), rule_kwargs: dict | None = None):
    """Train every model (once per seed), calibrate thresholds, evaluate.

    Saves to outputs/runs/<tag>/: metrics.csv (one row per model/variant/seed),
    scores.parquet + contrib_<model>.npy (first seed only), meta.json.
    """
    C.ensure_dirs()
    tag = tag or f"{setup}_{train_sets.replace('+', '-')}_{'noAIT' if drop_ait else 'all'}"
    out = C.OUT_DIR / "runs" / tag
    out.mkdir(parents=True, exist_ok=True)
    S = make_setup(setup, train_sets)
    fs = FeatureSpace(drop_ait=drop_ait).fit(S.train[valid_mask(S.train)])
    rules = RuleMonitor(**(rule_kwargs or {})).fit(S.train[valid_mask(S.train)])
    rules.calibrate(S.calib_df[S.calib_mask])
    print(f"[{tag}] train rows {len(S.train)}, features {len(fs.cols)}")

    Ztr, vtr = fs.transform(S.train), valid_mask(S.train)
    Zte = fs.transform(S.test)
    same = S.calib_df is S.test
    Zca = Zte if same else fs.transform(S.calib_df)
    y = S.test["_label"].values.astype(int)
    em = S.eval_mask
    idx = S.test.index[em]
    # "clean" normal = evaluated rows before the first attack (later normal rows are
    # contaminated by attack after-effects, e.g. P401/P403 stay off after A12 #1)
    clean = (S.test.index[em] < S.events.start.min())

    # rule layer ------------------------------------------------------------
    rule_any, hits = rules.alarm(S.test)
    hits_cal = rules.hits(S.calib_df).values.any(1)[S.calib_mask]

    rows, scores, thresholds = [], {}, {}
    model_kwargs = model_kwargs or {}
    for name in models:
        for seed in seeds:
            t0 = time.time()
            kw = dict(model_kwargs.get(name, {}), seed=C.SEED + seed)
            det = MODELS[name](**kw).fit(Ztr, vtr)
            s_te, c_te = det.score(Zte)
            s_ca = s_te if same else det.score(Zca)[0]
            w = 10 if name in ("IForest", "GMM", "AE") else 5
            s_te, s_ca = smooth(s_te, w), smooth(s_ca, w)
            thr = float(np.quantile(s_ca[S.calib_mask], q))
            # training-time threshold (no re-calibration, in-sample), reported for the drift discussion
            s_tr, c_tr = train_scores(det, Ztr, vtr, w)
            thr_train = float(np.quantile(s_tr, q))
            c_norm = c_tr.mean(0) + 1e-6
            dt = time.time() - t0

            for variant, sc, th in [
                ("model", s_te, thr),
                ("model+rules", np.maximum(score_ratio(s_te, thr), 2.0 * rule_any), 1.0),
                ("model (train thr)", s_te, thr_train),
            ]:
                r = full_report(sc[em], y[em], th, idx, S.events)
                r["fpr_clean"] = float((sc[em][clean] > th).mean()) if clean.any() else np.nan
                r.update(model=name, variant=variant, threshold=th, train_s=round(dt, 1), seed=seed)
                rows.append(r)
            if seed != seeds[0]:
                print(f"  {name} seed {seed}: AUC {rows[-3]['auc_roc']:.3f}")
                continue
            scores[name] = s_te
            thresholds[name] = {"calib": thr, "train": thr_train,
                                "extra": getattr(det, "k", None)}
            if save_contrib:
                np.save(out / f"contrib_{name}.npy", np.clip(c_te / c_norm, 0, 6e4).astype("float16"))
            print(f"  {name}: AUC {rows[-3]['auc_roc']:.3f}  event recall {rows[-3]['event_recall']:.2f}"
                  f"  (+rules {rows[-2]['event_recall']:.2f})  FPR(clean) {rows[-3]['fpr_clean']:.3f}  {dt:.0f}s")

    # rules alone
    r = full_report(rule_any[em].astype(float), y[em], 0.5, idx, S.events)
    r["fpr_clean"] = float(rule_any[em][clean].mean()) if clean.any() else np.nan
    r.update(model="Rules only", variant="rules", threshold=0.5, train_s=0, seed=0)
    rows.append(r)
    r_cal_fpr = float(hits_cal.mean())

    res = pd.DataFrame(rows)
    res.insert(0, "run", tag)
    res.to_csv(out / "metrics.csv", index=False)
    sc = pd.DataFrame(scores, index=S.test.index)
    sc["_label"] = y
    sc["_attack_id"] = S.test["_attack_id"].values
    sc["_rule_any"] = rule_any
    sc["_eval"] = em
    sc.to_parquet(out / "scores.parquet")
    hits.to_parquet(out / "rule_hits.parquet")
    with open(out / "meta.json", "w") as f:
        json.dump({"setup": setup, "train_sets": train_sets, "drop_ait": drop_ait, "q": q,
                   "features": fs.cols, "thresholds": thresholds,
                   "rules_fpr_on_calibration": r_cal_fpr,
                   "rules_disabled_after_calibration": rules.disabled}, f, indent=1)
    with open(out / "feature_space.pkl", "wb") as f:
        pickle.dump({"fs": fs, "rules": rules}, f)
    return res


def fit_and_calibrate(setup="a12", train_sets="A11+A10", drop_ait=True,
                      models=("IForest", "GMM", "AE", "WinAE", "LSTM-AE"), q=0.995, seed=0,
                      model_kwargs=None, rule_kwargs=None):
    """Fit models once and return everything needed to score new data.

    ``rule_kwargs`` is passed to ``RuleMonitor`` (e.g. ``{"stuck_s": 120}``).
    Returns dict(setup=S, fs=FeatureSpace, rules=RuleMonitor,
                 models={name: dict(det, thr, w, c_norm)}).
    """
    S = make_setup(setup, train_sets)
    v = valid_mask(S.train)
    fs = FeatureSpace(drop_ait=drop_ait).fit(S.train[v])
    rules = RuleMonitor(**(rule_kwargs or {})).fit(S.train[v])
    rules.calibrate(S.calib_df[S.calib_mask])
    Ztr, Zca = fs.transform(S.train), fs.transform(S.calib_df)
    out = {}
    for name in models:
        kw = dict((model_kwargs or {}).get(name, {}), seed=C.SEED + seed)
        det = MODELS[name](**kw).fit(Ztr, v)
        w = 10 if name in ("IForest", "GMM", "AE") else 5
        thr = float(np.quantile(smooth(det.score(Zca)[0], w)[S.calib_mask], q))
        c_tr = train_scores(det, Ztr, v, w)[1]
        out[name] = {"det": det, "thr": thr, "w": w, "c_norm": c_tr.mean(0) + 1e-6}
    return {"setup": S, "fs": fs, "rules": rules, "models": out}


def score_with(fitted, df):
    """Score a DataFrame with fitted models -> {name: (smoothed score, normalised contrib, thr)}."""
    Z = fitted["fs"].transform(df)
    res = {}
    for name, m in fitted["models"].items():
        s, c = m["det"].score(Z)
        res[name] = (smooth(s, m["w"]), c / m["c_norm"], m["thr"])
    return res
