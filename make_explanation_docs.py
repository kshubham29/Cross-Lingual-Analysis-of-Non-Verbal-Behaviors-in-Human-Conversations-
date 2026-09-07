"""Generate two viva-prep Word docs: (1) full project explanation, (2) code line-by-line."""
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING

NAVY = RGBColor(0x1E, 0x2C, 0x3F)
TEAL = RGBColor(0x02, 0x80, 0x90)
CODE = RGBColor(0x0A, 0x3A, 0x4A)


def new_doc():
    d = Document()
    n = d.styles["Normal"]; n.font.name = "Calibri"; n.font.size = Pt(11)
    n.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    n.paragraph_format.space_after = Pt(6)
    return d


def H(d, t, l=1):
    h = d.add_heading(t, level=l)
    for r in h.runs:
        r.font.color.rgb = NAVY


def body(d, t):
    p = d.add_paragraph(t); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY


def bullet(d, t):
    d.add_paragraph(t, style="List Bullet")


def code(d, t):
    p = d.add_paragraph()
    r = p.add_run(t); r.font.name = "Consolas"; r.font.size = Pt(10); r.font.color.rgb = CODE
    r.bold = True


def why(d, t):
    p = d.add_paragraph()
    a = p.add_run("Why: "); a.bold = True; a.font.color.rgb = TEAL
    p.add_run(t)


def title_page(d, t, sub):
    for _ in range(3):
        d.add_paragraph()
    p = d.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(t); r.bold = True; r.font.size = Pt(24); r.font.color.rgb = NAVY
    s = d.add_paragraph(); s.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rs = s.add_run(sub); rs.italic = True; rs.font.size = Pt(13); rs.font.color.rgb = TEAL
    d.add_page_break()


# ============================================================
# DOC 1 — PROJECT EXPLANATION (start to end)
# ============================================================
d = new_doc()
title_page(d, "Project Explanation (Start to End)",
           "Cross-Lingual Engagement Prediction from Non-Verbal Behaviour")

H(d, "1. What Is This Project?")
body(d, "We built a system that predicts how ENGAGED a person is in a conversation, using only their "
        "non-verbal behaviour - their facial expressions and their voice tone - NOT the words they say. "
        "We then test whether a model trained on one language works on speakers of another language "
        "(cross-lingual). The whole project runs on the NoXi dataset of real expert-novice conversations.")

H(d, "2. Why We Did This (Importance / Benefit)")
bullet(d, "Engagement detection is useful for online education (is the student paying attention?), "
          "social robots and virtual agents (adapt to keep the user interested), and video-conferencing.")
bullet(d, "Using only non-verbal cues means it is language-independent - it can work for any language, "
          "because it does not depend on understanding the words.")
bullet(d, "Testing across languages matters for FAIR AI - a system should work for people of all "
          "languages/cultures, not just English speakers.")

H(d, "3. The Full Pipeline (Start to End)")
for t, txt in [
    ("Step 1 - Data", "We use the NoXi dataset: real conversations between an expert and a novice, in "
     "French, English and German, with engagement labelled continuously (0 to 1) 25 times per second."),
    ("Step 2 - Features", "For each person, NoXi provides pre-extracted voice features (eGeMAPS: 88 numbers "
     "- pitch, loudness, voice quality) and face features (OpenFace: 714 numbers - expressions, gaze, head pose)."),
    ("Step 3 - Preprocessing", "The features come 25 times per second, which is too fine. We group them "
     "into 1-second windows and average each window, giving a table of 17,174 rows and 802 features, each "
     "row labelled with its average engagement."),
    ("Step 4 - EDA", "We explored the data with charts: engagement distribution, engagement by language, "
     "expert vs novice, and which features matter most."),
    ("Step 5 - Baselines", "We trained 3 classic ML models to predict engagement and compared them."),
    ("Step 6 - Cross-lingual", "We trained on one language and tested on another to measure transfer."),
    ("Step 7 - Deep learning", "We built an ANN (neural network) and compared it to the baselines."),
]:
    p = d.add_paragraph(); r = p.add_run(t + ": "); r.bold = True; p.add_run(txt)

H(d, "4. EDA - What We Found")
bullet(d, "Data is balanced across languages (French 6568, German 5630, English 4976 windows).")
bullet(d, "Engagement is mostly medium (~0.5), with few people fully bored or fully engaged.")
bullet(d, "Experts are more engaged than novices (0.66 vs 0.51).")
bullet(d, "Voice features relate to engagement MORE than face features (0.39 vs 0.19).")
bullet(d, "An ANOVA test showed the languages differ significantly in engagement (p < 0.001).")

H(d, "5. Baseline Models - Which, Why, Results")
body(d, "We used three classic ML models as baselines, chosen because they represent three different "
        "families: Linear Regression (linear), Random Forest (tree-based), and SVR (kernel-based). "
        "Trying different families shows which approach suits the data best, and gives a reference score "
        "for the deep learning model to beat. We score with CCC (Concordance Correlation Coefficient, "
        "0 to 1, higher is better) because engagement is a continuous number (regression), so accuracy "
        "does not apply.")
p = d.add_paragraph()
p.add_run("Results: Random Forest = 0.886 (best), SVR = 0.827, Linear Regression = 0.284.").bold = True
body(d, "Linear Regression scored poorly (even a negative R2) because engagement is not a simple straight-line "
        "relationship - this justifies using more powerful models like Random Forest and neural networks.")

H(d, "6. Cross-Lingual Experiment - The Main Result")
body(d, "We trained a model on one language and tested it on another, for every pair, filling a 3x3 CCC "
        "matrix. Within a language (diagonal) the average CCC is 0.55; across languages (off-diagonal) it "
        "drops to 0.39.")
p = d.add_paragraph()
p.add_run("FINDING: Engagement is partly language-specific - a model trained on one language does not "
          "fully transfer to another. Interestingly, engagement LEVELS are similar across languages, but "
          "HOW people express engagement (through voice and face) differs between cultures.").bold = True

H(d, "7. Deep Learning Model - the ANN (explained in detail)")
body(d, "For the deep learning part we used an ANN (Artificial Neural Network) called an MLP "
        "(Multi-Layer Perceptron), built in TensorFlow / Keras. Its structure is 802 inputs -> 256 "
        "neurons -> 128 neurons -> 1 output (the engagement value). It reached a CCC of 0.861, and "
        "0.883 after hyperparameter tuning. We also implemented the same model in PyTorch as a "
        "cross-check, and both frameworks found the same best settings - which confirms the result "
        "is robust and not framework-specific.")
body(d, "Each part of the network has a purpose:")
for name, txt in [
    ("Layers (Linear)", "the neurons that learn patterns from the features."),
    ("Activation function (ReLU)", "ReLU keeps positive values and turns negatives to zero. BENEFIT: "
     "without an activation function the network could only learn straight lines (like Linear Regression); "
     "ReLU lets it learn complex, non-linear patterns. That is what makes a neural network powerful."),
    ("Dropout (0.1, tuned)", "randomly switches off 10% of neurons during training. BENEFIT: prevents "
     "overfitting - it stops the network memorising the training data. We started at 0.3 and tuned it: "
     "0.1 gave the best validation score, so our data does not need heavy regularization."),
    ("Loss (MSE)", "measures how far the predictions are from the true engagement values (the error)."),
    ("Optimizer (Adam)", "the algorithm that adjusts the network to reduce the error; Adam is fast and "
     "stable, and beat SGD in our tuning experiments."),
    ("Backpropagation", "after measuring the error, the network calculates how to change its weights to do "
     "better - this is how it learns. In Keras this happens inside model.fit()."),
    ("Epochs (60-80)", "one epoch = one full pass over the data; training for many epochs lets the network "
     "improve gradually until the score settles."),
]:
    p = d.add_paragraph(); r = p.add_run(name + ": "); r.bold = True; p.add_run(txt)

H(d, "7b. Hyperparameter Tuning (Model Improvement)")
body(d, "We ran a grid search over dropout (0.1, 0.3, 0.5), learning rate (0.001, 0.0005), architecture "
        "(256-128, 512-256) and optimizer (Adam vs SGD). To be fair, we split the data 60% train / 20% "
        "validation / 20% test: configurations were compared on the VALIDATION set, and only the winner was "
        "scored on the untouched TEST set.")
body(d, "Best configuration: dropout 0.1, learning rate 0.001, architecture 256-128, optimizer Adam. "
        "This improved test CCC from 0.861 to 0.883, which matches the Random Forest baseline (0.886).")
body(d, "Key finding: lower dropout is clearly better for our data (0.1 gave 0.857, 0.3 gave 0.828, and 0.5 "
        "dropped to 0.67-0.78). Adam also clearly beat SGD. Importantly, the PyTorch and TensorFlow versions "
        "found the SAME best configuration, which confirms the finding is reliable.")

H(d, "8. Results Summary")
bullet(d, "Best baseline: Random Forest, CCC 0.886.")
bullet(d, "Deep learning (ANN/MLP, TensorFlow): CCC 0.861 untuned, 0.883 after tuning.")
bullet(d, "Cross-lingual: within-language 0.55 vs cross-language 0.39 -> engagement is language-specific.")
bullet(d, "Voice matters more than face; experts more engaged than novices.")
bullet(d, "Tuning finding: dropout 0.1 best, Adam beats SGD, 256-128 architecture best.")

H(d, "9. What We Can Do More (Future Work)")
bullet(d, "Build an LSTM (temporal model) - engagement changes over time, so an LSTM should beat the MLP.")
bullet(d, "Wider hyperparameter search (more values, more architectures) and more training data.")
bullet(d, "Add Japanese and Chinese (NoXi+J) for a wider cross-cultural study.")
bullet(d, "Fuse voice and face with attention (multimodal transformer).")
bullet(d, "Build a live demo web app that predicts engagement from an uploaded clip.")

H(d, "10. One-Minute Summary (to say aloud)")
body(d, "\"We built an AI that predicts engagement from a person's face and voice - not their words - and "
        "tested it across French, English and German. We did EDA, trained three baselines (Random Forest "
        "best at 0.89), and built a neural network (0.82). Our main finding is that engagement is partly "
        "language-specific: a model trained on one language does not fully transfer to another. Next we will "
        "build an LSTM to improve it.\"")

d.save("Project_Explanation.docx")
print("Saved Project_Explanation.docx")


# ============================================================
# DOC 2 — CODE LINE BY LINE
# ============================================================
d = new_doc()
title_page(d, "Code Explained - Line by Line",
           "What each line does and why - Cross-Lingual Engagement Project")

H(d, "How to read this")
body(d, "The project has 7 scripts, run in order (01 to 07). Below, each key line of code is shown with "
        "what it does and why. You do not write the maths yourself - libraries (pandas, scikit-learn, "
        "TensorFlow/Keras) do it; your code gives them instructions. Scripts 01-05 use pandas, "
        "scikit-learn and matplotlib; scripts 06-07 (the deep learning) use TensorFlow/Keras.")

# ---- common lines ----
H(d, "Lines that appear in EVERY script")
for c, w in [
    ("import pandas as pd", "brings in pandas, for handling data tables."),
    ("import numpy as np", "brings in numpy, for maths on arrays of numbers."),
    ("df = pd.read_parquet(FEATURES)", "loads the data table into 'df'."),
    ("X = df[feat_cols]", "X = the input features (voice + face numbers)."),
    ("y = df['engagement']", "y = the answer we predict (engagement)."),
    ("train_test_split(X, y, test_size=0.2)", "split data: 80% to train, 20% to test on unseen data."),
    ("StandardScaler()", "put all features on the same scale so the model is fair."),
    (".fit(Xtr, ytr)", "TRAIN the model on the training data."),
    (".predict(Xte)", "make predictions on the test data."),
    ("print(...)", "show the result on screen."),
]:
    code(d, c); why(d, w)

# ---- 01 ----
H(d, "01_extract_data.py - get the data ready")
for c, w in [
    ("KEEP_SUFFIXES = (...egemapsv2..., ...openface2..., ...engagement...)",
     "list of the only file types we keep (voice, face, labels); the rest (videos) is skipped."),
    ("with zipfile.ZipFile(zip_path) as z:", "open the downloaded NoXi zip."),
    ("z.extract(member, DEST)", "pull one needed file out of the zip into our data folder."),
]:
    code(d, c); why(d, w)

# ---- 02 ----
H(d, "02_build_features.py - build the feature table")
for c, w in [
    ("ET.parse(header_path)...info.get('dim')", "read the NoXi .stream header to know how many features per frame."),
    ("np.fromfile(header_path + '~', dtype=dtype)", "read the raw feature numbers from the binary file."),
    (".reshape(n, dim)", "shape the numbers into a table (frames x features)."),
    ("WINDOW = 25", "25 frames = 1 second (data is 25 frames per second)."),
    ("for w in range(T // WINDOW):", "loop over each 1-second window."),
    ("np.nanmean(ege[s], 0)", "average the voice features over the window (one row per second)."),
    ("np.nanmean(y[s])", "average engagement over the window (the label for that row)."),
    ("df.to_parquet(OUT)", "save the finished feature table."),
]:
    code(d, c); why(d, w)

# ---- 03 ----
H(d, "03_eda.py - explore the data")
for c, w in [
    ("df.groupby('language')['engagement'].agg([...])", "summarise engagement per language (mean, std, etc.)."),
    ("stats.f_oneway(*groups)", "ANOVA test: are the languages significantly different in engagement?"),
    ("sns.histplot(df['engagement'])", "draw the engagement distribution chart."),
    ("sns.boxplot(x='language', y='engagement')", "compare engagement across languages."),
    ("df[feat_cols].corrwith(df['engagement'])", "find which features relate most to engagement."),
    ("plt.savefig(...)", "save each chart as an image for the report."),
]:
    code(d, c); why(d, w)

# ---- 04 ----
H(d, "04_baselines.py - baseline models")
for c, w in [
    ("def ccc(...)", "the CCC scoring formula (how close predictions are to the truth, 0 to 1)."),
    ("models = {LinearRegression, RandomForest, SVR}", "the three baseline models (three different families)."),
    ("make_pipeline(StandardScaler(), m)", "chain: scale features, then run the model."),
    ("if name == 'SVR' and len(Xtr) > 4000: ... choice(4000)",
     "SVR is slow on lots of data, so train it on a 4000-row sample to keep it fast."),
    ("ccc(yte, pred)", "score each model on the test set."),
]:
    code(d, c); why(d, w)

# ---- 05 ----
H(d, "05_cross_lingual.py - the main experiment")
for c, w in [
    ("for a, b in itertools.product(langs, langs):", "loop over every pair of languages (train a, test b)."),
    ("if a == b: ... leave-one-session-out",
     "same language: train on all sessions except one, test on the held-out one (a fair test)."),
    ("else: train df[lang==a], test df[lang==b]", "different language: train on A, test on B (the transfer)."),
    ("mat.loc[a, b] = fit_score(...)", "store the CCC in the results matrix."),
    ("mat.to_csv(...)", "save the 3x3 cross-lingual result matrix."),
]:
    code(d, c); why(d, w)

# ---- 06 ----
H(d, "06_deep_learning.py - the ANN (neural network, TensorFlow/Keras)")
for c, w in [
    ("from tensorflow import keras", "TensorFlow/Keras - the deep learning library we use."),
    ("keras.utils.set_random_seed(42)", "fix randomness so results are repeatable."),
    ("model = keras.Sequential([...])", "define our neural network as a stack of layers."),
    ("layers.Input(shape=(802,))", "the input - 802 features (voice + face) per row."),
    ("layers.Dense(256, activation='relu')",
     "a layer of 256 neurons with ReLU activation. ReLU keeps positives and zeros negatives, "
     "which lets the network learn non-linear (curved) patterns."),
    ("layers.Dropout(0.1)", "randomly ignore 10% of neurons during training to prevent overfitting "
     "(0.1 was chosen by our tuning experiments)."),
    ("layers.Dense(1)", "the output layer - gives 1 number, the predicted engagement."),
    ("model.compile(optimizer=Adam(1e-3), loss='mse')",
     "set the optimizer (Adam, which improves the network) and the loss (MSE, which measures error)."),
    ("model.fit(Xtr, ytr, epochs=20, batch_size=64)",
     "TRAIN the network. Keras does the whole training loop internally - forward pass, loss, "
     "backpropagation, and weight updates."),
    ("model.predict(Xte)", "make predictions on the test data."),
    ("model.save('reports/noxi_mlp.keras')", "save the trained network for reuse (e.g. a demo)."),
]:
    code(d, c); why(d, w)

H(d, "07_tuning.py - hyperparameter tuning")
for c, w in [
    ("train_test_split(...) twice", "split into 60% train / 20% validation / 20% test, so tuning is fair."),
    ("DROPOUTS = [0.1, 0.3, 0.5]", "the dropout values we try."),
    ("LRS = [1e-3, 5e-4]  /  HIDDENS = [(256,128),(512,256)]", "learning rates and architectures we try."),
    ("for drop, lr, hid in itertools.product(...)", "grid search - try every combination."),
    ("val = ccc(y_va, model.predict(X_va))", "score each configuration on the VALIDATION set."),
    ("keras.optimizers.SGD(lr, momentum=0.9)", "optimizer selection - compare SGD against Adam."),
    ("res.sort_values('val_ccc', ascending=False)", "rank all configurations, best first."),
    ("test_ccc = ccc(y_te, model.predict(X_te))",
     "score ONLY the winning configuration on the untouched TEST set (this is the honest final number)."),
]:
    code(d, c); why(d, w)

H(d, "Golden rule for the viva")
body(d, "For any line, say WHAT it does (its goal), not the internal maths. If unsure, read the variable "
        "names aloud - Xtr = X-train, yte = y-test, pred = predictions - they tell the story. It is fine to "
        "say 'this uses the library's standard function for X'.")
body(d, "Note: we also have a PyTorch version of the deep learning scripts in src/pytorch_backup/. Both "
        "frameworks produced the same best configuration, which is a good robustness check to mention.")

d.save("Code_Explained_LineByLine.docx")
print("Saved Code_Explained_LineByLine.docx")
