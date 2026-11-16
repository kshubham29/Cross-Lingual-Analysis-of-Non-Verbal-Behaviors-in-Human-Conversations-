
import os
import itertools
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from xgboost import XGBRegressor

FEAT = os.path.join("data", "features", "noxi_engagement.parquet")
META = [f"face_{i}" for i in range(5)]      # frame, face_id, timestamp, confidence, success
os.makedirs("reports", exist_ok=True)


# metric: 1.0 = perfect
def ccc(yt, yp):
    yt, yp = np.asarray(yt), np.asarray(yp)
    cov = ((yt - yt.mean()) * (yp - yp.mean())).mean()
    return (2 * cov) / (yt.var() + yp.var() + (yt.mean() - yp.mean()) ** 2 + 1e-9)


# train on 'tr', test on 'te', return CCC
def fit_score(tr, te, cols):
    m = make_pipeline(StandardScaler(),
                      XGBRegressor(n_estimators=300, max_depth=6, learning_rate=0.1,
                                   subsample=0.8, colsample_bytree=0.8,
                                   tree_method="hist", random_state=42, n_jobs=-1))
    m.fit(tr[cols].fillna(0), tr["engagement"])
    return ccc(te["engagement"], m.predict(te[cols].fillna(0)))


df = pd.read_parquet(FEAT)
voice = [c for c in df.columns if c.startswith("voice_")]
face = [c for c in df.columns if c.startswith("face_") and c not in META]
modalities = {"voice": voice, "face": face, "both": voice + face}
langs = sorted(df["language"].unique())
sess = df.groupby("language")["session"].unique().apply(sorted)
folds = [[s[k] for s in sess] for k in range(3)]
print(f"voice {len(voice)} | face {len(face)} | both {len(voice) + len(face)} features\n", flush=True)


rows = []
for name, cols in modalities.items():
    print(f"=== {name} ({len(cols)} features) ===", flush=True)

    # 1) all languages, 3 session-wise folds
    fold_scores = [fit_score(df[~df.session.isin(t)], df[df.session.isin(t)], cols) for t in folds]

    # 2) within-language: leave one session out inside each language
    within = []
    for l in langs:
        d = df[df.language == l]
        within += [fit_score(d[d.session != s], d[d.session == s], cols) for s in d.session.unique()]

    # 3) cross-language: train on all of A, test on all of B
    cross = [fit_score(df[df.language == a], df[df.language == b], cols)
             for a, b in itertools.permutations(langs, 2)]

    w, c = np.mean(within), np.mean(cross)
    rows.append(dict(modality=name, n_features=len(cols),
                     session_ccc=np.mean(fold_scores), session_std=np.std(fold_scores, ddof=1),
                     within_ccc=w, cross_ccc=c, drop_pct=100 * (w - c) / w))
    r = rows[-1]
    print(f"  session-wise CCC {r['session_ccc']:.3f} +- {r['session_std']:.3f} | "
          f"within {w:.3f} | cross {c:.3f} | drop {r['drop_pct']:.0f}%\n", flush=True)


res = pd.DataFrame(rows)
res.to_csv(os.path.join("reports", "ablation_results.csv"), index=False)
print("=========== ABLATION (XGBoost, whole conversations held out) ===========")
print(f"{'modality':8s} {'features':>8} {'session CCC':>16} {'within':>7} {'cross':>7} {'drop':>6}")
for _, r in res.iterrows():
    print(f"{r['modality']:8s} {r['n_features']:8d} {r['session_ccc']:9.3f} +- {r['session_std']:.3f} "
          f"{r['within_ccc']:7.3f} {r['cross_ccc']:7.3f} {r['drop_pct']:5.0f}%")
print("\nSaved -> reports/ablation_results.csv")
