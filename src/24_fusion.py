"""
STEP 24 (improvement 4): Fuse the best features.
The strongest single inputs so far are eGeMAPS voice (step 17), w2v-BERT 2.0
speech and VideoMAE video (step 20). Here they go into one model together,
on 1 second and with the past context of step 23 ([now, last 5 s, last 10 s]).
Same models, folds and smoothing as steps 21-23.
Input:  data/features/noxi_engagement.parquet + pretrained_<name>.npy
Output: reports/fusion_results.csv
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
CONTEXT = [5, 10]
K_SMOOTH, CLIP = 5, 5


def ccc(yt, yp):
    yt, yp = np.asarray(yt), np.asarray(yp)
    cov = ((yt - yt.mean()) * (yp - yp.mean())).mean()
    return (2 * cov) / (yt.var() + yp.var() + (yt.mean() - yp.mean()) ** 2 + 1e-9)


def smooth(pred, groups, k):
    return pd.Series(pred).groupby(groups).transform(lambda g: g.rolling(k, min_periods=1).mean()).to_numpy()


def with_context(X, groups):
    frame = pd.DataFrame(X)
    return np.hstack([X] + [frame.groupby(groups).transform(lambda g: g.rolling(k, min_periods=1).mean()).to_numpy("float32")
                            for k in CONTEXT])


df = pd.read_parquet(FEAT)
voice = [c for c in df.columns if c.startswith("voice_")]
y = df["engagement"].to_numpy("float32")
speaker = (df["session"] + "_" + df["role"]).to_numpy()
lang, session = df["language"].to_numpy(), df["session"].to_numpy()
langs = sorted(df["language"].unique())
sess = df.groupby("language")["session"].unique().apply(sorted)
folds = [[s[k] for s in sess] for k in range(3)]

fused = np.hstack([df[voice].fillna(0).to_numpy("float32")] +
                  [np.load(os.path.join("data", "features", f"pretrained_{p}.npy")) for p in ("w2vbert2", "videomae")])
print(f"{len(df)} windows; fused input = {len(voice)} eGeMAPS + 1024 w2v-BERT + 1408 VideoMAE = {fused.shape[1]}", flush=True)
INPUTS = {"fusion, 1 s": fused, "fusion, 1 s + last 5 s + last 10 s": with_context(fused, speaker)}


def gb_predict(X, tr, te):
    m = make_pipeline(StandardScaler(), HistGradientBoostingRegressor(max_iter=300, random_state=42))
    return m.fit(X[tr], y[tr]).predict(X[te])


def dense_predict(X, tr, te):
    keras.utils.set_random_seed(42)
    m = keras.Sequential([layers.Input(shape=(X.shape[1],)),
                          layers.Dense(256, activation="relu"), layers.Dropout(0.1),
                          layers.Dense(128, activation="relu"), layers.Dropout(0.1), layers.Dense(1)])
    m.compile(optimizer=keras.optimizers.Adam(1e-3), loss="mse")
    sc = StandardScaler().fit(X[tr])
    m.fit(np.clip(sc.transform(X[tr]), -CLIP, CLIP), y[tr], epochs=30, batch_size=128, verbose=0)
    return m.predict(np.clip(sc.transform(X[te]), -CLIP, CLIP), verbose=0).flatten()


rows = []
for head, predict in (("Gradient Boosting", gb_predict), ("dense head", dense_predict)):
    print(f"\n=== {head} ===", flush=True)
    for name, X in INPUTS.items():
        raw, sm = [], []
        for t in folds:
            te = np.isin(session, t)
            p = predict(X, ~te, te)
            raw.append(ccc(y[te], p))
            sm.append(ccc(y[te], smooth(p, speaker[te], K_SMOOTH)))
        r = dict(model=head, input=name, dims=X.shape[1], ccc=np.mean(raw), std=np.std(raw, ddof=1),
                 smooth_ccc=np.mean(sm), smooth_std=np.std(sm, ddof=1))
        # cross-language test for the tree model with context (the candidate best)
        if predict is gb_predict and "last 5 s" in name:
            within = [ccc(y[session == s], predict(X, (lang == l) & (session != s), session == s)) for l in langs for s in sess[l]]
            cross = [ccc(y[lang == b], predict(X, lang == a, lang == b)) for a, b in itertools.permutations(langs, 2)]
            w, c = np.mean(within), np.mean(cross)
            r.update(within_ccc=w, cross_ccc=c, drop_pct=100 * (w - c) / w)
        rows.append(r)
        extra = f" | within {r['within_ccc']:.3f} cross {r['cross_ccc']:.3f} drop {r['drop_pct']:.0f}%" if "drop_pct" in r else ""
        print(f"  {name:36s} {r['ccc']:.3f} +- {r['std']:.3f} | smoothed {r['smooth_ccc']:.3f}{extra}", flush=True)
        pd.DataFrame(rows).to_csv(os.path.join("reports", "fusion_results.csv"), index=False)

print("\n=========== FUSION (eGeMAPS + w2v-BERT 2.0 + VideoMAE), unseen conversations ===========")
for _, r in pd.DataFrame(rows).iterrows():
    print(f"{r['model']:18s} {r['input']:36s} {r['ccc']:.3f} +- {r['std']:.3f}  smoothed {r['smooth_ccc']:.3f}")
print("\nSaved -> reports/fusion_results.csv")
