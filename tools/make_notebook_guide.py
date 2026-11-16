"""Writes Notebook_Code_Explanation.docx: for each of the 12 notebooks in notebooks/,
what the step does, every code cell with its code, a plain line-by-line explanation,
the result, and likely viva questions. Plain black and white.
Run from the project folder: python tools/make_notebook_guide.py"""
import nbformat
from docx import Document
from docx.shared import Pt, Cm, RGBColor

# ---------------- explanations shared by several notebooks (matched by the start of the cell) ----------------
COMMON = {
    "import os\nif os.getcwd()": [
        "The notebook opens inside the 'notebooks' folder, but the data is in the project folder.",
        "os.chdir(\"..\") moves one folder up, so paths like \"data/...\" and \"reports/...\" work exactly as in the scripts.",
    ],
    "import os\nos.environ": [
        "The two os.environ lines are set before TensorFlow is loaded.",
        "TF_CPP_MIN_LOG_LEVEL = 3 hides TensorFlow's information messages.",
        "TF_ENABLE_ONEDNN_OPTS = 0 turns off an optional speed-up so the maths is done exactly as in the original script (same results).",
        "Then, like every notebook, it moves from the 'notebooks' folder to the project folder.",
    ],
    "def ccc": [
        "This is the evaluation metric, CCC (Concordance Correlation Coefficient). 1 = perfect, 0 = no agreement.",
        "np.array(...) makes sure both inputs are plain number arrays.",
        "covariance: how much the true and predicted values move together (average of the product of their deviations from their means).",
        "Formula: 2 x covariance / (variance of true + variance of predicted + (difference of the means) squared).",
        "Unlike normal correlation, CCC is also lowered if the predictions are shifted or wrongly scaled.",
        "+ 1e-9 is a tiny number that avoids dividing by zero.",
    ],
    "import numpy as np\n\ndef ccc": None,   # same as "def ccc"
    'df = pd.read_parquet("data/features/noxi_engagement.parquet")\n\n# the first 5': [
        "Loads the feature table made in step 2 (one row per 1-second window).",
        "bookkeeping: the first 5 OpenFace columns are frame number, face id, time stamp, confidence and success flag. They describe the recording, not the person, so they are left out.",
        "The loop keeps every voice_ and face_ column except those 5: 88 voice + 709 face = 797 features.",
        "X = the features as a number table (float32); fillna(0) replaces any missing value with 0.",
        "y = the engagement labels (0 to 1).",
    ],
    "# the 3 sessions of each language": [
        "Lists the 3 sessions (conversations) of each language, sorted.",
        "Fold 1 tests on the 1st session of English, French and German; fold 2 on the 2nd; fold 3 on the 3rd.",
        "In each fold the model is trained on the other 6 conversations, so it is always tested on conversations it has never seen.",
        "This is how we avoid data leakage (neighbouring seconds of one conversation in both training and test).",
    ],
    "def past_mean": [
        "For every row, the mean of the same speaker's last k seconds (including the current one); only the past is used, so it would also work live.",
        "out = an empty table of the same size.",
        "For each speaker: find their rows (np.where), take a rolling mean over k rows (min_periods=1 means the first rows use whatever is available), and write it back.",
        "Used for context features (last 5 s and 10 s) and for smoothing predictions.",
    ],
}

# ---------------- per-notebook information and cell explanations (matched by the start of the cell) ----------------
NB = {
 "01_extract_data": dict(
    purpose="Copies only the needed small files (voice features, face features, engagement labels, language) out of the 14 GB NoXi zips.",
    io="Input: train.zip and 027.zip in Downloads.  Output: data/noxi/<session>/ (11 files per conversation).",
    result="9 conversation folders, 11 files each.",
    cells={
        "import zipfile": [
            "zipfile is Python's library for reading .zip files.",
            "KEEP lists the file endings we want: .audio.egemapsv2 (voice), .openface2 (face), .engagement.annotation.csv (labels), language.annotation.csv. Each feature has a .stream header and a .stream~ data file.",
            "ZIPS is the list of the two downloaded NoXi zips.",
        ],
        "for zip_path in ZIPS": [
            "Opens each zip and goes through every file name inside it (z.namelist()).",
            "name.endswith(KEEP) is True if the name ends with one of the wanted endings.",
            "If the file is wanted and not already extracted, z.extract copies it into data/noxi.",
            "Video, audio and big embedding files are skipped, which saves about 90% of the space.",
        ],
        "for session in sorted": ["Prints each conversation folder and how many files it has (should be 11)."],
    },
    viva=["Why not extract everything? - The zips are 14 GB, mostly raw video; we only need the feature files.",
          "What is a .stream and a .stream~ file? - The header (shape and type of the numbers) and the binary numbers."]),
 "02_build_features": dict(
    purpose="Lines up voice, face and engagement for every person, cuts the recording into 1-second windows of 25 frames, and averages each window into one row.",
    io="Input: data/noxi/.  Output: the feature table (17,174 rows) and the 25-frame sequences (compared with the saved files).",
    result="17,174 windows; 'True, True' = identical to the files saved by the script.",
    cells={
        "import xml": ["ElementTree reads the small XML header files; NumPy does the number work; pandas builds the table."],
        "def read_stream": [
            "Reads the header: dim = how many numbers each frame has (88 for voice, 714 for face).",
            "Reads all numbers from the .stream~ file as 32-bit or 64-bit floats, depending on the header type.",
            "frames = total numbers / numbers per frame; reshape turns the long list into a table of frames x features.",
        ],
        "def read_labels": [
            "read_labels: reads the engagement CSV (one value per frame, 25 per second). errors=\"coerce\" turns invalid values into NaN (missing) instead of crashing.",
            "read_language: the language file looks like 0.00;904.00;French;1.00 - split(\";\")[2] takes the third part, the language.",
        ],
        "rows = []": [
            "rows will hold one dictionary per 1-second window; sequences keeps the 25 raw frames of each window for the CNN/RNN/Transformer.",
            "Loop over every session folder and both roles (expert and novice).",
            "n = the shortest of the three streams; the streams can differ by a frame or two, so all are cut to the same length.",
            "for w in range(n // 25): every full second. start and end are the 25 frames of that second.",
            "np.nanmean(label[start:end]) = the average engagement of that second; if there is no valid label (NaN) the second is skipped.",
            "voice_mean and face_mean = the average of each feature over the 25 frames; they become columns voice_0..voice_87 and face_0..face_713.",
            "engagement, language, session and role are added so we know where each row came from.",
            "frames = the 25 raw frames (voice and face side by side); nan_to_num replaces missing values with 0.",
            "At the end, the rows become a table (DataFrame) and the sequences one 3-D array (windows x 25 x 802).",
        ],
        'print(df["language"]': ["How many windows each language has: French 6,568, German 5,630, English 4,976."],
        "saved = pd.read_parquet": ["Loads the files saved by the original script and checks they are the same (True, True)."],
    },
    viva=["Why 1-second windows? - 25 frames per second is very noisy; one second is stable and still fine-grained.",
          "Why skip windows without a label? - We cannot train or test on a second with no engagement value."]),
 "03_eda": dict(
    purpose="Looks at the data before building models: amounts, averages, a statistical test, charts, correlations and PCA.",
    io="Input: the feature table.  Output: numbers and charts on screen.",
    result="ANOVA F = 84.67 (languages differ slightly); experts 0.659 vs novices 0.506; voice correlates more with engagement (0.391) than face (0.187).",
    cells={
        "import numpy": ["Imports for numbers, tables, charts (matplotlib, seaborn), the ANOVA test (scipy) and PCA.",
                         "Loads the table and lists all voice_ and face_ columns."],
        'print(df["language"].value_counts': ["Windows per language and the average engagement per language."],
        "english = df[": ["Takes the engagement values of each language separately.",
                          "stats.f_oneway runs a one-way ANOVA: are the three averages different? p < 0.05 means yes."],
        'sns.histplot': ["Histogram of engagement, a box plot per language, and a box plot per role (expert vs novice).",
                         "plt.show() displays each chart."],
        "corr = df[feature_cols]": ["corrwith: correlation of every feature with engagement; abs() ignores the sign; sorted from strongest.",
                                    "The bar chart shows the 10 features most related to engagement."],
        "voice_cols = []": ["Splits the features into voice and face, then prints the average correlation of each group."],
        "X = StandardScaler": ["StandardScaler gives every feature mean 0 and spread 1.",
                               "PCA squeezes all features into 2 numbers so each window can be drawn as a point, coloured by language."],
    },
    viva=["What is ANOVA? - A test of whether the means of several groups differ.",
          "What is PCA? - A way to reduce many features to a few while keeping most of the variation."]),
 "05_cross_lingual": dict(
    purpose="The main research question: train on one language and test on another, for all pairs.",
    io="Input: the feature table.  Output: a 3x3 matrix of CCC values.",
    result="Within-language 0.556, cross-language 0.393: a 29% drop. 'same as saved: True'.",
    cells={
        "import numpy as np\nimport pandas": ["Imports and loads the table, keeps the 797 behaviour features, and lists the three languages."],
        "def train_and_test": [
            "StandardScaler is fitted on the training part only (fit_transform) and then applied to the test part (transform), so no test information leaks into training.",
            "A Random Forest with 120 trees is trained on the training rows and tested on the test rows.",
            "Returns the CCC between the true and predicted engagement.",
        ],
        "result = pd.DataFrame": [
            "An empty 3x3 table: rows = training language, columns = test language.",
            "Same language (a == b): hold out one session at a time, train on the other two sessions of that language, and average the 3 scores.",
            "Different language: train on all windows of language a and test on all windows of language b.",
        ],
        "within = np.mean": ["within = average of the diagonal (same language); cross = average of the 6 other cells.",
                             "drop = how much is lost in a new language, in percent.",
                             "Finally compares the matrix with the one saved by the script."],
    },
    viva=["Why leave one session out on the diagonal? - Otherwise the model would be tested on a conversation it trained on.",
          "Why is French -> English so low (0.092)? - Only 3 conversations per language; the French speakers' style may not match the English ones."]),
 "14_session_eval": dict(
    purpose="Tests the four classic ML models and the ANN on unseen conversations (3 folds); this fixed the data leakage of the earlier random split.",
    io="Input: the feature table.  Output: CCC of every model.",
    result="Gradient Boosting 0.633, Random Forest 0.631, XGBoost 0.620, ANN 0.591, Linear Regression 0.240 (all equal to the saved results).",
    cells={
        "import numpy as np\nimport pandas as pd\nfrom tensorflow": ["Imports: TensorFlow/Keras for the ANN, scikit-learn for scaling and the classic models, XGBoost."],
        "def make_models": [
            "make_models returns a fresh copy of the 4 classic models: Linear Regression, Random Forest (100 trees), Gradient Boosting (300 rounds) and XGBoost (300 trees, depth 6, learning rate 0.1).",
            "make_ann builds the ANN: 797 inputs -> 256 -> 128 -> 1, ReLU activations, dropout 0.1 (randomly switches off 10% of neurons to prevent overfitting).",
            "set_random_seed(42) makes the result repeatable. Adam optimiser with learning rate 0.001; loss = MSE (mean squared error).",
        ],
        "scores = {": [
            "For each fold: test = rows of the 3 test conversations; train = all other rows.",
            "The scaler learns from the training rows only and is applied to both.",
            "Each classic model is trained (fit) and tested (predict); the CCC is stored.",
            "The ANN uses the same scaled data limited to -5..5 (np.clip): a few extreme values in unseen conversations would otherwise break it. 30 epochs, batches of 128.",
        ],
        "saved = pd.read_csv": ["Prints the mean and standard deviation over the 3 folds, next to the value saved by the script."],
    },
    viva=["Why did the scores drop from 0.90 to 0.63? - The random split let the model see neighbouring seconds of the test conversation (leakage).",
          "Why does Gradient Boosting win? - Small data and already meaningful features suit tree models."]),
 "15_session_sequence": dict(
    purpose="Tests the deep sequence models - CNN, SimpleRNN, LSTM, GRU and our own Transformer - which read the 25 frames of each second.",
    io="Input: the 25-frame sequences.  Output: CCC of every model.",
    result="Transformer 0.583, CNN 0.577, GRU 0.528, LSTM 0.512, SimpleRNN 0.510.",
    cells={
        "import numpy as np\nimport pandas as pd\nfrom tensorflow": ["Imports TensorFlow/Keras and the scaler."],
        "df = pd.read_parquet": ["Loads the labels and the 25-frame sequences (windows x 25 x 802).",
                                 "np.delete removes columns 88-92 (the 5 bookkeeping columns) -> 797 features per frame."],
        "def head": ["The same ending for every model: dropout 0.1, a Dense layer of 64 neurons with ReLU, and one output (the engagement)."],
        "def cnn": ["CNN in VGG style: two convolution layers with 32 filters, max pooling, then two with 64 filters and max pooling.",
                    "Conv1D slides a filter of size 3 along the 25 frames to find short patterns; padding='same' keeps the length; pooling halves it.",
                    "Flatten turns the result into one vector for the head."],
        "def rnn": ["SimpleRNN, LSTM and GRU each read the 25 frames one by one with 128 units, then the head.",
                    "LSTM has 3 gates and a memory cell; GRU has 2 gates; the simple RNN has none (it forgets more)."],
        "class PositionalEncoding": ["Self-attention does not know the order of the frames.",
                                     "This layer adds a learned vector (25 positions x 64 numbers) to the input so the model knows which frame is which."],
        "def encoder_block": ["encoder_block: multi-head self-attention (4 heads) lets every frame look at every other frame; then add & normalise (residual connection + layer normalisation); then a feed-forward part (128 -> 64) with dropout; add & normalise again.",
                              "transformer: each frame -> 64 numbers (Dense), add positions, 2 encoder blocks, average over the 25 frames, then the head."],
        "scores = {": ["For each fold: the scaler learns from the training frames (reshape to rows of 797), values limited to -5..5, reshaped back to 25 x 797.",
                       "Each model is built with the same seed, compiled (Adam, MSE), trained for 20 epochs and tested."],
        "saved = pd.read_csv": ["Mean CCC per model next to the value saved by the script."],
    },
    viva=["What is self-attention? - Each frame scores how relevant every other frame is and mixes them accordingly.",
          "Why positional encoding? - Attention alone has no sense of order.",
          "Why did RNNs do worst? - Small data and only 25 frames; their results also varied a lot between folds."]),
 "16_autoencoder": dict(
    purpose="An autoencoder compresses the 797 features into 32 numbers and rebuilds them (no labels needed); the 32 numbers are then used to predict engagement.",
    io="Input: the feature table.  Output: CCC with a dense head and with XGBoost.",
    result="Autoencoder + XGBoost 0.577, + dense head 0.564 (equal to the saved results).",
    cells={
        "import numpy as np\nimport pandas as pd\nfrom tensorflow": ["Imports Keras, the scaler and XGBoost."],
        "def make_autoencoder": ["Encoder: 797 -> 256 -> 32 (the 'code'). Decoder: 32 -> 256 -> 797.",
                                 "autoencoder = the full model (input -> rebuilt input); encoder = only the first half (input -> 32 numbers)."],
        "scores = {": [
            "Scale on the training rows, limit to -5..5.",
            "1) The autoencoder is trained with the input also as the target (X_train, X_train): it learns to rebuild its input. The reconstruction error on the test data is printed.",
            "2) The encoder is frozen (trainable = False) and a small head (64 neurons, dropout) is trained on top to predict engagement.",
            "3) XGBoost is trained on the same 32-number codes.",
        ],
        "saved = pd.read_csv": ["Mean CCC of both versions next to the saved values."],
    },
    viva=["Is an autoencoder supervised? - The first part is unsupervised: it only rebuilds its input, no labels.",
          "Why did it not beat the original features? - Compressing 797 numbers to 32 loses some useful information."]),
 "17_ablation": dict(
    purpose="Ablation: the same XGBoost model with voice only, face only, and both - which signal works across languages?",
    io="Input: the feature table.  Output: unseen-conversation, within-language and cross-language CCC for each input.",
    result="Voice 0.652 (drop 12%), face 0.397 (drop 55%), both 0.631 (drop 21%).",
    cells={
        "import numpy as np\nimport pandas as pd\nfrom sklearn": ["Imports the scaler and XGBoost."],
        "def train_and_test": ["Same as in step 5 but with XGBoost and only the columns given (voice, face or both)."],
        'df = pd.read_parquet("data/features/noxi_engagement.parquet")\nbookkeeping': [
            "Builds the list of 88 voice columns and 709 face columns (without the 5 bookkeeping columns).",
            "inputs: the three versions to compare."],
        "for name, cols in inputs": [
            "unseen: the 3 folds (whole conversations held out).",
            "within: inside each language, leave one session out.",
            "cross: train on one language, test on another (6 pairs).",
            "drop = how much is lost in a new language, in percent.",
        ],
        "print(pd.read_csv": ["The results saved by the script, for comparison."],
    },
    viva=["What is an ablation study? - Removing or isolating parts of the input to see what each contributes.",
          "Why does face transfer badly? - Facial expression habits differ between cultures (also reported by MultiMediate'24)."]),
 "19_pretrained_features": dict(
    purpose="Reads the features made by six large pretrained Transformers (shipped with NoXi) and averages them over the same 1-second windows as step 2.",
    io="Input: the NoXi zips and data/noxi/.  Output: one feature table per model (compared with the saved files).",
    result="17,174 windows for each of: XLM-RoBERTa (768), w2v-BERT 2.0 (1024), CLIP (512), DINOv2 (768), Swin (768), VideoMAE (1408). All 'True'.",
    cells={
        "import zipfile": ["EMBEDDINGS maps our short names to the file names inside the zip: XLM-RoBERTa (text), w2v-BERT 2.0 (audio), CLIP, DINOv2, Swin, VideoMAE (video).",
                           "Warnings about averaging empty windows are hidden."],
        "def read_stream": ["read_stream reads an already-extracted file (as in step 2); read_from_zip reads the same format straight from the zip without extracting it."],
        "train_zip = zipfile": ["Opens the two zips: session 027 is in its own zip, the others in train.zip."],
        "result = {}": ["For every session and role: first find exactly the windows kept in step 2 (same voice/face/label check).",
                        "Then, for each pretrained model: read its stream (25 vectors per second), average the 25 vectors of each kept window.",
                        "If the embedding stream is shorter than the recording, that window gets NaN, later replaced with 0."],
        "for key in EMBEDDINGS": ["Joins the parts and compares each with the saved file (True = identical)."],
    },
    viva=["Did you train these Transformers? - No. They were trained by their authors on huge datasets; we only use their outputs (frozen).",
          "Why average 25 vectors? - To get one vector per 1-second window, like our own features."]),
 "20_pretrained_transformers": dict(
    purpose="Trains a small model (XGBoost or a dense network) on top of each frozen pretrained Transformer's features; this is transfer learning by feature extraction.",
    io="Input: the pretrained features.  Output: CCC and cross-language drop per pretrained model.",
    result="Best single model w2v-BERT 2.0: 0.631 with 0% language drop; w2v-BERT + VideoMAE: 0.663.",
    cells={
        "import numpy as np\nimport pandas as pd\nfrom tensorflow": ["SETS lists the 7 inputs: six single pretrained models and the w2v-BERT + VideoMAE combination."],
        "def xgb_score": ["xgb_score: scale on training rows, train XGBoost, return CCC on the test rows.",
                          "dense_score: the same 256-128 dense network as the ANN (dropout 0.1, 30 epochs), on scaled values limited to -5..5."],
        'df = pd.read_parquet("data/features/noxi_engagement.parquet", columns=["engagement"': ["Loads only the labels, languages and sessions (the features come from the pretrained files)."],
        "for name, files in SETS": ["Loads the feature file(s) of this pretrained model (two are joined side by side for the combination).",
                                    "3 folds with both heads; then within-language and cross-language with XGBoost; then the drop in percent."],
        "print(pd.read_csv": ["The results saved by the script, for comparison."],
    },
    viva=["What does 'frozen' mean? - The pretrained model's weights are not changed; only the small head is trained.",
          "Why not fine-tune? - No GPU, and 9 conversations are too few: it would overfit."]),
 "24_fusion": dict(
    purpose="The best model: voice features + w2v-BERT 2.0 speech + VideoMAE video features together, with past context (last 5 s and 10 s), predicted by Gradient Boosting.",
    io="Input: the feature table and the pretrained features.  Output: CCC of the fusion models and the cross-language test.",
    result="Gradient Boosting with fusion + context: CCC 0.777, cross-language drop 1% (the best result of the project).",
    cells={
        "import numpy as np\nimport pandas as pd\nfrom tensorflow": ["Imports Keras (dense head), the scaler and Gradient Boosting."],
        'df = pd.read_parquet("data/features/noxi_engagement.parquet")\nvoice': [
            "speaker = session + role (e.g. 001_expert), so context is computed per person.",
            "fused = 88 voice + 1024 w2v-BERT + 1408 VideoMAE = 2,520 features side by side (np.hstack).",
            "with_context = [now, mean of the last 5 s, mean of the last 10 s] = 7,560 features."],
        "def gb_predict": ["gb_predict: scale, train Gradient Boosting (300 rounds), predict.",
                          "dense_predict: the 256-128 dense network on scaled values limited to -5..5."],
        "for head_name, predict": ["Every head (Gradient Boosting, dense) on every input (1 s, with context), 3 folds.",
                                   "The raw predictions are scored, and also smoothed (mean of the last 5 s of predictions of the same speaker)."],
        "within = []": ["The cross-language test for the best model: within-language (leave one session out) vs train-on-A, test-on-B."],
        "print(pd.read_csv": ["The results saved by the script, for comparison."],
    },
    viva=["What is fusion? - Combining features from different sources (voice, speech model, video model) into one input.",
          "Why does context help? - Engagement builds up over several seconds, so the past is informative.",
          "Why only the past? - So the model could run live; it never uses future seconds."]),
 "26_significance": dict(
    purpose="Checks that the improvements are real and not luck: compares models speaker by speaker with statistical tests.",
    io="Input: the feature table and pretrained features.  Output: differences, 95% intervals and p-values.",
    result="Best model better than the baseline for 15 of 18 speakers, Holm p = 0.006; all three comparisons significant.",
    cells={
        "import numpy as np\nimport pandas as pd\nfrom scipy": ["Imports the Wilcoxon test (scipy), the scaler and Gradient Boosting."],
        'df = pd.read_parquet("data/features/noxi_engagement.parquet")\nbookkeeping': ["Loads the table, the 797 behaviour columns, the 88 voice columns, labels, speakers and sessions."],
        "own = df[cols]": ["The three models to compare: A = baseline (voice + face, 1 s), B = A + context, C = best (fusion + context)."],
        "predictions = {}": ["For each model and each fold: train on the other conversations and predict the test conversations.",
                            "In the end every row has exactly one prediction from a model that never saw its conversation."],
        "per_speaker = pd.DataFrame": ["CCC computed separately for each of the 18 speakers (each speaker is one person in one conversation).",
                                       "per_conversation: the average of the 2 speakers of each conversation (9 values) - a stricter check."],
        "rng = np.random": ["For each pair (C vs A, B vs A, C vs B) and each level: the difference per speaker/conversation.",
                            "Bootstrap: resample the differences 10,000 times to get a 95% interval; if it does not include 0, the gain is real.",
                            "better = how many speakers improved; Wilcoxon signed-rank test gives the p-value."],
        'res["p_holm"]': ["Holm correction: when several tests are done, the chance of a lucky result grows.",
                          "Sort the 3 p-values; multiply the smallest by 3, the next by 2, the last by 1 (never letting them go down). p < 0.05 = significant."],
        "print(pd.read_csv": ["The results saved by the script, for comparison."],
    },
    viva=["Why test per speaker? - 3 folds are too few for a test; 18 speakers give enough paired values.",
          "What is a p-value? - The chance of seeing a difference this big if there were really no difference.",
          "Why Holm correction? - Several comparisons increase the chance of a false positive."]),
}


def explanation(nb_key, code):
    for prefix, lines in NB[nb_key]["cells"].items():
        if code.startswith(prefix):
            return lines
    for prefix, lines in COMMON.items():
        if code.startswith(prefix) or (prefix == "def ccc" and "def ccc" in code):
            return lines if lines is not None else COMMON["def ccc"]
    return None


doc = Document()
for side in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
    setattr(doc.sections[0], side, Cm(2))
doc.styles["Normal"].font.name = "Calibri"; doc.styles["Normal"].font.size = Pt(10.5)
for h in ("Heading 1", "Heading 2"):
    doc.styles[h].font.color.rgb = RGBColor(0, 0, 0)

t = doc.add_paragraph().add_run("Notebook Code Explanation"); t.bold, t.font.size = True, Pt(18)
doc.add_paragraph("Cross-Lingual Prediction of Engagement from Non-Verbal Behaviour")
doc.add_paragraph("Each of the 12 main notebooks: what the step does, every code cell, and a plain explanation of the "
                  "code. The notebooks give the same results as the original scripts in src/.")

missing = []
for key, info in NB.items():
    nb = nbformat.read(f"notebooks/{key}.ipynb", as_version=4)
    doc.add_page_break()
    doc.add_heading(f"Step {key.split('_')[0]}: {key.split('_', 1)[1].replace('_', ' ').title()}", 1)
    for label, text in (("What it does: ", info["purpose"]), ("Input / output: ", info["io"]), ("Result: ", info["result"])):
        p = doc.add_paragraph(); p.add_run(label).bold = True; p.add_run(text)
    n = 0
    for cell in nb.cells:
        if cell.cell_type != "code":
            continue
        n += 1
        doc.add_heading(f"Cell {n}", 2)
        tbl = doc.add_table(rows=1, cols=1); tbl.style = "Table Grid"
        cp = tbl.rows[0].cells[0].paragraphs[0]
        for i, line in enumerate(cell.source.split("\n")):
            r = cp.add_run(line); r.font.name = "Consolas"; r.font.size = Pt(8.5)
            if i < len(cell.source.split("\n")) - 1:
                r.add_break()
        lines = explanation(key, cell.source)
        if lines is None:
            missing.append(f"{key} cell {n}")
            lines = ["(see the note above this cell in the notebook)"]
        for line in lines:
            doc.add_paragraph(line, style="List Bullet")
    doc.add_heading("Likely viva questions", 2)
    for q in info["viva"]:
        doc.add_paragraph(q, style="List Bullet")

doc.save("Notebook_Code_Explanation.docx")
print("saved Notebook_Code_Explanation.docx | cells without an explanation:", missing or "none")
