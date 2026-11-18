"""Figures for the report (outputs/figures/)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from swatad import config as C  # noqa: E402
from swatad import data as D  # noqa: E402

MODELS = ["IForest", "GMM", "AE", "WinAE", "LSTM-AE"]
COL = {"IForest": "#2a78d6", "GMM": "#eb6834", "AE": "#1baf7a", "WinAE": "#eda100",
       "LSTM-AE": "#e87ba4", "Rules only": "#52514e"}
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.grid": True,
                     "grid.color": GRID, "grid.linewidth": 0.6, "axes.spines.top": False,
                     "axes.spines.right": False, "figure.dpi": 130})
FIG = C.OUT_DIR / "figures"
FIG.mkdir(parents=True, exist_ok=True)
PRIMARY = sys.argv[1] if len(sys.argv) > 1 else "a12_A11-A10_noAIT"


def timeline(run=PRIMARY):
    rd = C.OUT_DIR / "runs" / run
    sc = pd.read_parquet(rd / "scores.parquet")
    meta = json.loads((rd / "meta.json").read_text())
    al = D.a12_attacks()
    fig, axes = plt.subplots(len(MODELS) + 1, 1, figsize=(11, 9), sharex=True)
    t = sc.index
    for ax, m in zip(axes, MODELS):
        thr = meta["thresholds"][m]["calib"]
        r = np.clip(sc[m].values / thr, 1e-2, None)
        ax.plot(t, r, color=COL[m], lw=0.8)
        ax.axhline(1, color=INK, lw=0.8, ls="--")
        ax.set_yscale("log")
        ax.set_ylabel(f"{m}\nscore / thr", fontsize=8)
        for _, a in al.iterrows():
            ax.axvspan(a.start, a.end, color="#e34948", alpha=0.12, lw=0)
    ax = axes[-1]
    ax.fill_between(t, 0, sc["_rule_any"].astype(int), step="post", color=COL["Rules only"], alpha=0.6)
    ax.set_ylabel("rule\nalarm", fontsize=8)
    for _, a in al.iterrows():
        ax.axvspan(a.start, a.end, color="#e34948", alpha=0.12, lw=0)
        axes[0].text(a.start, axes[0].get_ylim()[1], str(a.attack_id), fontsize=7, color=INK, va="bottom")
    for ax in axes:
        ax.axvspan(t[0], pd.Timestamp(f"2026-03-11 {C.A12_EVAL_FROM}"), color=GRID, alpha=0.5, lw=0)
    axes[0].set_title(f"A12 anomaly scores ({run}); red = labelled attacks, grey = calibration / not evaluated",
                      fontsize=9, loc="left")
    fig.tight_layout()
    fig.savefig(FIG / "a12_score_timeline.png")
    plt.close(fig)


def summary_bars():
    m = pd.read_csv(C.OUT_DIR / "metrics_all.csv")
    m = m[m.variant.isin(["model", "model+rules", "rules"])]
    g = m.groupby(["run", "model", "variant"])[["auc_roc", "event_recall", "fpr_clean"]].agg(["mean", "std"])
    runs = [r for r in ["a12_A11_noAIT", "a12_A11_all", "a12_A11-A10_noAIT", "a12_A11-A10_all",
                        "s2015_normal_noAIT", "s2015_normal_all"] if r in m.run.unique()]
    fig, axes = plt.subplots(2, 1, figsize=(11, 6.5), sharex=True)
    width = 0.15
    for ax, metric, label in [(axes[0], "auc_roc", "AUC-ROC (model score)"),
                              (axes[1], "event_recall", "Event recall (model alone)")]:
        for i, mod in enumerate(MODELS):
            vals, errs = [], []
            for r in runs:
                try:
                    vals.append(g.loc[(r, mod, "model"), (metric, "mean")])
                    errs.append(g.loc[(r, mod, "model"), (metric, "std")])
                except KeyError:
                    vals.append(np.nan)
                    errs.append(0)
            x = np.arange(len(runs)) + (i - 2) * width
            ax.bar(x, vals, width * 0.9, yerr=errs, color=COL[mod], label=mod,
                   error_kw={"lw": 0.8, "ecolor": MUTED})
        ax.set_ylabel(label)
        ax.set_ylim(0, 1.05)
    axes[0].legend(ncol=5, frameon=False, loc="upper left", bbox_to_anchor=(0, 1.18))
    axes[1].set_xticks(np.arange(len(runs)))
    axes[1].set_xticklabels([r.replace("_", "\n", 1) for r in runs], fontsize=8)
    fig.suptitle("Detectors across setups (mean ± std over 3 seeds)", x=0.01, ha="left", fontsize=10)
    fig.tight_layout()
    fig.savefig(FIG / "model_comparison.png")
    plt.close(fig)


def attack_matrix(run=PRIMARY):
    m = pd.read_csv(C.OUT_DIR / "runs" / run / "metrics.csv", dtype={"detected_ids": str})
    m = m[(m.seed == 0) & m.variant.isin(["model", "model+rules", "rules"])]
    rows = []
    for _, r in m.iterrows():
        det = set(str(r.detected_ids).split(",")) if isinstance(r.detected_ids, str) else set()
        rows.append([1 if str(a) in det else 0 for a in range(1, 12)])
    labels = [f"{r.model} ({r.variant})" if r.variant != "rules" else "Rules only" for _, r in m.iterrows()]
    A = np.array(rows)
    fig, ax = plt.subplots(figsize=(7.5, 0.32 * len(labels) + 1.2))
    ax.imshow(A, cmap=matplotlib.colors.ListedColormap(["#f3f2ef", "#2a78d6"]), aspect="auto")
    ax.set_xticks(range(11))
    ax.set_xticklabels([str(i) for i in range(1, 12)])
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel("A12 attack #  (blue = detected: alarm onset inside attack window + 5 min)")
    ax.grid(False)
    ax.set_xticks(np.arange(-.5, 11, 1), minor=True)
    ax.set_yticks(np.arange(-.5, len(labels), 1), minor=True)
    ax.grid(which="minor", color="white", lw=2)
    ax.tick_params(which="minor", length=0)
    ax.set_title(f"Per-attack detection, {run}, seed 0", fontsize=9, loc="left")
    fig.tight_layout()
    fig.savefig(FIG / "a12_attack_matrix.png")
    plt.close(fig)


def synthetic_heatmap():
    p = C.OUT_DIR / "synthetic" / "synthetic_summary.csv"
    if not p.exists():
        return
    s = pd.read_csv(p)
    for var in ["model", "model+rules"]:
        pv = s[(s.variant == var)].pivot(index="type", columns="model", values="recall")[MODELS]
        fig, ax = plt.subplots(figsize=(6.5, 3.6))
        ax.imshow(pv.values, cmap="Blues", vmin=0, vmax=1, aspect="auto")
        for i in range(pv.shape[0]):
            for j in range(pv.shape[1]):
                v = pv.values[i, j]
                ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=8,
                        color="white" if v > 0.6 else INK)
        ax.set_xticks(range(len(MODELS)))
        ax.set_xticklabels(MODELS)
        ax.set_yticks(range(len(pv.index)))
        ax.set_yticklabels(pv.index)
        ax.grid(False)
        ax.set_title(f"Synthetic injections: event recall by type ({var})", fontsize=9, loc="left")
        fig.tight_layout()
        fig.savefig(FIG / f"synthetic_recall_{var.replace('+', '_')}.png")
        plt.close(fig)


if __name__ == "__main__":
    timeline()
    attack_matrix()
    summary_bars()
    synthetic_heatmap()
    print("figures in", FIG)
