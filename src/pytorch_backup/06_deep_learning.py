"""
STEP 5: Deep learning model.
Train a neural network (MLP) to predict engagement, and compare it to the
Random Forest baseline. Saves the trained model for the demo.
Input: data/features/noxi_engagement.parquet
Output: reports/noxi_mlp.pt
"""

import os
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error

torch.manual_seed(42)
np.random.seed(42)
FEATURES = os.path.join("data", "features", "noxi_engagement.parquet")
os.makedirs("reports", exist_ok=True)


def ccc(yt, yp):
    # the engagement metric (closer to 1.0 = better)
    yt, yp = np.asarray(yt), np.asarray(yp)
    cov = ((yt - yt.mean()) * (yp - yp.mean())).mean()
    return (2 * cov) / (yt.var() + yp.var() + (yt.mean() - yp.mean()) ** 2 + 1e-9)


# load the data, split 80/20, and scale the features
df = pd.read_parquet(FEATURES)
cols = [c for c in df.columns if c.startswith(("voice_", "face_"))]
X = df[cols].fillna(0).to_numpy("float32")
y = df["engagement"].to_numpy("float32")
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42)
scaler = StandardScaler().fit(Xtr)
Xtr = scaler.transform(Xtr).astype("float32")
Xte = scaler.transform(Xte).astype("float32")

# baseline (Random Forest) to compare against
rf = RandomForestRegressor(n_estimators=120, n_jobs=-1, random_state=42).fit(Xtr, ytr)
rf_pred = rf.predict(Xte)


# the neural network: 802 inputs -> 256 -> 128 -> 1 output (engagement)
class MLP(nn.Module):
    def __init__(self, n_in):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(n_in, 256), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(256, 128), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(128, 1),
        )

    def forward(self, x):
        return self.net(x).squeeze(1)


model = MLP(Xtr.shape[1])
opt = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-4)
lossf = nn.MSELoss()
loader = DataLoader(TensorDataset(torch.tensor(Xtr), torch.tensor(ytr)),
  batch_size=64, shuffle=True)
Xte_t = torch.tensor(Xte)

# train the network for 80 rounds
print("Training the MLP...")
for epoch in range(1, 81):
    model.train()
    for xb, yb in loader:
        opt.zero_grad()
        loss = lossf(model(xb), yb)
        loss.backward()
        opt.step()
    if epoch % 20 == 0:
        model.eval()
        with torch.no_grad():
            p = model(Xte_t).numpy()
        print(f"  epoch {epoch:3d}  test CCC = {ccc(yte, p):.3f}")

# final predictions and comparison
model.eval()
with torch.no_grad():
    mlp_pred = model(Xte_t).numpy()

print("\n============ ENGAGEMENT prediction ============")
print(f"{'model':16s} {'CCC':>7} {'Pearson':>8} {'MAE':>7}")
for name, pred in [("RandomForest", rf_pred), ("MLP (Deep)", mlp_pred)]:
    r = np.corrcoef(yte, pred)[0, 1]
    print(f"{name:16s} {ccc(yte, pred):7.3f} {r:8.3f} {mean_absolute_error(yte, pred):7.3f}")

# save the trained network for the demo website
torch.save({"state": model.state_dict(), "cols": cols,
            "mean": scaler.mean_, "scale": scaler.scale_}, "reports/noxi_mlp.pt")
print("\nSaved trained model -> reports/noxi_mlp.pt")
