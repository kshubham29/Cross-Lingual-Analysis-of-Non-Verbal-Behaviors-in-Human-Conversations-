"""
STEP 7: Hyperparameter tuning (TensorFlow / Keras).
Searches dropout, learning rate, hidden layer sizes and optimizer to find the
best ANN settings. Uses a train/validation/test split so tuning is fair:
configs are compared on VALIDATION, and only the winner is scored on TEST.
Input: data/features/noxi_engagement.parquet
Output: reports/tuning_results.csv  + reports/noxi_mlp_tuned.keras
"""

# ---------------------------------------------------------------------------
# BLOCK 1 - SETTINGS
# Silence TensorFlow's startup messages (must be set before importing it).
# ---------------------------------------------------------------------------
import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

# ---------------------------------------------------------------------------
# BLOCK 2 - IMPORTS
# itertools.product builds the grid of settings to try. EPOCHS is kept at 30
# so that trying many configurations stays feasible on a CPU.
# ---------------------------------------------------------------------------
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
EPOCHS = 30


# ---------------------------------------------------------------------------
# BLOCK 3 - THE SCORING FUNCTION
# CCC again, so results are directly comparable with the other steps.
# ---------------------------------------------------------------------------
def ccc(yt, yp):
    yt, yp = np.asarray(yt), np.asarray(yp)
    cov = ((yt - yt.mean()) * (yp - yp.mean())).mean()
    return (2 * cov) / (yt.var() + yp.var() + (yt.mean() - yp.mean()) ** 2 + 1e-9)


# ---------------------------------------------------------------------------
# BLOCK 4 - THREE-WAY SPLIT (the key to honest tuning)
# 60% train / 20% validation / 20% test.
#   train      - used to fit each configuration
#   validation - used to COMPARE configurations and pick the winner
#   test       - never touched during tuning; only the winner is scored on it
# If we chose the best settings using the test set, the final score would look
# better than it really is. Keeping a separate validation set avoids that.
# ---------------------------------------------------------------------------
df = pd.read_parquet(FEATURES)
cols = [c for c in df.columns if c.startswith(("voice_", "face_"))]
X = df[cols].fillna(0).to_numpy("float32")
y = df["engagement"].to_numpy("float32")
X_tmp, X_te, y_tmp, y_te = train_test_split(X, y, test_size=0.2, random_state=42)
X_tr, X_va, y_tr, y_va = train_test_split(X_tmp, y_tmp, test_size=0.25, random_state=42)
sc = StandardScaler().fit(X_tr)
X_tr, X_va, X_te = [sc.transform(a).astype("float32") for a in (X_tr, X_va, X_te)]
print(f"train {len(X_tr)} | val {len(X_va)} | test {len(X_te)}\n", flush=True)


# ---------------------------------------------------------------------------
# BLOCK 5 - TRAIN ONE CONFIGURATION
# Builds a network with the given settings, trains it, and returns its score on
# the validation set. Called once for every combination in the grid.
# The seed is reset each time so every configuration starts from the same
# random weights - otherwise we would be comparing luck, not settings.
# ---------------------------------------------------------------------------
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
    val = ccc(y_va, model.predict(X_va, verbose=0).flatten())
    return val, model


# ---------------------------------------------------------------------------
# BLOCK 6 - THE GRID SEARCH
# Every combination of dropout, learning rate and architecture is tried:
#   dropout       - how much regularisation the network needs
#   learning rate - how big each improvement step is
#   hidden sizes  - the architecture (this is "architecture refinement")
# 3 x 2 x 2 = 12 configurations in total.
# ---------------------------------------------------------------------------
DROPOUTS = [0.1, 0.3, 0.5]
LRS = [1e-3, 5e-4]
HIDDENS = [(256, 128), (512, 256)]

rows = []
print(f"{'dropout':>8} {'lr':>8} {'hidden':>12} {'optimizer':>10} {'val CCC':>8}", flush=True)
for drop, lr, hid in itertools.product(DROPOUTS, LRS, HIDDENS):
    val, _ = run(drop, lr, hid)
    rows.append(dict(dropout=drop, lr=lr, hidden=f"{hid[0]}-{hid[1]}", optimizer="adam", val_ccc=val))
    print(f"{drop:8.1f} {lr:8.4f} {hid[0]}-{hid[1]:>8} {'adam':>10} {val:8.3f}", flush=True)

# ---------------------------------------------------------------------------
# BLOCK 7 - OPTIMIZER SELECTION
# Take the winning configuration and train it again with SGD instead of Adam,
# so we can compare the two optimizers fairly on identical settings.
# SGD normally needs a larger learning rate, so we scale it up by 10.
# ---------------------------------------------------------------------------
best = max(rows, key=lambda r: r["val_ccc"])
bh = tuple(int(v) for v in best["hidden"].split("-"))
val_sgd, _ = run(best["dropout"], best["lr"] * 10, bh, opt_name="sgd")
rows.append(dict(dropout=best["dropout"], lr=best["lr"] * 10, hidden=best["hidden"],
                 optimizer="sgd", val_ccc=val_sgd))
print(f"{best['dropout']:8.1f} {best['lr']*10:8.4f} {best['hidden']:>12} {'sgd':>10} {val_sgd:8.3f}", flush=True)

# ---------------------------------------------------------------------------
# BLOCK 8 - RANK THE RESULTS
# Sort every configuration by its validation score, best first, and save the
# table so the comparison can be reported.
# ---------------------------------------------------------------------------
res = pd.DataFrame(rows).sort_values("val_ccc", ascending=False).reset_index(drop=True)
res.to_csv(os.path.join("reports", "tuning_results.csv"), index=False)
print("\n=========== TUNING RESULTS (ranked by validation CCC) ===========")
print(res.to_string(index=False))

# ---------------------------------------------------------------------------
# BLOCK 9 - RETRAIN THE WINNER AND SCORE IT ON TEST
# The winning settings are trained again for longer (60 epochs), then scored on
# the test set that was never used during tuning. This is the honest final
# number we report.
# ---------------------------------------------------------------------------
w = res.iloc[0]
wh = tuple(int(v) for v in w["hidden"].split("-"))
val, model = run(float(w["dropout"]), float(w["lr"]), wh, str(w["optimizer"]), epochs=60)
test_ccc = ccc(y_te, model.predict(X_te, verbose=0).flatten())

print("\n=========== BEST CONFIGURATION ===========")
print(f"  dropout   : {w['dropout']}")
print(f"  learning rate: {w['lr']}")
print(f"  hidden    : {w['hidden']}")
print(f"  optimizer : {w['optimizer']}")
print(f"  validation CCC: {val:.3f}")
print(f"  TEST CCC      : {test_ccc:.3f}")

# ---------------------------------------------------------------------------
# BLOCK 10 - SAVE THE TUNED MODEL
# ---------------------------------------------------------------------------
model.save("reports/noxi_mlp_tuned.keras")
print("\nSaved tuned model -> reports/noxi_mlp_tuned.keras")
