"""
STEP 20: Transfer learning from large pretrained Transformers.
The pretrained Transformer (XLM-RoBERTa, w2v-BERT 2.0, CLIP, DINOv2, Swin,
VideoMAE) is FROZEN - it was already trained on millions of examples by its
authors. We only train a small head on top of its 1-second embeddings:
  XGBoost head - same settings as steps 14 and 17
  dense head   - the ANN from step 14 (256-128, dropout 0.1)
Same tests as step 17, so the numbers compare directly with our own features:
  session-wise : 3 folds, whole conversations held out
  within       : leave one session out inside each language
  cross        : train on one language, test on another
Input:  data/features/pretrained_<name>.npy (step 19) + noxi_engagement.parquet
Output: reports/pretrained_results.csv
"""

# silence TensorFlow (must be set before it is imported)
import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
import logging
logging.getLogger("tensorflow").setLevel(logging.ERROR)

import sys
import itertools
import numpy as np
import pandas as pd
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from xgboost import XGBRegressor

FEAT = os.path.join("data", "features", "noxi_engagement.parquet")
OUT = os.path.join("reports", "pretrained_results.csv")
CLIP = 5
SETS = {   # name -> (embeddings, input type)
    "XLM-RoBERTa": (["xlm_roberta"], "text"),
    "w2v-BERT 2.0": (["w2vbert2"], "audio"),
    "CLIP": (["clip"], "video"),
    "DINOv2": (["dino"], "video"),
    "Swin": (["swin"], "video"),
    "VideoMAE": (["videomae"], "video"),
    "w2v-BERT 2.0 + VideoMAE": (["w2vbert2", "videomae"], "audio + video"),
}


# metric: 1.0 = perfect
def ccc(yt, yp):
    yt, yp = np.asarray(yt), np.asarray(yp)
    cov = ((yt - yt.mean()) * (yp - yp.mean())).mean()
    return (2 * cov) / (yt.var() + yp.var() + (yt.mean() - yp.mean()) ** 2 + 1e-9)


def xgb_score(tr, te):
    m = make_pipeline(StandardScaler(),
                      XGBRegressor(n_estimators=300, max_depth=6, learning_rate=0.1,
                                   subsample=0.8, colsample_bytree=0.8,
                                   tree_method="hist", random_state=42, n_jobs=-1))
    m.fit(X[tr], y[tr])
    return ccc(y[te], m.predict(X[te]))


def dense_score(tr, te):
    keras.utils.set_random_seed(42)
    m = keras.Sequential([
        layers.Input(shape=(X.shape[1],)),
        layers.Dense(256, activation="relu"), layers.Dropout(0.1),
        layers.Dense(128, activation="relu"), layers.Dropout(0.1),
        layers.Dense(1),
    ])
    m.compile(optimizer=keras.optimizers.Adam(1e-3), loss="mse")
    sc = StandardScaler().fit(X[tr])
    m.fit(np.clip(sc.transform(X[tr]), -CLIP, CLIP), y[tr], epochs=30, batch_size=128, verbose=0)
    return ccc(y[te], m.predict(np.clip(sc.transform(X[te]), -CLIP, CLIP), verbose=0).flatten())


meta = pd.read_parquet(FEAT, columns=["engagement", "language", "session"])
y = meta["engagement"].to_numpy("float32")
lang, session = meta["language"].to_numpy(), meta["session"].to_numpy()
langs = sorted(meta["language"].unique())
sess = meta.groupby("language")["session"].unique().apply(sorted)
folds = [[s[k] for s in sess] for k in range(3)]

# resume: skip sets already in the results file (add --retrain to train everything again)
retrain = "--retrain" in sys.argv
rows = pd.read_csv(OUT).to_dict("records") if os.path.exists(OUT) and not retrain else []
done = {r["model"] for r in rows}
if done:
    print(f"Already trained, loaded from {OUT}: {', '.join(done)}")
    print("Run with --retrain to train them again (about 45 minutes).\n", flush=True)

for name, (parts, kind) in SETS.items():
    if name in done:
        continue
    X = np.concatenate([np.load(os.path.join("data", "features", f"pretrained_{p}.npy")) for p in parts], axis=1)
    print(f"=== {name} ({kind}, {X.shape[1]} dims, "
          f"{100 * (np.abs(X).sum(1) == 0).mean():.0f}% empty windows) ===", flush=True)

    # 1) all languages, 3 session-wise folds - both heads
    xgb_f, dense_f = [], []
    for t in folds:
        te = np.isin(session, t)
        xgb_f.append(xgb_score(~te, te))
        dense_f.append(dense_score(~te, te))

    # 2) within-language: leave one session out inside each language
    within = [xgb_score((lang == l) & (session != s), session == s)
              for l in langs for s in sess[l]]

    # 3) cross-language: train on all of A, test on all of B
    cross = [xgb_score(lang == a, lang == b) for a, b in itertools.permutations(langs, 2)]

    w, c = np.mean(within), np.mean(cross)
    rows.append(dict(model=name, input=kind, dims=X.shape[1],
                     xgb_ccc=np.mean(xgb_f), xgb_std=np.std(xgb_f, ddof=1),
                     dense_ccc=np.mean(dense_f), dense_std=np.std(dense_f, ddof=1),
                     within_ccc=w, cross_ccc=c, drop_pct=100 * (w - c) / w))
    pd.DataFrame(rows).to_csv(OUT, index=False)
    r = rows[-1]
    print(f"  XGB head {r['xgb_ccc']:.3f} +- {r['xgb_std']:.3f} | dense head {r['dense_ccc']:.3f} +- "
          f"{r['dense_std']:.3f} | within {w:.3f} | cross {c:.3f} | drop {r['drop_pct']:.0f}%\n", flush=True)


res = pd.DataFrame(rows)
print("=========== PRETRAINED TRANSFORMERS (frozen) + trained head, unseen conversations ===========")
print(f"{'model':24s} {'input':13s} {'XGB head':>15} {'dense head':>15} {'within':>7} {'cross':>7} {'drop':>5}")
for _, r in res.iterrows():
    print(f"{r['model']:24s} {r['input']:13s} {r['xgb_ccc']:7.3f} +- {r['xgb_std']:.3f} "
          f"{r['dense_ccc']:7.3f} +- {r['dense_std']:.3f} {r['within_ccc']:7.3f} {r['cross_ccc']:7.3f} "
          f"{r['drop_pct']:4.0f}%")
print("\nReference (step 17, our eGeMAPS + OpenFace, XGBoost): 0.631 session-wise, 21% drop; voice only 0.652, 12% drop")
print(f"Saved -> {OUT}")
