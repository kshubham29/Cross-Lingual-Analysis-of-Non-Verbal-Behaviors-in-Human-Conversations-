"""
STEP 11: Classic CNN architectures (TensorFlow / Keras).
LeNet, VGG and ResNet are 2-D image networks. My data is not images - it is a
sequence of 25 frames of behavioural features - so each architecture is rebuilt
with 1-D convolutions along the time axis, keeping its defining idea:
  LeNet-style  : conv -> pool -> conv -> pool -> flatten -> dense -> dense
  VGG-style    : blocks of TWO small (kernel 3) convs before each pool, deeper
  ResNet-style : residual blocks with skip connections + batch normalisation
All three use the same split, scaler and seed, so the comparison is fair.
Input:  data/features/noxi_sequences.npy + data/features/noxi_engagement.parquet
Output: reports/cnn_architectures.csv
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
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error

keras.utils.set_random_seed(42)
FEAT = os.path.join("data", "features", "noxi_engagement.parquet")
SEQ = os.path.join("data", "features", "noxi_sequences.npy")
os.makedirs("reports", exist_ok=True)
EPOCHS = 20


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


# LeNet-style: one conv per block, larger kernel, flatten into dense layers
def lenet():
    return keras.Sequential([
        layers.Input(shape=(n_steps, n_feat)),
        layers.Conv1D(32, 5, activation="relu"), layers.MaxPooling1D(2),
        layers.Conv1D(64, 5, activation="relu"), layers.MaxPooling1D(2),
        layers.Flatten(),
        layers.Dense(128, activation="relu"), layers.Dropout(0.1),
        layers.Dense(64, activation="relu"), layers.Dropout(0.1),
        layers.Dense(1),
    ], name="LeNet_style")


# VGG-style: TWO stacked kernel-3 convs before each pool (VGG's defining idea -
# small filters stacked deep instead of one large filter)
def vgg():
    return keras.Sequential([
        layers.Input(shape=(n_steps, n_feat)),
        layers.Conv1D(32, 3, padding="same", activation="relu"),
        layers.Conv1D(32, 3, padding="same", activation="relu"),
        layers.MaxPooling1D(2),
        layers.Conv1D(64, 3, padding="same", activation="relu"),
        layers.Conv1D(64, 3, padding="same", activation="relu"),
        layers.MaxPooling1D(2),
        layers.Flatten(),
        layers.Dense(128, activation="relu"), layers.Dropout(0.1),
        layers.Dense(64, activation="relu"), layers.Dropout(0.1),
        layers.Dense(1),
    ], name="VGG_style")


# ResNet-style: residual blocks. The input skips over the convolutions and is
# added back, so the block only has to learn the DIFFERENCE. This is what lets
# ResNet go deep without the gradient vanishing.
def res_block(x, filters):
    shortcut = x
    x = layers.Conv1D(filters, 3, padding="same")(x)
    x = layers.BatchNormalization()(x)
    x = layers.Activation("relu")(x)
    x = layers.Conv1D(filters, 3, padding="same")(x)
    x = layers.BatchNormalization()(x)
    x = layers.Add()([shortcut, x])          # the skip connection
    return layers.Activation("relu")(x)


def resnet():
    inp = layers.Input(shape=(n_steps, n_feat))
    x = layers.Conv1D(64, 5, padding="same", activation="relu")(inp)
    x = layers.MaxPooling1D(2)(x)
    x = res_block(x, 64)
    x = res_block(x, 64)
    x = layers.GlobalAveragePooling1D()(x)
    x = layers.Dropout(0.1)(x)
    x = layers.Dense(64, activation="relu")(x)
    out = layers.Dense(1)(x)
    return keras.Model(inp, out, name="ResNet_style")


rows = []
for build in (lenet, vgg, resnet):
    keras.utils.set_random_seed(42)          # same start for every architecture
    m = build()
    m.compile(optimizer=keras.optimizers.Adam(1e-3), loss="mse")
    print(f"Training {m.name} ({m.count_params():,} params)...", flush=True)
    m.fit(X_tr, y_tr, epochs=EPOCHS, batch_size=128, verbose=0)
    val = ccc(y_va, m.predict(X_va, verbose=0).flatten())
    pred = m.predict(X_te, verbose=0).flatten()
    rows.append(dict(model=m.name, params=m.count_params(), val_ccc=val,
                     test_ccc=ccc(y_te, pred), pearson=np.corrcoef(y_te, pred)[0, 1],
                     mae=mean_absolute_error(y_te, pred)))
    print(f"  val CCC = {val:.3f} | test CCC = {rows[-1]['test_ccc']:.3f}\n", flush=True)
    m.save(os.path.join("reports", f"noxi_{m.name.lower()}.keras"))

res = pd.DataFrame(rows).sort_values("test_ccc", ascending=False).reset_index(drop=True)
res.to_csv(os.path.join("reports", "cnn_architectures.csv"), index=False)
print("=========== CNN ARCHITECTURES (1-D versions, same test set) ===========")
print(f"{'model':14s} {'params':>10} {'val CCC':>8} {'test CCC':>9} {'Pearson':>8} {'MAE':>7}")
for _, r in res.iterrows():
    print(f"{r['model']:14s} {r['params']:10,d} {r['val_ccc']:8.3f} "
          f"{r['test_ccc']:9.3f} {r['pearson']:8.3f} {r['mae']:7.3f}")
print("\nSaved -> reports/cnn_architectures.csv")
