"""Builds Laboratory_Manual.docx from the project's result CSVs. Re-run after new results."""
import os
import sys
import pandas as pd
from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = sys.argv[1]
R = os.path.join(ROOT, "reports")
OUT = os.path.join(ROOT, "Laboratory_Manual.docx")
GREEN = RGBColor(0x3F, 0x6B, 0x35)
HEAD_FILL = "DCE6D2"

doc = Document()
for s in doc.sections:
    s.left_margin = s.right_margin = Cm(2.2)
    s.top_margin = s.bottom_margin = Cm(2)
st = doc.styles["Normal"]
st.font.name = "Calibri"
st.font.size = Pt(11)
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
for name, size in (("Heading 1", 16), ("Heading 2", 13), ("Heading 3", 11.5)):
    h = doc.styles[name]
    h.font.name = "Cambria"
    h.font.size = Pt(size)
    h.font.color.rgb = GREEN
    h.element.rPr.rFonts.set(qn("w:eastAsia"), "Cambria")


def shade(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear")
    sh.set(qn("w:color"), "auto")
    sh.set(qn("w:fill"), fill)
    tcPr.append(sh)


def para(text, bold=False, italic=False, size=None, align=None, space_after=4):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.bold, r.italic = bold, italic
    if size:
        r.font.size = Pt(size)
    if align:
        p.alignment = align
    p.paragraph_format.space_after = Pt(space_after)
    return p


def label(name, text):
    p = doc.add_paragraph()
    r = p.add_run(name + ": ")
    r.bold = True
    r.font.color.rgb = GREEN
    p.add_run(text)
    p.paragraph_format.space_after = Pt(4)


def bullets(items, style="List Bullet"):
    for it in items:
        p = doc.add_paragraph(it, style=style)
        p.paragraph_format.space_after = Pt(2)


def code(text):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.font.name = "Consolas"
    r.font.size = Pt(10)
    p.paragraph_format.left_indent = Cm(0.6)
    p.paragraph_format.space_after = Pt(6)


def table(header, rows, widths=None):
    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(header):
        c = t.rows[0].cells[i]
        c.text = ""
        r = c.paragraphs[0].add_run(str(h))
        r.bold = True
        r.font.size = Pt(10)
        shade(c, HEAD_FILL)
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            r = cells[i].paragraphs[0].add_run(str(v))
            r.font.size = Pt(10)
    if widths:
        for row in t.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Cm(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def f3(x):
    return f"{x:.3f}"


def csv(name):
    p = os.path.join(R, name)
    return pd.read_csv(p) if os.path.exists(p) else None


def pending(script):
    para(f"Result table is filled in automatically after running {script}.", italic=True)


def figure(name, width=14):
    p = os.path.join(R, "figures", name)
    if os.path.exists(p):
        doc.add_picture(p, width=Cm(width))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER


def viva(qa):
    doc.add_heading("Viva Questions", level=3)
    for i, (q, a) in enumerate(qa, 1):
        p = doc.add_paragraph()
        r = p.add_run(f"Q{i}. {q}")
        r.bold = True
        p.paragraph_format.space_after = Pt(0)
        p2 = doc.add_paragraph(f"Ans: {a}")
        p2.paragraph_format.left_indent = Cm(0.6)
        p2.paragraph_format.space_after = Pt(5)


def experiment(no, title, unit, aim, theory, procedure, script, command, results, observations, qa):
    doc.add_page_break()
    doc.add_heading(f"Experiment {no}: {title}", level=1)
    label("Syllabus link", unit)
    label("Aim", aim)
    doc.add_heading("Theory", level=3)
    for t in theory:
        para(t)
    doc.add_heading("Procedure", level=3)
    bullets(procedure, "List Number")
    doc.add_heading("Program", level=3)
    label("File", script)
    code(command)
    doc.add_heading("Output / Results", level=3)
    results()
    doc.add_heading("Observations and Conclusion", level=3)
    bullets(observations)
    viva(qa)


# ------------------------------------------------------------------ results
def fold_summary(df):
    g = df.groupby("model").agg(ccc=("ccc", "mean"), std=("ccc", "std"),
                                pearson=("pearson", "mean"), mae=("mae", "mean"))
    return g.sort_values("ccc", ascending=False)


def res_data():
    table(["Item", "Value"], [
        ["Conversations (sessions)", "9 (3 English, 3 French, 3 German)"],
        ["Speakers per conversation", "2 (expert + novice)"],
        ["Frame rate", "25 frames per second"],
        ["Window", "25 frames = 1 second, averaged into one row"],
        ["Rows (1-second windows)", "17,174"],
        ["Voice features (eGeMAPS)", "88"],
        ["Face features (OpenFace 2.0)", "714 (709 behaviour + 5 bookkeeping columns)"],
        ["Target", "engagement, continuous 0-1"],
        ["Outputs", "noxi_engagement.parquet (17174 x 806), noxi_sequences.npy (17174 x 25 x 802)"],
    ], [6, 10])


def res_eda():
    e = csv("eda_summary.csv")
    if e is not None:
        table(["Language", "Windows", "Mean", "Std", "Min", "Max"],
              [[r.language, int(r["count"]), f3(r["mean"]), f3(r["std"]), f3(r["min"]), f3(r["max"])]
               for _, r in e.iterrows()])
    figure("engagement_by_language.png", 12)


def res_baselines():
    para("Random 80/20 split of 1-second windows (development stage):")
    table(["Model", "CCC", "Pearson", "MAE", "R²"], [
        ["Linear Regression", "0.284", "0.385", "0.076", "-3.412"],
        ["Random Forest", "0.885", "0.896", "0.051", "0.802"],
        ["Gradient Boosting", "0.901", "0.907", "0.049", "0.823"],
        ["XGBoost", "0.906", "0.912", "0.048", "0.831"],
    ])
    para("Note: these scores are optimistic. Neighbouring seconds of the same conversation fall in "
         "both train and test. The honest, session-wise scores are in Experiment 11.", italic=True)


def res_cross():
    m = csv("noxi_crosslingual_ccc.csv")
    if m is None:
        return pending("05_cross_lingual.py")
    m = m.rename(columns={m.columns[0]: "train \\ test"})
    table(list(m.columns), [[r.iloc[0]] + [f3(v) for v in r.iloc[1:]] for _, r in m.iterrows()])
    langs = list(m.columns[1:])
    diag = sum(m.iloc[i, i + 1] for i in range(len(langs))) / len(langs)
    off = (m.iloc[:, 1:].to_numpy().sum() - diag * len(langs)) / (len(langs) * (len(langs) - 1))
    para(f"Average within-language CCC = {diag:.3f}; average cross-language CCC = {off:.3f}; "
         f"drop = {100 * (diag - off) / diag:.0f}%.", bold=True)


def res_ann():
    s = csv("sequence_results.csv")
    if s is not None:
        table(["Model", "CCC", "Pearson", "MAE"],
              [[r.model, f3(r.ccc), f3(r.pearson), f3(r.mae)] for _, r in s.iterrows()])


def res_tuning():
    t = csv("tuning_results.csv")
    if t is None:
        return pending("07_tuning.py")
    t = t.sort_values("val_ccc", ascending=False)
    table(["Dropout", "Learning rate", "Hidden", "Optimizer", "Validation CCC"],
          [[r.dropout, r.lr, r.hidden, r.optimizer, f3(r.val_ccc)] for _, r in t.iterrows()])
    para("Best: dropout 0.1, learning rate 0.001, 256-128, Adam. Test CCC of the winner = 0.881.", bold=True)


def res_cnn():
    t = csv("cnn_tuning_results.csv")
    if t is None:
        return pending("09_cnn.py")
    t = t.sort_values("val_ccc", ascending=False)
    table(["Filters", "Kernel", "Dropout", "Validation CCC"],
          [[r.filters, r.kernel, r.dropout, f3(r.val_ccc)] for _, r in t.iterrows()])
    para("Best: 32 filters, kernel 5, dropout 0.1. Test CCC = 0.843 (171,681 parameters).", bold=True)


def res_arch():
    t = csv("cnn_architectures.csv")
    if t is None:
        return pending("11_cnn_architectures.py")
    table(["Architecture", "Parameters", "Validation CCC", "Test CCC", "Pearson", "MAE"],
          [[r.model, f"{int(r.params):,}", f3(r.val_ccc), f3(r.test_ccc), f3(r.pearson), f3(r.mae)]
           for _, r in t.iterrows()])


def res_transfer():
    t = csv("transfer_results.csv")
    if t is None or "fraction" not in t.columns:
        return pending("10_transfer_learning.py")
    cond = ["zero_shot", "head_only", "fine_tune", "scratch"]
    g = t.groupby("fraction")[cond].mean()
    para("Mean CCC over 3 target languages x 3 adaptation sessions, by share of the adaptation session used:")
    table(["Share of 1 session", "Zero-shot", "Head-only", "Fine-tune", "Scratch"],
          [[f"{int(f * 100)}%"] + [f3(v) for v in r] for f, r in g.iterrows()])
    g2 = t[t.fraction == 1.0].groupby("target")[cond].mean()
    para("By target language (full adaptation session):")
    table(["Target", "Zero-shot", "Head-only", "Fine-tune", "Scratch"],
          [[l] + [f3(v) for v in r] for l, r in g2.iterrows()])


def res_lstm_tr():
    rows = []
    for f in ("lstm_results.csv", "transformer_results.csv"):
        t = csv(f)
        if t is not None:
            rows += [[r.model, f"{int(r.params):,}", f3(r.val_ccc), f3(r.test_ccc), f3(r.pearson), f3(r.mae)]
                     for _, r in t.iterrows()]
    table(["Model", "Parameters", "Validation CCC", "Test CCC", "Pearson", "MAE"], rows)


def res_session_flat():
    t = csv("session_flat.csv")
    if t is None:
        return pending("14_session_eval.py")
    old = {"LinearRegression": "0.284", "RandomForest": "0.885", "GradientBoosting": "0.901",
           "XGBoost": "0.906", "ANN (MLP)": "0.881"}
    table(["Model", "Session-wise CCC (mean ± std)", "Pearson", "MAE", "Old random-split CCC"],
          [[m, f"{r.ccc:.3f} ± {r['std']:.3f}", f3(r.pearson), f3(r.mae), old.get(m, "")]
           for m, r in fold_summary(t).iterrows()])


def res_session_seq():
    t = csv("session_sequence.csv")
    if t is None:
        return pending("15_session_sequence.py")
    params = t.groupby("model")["params"].first()
    table(["Model", "Parameters", "Session-wise CCC (mean ± std)", "Pearson", "MAE"],
          [[m, f"{int(params[m]):,}", f"{r.ccc:.3f} ± {r['std']:.3f}", f3(r.pearson), f3(r.mae)]
           for m, r in fold_summary(t).iterrows()])


def res_ae():
    t = csv("autoencoder_results.csv")
    if t is None:
        return pending("16_autoencoder.py")
    table(["Model", "Session-wise CCC (mean ± std)", "Pearson", "MAE"],
          [[m, f"{r.ccc:.3f} ± {r['std']:.3f}", f3(r.pearson), f3(r.mae)]
           for m, r in fold_summary(t).iterrows()])
    para(f"Mean reconstruction MSE on unseen sessions (scaled units): {t.recon_mse.mean():.3f}")


def res_ablation():
    t = csv("ablation_results.csv")
    if t is None:
        return pending("17_ablation.py")
    table(["Input", "Features", "Session-wise CCC", "Within-language", "Cross-language", "Drop"],
          [[r.modality, int(r.n_features), f"{r.session_ccc:.3f} ± {r.session_std:.3f}",
            f3(r.within_ccc), f3(r.cross_ccc), f"{r.drop_pct:.0f}%"] for _, r in t.iterrows()])


def res_master():
    t = csv("master_results.csv")
    if t is None:
        return pending("18_master_results.py")
    table(["Model", "Family", "Session-wise CCC", "Pearson", "MAE", "Random split"],
          [[r.model, r.family, f"{r.session_ccc:.3f} ± {r.session_std:.3f}", f3(r.pearson), f3(r.mae),
            "" if pd.isna(r.random_split_ccc) else f3(r.random_split_ccc)] for _, r in t.iterrows()])
    figure("master_ccc.png", 14)


# ------------------------------------------------------------------ cover
for _ in range(4):
    doc.add_paragraph()
para("LABORATORY MANUAL", bold=True, size=24, align=WD_ALIGN_PARAGRAPH.CENTER)
para("Deep Learning - Semester Project", size=14, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=30)
para("Cross-Lingual Prediction of Engagement from", bold=True, size=16, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=0)
para("Non-Verbal Behaviour in Human Conversations", bold=True, size=16, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=40)
para("Submitted by: [Team member names and roll numbers]", size=12, align=WD_ALIGN_PARAGRAPH.CENTER)
para("Supervisor: [Supervisor name]", size=12, align=WD_ALIGN_PARAGRAPH.CENTER)
para("Department: [Department, University]", size=12, align=WD_ALIGN_PARAGRAPH.CENTER)
para("Academic year: 2026-27", size=12, align=WD_ALIGN_PARAGRAPH.CENTER)

# ------------------------------------------------------------------ index
EXPS = [
    ("Dataset preparation and feature extraction", "01_extract_data.py, 02_build_features.py"),
    ("Exploratory data analysis (EDA)", "03_eda.py"),
    ("Machine-learning baselines", "04_baselines.py"),
    ("Cross-lingual evaluation", "05_cross_lingual.py"),
    ("Artificial Neural Network (ANN)", "06_deep_learning.py, 08_sequence_models.py"),
    ("Hyperparameter tuning and regularisation", "07_tuning.py"),
    ("Convolutional Neural Network (CNN) and tuning", "09_cnn.py"),
    ("Classic CNN architectures: LeNet, VGG, ResNet", "11_cnn_architectures.py"),
    ("Transfer learning across languages", "10_transfer_learning.py"),
    ("LSTM and Transformer encoder", "13_lstm.py, 12_transformer.py"),
    ("Session-wise evaluation (data-leakage fix)", "14_session_eval.py"),
    ("Sequence models session-wise: CNN, RNN, LSTM, GRU, Transformer", "15_session_sequence.py"),
    ("Autoencoder", "16_autoencoder.py"),
    ("Ablation study: voice vs face", "17_ablation.py"),
    ("Master results and comparison", "18_master_results.py"),
    ("AI prototype: engagement demo app", "app.py"),
]
doc.add_page_break()
doc.add_heading("Index", level=1)
table(["No.", "Experiment", "Program file", "Sign"],
      [[i, t, f, ""] for i, (t, f) in enumerate(EXPS, 1)], [1.2, 7.5, 6, 1.8])

# ------------------------------------------------------------------ setup
doc.add_page_break()
doc.add_heading("General Instructions and Lab Setup", level=1)
doc.add_heading("Software", level=3)
table(["Item", "Version"], [["Python", "3.12"], ["TensorFlow / Keras", "2.21 / 3.15"],
                            ["scikit-learn", "1.4.2"], ["XGBoost", "3.4.0"], ["pandas / NumPy", "2.1.4 / 1.26.4"],
                            ["Streamlit (demo)", "1.66.1"], ["Editor", "VS Code"]])
doc.add_heading("Setting up the environment", level=3)
code("python -m venv .venv\n.venv\\Scripts\\activate\npip install -r requirements.txt")
doc.add_heading("Folder structure", level=3)
code("cross-lingual-nonverbal/\n  data/        NoXi files and extracted features (licensed, not shared)\n"
     "  src/         one program per experiment (01 ... 18)\n  reports/     result tables (.csv), trained models, figures\n"
     "  app.py       demo application\n  requirements.txt")
doc.add_heading("Rules", level=3)
bullets([
    "Run every program from the project folder, e.g. python src/04_baselines.py.",
    "The NoXi dataset is licensed under an End-User Licence Agreement. Do not upload it to GitHub, cloud drives or online AI tools.",
    "Every scaler is fitted on training data only, to avoid data leakage.",
    "All experiments use random_state / seed 42 so results can be repeated.",
    "The main metric is the Concordance Correlation Coefficient (CCC): 1 = perfect agreement, 0 = no agreement.",
])
doc.add_heading("Evaluation metric", level=3)
para("CCC = 2·cov(y, ŷ) / (var(y) + var(ŷ) + (mean(y) − mean(ŷ))²)")
para("CCC is used instead of accuracy because engagement is a continuous value (regression), not a class. "
     "Unlike Pearson correlation, CCC also penalises predictions that are shifted or scaled away from the true values.")

# ------------------------------------------------------------------ experiments
experiment(1, EXPS[0][0], "Unit 1 - data preparation for neural networks",
    "To convert the raw NoXi feature streams into a table of 1-second windows with voice features, face features and an engagement label.",
    ["NoXi is a corpus of expert-novice conversations recorded in several languages. For every frame (25 per second) it provides "
     "88 eGeMAPS voice features (pitch, loudness, jitter, shimmer, spectral shape) and 714 OpenFace 2.0 face features "
     "(gaze, head pose, facial landmarks, action units), plus a continuous engagement annotation.",
     "Single frames are noisy, so 25 consecutive frames (1 second) are averaged into one row. The un-averaged 25-frame "
     "windows are also kept for the sequence models (CNN, RNN, LSTM, Transformer).",
     "The first 5 OpenFace columns (frame number, face id, timestamp, confidence, success) are recording bookkeeping, not behaviour, "
     "and are dropped in the final experiments."],
    ["Obtain NoXi access through the supervisor (EULA).", "Run 01_extract_data.py with the path of the NoXi zip to keep only the needed files.",
     "Run 02_build_features.py to read the SSI .stream files, align voice, face and engagement, and cut 1-second windows.",
     "Check that data/features/ contains noxi_engagement.parquet and noxi_sequences.npy."],
    "src/01_extract_data.py, src/02_build_features.py",
    'python src/01_extract_data.py "path/to/train.zip"\npython src/02_build_features.py',
    res_data,
    ["17,174 one-second windows were built from 9 conversations.", "Each row has voice + face features, engagement, language, session and role."],
    [("Why 25 frames per window?", "NoXi records at 25 fps, so 25 frames is exactly one second of behaviour."),
     ("Why average the frames?", "Single frames are noisy; the mean of one second is a stable summary."),
     ("What is eGeMAPS?", "A standard set of 88 voice parameters (pitch, loudness, voice quality) designed for emotion research."),
     ("Why are words not used?", "The project studies non-verbal cues only, so it can work across languages without translation.")])

experiment(2, EXPS[1][0], "Unit 1 - understanding the data before modelling",
    "To explore the distribution of engagement and the features before training any model.",
    ["EDA checks the target distribution, class balance between languages, missing values and correlations, "
     "so that modelling choices (metric, scaling, splits) are justified."],
    ["Load the feature table.", "Plot the engagement distribution, by language and by role.", "Plot the correlation heatmap and top correlated features.",
     "Save the summary table."],
    "src/03_eda.py", "python src/03_eda.py", res_eda,
    ["Engagement is continuous and spread over 0-1, so the task is regression.", "French has the most windows, English the fewest."],
    [("Is there class imbalance?", "No classes - it is regression. Languages differ in size, so results are reported per language."),
     ("Why look at correlations?", "To see which single features relate to engagement and to spot redundant features.")])

experiment(3, EXPS[2][0], "Unit 1 - overview of machine learning",
    "To train classic regression models as reference points for the deep-learning models.",
    ["Linear Regression assumes a straight-line relation. Random Forest averages many decision trees (bagging). "
     "Gradient Boosting and XGBoost add trees one by one, each correcting the previous errors (boosting).",
     "Features are standardised with StandardScaler fitted on the training part only."],
    ["Load features and engagement.", "Split 80/20 with random_state 42.", "Fit each model in a StandardScaler pipeline.", "Report CCC, Pearson, MAE and R² on the test set."],
    "src/04_baselines.py", "python src/04_baselines.py", res_baselines,
    ["Tree ensembles are far better than the linear model.", "XGBoost is the strongest baseline on the random split."],
    [("Bagging vs boosting?", "Bagging trains trees independently and averages them; boosting trains them in sequence to fix earlier errors."),
     ("What does negative R² mean?", "The model is worse than always predicting the mean."),
     ("Why fit the scaler on train only?", "Using test data to compute the mean and std leaks information from the test set.")])

experiment(4, EXPS[3][0], "Research question of the project",
    "To measure how much engagement prediction drops when the model is tested on a language it was not trained on.",
    ["Within-language: leave-one-session-out inside a language (train on 2 conversations, test on the 3rd). "
     "Cross-language: train on all conversations of language A and test on all of language B. Model: Random Forest."],
    ["Load features (bookkeeping columns removed).", "For every (train, test) language pair, train and score.", "Build the 3x3 CCC matrix and compare the diagonal with the off-diagonal."],
    "src/05_cross_lingual.py", "python src/05_cross_lingual.py", res_cross,
    ["Prediction drops by about 29% in a new language.", "French-trained models transfer worst to English."],
    [("Why leave-one-session-out on the diagonal?", "So the test conversation is never seen in training, same as in the cross-language case."),
     ("What can cause the drop?", "Cultural differences in non-verbal behaviour, and different recording sites per language.")])

experiment(5, EXPS[4][0], "Unit 1 - building an ANN, activation functions, loss, optimisers",
    "To build and train a feed-forward neural network that predicts engagement from the 802 features.",
    ["Architecture: 802 inputs → Dense 256 (ReLU) → Dropout → Dense 128 (ReLU) → Dropout → Dense 1.",
     "ReLU avoids vanishing gradients and is cheap to compute. Loss: mean squared error. Optimiser: Adam (learning rate 0.001). "
     "Weights are learned by back-propagation and gradient descent inside model.fit()."],
    ["Scale features.", "Build the Sequential model and print model.summary().", "Train for 20 epochs, checking test CCC every 5 epochs.", "Compare with XGBoost on the same test set."],
    "src/06_deep_learning.py, src/08_sequence_models.py", "python src/06_deep_learning.py\npython src/08_sequence_models.py", res_ann,
    ["The ANN learns the task but does not beat XGBoost on this tabular data."],
    [("Why ReLU?", "Simple, fast, and its gradient does not vanish for positive inputs."),
     ("Why Adam?", "It adapts the learning rate per weight and uses momentum, so it trains quickly with little tuning."),
     ("How many hidden layers and why?", "Two; more layers overfit with only 17k samples.")])

experiment(6, EXPS[5][0], "Unit 1 - evaluating, improving and tuning the ANN; Unit 2 - dropout",
    "To find the best dropout, learning rate, layer size and optimiser for the ANN.",
    ["Dropout randomly switches off neurons during training, which reduces overfitting. "
     "SGD with momentum and Adam are compared. Configurations are compared on a validation set; only the winner is scored on test."],
    ["Split 60/20/20 (train/validation/test).", "Grid over dropout {0.1, 0.3, 0.5} × learning rate × hidden size, plus SGD.", "Pick the best validation CCC; score it once on test."],
    "src/07_tuning.py", "python src/07_tuning.py", res_tuning,
    ["Small dropout (0.1) works best; Adam beats SGD."],
    [("Why a validation set?", "Choosing settings on the test set would make the test score optimistic."),
     ("What is momentum?", "It keeps part of the previous update so gradient descent moves faster and oscillates less.")])

experiment(7, EXPS[6][0], "Unit 2 - TensorFlow/Keras, convolution, pooling, flattening, full connection, tuning the CNN",
    "To apply a 1-D convolutional network to the 25-frame sequences and tune it.",
    ["A 1-D convolution slides a small filter along the time axis and detects short behaviour patterns. "
     "Max-pooling halves the length and keeps the strongest response; Flatten turns the result into a vector for the dense layers.",
     "LeNet-style: Conv → Pool → Conv → Pool → Flatten → Dense → Dense → output."],
    ["Load the (windows, 25, features) sequences and scale frame by frame.", "Grid over filters {32, 64}, kernel {3, 5}, dropout {0.1, 0.3}.",
     "Retrain the best configuration and score it on test."],
    "src/09_cnn.py", "python src/09_cnn.py", res_cnn,
    ["Kernel 5 (one-fifth of a second) with 32 filters is the best configuration."],
    [("Why 1-D and not 2-D convolution?", "The input is a time series of features, not an image; time is the only spatial axis."),
     ("What does pooling do?", "Reduces size and keeps the strongest local response, giving some robustness to small shifts.")])

experiment(8, EXPS[7][0], "Unit 2 - CNN applications and classic models",
    "To compare LeNet-, VGG- and ResNet-style networks rebuilt with 1-D convolutions.",
    ["LeNet: a few convolutions with larger kernels. VGG: stacks of small (kernel 3) convolutions before each pooling. "
     "ResNet: residual blocks where the input skips the convolutions and is added back, with batch normalisation."],
    ["Build the three networks with the same input, split and seed.", "Train each for 20 epochs.", "Compare validation and test CCC and parameter counts."],
    "src/11_cnn_architectures.py", "python src/11_cnn_architectures.py", res_arch,
    ["VGG-style is the best CNN; ResNet's skip connections bring no gain for such a short, shallow input."],
    [("Why do skip connections help in ResNet?", "Gradients flow directly through the shortcut, so very deep networks can still train."),
     ("Why did ResNet not win here?", "Our network is shallow and the sequence is only 25 steps, so there is no vanishing-gradient problem to solve.")])

experiment(9, EXPS[8][0], "Unit 2 - transfer learning models",
    "To test whether a CNN pretrained on two languages can be adapted to a third with a small amount of its data.",
    ["Session-wise protocol: pretrain on the two source languages; adapt on ONE conversation of the target language; "
     "test on its other two conversations. Each target conversation takes a turn, and 10%, 25%, 50% and 100% of it are tried.",
     "Conditions: zero-shot (no adaptation), head-only (convolutions frozen), fine-tune (all layers, learning rate 1e-4), "
     "scratch (same network, no pretraining)."],
    ["Fit the scaler on the source languages.", "Pretrain the tuned CNN for 30 epochs.", "For each adaptation session and share, run the four conditions.", "Average over languages and sessions."],
    "src/10_transfer_learning.py", "python src/10_transfer_learning.py", res_transfer,
    ["Compare head-only and fine-tune with scratch: if they are higher, knowledge transfers across languages.",
     "The share sweep shows how much new-language data is needed."],
    [("Why freeze the convolution layers?", "They hold general behaviour patterns learned from more data; only the head adapts to the new language."),
     ("Why a small learning rate for fine-tuning?", "So the pretrained weights change only slightly instead of being overwritten.")])

experiment(10, EXPS[9][0], "Unit 4 - LSTM; Unit 5 - Transformers",
    "To model the 25-frame sequence with a recurrent network (LSTM) and with self-attention (Transformer encoder).",
    ["LSTM reads frames in order and keeps a memory cell controlled by input, forget and output gates, which avoids the vanishing gradient of a simple RNN.",
     "The Transformer encoder projects each frame to 64 numbers, adds a learned positional encoding, and applies 2 blocks of 4-head self-attention "
     "with feed-forward layers, residual connections and layer normalisation. It is trained from scratch; pretrained text models such as BERT do not fit numeric behaviour features."],
    ["Load and scale sequences (60/20/20).", "Train LSTM(128) for 20 epochs and the Transformer for 25 epochs, watching validation CCC.", "Score both on test."],
    "src/13_lstm.py, src/12_transformer.py", "python src/13_lstm.py\npython src/12_transformer.py", res_lstm_tr,
    ["Both reach about 0.83-0.85 on the random split, below XGBoost.", "The Transformer peaks around epoch 15 and then overfits."],
    [("What problem does LSTM solve?", "Vanishing gradients in simple RNNs, using gates that control what to remember and forget."),
     ("Why positional encoding?", "Self-attention has no sense of order; the encoding tells the model which frame is which."),
     ("Encoder vs decoder?", "The encoder reads and understands the input; a decoder generates output step by step, which is not needed for regression.")])

experiment(11, EXPS[10][0], "Evaluation methodology (research rigour)",
    "To measure performance on completely unseen conversations, removing the data leakage of the random split.",
    ["With a random split, neighbouring seconds of the same conversation appear in train and test and are almost identical, "
     "so models recognise the person instead of learning behaviour.",
     "Session-wise protocol: 3 folds; each fold tests on one whole conversation per language and trains on the other 6. "
     "Neural-network inputs are clipped to [-5, 5] after scaling, because a few extreme values in unseen sessions (up to 100,000 standard deviations) destabilise them."],
    ["Build the 3 folds from the session ids.", "Train Linear Regression, Random Forest, Gradient Boosting, XGBoost and the tuned ANN on each fold.",
     "Report mean ± std CCC over the folds and save the XGBoost fold models for the demo."],
    "src/14_session_eval.py", "python src/14_session_eval.py", res_session_flat,
    ["Scores on unseen conversations are much lower than the random-split scores - this is the honest generalisation.",
     "Tree ensembles generalise best."],
    [("What is data leakage?", "Information from the test set reaching training, which makes scores look better than they really are."),
     ("Why 3 folds and not 9?", "Each fold holds out one conversation from every language, so every test set contains all three languages."),
     ("Why clip scaled values?", "Rare extreme values do not affect trees but produce huge activations in neural networks.")])

experiment(12, EXPS[11][0], "Unit 4 - RNN, vanishing gradient, LSTM variations, GRU",
    "To compare the sequence models on unseen conversations and add a simple RNN and a GRU.",
    ["Simple RNN: one hidden state updated every frame; suffers from vanishing gradients over long sequences. "
     "GRU: a lighter LSTM with update and reset gates and no separate memory cell.",
     "All models share the same head (Dropout → Dense 64 → Dense 1) and the same 3 session-wise folds."],
    ["Load the sequences and drop the 5 bookkeeping columns.", "For each fold, scale on training frames (clipped to [-5, 5]).",
     "Train CNN (VGG-style), Simple RNN, LSTM, GRU and Transformer for 20 epochs.", "Report mean ± std CCC."],
    "src/15_session_sequence.py", "python src/15_session_sequence.py", res_session_seq,
    ["Compare gated (LSTM, GRU) with ungated (Simple RNN) recurrence, and recurrence with attention and convolution."],
    [("LSTM vs GRU?", "LSTM has 3 gates and a memory cell; GRU has 2 gates and fewer parameters, often with similar accuracy."),
     ("What is the vanishing gradient?", "Gradients shrink as they pass back through many steps, so early steps learn almost nothing.")])

experiment(13, EXPS[12][0], "Unit 5 - autoencoders",
    "To compress the 797 features into a 32-number code without labels, and test whether the code still predicts engagement.",
    ["An autoencoder has an encoder (797 → 256 → 32) and a decoder (32 → 256 → 797) trained to reproduce its input. "
     "The 32-number bottleneck is a learned, compact summary of behaviour.",
     "After training, the encoder is frozen and a small dense head, or XGBoost, predicts engagement from the code."],
    ["For each session-wise fold, scale and clip the features.", "Train the autoencoder on the training sessions (input = target).",
     "Freeze the encoder, train the head; also train XGBoost on the codes.", "Report CCC and reconstruction error."],
    "src/16_autoencoder.py", "python src/16_autoencoder.py", res_ae,
    ["A 25x compression keeps much of the information needed to predict engagement."],
    [("Is an autoencoder supervised?", "No - it learns from the input alone; labels are used only by the head trained afterwards."),
     ("What is the bottleneck?", "The smallest layer (32 units); it forces the network to keep only the most important information.")])

experiment(14, EXPS[13][0], "Research contribution - ablation study",
    "To find out which modality - voice or face - predicts engagement best and which survives a change of language.",
    ["The same XGBoost model is trained three times with different inputs: voice only (88), face only (709) and both (797). "
     "Each is scored session-wise and in the within- vs cross-language setting of Experiment 4."],
    ["Select the voice, face and combined columns.", "Run the 3 session-wise folds.", "Run within-language leave-one-session-out and all 6 cross-language pairs.", "Compute the drop for each modality."],
    "src/17_ablation.py", "python src/17_ablation.py", res_ablation,
    ["Voice alone is the strongest input and the most language-independent.",
     "Face features drop sharply across languages; part of this may come from different cameras and rooms at each recording site."],
    [("What is an ablation study?", "Removing parts of the input or model one at a time to see how much each part contributes."),
     ("Why might the face transfer badly?", "Cultural display rules differ, and each language was recorded at a different site with different camera setups.")])

experiment(15, EXPS[14][0], "Comparative analysis",
    "To collect the session-wise scores of every model in one table and one chart.",
    ["One master table avoids conflicting numbers across the report, paper, poster and slides."],
    ["Run Experiments 11-13 first.", "Run 18_master_results.py to merge the per-fold results and draw the bar chart."],
    "src/18_master_results.py", "python src/18_master_results.py", res_master,
    ["All documents should take their numbers from reports/master_results.csv."],
    [("Why report mean ± std?", "It shows how much the score changes between folds, i.e. how reliable it is.")])

experiment(16, EXPS[15][0], "Deployment / AI prototype",
    "To build an interactive application that predicts engagement second by second for a chosen conversation.",
    ["The Streamlit app loads the XGBoost model of the fold in which the chosen conversation was held out, so the prediction is always on an unseen conversation. "
     "The user can switch between voice + face, voice only and face only."],
    ["Run Experiment 11 (it saves the fold models).", "Start the app with streamlit run app.py.", "Choose a conversation, speaker and input type; compare the predicted and actual curves."],
    "app.py", "streamlit run app.py", lambda: para("The app opens at http://localhost:8501 with a live chart of actual vs predicted engagement, "
                                                    "CCC and Pearson for the selected conversation, and a Results tab with all result tables."),
    ["The prediction follows the rises and falls of engagement (high Pearson) even when its level is shifted (lower CCC)."],
    [("Why use the held-out fold model?", "Otherwise the demo would show predictions on conversations the model was trained on."),
     ("Why Streamlit?", "It turns a Python script into a web app with a few lines and no front-end code.")])

doc.save(OUT)
print("saved", OUT)
