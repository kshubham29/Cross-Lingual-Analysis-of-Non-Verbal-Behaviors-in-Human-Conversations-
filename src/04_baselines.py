import os
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from xgboost import XGBRegressor

FEATURES = os.path.join("data", "features", "noxi_engagement.parquet")

def ccc(y_true, y_pred):
    yt, yp = np.asarray(y_true), np.asarray(y_pred)
    cov = ((yt - yt.mean()) * (yp - yp.mean())).mean()
    return (2 * cov) / (yt.var() + yp.var() + (yt.mean() - yp.mean()) ** 2 + 1e-9)


def main():
    # load the data
    df = pd.read_parquet(FEATURES)
    feat_cols = [c for c in df.columns if c.startswith(("voice_", "face_"))]
    X = df[feat_cols].fillna(0).to_numpy("float32")
    y = df["engagement"].to_numpy("float32")

    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42)

    models = {
        "LinearRegression": LinearRegression(),
        "RandomForest": RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1),
        "GradientBoosting": HistGradientBoostingRegressor(max_iter=300, random_state=42),
        "XGBoost": XGBRegressor(
            n_estimators=300, max_depth=6, learning_rate=0.1,
            subsample=0.8, colsample_bytree=0.8,
            tree_method="hist", random_state=42, n_jobs=-1,
        ),
    }

    print(f"{len(df)} windows, {len(feat_cols)} features\n")
    print(f"{'model':18s} {'CCC':>7} {'Pearson':>8} {'MAE':>7} {'R2':>7}", flush=True)

    # train each model, then score it on the unseen test data
    for name, m in models.items():
        pipe = make_pipeline(StandardScaler(), m)
        pipe.fit(Xtr, ytr)

        pred = pipe.predict(Xte)
        r = np.corrcoef(yte, pred)[0, 1]
        print(f"{name:18s} {ccc(yte, pred):7.3f} {r:8.3f} "
              f"{mean_absolute_error(yte, pred):7.3f} {r2_score(yte, pred):7.3f}", flush=True)


if __name__ == "__main__":
    main()
