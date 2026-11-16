"""
STEP 3: EDA (Exploratory Data Analysis) - look at the data before modeling.
Input: data/features/noxi_engagement.parquet
Output: reports/figures/*.png  and  reports/eda_summary.csv
"""

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

df = pd.read_parquet(FEATURES)
feat_cols = [c for c in df.columns if c.startswith(("voice_", "face_"))]

print("Total windows:", len(df))
print("Languages:", df["language"].unique().tolist())
print("\nWindows per language:")
print(df["language"].value_counts())

missing = df[feat_cols].isna().sum().sum()
print(f"\nMissing feature values: {missing}")

summary = df.groupby("language")["engagement"].agg(["count", "mean", "std", "min", "max"])
summary.to_csv(os.path.join("reports", "eda_summary.csv"))
print("\nEngagement summary per language:\n", summary)

groups = [g["engagement"].values for _, g in df.groupby("language")]
f_stat, p_val = stats.f_oneway(*groups)
print(f"\nANOVA (engagement across languages): F={f_stat:.2f}, p={p_val:.4g}")
print("p < 0.05 means the languages differ significantly in engagement level.")

plt.figure(figsize=(7, 4))
sns.histplot(df["engagement"], bins=30, kde=True)
plt.title("Engagement distribution (all data)")
plt.xlabel("engagement")
plt.tight_layout(); plt.savefig(os.path.join(FIG, "engagement_distribution.png")); plt.close()

plt.figure(figsize=(7, 4))
sns.boxplot(data=df, x="language", y="engagement")
plt.title("Engagement by language")
plt.tight_layout(); plt.savefig(os.path.join(FIG, "engagement_by_language.png")); plt.close()

plt.figure(figsize=(7, 4))
df["language"].value_counts().plot(kind="bar")
plt.title("Number of windows per language"); plt.ylabel("windows")
plt.tight_layout(); plt.savefig(os.path.join(FIG, "windows_per_language.png")); plt.close()

corr = df[feat_cols].corrwith(df["engagement"]).abs().sort_values(ascending=False)
plt.figure(figsize=(7, 4))
corr.head(10).plot(kind="barh")
plt.title("Top 10 features correlated with engagement")
plt.tight_layout(); plt.savefig(os.path.join(FIG, "top_features.png")); plt.close()

plt.figure(figsize=(7, 4))
sns.boxplot(data=df, x="role", y="engagement")
plt.title("Engagement by role (expert vs novice)")
plt.tight_layout(); plt.savefig(os.path.join(FIG, "engagement_by_role.png")); plt.close()
print("\nEngagement by role:\n", df.groupby("role")["engagement"].mean())

voice_corr = df[[c for c in feat_cols if c.startswith("voice_")]].corrwith(df["engagement"]).abs().mean()
face_corr = df[[c for c in feat_cols if c.startswith("face_")]].corrwith(df["engagement"]).abs().mean()
plt.figure(figsize=(5, 4))
plt.bar(["Voice", "Face"], [voice_corr, face_corr], color=["#028090", "#02C39A"])
plt.title("Avg |correlation| with engagement: Voice vs Face")
plt.ylabel("mean |correlation|")
plt.tight_layout(); plt.savefig(os.path.join(FIG, "voice_vs_face.png")); plt.close()
print(f"\nVoice avg |corr| = {voice_corr:.3f}   Face avg |corr| = {face_corr:.3f}")

top10 = corr.head(10).index.tolist()
plt.figure(figsize=(8, 6))
sns.heatmap(df[top10 + ["engagement"]].corr(), annot=False, cmap="coolwarm", center=0)
plt.title("Correlation heatmap (top 10 features + engagement)")
plt.tight_layout(); plt.savefig(os.path.join(FIG, "correlation_heatmap.png")); plt.close()

X = StandardScaler().fit_transform(df[feat_cols].fillna(0))
pcs = PCA(n_components=2).fit_transform(X)
plt.figure(figsize=(7, 5))
sns.scatterplot(x=pcs[:, 0], y=pcs[:, 1], hue=df["language"], s=8, alpha=0.5)
plt.title("PCA of features, colored by language")
plt.tight_layout(); plt.savefig(os.path.join(FIG, "pca_by_language.png")); plt.close()

print("\nSaved 8 charts to reports/figures/ and summary to reports/eda_summary.csv")
