"""
Step 2: EDA report.

- ydata-profiling  -> one full HTML report (distributions, correlations, missing, balance)
- a few 'by language' boxplots -> the cross-lingual story
Outputs to reports/.
"""

import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from ydata_profiling import ProfileReport

FEATURES = os.path.join("data", "features", "features.parquet")
FIG_DIR = os.path.join("reports", "figures")
os.makedirs(FIG_DIR, exist_ok=True)


def main():
    df = pd.read_parquet(FEATURES)

    # 1. automatic full report
    ProfileReport(df, title="Cross-Lingual Non-Verbal EDA", minimal=True) \
        .to_file(os.path.join("reports", "eda_report.html"))
    print("Wrote reports/eda_report.html")

    # 2. class balance per language
    print("\nLabel counts per language:")
    print(pd.crosstab(df["language"], df["label"]))

    # 3. cross-lingual boxplots for a few interpretable non-verbal features
    candidates = [c for c in df.columns
                  if c in ("face_au_AU12", "face_emo_happiness",
                           "F0semitoneFrom27.5Hz_sma3nz_amean",
                           "loudness_sma3_amean")]
    for col in candidates:
        plt.figure(figsize=(7, 4))
        sns.boxplot(data=df, x="language", y=col)
        plt.title(f"{col} by language")
        plt.tight_layout()
        fp = os.path.join(FIG_DIR, f"{col.replace('.', '_')}_by_lang.png")
        plt.savefig(fp)
        plt.close()
        print("Wrote", fp)


if __name__ == "__main__":
    main()
