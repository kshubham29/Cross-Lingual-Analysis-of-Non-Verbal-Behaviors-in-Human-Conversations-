"""
STEP 7: Hyperparameter tuning (TensorFlow / Keras).
Grid-searches dropout, learning rate, hidden sizes and optimizer.
Configs are compared on VALIDATION; only the winner is scored on TEST.
Input: data/features/noxi_engagement.parquet
Output: reports/tuning_results.csv + reports/noxi_mlp_tuned.keras
"""

# silence TensorFlow (must be set before it is imported)
import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
import logging
logging.getLogger("tensorflow").setLevel(logging.ERROR)

import itertools
import numpy as np
import pandas as pd
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

keras.utils.set_random_seed(42)
FEATURES = os.path.join("data", "features", "noxi_engagement.parquet")
os.makedirs("reports", exist_ok=True)
EPOCHS = 30          # short runs, so 13 networks stay feasible on a CPU


# metric: 1.0 = perfect
def ccc(yt, yp):
    yt, yp = np.asarray(yt), np.asarray(yp)
    cov = ((yt - yt.mean()) * (yp - yp.mean())).mean()
    return (2 * cov) / (yt.var() + yp.var() + (yt.mean() - yp.mean()) ** 2 + 1e-9)


# load data, split 60/20/20, scale (scaler fitted on train only)
df = pd.read_parquet(FEATURES)
cols = [c for c in df.columns if c.startswith(("voice_", "face_"))]
X = df[cols].fillna(0).to_numpy("float32")
y = df["engagement"].to_numpy("float32")
X_tmp, X_te, y_tmp, y_te = train_test_split(X, y, test_size=0.2, random_state=42)
X_tr, X_va, y_tr, y_va = train_test_split(X_tmp, y_tmp, test_size=0.25, random_state=42)
sc = StandardScaler().fit(X_tr)
X_tr, X_va, X_te = [sc.transform(a).astype("float32") for a in (X_tr, X_va, X_te)]
print(f"train {len(X_tr)} | val {len(X_va)} | test {len(X_te)}\n", flush=True)


# build, train and score ONE configuration (seed reset so all start equal)
def run(drop, lr, hidden, opt_name="adam", epochs=EPOCHS):
    h1, h2 = hidden
    keras.utils.set_random_seed(42)
    model = keras.Sequential([
        layers.Input(shape=(X_tr.shape[1],)),
        layers.Dense(h1, activation="relu"), layers.Dropout(drop),
        layers.Dense(h2, activation="relu"), layers.Dropout(drop),
        layers.Dense(1),
    ])
    opt = (keras.optimizers.Adam(learning_rate=lr) if opt_name == "adam"
           else keras.optimizers.SGD(learning_rate=lr, momentum=0.9))
    model.compile(optimizer=opt, loss="mse")
    model.fit(X_tr, y_tr, epochs=epochs, batch_size=128, verbose=0)
    return ccc(y_va, model.predict(X_va, verbose=0).flatten()), model


# grid search: 3 dropouts x 2 learning rates x 2 architectures = 12 configs
DROPOUTS, LRS, HIDDENS = [0.1, 0.3, 0.5], [1e-3, 5e-4], [(256, 128), (512, 256)]
rows = []
print(f"{'dropout':>8} {'lr':>8} {'hidden':>12} {'optimizer':>10} {'val CCC':>8}", flush=True)
for drop, lr, hid in itertools.product(DROPOUTS, LRS, HIDDENS):
    val, _ = run(drop, lr, hid)
    hid_str = f"{hid[0]}-{hid[1]}"
    rows.append(dict(dropout=drop, lr=lr, hidden=hid_str, optimizer="adam", val_ccc=val))
    print(f"{drop:8.1f} {lr:8.4f} {hid_str:>12} {'adam':>10} {val:8.3f}", flush=True)

# 13th run: the winning config with SGD instead of Adam (SGD needs a 10x lr)
best = max(rows, key=lambda r: r["val_ccc"])
bh = tuple(int(v) for v in best["hidden"].split("-"))
val_sgd, _ = run(best["dropout"], best["lr"] * 10, bh, opt_name="sgd")
rows.append(dict(dropout=best["dropout"], lr=best["lr"] * 10,
                 hidden=best["hidden"], optimizer="sgd", val_ccc=val_sgd))
print(f"{best['dropout']:8.1f} {best['lr']*10:8.4f} {best['hidden']:>12} "
      f"{'sgd':>10} {val_sgd:8.3f}", flush=True)

# rank all 13 configs by validation score and save the table as evidence
res = pd.DataFrame(rows).sort_values("val_ccc", ascending=False).reset_index(drop=True)
res.to_csv(os.path.join("reports", "tuning_results.csv"), index=False)
print("\n=========== TUNING RESULTS (ranked by validation CCC) ===========")
print(res.to_string(index=False))

# retrain the winner for longer, then score it on the untouched test set
w = res.iloc[0]
wh = tuple(int(v) for v in w["hidden"].split("-"))
val, model = run(float(w["dropout"]), float(w["lr"]), wh, str(w["optimizer"]), epochs=60)
test_ccc = ccc(y_te, model.predict(X_te, verbose=0).flatten())

print("\n=========== BEST CONFIGURATION ===========")
print(f"  dropout       : {w['dropout']}")
print(f"  learning rate : {w['lr']}")
print(f"  hidden        : {w['hidden']}")
print(f"  optimizer     : {w['optimizer']}")
print(f"  validation CCC: {val:.3f}")
print(f"  TEST CCC      : {test_ccc:.3f}")

# save the tuned model for reuse
model.save(os.path.join("reports", "noxi_mlp_tuned.keras"))
print("\nSaved tuned model -> reports/noxi_mlp_tuned.keras")
