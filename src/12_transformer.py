

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
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error

keras.utils.set_random_seed(42)
FEAT = os.path.join("data", "features", "noxi_engagement.parquet")
SEQ = os.path.join("data", "features", "noxi_sequences.npy")
os.makedirs("reports", exist_ok=True)

D_MODEL = 64        # size each frame is projected to
HEADS = 4           # attention heads - each learns a different relationship
FF_DIM = 128        # width of the feed-forward layer inside each block
BLOCKS = 2          # encoder blocks stacked
EPOCHS = 25


# metric: 1.0 = perfect
def ccc(yt, yp):
    yt, yp = np.asarray(yt), np.asarray(yp)
    cov = ((yt - yt.mean()) * (yp - yp.mean())).mean()
    return (2 * cov) / (yt.var() + yp.var() + (yt.mean() - yp.mean()) ** 2 + 1e-9)


# load sequences, split 60/20/20, scale on training frames only
y = pd.read_parquet(FEAT, columns=["engagement"])["engagement"].to_numpy("float32")
X = np.load(SEQ)
n_steps, n_feat = X.shape[1], X.shape[2]
i_tmp, i_te = train_test_split(np.arange(len(y)), test_size=0.2, random_state=42)
i_tr, i_va = train_test_split(i_tmp, test_size=0.25, random_state=42)
sc = StandardScaler().fit(X[i_tr].reshape(-1, n_feat))
def prep(idx):
    return sc.transform(X[idx].reshape(-1, n_feat)).reshape(len(idx), n_steps, n_feat).astype("float32")
X_tr, X_va, X_te = prep(i_tr), prep(i_va), prep(i_te)
y_tr, y_va, y_te = y[i_tr], y[i_va], y[i_te]
del X
print(f"train {len(X_tr)} | val {len(X_va)} | test {len(X_te)} | input {n_steps}x{n_feat}\n", flush=True)


# self-attention has no sense of order, so every position gets its own learned
# vector added to it. This is the positional encoding.
class PositionalEncoding(layers.Layer):
    def __init__(self, n_steps, d_model, **kw):
        super().__init__(**kw)
        self.n_steps, self.d_model = n_steps, d_model

    def build(self, input_shape):
        self.pos = self.add_weight(shape=(self.n_steps, self.d_model),
                                   initializer="random_normal", name="pos")

    def call(self, x):
        return x + self.pos

    def get_config(self):
        return {**super().get_config(), "n_steps": self.n_steps, "d_model": self.d_model}


# one encoder block: attention then feed-forward, each wrapped in a residual
# connection and layer normalisation (the standard Transformer block)
def encoder_block(x, drop=0.1):
    attn = layers.MultiHeadAttention(num_heads=HEADS, key_dim=D_MODEL // HEADS, dropout=drop)(x, x)
    x = layers.LayerNormalization(epsilon=1e-6)(layers.Add()([x, attn]))
    ff = layers.Dense(FF_DIM, activation="relu")(x)
    ff = layers.Dropout(drop)(ff)
    ff = layers.Dense(D_MODEL)(ff)
    return layers.LayerNormalization(epsilon=1e-6)(layers.Add()([x, ff]))


def build():
    inp = layers.Input(shape=(n_steps, n_feat))
    # project each frame from 802 features down to D_MODEL
    x = layers.Dense(D_MODEL)(inp)
    x = PositionalEncoding(n_steps, D_MODEL)(x)
    for _ in range(BLOCKS):
        x = encoder_block(x)
    x = layers.GlobalAveragePooling1D()(x)      # summarise the 25 frames
    x = layers.Dropout(0.1)(x)
    x = layers.Dense(64, activation="relu")(x)
    return keras.Model(inp, layers.Dense(1)(x), name="Transformer")


keras.utils.set_random_seed(42)
model = build()
model.compile(optimizer=keras.optimizers.Adam(1e-3), loss="mse")
print("============ ARCHITECTURE ============")
model.summary()

print(f"\nTraining Transformer ({model.count_params():,} params)...", flush=True)
for stage in range(5):
    model.fit(X_tr, y_tr, epochs=EPOCHS // 5, batch_size=128, verbose=0)
    p = model.predict(X_va, verbose=0).flatten()
    print(f"  epoch {(stage + 1) * (EPOCHS // 5):3d}  val CCC = {ccc(y_va, p):.3f}", flush=True)

val = ccc(y_va, model.predict(X_va, verbose=0).flatten())
pred = model.predict(X_te, verbose=0).flatten()

print("\n=========== TRANSFORMER ===========")
print(f"  d_model / heads / blocks : {D_MODEL} / {HEADS} / {BLOCKS}")
print(f"  parameters      : {model.count_params():,}")
print(f"  validation CCC  : {val:.3f}")
print(f"  TEST CCC        : {ccc(y_te, pred):.3f}")
print(f"  TEST Pearson    : {np.corrcoef(y_te, pred)[0, 1]:.3f}")
print(f"  TEST MAE        : {mean_absolute_error(y_te, pred):.3f}")

pd.DataFrame([dict(model="Transformer", params=model.count_params(), val_ccc=val,
                   test_ccc=ccc(y_te, pred), pearson=np.corrcoef(y_te, pred)[0, 1],
                   mae=mean_absolute_error(y_te, pred))]).to_csv(
    os.path.join("reports", "transformer_results.csv"), index=False)
model.save(os.path.join("reports", "noxi_transformer.keras"))
print("\nSaved -> reports/transformer_results.csv, reports/noxi_transformer.keras")
