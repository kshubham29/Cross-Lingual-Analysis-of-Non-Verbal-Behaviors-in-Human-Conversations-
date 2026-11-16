"""
STEP 26: Is the best model REALLY better, or just lucky?
Three folds are too few for a test on fold scores, so we test on the people:
every speaker (18) is in exactly one test fold, so every model has one
prediction per second for every speaker on a conversation it never saw.
  - CCC per speaker for each model (18 values per model)
  - Wilcoxon signed-rank test on the paired differences (same speakers)
  - bootstrap 95% confidence interval of the mean difference (resampling speakers)
  - the same at conversation level (9 values) as a stricter check
  - Holm correction because several pairs are tested
Models (same settings and folds as steps 14, 23 and 24):
  A  Gradient Boosting, voice + face, 1 s                     (baseline, step 14)
  B  Gradient Boosting, voice + face + context                (step 23)
  C  Gradient Boosting, eGeMAPS + w2v-BERT + VideoMAE + context (best, step 24)
Input:  data/features/noxi_engagement.parquet + pretrained_<name>.npy
Output: reports/significance_results.csv, reports/significance_per_speaker.csv
"""
import os
import itertools
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import HistGradientBoostingRegressor

FEAT = os.path.join("data", "features", "noxi_engagement.parquet")
META = [f"face_{i}" for i in range(5)]
CONTEXT, N_BOOT = [5, 10], 10000


def ccc(yt, yp):
    yt, yp = np.asarray(yt), np.asarray(yp)
    cov = ((yt - yt.mean()) * (yp - yp.mean())).mean()
    return (2 * cov) / (yt.var() + yp.var() + (yt.mean() - yp.mean()) ** 2 + 1e-9)


def with_context(X, groups):
    frame = pd.DataFrame(X)
    return np.hstack([X] + [frame.groupby(groups).transform(lambda g: g.rolling(k, min_periods=1).mean()).to_numpy("float32")
                            for k in CONTEXT])


df = pd.read_parquet(FEAT)
cols = [c for c in df.columns if c.startswith(("voice_", "face_")) and c not in META]
voice = [c for c in df.columns if c.startswith("voice_")]
y = df["engagement"].to_numpy("float32")
speaker = (df["session"] + "_" + df["role"]).to_numpy()
session = df["session"].to_numpy()
sess = df.groupby("language")["session"].unique().apply(sorted)
folds = [[s[k] for s in sess] for k in range(3)]

own = df[cols].fillna(0).to_numpy("float32")
fused = np.hstack([df[voice].fillna(0).to_numpy("float32")] +
                  [np.load(os.path.join("data", "features", f"pretrained_{p}.npy")) for p in ("w2vbert2", "videomae")])
MODELS = {"A baseline (GB, voice + face, 1 s)": own,
          "B GB, voice + face + context": with_context(own, speaker),
          "C best (GB, fusion + context)": with_context(fused, speaker)}
print(f"{len(df)} windows, {len(np.unique(speaker))} speakers, folds {folds}", flush=True)

# out-of-fold predictions: every row is predicted once, by a model that never saw its conversation
pred = {}
for name, X in MODELS.items():
    p = np.zeros(len(y), dtype="float32")
    for t in folds:
        te = np.isin(session, t)
        m = make_pipeline(StandardScaler(), HistGradientBoostingRegressor(max_iter=300, random_state=42))
        p[te] = m.fit(X[~te], y[~te]).predict(X[te])
    pred[name] = p
    fold_ccc = [ccc(y[np.isin(session, t)], p[np.isin(session, t)]) for t in folds]
    print(f"  {name:40s} fold mean CCC {np.mean(fold_ccc):.3f} (matches earlier steps)", flush=True)

# CCC per speaker and per conversation
spk = pd.unique(speaker)
per_spk = pd.DataFrame({n: [ccc(y[speaker == s], p[speaker == s]) for s in spk] for n, p in pred.items()}, index=spk)
per_spk.index.name = "speaker"
per_spk.to_csv(os.path.join("reports", "significance_per_speaker.csv"))
per_conv = per_spk.groupby(per_spk.index.str.split("_").str[0]).mean()

rng = np.random.default_rng(42)
rows = []
for a, b in [("C", "A"), ("B", "A"), ("C", "B")]:
    na = next(n for n in pred if n.startswith(a)); nb = next(n for n in pred if n.startswith(b))
    for level, tab in (("speaker (18)", per_spk), ("conversation (9)", per_conv)):
        d = (tab[na] - tab[nb]).to_numpy()
        boot = rng.choice(d, (N_BOOT, len(d))).mean(1)
        rows.append(dict(comparison=f"{a} vs {b}", level=level, mean_a=tab[na].mean(), mean_b=tab[nb].mean(),
                         mean_diff=d.mean(), ci_low=np.percentile(boot, 2.5), ci_high=np.percentile(boot, 97.5),
                         a_better=f"{(d > 0).sum()}/{len(d)}", p_wilcoxon=wilcoxon(d).pvalue))

res = pd.DataFrame(rows)
# Holm correction over the 3 comparisons, separately for each level
for level, g in res.groupby("level"):
    order = g["p_wilcoxon"].sort_values().index
    adj, running = {}, 0.0
    for i, idx in enumerate(order):
        running = max(running, min(1.0, (len(order) - i) * res.at[idx, "p_wilcoxon"]))
        adj[idx] = running
    res.loc[list(adj), "p_holm"] = pd.Series(adj)
res["significant"] = np.where(res["p_holm"] < 0.05, "yes", "no")
res.to_csv(os.path.join("reports", "significance_results.csv"), index=False)

print("\n=========== SIGNIFICANCE (paired, same speakers; A = baseline, B = + context, C = best) ===========")
print(f"{'pair':7s} {'level':17s} {'mean A/B or C':>15s} {'diff':>7s} {'95% CI':>17s} {'better':>7s} {'p':>8s} {'p Holm':>8s} sig")
for r in res.itertuples():
    print(f"{r.comparison:7s} {r.level:17s} {r.mean_a:.3f} / {r.mean_b:.3f}   {r.mean_diff:+.3f} "
          f"[{r.ci_low:+.3f}, {r.ci_high:+.3f}] {r.a_better:>7s} {r.p_wilcoxon:8.4f} {r.p_holm:8.4f} {r.significant}")
print("\nSaved -> reports/significance_results.csv, reports/significance_per_speaker.csv")
