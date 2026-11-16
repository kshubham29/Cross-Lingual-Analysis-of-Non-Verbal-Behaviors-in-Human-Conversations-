"""
STEP 16: Autoencoder (TensorFlow / Keras).
An autoencoder learns to squeeze the 797 features into a small CODE (32 numbers)
and rebuild them from it - without using the engagement labels. If 32 numbers
are enough to predict engagement, the network has learned a compact summary of
the behaviour.
  1) train encoder + decoder to reconstruct the input (797 -> 256 -> 32 -> 256 -> 797)
  2) freeze the encoder, put a small dense head on the 32-number code, predict engagement
  3) for comparison, XGBoost on the same 32 numbers
Same 3 session-wise folds as step 14.
Input:  data/features/noxi_engagement.parquet
Output: reports/autoencoder_results.csv
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
from xgboost import XGBRegressor

FEAT = os.path.join("data", "features", "noxi_engagement.parquet")
META = [f"face_{i}" for i in range(5)]      # frame, face_id, timestamp, confidence, success
os.makedirs("reports", exist_ok=True)
CODE = 32           # size of the compressed code
EPOCHS = 30


# metric: 1.0 = perfect
def ccc(yt, yp):
    yt, yp = np.asarray(yt), np.asarray(yp)
    cov = ((yt - yt.mean()) * (yp - yp.mean())).mean()
    return (2 * cov) / (yt.var() + yp.var() + (yt.mean() - yp.mean()) ** 2 + 1e-9)


# load data, same columns and folds as step 14
df = pd.read_parquet(FEAT)
cols = [c for c in df.columns if c.startswith(("voice_", "face_")) and c not in META]
X = df[cols].fillna(0).to_numpy("float32")
y = df["engagement"].to_numpy("float32")
sess = df.groupby("language")["session"].unique().apply(sorted)
folds = [[s[k] for s in sess] for k in range(3)]
n_feat = len(cols)
print(f"{len(df)} windows, {n_feat} features -> code of {CODE}\n", flush=True)


# encoder squeezes, decoder rebuilds
def build_autoencoder():
    inp = layers.Input(shape=(n_feat,))
    h = layers.Dense(256, activation="relu")(inp)
    code = layers.Dense(CODE, activation="relu", name="code")(h)
    h = layers.Dense(256, activation="relu")(code)
    out = layers.Dense(n_feat)(h)
    return keras.Model(inp, out, name="Autoencoder"), keras.Model(inp, code, name="Encoder")


rows = []
for k, test_sess in enumerate(folds, 1):
    te = df["session"].isin(test_sess).to_numpy()
    tr = ~te
    # scale on the training sessions, clip extreme values to [-5, 5]
    sc = StandardScaler().fit(X[tr])
    X_tr, X_te = np.clip(sc.transform(X[tr]), -5, 5), np.clip(sc.transform(X[te]), -5, 5)
    print(f"fold {k}: test sessions {test_sess}", flush=True)

    # 1) unsupervised: input = target, no engagement labels used
    keras.utils.set_random_seed(42)
    ae, encoder = build_autoencoder()
    ae.compile(optimizer=keras.optimizers.Adam(1e-3), loss="mse")
    ae.fit(X_tr, X_tr, epochs=EPOCHS, batch_size=128, verbose=0)
    recon = ae.evaluate(X_te, X_te, verbose=0)
    print(f"  reconstruction MSE on test = {recon:.3f}", flush=True)

    # 2) frozen encoder + small head -> engagement
    encoder.trainable = False
    inp = layers.Input(shape=(n_feat,))
    x = layers.Dense(64, activation="relu")(encoder(inp))
    x = layers.Dropout(0.1)(x)
    reg = keras.Model(inp, layers.Dense(1)(x))
    reg.compile(optimizer=keras.optimizers.Adam(1e-3), loss="mse")
    reg.fit(X_tr, y[tr], epochs=EPOCHS, batch_size=128, verbose=0)
    pred = reg.predict(X_te, verbose=0).flatten()
    rows.append(dict(model="Autoencoder + dense head", fold=k, recon_mse=recon, ccc=ccc(y[te], pred),
                     pearson=np.corrcoef(y[te], pred)[0, 1], mae=mean_absolute_error(y[te], pred)))
    print(f"  AE + dense head  CCC = {rows[-1]['ccc']:.3f}", flush=True)

    # 3) XGBoost on the same 32-number codes
    c_tr, c_te = encoder.predict(X_tr, verbose=0), encoder.predict(X_te, verbose=0)
    xgb = XGBRegressor(n_estimators=300, max_depth=6, learning_rate=0.1, subsample=0.8,
                       colsample_bytree=0.8, tree_method="hist", random_state=42, n_jobs=-1)
    pred = xgb.fit(c_tr, y[tr]).predict(c_te)
    rows.append(dict(model="Autoencoder + XGBoost", fold=k, recon_mse=recon, ccc=ccc(y[te], pred),
                     pearson=np.corrcoef(y[te], pred)[0, 1], mae=mean_absolute_error(y[te], pred)))
    print(f"  AE + XGBoost     CCC = {rows[-1]['ccc']:.3f}\n", flush=True)


res = pd.DataFrame(rows)
res.to_csv(os.path.join("reports", "autoencoder_results.csv"), index=False)
print(f"=========== AUTOENCODER ({n_feat} -> {CODE}), SESSION-WISE ===========")
for name, g in res.groupby("model"):
    print(f"{name:26s} CCC {g.ccc.mean():.3f} +- {g.ccc.std():.3f} | "
          f"Pearson {g.pearson.mean():.3f} | MAE {g.mae.mean():.3f}")
print(f"reconstruction MSE (scaled units) {res.recon_mse.mean():.3f}")
print("\nSaved -> reports/autoencoder_results.csv")
