"""
STEP 3: EDA (Exploratory Data Analysis) - look at the data before modeling.
Makes charts + checks so we understand the data before training any model.
Input: data/features/noxi_engagement.parquet
Output: reports/figures/*.png  and  reports/eda_summary.csv
"""

# ---------------------------------------------------------------------------
# BLOCK 1 - IMPORTS
# matplotlib/seaborn draw the charts, scipy runs the statistical test, and
# scikit-learn provides PCA for the 2-D visualisation.
# ---------------------------------------------------------------------------
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from scipy import stats

FEATURES = os.path.join("data", "features", "noxi_engagement.parquet")
FIG = os.path.join("reports", "figures")
os.makedirs(FIG, exist_ok=True)

# ---------------------------------------------------------------------------
# BLOCK 2 - LOAD THE DATA
# Read the table built in step 2 and pick out the 802 feature columns
# (ignoring engagement, language, session and role, which are not inputs).
# ---------------------------------------------------------------------------
df = pd.read_parquet(FEATURES)
feat_cols = [c for c in df.columns if c.startswith(("voice_", "face_"))]

# ---------------------------------------------------------------------------
# BLOCK 3 - BASIC INFORMATION
# How much data do we have, which languages, and is it balanced between them?
# An unbalanced dataset would bias the models toward one language.
# ---------------------------------------------------------------------------
print("Total windows:", len(df))
print("Languages:", df["language"].unique().tolist())
print("\nWindows per language:")
print(df["language"].value_counts())

# ---------------------------------------------------------------------------
# BLOCK 4 - DATA QUALITY CHECK
# Count missing values. We want zero before training anything.
# ---------------------------------------------------------------------------
missing = df[feat_cols].isna().sum().sum()
print(f"\nMissing feature values: {missing}")

# ---------------------------------------------------------------------------
# BLOCK 5 - ENGAGEMENT SUMMARY PER LANGUAGE
# Average, spread, minimum and maximum engagement for each language, saved to a
# CSV for the report. If the averages are similar, the languages are comparable.
# ---------------------------------------------------------------------------
summary = df.groupby("language")["engagement"].agg(["count", "mean", "std", "min", "max"])
summary.to_csv(os.path.join("reports", "eda_summary.csv"))
print("\nEngagement summary per language:\n", summary)

# ---------------------------------------------------------------------------
# BLOCK 6 - STATISTICAL TEST (ANOVA)
# Are the differences between languages real, or just random variation?
# A p-value below 0.05 means the difference is statistically significant.
# ---------------------------------------------------------------------------
groups = [g["engagement"].values for _, g in df.groupby("language")]
f_stat, p_val = stats.f_oneway(*groups)
print(f"\nANOVA (engagement across languages): F={f_stat:.2f}, p={p_val:.4g}")
print("p < 0.05 means the languages differ significantly in engagement level.")

# ---------------------------------------------------------------------------
# BLOCK 7 - CHART 1: ENGAGEMENT DISTRIBUTION
# Shows how engagement values are spread. We expect most values in the middle,
# because people in a conversation are rarely fully bored or fully absorbed.
# ---------------------------------------------------------------------------
plt.figure(figsize=(7, 4))
sns.histplot(df["engagement"], bins=30, kde=True)
plt.title("Engagement distribution (all data)")
plt.xlabel("engagement")
plt.tight_layout(); plt.savefig(os.path.join(FIG, "engagement_distribution.png")); plt.close()

# ---------------------------------------------------------------------------
# BLOCK 8 - CHART 2: ENGAGEMENT BY LANGUAGE
# Compares the three languages side by side. This shows whether people are
# engaged to a similar degree regardless of language.
# ---------------------------------------------------------------------------
plt.figure(figsize=(7, 4))
sns.boxplot(data=df, x="language", y="engagement")
plt.title("Engagement by language")
plt.tight_layout(); plt.savefig(os.path.join(FIG, "engagement_by_language.png")); plt.close()

# ---------------------------------------------------------------------------
# BLOCK 9 - CHART 3: DATA BALANCE
# How many windows each language contributes. Confirms no language dominates.
# ---------------------------------------------------------------------------
plt.figure(figsize=(7, 4))
df["language"].value_counts().plot(kind="bar")
plt.title("Number of windows per language"); plt.ylabel("windows")
plt.tight_layout(); plt.savefig(os.path.join(FIG, "windows_per_language.png")); plt.close()

# ---------------------------------------------------------------------------
# BLOCK 10 - CHART 4: WHICH FEATURES MATTER
# Correlate every feature with engagement and plot the ten strongest. This
# hints at which behaviours carry the engagement signal.
# ---------------------------------------------------------------------------
corr = df[feat_cols].corrwith(df["engagement"]).abs().sort_values(ascending=False)
plt.figure(figsize=(7, 4))
corr.head(10).plot(kind="barh")
plt.title("Top 10 features correlated with engagement")
plt.tight_layout(); plt.savefig(os.path.join(FIG, "top_features.png")); plt.close()

# ---------------------------------------------------------------------------
# BLOCK 11 - CHART 5: EXPERT vs NOVICE
# Each conversation has one expert and one novice. Do they differ in engagement?
# ---------------------------------------------------------------------------
plt.figure(figsize=(7, 4))
sns.boxplot(data=df, x="role", y="engagement")
plt.title("Engagement by role (expert vs novice)")
plt.tight_layout(); plt.savefig(os.path.join(FIG, "engagement_by_role.png")); plt.close()
print("\nEngagement by role:\n", df.groupby("role")["engagement"].mean())

# ---------------------------------------------------------------------------
# BLOCK 12 - CHART 6: VOICE vs FACE
# Which modality carries more engagement information? We compare the average
# absolute correlation of the voice features against the face features.
# ---------------------------------------------------------------------------
voice_corr = df[[c for c in feat_cols if c.startswith("voice_")]].corrwith(df["engagement"]).abs().mean()
face_corr = df[[c for c in feat_cols if c.startswith("face_")]].corrwith(df["engagement"]).abs().mean()
plt.figure(figsize=(5, 4))
plt.bar(["Voice", "Face"], [voice_corr, face_corr], color=["#028090", "#02C39A"])
plt.title("Avg |correlation| with engagement: Voice vs Face")
plt.ylabel("mean |correlation|")
plt.tight_layout(); plt.savefig(os.path.join(FIG, "voice_vs_face.png")); plt.close()
print(f"\nVoice avg |corr| = {voice_corr:.3f}   Face avg |corr| = {face_corr:.3f}")

# ---------------------------------------------------------------------------
# BLOCK 13 - CHART 7: CORRELATION HEATMAP
# Shows how the top features relate to each other and to engagement. Strongly
# correlated features carry overlapping information.
# ---------------------------------------------------------------------------
top10 = corr.head(10).index.tolist()
plt.figure(figsize=(8, 6))
sns.heatmap(df[top10 + ["engagement"]].corr(), annot=False, cmap="coolwarm", center=0)
plt.title("Correlation heatmap (top 10 features + engagement)")
plt.tight_layout(); plt.savefig(os.path.join(FIG, "correlation_heatmap.png")); plt.close()

# ---------------------------------------------------------------------------
# BLOCK 14 - CHART 8: PCA BY LANGUAGE
# PCA compresses all 802 features into 2 dimensions so they can be plotted.
# If the languages form separate clusters, their behaviour patterns differ -
# an early hint of the cross-lingual result we test in step 5.
# ---------------------------------------------------------------------------
X = StandardScaler().fit_transform(df[feat_cols].fillna(0))
pcs = PCA(n_components=2).fit_transform(X)
plt.figure(figsize=(7, 5))
sns.scatterplot(x=pcs[:, 0], y=pcs[:, 1], hue=df["language"], s=8, alpha=0.5)
plt.title("PCA of features, colored by language")
plt.tight_layout(); plt.savefig(os.path.join(FIG, "pca_by_language.png")); plt.close()

print("\nSaved 8 charts to reports/figures/ and summary to reports/eda_summary.csv")
