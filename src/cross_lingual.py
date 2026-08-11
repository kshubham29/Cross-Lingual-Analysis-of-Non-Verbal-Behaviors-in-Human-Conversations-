"""
Step 4: the highlight — cross-lingual transfer.

Train a model on ONE language, test on ANOTHER, to see whether non-verbal
behavior models transfer across languages/cultures. Also runs the full
leave-one-language-out matrix.
"""

import os
import itertools
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import f1_score

FEATURES = os.path.join("data", "features", "features.parquet")


def numeric_X(df):
    return df.select_dtypes("number").fillna(0)


def train_test(df, lang_a, lang_b):
    tr, te = df[df.language == lang_a], df[df.language == lang_b]
    if len(tr) == 0 or len(te) == 0:
        return None
    Xtr, ytr = numeric_X(tr), tr["label"]
    Xte, yte = numeric_X(te)[Xtr.columns], te["label"]
    clf = make_pipeline(StandardScaler(), RandomForestClassifier(random_state=42))
    clf.fit(Xtr, ytr)
    return f1_score(yte, clf.predict(Xte), average="macro")


def main():
    df = pd.read_parquet(FEATURES)
    langs = sorted(df["language"].unique())
    if len(langs) < 2:
        print(f"Only one language ({langs}). Add a second language for cross-lingual.")
        return

    print(f"Languages: {langs}\nMacro-F1 for train(row) -> test(col):\n")
    matrix = pd.DataFrame(index=langs, columns=langs, dtype=float)
    for a, b in itertools.product(langs, langs):
        matrix.loc[a, b] = train_test(df, a, b)

    print(matrix.round(3).to_string())
    matrix.to_csv(os.path.join("reports", "cross_lingual_matrix.csv"))
    print("\nSaved reports/cross_lingual_matrix.csv")
    print("Diagonal = same-language (upper bound); off-diagonal = cross-lingual transfer.")


if __name__ == "__main__":
    main()
