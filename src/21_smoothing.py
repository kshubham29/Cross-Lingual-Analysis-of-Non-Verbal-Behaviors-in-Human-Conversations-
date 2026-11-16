"""
STEP 21 (improvement 1): Smoothing predictions over time.
Engagement changes slowly, but a model predicts every second on its own, so its
output jumps around. Here each prediction is replaced by the average of the
last k seconds of predictions for the same speaker (only past seconds, so it
would also work live).
  k = 5 seconds is fixed in advance as the main setting; other values of k are
  reported as a curve only - picking k by its test score would be cheating.
Two base models, the same 3 session-wise folds as steps 14 and 20:
  Gradient Boosting on eGeMAPS + OpenFace (step 14)
  w2v-BERT 2.0 + VideoMAE embeddings with the dense head (step 20)
Plus the cross-language test (as step 17) for Gradient Boosting.
Input:  data/features/noxi_engagement.parquet + pretrained_<name>.npy (step 19)
Output: reports/smoothing_results.csv, reports/smoothing_curve.csv
"""

# silence TensorFlow (must be set before it is imported)
import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
import logging
logging.getLogger("tensorflow").setLevel(logging.ERROR)

import itertools
import numpy as np
import pandas as pd
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.ensemble import HistGradientBoostingRegressor

FEAT = os.path.join("data", "features", "noxi_engagement.parquet")
META = [f"face_{i}" for i in range(5)]      # frame, face_id, timestamp, confidence, success
K_MAIN = 5                                  # fixed before looking at any result
K_CURVE = [1, 3, 5, 10, 15, 20, 30]
CLIP = 5


# metric: 1.0 = perfect
def ccc(yt, yp):
    yt, yp = np.asarray(yt), np.asarray(yp)
    cov = ((yt - yt.mean()) * (yp - yp.mean())).mean()
    return (2 * cov) / (yt.var() + yp.var() + (yt.mean() - yp.mean()) ** 2 + 1e-9)


# average of the last k predictions of the same speaker (rows are in time order)
def smooth(pred, groups, k):
    if k == 1:
        return pred
    s = pd.Series(pred)
    return s.groupby(groups).transform(lambda g: g.rolling(k, min_periods=1).mean()).to_numpy()


def gb_predict(tr, te):
    m = make_pipeline(StandardScaler(), HistGradientBoostingRegressor(max_iter=300, random_state=42))
    m.fit(X_own[tr], y[tr])
    return m.predict(X_own[te])


def dense_predict(tr, te):
    keras.utils.set_random_seed(42)
    m = keras.Sequential([
        layers.Input(shape=(X_pre.shape[1],)),
        layers.Dense(256, activation="relu"), layers.Dropout(0.1),
        layers.Dense(128, activation="relu"), layers.Dropout(0.1),
        layers.Dense(1),
    ])
    m.compile(optimizer=keras.optimizers.Adam(1e-3), loss="mse")
    sc = StandardScaler().fit(X_pre[tr])
    m.fit(np.clip(sc.transform(X_pre[tr]), -CLIP, CLIP), y[tr], epochs=30, batch_size=128, verbose=0)
    return m.predict(np.clip(sc.transform(X_pre[te]), -CLIP, CLIP), verbose=0).flatten()


df = pd.read_parquet(FEAT)
cols = [c for c in df.columns if c.startswith(("voice_", "face_")) and c not in META]
X_own = df[cols].fillna(0).to_numpy("float32")
X_pre = np.concatenate([np.load(os.path.join("data", "features", f"pretrained_{p}.npy"))
                        for p in ("w2vbert2", "videomae")], axis=1)
y = df["engagement"].to_numpy("float32")
speaker = (df["session"] + "_" + df["role"]).to_numpy()
lang, session = df["language"].to_numpy(), df["session"].to_numpy()
langs = sorted(df["language"].unique())
sess = df.groupby("language")["session"].unique().apply(sorted)
folds = [[s[k] for s in sess] for k in range(3)]
print(f"{len(df)} windows, {len(np.unique(speaker))} speakers, folds: {folds}\n", flush=True)

curve, rows = [], []
for name, predict in (("Gradient Boosting (eGeMAPS + OpenFace)", gb_predict),
                      ("w2v-BERT 2.0 + VideoMAE (dense head)", dense_predict)):
    print(f"=== {name} ===", flush=True)
    raw, sm = [], []
    for k_fold, t in enumerate(folds, 1):
        te = np.isin(session, t)
        pred = predict(~te, te)
        for k in K_CURVE:
            curve.append(dict(model=name, fold=k_fold, k=k, ccc=ccc(y[te], smooth(pred, speaker[te], k))))
        raw.append(ccc(y[te], pred))
        sm.append(ccc(y[te], smooth(pred, speaker[te], K_MAIN)))
        print(f"  fold {k_fold}: raw {raw[-1]:.3f} -> smoothed {sm[-1]:.3f}", flush=True)

    r = dict(model=name, raw_ccc=np.mean(raw), raw_std=np.std(raw, ddof=1),
             smooth_ccc=np.mean(sm), smooth_std=np.std(sm, ddof=1), gain=np.mean(sm) - np.mean(raw))

    # cross-language test for the tree model (as step 17): does smoothing shrink the drop?
    if predict is gb_predict:
        def both(tr, te):
            p = predict(tr, te)
            return ccc(y[te], p), ccc(y[te], smooth(p, speaker[te], K_MAIN))
        within = [both((lang == l) & (session != s), session == s) for l in langs for s in sess[l]]
        cross = [both(lang == a, lang == b) for a, b in itertools.permutations(langs, 2)]
        for i, tag in ((0, "raw"), (1, "smooth")):
            w, c = np.mean([x[i] for x in within]), np.mean([x[i] for x in cross])
            r.update({f"{tag}_within": w, f"{tag}_cross": c, f"{tag}_drop_pct": 100 * (w - c) / w})
    rows.append(r)
    print(f"  mean: raw {r['raw_ccc']:.3f} +- {r['raw_std']:.3f} -> smoothed ({K_MAIN} s) "
          f"{r['smooth_ccc']:.3f} +- {r['smooth_std']:.3f}  (gain {r['gain']:+.3f})\n", flush=True)

res = pd.DataFrame(rows)
res.to_csv(os.path.join("reports", "smoothing_results.csv"), index=False)
cv = pd.DataFrame(curve).groupby(["model", "k"])["ccc"].mean().unstack(0)
cv.to_csv(os.path.join("reports", "smoothing_curve.csv"))

print(f"=========== SMOOTHING ({K_MAIN} seconds, past only), unseen conversations ===========")
for _, r in res.iterrows():
    print(f"{r['model']:40s} {r['raw_ccc']:.3f} -> {r['smooth_ccc']:.3f}  ({r['gain']:+.3f})")
gb = res.iloc[0]
print(f"\nCross-language (Gradient Boosting): drop {gb['raw_drop_pct']:.0f}% raw -> "
      f"{gb['smooth_drop_pct']:.0f}% smoothed (within {gb['smooth_within']:.3f}, cross {gb['smooth_cross']:.3f})")
print("\nCCC by smoothing window (mean of 3 folds; for reference only):")
print(cv.round(3).to_string())
print("\nSaved -> reports/smoothing_results.csv, reports/smoothing_curve.csv")
