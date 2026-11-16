"""
STEP 23 (improvement 3): Longer context.
So far every prediction looks at one second only. Engagement builds up and fades
over several seconds, so here each window also gets the average behaviour of
the same speaker over the last 5 and the last 10 seconds (past only, so it would
also work live). The setting [now, last 5 s, last 10 s] is fixed in advance.
Same models, folds and smoothing as steps 21 and 22.
Input:  data/features/noxi_engagement.parquet + pretrained_<name>.npy
Output: reports/context_results.csv
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
META = [f"face_{i}" for i in range(5)]
CONTEXT = [5, 10]          # seconds of past behaviour added to each window
K_SMOOTH, CLIP = 5, 5


def ccc(yt, yp):
    yt, yp = np.asarray(yt), np.asarray(yp)
    cov = ((yt - yt.mean()) * (yp - yp.mean())).mean()
    return (2 * cov) / (yt.var() + yp.var() + (yt.mean() - yp.mean()) ** 2 + 1e-9)


def smooth(pred, groups, k):
    return pd.Series(pred).groupby(groups).transform(lambda g: g.rolling(k, min_periods=1).mean()).to_numpy()


# [now, mean of the last 5 s, mean of the last 10 s] for each speaker (rows are in time order)
def with_context(X, groups):
    parts = [X]
    frame = pd.DataFrame(X)
    for k in CONTEXT:
        parts.append(frame.groupby(groups).transform(lambda g: g.rolling(k, min_periods=1).mean()).to_numpy("float32"))
    return np.hstack(parts)


df = pd.read_parquet(FEAT)
cols = [c for c in df.columns if c.startswith(("voice_", "face_")) and c not in META]
y = df["engagement"].to_numpy("float32")
speaker = (df["session"] + "_" + df["role"]).to_numpy()
lang, session = df["language"].to_numpy(), df["session"].to_numpy()
langs = sorted(df["language"].unique())
sess = df.groupby("language")["session"].unique().apply(sorted)
folds = [[s[k] for s in sess] for k in range(3)]

own = df[cols].fillna(0).to_numpy("float32")
pre = np.concatenate([np.load(os.path.join("data", "features", f"pretrained_{p}.npy"))
                      for p in ("w2vbert2", "videomae")], axis=1)
print(f"{len(df)} windows; building context features ...", flush=True)
INPUTS = {
    "Gradient Boosting (eGeMAPS + OpenFace)": {"1 s": own, "1 s + last 5 s + last 10 s": with_context(own, speaker)},
    "w2v-BERT 2.0 + VideoMAE (dense head)": {"1 s": pre, "1 s + last 5 s + last 10 s": with_context(pre, speaker)},
}


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
for model, inputs in INPUTS.items():
    predict = gb_predict if model.startswith("Gradient") else dense_predict
    print(f"\n=== {model} ===", flush=True)
    for name, X in inputs.items():
        raw, sm = [], []
        for t in folds:
            te = np.isin(session, t)
            p = predict(X, ~te, te)
            raw.append(ccc(y[te], p))
            sm.append(ccc(y[te], smooth(p, speaker[te], K_SMOOTH)))
        r = dict(model=model, input=name, dims=X.shape[1], ccc=np.mean(raw), std=np.std(raw, ddof=1),
                 smooth_ccc=np.mean(sm), smooth_std=np.std(sm, ddof=1))
        if predict is gb_predict:
            within = [ccc(y[session == s], predict(X, (lang == l) & (session != s), session == s)) for l in langs for s in sess[l]]
            cross = [ccc(y[lang == b], predict(X, lang == a, lang == b)) for a, b in itertools.permutations(langs, 2)]
            w, c = np.mean(within), np.mean(cross)
            r.update(within_ccc=w, cross_ccc=c, drop_pct=100 * (w - c) / w)
        rows.append(r)
        extra = f" | within {r['within_ccc']:.3f} cross {r['cross_ccc']:.3f} drop {r['drop_pct']:.0f}%" if "drop_pct" in r else ""
        print(f"  {name:28s} {r['ccc']:.3f} +- {r['std']:.3f} | smoothed {r['smooth_ccc']:.3f}{extra}", flush=True)
        pd.DataFrame(rows).to_csv(os.path.join("reports", "context_results.csv"), index=False)

print("\n=========== LONGER CONTEXT, unseen conversations (3 folds) ===========")
for _, r in pd.DataFrame(rows).iterrows():
    print(f"{r['model']:40s} {r['input']:28s} {r['ccc']:.3f} +- {r['std']:.3f}  smoothed {r['smooth_ccc']:.3f}")
print("\nSaved -> reports/context_results.csv")
