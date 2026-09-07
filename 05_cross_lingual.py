"""
STEP 5: The main experiment (cross-lingual transfer).
Train a model on one language and test it on another, for every pair,
to see if engagement transfers across languages. Fills a 3x3 CCC matrix.
Input: data/features/noxi_engagement.parquet
Output: reports/noxi_crosslingual_ccc.csv
"""

# ---------------------------------------------------------------------------
# BLOCK 1 - IMPORTS
# itertools.product gives us every (train language, test language) pair.
# Random Forest is used because it was our strongest baseline, so it gives the
# fairest picture of how well engagement transfers.
# ---------------------------------------------------------------------------
import os
import itertools
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

FEATURES = os.path.join("data", "features", "noxi_engagement.parquet")


# ---------------------------------------------------------------------------
# BLOCK 2 - THE SCORING FUNCTION
# CCC measures how closely predicted engagement matches the true engagement.
# 1.0 is perfect; higher is better.
# ---------------------------------------------------------------------------
def ccc(yt, yp):
    yt, yp = np.asarray(yt), np.asarray(yp)
    cov = ((yt - yt.mean()) * (yp - yp.mean())).mean()
    return (2 * cov) / (yt.var() + yp.var() + (yt.mean() - yp.mean()) ** 2 + 1e-9)


# ---------------------------------------------------------------------------
# BLOCK 3 - TRAIN ON ONE SET, TEST ON ANOTHER
# The core helper of this experiment. It scales the features, trains a Random
# Forest on the 'tr' rows, predicts on the 'te' rows, and returns the CCC.
# By passing different data into 'tr' and 'te' we can measure any kind of
# transfer we like.
# ---------------------------------------------------------------------------
def fit_score(tr, te, cols):
    m = make_pipeline(StandardScaler(),
                      RandomForestRegressor(n_estimators=120, n_jobs=-1, random_state=42))
    m.fit(tr[cols].fillna(0), tr["engagement"])
    return ccc(te["engagement"], m.predict(te[cols].fillna(0)))


def main():
    # -----------------------------------------------------------------------
    # BLOCK 4 - LOAD THE DATA
    # Read the table, pick the 802 feature columns, and get the list of
    # languages present (English, French, German).
    # -----------------------------------------------------------------------
    df = pd.read_parquet(FEATURES)
    cols = [c for c in df.columns if c.startswith(("voice_", "face_"))]
    langs = sorted(df["language"].unique())
    print(f"{len(df)} windows, {len(cols)} features, languages: {langs}\n")

    # -----------------------------------------------------------------------
    # BLOCK 5 - THE MAIN LOOP: EVERY LANGUAGE PAIR
    # itertools.product gives all 9 combinations of (train language a,
    # test language b). Each result goes into one cell of the 3x3 matrix.
    # -----------------------------------------------------------------------
    mat = pd.DataFrame(index=langs, columns=langs, dtype=float)
    for a, b in itertools.product(langs, langs):

        if a == b:
            # ---------------------------------------------------------------
            # BLOCK 5a - SAME LANGUAGE (the diagonal)
            # Here we must be careful. If windows from the SAME conversation
            # appeared in both training and testing, the model would recognise
            # that conversation and score far too high. So we leave one whole
            # session out for testing, train on the rest, and average over all
            # sessions. This makes the diagonal an honest upper bound.
            # ---------------------------------------------------------------
            scores = []
            for s in df.loc[df.language == a, "session"].unique():
                tr = df[(df.language == a) & (df.session != s)]
                te = df[(df.language == a) & (df.session == s)]
                scores.append(fit_score(tr, te, cols))
            mat.loc[a, b] = np.mean(scores)

        else:
            # ---------------------------------------------------------------
            # BLOCK 5b - DIFFERENT LANGUAGE (the off-diagonal)
            # This is the actual cross-lingual measurement: train on ALL of
            # language A, then test on ALL of language B. The model has never
            # seen a speaker of language B during training.
            # ---------------------------------------------------------------
            mat.loc[a, b] = fit_score(df[df.language == a], df[df.language == b], cols)

        print(f"  {a:8s} -> {b:8s}  CCC = {mat.loc[a, b]:.3f}")

    # -----------------------------------------------------------------------
    # BLOCK 6 - SHOW AND SAVE THE MATRIX
    # Rows are the training language, columns are the testing language.
    # -----------------------------------------------------------------------
    print("\nCross-lingual engagement CCC (train=row, test=col):\n")
    print(mat.round(3).to_string())
    mat.to_csv(os.path.join("reports", "noxi_crosslingual_ccc.csv"))

    # -----------------------------------------------------------------------
    # BLOCK 7 - THE FINDING
    # Average the diagonal (same language) and the off-diagonal (different
    # language). The GAP between these two numbers is the result of this
    # project: if the diagonal is much higher, engagement is language-specific
    # and a model does not fully transfer to a new language.
    # -----------------------------------------------------------------------
    diag = np.mean([mat.loc[l, l] for l in langs])
    off = np.mean([mat.loc[a, b] for a in langs for b in langs if a != b])
    print(f"\nAvg within-language CCC: {diag:.3f}   avg cross-language CCC: {off:.3f}")


if __name__ == "__main__":
    main()
