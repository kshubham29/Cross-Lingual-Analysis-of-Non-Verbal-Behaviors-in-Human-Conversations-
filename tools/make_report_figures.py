"""Draws the result charts used in the final report, from the CSVs in reports/.
Run from the project folder: python tools/make_report_figures.py
Output: reports/figures/report_*.png"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np
import pandas as pd

R = lambda f: pd.read_csv(f"reports/{f}.csv")
OUT = "reports/figures"
OWN, PRE, GREY, INK, MUTED, GRID = "#3f6b35", "#c47d24", "#a9b0a3", "#1d2419", "#5d6857", "#e3e6df"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": GRID,
                     "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED,
                     "axes.spines.top": False, "axes.spines.right": False})


def save(fig, name):
    fig.savefig(os.path.join(OUT, f"report_{name}.png"), dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("saved", name)


def title(ax, main, sub):
    ax.set_title(main, loc="left", fontsize=12.5, fontweight="bold", color=INK, pad=22)
    ax.text(0, 1.02, sub, transform=ax.transAxes, fontsize=9.5, color=MUTED)


# 1. all models, unseen conversations
ms, pt = R("master_results"), R("pretrained_results")
rows = [(r.model, r.session_ccc, r.session_std, "own") for r in ms.itertuples()]
for r in pt.itertuples():
    dense = r.dense_ccc >= r.xgb_ccc
    rows.append((f"{r.model} ({'dense' if dense else 'XGB'} head)",
                 r.dense_ccc if dense else r.xgb_ccc, r.dense_std if dense else r.xgb_std, "pre"))
df = pd.DataFrame(rows, columns=["model", "ccc", "std", "kind"]).sort_values("ccc")
fig, ax = plt.subplots(figsize=(8.6, 7.2))
y = np.arange(len(df))
ax.barh(y, df.ccc, height=0.62, color=[OWN if k == "own" else PRE for k in df.kind])
ax.errorbar(df.ccc, y, xerr=df["std"], fmt="none", ecolor=MUTED, elinewidth=0.8, capsize=2)
for yi, (c, s) in enumerate(zip(df.ccc, df["std"])):
    ax.text(c + s + 0.012, yi, f"{c:.3f}", va="center", fontsize=8.5, color=INK)
ax.set_yticks(y, df.model, fontsize=9)
ax.set_xlim(0, 1)
ax.set_xlabel("CCC on unseen conversations (mean ± std over 3 folds)")
ax.grid(axis="x", color=GRID, linewidth=0.6)
ax.set_axisbelow(True)
ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=OWN), plt.Rectangle((0, 0), 1, 1, color=PRE)],
          labels=["trained from scratch on eGeMAPS + OpenFace", "frozen pretrained Transformer + trained head"],
          loc="upper right", frameon=False, fontsize=8.5)
best = df.iloc[-1]
title(ax, f"Pretrained audio + video Transformers lead at CCC {best.ccc:.3f}",
      "19 models, whole conversations held out")
save(fig, "all_models")

# 2. leakage: random split vs unseen conversations
lk = ms.dropna(subset=["random_split_ccc"]).sort_values("random_split_ccc")
fig, ax = plt.subplots(figsize=(8.2, 4.2))
y = np.arange(len(lk))
ax.hlines(y, lk.session_ccc, lk.random_split_ccc, color=GREY, linewidth=2)
ax.scatter(lk.random_split_ccc, y, color=GREY, s=46, zorder=3, label="random split (leaky)")
ax.scatter(lk.session_ccc, y, color=OWN, s=46, zorder=3, label="unseen conversations")
for yi, r in enumerate(lk.itertuples()):
    ax.text(r.random_split_ccc + 0.015, yi, f"{r.random_split_ccc:.3f}", va="center", fontsize=8.5, color=MUTED)
    ax.text(r.session_ccc - 0.015, yi, f"{r.session_ccc:.3f}", va="center", ha="right", fontsize=8.5, color=INK)
ax.set_yticks(y, lk.model)
ax.set_xlim(0, 1.05)
ax.set_xlabel("CCC")
ax.grid(axis="x", color=GRID, linewidth=0.6)
ax.set_axisbelow(True)
ax.legend(loc="lower right", frameon=False, fontsize=8.5)
gap = (lk.random_split_ccc - lk.session_ccc)
title(ax, f"A random split inflates CCC by up to {gap.max():.2f}",
      "same models, two ways of splitting the data")
save(fig, "leakage")

# 3. cross-lingual matrix
cm = R("noxi_crosslingual_ccc").set_index("Unnamed: 0")
langs = list(cm.columns)
m = cm.to_numpy()
diag = np.trace(m) / 3
off = (m.sum() - np.trace(m)) / 6
fig, ax = plt.subplots(figsize=(5.4, 4.4))
im = ax.imshow(m, cmap="Greens", vmin=0, vmax=0.8)
for i in range(3):
    for j in range(3):
        ax.text(j, i, f"{m[i, j]:.3f}", ha="center", va="center", fontsize=11,
                fontweight="bold" if i == j else "normal", color="white" if m[i, j] > 0.5 else INK)
ax.set_xticks(range(3), langs)
ax.set_yticks(range(3), langs)
ax.set_xlabel("test language")
ax.set_ylabel("train language")
ax.spines[:].set_visible(False)
fig.colorbar(im, ax=ax, fraction=0.045, label="CCC")
title(ax, f"A new language costs {100 * (diag - off) / diag:.0f}%",
      f"within {diag:.3f} (diagonal) vs cross {off:.3f}, Random Forest")
save(fig, "cross_lingual")

# 4. ablation + pretrained: within vs cross language
ab = R("ablation_results")
names = {"voice": "voice (eGeMAPS)", "face": "face (OpenFace)", "both": "voice + face (eGeMAPS + OpenFace)"}
items = [(names[r.modality], r.within_ccc, r.cross_ccc, "own") for r in ab.itertuples()]
items += [(r.model, r.within_ccc, r.cross_ccc, "pre") for r in pt.itertuples()]
it = pd.DataFrame(items, columns=["name", "within", "cross", "kind"])
it["drop"] = 100 * (it.within - it.cross) / it.within
it = it.sort_values("drop", ascending=False)
fig, ax = plt.subplots(figsize=(8.4, 5.2))
y = np.arange(len(it))
for yi, r in enumerate(it.itertuples()):
    col = OWN if r.kind == "own" else PRE
    ax.annotate("", xy=(r.cross, yi), xytext=(r.within, yi),
                arrowprops=dict(arrowstyle="-|>", color=col, lw=1.6, mutation_scale=11))
    ax.scatter(r.within, yi, color=col, s=30, zorder=3)
    ax.text(max(r.within, r.cross) + 0.03, yi, f"{max(r.drop, 0):.0f}% drop", va="center", fontsize=8.5, color=INK)
ax.set_yticks(y, it.name)
ax.set_xlim(-0.1, 0.85)
ax.axvline(0, color=GRID, linewidth=0.8)
ax.set_xlabel("CCC: dot = same language, arrow head = other language")
ax.grid(axis="x", color=GRID, linewidth=0.6)
ax.set_axisbelow(True)
title(ax, "Speech features transferred across languages better than face and video features",
      "within-language (leave one conversation out) vs cross-language CCC, per input")
save(fig, "within_vs_cross")

# 5. transfer learning
tr = R("transfer_results")
cond = {"fine_tune": ("Fine-tune", OWN, "-"), "head_only": ("Head only", GREY, "-"),
        "zero_shot": ("Zero-shot", GREY, "--"), "scratch": ("From scratch", PRE, "-")}
g = tr.groupby("fraction")[list(cond)].mean()
fig, ax = plt.subplots(figsize=(7.4, 4.2))
for k, (lab, col, ls) in cond.items():
    ax.plot(g.index * 100, g[k], color=col, linestyle=ls, marker="o", markersize=5, linewidth=2 if k == "fine_tune" else 1.4)
    nudge = {"head_only": 0.014, "zero_shot": -0.014}.get(k, 0)
    ax.text(102, g[k].iloc[-1] + nudge, f"{lab} {g[k].iloc[-1]:.3f}", va="center", fontsize=9, color=INK)
ax.set_xticks([10, 25, 50, 100])
ax.set_xlim(5, 135)
ax.set_ylim(0, 0.7)
ax.set_xlabel("share of one target-language conversation used to adapt (%)")
ax.set_ylabel("CCC on the other two conversations")
ax.grid(color=GRID, linewidth=0.6)
title(ax, f"Fine-tuning with 10% of one conversation reaches {g.fine_tune.iloc[0]:.3f}",
      "CNN pretrained on two languages, adapted to the third; mean of 9 runs per point")
save(fig, "transfer")

# 6. pipeline diagram
fig, ax = plt.subplots(figsize=(11, 2.3))
ax.axis("off")
ax.set_aspect("equal")
steps = [("NoXi data", "9 conversations\nEN, FR, DE"), ("Features", "voice 88, face 709\n+ 6 pretrained"),
         ("Windows", "17,174 rows\n1 second each"), ("Models", "ML, ANN, CNN,\nRNN, AE, Transformers"),
         ("Evaluation", "unseen conversations\ncross-language, transfer"), ("Outputs", "tables, demo app,\npaper, report")]
w, h, gapx = 1.9, 1.0, 0.26
for i, (head, body) in enumerate(steps):
    x = i * (w + gapx)
    ax.add_patch(FancyBboxPatch((x, 0), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                                fc="#eef3ea" if i in (3, 4) else "white", ec=OWN if i in (3, 4) else GREY, lw=1.3))
    ax.text(x + w / 2, h - 0.22, head, ha="center", va="center", fontsize=10, fontweight="bold", color=INK)
    ax.text(x + w / 2, h / 2 - 0.14, body, ha="center", va="center", fontsize=7.8, color=MUTED, linespacing=1.35)
    if i < len(steps) - 1:
        ax.annotate("", xy=(x + w + gapx - 0.03, h / 2), xytext=(x + w + 0.03, h / 2),
                    arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=1.2))
ax.set_xlim(-0.05, len(steps) * (w + gapx))
ax.set_ylim(-0.1, h + 0.1)
save(fig, "pipeline")
