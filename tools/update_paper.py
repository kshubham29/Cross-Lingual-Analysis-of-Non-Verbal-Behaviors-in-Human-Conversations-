"""Rewrites Research_Paper_Draft.docx with the session-wise results -> Research_Paper_Draft_v2.docx.
Keeps the IEEE layout of the draft; text and tables are filled from reports/*.csv."""
import os
import copy
import json
import pandas as pd
from docx import Document
from docx.text.paragraph import Paragraph
from docx.table import Table

R = "reports"
J = json.load(open(os.path.join(R, "results_summary.json")))
d = Document("Research_Paper_Draft.docx")
P = list(d.paragraphs)          # fixed references before anything is inserted
T = list(d.tables)
f3 = lambda x: f"{x:.3f}"
NAME = {"GradientBoosting": "Gradient boosting", "RandomForest": "Random forest", "XGBoost": "XGBoost",
        "ANN (MLP)": "MLP (tuned)", "LinearRegression": "Linear regression", "CNN_VGG": "CNN, VGG-style",
        "SimpleRNN": "Simple RNN", "LSTM": "LSTM", "GRU": "GRU", "Transformer": "Transformer",
        "Autoencoder + XGBoost": "Autoencoder + XGBoost", "Autoencoder + dense head": "Autoencoder + dense head"}
OLD = {"LinearRegression": 0.284, "RandomForest": 0.885, "GradientBoosting": 0.901, "XGBoost": 0.906, "ANN (MLP)": 0.881}


# ---------- helpers ----------
def set_text(p, text):
    runs = p.runs
    runs[0].text = text
    for r in runs[1:]:
        r._r.getparent().remove(r._r)


def set_lead(p, lead, text):
    runs = p.runs
    runs[0].text, runs[1].text = lead, text
    for r in runs[2:]:
        r._r.getparent().remove(r._r)


def add_after(anchor, template, text=None, lead=None):
    el = copy.deepcopy(template._p)
    anchor._p.addnext(el)
    p = Paragraph(el, anchor._parent)
    if lead is not None:
        set_lead(p, lead, text)
    elif text is not None:
        set_text(p, text)
    return p


def cell_text(cell, text):
    p = cell.paragraphs[0]
    if p.runs:
        set_text(p, str(text))
    else:
        p.add_run(str(text))


def fill(tbl, rows):
    trs = tbl._tbl.tr_lst
    while len(trs) < len(rows):
        trs[-1].addnext(copy.deepcopy(trs[-1]))
        trs = tbl._tbl.tr_lst
    while len(trs) > len(rows):
        tbl._tbl.remove(trs[-1])
        trs = tbl._tbl.tr_lst
    for r, row in zip(tbl.rows, rows):
        for c, v in zip(r.cells, row):
            cell_text(c, v)


def copy_table_after(anchor, tbl):
    el = copy.deepcopy(tbl._tbl)
    anchor._p.addnext(el)
    return Table(el, anchor._parent)


# ---------- numbers ----------
flat = {r["model"]: r for r in J["flat"]}
seq = {r["model"]: r for r in J.get("sequence", [])}
ae = {r["model"]: r for r in J.get("autoencoder", [])}
master = [r for r in J["master"] if r["model"] != "LinearRegression"]
best = master[0]
abl = {r["modality"]: r for r in J["ablation"]}
cm, langs = J["cross"]["matrix"], J["cross"]["langs"]
diag = sum(cm[i][i] for i in range(3)) / 3
off = (sum(map(sum, cm)) - 3 * diag) / 6
drop = round(100 * (diag - off) / diag)
v, fc, both = abl["voice"], abl["face"], abl["both"]
seq_sorted = sorted(seq.values(), key=lambda r: -r["ccc"])
tr = pd.read_csv(os.path.join(R, "transfer_results.csv"))
has_tr = "fraction" in tr.columns
if has_tr:
    tf = tr.groupby("fraction")[["n_adapt", "zero_shot", "head_only", "fine_tune", "scratch"]].mean()
    full = tf.loc[1.0]
    best_adapt = max(full.head_only, full.fine_tune)
    best_name = "head-only adaptation" if full.head_only >= full.fine_tune else "fine-tuning"
ann_params = 797 * 256 + 256 + 256 * 128 + 128 + 129
flat_mae = pd.read_csv(os.path.join(R, "session_flat.csv")).groupby("model")["mae"].mean()
seq_params = (pd.read_csv(os.path.join(R, "session_sequence.csv")).groupby("model")["params"].first()
              if os.path.exists(os.path.join(R, "session_sequence.csv")) else {})

# ---------- title block, abstract, introduction ----------
set_lead(P[4], "Abstract", (
    "—Automatic engagement estimation is used in tutoring systems, virtual agents and video-mediated meetings, yet engagement "
    "models are almost always trained and tested within one language. We ask how much performance survives when a model meets "
    "speakers of a language it has never seen, and which non-verbal channel carries across. On the English, French and German "
    "sessions of the NoXi corpus we predict continuous engagement from 88 eGeMAPS voice descriptors and 709 OpenFace facial "
    "features, aggregated into 17,174 one-second windows, with no transcripts. We first show that the common random window-level "
    "split leaks conversation identity: gradient boosting drops from a concordance correlation coefficient (CCC) of 0.901 to "
    f"{f3(flat['GradientBoosting']['ccc'])} when whole conversations are held out. Under this session-disjoint protocol, "
    f"{NAME[best['model']].lower()} is the strongest of twelve models ({f3(best['session_ccc'])}), ahead of an MLP, CNN, simple RNN, "
    "LSTM, GRU, Transformer encoder and autoencoder. Moving to a new language lowers CCC from "
    f"{f3(diag)} to {f3(off)}, a relative loss of {drop}%. An ablation locates the loss: voice alone predicts engagement better than "
    f"voice and face together ({f3(v['session_ccc'])} vs. {f3(both['session_ccc'])}) and loses only {v['drop_pct']:.0f}% across "
    f"languages, whereas facial features lose {fc['drop_pct']:.0f}%."
    + (f" Pretraining a CNN on two languages and adapting it with one conversation of the third reaches {f3(best_adapt)}, "
       f"against {f3(full.scratch)} when the same data is used from scratch." if has_tr else "")))

set_text(P[10], (
    "This paper measures that loss directly. Using the English, French and German sessions of NoXi, we (i) build a language-labelled "
    "table of one-second windows described only by acoustic and facial features; (ii) show that random window-level splits inflate "
    "scores and evaluate every model on held-out conversations instead; (iii) compare classical regressors with eight deep "
    "architectures under that protocol; (iv) train on each language and test on every other; (v) separate the contribution of voice "
    "and face with an ablation; and (vi) test whether transfer learning recovers the cross-lingual loss. "
    f"A model moved to an unseen language loses {drop}% of its concordance, and most of that loss comes from the face channel."))

# ---------- dataset ----------
set_text(P[22], (
    "For each participant we use the 88 eGeMAPS descriptors [16] and the OpenFace 2.0 outputs [18] supplied with the corpus, both at "
    "25 frames per second. Five OpenFace columns (frame number, face identifier, timestamp, detection confidence and success flag) "
    "describe the recording rather than behaviour and are removed, leaving 709 facial features. No speech content or transcript is "
    "used: because words differ between languages, any lexical feature would confound the cross-lingual comparison."))
set_text(P[24], (
    "The voice, face and engagement streams are aligned and truncated to their common length, then segmented into non-overlapping "
    "one-second windows of 25 frames. For each window we keep (a) the mean of every feature, a 797-dimensional vector used by the "
    "classical models, the MLP and the autoencoder, and (b) the full 25 × 797 frame sequence used by the convolutional, recurrent and "
    "attention models. The label is the mean engagement over the window. Invalid annotation entries are converted to missing values, "
    "windows with no valid label are discarded, and each window is tagged with its language, session and participant role. The "
    "result is 17,174 windows (Table I)."))

# ---------- methodology ----------
set_text(P[36], (
    "We train linear regression, a random forest (100 trees), histogram-based gradient boosting (300 iterations) and XGBoost [24] "
    "(300 trees, depth 6, learning rate 0.1, row and column subsampling 0.8), all on standardised inputs."))
set_text(P[38], (
    "All networks are implemented in TensorFlow/Keras, trained with Adam [25] on mean squared error and regularised with dropout [26]. "
    "The output layer is linear because the target is continuous. Inputs are standardised on the training data and then clipped to "
    "[−5, 5]: a small fraction of values in unseen sessions (about 0.02%) lie hundreds to thousands of standard deviations from the "
    "training mean, which leaves tree models unaffected but destabilises neural networks."))
set_lead(P[39], "Multilayer perceptron (MLP). ", (
    "Two hidden layers of 256 and 128 ReLU units over the window mean. Dropout (0.1), learning rate (10⁻³), layer widths and optimiser "
    "were selected by a grid search over 13 configurations on a validation split during development."))
set_lead(P[40], "Convolutional networks. ", (
    "Because the input is a time series of feature vectors rather than an image, we adapt three classic CNN designs to "
    "one-dimensional convolution along the 25-frame axis: a LeNet-style network [27], a VGG-style network [28] with two stacked "
    "kernel-3 convolutions per block, and a ResNet-style network [29] with residual blocks and batch normalisation. The VGG-style "
    "network, the best of the three in development, represents the CNN family in the final comparison."))
set_lead(P[41], "Recurrent networks. ", (
    "A simple RNN, a long short-term memory network [30] and a gated recurrent unit network, each with 128 units, read the 25 frames "
    "in order; the final hidden state feeds a 64-unit dense layer and the output."))
set_lead(P[42], "Transformer. ", (
    "Each frame is projected to 64 dimensions and a learned positional encoding is added. Two encoder blocks follow, each with "
    "four-head self-attention, a 128-unit feed-forward layer, residual connections and layer normalisation [31]. Frames are averaged "
    "before a dense output head."))
p_ae = add_after(P[42], P[42], lead="Autoencoder. ", text=(
    "An encoder (797 → 256 → 32) and a mirrored decoder are trained without labels to reconstruct the input. The encoder is then "
    "frozen and either a small dense head or XGBoost predicts engagement from the 32-dimensional code."))

set_text(P[43], "D. Evaluation Protocols")
set_text(P[44], (
    "Unseen conversations. Every model is evaluated with three session-disjoint folds: each fold holds out one complete conversation "
    "per language (three conversations, both participants) and trains on the remaining six. We report the mean and standard "
    "deviation of CCC over the folds. For comparison, the classical models and the MLP were also scored on a random 80/20 split of "
    "windows, which lets neighbouring seconds of the same conversation fall on both sides. "
    "Cross-lingual transfer. A random forest is trained on all windows of one language and tested on all windows of another, for every "
    "ordered pair; for the diagonal we use leave-one-session-out within the language. "
    "Modality ablation. The same XGBoost model is trained on voice only (88), face only (709) and both (797), under both protocols."))
set_text(P[46], (
    "For each target language, the tuned LeNet-style CNN is pretrained on the other two languages, with the scaler fitted on the "
    "source languages only. One conversation of the target language is used for adaptation and its other two for testing, so "
    "adaptation and test never share a session; each conversation takes a turn, and 10%, 25%, 50% and 100% of it are tried. Four "
    "conditions are compared: zero-shot (the pretrained model unchanged); head-only (convolutional layers frozen, dense layers "
    "retrained); fine-tuning (all layers retrained at a learning rate of 10⁻⁴); and scratch (the same network trained on the "
    "adaptation data alone)."))

# ---------- results ----------
set_text(P[48], "A. Random Split Versus Unseen Conversations")
set_text(P[49], (
    f"On the random split every non-linear model exceeds 0.88 CCC (Table II). Holding out whole conversations removes 0.25 to 0.29 "
    f"from each: the best model, gradient boosting, falls from 0.901 to {f3(flat['GradientBoosting']['ccc'])}, and the tuned MLP from "
    f"0.881 to {f3(flat['ANN (MLP)']['ccc'])}. Consecutive one-second windows of one conversation are nearly identical, so a random "
    "split rewards recognising the speaker rather than reading engagement. All following results use held-out conversations. "
    f"Linear regression is unstable across folds ({f3(flat['LinearRegression']['ccc'])} ± {f3(flat['LinearRegression']['std'])})."))
set_text(P[51], "CLASSICAL MODELS AND MLP: RANDOM SPLIT VS. UNSEEN CONVERSATIONS")
order = ["GradientBoosting", "RandomForest", "XGBoost", "ANN (MLP)", "LinearRegression"]
fill(T[1], [["Model", "Random split", "Unseen (mean ± sd)", "r", "MAE"]] +
     [[NAME[m], f3(OLD[m]), f"{f3(flat[m]['ccc'])} ± {f3(flat[m]['std'])}", f3(flat[m]["pearson"]),
       f3(flat_mae[m])] for m in order])

set_text(P[54], (
    "Table III compares the deep models on the same folds. "
    + (f"Among the sequence models, the {NAME[seq_sorted[0]['model']]} is best ({f3(seq_sorted[0]['ccc'])}) and the "
       f"{NAME[seq_sorted[-1]['model']]} weakest ({f3(seq_sorted[-1]['ccc'])}). " if seq_sorted else "")
    + f"The MLP on the window mean reaches {f3(flat['ANN (MLP)']['ccc'])}, and the autoencoder keeps most of the signal after a 25-fold "
    f"compression ({f3(ae['Autoencoder + XGBoost']['ccc'])} with XGBoost on the 32-dimensional code). None of the deep models "
    f"exceeds {NAME[best['model']].lower()} ({f3(best['session_ccc'])})."))
set_text(P[56], "DEEP MODELS ON UNSEEN CONVERSATIONS (3 SESSION-DISJOINT FOLDS)")
deep_rows = [["Model", "Input", "Params", "CCC (mean ± sd)"]]
for r in seq_sorted:
    deep_rows.append([NAME[r["model"]], "25×797", f"{int(seq_params[r['model']]):,}", f"{f3(r['ccc'])} ± {f3(r['std'])}"])
deep_rows.append(["MLP (tuned)", "797", f"{ann_params:,}", f"{f3(flat['ANN (MLP)']['ccc'])} ± {f3(flat['ANN (MLP)']['std'])}"])
for m in ("Autoencoder + XGBoost", "Autoencoder + dense head"):
    deep_rows.append([NAME[m], "797→32", "–", f"{f3(ae[m]['ccc'])} ± {f3(ae[m]['std'])}"])
fill(T[2], deep_rows)

fr_en, de_fr, fr_fr = cm[1][0], cm[2][1], cm[1][1]
set_text(P[59], (
    f"Within-language CCC (the diagonal of Table IV) averages {f3(diag)}, while cross-language CCC averages {f3(off)}, a relative drop "
    f"of {drop}%. Transfer is asymmetric: a model trained on French transfers poorly to English ({f3(fr_en)}), whereas a model trained "
    f"on German reaches {f3(de_fr)} on French, above French's own leave-one-session-out score ({f3(fr_fr)}), plausibly because it is "
    "trained on three sessions rather than two."))
fill(T[3], [["Train \\ Test"] + langs] + [[langs[i]] + [f3(x) for x in cm[i]] for i in range(3)])

# new subsection D: ablation, with its own table
h_abl = add_after(P[62], P[58], text="D. Modality Ablation")     # P[62] = blank line after Table IV
p_abl = add_after(h_abl, P[59], text=(
    f"Voice alone is the strongest input (Table V): {f3(v['session_ccc'])} on unseen conversations, against {f3(fc['session_ccc'])} for "
    f"the face and {f3(both['session_ccc'])} for both, so adding 709 facial features to 88 acoustic ones slightly hurts. The modalities "
    f"also differ in how well they survive a new language: voice loses {v['drop_pct']:.0f}% (from {f3(v['within_ccc'])} to "
    f"{f3(v['cross_ccc'])}), the face {fc['drop_pct']:.0f}% (from {f3(fc['within_ccc'])} to {f3(fc['cross_ccc'])}). Most of the "
    "cross-lingual loss of the combined model therefore comes from the facial channel."))
c1 = add_after(p_abl, P[60], text="TABLE V")
c2 = add_after(c1, P[61], text="MODALITY ABLATION (XGBOOST, HELD-OUT CONVERSATIONS)")
t_abl = copy_table_after(c2, T[4])
fill(t_abl, [["Input", "Feat.", "Unseen", "Within", "Cross", "Drop"]] +
     [[m, int(abl[m]["n_features"]), f3(abl[m]["session_ccc"]), f3(abl[m]["within_ccc"]), f3(abl[m]["cross_ccc"]),
       f"{abl[m]['drop_pct']:.0f}%"] for m in ("voice", "face", "both")])
gap = copy.deepcopy(P[62]._p)
t_abl._tbl.addnext(gap)

set_text(P[63], "E. Transfer Learning")
set_text(P[65], "TABLE VI")
set_text(P[66], "TRANSFER LEARNING (CCC ON THE TWO HELD-OUT CONVERSATIONS OF THE TARGET)")
if has_tr:
    set_text(P[64], (
        f"Used unchanged, the CNN pretrained on two languages reaches {f3(full.zero_shot)} on the third. Adapting it with one full "
        f"conversation of the target gives {f3(full.head_only)} (head-only) and {f3(full.fine_tune)} (fine-tuning), against "
        f"{f3(full.scratch)} for the same network trained on that conversation alone (Table VI). "
        f"With only 10% of the conversation ({tf.loc[0.1].n_adapt:.0f} windows), {best_name} reaches "
        f"{f3(max(tf.loc[0.1].head_only, tf.loc[0.1].fine_tune))} against {f3(tf.loc[0.1].scratch)} from scratch."))
    fill(T[4], [["Share", "Windows", "Zero-shot", "Head-only", "Fine-tune", "Scratch"]] +
         [[f"{int(f * 100)}%", f"{r.n_adapt:.0f}", f3(r.zero_shot), f3(r.head_only), f3(r.fine_tune), f3(r.scratch)]
          for f, r in tf.iterrows()])

# ---------- discussion, limitations, conclusion ----------
set_text(P[69], "A. Simple Models Generalise Best at This Scale")
set_text(P[70], (
    f"No deep architecture exceeded {NAME[best['model']].lower()} on held-out conversations, in line with benchmark evidence that tree "
    "ensembles remain strong on medium-sized tabular data [32]. With nine conversations, the networks have few independent speakers to "
    "learn from: the MLP varied most across folds, and the sequence models, which receive the full 25-frame window, did not clearly "
    "improve on models of the window mean, suggesting that variation within one second is mostly noise relative to an engagement "
    "signal that evolves over longer spans [14]."))
set_text(P[71], "B. Voice Travels, Faces Do Not")
set_text(P[72], (
    f"The ablation shows that the {drop}% cross-lingual loss is not spread evenly. Prosodic cues to engagement — pitch, loudness and "
    "voice quality — transfer between English, French and German with little loss, while facial features lose more than half their "
    "concordance. This is consistent with the view that non-verbal expression is partly universal and partly culture-specific, with "
    "facial display rules among the culture-specific part [8], [9]. For deployment in a new language, a voice-based model is the safer "
    "starting point" + (", and a small amount of in-language data used to adapt a pretrained model is worth more than the same data alone." if has_tr else ".")))
set_text(P[74], (
    "In NoXi, language is confounded with recording site, speaker population and conversation topics. The face channel is the most "
    "exposed to this confound, since camera position and lighting differ between sites, so part of its larger drop may reflect "
    "recording conditions rather than culture. The NoXi+J extension [21] and multi-cultural corpora such as SEWA [20] offer a way to "
    "separate these factors."))
set_text(P[76], (
    "The corpus subset is small: nine sessions and 18 participant recordings, so fold-to-fold variation is large and three folds give "
    "only a coarse estimate of uncertainty. Each fold uses a single training run with a fixed seed. Hyperparameters of the MLP and the "
    "CNN were selected during development on a random split. Only one-second windows were examined, and the ablation used a single "
    "model family."))
set_text(P[78], (
    "We measured how well non-verbal engagement models transfer between English, French and German in the NoXi corpus. Evaluating on "
    "held-out conversations is essential: a random window split overstated performance by about 0.28 CCC. On unseen conversations, "
    f"{NAME[best['model']].lower()} on one-second feature averages outperformed eight deep architectures. Across languages, concordance "
    f"fell by {drop}%, and the ablation traced most of this loss to facial features, while voice alone was both the best single "
    f"modality and the most language-independent ({v['drop_pct']:.0f}% vs. {fc['drop_pct']:.0f}% drop). Future work will examine longer "
    "temporal windows, the additional languages of NoXi+J, and domain-adaptation methods that need no target labels."))

d.save("Research_Paper_Draft_v2.docx")
print("saved Research_Paper_Draft_v2.docx")
