# Line-by-Line Cheat Sheet (what to SAY for each line)

Study this before your viva. Almost every ML script reuses the SAME lines, so
once you learn Part 1, you can explain any of the 5 scripts.

===========================================================================
## PART 1 — The lines that appear in EVERY script (learn these first!)
===========================================================================

**`import pandas as pd`**
> "This brings in pandas, a tool for handling data tables."

**`import numpy as np`**
> "This brings in numpy, a tool for doing maths on numbers/arrays."

**`from sklearn... import ...`**
> "This imports the machine-learning models and tools I use."

**`import torch`**
> "This brings in PyTorch, the deep-learning library for my neural network."

**`df = pd.read_parquet(FEATURES)`**
> "This loads my data table (the features and engagement scores)."

**`X = df[feat_cols]...`**
> "X is my inputs — the face and voice features."

**`y = df["engagement"]...`**
> "y is the answer I want to predict — the engagement score."

**`train_test_split(X, y, test_size=0.2)`**
> "This splits the data: 80% to train the model, 20% to test it on unseen data."

**`StandardScaler()`**
> "This puts all features on the same scale so the model treats them fairly."

**`.fit(Xtr, ytr)`**
> "This TRAINS the model — it learns from the training data."

**`.predict(Xte)`**
> "This makes predictions on the test data."

**`ccc(...)` / `f1_score(...)`**
> "This scores how good the predictions are."

**`for ... in ...:`**
> "This is a loop — it repeats the same steps for each item."

**`print(...)`**
> "This shows the result on the screen."

**`if __name__ == "__main__":`**
> "This just means 'start running the program here'."

===========================================================================
## PART 2 — Script 04_baselines.py, line by line
===========================================================================

**`def ccc(y_true, y_pred):`**
> "This defines the CCC scoring function — my engagement metric."

**`cov = ((yt - yt.mean()) * (yp - yp.mean())).mean()`**
> "This is the maths of the CCC formula — it measures how well predictions
> match the true values. (It's a standard formula, I don't compute it by hand.)"

**`feat_cols = [c for c in df.columns if c.startswith(("voice_", "face_"))]`**
> "This picks out only the feature columns (the voice and face numbers)."

**`X = df[feat_cols].fillna(0).to_numpy("float32")`**
> "This turns the features into a numbers array; fillna(0) replaces any blanks with 0."

**`Xtr, Xte, ytr, yte = train_test_split(...)`**
> "This splits into training and testing sets."

**`models = { "LinearRegression": ..., "RandomForest": ..., "SVR": ... }`**
> "These are the three baseline models I compare."

**`pipe = make_pipeline(StandardScaler(), m)`**
> "This chains two steps: scale the features, then run the model."

**`pipe.fit(Xtr, ytr)`**
> "This trains the model."

**`pred = pipe.predict(Xte)`**
> "This makes predictions on the test set."

**`print(f"{name} {ccc(...)} ...")`**
> "This prints each model's scores."

===========================================================================
## PART 3 — Script 06_deep_learning.py, line by line (the neural network)
===========================================================================

**`class MLP(nn.Module):`**
> "This defines my neural network, called MLP."

**`nn.Linear(n_in, 256)`**
> "This is a layer of the network with 256 neurons; it takes the inputs in."

**`nn.ReLU()`**
> "This is an activation — it lets the network learn non-straight-line patterns."

**`nn.Dropout(0.3)`**
> "This randomly ignores 30% of neurons during training to prevent overfitting."

**`nn.Linear(128, 1)`**
> "The final layer — it outputs 1 number: the predicted engagement."

**`opt = torch.optim.Adam(model.parameters(), lr=1e-3)`**
> "Adam is the optimiser — the algorithm that improves the network as it learns.
> lr is the learning rate (how big each improvement step is)."

**`lossf = nn.MSELoss()`**
> "This measures the error — how far predictions are from the true values."

**`for epoch in range(1, 81):`**
> "This trains the network for 80 rounds (epochs) over the data."

**`opt.zero_grad()`**
> "This resets the gradients before each step. (Standard PyTorch step.)"

**`loss = lossf(model(xb), yb)`**
> "This checks how wrong the current prediction is."

**`loss.backward()`**
> "This calculates how to adjust the network to reduce the error (backpropagation)."

**`opt.step()`**
> "This updates the network to be a little better."

**`torch.save(...)`**
> "This saves the trained network to a file so I can reuse it (for the demo)."

===========================================================================
## PART 4 — Scripts 01, 02, 05 (the unique lines)
===========================================================================

**01 — `z.extract(member, DEST)`**
> "This pulls one needed file out of the zip."

**02 — `np.fromfile(header_path + '~', dtype=dtype)`**
> "This reads NoXi's binary feature file into numbers."

**02 — `np.nanmean(ege[s], 0)`**
> "This averages the features over a 1-second window."

**05 — `for a, b in itertools.product(langs, langs):`**
> "This loops over every pair of languages (train a, test b)."

**05 — `if a == b:`**
> "If training and testing on the SAME language, I leave one conversation out
> for a fair test. Otherwise, I train on one language and test on another."

===========================================================================
## GOLDEN RULES for the viva
===========================================================================
1. You do NOT write the maths yourself — libraries (sklearn, torch) do it.
   It's fine to say "this uses the library's standard function for X."
2. If unsure, read the variable names aloud: `Xtr` = X-train, `yte` = y-test,
   `pred` = predictions. The names tell the story.
3. For any line, answer WHAT it does (the goal), not the internal maths.
4. If you truly don't know a line: "That line prepares the data for the model —
   let me trace what it produces." Then read the variables.
