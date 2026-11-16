"""
Quick look at the feature table (for demonstration).
Input: data/features/noxi_engagement.parquet
"""

import os
import pandas as pd

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 12)

df = pd.read_parquet(os.path.join("data", "features", "noxi_engagement.parquet"))
voice = [c for c in df.columns if c.startswith("voice_")]
face = [c for c in df.columns if c.startswith("face_")]

# size
print(f"\nShape: {df.shape[0]} rows x {df.shape[1]} columns")
print(f"  voice features : {len(voice)}")
print(f"  face features  : {len(face)}")
print(f"  total features : {len(voice) + len(face)}")

# what the columns are called
print("\nFirst 5 voice features:", voice[:5])
print("First 5 face features :", face[:5])
print("Label columns         :", [c for c in df.columns if not c.startswith(("voice_", "face_"))])

# the actual numbers
print("\nFirst 5 rows (a few columns):")
print(df[voice[:3] + face[:3] + ["engagement", "language", "role"]].head().round(3).to_string())

# data quality
print(f"\nMissing values: {df[voice + face].isna().sum().sum()}")
print("\nWindows per language:")
print(df["language"].value_counts().to_string())
print("\nEngagement range: %.3f to %.3f (mean %.3f)"
      % (df["engagement"].min(), df["engagement"].max(), df["engagement"].mean()))
