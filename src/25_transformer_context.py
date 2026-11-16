"""
STEP 25: Our own Transformer with longer context + the cross-language test.
In step 15 the Transformer read the 25 frames of ONE second. Self-attention is
built for longer sequences, and step 23 showed that past context helps the most,
so here the same Transformer reads the last 10 SECONDS of the speaker's
behaviour (one token per second, past only, so it would also work live).
  1 s  : 25 frames x 797 features (as step 15)
  10 s : 10 seconds x 797 features (mean behaviour of each second)
Both are tested on unseen conversations (3 folds, as step 15) and across
languages (within = leave one conversation out, cross = train A test B, as step 17).
Input:  data/features/noxi_engagement.parquet + noxi_sequences.npy
Output: reports/transformer_context_results.csv
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

FEAT = os.path.join("data", "features", "noxi_engagement.parquet")
SEQ = os.path.join("data", "features", "noxi_sequences.npy")
META = [f"face_{i}" for i in range(5)]
OUT = os.path.join("reports", "transformer_context_results.csv")
L_CTX, EPOCHS, CLIP = 10, 20, 5


def ccc(yt, yp):
    yt, yp = np.asarray(yt), np.asarray(yp)
    cov = ((yt - yt.mean()) * (yp - yp.mean())).mean()
    return (2 * cov) / (yt.var() + yp.var() + (yt.mean() - yp.mean()) ** 2 + 1e-9)


# same Transformer as steps 12 and 15
class PositionalEncoding(layers.Layer):
    def __init__(self, n_steps, d_model, **kw):
        super().__init__(**kw)
        self.n_steps, self.d_model = n_steps, d_model

    def build(self, input_shape):
        self.pos = self.add_weight(shape=(self.n_steps, self.d_model), initializer="random_normal", name="pos")

    def call(self, x):
        return x + self.pos


def encoder_block(x, drop=0.1):
    attn = layers.MultiHeadAttention(num_heads=4, key_dim=16, dropout=drop)(x, x)
    x = layers.LayerNormalization(epsilon=1e-6)(layers.Add()([x, attn]))
    ff = layers.Dense(128, activation="relu")(x)
    ff = layers.Dense(64)(layers.Dropout(drop)(ff))
    return layers.LayerNormalization(epsilon=1e-6)(layers.Add()([x, ff]))


def transformer(n_steps, n_feat):
    keras.utils.set_random_seed(42)
    inp = layers.Input(shape=(n_steps, n_feat))
    x = PositionalEncoding(n_steps, 64)(layers.Dense(64)(inp))
    for _ in range(2):
        x = encoder_block(x)
    x = layers.GlobalAveragePooling1D()(x)
    x = layers.Dense(64, activation="relu")(layers.Dropout(0.1)(x))
    m = keras.Model(inp, layers.Dense(1)(x))
    m.compile(optimizer=keras.optimizers.Adam(1e-3), loss="mse")
    return m


df = pd.read_parquet(FEAT)
cols = [c for c in df.columns if c.startswith(("voice_", "face_")) and c not in META]
X_sec = df[cols].fillna(0).to_numpy("float32")                 # one row per second
X_frm = np.delete(np.load(SEQ), range(88, 93), axis=2)         # 25 frames per second
y = df["engagement"].to_numpy("float32")
speaker = (df["session"] + "_" + df["role"]).to_numpy()
lang, session = df["language"].to_numpy(), df["session"].to_numpy()
langs = sorted(df["language"].unique())
sess = df.groupby("language")["session"].unique().apply(sorted)
folds = [[s[k] for s in sess] for k in range(3)]
groups = [np.where(speaker == s)[0] for s in pd.unique(speaker)]   # rows of each speaker, in time order
print(f"{len(df)} windows | 1 s input {X_frm.shape[1:]} | {L_CTX} s input ({L_CTX}, {X_sec.shape[1]})", flush=True)


# the last L_CTX seconds of each row's speaker (zeros = the training mean before the start)
def context_seq(Z):
    out = np.zeros((len(Z), L_CTX, Z.shape[1]), dtype="float32")
    for g in groups:
        for lag in range(L_CTX):
            out[g[lag:], L_CTX - 1 - lag] = Z[g[:len(g) - lag]]
    return out


def fit_predict(kind, tr, te):
    if kind == "1 s":
        sc = StandardScaler().fit(X_frm[tr].reshape(-1, X_frm.shape[2]))
        prep = lambda idx: np.clip(sc.transform(X_frm[idx].reshape(-1, X_frm.shape[2])), -CLIP, CLIP) \
            .reshape(len(idx), X_frm.shape[1], -1).astype("float32")
        X_tr, X_te = prep(np.where(tr)[0]), prep(np.where(te)[0])
    else:
        sc = StandardScaler().fit(X_sec[tr])
        S = context_seq(np.clip(sc.transform(X_sec), -CLIP, CLIP).astype("float32"))
        X_tr, X_te = S[tr], S[te]
    m = transformer(X_tr.shape[1], X_tr.shape[2])
    m.fit(X_tr, y[tr], epochs=EPOCHS, batch_size=128, verbose=0)
    return m.predict(X_te, verbose=0).flatten(), m.count_params()


rows = []
for kind in ("1 s", f"{L_CTX} s"):
    print(f"\n=== Transformer, {kind} of context ===", flush=True)
    fold_ccc = []
    for k, t in enumerate(folds, 1):
        te = np.isin(session, t)
        p, n_params = fit_predict(kind, ~te, te)
        fold_ccc.append(ccc(y[te], p))
        print(f"  fold {k}: CCC {fold_ccc[-1]:.3f}", flush=True)
    within = []
    for l in langs:
        for s in sess[l]:
            p, _ = fit_predict(kind, (lang == l) & (session != s), session == s)
            within.append(ccc(y[session == s], p))
    print(f"  within-language (9 runs): {np.mean(within):.3f}", flush=True)
    cross = []
    for a, b in itertools.permutations(langs, 2):
        p, _ = fit_predict(kind, lang == a, lang == b)
        cross.append(ccc(y[lang == b], p))
        print(f"  {a:8s} -> {b:8s} CCC {cross[-1]:.3f}", flush=True)
    w, c = np.mean(within), np.mean(cross)
    rows.append(dict(model="Transformer (own)", context=kind, params=n_params,
                     ccc=np.mean(fold_ccc), std=np.std(fold_ccc, ddof=1),
                     within_ccc=w, cross_ccc=c, drop_pct=100 * (w - c) / w))
    pd.DataFrame(rows).to_csv(OUT, index=False)
    r = rows[-1]
    print(f"  unseen conversations {r['ccc']:.3f} +- {r['std']:.3f} | within {w:.3f} | cross {c:.3f} | drop {r['drop_pct']:.0f}%", flush=True)

print("\n=========== OUR TRANSFORMER: 1 s vs 10 s of context ===========")
print(f"{'context':8s} {'params':>8} {'unseen CCC':>16} {'within':>7} {'cross':>7} {'drop':>5}")
for _, r in pd.DataFrame(rows).iterrows():
    print(f"{r['context']:8s} {int(r['params']):8,d} {r['ccc']:9.3f} +- {r['std']:.3f} "
          f"{r['within_ccc']:7.3f} {r['cross_ccc']:7.3f} {r['drop_pct']:4.0f}%")
print(f"\nSaved -> {OUT}")
