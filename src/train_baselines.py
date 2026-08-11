"""
Step 3: baseline models (high-level via PyCaret).

compare_models() trains ~15 classifiers and ranks them by F1.
We report the top 2 as our two baselines, plus a confusion matrix.
"""

import os
import pandas as pd
from pycaret.classification import (
    setup, compare_models, pull, plot_model, save_model,
)

FEATURES = os.path.join("data", "features", "features.parquet")
os.makedirs("reports", exist_ok=True)


def main():
    df = pd.read_parquet(FEATURES)
    # drop identifier / grouping columns the model shouldn't see
    data = df.drop(columns=[c for c in ("language", "clip") if c in df.columns])

    setup(data=data, target="label", session_id=42, verbose=False)
    best2 = compare_models(n_select=2)          # your two baselines
    leaderboard = pull()
    leaderboard.to_csv(os.path.join("reports", "baseline_leaderboard.csv"))
    print("\nTop models:\n", leaderboard.head(5))

    # confusion matrix for the best one
    try:
        plot_model(best2[0], plot="confusion_matrix", save=True)
    except Exception as e:
        print("plot skipped:", e)

    save_model(best2[0], os.path.join("reports", "best_baseline"))
    print("Saved best baseline model + leaderboard to reports/")


if __name__ == "__main__":
    main()
