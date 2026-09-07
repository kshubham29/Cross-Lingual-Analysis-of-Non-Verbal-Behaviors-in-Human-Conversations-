"""
STEP 4: Baseline models.
Train simple models (Linear Regression, Random Forest, SVR) to predict
engagement. This is our reference score to beat later.
Metric: CCC (closer to 1.0 = better).
Input: data/features/noxi_engagement.parquet
"""

# ---------------------------------------------------------------------------
# BLOCK 1 - IMPORTS
# scikit-learn provides the three models, the train/test split, the scaler and
# the evaluation metrics.
# ---------------------------------------------------------------------------
import os
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR
from sklearn.metrics import mean_absolute_error, r2_score

FEATURES = os.path.join("data", "features", "noxi_engagement.parquet")


# ---------------------------------------------------------------------------
# BLOCK 2 - THE SCORING FUNCTION
# CCC (Concordance Correlation Coefficient) measures how closely the predicted
# engagement matches the true engagement, in both trend and actual value.
# 1.0 is perfect. We use CCC rather than accuracy because engagement is a
# continuous number - this is regression, not classification.
# ---------------------------------------------------------------------------
def ccc(y_true, y_pred):
    yt, yp = np.asarray(y_true), np.asarray(y_pred)
    cov = ((yt - yt.mean()) * (yp - yp.mean())).mean()
    return (2 * cov) / (yt.var() + yp.var() + (yt.mean() - yp.mean()) ** 2 + 1e-9)


def main():
    # -----------------------------------------------------------------------
    # BLOCK 3 - LOAD THE DATA
    # X = the 802 inputs (voice + face features).
    # y = the answer we predict (engagement, 0 to 1).
    # -----------------------------------------------------------------------
    df = pd.read_parquet(FEATURES)
    feat_cols = [c for c in df.columns if c.startswith(("voice_", "face_"))]
    X = df[feat_cols].fillna(0).to_numpy("float32")
    y = df["engagement"].to_numpy("float32")

    # -----------------------------------------------------------------------
    # BLOCK 4 - SPLIT THE DATA
    # 80% is used to train the models and 20% is held back for testing. Testing
    # on unseen rows is the only honest way to measure performance.
    # random_state=42 makes the split the same every run, so results are
    # reproducible.
    # -----------------------------------------------------------------------
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42)

    # -----------------------------------------------------------------------
    # BLOCK 5 - THE THREE BASELINE MODELS
    # These are deliberately from three different families:
    #   Linear Regression - linear, the simplest possible approach
    #   Random Forest     - an ensemble of decision trees
    #   SVR               - a kernel-based method
    # Comparing different families shows which kind of approach suits our data,
    # and gives a reference score the neural network must beat.
    # -----------------------------------------------------------------------
    models = {
        "LinearRegression": LinearRegression(),
        "RandomForest": RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1),
        "SVR": SVR(),
    }

    print(f"{len(df)} windows, {len(feat_cols)} features\n")
    print(f"{'model':18s} {'CCC':>7} {'Pearson':>8} {'MAE':>7} {'R2':>7}", flush=True)

    # -----------------------------------------------------------------------
    # BLOCK 6 - TRAIN AND SCORE EACH MODEL
    # Each model runs inside a pipeline that first standardises the features.
    # Scaling matters because the features are on very different scales (pitch
    # is in the hundreds, probabilities are between 0 and 1); without it,
    # distance-based models like SVR are dominated by the largest values.
    # -----------------------------------------------------------------------
    for name, m in models.items():
        pipe = make_pipeline(StandardScaler(), m)

        # SVR scales very badly with data size - on all 17,000 rows it takes
        # many minutes. Training it on a random 4,000-row sample keeps it fast
        # with almost no loss in score.
        if name == "SVR" and len(Xtr) > 4000:
            idx = np.random.RandomState(42).choice(len(Xtr), 4000, replace=False)
            pipe.fit(Xtr[idx], ytr[idx])
        else:
            pipe.fit(Xtr, ytr)

        # Predict on the unseen test data, then report four measures.
        # R2 below zero means the model is worse than simply predicting the
        # average every time - which is what happens to Linear Regression here.
        pred = pipe.predict(Xte)
        r = np.corrcoef(yte, pred)[0, 1]
        print(f"{name:18s} {ccc(yte, pred):7.3f} {r:8.3f} "
              f"{mean_absolute_error(yte, pred):7.3f} {r2_score(yte, pred):7.3f}", flush=True)


if __name__ == "__main__":
    main()
