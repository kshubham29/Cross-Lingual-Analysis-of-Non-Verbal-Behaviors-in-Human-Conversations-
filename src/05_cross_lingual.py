
import os
import itertools
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

FEATURES = os.path.join("data", "features", "noxi_engagement.parquet")


# metric: 1.0 = perfect
def ccc(yt, yp):
    yt, yp = np.asarray(yt), np.asarray(yp)
    cov = ((yt - yt.mean()) * (yp - yp.mean())).mean()
    return (2 * cov) / (yt.var() + yp.var() + (yt.mean() - yp.mean()) ** 2 + 1e-9)


# train on 'tr', test on 'te', return CCC
def fit_score(tr, te, cols):
    m = make_pipeline(StandardScaler(),
                      RandomForestRegressor(n_estimators=120, n_jobs=-1, random_state=42))
    m.fit(tr[cols].fillna(0), tr["engagement"])
    return ccc(te["engagement"], m.predict(te[cols].fillna(0)))


def main():
    # load data
    df = pd.read_parquet(FEATURES)
    # drop the 5 OpenFace bookkeeping columns (frame, face_id, timestamp, confidence, success)
    meta = [f"face_{i}" for i in range(5)]
    cols = [c for c in df.columns if c.startswith(("voice_", "face_")) and c not in meta]
    langs = sorted(df["language"].unique())
    print(f"{len(df)} windows, {len(cols)} features, languages: {langs}\n")

    # every (train language, test language) pair
    mat = pd.DataFrame(index=langs, columns=langs, dtype=float)
    for a, b in itertools.product(langs, langs):

        if a == b:
            # same language: leave-one-session-out, then average
            scores = []
            for s in df.loc[df.language == a, "session"].unique():
                tr = df[(df.language == a) & (df.session != s)]
                te = df[(df.language == a) & (df.session == s)]
                scores.append(fit_score(tr, te, cols))
            mat.loc[a, b] = np.mean(scores)
        else:
            # different language: train on all of A, test on all of B
            mat.loc[a, b] = fit_score(df[df.language == a], df[df.language == b], cols)

        print(f"  {a:8s} -> {b:8s}  CCC = {mat.loc[a, b]:.3f}")

    # show and save the matrix (row = train, col = test)
    print("\nCross-lingual engagement CCC (train=row, test=col):\n")
    print(mat.round(3).to_string())
    mat.to_csv(os.path.join("reports", "noxi_crosslingual_ccc.csv"))

    # the finding: within-language vs cross-language
    diag = np.mean([mat.loc[l, l] for l in langs])
    off = np.mean([mat.loc[a, b] for a in langs for b in langs if a != b])
    print(f"\nAvg within-language CCC: {diag:.3f}   avg cross-language CCC: {off:.3f}")


if __name__ == "__main__":
    main()
