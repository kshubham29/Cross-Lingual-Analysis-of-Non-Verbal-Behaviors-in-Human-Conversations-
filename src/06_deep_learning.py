"""
STEP 6: Deep learning model (TensorFlow / Keras).
Train a neural network (MLP) to predict engagement, and compare it to the
Random Forest baseline. Saves the trained model for the demo.
Input: data/features/noxi_engagement.parquet
Output: reports/noxi_mlp.keras
"""

# ---------------------------------------------------------------------------
# BLOCK 1 - SETTINGS
# Turn off TensorFlow's noisy startup messages. This must happen before
# TensorFlow is imported, otherwise the warnings still appear.
# ---------------------------------------------------------------------------
import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

# ---------------------------------------------------------------------------
# BLOCK 2 - IMPORTS
# pandas/numpy handle the data, keras builds the neural network, and
# scikit-learn provides the split, the scaler and the Random Forest baseline.
# ---------------------------------------------------------------------------
import numpy as np
import pandas as pd
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error

# Fix the random seed so the network starts from the same random weights every
# run - this makes our results reproducible.
keras.utils.set_random_seed(42)
FEATURES = os.path.join("data", "features", "noxi_engagement.parquet")
os.makedirs("reports", exist_ok=True)


# ---------------------------------------------------------------------------
# BLOCK 3 - THE SCORING FUNCTION
# CCC (Concordance Correlation Coefficient) is our metric. It checks whether
# the predictions match the true engagement in both trend and actual value.
# 1.0 is perfect. We use CCC instead of accuracy because engagement is a
# continuous number, not a category.
# ---------------------------------------------------------------------------
def ccc(yt, yp):
    yt, yp = np.asarray(yt), np.asarray(yp)
    cov = ((yt - yt.mean()) * (yp - yp.mean())).mean()
    return (2 * cov) / (yt.var() + yp.var() + (yt.mean() - yp.mean()) ** 2 + 1e-9)


# ---------------------------------------------------------------------------
# BLOCK 4 - LOAD THE DATA
# Read the feature table. X = the 802 inputs (voice + face features),
# y = the answer we want to predict (engagement, a number from 0 to 1).
# ---------------------------------------------------------------------------
df = pd.read_parquet(FEATURES)
cols = [c for c in df.columns if c.startswith(("voice_", "face_"))]
X = df[cols].fillna(0).to_numpy("float32")
y = df["engagement"].to_numpy("float32")

# ---------------------------------------------------------------------------
# BLOCK 5 - SPLIT AND SCALE
# Keep 20% of the data aside for testing, so we measure performance on rows the
# model has never seen. Then scale the features to a similar range, because
# neural networks train faster and more reliably on scaled inputs.
# The scaler is fitted on the TRAINING data only, so no test information leaks.
# ---------------------------------------------------------------------------
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42)
scaler = StandardScaler().fit(Xtr)
Xtr = scaler.transform(Xtr).astype("float32")
Xte = scaler.transform(Xte).astype("float32")

# ---------------------------------------------------------------------------
# BLOCK 6 - THE BASELINE TO BEAT
# Train a Random Forest on exactly the same data. This gives a fair, direct
# comparison between a classic machine-learning model and the neural network.
# ---------------------------------------------------------------------------
rf = RandomForestRegressor(n_estimators=120, n_jobs=-1, random_state=42).fit(Xtr, ytr)
rf_pred = rf.predict(Xte)

# ---------------------------------------------------------------------------
# BLOCK 7 - BUILD THE NEURAL NETWORK (the ANN)
# Structure: 802 inputs -> 256 neurons -> 128 neurons -> 1 output.
#   Dense   = a layer of neurons that learns patterns.
#   ReLU    = the activation function; keeps positive values and turns
#             negatives to zero, which lets the network learn curved (non-linear)
#             patterns. Without it the network could only learn straight lines.
#   Dropout = randomly switches off 30% of neurons while training, which stops
#             the network memorising the training data (prevents overfitting).
#   Last Dense(1) has no activation because we want a raw number (regression).
# ---------------------------------------------------------------------------
model = keras.Sequential([
    layers.Input(shape=(Xtr.shape[1],)),
    layers.Dense(256, activation="relu"),
    layers.Dropout(0.3),
    layers.Dense(128, activation="relu"),
    layers.Dropout(0.3),
    layers.Dense(1),
])

# ---------------------------------------------------------------------------
# BLOCK 8 - SET UP TRAINING
# Adam is the optimizer: the algorithm that adjusts the network's weights to
# reduce the error. MSE (mean squared error) is the loss: it measures how far
# the predictions are from the true engagement values.
# ---------------------------------------------------------------------------
model.compile(optimizer=keras.optimizers.Adam(learning_rate=1e-3), loss="mse")

# ---------------------------------------------------------------------------
# BLOCK 9 - TRAIN THE NETWORK
# We train for 80 epochs in total (one epoch = one full pass over the data),
# done in 4 stages of 20 so we can print the score as it improves.
# Inside model.fit(), Keras repeatedly: makes predictions, measures the error,
# runs backpropagation to work out how each weight should change, and updates
# them. batch_size=64 means it learns from 64 rows at a time.
# ---------------------------------------------------------------------------
print("Training the MLP...")
for stage in range(4):
    model.fit(Xtr, ytr, epochs=20, batch_size=64, verbose=0)
    p = model.predict(Xte, verbose=0).flatten()
    print(f"  epoch {(stage + 1) * 20:3d}  test CCC = {ccc(yte, p):.3f}")

# ---------------------------------------------------------------------------
# BLOCK 10 - COMPARE THE MODELS
# Make final predictions with the network and print both models side by side,
# scored with CCC, Pearson correlation and mean absolute error.
# ---------------------------------------------------------------------------
mlp_pred = model.predict(Xte, verbose=0).flatten()
print("\n============ ENGAGEMENT prediction ============")
print(f"{'model':16s} {'CCC':>7} {'Pearson':>8} {'MAE':>7}")
for name, pred in [("RandomForest", rf_pred), ("MLP (Deep)", mlp_pred)]:
    r = np.corrcoef(yte, pred)[0, 1]
    print(f"{name:16s} {ccc(yte, pred):7.3f} {r:8.3f} {mean_absolute_error(yte, pred):7.3f}")

# ---------------------------------------------------------------------------
# BLOCK 11 - SAVE THE TRAINED NETWORK
# Store the model so it can be reused later without retraining, for example in
# a demo application.
# ---------------------------------------------------------------------------
model.save("reports/noxi_mlp.keras")
print("\nSaved trained model -> reports/noxi_mlp.keras")
