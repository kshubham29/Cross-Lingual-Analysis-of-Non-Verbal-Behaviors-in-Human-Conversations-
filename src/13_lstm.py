"""
STEP 13: LSTM (TensorFlow / Keras).
An LSTM reads the 25 frames of each window in order and keeps a memory as it
goes, so it can use how behaviour changes over time, not just the average.
Same 60/20/20 split, scaler and seed as the CNN and Transformer, so all the
sequence models are scored on identical test rows.
Input:  data/features/noxi_sequences.npy + data/features/noxi_engagement.parquet
Output: reports/lstm_results.csv + reports/noxi_lstm.keras
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

UNITS = 128         # size of the LSTM memory
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


# the LSTM: reads frame 1 -> frame 25 in order, its final memory summarises the
# whole second; then a small dense head predicts engagement
model = keras.Sequential([
    layers.Input(shape=(n_steps, n_feat)),
    layers.LSTM(UNITS),
    layers.Dropout(0.1),
    layers.Dense(64, activation="relu"),
    layers.Dense(1),
], name="LSTM")
model.compile(optimizer=keras.optimizers.Adam(1e-3), loss="mse")
print("============ ARCHITECTURE ============")
model.summary()

# train 20 epochs, in 4 stages of 5 so we can watch the score
print(f"\nTraining LSTM ({model.count_params():,} params)...", flush=True)
for stage in range(4):
    model.fit(X_tr, y_tr, epochs=EPOCHS // 4, batch_size=128, verbose=0)
    p = model.predict(X_va, verbose=0).flatten()
    print(f"  epoch {(stage + 1) * (EPOCHS // 4):3d}  val CCC = {ccc(y_va, p):.3f}", flush=True)

val = ccc(y_va, model.predict(X_va, verbose=0).flatten())
pred = model.predict(X_te, verbose=0).flatten()

print("\n=========== LSTM ===========")
print(f"  units           : {UNITS}")
print(f"  parameters      : {model.count_params():,}")
print(f"  validation CCC  : {val:.3f}")
print(f"  TEST CCC        : {ccc(y_te, pred):.3f}")
print(f"  TEST Pearson    : {np.corrcoef(y_te, pred)[0, 1]:.3f}")
print(f"  TEST MAE        : {mean_absolute_error(y_te, pred):.3f}")

pd.DataFrame([dict(model="LSTM", params=model.count_params(), val_ccc=val,
                   test_ccc=ccc(y_te, pred), pearson=np.corrcoef(y_te, pred)[0, 1],
                   mae=mean_absolute_error(y_te, pred))]).to_csv(
    os.path.join("reports", "lstm_results.csv"), index=False)
model.save(os.path.join("reports", "noxi_lstm.keras"))
print("\nSaved -> reports/lstm_results.csv, reports/noxi_lstm.keras")
