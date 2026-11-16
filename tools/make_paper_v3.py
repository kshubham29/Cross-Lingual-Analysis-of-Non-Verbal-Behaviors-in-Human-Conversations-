"""Writes Research_Paper_Draft_v3.docx: the research paper updated with all
results (pretrained Transformers, improvements, significance test,
person-disjoint check, comparison with MultiMediate'24). Plain black text,
IEEE-style structure; paste into the official IEEE template for submission.
Result tables are read from reports/*.csv.
Run from the project folder: python tools/make_paper_v3.py"""
import pandas as pd
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

R = lambda f: pd.read_csv(f"reports/{f}.csv")
f3 = lambda x: f"{x:.3f}"
pm = lambda m, s: f"{m:.3f} ± {s:.3f}"
pc = lambda x: f"{max(x, 0):.0f}%"

doc = Document()
sec = doc.sections[0]
for side in ("left_margin", "right_margin"):
    setattr(sec, side, Cm(2.2))
for side in ("top_margin", "bottom_margin"):
    setattr(sec, side, Cm(2.0))
st = doc.styles["Normal"]; st.font.name = "Times New Roman"; st.font.size = Pt(10.5)
for h in ("Heading 1", "Heading 2"):
    doc.styles[h].font.name = "Times New Roman"; doc.styles[h].font.color.rgb = RGBColor(0, 0, 0)
doc.styles["Heading 1"].font.size = Pt(11); doc.styles["Heading 2"].font.size = Pt(10.5)
from docx.oxml.ns import qn
for name in ("Normal", "Heading 1", "Heading 2"):   # drop theme fonts so Times New Roman is really used
    rf = doc.styles[name].element.get_or_add_rPr().get_or_add_rFonts()
    for a in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
        rf.attrib.pop(qn(a), None)
    rf.set(qn("w:ascii"), "Times New Roman"); rf.set(qn("w:hAnsi"), "Times New Roman")
doc.styles["Heading 2"].font.italic = True


def para(text, bold_lead=None, align=WD_ALIGN_PARAGRAPH.JUSTIFY):
    p = doc.add_paragraph()
    if bold_lead:
        p.add_run(bold_lead).bold = True
    p.add_run(text)
    p.alignment = align
    p.paragraph_format.space_after = Pt(4)
    return p


def center(text, size=10.5, bold=False, italic=False):
    p = doc.add_paragraph(); r = p.add_run(text)
    r.font.size, r.bold, r.italic = Pt(size), bold, italic
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    return p


def table(num, title, header, rows):
    center(f"TABLE {num}", 9)
    center(title.upper(), 9)
    t = doc.add_table(rows=1, cols=len(header)); t.style = "Table Grid"
    for i, h in enumerate(header):
        c = t.rows[0].cells[i]; c.text = ""; r = c.paragraphs[0].add_run(h); r.bold = True; r.font.size = Pt(9)
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""; r = cells[i].paragraphs[0].add_run(str(v)); r.font.size = Pt(9)
    doc.add_paragraph()


H1 = lambda t: doc.add_heading(t, 1)
H2 = lambda t: doc.add_heading(t, 2)

# ---------------- numbers from the result files ----------------
pt = R("pretrained_results")
sm, pa, cx, fu, tc = R("smoothing_results"), R("partner_results"), R("context_results"), R("fusion_results"), R("transformer_context_results")
sig, pdj = R("significance_results"), R("person_disjoint_results").set_index("input")
gb = sm.iloc[0]
gb_pa = pa[(pa.input == "self + partner") & pa.model.str.startswith("Gradient")].iloc[0]
gb_ctx = cx[cx.input.str.contains("last 5 s") & cx.model.str.startswith("Gradient")].iloc[0]
dn_ctx = cx[cx.input.str.contains("last 5 s") & cx.model.str.startswith("w2v")].iloc[0]
fu1 = fu[(fu.model == "Gradient Boosting") & ~fu.input.str.contains("last 5 s")].iloc[0]
best = fu[(fu.model == "Gradient Boosting") & fu.input.str.contains("last 5 s")].iloc[0]
t1, t10 = tc.iloc[0], tc.iloc[1]
best_new = pdj.loc["fusion + context (best)"]
s_spk = sig[sig.level.str.startswith("speaker")].set_index("comparison")

# ---------------- title ----------------
p = doc.add_paragraph(); r = p.add_run("[Draft v3 - rewrite in your own words before submission; delete this line]")
r.italic = True; r.font.size = Pt(9)
center("How Much Is Lost in Translation? Cross-Lingual Prediction of Conversational Engagement from Non-Verbal Behaviour", 16, bold=True)
center("First Author, Second Author, Third Author")
center("Department, University, City, Country", italic=True)
center("email@university.edu")

para(f"Systems such as virtual tutors and meeting assistants benefit from knowing how engaged their users are, "
     f"yet engagement estimators are normally developed and evaluated within one language. This work asks two "
     f"questions: how much accuracy remains when the test speakers use a language the model never saw, and which "
     f"non-verbal signal is responsible for the loss. We use the English, French and German conversations of NoXi and "
     f"describe each second of behaviour with 88 voice descriptors (eGeMAPS), 709 face measurements (OpenFace) and the "
     f"frozen outputs of six pretrained Transformer encoders; spoken words are not used by the main models. Splitting "
     f"one-second windows at random lets the same conversation appear in training and test and pushes the concordance "
     f"correlation coefficient (CCC) to about 0.90, against about 0.63 when whole conversations are held out, so we "
     f"use the latter throughout. In this setting a gradient-boosting regressor (0.633) is stronger than eight neural "
     f"networks trained from scratch. Changing the language costs 29% of CCC on average, and the face features account "
     f"for most of it (55% loss) while the voice features lose only 12%. Combining the voice descriptors with w2v-BERT "
     f"2.0 and VideoMAE embeddings and adding the last 5 and 10 seconds of context lifts CCC to {best.ccc:.3f}, with "
     f"just {pc(best.drop_pct)} lost on a new language. This improvement is significant at speaker level (Wilcoxon "
     f"test, Holm-corrected p = {s_spk.loc['C vs A', 'p_holm']:.3f}) and persists ({best_new.ccc_new:.3f}) when no "
     f"person appears in both training and test data.", bold_lead="Abstract—")
para("conversational engagement, multilingual interaction, prosody, facial behaviour, pretrained "
     "Transformers, domain transfer, NoXi corpus.", bold_lead="Index Terms—")

# ---------------- I. Introduction ----------------
H1("I. Introduction")
para("Engagement is the process through which people in an interaction build, sustain and finally close their "
     "connection with each other [1]. An adaptive system, whether a tutoring program or a social robot, needs to track "
     "this process as it happens [2]. Because spoken content says little about how involved someone is, automatic "
     "estimators usually rely on non-verbal cues such as where a person looks, how the face and head move, and how the "
     "voice sounds [2], [3].")
para("Since the MultiMediate challenges began scoring frame-level engagement on NoXi with the concordance "
     "correlation coefficient [4], [5], several models trained on these labels have achieved high scores [6], [7]. "
     "Language, however, is rarely treated as a separate factor in these comparisons. Research in psychology suggests "
     "that some ways of showing emotion are shared across cultures while others are learned locally [8], [9], and "
     "speech-based emotion recognition is known to degrade when the corpus or language changes [10]–[12]. How strongly "
     "this affects engagement prediction, and which signals are responsible, is still an open question.")
para("We address this question with the English, French and German parts of NoXi. Our contributions are to: (i) "
     "describe every one-second window with non-verbal features and a language tag; (ii) demonstrate that splitting "
     "windows at random inflates scores, and use session-level held-out testing instead; (iii) benchmark four classical "
     "regressors, eight deep networks and six frozen pretrained Transformers under the same protocol; (iv) evaluate "
     "every train-language/test-language pair; (v) isolate the contribution of voice and face; (vi) adapt a pretrained "
     "network to a new language with little data; and (vii) examine temporal context, partner features and feature "
     "fusion. A speaker-level significance test and a re-evaluation without shared participants back up the main result.")

# ---------------- II. Related work ----------------
H1("II. Related Work")
H2("A. Engagement Recognition")
para("Sidner et al. analysed engagement in conversations with robots in terms of gaze, nods and joint attention "
     "[1]. Facial expressions were later shown to reveal student engagement almost as reliably as human observers [13], "
     "and affective states during learning were found to shift from moment to moment [14], which argues for continuous "
     "rather than categorical labels. There is still no agreed definition or measurement method [3], and very few "
     "studies consider culture [2]. Work on NoXi includes sequence-based engagement modelling by Dermouche and Pelachaud "
     "[6], the series of MultiMediate challenges, which progressed from backchannel detection to engagement estimation "
     "across domains [16], [4], [5], and the CEAM model of Yu et al., which attends to the conversation partner through "
     "cross-attention [7].")
H2("B. Non-Verbal and Pretrained Representations")
para("For the voice we rely on eGeMAPS, a compact set of 88 parameters proposed for emotion and voice research [17] "
     "and extracted with the openSMILE toolkit [18]. Facial behaviour comes from OpenFace 2.0, which tracks landmarks, "
     "head orientation, eye gaze and the intensity of facial action units [19]. Large self-supervised Transformers offer "
     "a different kind of representation: w2v-BERT 2.0 encodes speech [20], XLM-RoBERTa encodes text in many languages "
     "[21], and CLIP [22], DINOv2 [23], Video Swin [24] and VideoMAE [25] encode images or video clips. The MultiMediate'24 "
     "organisers distributed such embeddings together with NoXi, and in their baseline the speech model w2v-BERT 2.0 "
     "was the best single input [5].")
H2("C. Cross-Corpus and Cross-Lingual Transfer")
para("Emotion recognisers built from acoustic features are known to lose accuracy when applied to a different "
     "corpus [10], and the loss is smaller between closely related languages [11]. The cross-cultural task of AVEC 2018 "
     "reported the same problem when models trained on German speakers were tested on Hungarian ones [12], [26]. With "
     "NoXi+J, Japanese and Chinese conversations were added to NoXi, revealing culture-specific engagement cues [27], "
     "and the MultiMediate'24 baseline found visual features to be hit harder than acoustic ones on unseen languages "
     "[5]. Our study measures the effect separately for every language pair within a single corpus annotated in one "
     "consistent way.")

# ---------------- III. Dataset ----------------
H1("III. Dataset and Preprocessing")
H2("A. The NoXi Corpus")
para("In every NoXi session two people talk over a video link: one is an expert on a topic and the other a novice "
     "who wants to learn about it. Sessions were recorded in Paris, Nottingham and Augsburg [28], and human raters "
     "scored the engagement of both people frame by frame on a 0-1 scale (25 values per second). Our subset has three "
     "sessions for each language, i.e. 18 people in total. We accessed the corpus under its licence agreement and do "
     "not share the data.")
H2("B. Features")
para("Both the eGeMAPS and the OpenFace 2.0 streams are provided with NoXi at 25 frames per second for every "
     "participant. Five OpenFace columns carry bookkeeping information (frame index, face ID, time stamp, tracking "
     "confidence, success flag) rather than behaviour; after removing them, 709 face features remain. In addition we "
     "use the frame-level outputs of six pretrained Transformers that are distributed with the corpus (Table IV). The "
     "main models never see what is said; transcript embeddings from XLM-RoBERTa are included only to compare text "
     "with voice and face.")
H2("C. Windowing")
para("After aligning the voice, face and label streams and trimming them to the same length, we cut each "
     "recording into consecutive, non-overlapping blocks of 25 frames (one second). For every block we store two "
     "views: the average of each of the 797 features, which feeds the tree models, the MLP and the autoencoder, and "
     "the complete 25 x 797 matrix, which feeds the convolutional, recurrent and attention networks. The target is the "
     "average engagement inside the block, and the pretrained embeddings are averaged over the same blocks. Blocks "
     "without a usable label are discarded, which leaves 17,174 windows (Table I).")
table("I", "Dataset composition", ["Language", "Windows", "Mean engagement"],
      [("English", "4,976", "0.558"), ("French", "6,568", "0.592"), ("German", "5,630", "0.594"), ("Total", "17,174", "0.583")])
para("The three languages have slightly different average engagement levels, and the difference is statistically "
     "reliable (one-way ANOVA: F = 84.67, p < 0.001). Experts receive higher ratings than novices on average (0.659 "
     "against 0.506). Voice descriptors are also more closely related to the labels than facial ones: their mean "
     "absolute correlation with engagement is 0.391, compared with 0.187.")

# ---------------- IV. Method ----------------
H1("IV. Methodology")
H2("A. Metric")
para("We report the concordance correlation coefficient [29], ρc = 2ρσyσŷ / (σy² + σŷ² + (μy − μŷ)²), where ρ is the "
     "Pearson correlation and μ, σ the means and standard deviations of labels y and predictions ŷ. Unlike Pearson's r, "
     "CCC penalises offsets and scale errors, and it is the MultiMediate metric [4], [5].")
H2("B. Models")
para("The non-neural models are a linear regression, a random forest [30] with 100 trees, histogram-based "
     "gradient boosting [31] with 300 iterations, and XGBoost [32] with 300 trees of depth 6 and a learning rate of 0.1. "
     "All neural networks are written in TensorFlow/Keras, optimised with Adam [33] on the mean squared error and "
     "regularised with dropout [34]. Features are standardised with statistics from the training data and then limited "
     "to the range [−5, 5]: roughly 0.02% of the values in unseen sessions are extreme outliers, which trees tolerate "
     "but which make network training unstable.", bold_lead="Classical and deep models. ")
para("The MLP uses two ReLU layers with 256 and 128 units, the best of 13 tried configurations. The convolutional "
     "models follow the LeNet [35], VGG [36] and ResNet [37] designs but convolve along time over the 25 frames. Three "
     "recurrent models (simple RNN, LSTM [38] and GRU [39], each with 128 units) process the frames one after another. "
     "Our own Transformer maps every frame to 64 values, adds a trainable position embedding and stacks two encoder "
     "layers with four attention heads [40]. Finally, an autoencoder squeezes each window from 797 to 32 values, and "
     "either a small dense network or XGBoost predicts engagement from this code.")
para("For each pretrained Transformer the backbone stays frozen; its window-averaged embedding feeds either XGBoost or "
     "a dense head (256-128). This is transfer learning by feature extraction, chosen because only a CPU was available "
     "and nine conversations are too few for fine-tuning.", bold_lead="Frozen pretrained Transformers. ")
H2("C. Evaluation Protocols")
para("We split the nine sessions into three folds so that no conversation is ever divided between training and "
     "testing. In each fold, one session from every language (three in total) is set aside for testing and the "
     "remaining six are used to fit the model; we give the average CCC over the three folds and its standard "
     "deviation. To show the effect of this choice, the tree models and the MLP were additionally evaluated with an "
     "ordinary random 80/20 split of the windows.", bold_lead="Held-out conversations. ")
para("For each of the six ordered language pairs, a model is fitted on all windows of the first language and "
     "evaluated on all windows of the second. The within-language reference is obtained by leaving out one session at "
     "a time inside the same language, and the relative loss is computed as 100 x (within − cross) / within. We use a "
     "random forest for this matrix and XGBoost for the modality comparison, which trains on the 88 voice features, the "
     "709 face features, or all 797.", bold_lead="Cross-lingual transfer and ablation. ")
para("A LeNet-style CNN is first trained on two languages. It is then adapted to the third language with 10%, "
     "25%, 50% or 100% of one session from that language, and evaluated on the other two sessions of the same language. "
     "Four variants are compared: using the network as it is, retraining only its dense layers, updating all layers "
     "with a learning rate of 10⁻⁴, and training it from random initialisation on the adaptation data.",
     bold_lead="Transfer learning. ")
para("All settings below were fixed before testing: (a) causal smoothing of predictions with a 5-second moving average; "
     "(b) adding the partner's features at the same second; (c) adding the speaker's mean features over the past 5 and "
     "10 seconds (past only, so usable live); (d) fusing eGeMAPS with w2v-BERT 2.0 and VideoMAE embeddings; and (e) "
     "feeding our Transformer the last 10 seconds (one token per second) instead of the 25 frames of one second.",
     bold_lead="Improvements. ")
para("Three folds are too few for a test on fold scores, so we test on speakers: every speaker is predicted exactly once "
     "by a model that never saw their conversation, we compute CCC per speaker, and compare models with a Wilcoxon "
     "signed-rank test [41], a bootstrap 95% confidence interval and Holm correction [42]. Two NoXi participants appear "
     "in two of our sessions each, so we also repeat the key models with person-disjoint folds, in which sessions "
     "sharing a participant are always held out together.", bold_lead="Significance and robustness. ")

# ---------------- V. Results ----------------
H1("V. Results")
H2("A. Random Split Versus Held-Out Conversations")
para("With a random split, all non-linear models score above 0.88 CCC. Once complete sessions are kept apart, the "
     "same models lose between 0.25 and 0.29 (Table II). The reason is that consecutive one-second windows from one "
     "session look almost the same, so under a random split the model mostly learns to recognise a familiar speaker. "
     "We therefore report only session-held-out scores from here on.")
table("II", "Effect of the data split on tree models and the MLP",
      ["Model", "Random split", "Held-out (mean ± sd)", "MAE"],
      [("Gradient boosting", "0.901", "0.633 ± 0.063", "0.094"), ("Random forest", "0.885", "0.631 ± 0.050", "0.093"),
       ("XGBoost", "0.906", "0.620 ± 0.052", "0.093"), ("MLP (tuned)", "0.881", "0.591 ± 0.154", "0.105"),
       ("Linear regression", "0.284", "0.240 ± 0.286", "7.030")])
H2("B. Deep Models Trained from Scratch")
para("Among the networks that read the 25 frames, the Transformer does best (0.583) and the simple RNN worst "
     "(0.510). The MLP on window averages reaches 0.591, and the autoencoder loses little information despite reducing "
     "797 values to 32 (Table III). Still, no network matches gradient boosting.")
table("III", "Deep models on held-out conversations", ["Model", "Input", "Params", "CCC (mean ± sd)"],
      [("Transformer", "25x797", "123,841", "0.583 ± 0.038"), ("CNN, VGG-style", "25x797", "122,913", "0.577 ± 0.101"),
       ("GRU", "25x797", "364,289", "0.528 ± 0.166"), ("LSTM", "25x797", "482,433", "0.512 ± 0.219"),
       ("Simple RNN", "25x797", "126,849", "0.510 ± 0.201"), ("MLP (tuned)", "797", "237,313", "0.591 ± 0.154"),
       ("Autoencoder + XGBoost", "797→32", "-", "0.577 ± 0.092"), ("Autoencoder + dense head", "797→32", "-", "0.564 ± 0.099")])
H2("C. Frozen Pretrained Transformers")
w2v = pt.set_index("model").loc["w2v-BERT 2.0"]; comb = pt.set_index("model").loc["w2v-BERT 2.0 + VideoMAE"]
para(f"Speech embeddings are the strongest pretrained input and also the most language-independent: w2v-BERT 2.0 reaches "
     f"{w2v.xgb_ccc:.3f} with no cross-lingual drop (Table IV). Among video models VideoMAE is best, while CLIP, an "
     f"image-text model, does not transfer at all. Combining w2v-BERT 2.0 and VideoMAE gives {comb.dense_ccc:.3f}, "
     f"above every model trained from scratch, with a {pc(comb.drop_pct)} drop.")
table("IV", "Pretrained encoders (frozen) with a learned regressor",
      ["Model", "Input", "Dims", "XGBoost head", "Dense head", "Within", "Cross", "Drop"],
      [(r.model, r.input, r.dims, pm(r.xgb_ccc, r.xgb_std), pm(r.dense_ccc, r.dense_std), f3(r.within_ccc),
        f3(r.cross_ccc), pc(r.drop_pct)) for r in pt.itertuples()])
H2("D. Cross-Lingual Transfer")
para("Averaged over the diagonal of Fig. 1, models tested on their own language reach 0.556, while models tested on "
     "a different language reach 0.393, i.e. 29% less. The direction matters: training on French and testing on "
     "English almost fails (0.092), but training on German and testing on French gives 0.658, which is even higher "
     "than the French within-language result (0.604). A likely explanation is that the German model is fitted on "
     "three sessions, whereas each within-language model sees only two.")
doc.add_picture("reports/figures/report_cross_lingual.png", width=Cm(10))
doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
center("Fig. 1. Cross-lingual CCC (random forest, voice + face); rows: training language, columns: test language.", 9)
H2("E. Modality Ablation")
para("The 88 voice features on their own give the highest score (0.652). The 709 face features reach only 0.397, "
     "and combining both (0.631) is slightly worse than voice alone (Table V). The two channels also behave very "
     "differently across languages: the voice model loses 12% of its CCC, the face model 55%. The cross-language loss of "
     "the combined model is therefore driven mainly by the face.")
table("V", "Modality ablation (XGBoost, held-out conversations)", ["Input", "Features", "Held-out", "Within", "Cross", "Drop"],
      [("Voice", "88", "0.652", "0.596", "0.522", "12%"), ("Face", "709", "0.397", "0.322", "0.145", "55%"),
       ("Both", "797", "0.631", "0.571", "0.451", "21%")])
H2("F. Transfer Learning")
para("Without any adaptation, a CNN trained on the other two languages scores 0.473 on the target language (Table "
     "VI). Fine-tuning it on just 10% of a single target session raises this to 0.569, whereas training the same network "
     "only on that small amount of data gives 0.230. Using the whole session, the corresponding values are 0.555 and 0.376.")
table("VI", "CNN adaptation to a new language (CCC on unseen target sessions)",
      ["Share", "Windows", "Zero-shot", "Head-only", "Fine-tune", "Scratch"],
      [("10%", "190", "0.473", "0.501", "0.569", "0.230"), ("25%", "477", "0.473", "0.465", "0.533", "0.252"),
       ("50%", "954", "0.473", "0.467", "0.537", "0.301"), ("100%", "1908", "0.473", "0.474", "0.555", "0.376")])
H2("G. Temporal Context, Partner and Fusion")
para(f"Table VII lists the improvements in the order they were tested. Smoothing adds a little ({gb.raw_ccc:.3f} → "
     f"{gb.smooth_ccc:.3f}). The partner's features leave accuracy unchanged ({gb_pa.ccc:.3f}) but halve the "
     f"cross-lingual drop. Past context gives the largest single gain ({gb_ctx.ccc:.3f}) and removes the drop "
     f"entirely, with very stable folds (± {gb_ctx['std']:.3f}). Fusing acoustic descriptors with w2v-BERT 2.0 and "
     f"VideoMAE embeddings and adding context yields the best model, {best.ccc:.3f} ± {best['std']:.3f}, with a "
     f"{pc(best.drop_pct)} drop. Our own Transformer also benefits from a longer input: {t1.ccc:.3f} with one second, "
     f"{t10.ccc:.3f} with ten, while its cross-lingual drop falls from {pc(t1.drop_pct)} to {pc(t10.drop_pct)}.")
table("VII", "Improvements (gradient boosting unless stated)", ["Setting", "Held-out CCC", "Within", "Cross", "Drop"],
      [("Voice + face, 1 s (baseline)", pm(gb.raw_ccc, gb.raw_std), f3(gb.raw_within), f3(gb.raw_cross), pc(gb.raw_drop_pct)),
       ("+ smoothing (5 s)", pm(gb.smooth_ccc, gb.smooth_std), f3(gb.smooth_within), f3(gb.smooth_cross), pc(gb.smooth_drop_pct)),
       ("+ partner's features", pm(gb_pa.ccc, gb_pa["std"]), f3(gb_pa.within_ccc), f3(gb_pa.cross_ccc), pc(gb_pa.drop_pct)),
       ("+ past context (5 s, 10 s)", pm(gb_ctx.ccc, gb_ctx["std"]), f3(gb_ctx.within_ccc), f3(gb_ctx.cross_ccc), pc(gb_ctx.drop_pct)),
       ("Fusion (eGeMAPS + w2v-BERT + VideoMAE), 1 s", pm(fu1.ccc, fu1["std"]), "-", "-", "-"),
       ("Fusion + past context (best)", pm(best.ccc, best["std"]), f3(best.within_ccc), f3(best.cross_ccc), pc(best.drop_pct)),
       ("Own Transformer, 1 s", pm(t1.ccc, t1["std"]), f3(t1.within_ccc), f3(t1.cross_ccc), pc(t1.drop_pct)),
       ("Own Transformer, 10 s", pm(t10.ccc, t10["std"]), f3(t10.within_ccc), f3(t10.cross_ccc), pc(t10.drop_pct))])
H2("H. Significance and Robustness")
a, b, c = s_spk.loc["C vs A"], s_spk.loc["B vs A"], s_spk.loc["C vs B"]
para(f"At speaker level the best model improves on the baseline for {a.a_better} speakers (mean +{a.mean_diff:.3f} CCC, "
     f"95% CI [{a.ci_low:.3f}, {a.ci_high:.3f}], Holm-corrected p = {a.p_holm:.3f}); context alone helps "
     f"{b.a_better} speakers (p = {b.p_holm:.3f}), and fusion adds a further significant gain over context "
     f"(p = {c.p_holm:.3f}). All three comparisons stay significant at conversation level. With person-disjoint folds "
     f"(Table VIII) scores fall by 0.02 to 0.04 for voice-based inputs and by 0.09 for face, consistent with the face "
     f"model partly recognising familiar people; the best model keeps {best_new.ccc_new:.3f} with no cross-lingual drop.")
table("VIII", "Held-out conversations vs. person-disjoint folds (gradient boosting)",
      ["Input", "Conversation-disjoint", "Person-disjoint", "Drop (person-disjoint)"],
      [(i, f3(r.ccc_old), pm(r.ccc_new, r.std_new), pc(r.drop_new)) for i, r in pdj.iterrows()])

# ---------------- VI. Discussion ----------------
H1("VI. Discussion")
H2("A. Pretrained Features and Simple Learners Suit Small Data")
para("Gradient boosting stayed ahead of every network trained from scratch, which matches benchmark studies "
     "showing that tree ensembles are hard to beat on tabular data of moderate size [43]. Nine conversations offer only "
     "a handful of independent speakers, and within a single second most variation is noise relative to an engagement "
     "level that changes over several seconds [14]. Pretrained Transformers, on the other hand, carry knowledge from "
     "much larger datasets, and feeding their embeddings to a tree model produced the strongest system.")
H2("B. Voice Transfers Better than Face")
para("The average cross-language loss of 29% is not shared equally by the two channels. Prosodic features keep "
     "most of their predictive power when moving between English, French and German, while facial features lose more "
     "than half. Psychological work also points to culture-dependent rules for facial display [8], [9], and the "
     "MultiMediate'24 baseline shows a similar pattern on new languages: OpenFace drops by 54%, w2v-BERT 2.0 by 20% "
     "[5]. A model built on voice is therefore the more robust choice when the target language is new.")
H2("C. Longer Context Matters More than the Partner")
para("Past context gave the largest gain, and simply adding the partner's features did not help. Yu et al. report the "
     "same ordering on the official test set: a 10-second window (0.711) outperformed cross-attention to the "
     "interlocutor with a 2.5-second window (0.704) [7]. Engagement builds up over seconds, so a model needs to see "
     "that history.")
H2("D. Relation to the MultiMediate Benchmarks")
para("Our single-feature results are close to the MultiMediate'24 baseline on the NoXi test set (w2v-BERT 2.0: 0.631 "
     "vs. 0.64; XLM-RoBERTa: 0.393 vs. 0.40) [5], which supports the validity of the pipeline. The best published NoXi "
     "systems reach 0.71-0.76 [5], [7]. Our 0.777 is in the same range but is not directly comparable: we use nine "
     "conversations, our own held-out splits and one-second windows rather than the official frame-level test set.")
H2("E. Language or Recording Site?")
para("Each NoXi language was recorded at a different site, with different people and topics, so language cannot be "
     "fully separated from these factors. Video is the channel most affected by the site, because cameras and "
     "lighting were not identical; some of the face drop may therefore be technical rather than cultural. Corpora that "
     "record several cultures under one protocol, such as NoXi+J [27] and SEWA [26], would allow this to be tested.")

# ---------------- VII. Limitations / VIII. Conclusion ----------------
H1("VII. Limitations")
para("The subset is small (nine sessions, 18 recordings), so fold-to-fold variation is large; each fold uses a single "
     "seeded run. The pretrained Transformers were used frozen and not fine-tuned. Only one-second windows and up to "
     "ten seconds of context were examined, and partner information was added by concatenation rather than "
     "attention. Results are on our own splits, not the official challenge test set.")
H1("VIII. Conclusion")
para(f"This study examined how well engagement models based on non-verbal behaviour carry over between English, "
     f"French and German conversations in NoXi. Testing on unseen sessions proved necessary, since splitting windows at "
     f"random overestimated CCC by roughly 0.28. Moving to another language reduced CCC by 29% on average, mostly "
     f"because facial features did not generalise, whereas voice features and pretrained speech embeddings lost little "
     f"or nothing. Adding past context and combining acoustic descriptors with frozen speech and video Transformer "
     f"embeddings gave the strongest model (CCC {best.ccc:.3f}, {pc(best.drop_pct)} cross-language drop); its advantage "
     f"over the baseline is statistically significant and remains when no participant is shared between training and "
     f"test data. Next steps are to add more NoXi sessions, fine-tune the pretrained encoders, attend to the "
     f"conversation partner with cross-attention, and test transfer to Japanese and Chinese using NoXi+J.")

# ---------------- References ----------------
# citations were written with a 44-entry list; one unverified entry ([15]) was removed, so shift [16]..[44] down by one
import re
for p in doc.paragraphs:
    for r in p.runs:
        if "[" in r.text:   # only text runs with citations (setting .text would erase a picture run)
            r.text = re.sub(r"\[(\d+)\]", lambda m: f"[{int(m.group(1)) - 1 if int(m.group(1)) > 15 else m.group(1)}]", r.text)
H1("References")
refs = [
 "C. L. Sidner, C. Lee, C. D. Kidd, N. Lesh, and C. Rich, \"Explorations in engagement for humans and robots,\" Artificial Intelligence, vol. 166, no. 1-2, pp. 140-164, 2005.",
 "C. Oertel et al., \"Engagement in human-agent interaction: An overview,\" Frontiers in Robotics and AI, vol. 7, p. 92, 2020.",
 "K. Doherty and G. Doherty, \"Engagement in HCI: Conception, theory and measurement,\" ACM Computing Surveys, vol. 51, no. 5, Art. 99, 2018.",
 "P. Müller et al., \"MultiMediate '23: Engagement estimation and bodily behaviour recognition in social interactions,\" in Proc. ACM Int. Conf. Multimedia, 2023, pp. 9640-9645.",
 "P. Müller et al., \"MultiMediate '24: Multi-domain engagement estimation,\" in Proc. ACM Int. Conf. Multimedia, 2024.",
 "S. Dermouche and C. Pelachaud, \"Engagement modeling in dyadic interaction,\" in Proc. ACM Int. Conf. Multimodal Interaction (ICMI), 2019, pp. 440-445.",
 "J. Yu, K. Lu, J. Zhao, Z. Wei, I.-H. Chu, and P. Chang, \"Dialogue cross-enhanced central engagement attention model for real-time engagement estimation,\" in Proc. IJCAI, 2024, pp. 3187-3195.",
 "H. A. Elfenbein and N. Ambady, \"On the universality and cultural specificity of emotion recognition: A meta-analysis,\" Psychological Bulletin, vol. 128, no. 2, pp. 203-235, 2002.",
 "R. E. Jack, O. G. B. Garrod, H. Yu, R. Caldara, and P. G. Schyns, \"Facial expressions of emotion are not culturally universal,\" Proc. Natl. Acad. Sci. USA, vol. 109, no. 19, pp. 7241-7244, 2012.",
 "B. Schuller et al., \"Cross-corpus acoustic emotion recognition: Variances and strategies,\" IEEE Trans. Affective Computing, vol. 1, no. 2, pp. 119-131, 2010.",
 "S. M. Feraru, D. Schuller, and B. Schuller, \"Cross-language acoustic emotion recognition: An overview and some tendencies,\" in Proc. ACII, 2015, pp. 125-131.",
 "F. Ringeval et al., \"AVEC 2018 workshop and challenge: Bipolar disorder and cross-cultural affect recognition,\" in Proc. Audio/Visual Emotion Challenge and Workshop, 2018, pp. 3-13.",
 "J. Whitehill, Z. Serpell, Y.-C. Lin, A. Foster, and J. R. Movellan, \"The faces of engagement: Automatic recognition of student engagement from facial expressions,\" IEEE Trans. Affective Computing, vol. 5, no. 1, pp. 86-98, 2014.",
 "S. D'Mello and A. Graesser, \"Dynamics of affective states during complex learning,\" Learning and Instruction, vol. 22, no. 2, pp. 145-157, 2012.",
 "P. Müller et al., \"MultiMediate '22: Backchannel detection and agreement estimation in group interactions,\" in Proc. ACM Int. Conf. Multimedia, 2022.",
 "F. Eyben et al., \"The Geneva minimalistic acoustic parameter set (GeMAPS) for voice research and affective computing,\" IEEE Trans. Affective Computing, vol. 7, no. 2, pp. 190-202, 2016.",
 "F. Eyben, M. Wöllmer, and B. Schuller, \"openSMILE: The Munich versatile and fast open-source audio feature extractor,\" in Proc. ACM Int. Conf. Multimedia, 2010, pp. 1459-1462.",
 "T. Baltrušaitis, A. Zadeh, Y. C. Lim, and L.-P. Morency, \"OpenFace 2.0: Facial behavior analysis toolkit,\" in Proc. IEEE FG, 2018, pp. 59-66.",
 "L. Barrault et al., \"Seamless: Multilingual expressive and streaming speech translation,\" arXiv:2312.05187, 2023.",
 "A. Conneau et al., \"Unsupervised cross-lingual representation learning at scale,\" in Proc. ACL, 2020, pp. 8440-8451.",
 "A. Radford et al., \"Learning transferable visual models from natural language supervision,\" in Proc. ICML, 2021, pp. 8748-8763.",
 "M. Oquab et al., \"DINOv2: Learning robust visual features without supervision,\" Trans. Machine Learning Research, 2024.",
 "Z. Liu et al., \"Video Swin Transformer,\" in Proc. IEEE/CVF CVPR, 2022, pp. 3202-3211.",
 "Z. Tong, Y. Song, J. Wang, and L. Wang, \"VideoMAE: Masked autoencoders are data-efficient learners for self-supervised video pre-training,\" in Proc. NeurIPS, 2022.",
 "J. Kossaifi et al., \"SEWA DB: A rich database for audio-visual emotion and sentiment research in the wild,\" IEEE Trans. Pattern Analysis and Machine Intelligence, vol. 43, no. 3, pp. 1022-1040, 2021.",
 "M. Funk, S. Okada, and E. André, \"Multilingual dyadic interaction corpus NoXi+J: Toward understanding Asian-European non-verbal cultural characteristics and their influences on engagement,\" in Proc. ACM ICMI, 2024.",
 "A. Cafaro et al., \"The NoXi database: Multimodal recordings of mediated novice-expert interactions,\" in Proc. ACM ICMI, 2017, pp. 350-359.",
 "L. I-K. Lin, \"A concordance correlation coefficient to evaluate reproducibility,\" Biometrics, vol. 45, no. 1, pp. 255-268, 1989.",
 "L. Breiman, \"Random forests,\" Machine Learning, vol. 45, no. 1, pp. 5-32, 2001.",
 "J. H. Friedman, \"Greedy function approximation: A gradient boosting machine,\" Annals of Statistics, vol. 29, no. 5, pp. 1189-1232, 2001.",
 "T. Chen and C. Guestrin, \"XGBoost: A scalable tree boosting system,\" in Proc. ACM SIGKDD, 2016, pp. 785-794.",
 "D. P. Kingma and J. Ba, \"Adam: A method for stochastic optimization,\" in Proc. ICLR, 2015.",
 "N. Srivastava, G. Hinton, A. Krizhevsky, I. Sutskever, and R. Salakhutdinov, \"Dropout: A simple way to prevent neural networks from overfitting,\" J. Machine Learning Research, vol. 15, no. 1, pp. 1929-1958, 2014.",
 "Y. LeCun, L. Bottou, Y. Bengio, and P. Haffner, \"Gradient-based learning applied to document recognition,\" Proc. IEEE, vol. 86, no. 11, pp. 2278-2324, 1998.",
 "K. Simonyan and A. Zisserman, \"Very deep convolutional networks for large-scale image recognition,\" in Proc. ICLR, 2015.",
 "K. He, X. Zhang, S. Ren, and J. Sun, \"Deep residual learning for image recognition,\" in Proc. IEEE CVPR, 2016, pp. 770-778.",
 "S. Hochreiter and J. Schmidhuber, \"Long short-term memory,\" Neural Computation, vol. 9, no. 8, pp. 1735-1780, 1997.",
 "K. Cho et al., \"Learning phrase representations using RNN encoder-decoder for statistical machine translation,\" in Proc. EMNLP, 2014, pp. 1724-1734.",
 "A. Vaswani et al., \"Attention is all you need,\" in Proc. NeurIPS, 2017, pp. 5998-6008.",
 "F. Wilcoxon, \"Individual comparisons by ranking methods,\" Biometrics Bulletin, vol. 1, no. 6, pp. 80-83, 1945.",
 "S. Holm, \"A simple sequentially rejective multiple test procedure,\" Scandinavian J. Statistics, vol. 6, no. 2, pp. 65-70, 1979.",
 "L. Grinsztajn, E. Oyallon, and G. Varoquaux, \"Why do tree-based models still outperform deep learning on typical tabular data?\" in Proc. NeurIPS Datasets and Benchmarks Track, 2022.",
]
for i, ref in enumerate(refs, 1):
    p = doc.add_paragraph(f"[{i}]  {ref}")
    p.paragraph_format.space_after = Pt(2)
    for r in p.runs:
        r.font.size = Pt(9)

doc.save("Research_Paper_Draft_v3.docx")
print(f"saved Research_Paper_Draft_v3.docx ({len(refs)} references)")
