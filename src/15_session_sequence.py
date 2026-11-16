"""
STEP 15: Session-wise evaluation of the sequence models + RNN and GRU.
Same 3 session-wise folds as step 14 (each fold holds out one whole conversation
per language). Every model reads the 25 frames of each 1-second window:
  CNN (VGG-style) - best CNN from step 11
  Simple RNN      - basic recurrent net (suffers from vanishing gradients)
  LSTM            - RNN with gates + a memory cell
  GRU             - lighter LSTM: 2 gates instead of 3, no separate memory cell
  Transformer     - self-attention encoder from step 12
Input:  data/features/noxi_sequences.npy + data/features/noxi_engagement.parquet
Output: reports/session_sequence.csv
"""

# silence TensorFlow (must be set before it is imported)
import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
import logging
logging.getLogger("tensorflow").setLevel(logging.ERROR)

import numpy as np
import pandas as pd
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error

FEAT = os.path.join("data", "features", "noxi_engagement.parquet")
SEQ = os.path.join("data", "features", "noxi_sequences.npy")
os.makedirs("reports", exist_ok=True)
EPOCHS = 20


# metric: 1.0 = perfect
def ccc(yt, yp):
    yt, yp = np.asarray(yt), np.asarray(yp)
    cov = ((yt - yt.mean()) * (yp - yp.mean())).mean()
    return (2 * cov) / (yt.var() + yp.var() + (yt.mean() - yp.mean()) ** 2 + 1e-9)


# load; drop the 5 OpenFace bookkeeping columns (voice is 0-87, so face_0..4 = 88..92)
meta = pd.read_parquet(FEAT, columns=["engagement", "language", "session"])
y = meta["engagement"].to_numpy("float32")
X = np.load(SEQ)
assert X.shape[2] == 802
X = np.delete(X, range(88, 93), axis=2)
n_steps, n_feat = X.shape[1], X.shape[2]

# same 3 folds as step 14
sess = meta.groupby("language")["session"].unique().apply(sorted)
folds = [[s[k] for s in sess] for k in range(3)]
print(f"sequences {X.shape}, folds: {folds}\n", flush=True)


# same small head on top of every model
def head(x):
    x = layers.Dropout(0.1)(x)
    x = layers.Dense(64, activation="relu")(x)
    return layers.Dense(1)(x)


def cnn():
    inp = layers.Input(shape=(n_steps, n_feat))
    x = inp
    for f in (32, 64):
        x = layers.Conv1D(f, 3, padding="same", activation="relu")(x)
        x = layers.Conv1D(f, 3, padding="same", activation="relu")(x)
        x = layers.MaxPooling1D(2)(x)
    return keras.Model(inp, head(layers.Flatten()(x)), name="CNN_VGG")


def rnn():
    inp = layers.Input(shape=(n_steps, n_feat))
    return keras.Model(inp, head(layers.SimpleRNN(128)(inp)), name="SimpleRNN")


def lstm():
    inp = layers.Input(shape=(n_steps, n_feat))
    return keras.Model(inp, head(layers.LSTM(128)(inp)), name="LSTM")


def gru():
    inp = layers.Input(shape=(n_steps, n_feat))
    return keras.Model(inp, head(layers.GRU(128)(inp)), name="GRU")


# Transformer from step 12: learned positional encoding + 2 encoder blocks
class PositionalEncoding(layers.Layer):
    def __init__(self, n_steps, d_model, **kw):
        super().__init__(**kw)
        self.n_steps, self.d_model = n_steps, d_model

    def build(self, input_shape):
        self.pos = self.add_weight(shape=(self.n_steps, self.d_model),
                                   initializer="random_normal", name="pos")

    def call(self, x):
        return x + self.pos


def encoder_block(x, drop=0.1):
    attn = layers.MultiHeadAttention(num_heads=4, key_dim=16, dropout=drop)(x, x)
    x = layers.LayerNormalization(epsilon=1e-6)(layers.Add()([x, attn]))
    ff = layers.Dense(128, activation="relu")(x)
    ff = layers.Dropout(drop)(ff)
    ff = layers.Dense(64)(ff)
    return layers.LayerNormalization(epsilon=1e-6)(layers.Add()([x, ff]))


def transformer():
    inp = layers.Input(shape=(n_steps, n_feat))
    x = PositionalEncoding(n_steps, 64)(layers.Dense(64)(inp))
    for _ in range(2):
        x = encoder_block(x)
    return keras.Model(inp, head(layers.GlobalAveragePooling1D()(x)), name="Transformer")


rows = []
for k, test_sess in enumerate(folds, 1):
    te = meta["session"].isin(test_sess).to_numpy()
    i_tr, i_te = np.where(~te)[0], np.where(te)[0]
    print(f"fold {k}: test sessions {test_sess} | train {len(i_tr)} | test {len(i_te)}", flush=True)

    # scale with a scaler fitted on the training frames only, clip extreme values to [-5, 5]
    sc = StandardScaler().fit(X[i_tr].reshape(-1, n_feat))
    def prep(idx):
        z = sc.transform(X[idx].reshape(-1, n_feat)).reshape(len(idx), n_steps, n_feat)
        return np.clip(z, -5, 5).astype("float32")
    X_tr, X_te = prep(i_tr), prep(i_te)

    for build in (cnn, rnn, lstm, gru, transformer):
        keras.utils.set_random_seed(42)
        m = build()
        m.compile(optimizer=keras.optimizers.Adam(1e-3), loss="mse")
        m.fit(X_tr, y[i_tr], epochs=EPOCHS, batch_size=128, verbose=0)
        pred = m.predict(X_te, verbose=0).flatten()
        rows.append(dict(model=m.name, fold=k, params=m.count_params(), ccc=ccc(y[i_te], pred),
                         pearson=np.corrcoef(y[i_te], pred)[0, 1],
                         mae=mean_absolute_error(y[i_te], pred)))
        print(f"  {m.name:12s} CCC = {rows[-1]['ccc']:.3f}", flush=True)
    del X_tr, X_te
    print()


res = pd.DataFrame(rows)
res.to_csv(os.path.join("reports", "session_sequence.csv"), index=False)
summary = res.groupby("model").agg(params=("params", "first"), ccc=("ccc", "mean"),
                                   ccc_std=("ccc", "std"), pearson=("pearson", "mean"),
                                   mae=("mae", "mean")).sort_values("ccc", ascending=False)
print("=========== SEQUENCE MODELS, SESSION-WISE (mean +- std over 3 folds) ===========")
print(f"{'model':12s} {'params':>9} {'CCC':>14} {'Pearson':>8} {'MAE':>7}")
for name, r in summary.iterrows():
    print(f"{name:12s} {int(r['params']):9,d} {r['ccc']:7.3f} +- {r['ccc_std']:.3f} "
          f"{r['pearson']:8.3f} {r['mae']:7.3f}")
print("\nSaved -> reports/session_sequence.csv")
