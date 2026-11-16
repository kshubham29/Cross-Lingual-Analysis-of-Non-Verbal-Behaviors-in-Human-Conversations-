"""
STEP 27: Unseen PEOPLE, not only unseen conversations.
NoXi metadata shows that two participants appear in two of our sessions
(person 12: sessions 001 and 021; person 44: sessions 028 and 030). With the
earlier folds the same person could be in training and in test.
Here every split keeps all sessions of a person together (src/splits.py):
  folds  : 3 person-disjoint folds (GroupKFold over person groups)
  within : leave one session out, ALSO removing sessions that share a person
  cross  : train language A, test language B (no person is in two languages, unchanged)
Each model is scored both ways, so the size of the leak is visible.
Models: Gradient Boosting (same settings as steps 14/23/24) on
  voice | face | voice + face | voice + face + context | eGeMAPS + w2v-BERT + VideoMAE + context (best)
Input:  data/features/noxi_engagement.parquet + pretrained_<name>.npy + data/noxi_metadata.xlsx
Output: reports/person_disjoint_results.csv
"""
import os
import itertools
import numpy as np
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import HistGradientBoostingRegressor
from splits import person_folds, same_person

FEAT = os.path.join("data", "features", "noxi_engagement.parquet")
META = [f"face_{i}" for i in range(5)]
CONTEXT = [5, 10]
OUT = os.path.join("reports", "person_disjoint_results.csv")


def ccc(yt, yp):
    yt, yp = np.asarray(yt), np.asarray(yp)
    cov = ((yt - yt.mean()) * (yp - yp.mean())).mean()
    return (2 * cov) / (yt.var() + yp.var() + (yt.mean() - yp.mean()) ** 2 + 1e-9)


def with_context(X, groups):
    frame = pd.DataFrame(X)
    return np.hstack([X] + [frame.groupby(groups).transform(lambda g: g.rolling(k, min_periods=1).mean()).to_numpy("float32")
                            for k in CONTEXT])


df = pd.read_parquet(FEAT)
voice = [c for c in df.columns if c.startswith("voice_")]
face = [c for c in df.columns if c.startswith("face_") and c not in META]
y = df["engagement"].to_numpy("float32")
speaker = (df["session"] + "_" + df["role"]).to_numpy()
lang, session = df["language"].to_numpy(), df["session"].to_numpy()
langs = sorted(df["language"].unique())
sess = df.groupby("language")["session"].unique().apply(sorted)

old_folds = [[s[k] for s in sess] for k in range(3)]
new_folds = person_folds(df, 3)
mates = same_person(df["session"].unique())
print(f"{len(df)} windows\nold folds (conversation-disjoint): {old_folds}\nnew folds (person-disjoint):       {new_folds}")
print("sessions sharing a person:", {s: m for s, m in mates.items() if len(m) > 1}, flush=True)

own = df[voice + face].fillna(0).to_numpy("float32")
fused = np.hstack([df[voice].fillna(0).to_numpy("float32")] +
                  [np.load(os.path.join("data", "features", f"pretrained_{p}.npy")) for p in ("w2vbert2", "videomae")])
INPUTS = {
    "voice": df[voice].fillna(0).to_numpy("float32"),
    "face": df[face].fillna(0).to_numpy("float32"),
    "voice + face": own,
    "voice + face + context": with_context(own, speaker),
    "fusion + context (best)": with_context(fused, speaker),
}


def gb(X, tr, te):
    m = make_pipeline(StandardScaler(), HistGradientBoostingRegressor(max_iter=300, random_state=42))
    return m.fit(X[tr], y[tr]).predict(X[te])


rows = []
for name, X in INPUTS.items():
    r = dict(input=name)
    for tag, folds in (("old", old_folds), ("new", new_folds)):
        sc = [ccc(y[np.isin(session, t)], gb(X, ~np.isin(session, t), np.isin(session, t))) for t in folds]
        r[f"ccc_{tag}"], r[f"std_{tag}"] = np.mean(sc), np.std(sc, ddof=1)
    w_old, w_new = [], []
    for l in langs:
        for s in sess[l]:
            w_old.append(ccc(y[session == s], gb(X, (lang == l) & (session != s), session == s)))
            w_new.append(ccc(y[session == s], gb(X, (lang == l) & ~np.isin(session, mates[s]), session == s)))
    cross = [ccc(y[lang == b], gb(X, lang == a, lang == b)) for a, b in itertools.permutations(langs, 2)]
    c = np.mean(cross)
    r.update(within_old=np.mean(w_old), within_new=np.mean(w_new), cross=c,
             drop_old=100 * (np.mean(w_old) - c) / np.mean(w_old), drop_new=100 * (np.mean(w_new) - c) / np.mean(w_new))
    rows.append(r)
    pd.DataFrame(rows).to_csv(OUT, index=False)
    print(f"  {name:26s} folds {r['ccc_old']:.3f} -> {r['ccc_new']:.3f} (+-{r['std_new']:.3f}) | within {r['within_old']:.3f} -> "
          f"{r['within_new']:.3f} | cross {c:.3f} | drop {r['drop_old']:.0f}% -> {r['drop_new']:.0f}%", flush=True)

print("\n=========== UNSEEN CONVERSATIONS (old) vs UNSEEN PEOPLE (new), Gradient Boosting ===========")
print(f"{'input':26s} {'folds old':>9s} {'folds new':>15s} {'within old':>10s} {'within new':>10s} {'cross':>6s} {'drop old':>8s} {'drop new':>8s}")
for r in rows:
    print(f"{r['input']:26s} {r['ccc_old']:9.3f} {r['ccc_new']:7.3f} +-{r['std_new']:.3f} {r['within_old']:10.3f} "
          f"{r['within_new']:10.3f} {r['cross']:6.3f} {r['drop_old']:7.0f}% {r['drop_new']:7.0f}%")
print(f"Saved -> {OUT}")
