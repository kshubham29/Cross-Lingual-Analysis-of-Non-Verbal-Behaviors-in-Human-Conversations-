"""
STEP 18: Master results table.
Collects the session-wise scores of every model (steps 14, 15, 16) into ONE
table, next to the old random-split score, so every document can be updated
from the same numbers. Also draws one bar chart for the poster / slides.
Input:  reports/session_flat.csv, reports/session_sequence.csv, reports/autoencoder_results.csv
Output: reports/master_results.csv + reports/figures/master_ccc.png
"""

import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

R = "reports"
FIG = os.path.join(R, "figures")
os.makedirs(FIG, exist_ok=True)

# random-split scores from steps 4, 7, 11, 13, 12 (same conversations in train and test)
OLD = {"LinearRegression": 0.284, "RandomForest": 0.885, "GradientBoosting": 0.901,
       "XGBoost": 0.906, "ANN (MLP)": 0.881, "CNN_VGG": 0.860, "LSTM": 0.849,
       "Transformer": 0.826}
FAMILY = {"LinearRegression": "classic ML", "RandomForest": "classic ML",
          "GradientBoosting": "classic ML", "XGBoost": "classic ML", "ANN (MLP)": "ANN",
          "CNN_VGG": "CNN", "SimpleRNN": "RNN", "LSTM": "RNN", "GRU": "RNN",
          "Transformer": "Transformer", "Autoencoder + dense head": "Autoencoder",
          "Autoencoder + XGBoost": "Autoencoder"}

# stack the per-fold results of every model, then average over the 3 folds
parts = [pd.read_csv(os.path.join(R, f)) for f in
         ("session_flat.csv", "session_sequence.csv", "autoencoder_results.csv")
         if os.path.exists(os.path.join(R, f))]
folds = pd.concat(parts)[["model", "fold", "ccc", "pearson", "mae"]]
res = folds.groupby("model").agg(session_ccc=("ccc", "mean"), session_std=("ccc", "std"),
                                 pearson=("pearson", "mean"), mae=("mae", "mean")).reset_index()
res["family"] = res["model"].map(FAMILY)
res["random_split_ccc"] = res["model"].map(OLD)
res = res.sort_values("session_ccc", ascending=False).reset_index(drop=True)
res.round(3).to_csv(os.path.join(R, "master_results.csv"), index=False)

print("=========== MASTER RESULTS (whole conversations held out, 3 folds) ===========")
print(f"{'model':26s} {'family':12s} {'session CCC':>16} {'Pearson':>8} {'MAE':>6} {'random split':>13}")
for _, r in res.iterrows():
    old = "" if pd.isna(r["random_split_ccc"]) else f"{r['random_split_ccc']:.3f}"
    print(f"{r['model']:26s} {r['family']:12s} {r['session_ccc']:9.3f} +- {r['session_std']:.3f} "
          f"{r['pearson']:8.3f} {r['mae']:6.3f} {old:>13}")

# one bar per model, with the spread over the 3 folds
plot = res[res["model"] != "LinearRegression"].iloc[::-1]
plt.figure(figsize=(8, 5))
plt.barh(plot["model"], plot["session_ccc"], xerr=plot["session_std"], color="#5b7f4a", capsize=3)
plt.xlabel("CCC (mean over 3 session-wise folds)")
plt.title("Engagement prediction - unseen conversations")
plt.tight_layout()
plt.savefig(os.path.join(FIG, "master_ccc.png"), dpi=150)
print("\nSaved -> reports/master_results.csv, reports/figures/master_ccc.png")
