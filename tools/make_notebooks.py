"""Writes very simple, explainable Jupyter notebooks for the 12 main steps into notebooks/.
Each notebook does the same work as the matching script in src/ (same models, same
settings, same order), written with plain loops and short cells, each with a note.
Notebooks do not overwrite data/ or reports/: they show the results, and the last
cell compares them with the results saved by the original script.
Run from the project folder: python tools/make_notebooks.py"""
import os
import nbformat as nbf

OUT = "notebooks"
os.makedirs(OUT, exist_ok=True)

GO = '''import os
if os.getcwd().endswith("notebooks"):
    os.chdir("..")          # work from the project folder'''

GO_TF = '''import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"     # hide TensorFlow messages
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"    # same maths settings as the original script
if os.getcwd().endswith("notebooks"):
    os.chdir("..")                           # work from the project folder'''

CCC = '''def ccc(y_true, y_pred):
    # Concordance Correlation Coefficient: 1 = perfect agreement
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    covariance = np.mean((y_true - y_true.mean()) * (y_pred - y_pred.mean()))
    return 2 * covariance / (y_true.var() + y_pred.var() + (y_true.mean() - y_pred.mean()) ** 2 + 1e-9)'''

LOAD = '''df = pd.read_parquet("data/features/noxi_engagement.parquet")

# the first 5 face columns are bookkeeping (frame number, face id, time, confidence, success)
bookkeeping = ["face_0", "face_1", "face_2", "face_3", "face_4"]
cols = []
for c in df.columns:
    if (c.startswith("voice_") or c.startswith("face_")) and c not in bookkeeping:
        cols.append(c)

X = df[cols].fillna(0).to_numpy("float32")      # features
y = df["engagement"].to_numpy("float32")        # labels
print(X.shape)'''

FOLDS = '''# the 3 sessions of each language
english = sorted(df[df["language"] == "English"]["session"].unique())
french = sorted(df[df["language"] == "French"]["session"].unique())
german = sorted(df[df["language"] == "German"]["session"].unique())

# fold 1 tests on the 1st session of each language, fold 2 on the 2nd, fold 3 on the 3rd
folds = []
for k in range(3):
    folds.append([english[k], french[k], german[k]])
print(folds)'''

PAST_MEAN = '''def past_mean(X, speakers, k):
    # for every row: the mean of the same speaker's last k seconds (only the past)
    out = np.zeros(X.shape)
    for s in pd.unique(speakers):
        rows = np.where(speakers == s)[0]
        out[rows] = pd.DataFrame(X[rows]).rolling(k, min_periods=1).mean().to_numpy()
    return out'''


DATASET = """### Dataset
**NoXi** (NOvice eXpert Interaction) - multimodal recordings of expert-novice conversations with continuous engagement labels.
- Dataset page: https://multimediate-challenge.org/datasets/Dataset_NoXi/
- Paper: A. Cafaro et al., "The NoXi Database: Multimodal Recordings of Mediated Novice-Expert Interactions", ACM ICMI 2017, https://doi.org/10.1145/3136755.3136780
- Used here: 9 conversations (English 027, 028, 030; French 001, 013, 021; German 070, 072, 077) from the NoXi train set:
  eGeMAPS voice features, OpenFace 2.0 face features, engagement labels (25 per second) and the pretrained-Transformer embeddings shipped with the corpus.
- Licence: NoXi is available for research under an End-User Licence Agreement (signed by the supervisor). The data is **not included** here and must not be shared;
  request access on the dataset page and place the downloaded zips as described in `01_extract_data`."""


def build(name, title, cells):
    nb = nbf.v4.new_notebook()
    nb.cells.append(nbf.v4.new_markdown_cell(title))
    nb.cells.append(nbf.v4.new_markdown_cell(DATASET))
    for kind, text in cells:
        nb.cells.append(nbf.v4.new_markdown_cell(text) if kind == "md" else nbf.v4.new_code_cell(text))
    nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
    nbf.write(nb, os.path.join(OUT, name))
    print("wrote", name)


M, C = "md", "code"

# ================================================================= 01
build("01_extract_data.ipynb",
      "# Step 1: Extract the data\nThe NoXi zips are huge (14 GB). We copy out only the small files we need.\n"
      "*Same as `src/01_extract_data.py`. Files already extracted are skipped.*",
      [(M, "Go to the project folder."), (C, GO),
       (M, "The file endings we keep: voice features, face features, engagement labels, language."),
       (C, '''import zipfile

KEEP = (".audio.egemapsv2.stream", ".audio.egemapsv2.stream~",
        ".openface2.stream", ".openface2.stream~",
        ".engagement.annotation.csv",
        "language.annotation.csv")

ZIPS = ["C:/Users/SHUBHAM KUMAR/Downloads/train.zip",
        "C:/Users/SHUBHAM KUMAR/Downloads/027.zip"]'''),
       (M, "Open each zip and copy out every file that ends with one of those endings."),
       (C, '''for zip_path in ZIPS:
    z = zipfile.ZipFile(zip_path)
    for name in z.namelist():
        if name.endswith(KEEP) and not os.path.exists("data/noxi/" + name):
            z.extract(name, "data/noxi")
    print("done:", zip_path)'''),
       (M, "Check: one folder per conversation."),
       (C, '''for session in sorted(os.listdir("data/noxi")):
    print(session, len(os.listdir("data/noxi/" + session)), "files")'''),
       ])

# ================================================================= 02
build("02_build_features.ipynb",
      "# Step 2: Build the feature table\nLine up voice + face features with the engagement score, cut each "
      "recording into **1-second windows** (25 frames) and average each window into one row.\n"
      "*Same as `src/02_build_features.py`; compared with the saved table instead of overwriting it.*",
      [(M, "Go to the project folder."), (C, GO),
       (C, '''import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd'''),
       (M, "**Read a feature file.** The `.stream` header says how many numbers each frame has; the `.stream~` "
           "file holds the numbers."),
       (C, '''def read_stream(path):
    info = ET.parse(path).getroot().find("info")
    dim = int(info.get("dim"))                       # numbers per frame
    if info.get("type") == "FLOAT":
        data = np.fromfile(path + "~", dtype=np.float32)
    else:
        data = np.fromfile(path + "~", dtype=np.float64)
    frames = data.size // dim
    return data[: frames * dim].reshape(frames, dim)     # table: frames x numbers'''),
       (M, "**Read the labels** (bad values become NaN) **and the language**."),
       (C, '''def read_labels(path):
    values = pd.read_csv(path, header=None)[0]
    return pd.to_numeric(values, errors="coerce").to_numpy("float32")


def read_language(folder):
    text = open(folder + "/language.annotation.csv").read()     # e.g. 0.00;904.00;French;1.00
    return text.strip().split(";")[2]'''),
       (M, "**Main loop:** every session, both people, every 1-second window."),
       (C, '''rows = []         # one row per window (averaged)
sequences = []    # the 25 raw frames of each window (for CNN / RNN / Transformer)

for session in sorted(os.listdir("data/noxi")):
    folder = "data/noxi/" + session
    language = read_language(folder)
    for role in ["expert", "novice"]:
        voice = read_stream(folder + "/" + role + ".audio.egemapsv2.stream")
        face = read_stream(folder + "/" + role + ".openface2.stream")
        label = read_labels(folder + "/" + role + ".engagement.annotation.csv")

        n = min(len(voice), len(face), len(label))      # cut all three to the same length
        for w in range(n // 25):
            start, end = w * 25, (w + 1) * 25           # the 25 frames of second w
            engagement = np.nanmean(label[start:end])
            if np.isnan(engagement):                    # no valid label: skip this second
                continue
            row = {}
            voice_mean = np.nanmean(voice[start:end], axis=0)
            face_mean = np.nanmean(face[start:end], axis=0)
            for i in range(len(voice_mean)):
                row["voice_" + str(i)] = float(voice_mean[i])
            for i in range(len(face_mean)):
                row["face_" + str(i)] = float(face_mean[i])
            row["engagement"] = float(engagement)
            row["language"] = language
            row["session"] = session
            row["role"] = role
            rows.append(row)

            frames = np.concatenate([voice[start:end], face[start:end]], axis=1)
            sequences.append(np.nan_to_num(frames).astype(np.float32))
    print(session, language, "done")

df = pd.DataFrame(rows)
seq = np.stack(sequences)
print(df.shape, seq.shape)'''),
       (M, "**Windows per language**"),
       (C, '''print(df["language"].value_counts())'''),
       (M, "**Same as the files saved by the script?** (should print True, True)"),
       (C, '''saved = pd.read_parquet("data/features/noxi_engagement.parquet")
saved_seq = np.load("data/features/noxi_sequences.npy")
print(np.allclose(saved.select_dtypes("number"), df.select_dtypes("number"), equal_nan=True))
print(np.array_equal(saved_seq, seq))'''),
       ])

# ================================================================= 03
build("03_eda.ipynb",
      "# Step 3: Look at the data (EDA)\n*Same as `src/03_eda.py`; charts are shown here instead of saved.*",
      [(M, "Go to the project folder."), (C, GO),
       (C, '''import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

df = pd.read_parquet("data/features/noxi_engagement.parquet")
feature_cols = []
for c in df.columns:
    if c.startswith("voice_") or c.startswith("face_"):
        feature_cols.append(c)
print("windows:", len(df))'''),
       (M, "**How much data per language**, and **average engagement per language**."),
       (C, '''print(df["language"].value_counts())
print(df.groupby("language")["engagement"].mean())'''),
       (M, "**ANOVA:** is the average engagement different between the languages? (p < 0.05 = yes)"),
       (C, '''english = df[df["language"] == "English"]["engagement"]
french = df[df["language"] == "French"]["engagement"]
german = df[df["language"] == "German"]["engagement"]
f_value, p_value = stats.f_oneway(english, french, german)
print("F =", round(f_value, 2), " p =", p_value)'''),
       (M, "**Charts:** distribution, by language, by role."),
       (C, '''sns.histplot(df["engagement"], bins=30, kde=True)
plt.title("Engagement distribution")
plt.show()

sns.boxplot(data=df, x="language", y="engagement")
plt.title("Engagement by language")
plt.show()

sns.boxplot(data=df, x="role", y="engagement")
plt.title("Engagement by role")
plt.show()
print(df.groupby("role")["engagement"].mean())'''),
       (M, "**Which features go with engagement?** Correlation of every feature with engagement."),
       (C, '''corr = df[feature_cols].corrwith(df["engagement"]).abs()
corr = corr.sort_values(ascending=False)
corr.head(10).plot(kind="barh")
plt.title("Top 10 features")
plt.show()'''),
       (M, "**Voice vs face:** average correlation of each group."),
       (C, '''voice_cols = []
face_cols = []
for c in feature_cols:
    if c.startswith("voice_"):
        voice_cols.append(c)
    else:
        face_cols.append(c)
print("voice:", round(corr[voice_cols].mean(), 3))
print("face: ", round(corr[face_cols].mean(), 3))'''),
       (M, "**PCA:** squeeze all features into 2 numbers and colour each window by language."),
       (C, '''X = StandardScaler().fit_transform(df[feature_cols].fillna(0))
points = PCA(n_components=2).fit_transform(X)
sns.scatterplot(x=points[:, 0], y=points[:, 1], hue=df["language"], s=8, alpha=0.5)
plt.title("PCA by language")
plt.show()'''),
       ])

# ================================================================= 05
build("05_cross_lingual.ipynb",
      "# Step 5: Cross-language test\nTrain on one language and test on another, for every pair. Same language: "
      "hold out one session at a time.\n*Same as `src/05_cross_lingual.py`.*",
      [(M, "Go to the project folder."), (C, GO),
       (C, '''import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor

df = pd.read_parquet("data/features/noxi_engagement.parquet")
bookkeeping = ["face_0", "face_1", "face_2", "face_3", "face_4"]
cols = []
for c in df.columns:
    if (c.startswith("voice_") or c.startswith("face_")) and c not in bookkeeping:
        cols.append(c)
languages = ["English", "French", "German"]'''),
       (C, CCC),
       (M, "**Train on one part, test on another, return the CCC.** First scale the features (fitted on the "
           "training part), then a Random Forest."),
       (C, '''def train_and_test(train, test):
    scaler = StandardScaler()
    X_train = scaler.fit_transform(train[cols].fillna(0))
    X_test = scaler.transform(test[cols].fillna(0))
    model = RandomForestRegressor(n_estimators=120, n_jobs=-1, random_state=42)
    model.fit(X_train, train["engagement"])
    return ccc(test["engagement"], model.predict(X_test))'''),
       (M, "**Every pair** (rows = train language, columns = test language)."),
       (C, '''result = pd.DataFrame(index=languages, columns=languages, dtype=float)

for a in languages:
    for b in languages:
        if a == b:
            # same language: hold out one session at a time and average
            data = df[df["language"] == a]
            scores = []
            for s in data["session"].unique():
                scores.append(train_and_test(data[data["session"] != s], data[data["session"] == s]))
            result.loc[a, b] = np.mean(scores)
        else:
            # different language: train on all of a, test on all of b
            result.loc[a, b] = train_and_test(df[df["language"] == a], df[df["language"] == b])
        print(a, "->", b, round(result.loc[a, b], 3))'''),
       (M, "**Within vs cross language** and comparison with the saved result."),
       (C, '''within = np.mean([result.loc[l, l] for l in languages])
cross = np.mean([result.loc[a, b] for a in languages for b in languages if a != b])
print("within:", round(within, 3), " cross:", round(cross, 3), " drop:", round(100 * (within - cross) / within), "%")

saved = pd.read_csv("reports/noxi_crosslingual_ccc.csv", index_col=0)
print("same as saved:", np.allclose(saved.values, result.values))'''),
       ])

# ================================================================= 14
build("14_session_eval.ipynb",
      "# Step 14: ML models + ANN on unseen conversations\nWhole conversations are held out (3 folds). This fixes "
      "the data leakage of a random split.\n*Same as `src/14_session_eval.py`.*",
      [(M, "Go to the project folder."), (C, GO_TF),
       (C, '''import numpy as np
import pandas as pd
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
from xgboost import XGBRegressor'''),
       (C, CCC),
       (M, "**Load the data.** The 5 bookkeeping columns describe the recording, not the person, so they are dropped."),
       (C, LOAD),
       (M, "**The 3 folds.** Each fold holds out 3 whole conversations (one per language)."), (C, FOLDS),
       (M, "**The models.** A new copy of each model is made for every fold."),
       (C, '''def make_models():
    return {
        "LinearRegression": LinearRegression(),
        "RandomForest": RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1),
        "GradientBoosting": HistGradientBoostingRegressor(max_iter=300, random_state=42),
        "XGBoost": XGBRegressor(n_estimators=300, max_depth=6, learning_rate=0.1, subsample=0.8,
                                colsample_bytree=0.8, tree_method="hist", random_state=42, n_jobs=-1),
    }


def make_ann():
    keras.utils.set_random_seed(42)
    model = keras.Sequential([
        layers.Input(shape=(X.shape[1],)),
        layers.Dense(256, activation="relu"),
        layers.Dropout(0.1),
        layers.Dense(128, activation="relu"),
        layers.Dropout(0.1),
        layers.Dense(1),
    ])
    model.compile(optimizer=keras.optimizers.Adam(0.001), loss="mse")
    return model'''),
       (M, "**Train and test on every fold.** The scaler learns only from the training sessions. For the ANN the "
           "scaled values are also limited to -5..5 (a few extreme values break neural networks)."),
       (C, '''scores = {"LinearRegression": [], "RandomForest": [], "GradientBoosting": [], "XGBoost": [], "ANN (MLP)": []}

for test_sessions in folds:
    test = df["session"].isin(test_sessions).to_numpy()
    train = ~test

    scaler = StandardScaler()
    X_train = scaler.fit_transform(X[train])
    X_test = scaler.transform(X[test])

    for name, model in make_models().items():
        model.fit(X_train, y[train])
        scores[name].append(ccc(y[test], model.predict(X_test)))

    ann = make_ann()
    ann.fit(np.clip(X_train, -5, 5), y[train], epochs=30, batch_size=128, verbose=0)
    scores["ANN (MLP)"].append(ccc(y[test], ann.predict(np.clip(X_test, -5, 5), verbose=0).flatten()))
    print("fold done:", test_sessions)'''),
       (M, "**Results** (mean over 3 folds) next to the result saved by the script."),
       (C, '''saved = pd.read_csv("reports/session_flat.csv").groupby("model")["ccc"].mean()
for name in scores:
    print(name.ljust(18), "mean", round(np.mean(scores[name]), 3), " std", round(np.std(scores[name], ddof=1), 3),
          " saved", round(saved[name], 3))'''),
       ])

# ================================================================= 15
build("15_session_sequence.ipynb",
      "# Step 15: CNN, RNN, LSTM, GRU and Transformer\nEvery model reads the **25 frames** of each second. "
      "Same 3 folds as step 14.\n*Same as `src/15_session_sequence.py`. Slow on a CPU (about an hour).*",
      [(M, "Go to the project folder."), (C, GO_TF),
       (C, '''import numpy as np
import pandas as pd
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.preprocessing import StandardScaler'''),
       (C, CCC),
       (M, "**Load the 25-frame windows.** Columns 88-92 are the 5 bookkeeping columns, so they are removed."),
       (C, '''df = pd.read_parquet("data/features/noxi_engagement.parquet", columns=["engagement", "language", "session"])
y = df["engagement"].to_numpy("float32")
X = np.load("data/features/noxi_sequences.npy")
X = np.delete(X, [88, 89, 90, 91, 92], axis=2)
print(X.shape)      # windows x 25 frames x 797 features'''),
       (C, FOLDS),
       (M, "**The same small head** at the end of every model: dropout, Dense(64), one output."),
       (C, '''def head(x):
    x = layers.Dropout(0.1)(x)
    x = layers.Dense(64, activation="relu")(x)
    return layers.Dense(1)(x)'''),
       (M, "**CNN (VGG style):** two blocks of [convolution, convolution, pooling]."),
       (C, '''def cnn():
    inp = layers.Input(shape=(25, 797))
    x = layers.Conv1D(32, 3, padding="same", activation="relu")(inp)
    x = layers.Conv1D(32, 3, padding="same", activation="relu")(x)
    x = layers.MaxPooling1D(2)(x)
    x = layers.Conv1D(64, 3, padding="same", activation="relu")(x)
    x = layers.Conv1D(64, 3, padding="same", activation="relu")(x)
    x = layers.MaxPooling1D(2)(x)
    return keras.Model(inp, head(layers.Flatten()(x)), name="CNN_VGG")'''),
       (M, "**RNN, LSTM, GRU:** each reads the 25 frames one after another (128 units)."),
       (C, '''def rnn():
    inp = layers.Input(shape=(25, 797))
    return keras.Model(inp, head(layers.SimpleRNN(128)(inp)), name="SimpleRNN")


def lstm():
    inp = layers.Input(shape=(25, 797))
    return keras.Model(inp, head(layers.LSTM(128)(inp)), name="LSTM")


def gru():
    inp = layers.Input(shape=(25, 797))
    return keras.Model(inp, head(layers.GRU(128)(inp)), name="GRU")'''),
       (M, "**Positional encoding:** attention does not know the order of the frames, so a learned vector is added "
           "for each of the 25 positions."),
       (C, '''class PositionalEncoding(layers.Layer):
    def build(self, input_shape):
        self.pos = self.add_weight(shape=(25, 64), initializer="random_normal", name="pos")

    def call(self, x):
        return x + self.pos'''),
       (M, "**Transformer:** frames → 64 numbers → add positions → 2 encoder blocks (self-attention + feed-forward, "
           "each with add & normalise) → average over frames → head."),
       (C, '''def encoder_block(x):
    attention = layers.MultiHeadAttention(num_heads=4, key_dim=16, dropout=0.1)(x, x)
    x = layers.LayerNormalization(epsilon=1e-6)(layers.Add()([x, attention]))
    ff = layers.Dense(128, activation="relu")(x)
    ff = layers.Dropout(0.1)(ff)
    ff = layers.Dense(64)(ff)
    return layers.LayerNormalization(epsilon=1e-6)(layers.Add()([x, ff]))


def transformer():
    inp = layers.Input(shape=(25, 797))
    x = layers.Dense(64)(inp)
    x = PositionalEncoding()(x)
    x = encoder_block(x)
    x = encoder_block(x)
    x = layers.GlobalAveragePooling1D()(x)
    return keras.Model(inp, head(x), name="Transformer")'''),
       (M, "**Train every model on every fold.** Scaling learns only from the training frames; values limited to -5..5."),
       (C, '''scores = {"CNN_VGG": [], "SimpleRNN": [], "LSTM": [], "GRU": [], "Transformer": []}

for test_sessions in folds:
    test = df["session"].isin(test_sessions).to_numpy()
    train = ~test

    scaler = StandardScaler().fit(X[train].reshape(-1, 797))
    X_train = np.clip(scaler.transform(X[train].reshape(-1, 797)), -5, 5).reshape(-1, 25, 797).astype("float32")
    X_test = np.clip(scaler.transform(X[test].reshape(-1, 797)), -5, 5).reshape(-1, 25, 797).astype("float32")

    for make_model in [cnn, rnn, lstm, gru, transformer]:
        keras.utils.set_random_seed(42)
        model = make_model()
        model.compile(optimizer=keras.optimizers.Adam(0.001), loss="mse")
        model.fit(X_train, y[train], epochs=20, batch_size=128, verbose=0)
        scores[model.name].append(ccc(y[test], model.predict(X_test, verbose=0).flatten()))
    print("fold done:", test_sessions)'''),
       (C, '''saved = pd.read_csv("reports/session_sequence.csv").groupby("model")["ccc"].mean()
for name in scores:
    print(name.ljust(12), "mean", round(np.mean(scores[name]), 3), " saved", round(saved[name], 3))'''),
       ])

# ================================================================= 16
build("16_autoencoder.ipynb",
      "# Step 16: Autoencoder\nThe autoencoder squeezes 797 features into **32 numbers** and rebuilds them (no labels "
      "needed). Then the 32 numbers are used to predict engagement.\n*Same as `src/16_autoencoder.py`.*",
      [(M, "Go to the project folder."), (C, GO_TF),
       (C, '''import numpy as np
import pandas as pd
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor'''),
       (C, CCC), (C, LOAD), (C, FOLDS),
       (M, "**Autoencoder:** encoder 797 → 256 → 32, decoder 32 → 256 → 797."),
       (C, '''def make_autoencoder():
    inp = layers.Input(shape=(797,))
    h = layers.Dense(256, activation="relu")(inp)
    code = layers.Dense(32, activation="relu")(h)
    h = layers.Dense(256, activation="relu")(code)
    out = layers.Dense(797)(h)
    autoencoder = keras.Model(inp, out)
    encoder = keras.Model(inp, code)
    return autoencoder, encoder'''),
       (M, "**Every fold:** (1) train the autoencoder to rebuild its input, (2) freeze the encoder and train a small "
           "head on the 32 numbers, (3) XGBoost on the same 32 numbers."),
       (C, '''scores = {"Autoencoder + dense head": [], "Autoencoder + XGBoost": []}

for test_sessions in folds:
    test = df["session"].isin(test_sessions).to_numpy()
    train = ~test
    scaler = StandardScaler().fit(X[train])
    X_train = np.clip(scaler.transform(X[train]), -5, 5)
    X_test = np.clip(scaler.transform(X[test]), -5, 5)

    # 1) autoencoder: input = target, no labels
    keras.utils.set_random_seed(42)
    autoencoder, encoder = make_autoencoder()
    autoencoder.compile(optimizer=keras.optimizers.Adam(0.001), loss="mse")
    autoencoder.fit(X_train, X_train, epochs=30, batch_size=128, verbose=0)
    print("reconstruction error:", round(autoencoder.evaluate(X_test, X_test, verbose=0), 3))

    # 2) frozen encoder + small head
    encoder.trainable = False
    inp = layers.Input(shape=(797,))
    x = layers.Dense(64, activation="relu")(encoder(inp))
    x = layers.Dropout(0.1)(x)
    head = keras.Model(inp, layers.Dense(1)(x))
    head.compile(optimizer=keras.optimizers.Adam(0.001), loss="mse")
    head.fit(X_train, y[train], epochs=30, batch_size=128, verbose=0)
    scores["Autoencoder + dense head"].append(ccc(y[test], head.predict(X_test, verbose=0).flatten()))

    # 3) XGBoost on the 32 numbers
    code_train = encoder.predict(X_train, verbose=0)
    code_test = encoder.predict(X_test, verbose=0)
    xgb = XGBRegressor(n_estimators=300, max_depth=6, learning_rate=0.1, subsample=0.8,
                       colsample_bytree=0.8, tree_method="hist", random_state=42, n_jobs=-1)
    xgb.fit(code_train, y[train])
    scores["Autoencoder + XGBoost"].append(ccc(y[test], xgb.predict(code_test)))'''),
       (C, '''saved = pd.read_csv("reports/autoencoder_results.csv").groupby("model")["ccc"].mean()
for name in scores:
    print(name.ljust(26), "mean", round(np.mean(scores[name]), 3), " saved", round(saved[name], 3))'''),
       ])

# ================================================================= 17
build("17_ablation.ipynb",
      "# Step 17: Voice vs face\nThe same XGBoost model with **voice only**, **face only** and **both**.\n"
      "*Same as `src/17_ablation.py`.*",
      [(M, "Go to the project folder."), (C, GO),
       (C, '''import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor'''),
       (C, CCC),
       (M, "**Train on one part, test on another, using only the given columns.**"),
       (C, '''def train_and_test(train, test, cols):
    scaler = StandardScaler()
    X_train = scaler.fit_transform(train[cols].fillna(0))
    X_test = scaler.transform(test[cols].fillna(0))
    model = XGBRegressor(n_estimators=300, max_depth=6, learning_rate=0.1, subsample=0.8,
                         colsample_bytree=0.8, tree_method="hist", random_state=42, n_jobs=-1)
    model.fit(X_train, train["engagement"])
    return ccc(test["engagement"], model.predict(X_test))'''),
       (C, '''df = pd.read_parquet("data/features/noxi_engagement.parquet")
bookkeeping = ["face_0", "face_1", "face_2", "face_3", "face_4"]
voice, face = [], []
for c in df.columns:
    if c.startswith("voice_"):
        voice.append(c)
    elif c.startswith("face_") and c not in bookkeeping:
        face.append(c)
inputs = {"voice": voice, "face": face, "both": voice + face}
languages = ["English", "French", "German"]
print(len(voice), "voice and", len(face), "face features")'''),
       (C, FOLDS),
       (M, "**For each input:** unseen conversations (3 folds), within each language, and across languages."),
       (C, '''for name, cols in inputs.items():
    unseen = []
    for test_sessions in folds:
        test = df["session"].isin(test_sessions)
        unseen.append(train_and_test(df[~test], df[test], cols))

    within = []
    for l in languages:
        data = df[df["language"] == l]
        for s in data["session"].unique():
            within.append(train_and_test(data[data["session"] != s], data[data["session"] == s], cols))

    cross = []
    for a in languages:
        for b in languages:
            if a != b:
                cross.append(train_and_test(df[df["language"] == a], df[df["language"] == b], cols))

    drop = 100 * (np.mean(within) - np.mean(cross)) / np.mean(within)
    print(name.ljust(6), "unseen", round(np.mean(unseen), 3), "| within", round(np.mean(within), 3),
          "| cross", round(np.mean(cross), 3), "| drop", round(drop), "%")'''),
       (M, "**The result saved by the script**, for comparison."),
       (C, '''print(pd.read_csv("reports/ablation_results.csv")[["modality", "session_ccc", "within_ccc", "cross_ccc", "drop_pct"]].round(3))'''),
       ])

# ================================================================= 19
build("19_pretrained_features.ipynb",
      "# Step 19: Pretrained Transformer features\nThe NoXi zips also contain features made by six big pretrained "
      "Transformers (text: XLM-RoBERTa; audio: w2v-BERT 2.0; video: CLIP, DINOv2, Swin, VideoMAE). We average them over "
      "the same 1-second windows as step 2.\n*Same as `src/19_pretrained_features.py`; compared with the saved files. "
      "Slow: it reads the 14 GB zip.*",
      [(M, "Go to the project folder."), (C, GO),
       (C, '''import zipfile
import warnings
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd
warnings.filterwarnings("ignore")      # "mean of empty slice" warnings

EMBEDDINGS = {"xlm_roberta": "audio.xlm_roberta_embeddings", "w2vbert2": "audio.w2vbert2_embeddings",
              "clip": "clip", "dino": "dino", "swin": "swin", "videomae": "videomae"}'''),
       (M, "**Read a feature file** from the folder (like step 2) **or directly from the zip**."),
       (C, '''def read_stream(path):
    dim = int(ET.parse(path).getroot().find("info").get("dim"))
    data = np.fromfile(path + "~", dtype=np.float32)
    return data[: data.size // dim * dim].reshape(-1, dim)


def read_from_zip(z, name):
    dim = int(ET.fromstring(z.read(name)).find("info").get("dim"))
    data = np.frombuffer(z.read(name + "~"), dtype=np.float32)
    return data[: data.size // dim * dim].reshape(-1, dim)'''),
       (M, "Session 027 is in its own zip; all others are in train.zip."),
       (C, '''train_zip = zipfile.ZipFile("C:/Users/SHUBHAM KUMAR/Downloads/train.zip")
zip_027 = zipfile.ZipFile("C:/Users/SHUBHAM KUMAR/Downloads/027.zip")'''),
       (M, "**Main loop:** find the same windows as step 2, then average every embedding over those windows."),
       (C, '''result = {}
for key in EMBEDDINGS:
    result[key] = []

for session in sorted(os.listdir("data/noxi")):
    folder = "data/noxi/" + session
    z = zip_027 if session == "027" else train_zip
    for role in ["expert", "novice"]:
        # the windows kept in step 2
        voice = read_stream(folder + "/" + role + ".audio.egemapsv2.stream")
        face = read_stream(folder + "/" + role + ".openface2.stream")
        label = pd.read_csv(folder + "/" + role + ".engagement.annotation.csv", header=None)[0]
        label = pd.to_numeric(label, errors="coerce").to_numpy("float32")
        n = min(len(voice), len(face), len(label))
        keep = []
        for w in range(n // 25):
            if not np.isnan(np.nanmean(label[w * 25:(w + 1) * 25])):
                keep.append(w)

        # average each embedding over the same windows
        for key, stream in EMBEDDINGS.items():
            E = read_from_zip(z, session + "/" + role + "." + stream + ".stream")
            windows = []
            for w in keep:
                if w * 25 < len(E):
                    windows.append(np.nanmean(E[w * 25:(w + 1) * 25], axis=0))
                else:
                    windows.append(np.full(E.shape[1], np.nan, np.float32))    # embedding is shorter
            result[key].append(np.nan_to_num(np.stack(windows)).astype(np.float32))
    print(session, "done")'''),
       (M, "**Same as the saved files?** (True for all six)"),
       (C, '''for key in EMBEDDINGS:
    new = np.concatenate(result[key])
    saved = np.load("data/features/pretrained_" + key + ".npy")
    print(key.ljust(12), new.shape, np.array_equal(new, saved))'''),
       ])

# ================================================================= 20
build("20_pretrained_transformers.ipynb",
      "# Step 20: Pretrained Transformers (frozen) + trained head\nThe pretrained Transformer is **not changed**; only a "
      "small model on top of its features is trained: XGBoost or a dense network.\n*Same as "
      "`src/20_pretrained_transformers.py`. Slow on a CPU (about 45 minutes).*",
      [(M, "Go to the project folder."), (C, GO_TF),
       (C, '''import numpy as np
import pandas as pd
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor

SETS = {   # name -> feature files
    "XLM-RoBERTa": ["xlm_roberta"],
    "w2v-BERT 2.0": ["w2vbert2"],
    "CLIP": ["clip"],
    "DINOv2": ["dino"],
    "Swin": ["swin"],
    "VideoMAE": ["videomae"],
    "w2v-BERT 2.0 + VideoMAE": ["w2vbert2", "videomae"],
}'''),
       (C, CCC),
       (M, "**Head 1: XGBoost.**  **Head 2: dense network** (256-128, dropout 0.1). Both: scale on training rows, "
           "train, return the CCC on the test rows."),
       (C, '''def xgb_score(train, test):
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X[train])
    X_test = scaler.transform(X[test])
    model = XGBRegressor(n_estimators=300, max_depth=6, learning_rate=0.1, subsample=0.8,
                         colsample_bytree=0.8, tree_method="hist", random_state=42, n_jobs=-1)
    model.fit(X_train, y[train])
    return ccc(y[test], model.predict(X_test))


def dense_score(train, test):
    keras.utils.set_random_seed(42)
    model = keras.Sequential([
        layers.Input(shape=(X.shape[1],)),
        layers.Dense(256, activation="relu"),
        layers.Dropout(0.1),
        layers.Dense(128, activation="relu"),
        layers.Dropout(0.1),
        layers.Dense(1),
    ])
    model.compile(optimizer=keras.optimizers.Adam(0.001), loss="mse")
    scaler = StandardScaler().fit(X[train])
    model.fit(np.clip(scaler.transform(X[train]), -5, 5), y[train], epochs=30, batch_size=128, verbose=0)
    return ccc(y[test], model.predict(np.clip(scaler.transform(X[test]), -5, 5), verbose=0).flatten())'''),
       (C, '''df = pd.read_parquet("data/features/noxi_engagement.parquet", columns=["engagement", "language", "session"])
y = df["engagement"].to_numpy("float32")
language = df["language"].to_numpy()
session = df["session"].to_numpy()
languages = ["English", "French", "German"]'''),
       (C, FOLDS),
       (M, "**For each pretrained model:** 3 folds with both heads, then within-language and cross-language (XGBoost)."),
       (C, '''for name, files in SETS.items():
    parts = []
    for f in files:
        parts.append(np.load("data/features/pretrained_" + f + ".npy"))
    X = np.concatenate(parts, axis=1)

    xgb_scores, dense_scores = [], []
    for test_sessions in folds:
        test = np.isin(session, test_sessions)
        xgb_scores.append(xgb_score(~test, test))
        dense_scores.append(dense_score(~test, test))

    within = []
    for l in languages:
        for s in sorted(df[df["language"] == l]["session"].unique()):
            within.append(xgb_score((language == l) & (session != s), session == s))
    cross = []
    for a in languages:
        for b in languages:
            if a != b:
                cross.append(xgb_score(language == a, language == b))

    drop = 100 * (np.mean(within) - np.mean(cross)) / np.mean(within)
    print(name.ljust(24), "XGB", round(np.mean(xgb_scores), 3), "| dense", round(np.mean(dense_scores), 3),
          "| drop", round(drop), "%")'''),
       (M, "**The result saved by the script**, for comparison."),
       (C, '''print(pd.read_csv("reports/pretrained_results.csv")[["model", "xgb_ccc", "dense_ccc", "drop_pct"]].round(3))'''),
       ])

# ================================================================= 24
build("24_fusion.ipynb",
      "# Step 24: Fusion - the best model\nVoice (eGeMAPS) + w2v-BERT 2.0 speech + VideoMAE video features together, "
      "with and without **past context** (mean of the last 5 s and 10 s). Two heads: Gradient Boosting and a dense "
      "network. Predictions are also **smoothed** over the last 5 s.\n*Same as `src/24_fusion.py`. Slow (over an hour).*",
      [(M, "Go to the project folder."), (C, GO_TF),
       (C, '''import numpy as np
import pandas as pd
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import HistGradientBoostingRegressor'''),
       (C, CCC),
       (M, "**Past mean:** for each row, the mean of the same speaker's last k seconds (only the past, so it would "
           "also work live). Used for **context** (features) and **smoothing** (predictions)."),
       (C, PAST_MEAN),
       (C, '''df = pd.read_parquet("data/features/noxi_engagement.parquet")
voice = []
for c in df.columns:
    if c.startswith("voice_"):
        voice.append(c)
y = df["engagement"].to_numpy("float32")
speaker = (df["session"] + "_" + df["role"]).to_numpy()
language = df["language"].to_numpy()
session = df["session"].to_numpy()
languages = ["English", "French", "German"]

fused = np.hstack([df[voice].fillna(0).to_numpy("float32"),
                   np.load("data/features/pretrained_w2vbert2.npy"),
                   np.load("data/features/pretrained_videomae.npy")])
with_context = np.hstack([fused, past_mean(fused, speaker, 5).astype("float32"), past_mean(fused, speaker, 10).astype("float32")])
print(fused.shape[1], "features, with context:", with_context.shape[1])'''),
       (C, FOLDS),
       (M, "**The two heads.**"),
       (C, '''def gb_predict(X, train, test):
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X[train])
    X_test = scaler.transform(X[test])
    model = HistGradientBoostingRegressor(max_iter=300, random_state=42)
    model.fit(X_train, y[train])
    return model.predict(X_test)


def dense_predict(X, train, test):
    keras.utils.set_random_seed(42)
    model = keras.Sequential([
        layers.Input(shape=(X.shape[1],)),
        layers.Dense(256, activation="relu"),
        layers.Dropout(0.1),
        layers.Dense(128, activation="relu"),
        layers.Dropout(0.1),
        layers.Dense(1),
    ])
    model.compile(optimizer=keras.optimizers.Adam(0.001), loss="mse")
    scaler = StandardScaler().fit(X[train])
    model.fit(np.clip(scaler.transform(X[train]), -5, 5), y[train], epochs=30, batch_size=128, verbose=0)
    return model.predict(np.clip(scaler.transform(X[test]), -5, 5), verbose=0).flatten()'''),
       (M, "**3 folds for every head and input** (raw and smoothed predictions)."),
       (C, '''for head_name, predict in [("Gradient Boosting", gb_predict), ("dense head", dense_predict)]:
    for input_name, X in [("fusion, 1 s", fused), ("fusion + context", with_context)]:
        raw, smoothed = [], []
        for test_sessions in folds:
            test = np.isin(session, test_sessions)
            pred = predict(X, ~test, test)
            raw.append(ccc(y[test], pred))
            smooth_pred = past_mean(pred.reshape(-1, 1), speaker[test], 5).flatten()
            smoothed.append(ccc(y[test], smooth_pred))
        print(head_name.ljust(18), input_name.ljust(16), round(np.mean(raw), 3), "+-", round(np.std(raw, ddof=1), 3),
              "| smoothed", round(np.mean(smoothed), 3))'''),
       (M, "**Cross-language test of the best model** (Gradient Boosting, fusion + context)."),
       (C, '''within = []
for l in languages:
    for s in sorted(df[df["language"] == l]["session"].unique()):
        within.append(ccc(y[session == s], gb_predict(with_context, (language == l) & (session != s), session == s)))
cross = []
for a in languages:
    for b in languages:
        if a != b:
            cross.append(ccc(y[language == b], gb_predict(with_context, language == a, language == b)))
drop = 100 * (np.mean(within) - np.mean(cross)) / np.mean(within)
print("within", round(np.mean(within), 3), "| cross", round(np.mean(cross), 3), "| drop", round(drop), "%")'''),
       (M, "**The result saved by the script**, for comparison."),
       (C, '''print(pd.read_csv("reports/fusion_results.csv")[["model", "input", "ccc", "smooth_ccc", "drop_pct"]].round(3))'''),
       ])

# ================================================================= 26
build("26_significance.ipynb",
      "# Step 26: Is the best model really better?\nWe compare models **person by person**: every speaker (18) gets "
      "predictions from a model that never saw their conversation. Then a **Wilcoxon test**, a **bootstrap 95% "
      "interval** and **Holm correction**.\n*Same as `src/26_significance.py`.*",
      [(M, "Go to the project folder."), (C, GO),
       (C, '''import numpy as np
import pandas as pd
from scipy.stats import wilcoxon
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import HistGradientBoostingRegressor'''),
       (C, CCC), (C, PAST_MEAN),
       (C, '''df = pd.read_parquet("data/features/noxi_engagement.parquet")
bookkeeping = ["face_0", "face_1", "face_2", "face_3", "face_4"]
cols, voice = [], []
for c in df.columns:
    if (c.startswith("voice_") or c.startswith("face_")) and c not in bookkeeping:
        cols.append(c)
    if c.startswith("voice_"):
        voice.append(c)
y = df["engagement"].to_numpy("float32")
speaker = (df["session"] + "_" + df["role"]).to_numpy()
session = df["session"].to_numpy()'''),
       (C, FOLDS),
       (M, "**The three models:** A = baseline, B = + context, C = best (fusion + context)."),
       (C, '''own = df[cols].fillna(0).to_numpy("float32")
fused = np.hstack([df[voice].fillna(0).to_numpy("float32"),
                   np.load("data/features/pretrained_w2vbert2.npy"),
                   np.load("data/features/pretrained_videomae.npy")])
inputs = {
    "A": own,
    "B": np.hstack([own, past_mean(own, speaker, 5).astype("float32"), past_mean(own, speaker, 10).astype("float32")]),
    "C": np.hstack([fused, past_mean(fused, speaker, 5).astype("float32"), past_mean(fused, speaker, 10).astype("float32")]),
}'''),
       (M, "**Predict every row once**, with a model that did not see its conversation."),
       (C, '''predictions = {}
for name, X in inputs.items():
    pred = np.zeros(len(y), dtype="float32")
    for test_sessions in folds:
        test = np.isin(session, test_sessions)
        scaler = StandardScaler()
        X_train = scaler.fit_transform(X[~test])
        model = HistGradientBoostingRegressor(max_iter=300, random_state=42)
        model.fit(X_train, y[~test])
        pred[test] = model.predict(scaler.transform(X[test]))
    predictions[name] = pred
    print(name, "done")'''),
       (M, "**CCC for each of the 18 speakers**, and the average per conversation (9)."),
       (C, '''per_speaker = pd.DataFrame(index=pd.unique(speaker))
for name in predictions:
    values = []
    for s in per_speaker.index:
        values.append(ccc(y[speaker == s], predictions[name][speaker == s]))
    per_speaker[name] = values

conversation = per_speaker.index.str.split("_").str[0]        # "001_expert" -> "001"
per_conversation = per_speaker.groupby(conversation).mean()
per_speaker.round(3)'''),
       (M, "**The tests.** For each pair and level: average difference, 95% bootstrap interval, how many improved, Wilcoxon p."),
       (C, '''rng = np.random.default_rng(42)
pairs = [("C", "A"), ("B", "A"), ("C", "B")]
results = []
for a, b in pairs:
    for level, table in [("speaker", per_speaker), ("conversation", per_conversation)]:
        diff = (table[a] - table[b]).to_numpy()
        boot = rng.choice(diff, (10000, len(diff))).mean(axis=1)    # 10,000 resamples
        results.append([a + " vs " + b, level, diff.mean(), np.percentile(boot, 2.5), np.percentile(boot, 97.5),
                        (diff > 0).sum(), len(diff), wilcoxon(diff).pvalue])
res = pd.DataFrame(results, columns=["pair", "level", "difference", "ci_low", "ci_high", "better", "out_of", "p"])'''),
       (M, "**Holm correction** (3 tests per level): sort the p-values; multiply the smallest by 3, the next by 2, the "
           "last by 1 (never going down)."),
       (C, '''res["p_holm"] = 0.0
for level in ["speaker", "conversation"]:
    rows = res[res["level"] == level].sort_values("p").index
    running = 0
    for rank, i in enumerate(rows):
        running = max(running, min(1, (3 - rank) * res.loc[i, "p"]))
        res.loc[i, "p_holm"] = running
res["significant"] = res["p_holm"] < 0.05
res.round(4)'''),
       (M, "**The result saved by the script**, for comparison."),
       (C, '''print(pd.read_csv("reports/significance_results.csv")[["comparison", "level", "mean_diff", "ci_low", "ci_high", "p_holm"]].round(4))'''),
       ])
print("done")
