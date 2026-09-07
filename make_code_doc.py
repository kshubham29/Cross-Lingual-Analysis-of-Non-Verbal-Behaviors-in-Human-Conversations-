"""Generate a complete line-by-line code explanation Word document."""
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING

NAVY = RGBColor(0x1E, 0x2C, 0x3F)
TEAL = RGBColor(0x02, 0x80, 0x90)
CODEC = RGBColor(0x0A, 0x3A, 0x4A)
GREY = RGBColor(0x55, 0x66, 0x70)

d = Document()
n = d.styles["Normal"]; n.font.name = "Calibri"; n.font.size = Pt(10.5)
n.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
n.paragraph_format.space_after = Pt(4)


def H(t, l=1):
    h = d.add_heading(t, level=l)
    for r in h.runs:
        r.font.color.rgb = NAVY


def intro(t):
    p = d.add_paragraph()
    r = p.add_run(t); r.italic = True; r.font.color.rgb = GREY; r.font.size = Pt(10.5)


def line(c, what, why=None):
    """One code line + what it does (+ optional why)."""
    p = d.add_paragraph()
    p.paragraph_format.space_after = Pt(1)
    r = p.add_run(c); r.font.name = "Consolas"; r.font.size = Pt(9.5)
    r.bold = True; r.font.color.rgb = CODEC
    q = d.add_paragraph()
    q.paragraph_format.left_indent = Pt(18)
    q.paragraph_format.space_after = Pt(8) if not why else Pt(1)
    q.add_run(what).font.size = Pt(10.5)
    if why:
        w = d.add_paragraph()
        w.paragraph_format.left_indent = Pt(18)
        w.paragraph_format.space_after = Pt(8)
        a = w.add_run("Why: "); a.bold = True; a.font.color.rgb = TEAL; a.font.size = Pt(10)
        b = w.add_run(why); b.font.size = Pt(10)


# ---------------- TITLE ----------------
for _ in range(3):
    d.add_paragraph()
p = d.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("Complete Code Explanation"); r.bold = True; r.font.size = Pt(26); r.font.color.rgb = NAVY
s = d.add_paragraph(); s.alignment = WD_ALIGN_PARAGRAPH.CENTER
rs = s.add_run("Every line, what it does and why\nCross-Lingual Engagement Prediction (NoXi)")
rs.italic = True; rs.font.size = Pt(13); rs.font.color.rgb = TEAL
d.add_page_break()

H("How to use this document")
d.add_paragraph("The project has 7 scripts, run in order. Each one below is explained line by line: "
                "the code is in blue, what it does is underneath, and 'Why' explains the reason.")
d.add_paragraph("Key idea: you do not write the mathematics yourself. Libraries do the work - pandas "
                "handles tables, scikit-learn provides the classic models, TensorFlow/Keras provides "
                "the neural network. Your code simply instructs them.")

# ================= 01 =================
H("Script 01 - extract_data.py  (get the data ready)")
intro("Purpose: the NoXi zips are ~1.2 GB each because of raw videos. This keeps only the small "
      "files we actually use.")
line("import os, sys, glob, zipfile",
     "Imports tools for file paths, command-line arguments, finding files, and reading zip archives.")
line('DEST = os.path.join("data", "noxi")',
     "Sets the destination folder where extracted files are saved.")
line('KEEP_SUFFIXES = (".audio.egemapsv2.stream", ".openface2.stream", ".engagement.annotation.csv", "language.annotation.csv")',
     "A list of the only file types we keep: voice features, face features, engagement labels and the language tag.",
     "Everything else (videos, large embeddings) is ignored, saving about 90% of the space.")
line("def wanted(name): return name.endswith(KEEP_SUFFIXES)",
     "A small helper that returns True if a file is one we want to keep.")
line("with zipfile.ZipFile(zip_path) as z:",
     "Opens one downloaded NoXi zip file.")
line("for member in z.namelist():",
     "Loops over every file inside that zip.")
line("z.extract(member, DEST)",
     "Extracts a wanted file into data/noxi/.")

# ================= 02 =================
H("Script 02 - build_features.py  (build the feature table)")
intro("Purpose: turn the raw NoXi feature streams into one table where each row is 1 second of "
      "behaviour with its engagement value.")
line("WINDOW = 25",
     "Sets the window size to 25 frames.",
     "NoXi data is recorded at 25 frames per second, so 25 frames = exactly 1 second.")
line("info = ET.parse(header_path).getroot().find('info')",
     "Reads the small XML header file (.stream) that describes the data.")
line("dim = int(info.get('dim'))",
     "Gets how many feature values there are per frame (88 for voice, 714 for face).")
line("data = np.fromfile(header_path + '~', dtype=dtype)",
     "Reads the actual numbers from the binary .stream~ file.",
     "NoXi stores features as raw binary for speed; numpy reads them directly.")
line("return data[: n * dim].reshape(n, dim)",
     "Reshapes the flat list of numbers into a table of (frames x features).")
line("pd.to_numeric(s, errors='coerce')",
     "Reads the engagement labels, turning any bad/missing values into NaN.",
     "One session had an invalid value; this stops it crashing the script.")
line("open(p).read().strip().split(';')[2]",
     "Reads the language of the conversation from language.annotation.csv.")
line("for role in ('expert', 'novice'):",
     "Loops over both people in the conversation.",
     "Each NoXi session has an expert and a novice, and both have their own features and engagement.")
line("T = min(len(ege), len(y), len(face))",
     "Finds the shortest length among voice, face and labels, then trims all three to match.",
     "The three streams can differ by a frame or two; they must be the same length to line up.")
line("for w in range(T // WINDOW):",
     "Loops over each 1-second window in the session.")
line("eng = float(np.nanmean(y[s]))",
     "Averages the engagement values inside that window - this becomes the row's label.")
line("feat = {f'voice_{i}': float(v) for i, v in enumerate(np.nanmean(ege[s], 0))}",
     "Averages the voice features over the window and names them voice_0 ... voice_87.")
line("feat.update(engagement=eng, language=lang, session=sess, role=role)",
     "Adds the label and the tags (language, session, role) to the row.")
line("df.to_parquet(OUT, index=False)",
     "Saves the finished table (17,174 rows x 806 columns).",
     "Parquet is a compact, fast file format for large tables.")

# ================= 03 =================
H("Script 03 - eda.py  (explore the data before modelling)")
intro("Purpose: understand the data before training anything - balance, distribution, differences "
      "between languages, and which features matter.")
line("df = pd.read_parquet(FEATURES)",
     "Loads the feature table built in step 2.")
line("feat_cols = [c for c in df.columns if c.startswith(('voice_', 'face_'))]",
     "Selects only the 802 feature columns (ignoring engagement, language, session, role).")
line("missing = df[feat_cols].isna().sum().sum()",
     "Counts missing values across all features.",
     "Confirms the data is clean before modelling (ours has 0 missing).")
line("summary = df.groupby('language')['engagement'].agg(['count','mean','std','min','max'])",
     "Summarises engagement per language: how many rows, average, spread, minimum and maximum.")
line("f_stat, p_val = stats.f_oneway(*groups)",
     "Runs an ANOVA statistical test comparing engagement across the three languages.",
     "It tells us whether the differences between languages are statistically real (p < 0.05) "
     "rather than random chance. Ours gave p < 0.001.")
line("sns.histplot(df['engagement'], bins=30, kde=True)",
     "Draws the engagement distribution histogram.",
     "Shows most engagement is medium (~0.5), with few extremes.")
line("sns.boxplot(data=df, x='language', y='engagement')",
     "Draws a boxplot comparing engagement across the three languages.")
line("sns.boxplot(data=df, x='role', y='engagement')",
     "Compares engagement between experts and novices.",
     "Revealed experts are more engaged (0.66) than novices (0.51).")
line("corr = df[feat_cols].corrwith(df['engagement']).abs().sort_values(ascending=False)",
     "Measures how strongly each feature relates to engagement, strongest first.")
line("voice_corr = ...corrwith(...).abs().mean()   /   face_corr = ...",
     "Compares the average correlation of voice features vs face features with engagement.",
     "Showed voice (0.39) relates to engagement more than face (0.19) - a useful finding.")
line("pcs = PCA(n_components=2).fit_transform(StandardScaler().fit_transform(...))",
     "Compresses the 802 features down to 2 dimensions so they can be plotted.",
     "Lets us see visually whether the languages form separate clusters.")
line("plt.savefig(...)",
     "Saves each chart as a PNG image for the report and presentation.")

# ================= 04 =================
H("Script 04 - baselines.py  (classic machine-learning models)")
intro("Purpose: train simple, standard models to get a reference score that the deep learning "
      "model must beat.")
line("def ccc(y_true, y_pred): ...",
     "Defines the CCC (Concordance Correlation Coefficient) scoring function.",
     "Engagement is a continuous number, so we cannot use accuracy. CCC measures how closely "
     "predictions match the true values, both in trend and in actual value. 1.0 is perfect.")
line("X = df[feat_cols].fillna(0).to_numpy('float32')",
     "X is the input: the 802 face and voice features. Any blanks become 0.")
line("y = df['engagement'].to_numpy('float32')",
     "y is the target we predict: the engagement value.")
line("Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42)",
     "Splits the data: 80% to train the models, 20% held back to test them.",
     "Testing on unseen data is the only honest way to measure performance. random_state=42 "
     "makes the split reproducible.")
line("models = {'LinearRegression': ..., 'RandomForest': ..., 'SVR': ...}",
     "The three baseline models.",
     "They represent three different families - linear, tree-based and kernel-based - so we can "
     "see which type of approach suits our data best.")
line("pipe = make_pipeline(StandardScaler(), m)",
     "Chains two steps: first scale all features to a similar range, then run the model.",
     "Features are on very different scales (pitch in hundreds, probabilities 0-1). Without "
     "scaling, models like SVR are dominated by the large-valued features.")
line("if name == 'SVR' and len(Xtr) > 4000: idx = ...choice(4000)",
     "Trains SVR on a random 4,000-row sample instead of all rows.",
     "SVR scales very poorly with data size - on all 17,000 rows it took many minutes. Sampling "
     "keeps it fast with almost no loss in score.")
line("pipe.fit(Xtr, ytr)",
     "Trains the model on the training data.")
line("pred = pipe.predict(Xte)",
     "Makes predictions on the unseen test data.")
line("ccc(yte, pred), r2_score(yte, pred), mean_absolute_error(yte, pred)",
     "Scores the predictions with CCC, R2 and mean absolute error.",
     "R2 below 0 means the model is worse than simply predicting the average - which is what "
     "happened to Linear Regression (-3.4), showing the data is not linear.")

# ================= 05 =================
H("Script 05 - cross_lingual.py  (the main experiment)")
intro("Purpose: answer the research question - does an engagement model trained on one language "
      "work on another?")
line("langs = sorted(df['language'].unique())",
     "Gets the list of languages: English, French, German.")
line("mat = pd.DataFrame(index=langs, columns=langs, dtype=float)",
     "Creates an empty 3x3 table to hold the results.")
line("for a, b in itertools.product(langs, langs):",
     "Loops over every pair of languages: train on 'a', test on 'b'.",
     "This produces all 9 combinations that fill the matrix.")
line("if a == b:",
     "Checks whether we are training and testing on the SAME language.")
line("for s in df.loc[df.language == a, 'session'].unique():",
     "For the same-language case, loops over each conversation to leave one out.",
     "If we trained and tested on the same conversation the score would be inflated. Leaving a "
     "whole session out makes the diagonal an honest number.")
line("tr = df[(df.language == a) & (df.session != s)]  /  te = df[... == s]",
     "Trains on all sessions except one, and tests on the held-out session.")
line("mat.loc[a, b] = fit_score(df[df.language == a], df[df.language == b], cols)",
     "For different languages: trains on all of language A and tests on all of language B.",
     "This is the actual cross-lingual transfer measurement.")
line("RandomForestRegressor(n_estimators=120, n_jobs=-1, random_state=42)",
     "The model used for this experiment - Random Forest with 120 trees.",
     "Random Forest was our best baseline, so it gives the fairest picture of transfer. "
     "n_jobs=-1 uses all CPU cores to speed it up.")
line("diag = np.mean([mat.loc[l, l] for l in langs])",
     "Averages the diagonal - the within-language scores (0.55).")
line("off = np.mean([mat.loc[a, b] for a in langs for b in langs if a != b])",
     "Averages the off-diagonal - the cross-language scores (0.39).",
     "The gap between these two numbers (0.55 vs 0.39) is our main finding: engagement is "
     "partly language-specific.")
line("mat.to_csv('reports/noxi_crosslingual_ccc.csv')",
     "Saves the result matrix.")

# ================= 06 =================
H("Script 06 - deep_learning.py  (the ANN, TensorFlow / Keras)")
intro("Purpose: build and train an Artificial Neural Network to predict engagement, and compare "
      "it with the Random Forest baseline.")
line("os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'",
     "Hides TensorFlow's noisy startup messages.",
     "Must be set before importing TensorFlow, otherwise the warnings still appear.")
line("from tensorflow import keras;  from tensorflow.keras import layers",
     "Imports TensorFlow/Keras - the deep learning library used to build the network.")
line("keras.utils.set_random_seed(42)",
     "Fixes the random seed.",
     "Neural networks start with random weights; fixing the seed makes results reproducible.")
line("scaler = StandardScaler().fit(Xtr);  Xtr = scaler.transform(Xtr)",
     "Scales the features to have mean 0 and standard deviation 1.",
     "Neural networks train much faster and more stably on scaled inputs.")
line("rf = RandomForestRegressor(...).fit(Xtr, ytr)",
     "Also trains a Random Forest on the same data.",
     "Gives a direct, fair comparison between the classic model and the neural network.")
line("model = keras.Sequential([...])",
     "Defines the neural network as a stack of layers.")
line("layers.Input(shape=(802,))",
     "The input layer - accepts the 802 features of one window.")
line("layers.Dense(256, activation='relu')",
     "A hidden layer of 256 neurons using the ReLU activation function.",
     "ReLU keeps positive values and turns negatives to zero. Without an activation function "
     "the network could only learn straight lines; ReLU lets it learn complex, curved patterns.")
line("layers.Dropout(0.3)",
     "Randomly switches off 30% of the neurons during training.",
     "This prevents overfitting - it stops the network memorising the training data and forces "
     "it to learn patterns that generalise. (Our tuning later found 0.1 works even better.)")
line("layers.Dense(128, activation='relu')",
     "A second hidden layer of 128 neurons.",
     "Decreasing layer sizes let the network build from many simple patterns to fewer, higher-level ones.")
line("layers.Dense(1)",
     "The output layer - a single neuron producing one number, the predicted engagement.",
     "No activation here because we want a raw continuous value (regression), not a probability.")
line("model.compile(optimizer=keras.optimizers.Adam(learning_rate=1e-3), loss='mse')",
     "Sets the optimizer and the loss function.",
     "Adam is the algorithm that adjusts the network's weights to reduce error - it is fast and "
     "stable. MSE (mean squared error) measures how far predictions are from the truth.")
line("model.fit(Xtr, ytr, epochs=20, batch_size=64, verbose=0)",
     "Trains the network.",
     "Keras runs the whole training loop internally: it makes predictions, measures the error, "
     "performs backpropagation to work out how each weight should change, and updates them. "
     "One epoch = one full pass over the data; batch_size=64 means it learns from 64 rows at a time.")
line("p = model.predict(Xte, verbose=0).flatten()",
     "Makes predictions on the test set.")
line("model.save('reports/noxi_mlp.keras')",
     "Saves the trained network to a file.",
     "So the model can be reused later without retraining - for example in a demo application.")

# ================= 07 =================
H("Script 07 - tuning.py  (hyperparameter tuning)")
intro("Purpose: find the best settings for the neural network instead of guessing them.")
line("X_tmp, X_te, y_tmp, y_te = train_test_split(X, y, test_size=0.2)",
     "First split: holds back 20% as the final TEST set.")
line("X_tr, X_va, y_tr, y_va = train_test_split(X_tmp, y_tmp, test_size=0.25)",
     "Second split: divides the rest into 60% train and 20% validation.",
     "Three-way splitting is essential. Configurations are compared on VALIDATION, and only the "
     "winner is scored on TEST. If we chose the best setting using the test set, the final score "
     "would be dishonestly high.")
line("DROPOUTS = [0.1, 0.3, 0.5]",
     "The dropout values to try.")
line("LRS = [1e-3, 5e-4]",
     "The learning rates to try.",
     "The learning rate controls how big each improvement step is - too big overshoots, too small learns slowly.")
line("HIDDENS = [(256, 128), (512, 256)]",
     "The two network architectures to compare (this is 'architecture refinement').")
line("for drop, lr, hid in itertools.product(DROPOUTS, LRS, HIDDENS):",
     "Grid search - trains a model for every combination (3 x 2 x 2 = 12 configurations).")
line("val = ccc(y_va, model.predict(X_va).flatten())",
     "Scores each configuration on the validation set.")
line("keras.optimizers.SGD(learning_rate=lr, momentum=0.9)",
     "Trains the best configuration again using SGD instead of Adam.",
     "This is 'optimizer selection' - comparing two optimizers fairly. Adam won (0.873 vs 0.817).")
line("res = pd.DataFrame(rows).sort_values('val_ccc', ascending=False)",
     "Ranks all configurations, best first, and saves them to a CSV.")
line("test_ccc = ccc(y_te, model.predict(X_te).flatten())",
     "Scores ONLY the winning configuration on the untouched test set.",
     "This is the honest final number: 0.883, improved from 0.861 before tuning.")
line("model.save('reports/noxi_mlp_tuned.keras')",
     "Saves the tuned model.")

# ================= CLOSING =================
d.add_page_break()
H("Answering questions confidently")
d.add_paragraph("1. Say WHAT a line does (its purpose), not the internal mathematics.")
d.add_paragraph("2. Variable names tell the story: Xtr = X-train, Xte = X-test, yte = y-test, "
                "pred = predictions, df = dataframe (the table).")
d.add_paragraph("3. It is perfectly acceptable to say: 'this uses the library's standard function for X'.")
d.add_paragraph("4. If unsure, trace what a line produces: 'this line takes the features and returns "
                "the model's predictions'.")

H("The libraries used", 2)
for a, b in [("pandas", "handling the data table"),
             ("NumPy", "mathematics on arrays of numbers"),
             ("scikit-learn", "the classic ML models, splitting, scaling and metrics"),
             ("TensorFlow / Keras", "the deep learning model (the ANN)"),
             ("Matplotlib / Seaborn", "the EDA charts"),
             ("SciPy", "the ANOVA statistical test")]:
    p = d.add_paragraph(style="List Bullet")
    r = p.add_run(a + " - "); r.bold = True
    p.add_run(b)
d.add_paragraph("A PyTorch version of scripts 06-07 is kept in src/pytorch_backup/. Both frameworks "
                "produced the same best configuration, which is a useful robustness check to mention.")

d.save("Complete_Code_Explanation.docx")
print("Saved Complete_Code_Explanation.docx")
