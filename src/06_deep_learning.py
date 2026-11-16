
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

keras.utils.set_random_seed(42)          # reproducible weights
FEATURES = os.path.join("data", "features", "noxi_engagement.parquet")
os.makedirs("reports", exist_ok=True)


# metric: 1.0 = perfect
def ccc(yt, yp):
    yt, yp = np.asarray(yt), np.asarray(yp)
    cov = ((yt - yt.mean()) * (yp - yp.mean())).mean()
    return (2 * cov) / (yt.var() + yp.var() + (yt.mean() - yp.mean()) ** 2 + 1e-9)


# load data: X = 802 voice+face features, y = engagement (0-1)
df = pd.read_parquet(FEATURES)
cols = [c for c in df.columns if c.startswith(("voice_", "face_"))]
X = df[cols].fillna(0).to_numpy("float32")
y = df["engagement"].to_numpy("float32")

# 80/20 split, then scale (scaler fitted on train only)
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42)
sc = StandardScaler().fit(Xtr)
Xtr, Xte = [sc.transform(a).astype("float32") for a in (Xtr, Xte)]

# baseline to beat (my best classic model), trained on identical data
xgb_pred = XGBRegressor(n_estimators=300, max_depth=6, learning_rate=0.1, subsample=0.8, colsample_bytree=0.8, tree_method="hist",  random_state=42, n_jobs=-1).fit(Xtr, ytr).predict(Xte)

# the ANN: 802 -> 256 -> 128 -> 1
model = keras.Sequential([
    layers.Input(shape=(Xtr.shape[1],)),
    layers.Dense(256, activation="relu"), layers.Dropout(0.3),
    layers.Dense(128, activation="relu"), layers.Dropout(0.3),
    layers.Dense(1),
])
model.compile(optimizer=keras.optimizers.Adam(learning_rate=1e-3), loss="mse")
print("\n============ NETWORK ARCHITECTURE ============")
model.summary()

# train 80 epochs, in 4 stages of 20 so we can watch the score
print("\nTraining the MLP...")
for stage in range(4):
    model.fit(Xtr, ytr, epochs=20, batch_size=64, verbose=0)
    p = model.predict(Xte, verbose=0).flatten()
    print(f"  epoch {(stage + 1) * 20:3d}  test CCC = {ccc(yte, p):.3f}")


# compare both models on the same test set 
mlp_pred = model.predict(Xte, verbose=0).flatten()
print("\n============ ENGAGEMENT prediction ============")
print(f"{'model':16s} {'CCC':>7} {'Pearson':>8} {'MAE':>7}")
for name, pred in [("XGBoost", xgb_pred), ("MLP (Deep)", mlp_pred)]:
    print(f"{name:16s} {ccc(yte, pred):7.3f} {np.corrcoef(yte, pred)[0, 1]:8.3f} "
          f"{mean_absolute_error(yte, pred):7.3f}")

# save for reuse in a demo
model.save(os.path.join("reports", "noxi_mlp.keras"))
print("\nSaved model -> reports/noxi_mlp.keras")
