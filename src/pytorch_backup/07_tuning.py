"""
STEP 7: Hyperparameter tuning (Week 6-7).
Searches dropout, learning rate, hidden layer sizes and optimizer to find the
best ANN settings. Uses a train/validation/test split so tuning is fair:
configs are compared on VALIDATION, and only the winner is scored on TEST.
Input: data/features/noxi_engagement.parquet
Output: reports/tuning_results.csv  + reports/noxi_mlp_tuned.pt
"""

import os
import itertools
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

torch.manual_seed(42)
np.random.seed(42)
FEATURES = os.path.join("data", "features", "noxi_engagement.parquet")
os.makedirs("reports", exist_ok=True)
EPOCHS = 30


def ccc(yt, yp):
    yt, yp = np.asarray(yt), np.asarray(yp)
    cov = ((yt - yt.mean()) * (yp - yp.mean())).mean()
    return (2 * cov) / (yt.var() + yp.var() + (yt.mean() - yp.mean()) ** 2 + 1e-9)


# load and split 60% train / 20% validation / 20% test
df = pd.read_parquet(FEATURES)
cols = [c for c in df.columns if c.startswith(("voice_", "face_"))]
X = df[cols].fillna(0).to_numpy("float32")
y = df["engagement"].to_numpy("float32")
X_tmp, X_te, y_tmp, y_te = train_test_split(X, y, test_size=0.2, random_state=42)
X_tr, X_va, y_tr, y_va = train_test_split(X_tmp, y_tmp, test_size=0.25, random_state=42)
sc = StandardScaler().fit(X_tr)
X_tr, X_va, X_te = [sc.transform(a).astype("float32") for a in (X_tr, X_va, X_te)]
print(f"train {len(X_tr)} | val {len(X_va)} | test {len(X_te)}\n", flush=True)


class MLP(nn.Module):
    def __init__(self, n_in, h1, h2, drop):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(n_in, h1), nn.ReLU(), nn.Dropout(drop),
            nn.Linear(h1, h2), nn.ReLU(), nn.Dropout(drop),
            nn.Linear(h2, 1),
        )

    def forward(self, x):
        return self.net(x).squeeze(1)


def run(drop, lr, hidden, opt_name="adam", epochs=EPOCHS):
    """Train one configuration and return its validation CCC."""
    h1, h2 = hidden
    torch.manual_seed(42)
    model = MLP(X_tr.shape[1], h1, h2, drop)
    if opt_name == "adam":
        opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-4)
    else:
        opt = torch.optim.SGD(model.parameters(), lr=lr, momentum=0.9, weight_decay=1e-4)
    lossf = nn.MSELoss()
    loader = DataLoader(TensorDataset(torch.tensor(X_tr), torch.tensor(y_tr)),
                        batch_size=128, shuffle=True)
    Xva_t = torch.tensor(X_va)
    for _ in range(epochs):
        model.train()
        for xb, yb in loader:
            opt.zero_grad()
            lossf(model(xb), yb).backward()
            opt.step()
    model.eval()
    with torch.no_grad():
        val = ccc(y_va, model(Xva_t).numpy())
    return val, model


# ---------- grid search (dropout x learning rate x hidden size) ----------
DROPOUTS = [0.1, 0.3, 0.5]
LRS = [1e-3, 5e-4]
HIDDENS = [(256, 128), (512, 256)]

rows = []
print(f"{'dropout':>8} {'lr':>8} {'hidden':>12} {'optimizer':>10} {'val CCC':>8}", flush=True)
for drop, lr, hid in itertools.product(DROPOUTS, LRS, HIDDENS):
    val, _ = run(drop, lr, hid)
    rows.append(dict(dropout=drop, lr=lr, hidden=f"{hid[0]}-{hid[1]}", optimizer="adam", val_ccc=val))
    print(f"{drop:8.1f} {lr:8.4f} {hid[0]}-{hid[1]:>8} {'adam':>10} {val:8.3f}", flush=True)

# ---------- optimizer selection: best config with SGD ----------
best = max(rows, key=lambda r: r["val_ccc"])
bh = tuple(int(v) for v in best["hidden"].split("-"))
val_sgd, _ = run(best["dropout"], best["lr"] * 10, bh, opt_name="sgd")   # SGD needs a bigger lr
rows.append(dict(dropout=best["dropout"], lr=best["lr"] * 10, hidden=best["hidden"],
                 optimizer="sgd", val_ccc=val_sgd))
print(f"{best['dropout']:8.1f} {best['lr']*10:8.4f} {best['hidden']:>12} {'sgd':>10} {val_sgd:8.3f}", flush=True)

# ---------- results table ----------
res = pd.DataFrame(rows).sort_values("val_ccc", ascending=False).reset_index(drop=True)
res.to_csv(os.path.join("reports", "tuning_results.csv"), index=False)
print("\n=========== TUNING RESULTS (ranked by validation CCC) ===========")
print(res.to_string(index=False))

# ---------- retrain the winner and score on the untouched TEST set ----------
w = res.iloc[0]
wh = tuple(int(v) for v in w["hidden"].split("-"))
val, model = run(float(w["dropout"]), float(w["lr"]), wh, str(w["optimizer"]), epochs=60)
with torch.no_grad():
    test_ccc = ccc(y_te, model(torch.tensor(X_te)).numpy())

print("\n=========== BEST CONFIGURATION ===========")
print(f"  dropout   : {w['dropout']}")
print(f"  learning rate: {w['lr']}")
print(f"  hidden    : {w['hidden']}")
print(f"  optimizer : {w['optimizer']}")
print(f"  validation CCC: {val:.3f}")
print(f"  TEST CCC      : {test_ccc:.3f}   (untuned baseline MLP was 0.823)")

torch.save({"state": model.state_dict(), "cols": cols, "config": dict(w)},
           "reports/noxi_mlp_tuned.pt")
print("\nSaved tuned model -> reports/noxi_mlp_tuned.pt")
