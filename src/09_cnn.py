"""
STEP 9: CNN (TensorFlow / Keras).
A LeNet-style 1D convolutional network over the 25-frame sequences:
  Conv -> Pool -> Conv -> Pool -> Flatten -> Dense -> Dense -> output
Tuned by grid search on a 60/20/20 split; only the winner is scored on TEST.
Input:  data/features/noxi_sequences.npy  (windows, 25, 802)
        data/features/noxi_engagement.parquet
Output: reports/cnn_tuning_results.csv + reports/noxi_cnn_tuned.keras
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
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error

keras.utils.set_random_seed(42)
FEAT = os.path.join("data", "features", "noxi_engagement.parquet")
SEQ = os.path.join("data", "features", "noxi_sequences.npy")
os.makedirs("reports", exist_ok=True)
EPOCHS = 15          # per config during the search


# metric: 1.0 = perfect
def ccc(yt, yp):
    yt, yp = np.asarray(yt), np.asarray(yp)
    cov = ((yt - yt.mean()) * (yp - yp.mean())).mean()
    return (2 * cov) / (yt.var() + yp.var() + (yt.mean() - yp.mean()) ** 2 + 1e-9)


# load the 25-frame sequences and the labels, split 60/20/20 (same seeds as step 7)
y = pd.read_parquet(FEAT, columns=["engagement"])["engagement"].to_numpy("float32")
X = np.load(SEQ)
assert len(X) == len(y), "sequence file and table are out of sync - rerun 02_build_features.py"
n_steps, n_feat = X.shape[1], X.shape[2]
i_tmp, i_te = train_test_split(np.arange(len(y)), test_size=0.2, random_state=42)
i_tr, i_va = train_test_split(i_tmp, test_size=0.25, random_state=42)

# scale every frame with a scaler fitted on TRAINING frames only
sc = StandardScaler().fit(X[i_tr].reshape(-1, n_feat))
def prep(idx):
    return sc.transform(X[idx].reshape(-1, n_feat)).reshape(len(idx), n_steps, n_feat).astype("float32")
X_tr, X_va, X_te = prep(i_tr), prep(i_va), prep(i_te)
y_tr, y_va, y_te = y[i_tr], y[i_va], y[i_te]
del X
print(f"train {len(X_tr)} | val {len(X_va)} | test {len(X_te)} | input {n_steps}x{n_feat}\n", flush=True)


# LeNet-style 1D-CNN: two conv+pool blocks, flatten, two dense layers, output
def build(filters, kernel, drop):
    return keras.Sequential([
        layers.Input(shape=(n_steps, n_feat)),
        layers.Conv1D(filters, kernel, activation="relu"), layers.MaxPooling1D(2),
        layers.Conv1D(filters * 2, kernel, activation="relu"), layers.MaxPooling1D(2),
        layers.Flatten(),
        layers.Dense(128, activation="relu"), layers.Dropout(drop),
        layers.Dense(64, activation="relu"), layers.Dropout(drop),
        layers.Dense(1),
    ])


# build, train and score ONE configuration on validation (seed reset so all start equal)
def run(filters, kernel, drop, epochs=EPOCHS):
    keras.utils.set_random_seed(42)
    m = build(filters, kernel, drop)
    m.compile(optimizer=keras.optimizers.Adam(1e-3), loss="mse")
    m.fit(X_tr, y_tr, epochs=epochs, batch_size=128, verbose=0)
    return ccc(y_va, m.predict(X_va, verbose=0).flatten()), m


# grid search: 2 filter sizes x 2 kernel sizes x 2 dropouts = 8 configs
FILTERS, KERNELS, DROPS = [32, 64], [3, 5], [0.1, 0.3]
rows = []
print(f"{'filters':>8} {'kernel':>7} {'dropout':>8} {'val CCC':>8}", flush=True)
for f, k, d in itertools.product(FILTERS, KERNELS, DROPS):
    val, _ = run(f, k, d)
    rows.append(dict(filters=f, kernel=k, dropout=d, val_ccc=val))
    print(f"{f:8d} {k:7d} {d:8.1f} {val:8.3f}", flush=True)

# rank and save
res = pd.DataFrame(rows).sort_values("val_ccc", ascending=False).reset_index(drop=True)
res.to_csv(os.path.join("reports", "cnn_tuning_results.csv"), index=False)
print("\n=========== CNN TUNING RESULTS (ranked by validation CCC) ===========")
print(res.to_string(index=False))

# retrain the winner for longer, then score it on the untouched test set
w = res.iloc[0]
val, model = run(int(w["filters"]), int(w["kernel"]), float(w["dropout"]), epochs=30)
pred = model.predict(X_te, verbose=0).flatten()

print("\n=========== BEST CNN ===========")
print(f"  filters   : {int(w['filters'])} -> {int(w['filters']) * 2}")
print(f"  kernel    : {int(w['kernel'])}")
print(f"  dropout   : {w['dropout']}")
print(f"  validation CCC: {val:.3f}")
print(f"  TEST CCC      : {ccc(y_te, pred):.3f}")
print(f"  TEST Pearson  : {np.corrcoef(y_te, pred)[0, 1]:.3f}")
print(f"  TEST MAE      : {mean_absolute_error(y_te, pred):.3f}")

print("\n============ ARCHITECTURE ============")
model.summary()

model.save(os.path.join("reports", "noxi_cnn_tuned.keras"))
print("\nSaved -> reports/cnn_tuning_results.csv, reports/noxi_cnn_tuned.keras")
