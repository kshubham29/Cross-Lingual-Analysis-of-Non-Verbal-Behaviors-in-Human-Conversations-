"""
STEP 10: Transfer learning (TensorFlow / Keras), session-wise.
Pretrain the CNN on two languages, then adapt it to the third using ONE
conversation of that language, and test on its OTHER two conversations - so
adaptation and test never share a session. Each of the 3 target conversations
takes a turn as the adaptation session, and the adaptation data is also cut to
10%, 25%, 50% and 100% of that session to see how much new-language data is needed.
Four conditions, each reported separately:
  zero-shot  - pretrained model used as-is, no target data
  head-only  - conv layers frozen, only the dense head retrained
  fine-tune  - all layers retrained with a small learning rate
  scratch    - same CNN trained on the adaptation data only, no pretraining
Input:  data/features/noxi_sequences.npy + data/features/noxi_engagement.parquet
Output: reports/transfer_results.csv + reports/cnn_pretrained_not_{lang}.keras / scaler_not_{lang}.joblib
"""

# silence TensorFlow (must be set before it is imported)
import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
import logging
logging.getLogger("tensorflow").setLevel(logging.ERROR)

import joblib
import numpy as np
import pandas as pd
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.preprocessing import StandardScaler

keras.utils.set_random_seed(42)
FEAT = os.path.join("data", "features", "noxi_engagement.parquet")
SEQ = os.path.join("data", "features", "noxi_sequences.npy")
os.makedirs("reports", exist_ok=True)

PRETRAIN_EPOCHS = 30
ADAPT_EPOCHS = 20
FRACTIONS = [0.1, 0.25, 0.5, 1.0]     # share of the adaptation session used


# metric: 1.0 = perfect
def ccc(yt, yp):
    yt, yp = np.asarray(yt), np.asarray(yp)
    cov = ((yt - yt.mean()) * (yp - yp.mean())).mean()
    return (2 * cov) / (yt.var() + yp.var() + (yt.mean() - yp.mean()) ** 2 + 1e-9)


# load sequences + labels + language/session tags; drop the 5 OpenFace bookkeeping columns
meta = pd.read_parquet(FEAT, columns=["engagement", "language", "session"])
y_all = meta["engagement"].to_numpy("float32")
lang_all = meta["language"].to_numpy()
sess_all = meta["session"].to_numpy()
X_all = np.load(SEQ)
assert len(X_all) == len(y_all) and X_all.shape[2] == 802
X_all = np.delete(X_all, range(88, 93), axis=2)
n_steps, n_feat = X_all.shape[1], X_all.shape[2]
langs = sorted(set(lang_all))
print(f"sequences {X_all.shape} | languages {langs}\n", flush=True)


# the tuned CNN from step 9 (32 filters, kernel 5, dropout 0.1)
def build():
    return keras.Sequential([
        layers.Input(shape=(n_steps, n_feat)),
        layers.Conv1D(32, 5, activation="relu"), layers.MaxPooling1D(2),
        layers.Conv1D(64, 5, activation="relu"), layers.MaxPooling1D(2),
        layers.Flatten(),
        layers.Dense(128, activation="relu"), layers.Dropout(0.1),
        layers.Dense(64, activation="relu"), layers.Dropout(0.1),
        layers.Dense(1),
    ])


def train(model, X, y, epochs, lr):
    model.compile(optimizer=keras.optimizers.Adam(lr), loss="mse")
    model.fit(X, y, epochs=epochs, batch_size=128, verbose=0)
    return model


def score(model, X, y):
    return ccc(y, model.predict(X, verbose=0).flatten())


def copy_of(base):
    m = keras.models.clone_model(base)
    m.set_weights(base.get_weights())
    return m


rows = []
for target in langs:
    print(f"=== target language: {target} ===", flush=True)
    src = np.where(lang_all != target)[0]

    # scale everything with a scaler fitted on the SOURCE languages only, clip extreme values to [-5, 5]
    sc = StandardScaler().fit(X_all[src].reshape(-1, n_feat))
    def prep(idx):
        z = sc.transform(X_all[idx].reshape(-1, n_feat)).reshape(len(idx), n_steps, n_feat)
        return np.clip(z, -5, 5).astype("float32")

    # 1) pretrain on the two source languages
    keras.utils.set_random_seed(42)
    base = train(build(), prep(src), y_all[src], PRETRAIN_EPOCHS, 1e-3)
    base.save(os.path.join("reports", f"cnn_pretrained_not_{target}.keras"))
    joblib.dump(sc, os.path.join("reports", f"scaler_not_{target}.joblib"))

    # each conversation of the target language takes a turn as the adaptation session
    for adapt_s in sorted(set(sess_all[lang_all == target])):
        i_session = np.where(sess_all == adapt_s)[0]
        i_test = np.where((lang_all == target) & (sess_all != adapt_s))[0]
        X_te, y_te = prep(i_test), y_all[i_test]
        zero_shot = score(base, X_te, y_te)
        print(f"  adapt on session {adapt_s} ({len(i_session)} windows), test on {len(i_test)} | "
              f"zero-shot {zero_shot:.3f}", flush=True)

        for frac in FRACTIONS:
            rng = np.random.default_rng(42)
            i_adapt = rng.choice(i_session, size=int(frac * len(i_session)), replace=False)
            X_ad, y_ad = prep(i_adapt), y_all[i_adapt]

            # 2) head-only: freeze the conv layers, retrain the dense head
            head = copy_of(base)
            for l in head.layers:
                if isinstance(l, layers.Conv1D):
                    l.trainable = False
            head_only = score(train(head, X_ad, y_ad, ADAPT_EPOCHS, 1e-3), X_te, y_te)

            # 3) fine-tune: all layers, small learning rate so pretrained weights are kept
            fine_tune = score(train(copy_of(base), X_ad, y_ad, ADAPT_EPOCHS, 1e-4), X_te, y_te)

            # 4) scratch: same network, same adaptation data, no pretraining
            keras.utils.set_random_seed(42)
            scratch = score(train(build(), X_ad, y_ad, PRETRAIN_EPOCHS, 1e-3), X_te, y_te)

            rows.append(dict(target=target, adapt_session=adapt_s, fraction=frac,
                             n_adapt=len(i_adapt), n_test=len(i_test), zero_shot=zero_shot,
                             head_only=head_only, fine_tune=fine_tune, scratch=scratch))
            print(f"    {int(frac * 100):3d}% ({len(i_adapt):4d} windows)  head-only {head_only:.3f} | "
                  f"fine-tune {fine_tune:.3f} | scratch {scratch:.3f}", flush=True)
    print()


res = pd.DataFrame(rows)
res.to_csv(os.path.join("reports", "transfer_results.csv"), index=False)
cond = ["zero_shot", "head_only", "fine_tune", "scratch"]
print("=========== TRANSFER LEARNING, SESSION-WISE (CCC, mean over 3 languages x 3 sessions) ===========")
print(res.groupby("fraction")[cond].mean().round(3).to_string())
print("\nby target language, using the full adaptation session:")
print(res[res.fraction == 1.0].groupby("target")[cond].mean().round(3).to_string())
print("\nSaved -> reports/transfer_results.csv")
