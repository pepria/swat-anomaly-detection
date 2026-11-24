"""Unsupervised detectors trained on normal data only.

Common interface::

    det.fit(Z, valid)          # Z: [T, F] standardised 1 Hz matrix, valid: bool [T]
    score, contrib = det.score(Z)
        score   [T]     higher = more anomalous
        contrib [T, F]  non-negative per-feature contribution to the score

Point models (IsolationForest, GMM, AE) look at a single time step.
Window models (WindowAE, LSTMAE) look at the last ``win`` samples taken every
``every`` seconds (default 30 x 4 s = 2 minutes) and score the window end.
"""
from __future__ import annotations

import os
import time

import numpy as np
import torch
from sklearn.ensemble import IsolationForest
from sklearn.mixture import GaussianMixture
from torch import nn

from . import config as C
from .features import make_windows

torch.set_num_threads(4)


def _subsample(Z, valid, every, max_n=None, seed=C.SEED):
    X = Z[valid][::every]
    if max_n and len(X) > max_n:
        X = X[np.random.default_rng(seed).choice(len(X), max_n, replace=False)]
    return X


# --------------------------------------------------------------------- baselines
class IForestDet:
    name = "IForest"

    def __init__(self, n_estimators=300, sub_every=5, seed=C.SEED):
        self.m = IsolationForest(n_estimators=n_estimators, max_samples=512,
                                 random_state=seed, n_jobs=4)
        self.sub_every = sub_every

    def fit(self, Z, valid):
        X = _subsample(Z, valid, self.sub_every)
        self.m.fit(X)
        self.med = np.median(X, axis=0)
        return self

    def score(self, Z):
        s = -self.m.score_samples(Z)
        # IForest has no native attribution: use distance from the training median
        return s, np.abs(Z - self.med)


class GMMDet:
    name = "GMM"

    def __init__(self, k_grid=(4, 8, 12, 16), sub_every=5, max_n=60000, seed=C.SEED):
        self.k_grid, self.sub_every, self.max_n, self.seed = k_grid, sub_every, max_n, seed

    def fit(self, Z, valid):
        X = _subsample(Z, valid, self.sub_every, self.max_n, self.seed)
        best, self.bic = None, {}
        for k in self.k_grid:
            g = GaussianMixture(k, covariance_type="full", reg_covar=1e-3,
                                random_state=self.seed, max_iter=300).fit(X)
            self.bic[k] = float(g.bic(X))
            if best is None or self.bic[k] < min(v for kk, v in self.bic.items() if kk != k):
                best = g
        self.m = best
        self.k = best.n_components
        self.prec = best.precisions_                                   # [K, F, F]
        return self

    def score(self, Z):
        s = -self.m.score_samples(Z)
        k = self.m.predict(Z)
        # per-feature share of the squared Mahalanobis distance to the responsible component
        # (d_i * (P d)_i sums to d' P d, so the attribution is consistent with the full covariance);
        # negative shares (features that cancel a correlated deviation) are clipped to 0
        d = Z.astype("float64") - self.m.means_[k]
        contrib = np.zeros_like(d)
        for j in range(self.k):
            m = k == j
            if m.any():
                contrib[m] = d[m] * (d[m] @ self.prec[j])
        return s, np.clip(contrib, 0, None)


# --------------------------------------------------------------------- neural
class _MLPAE(nn.Module):
    def __init__(self, d, hidden=(64, 32), latent=8):
        super().__init__()
        enc, last = [], d
        for h in hidden:
            enc += [nn.Linear(last, h), nn.ReLU()]
            last = h
        enc += [nn.Linear(last, latent)]
        dec, last = [], latent
        for h in reversed(hidden):
            dec += [nn.Linear(last, h), nn.ReLU()]
            last = h
        dec += [nn.Linear(last, d)]
        self.enc, self.dec = nn.Sequential(*enc), nn.Sequential(*dec)

    def forward(self, x):
        return self.dec(self.enc(x))


class _LSTMAE(nn.Module):
    def __init__(self, d, hidden=64, latent=16):
        super().__init__()
        self.enc = nn.LSTM(d, hidden, batch_first=True)
        self.to_lat = nn.Linear(hidden, latent)
        self.dec = nn.LSTM(latent, hidden, batch_first=True)
        self.out = nn.Linear(hidden, d)

    def forward(self, x):
        _, (h, _) = self.enc(x)
        z = self.to_lat(h[-1])
        rep = z.unsqueeze(1).repeat(1, x.shape[1], 1)
        y, _ = self.dec(rep)
        return self.out(y)


# "blocks": validation = contiguous time blocks (default). "random": random rows, which leaks
# for overlapping windows and autocorrelated 1 Hz data (kept only to reproduce the first results).
VAL_SPLIT = os.environ.get("SWAT_VAL_SPLIT", "blocks")


def _val_mask(n, seed, split=None, n_blocks=20, val_every=10):
    """Boolean mask of validation rows (about 10 %). X must be in time order for "blocks"."""
    split = split or VAL_SPLIT
    if split == "random" or n < 4 * n_blocks:
        m = np.zeros(n, bool)
        m[np.random.default_rng(seed).permutation(n)[:max(1, n // 10)]] = True
        return m
    edges = np.linspace(0, n, n_blocks + 1).astype(int)
    m = np.zeros(n, bool)
    for j in range(val_every - 1, n_blocks, val_every):
        m[edges[j]:edges[j + 1]] = True
    return m


def _train(net, X, epochs, lr, batch, seed, log_name):
    torch.manual_seed(seed)
    val = _val_mask(len(X), seed)
    Xv = torch.tensor(X[val])
    Xt = torch.tensor(X[~val])
    opt = torch.optim.Adam(net.parameters(), lr=lr)
    best, best_state, patience, history = np.inf, None, 0, []
    t0 = time.time()
    for ep in range(epochs):
        net.train()
        perm = torch.randperm(len(Xt))
        for i in range(0, len(Xt), batch):
            xb = Xt[perm[i:i + batch]]
            loss = ((net(xb) - xb) ** 2).mean()
            opt.zero_grad()
            loss.backward()
            opt.step()
        net.eval()
        with torch.no_grad():
            vl = float(((net(Xv) - Xv) ** 2).mean())
        history.append(vl)
        if vl < best - 1e-5:
            best, best_state, patience = vl, {k: v.clone() for k, v in net.state_dict().items()}, 0
        else:
            patience += 1
            if patience >= 5:
                break
    if best_state is None:     # validation loss never improved (e.g. NaN): keep the current weights
        print(f"  [{log_name}] WARNING: validation loss never improved, keeping the last weights")
    else:
        net.load_state_dict(best_state)
    print(f"  [{log_name}] {ep + 1} epochs, best val MSE {best:.4f}, {time.time() - t0:.0f}s")
    return history


class AEDet:
    name = "AE"

    def __init__(self, sub_every=2, epochs=60, lr=1e-3, batch=512, seed=C.SEED):
        self.sub_every, self.epochs, self.lr, self.batch, self.seed = sub_every, epochs, lr, batch, seed

    def fit(self, Z, valid):
        X = _subsample(Z, valid, self.sub_every).astype("float32")
        self.net = _MLPAE(X.shape[1])
        self.history = _train(self.net, X, self.epochs, self.lr, self.batch, self.seed, self.name)
        return self

    def score(self, Z):
        with torch.no_grad():
            Zt = torch.tensor(Z.astype("float32"))
            err = np.concatenate([((self.net(Zt[i:i + 65536]) - Zt[i:i + 65536]) ** 2).numpy()
                                  for i in range(0, len(Zt), 65536)])
        return err.mean(1), err


class _WindowDet:
    """Shared logic of the two window models."""
    name = "window"

    def __init__(self, win=30, every=4, train_step=10, epochs=40, lr=1e-3, batch=256,
                 score_step=1, seed=C.SEED):
        self.win, self.every, self.train_step = win, every, train_step
        self.epochs, self.lr, self.batch, self.seed = epochs, lr, batch, seed
        self.score_step = score_step

    def _net(self, d):
        raise NotImplementedError

    def _fwd(self, xb):
        return self.net(xb)

    def fit(self, Z, valid):
        W, _ = make_windows(Z.astype("float32"), self.win, self.train_step, self.every, valid)
        self.net = self._net(Z.shape[1])
        self.history = _train(self.net, W, self.epochs, self.lr, self.batch, self.seed, self.name)
        return self

    def score(self, Z):
        Z = Z.astype("float32")
        T, F = Z.shape
        span = (self.win - 1) * self.every
        ends = np.arange(span, T, self.score_step)
        offs = np.arange(-span, 1, self.every)
        contrib = np.full((T, F), np.nan, dtype="float32")
        self.net.eval()
        with torch.no_grad():
            for i in range(0, len(ends), 4096):
                e = ends[i:i + 4096]
                xb = torch.tensor(Z[e[:, None] + offs[None, :]])
                err = ((self._fwd(xb) - xb) ** 2).numpy()
                # weight recent samples more so the score reacts faster to onsets
                w = np.linspace(0.5, 1.5, self.win, dtype="float32")[None, :, None]
                contrib[e] = (err * w).mean(1)
        # rows before the first full window / between score steps: carry values
        contrib = _ffill_rows(contrib)
        return contrib.mean(1), contrib


def _ffill_rows(a):
    mask = np.isnan(a[:, 0])
    idx = np.where(~mask, np.arange(len(a)), 0)
    np.maximum.accumulate(idx, out=idx)
    out = a[idx]
    first = np.flatnonzero(~mask)[0]
    out[:first] = a[first]
    return out


class WindowAEDet(_WindowDet):
    """MLP autoencoder on a flattened 2-minute window."""
    name = "WinAE"

    def _net(self, d):
        self.d = d
        return _MLPAE(d * self.win, hidden=(256, 64), latent=16)

    def _fwd(self, xb):
        n = xb.shape[0]
        return self.net(xb.reshape(n, -1)).reshape(xb.shape)

    def fit(self, Z, valid):
        W, _ = make_windows(Z.astype("float32"), self.win, self.train_step, self.every, valid)
        self.net = self._net(Z.shape[1])
        Wf = W.reshape(len(W), -1)

        class _Wrap(nn.Module):  # train on flattened windows
            def __init__(s, net):
                super().__init__()
                s.net = net

            def forward(s, x):
                return s.net(x)
        self.history = _train(_Wrap(self.net), Wf, self.epochs, self.lr, self.batch, self.seed, self.name)
        return self


class LSTMAEDet(_WindowDet):
    """Sequence-to-sequence LSTM autoencoder on a 2-minute window."""
    name = "LSTM-AE"

    def _net(self, d):
        return _LSTMAE(d)


MODELS = {"IForest": IForestDet, "GMM": GMMDet, "AE": AEDet,
          "WinAE": WindowAEDet, "LSTM-AE": LSTMAEDet}
