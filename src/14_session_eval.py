
# silence TensorFlow (must be set before it is imported)
import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
import logging
logging.getLogger("tensorflow").setLevel(logging.ERROR)

import joblib
import numpy as np
import pandas as pd
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.base import clone
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error
from xgboost import XGBRegressor

FEAT = os.path.join("data", "features", "noxi_engagement.parquet")
META = [f"face_{i}" for i in range(5)]      # frame, face_id, timestamp, confidence, success
CLIP = 5            # neural nets: scaled values limited to [-5, 5]
os.makedirs("reports", exist_ok=True)


# metric: 1.0 = perfect
def ccc(yt, yp):
    yt, yp = np.asarray(yt), np.asarray(yp)
    cov = ((yt - yt.mean()) * (yp - yp.mean())).mean()
    return (2 * cov) / (yt.var() + yp.var() + (yt.mean() - yp.mean()) ** 2 + 1e-9)


# load data, drop the bookkeeping columns
df = pd.read_parquet(FEAT)
cols = [c for c in df.columns if c.startswith(("voice_", "face_")) and c not in META]
X = df[cols].fillna(0).to_numpy("float32")
y = df["engagement"].to_numpy("float32")

# 3 folds: fold k tests on the k-th session of every language
sess = df.groupby("language")["session"].unique().apply(sorted)
folds = [[s[k] for s in sess] for k in range(3)]
print(f"{len(df)} windows, {len(cols)} features, folds: {folds}\n", flush=True)


models = {
    "LinearRegression": LinearRegression(),
    "RandomForest": RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1),
    "GradientBoosting": HistGradientBoostingRegressor(max_iter=300, random_state=42),
    "XGBoost": XGBRegressor(n_estimators=300, max_depth=6, learning_rate=0.1,
                            subsample=0.8, colsample_bytree=0.8,
                            tree_method="hist", random_state=42, n_jobs=-1),
}


# the tuned ANN from step 7 (256-128, dropout 0.1, Adam 1e-3)
def mlp():
    keras.utils.set_random_seed(42)
    m = keras.Sequential([
        layers.Input(shape=(len(cols),)),
        layers.Dense(256, activation="relu"), layers.Dropout(0.1),
        layers.Dense(128, activation="relu"), layers.Dropout(0.1),
        layers.Dense(1),
    ])
    m.compile(optimizer=keras.optimizers.Adam(1e-3), loss="mse")
    return m


rows = []
def report(name, fold, pred, yte):
    rows.append(dict(model=name, fold=fold, ccc=ccc(yte, pred),
                     pearson=np.corrcoef(yte, pred)[0, 1], mae=mean_absolute_error(yte, pred)))
    print(f"  {name:18s} CCC = {rows[-1]['ccc']:.3f}", flush=True)


for k, test_sess in enumerate(folds, 1):
    te = df["session"].isin(test_sess).to_numpy()
    tr = ~te
    print(f"fold {k}: test sessions {test_sess} | train {tr.sum()} | test {te.sum()}", flush=True)

    # classic models: scaler + model in one pipeline, fitted on the training sessions only
    for name, m in models.items():
        pipe = make_pipeline(StandardScaler(), clone(m)).fit(X[tr], y[tr])
        report(name, k, pipe.predict(X[te]), y[te])
        if name == "XGBoost":
            joblib.dump(dict(pipe=pipe, cols=cols, test_sessions=test_sess),
                        os.path.join("reports", f"xgb_fold{k}.joblib"))

    # ANN - scaled values are clipped to [-5, 5]: a few extreme values in unseen
    # sessions (up to 100,000 std) do not bother trees but wreck a neural network
    sc = StandardScaler().fit(X[tr])
    m = mlp()
    m.fit(np.clip(sc.transform(X[tr]), -CLIP, CLIP), y[tr], epochs=30, batch_size=128, verbose=0)
    report("ANN (MLP)", k, m.predict(np.clip(sc.transform(X[te]), -CLIP, CLIP), verbose=0).flatten(), y[te])
    print()


res = pd.DataFrame(rows)
res.to_csv(os.path.join("reports", "session_flat.csv"), index=False)
summary = res.groupby("model")[["ccc", "pearson", "mae"]].agg(["mean", "std"])
summary = summary.sort_values(("ccc", "mean"), ascending=False)
print("=========== FLAT MODELS, SESSION-WISE (mean +- std over 3 folds) ===========")
print(f"{'model':18s} {'CCC':>14} {'Pearson':>8} {'MAE':>7}")
for name, r in summary.iterrows():
    print(f"{name:18s} {r[('ccc', 'mean')]:7.3f} +- {r[('ccc', 'std')]:.3f} "
          f"{r[('pearson', 'mean')]:8.3f} {r[('mae', 'mean')]:7.3f}")
print("\nSaved -> reports/session_flat.csv, reports/xgb_fold{1,2,3}.joblib")
