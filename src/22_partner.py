"""
STEP 22 (improvement 2): The partner's behaviour (dyadic features).
Engagement is social: how lively the expert is may change how engaged the novice
is, and the other way round. For every 1-second window we add the OTHER
speaker's features at the same second (never their engagement label).
Three inputs, same models and folds as step 21:
  self           - this speaker only (as before)
  self + partner - both speakers side by side
  partner only   - can you read my engagement from the other person alone?
Both speakers of a conversation are always in the same fold, so nothing leaks.
Input:  data/noxi/ (to rebuild window positions) + noxi_engagement.parquet + pretrained_<name>.npy
Output: reports/partner_results.csv
"""

# silence TensorFlow (must be set before it is imported)
import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
import logging
logging.getLogger("tensorflow").setLevel(logging.ERROR)

import itertools
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.ensemble import HistGradientBoostingRegressor

NOXI_ROOT = os.path.join("data", "noxi")
FEAT = os.path.join("data", "features", "noxi_engagement.parquet")
META = [f"face_{i}" for i in range(5)]
WINDOW, K_SMOOTH, CLIP = 25, 5, 5


def ccc(yt, yp):
    yt, yp = np.asarray(yt), np.asarray(yp)
    cov = ((yt - yt.mean()) * (yp - yp.mean())).mean()
    return (2 * cov) / (yt.var() + yp.var() + (yt.mean() - yp.mean()) ** 2 + 1e-9)


def smooth(pred, groups, k):
    return pd.Series(pred).groupby(groups).transform(lambda g: g.rolling(k, min_periods=1).mean()).to_numpy()


def read_stream(header_path):
    dim = int(ET.parse(header_path).getroot().find("info").get("dim"))
    data = np.fromfile(header_path + "~", dtype=np.float32)
    return data[: data.size // dim * dim].reshape(-1, dim)


# rebuild the window position (second w) of every row, exactly as step 2 kept them
win = []
for sess in sorted(os.listdir(NOXI_ROOT)):
    folder = os.path.join(NOXI_ROOT, sess)
    for role in ("expert", "novice"):
        eng_path = os.path.join(folder, f"{role}.engagement.annotation.csv")
        if not os.path.exists(eng_path):
            continue
        ege = read_stream(os.path.join(folder, f"{role}.audio.egemapsv2.stream"))
        face = read_stream(os.path.join(folder, f"{role}.openface2.stream"))
        y_raw = pd.to_numeric(pd.read_csv(eng_path, header=None).iloc[:, 0], errors="coerce").to_numpy("float32")
        T = min(len(ege), len(y_raw), len(face))
        win += [w for w in range(T // WINDOW) if not np.isnan(np.nanmean(y_raw[w * WINDOW:(w + 1) * WINDOW]))]

df = pd.read_parquet(FEAT)
assert len(win) == len(df), "window positions do not line up with the feature table"
df["second"] = win

# row of the partner at the same second (-1 when the partner has no window there)
idx = {(s, r, w): i for i, (s, r, w) in enumerate(zip(df.session, df.role, df.second))}
other = {"expert": "novice", "novice": "expert"}
partner = np.array([idx.get((s, other[r], w), -1) for s, r, w in zip(df.session, df.role, df.second)])
has = partner >= 0
print(f"{len(df)} windows; partner found at the same second for {100 * has.mean():.1f}%", flush=True)


def with_partner(X):
    P = np.where(has[:, None], X[np.maximum(partner, 0)], 0).astype("float32")
    return P


cols = [c for c in df.columns if c.startswith(("voice_", "face_")) and c not in META]
own = df[cols].fillna(0).to_numpy("float32")
pre = np.concatenate([np.load(os.path.join("data", "features", f"pretrained_{p}.npy"))
                      for p in ("w2vbert2", "videomae")], axis=1)
flag = has.astype("float32")[:, None]
INPUTS = {
    "Gradient Boosting (eGeMAPS + OpenFace)": {
        "self": own, "self + partner": np.hstack([own, with_partner(own), flag]), "partner only": np.hstack([with_partner(own), flag])},
    "w2v-BERT 2.0 + VideoMAE (dense head)": {
        "self": pre, "self + partner": np.hstack([pre, with_partner(pre), flag]), "partner only": np.hstack([with_partner(pre), flag])},
}

y = df["engagement"].to_numpy("float32")
speaker = (df["session"] + "_" + df["role"]).to_numpy()
lang, session = df["language"].to_numpy(), df["session"].to_numpy()
langs = sorted(df["language"].unique())
sess = df.groupby("language")["session"].unique().apply(sorted)
folds = [[s[k] for s in sess] for k in range(3)]


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
        # cross-language test for the tree model
        if predict is gb_predict and name != "partner only":
            within = [ccc(y[session == s], predict(X, (lang == l) & (session != s), session == s)) for l in langs for s in sess[l]]
            cross = [ccc(y[lang == b], predict(X, lang == a, lang == b)) for a, b in itertools.permutations(langs, 2)]
            w, c = np.mean(within), np.mean(cross)
            r.update(within_ccc=w, cross_ccc=c, drop_pct=100 * (w - c) / w)
        rows.append(r)
        extra = f" | within {r['within_ccc']:.3f} cross {r['cross_ccc']:.3f} drop {r['drop_pct']:.0f}%" if "drop_pct" in r else ""
        print(f"  {name:15s} {r['ccc']:.3f} +- {r['std']:.3f} | smoothed {r['smooth_ccc']:.3f}{extra}", flush=True)
        pd.DataFrame(rows).to_csv(os.path.join("reports", "partner_results.csv"), index=False)

print("\n=========== PARTNER'S BEHAVIOUR, unseen conversations (3 folds) ===========")
res = pd.DataFrame(rows)
for _, r in res.iterrows():
    print(f"{r['model']:40s} {r['input']:15s} {r['ccc']:.3f} +- {r['std']:.3f}  smoothed {r['smooth_ccc']:.3f}")
print("\nSaved -> reports/partner_results.csv")
