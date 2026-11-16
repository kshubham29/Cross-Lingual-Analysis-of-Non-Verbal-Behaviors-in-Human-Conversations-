"""
STEP 8: Model comparison (TensorFlow / Keras).
The MLP sees one averaged row per second and throws away how behaviour changes
inside that second. The 1D-CNN reads the 25 frames in order instead.
All three models are scored on the same test rows, so the comparison is fair.
Input:  data/features/noxi_sequences.npy  (windows, 25, 802)
        data/features/noxi_engagement.parquet
Output: reports/sequence_results.csv + reports/noxi_cnn.keras
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
from xgboost import XGBRegressor

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


# load both views of the same windows: flat (averaged) and sequence (25 frames)
df = pd.read_parquet(FEAT)
cols = [c for c in df.columns if c.startswith(("voice_", "face_"))]
X_flat = df[cols].fillna(0).to_numpy("float32")
y = df["engagement"].to_numpy("float32")
X_seq = np.load(SEQ)
assert len(X_seq) == len(df), "sequence file and table are out of sync - rerun 02_build_features.py"
print(f"flat {X_flat.shape} | sequence {X_seq.shape}\n")

# same 80/20 split as every other step (same seed -> same test rows)
idx_tr, idx_te = train_test_split(np.arange(len(y)), test_size=0.2, random_state=42)
ytr, yte = y[idx_tr], y[idx_te]

# scale the flat features (fit on train only)
sc = StandardScaler().fit(X_flat[idx_tr])
Ftr, Fte = [sc.transform(X_flat[i]).astype("float32") for i in (idx_tr, idx_te)]

# scale the sequences frame by frame with a scaler fitted on training frames only
n_feat = X_seq.shape[2]
sc_seq = StandardScaler().fit(X_seq[idx_tr].reshape(-1, n_feat))
def scale_seq(a):
    return sc_seq.transform(a.reshape(-1, n_feat)).reshape(a.shape).astype("float32")
Str, Ste = scale_seq(X_seq[idx_tr]), scale_seq(X_seq[idx_te])
del X_seq

results = {}
def report(name, pred):
    results[name] = dict(model=name, ccc=ccc(yte, pred),
                         pearson=np.corrcoef(yte, pred)[0, 1],
                         mae=mean_absolute_error(yte, pred))
    print(f"  {name:12s} CCC = {results[name]['ccc']:.3f}", flush=True)


# 1) XGBoost on the flat features - best classic model
print("Training XGBoost...")
xgb = XGBRegressor(n_estimators=300, max_depth=6, learning_rate=0.1, subsample=0.8,
                   colsample_bytree=0.8, tree_method="hist", random_state=42, n_jobs=-1)
report("XGBoost", xgb.fit(Ftr, ytr).predict(Fte))


# 2) MLP on the flat features - the tuned settings from step 7
print("Training MLP...")
keras.utils.set_random_seed(42)
mlp = keras.Sequential([
    layers.Input(shape=(n_feat,)),
    layers.Dense(256, activation="relu"), layers.Dropout(0.1),
    layers.Dense(128, activation="relu"), layers.Dropout(0.1),
    layers.Dense(1),
])
mlp.compile(optimizer=keras.optimizers.Adam(1e-3), loss="mse")
mlp.fit(Ftr, ytr, epochs=60, batch_size=128, verbose=0)
report("MLP", mlp.predict(Fte, verbose=0).flatten())


# 3) 1D-CNN on the sequences - slides a filter along the 25 frames
print("Training 1D-CNN...")
keras.utils.set_random_seed(42)
cnn = keras.Sequential([
    layers.Input(shape=(25, n_feat)),
    layers.Conv1D(128, kernel_size=3, activation="relu"),
    layers.Conv1D(64, kernel_size=3, activation="relu"),
    layers.GlobalAveragePooling1D(),
    layers.Dropout(0.1),
    layers.Dense(64, activation="relu"),
    layers.Dense(1),
])
cnn.compile(optimizer=keras.optimizers.Adam(1e-3), loss="mse")
cnn.fit(Str, ytr, epochs=EPOCHS, batch_size=128, verbose=0)
report("1D-CNN", cnn.predict(Ste, verbose=0).flatten())
cnn.save(os.path.join("reports", "noxi_cnn.keras"))


# final table: flat models vs the sequence model, same test set
res = pd.DataFrame(results.values())
res["uses_time"] = res["model"] == "1D-CNN"
res.to_csv(os.path.join("reports", "sequence_results.csv"), index=False)
print("\n============ FLAT vs SEQUENCE (same test set) ============")
print(f"{'model':12s} {'time?':>6} {'CCC':>7} {'Pearson':>8} {'MAE':>7}")
for _, r in res.iterrows():
    print(f"{r['model']:12s} {'yes' if r['uses_time'] else 'no':>6} "
          f"{r['ccc']:7.3f} {r['pearson']:8.3f} {r['mae']:7.3f}")
print("\nSaved -> reports/sequence_results.csv, noxi_cnn.keras")
