"""Builds Project_Report_Final.docx - the full project report, start to now.
Numbers are read from reports/*.csv; figures from reports/figures/;
screenshots from the folder given as the first argument.
Run from the project folder: python tools/make_final_report.py <screenshots folder>"""
import os
import sys
import pandas as pd
from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

SHOTS = sys.argv[1]
FIG = "reports/figures"
R = lambda f: pd.read_csv(f"reports/{f}.csv")
f3 = lambda x: f"{x:.3f}"
GREEN, INK, MUTED = RGBColor(0x2F, 0x55, 0x27), RGBColor(0x1D, 0x24, 0x19), RGBColor(0x5D, 0x68, 0x57)

doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21), Cm(29.7)
for side in ("left_margin", "right_margin"):
    setattr(sec, side, Cm(2.3))
sec.top_margin = sec.bottom_margin = Cm(2.2)

st = doc.styles
st["Normal"].font.name = "Calibri"
st["Normal"].font.size = Pt(11)
st["Normal"].paragraph_format.space_after = Pt(6)
st["Normal"].paragraph_format.line_spacing = 1.15
for name, size, before in (("Heading 1", 17, 18), ("Heading 2", 13, 12), ("Heading 3", 11.5, 10)):
    s = st[name]
    s.font.name, s.font.size, s.font.bold, s.font.color.rgb = "Cambria", Pt(size), True, GREEN
    s.paragraph_format.space_before, s.paragraph_format.space_after = Pt(before), Pt(6)
    s.paragraph_format.keep_with_next = True

counters = {"Figure": 0, "Table": 0}


def shade(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    s = OxmlElement("w:shd")
    s.set(qn("w:val"), "clear"); s.set(qn("w:color"), "auto"); s.set(qn("w:fill"), fill)
    tcPr.append(s)


def h1(text, new_page=True):
    doc.add_heading(text, 1).paragraph_format.page_break_before = new_page


def h2(text):
    doc.add_heading(text, 2)


def p(text, italic=False, bold_lead=None, size=None, color=None, align=None):
    para = doc.add_paragraph()
    if bold_lead:
        para.add_run(bold_lead).bold = True
    r = para.add_run(text)
    r.italic = italic
    if size:
        r.font.size = Pt(size)
    if color:
        r.font.color.rgb = color
    if align:
        para.alignment = align
    return para


def bullets(items, style="List Bullet"):
    # numbered lists are written out by hand so each list restarts at 1
    for n, it in enumerate(items, 1):
        if style == "List Number":
            para = doc.add_paragraph()
            para.paragraph_format.left_indent = Cm(0.9)
            para.paragraph_format.first_line_indent = Cm(-0.6)
            para.add_run(f"{n}.  ")
        else:
            para = doc.add_paragraph(style=style)
        if isinstance(it, tuple):
            para.add_run(it[0]).bold = True
            para.add_run(it[1])
        else:
            para.add_run(it)


def caption(kind, text):
    counters[kind] += 1
    para = doc.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = para.add_run(f"{kind} {counters[kind]}. ")
    r.bold = True
    r.font.size = Pt(9.5)
    r2 = para.add_run(text)
    r2.font.size = Pt(9.5)
    r2.font.color.rgb = MUTED
    return counters[kind]


def figure(path, text, width=16):
    para = doc.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    para.paragraph_format.keep_with_next = True
    para.add_run().add_picture(path, width=Cm(width))
    return caption("Figure", text)


def table(header, rows, text, widths=None, size=9.5, bold_first_row=None):
    n = caption("Table", text)
    doc.paragraphs[-1].paragraph_format.keep_with_next = True
    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(header):
        c = t.rows[0].cells[i]
        c.text = ""
        run = c.paragraphs[0].add_run(str(h))
        run.bold, run.font.size = True, Pt(size)
        run.font.color.rgb = RGBColor(255, 255, 255)
        shade(c, "3F6B35")
    for k, row in enumerate(rows):
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            run = cells[i].paragraphs[0].add_run(str(v))
            run.font.size = Pt(size)
            if bold_first_row is not None and k == bold_first_row:
                run.bold = True
            if k % 2:
                shade(cells[i], "EEF3EA")
    if widths:
        for row in t.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Cm(w)
    doc.add_paragraph()
    return n


def code(text):
    for line in text.strip("\n").split("\n"):
        para = doc.add_paragraph()
        para.paragraph_format.space_after = Pt(0)
        para.paragraph_format.left_indent = Cm(0.4)
        r = para.add_run(line if line else " ")
        r.font.name, r.font.size = "Consolas", Pt(8.5)
        r._element.rPr.rFonts.set(qn("w:eastAsia"), "Consolas")
        pPr = para._p.get_or_add_pPr()
        s = OxmlElement("w:shd")
        s.set(qn("w:val"), "clear"); s.set(qn("w:color"), "auto"); s.set(qn("w:fill"), "F2F4EF")
        pPr.append(s)
    doc.add_paragraph()


def toc():
    para = doc.add_paragraph()
    run = para.add_run()
    for tag, txt in (("begin", None), (None, 'TOC \\o "1-2" \\h \\z \\u'), ("separate", None), (None, None), ("end", None)):
        if tag:
            el = OxmlElement("w:fldChar"); el.set(qn("w:fldCharType"), tag); run._r.append(el)
        elif txt:
            el = OxmlElement("w:instrText"); el.set(qn("xml:space"), "preserve"); el.text = txt; run._r.append(el)
        else:
            t = OxmlElement("w:t"); t.text = "Right-click here and choose Update Field to build the table of contents."; run._r.append(t)
    upd = OxmlElement("w:updateFields"); upd.set(qn("w:val"), "true")
    doc.settings.element.append(upd)


# ------------------------------------------------------------------ data
ms, pt, ab = R("master_results"), R("pretrained_results"), R("ablation_results")
cm = R("noxi_crosslingual_ccc").set_index("Unnamed: 0")
langs = list(cm.columns)
diag = sum(cm.loc[l, l] for l in langs) / 3
off = (cm.to_numpy().sum() - 3 * diag) / 6
drop = round(100 * (diag - off) / diag)
eda = R("eda_summary")
tr = R("transfer_results")
gtr = tr.groupby("fraction")[["zero_shot", "head_only", "fine_tune", "scratch"]].mean()
best_pt = pt.loc[pt[["xgb_ccc", "dense_ccc"]].max(axis=1).idxmax()]
best_pt_ccc = max(best_pt.xgb_ccc, best_pt.dense_ccc)
gb = ms.set_index("model").loc["GradientBoosting"]
xgb = ms.set_index("model").loc["XGBoost"]
abl = ab.set_index("modality")
w2v = pt.set_index("model").loc["w2v-BERT 2.0"]
n_models = len(ms) + len(pt)
lit = pd.read_excel("Literature_Review.xlsx")
sm, pa, cx = R("smoothing_results"), R("partner_results"), R("context_results")
fu, tcx = R("fusion_results"), R("transformer_context_results")
sig, pdj = R("significance_results"), R("person_disjoint_results").set_index("input")
gb_sm = sm.iloc[0]
gb_pa = pa[(pa.input == "self + partner") & pa.model.str.startswith("Gradient")].iloc[0]
gb_ctx = cx[cx.input.str.contains("last 5 s") & cx.model.str.startswith("Gradient")].iloc[0]
fu1 = fu[(fu.model == "Gradient Boosting") & ~fu.input.str.contains("last 5 s")].iloc[0]
best = fu[(fu.model == "Gradient Boosting") & fu.input.str.contains("last 5 s")].iloc[0]
t1, t10 = tcx.iloc[0], tcx.iloc[1]
s_spk = sig[sig.level.str.startswith("speaker")].set_index("comparison")
best_new = pdj.loc["fusion + context (best)"]

# ------------------------------------------------------------------ title page
for _ in range(5):
    doc.add_paragraph()
p("Deep Learning Semester Project", size=12, color=MUTED, align=WD_ALIGN_PARAGRAPH.CENTER)
t = doc.add_paragraph(); t.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = t.add_run("Cross-Lingual Prediction of Engagement from Non-Verbal Behaviour in Human Conversations")
r.bold, r.font.size, r.font.name, r.font.color.rgb = True, Pt(24), "Cambria", GREEN
p("Project Report: work from the start of the project to November 2026", size=12, color=MUTED, align=WD_ALIGN_PARAGRAPH.CENTER)
doc.add_paragraph()
info = doc.add_table(rows=0, cols=2)
info.style = "Table Grid"
info.alignment = WD_TABLE_ALIGNMENT.CENTER
for k, v in (("Team members", "[names]"), ("Roll numbers", "[roll numbers]"), ("Supervisor", "[supervisor name]"),
             ("Department", "[department, institution]"), ("Course", "Deep Learning (Units 1-5)"),
             ("Dataset", "NoXi, used under its End-User Licence Agreement"), ("Date", "16 November 2026")):
    c = info.add_row().cells
    c[0].text, c[1].text = k, v
    c[0].paragraphs[0].runs[0].bold = True
    shade(c[0], "EEF3EA")
    c[0].width, c[1].width = Cm(4.5), Cm(9)

# ------------------------------------------------------------------ abstract + contents
h1("Abstract")
p(f"This project predicts how engaged a person is in a conversation, as a continuous score from 0 to 1, using only "
  f"non-verbal behaviour: the sound of the voice and the movements of the face, never the words. It also asks whether "
  f"a model trained on one language still works on another. We use 9 expert-novice conversations from the NoXi "
  f"dataset (3 English, 3 French, 3 German), cut into 17,174 one-second windows with 88 voice features (eGeMAPS) "
  f"and 709 face features (OpenFace 2.0).")
p(f"We trained {n_models} final models that cover every unit of the syllabus: classic machine learning, an ANN, CNNs, "
  f"a simple RNN, LSTM and GRU, an autoencoder, our own Transformer encoder, and six large pretrained Transformers used "
  f"as frozen feature extractors. Every final model is tested on whole conversations it never saw during training.")
p("We then improved the models with past context, prediction smoothing, the partner's behaviour and feature fusion, "
  "and checked the results with significance tests and a person-disjoint evaluation.")
p("Main results:", bold_lead=None)
bullets([
    ("Best model: ", f"Gradient Boosting on eGeMAPS voice features + w2v-BERT 2.0 + VideoMAE embeddings with past "
                     f"context (last 5 s and 10 s): CCC {best.ccc:.3f}, with only {max(best.drop_pct, 0):.0f}% lost on a new "
                     f"language. The baseline (Gradient Boosting on our own features) reaches {gb.session_ccc:.3f}."),
    ("The gain is real: ", f"it is significant per speaker (better for {s_spk.loc['C vs A', 'a_better']} speakers, Holm-corrected "
                           f"p = {s_spk.loc['C vs A', 'p_holm']:.3f}) and holds when no person appears in both training and "
                           f"test data (CCC {best_new.ccc_new:.3f})."),
    ("Data leakage: ", f"a random split of windows inflates XGBoost from {xgb.session_ccc:.3f} to {xgb.random_split_ccc:.3f}, "
                       f"because neighbouring seconds of one conversation land in both train and test."),
    ("A new language costs ", f"{drop}%: within-language CCC {diag:.3f} vs cross-language {off:.3f}."),
    ("Voice transferred better than face in our data: ", f"voice features lose {abl.loc['voice', 'drop_pct']:.0f}% across languages, "
                                           f"face features {abl.loc['face', 'drop_pct']:.0f}%, and pretrained speech "
                                           f"embeddings {max(w2v.drop_pct, 0):.0f}%."),
    ("Transfer learning: ", f"a CNN pretrained on two languages and fine-tuned on 10% of one conversation of the third "
                            f"reaches {gtr.fine_tune.iloc[0]:.3f}, against {gtr.scratch.iloc[0]:.3f} from scratch."),
])
h1("Contents")
toc()

# ------------------------------------------------------------------ 1 introduction
h1("1. Introduction")
p("In a conversation, much of the meaning is carried by how people look and sound: facial expression, gaze, head "
  "movement, the pitch and energy of the voice. Engagement is one of the most useful of these signals. It describes how "
  "interested and involved a person is in the interaction. A system that measures engagement automatically could tell "
  "an online teacher when students drift away, let a virtual assistant adapt its behaviour, or show a speaker whether "
  "the audience is following.")
p("Engagement is not fixed. It rises and falls during a conversation, so we treat it as a number that changes over "
  "time, not as a category. A second question is often ignored: does an engagement model trained on speakers of one "
  "language still work on speakers of another? Cultures express interest differently and languages have different "
  "speech rhythms, so a model may quietly fail when it is moved. Systems used around the world should work fairly for "
  "everyone, which makes this question practical, not only academic.")
h2("1.1 Problem statement")
p("Given one second of a person's non-verbal behaviour in a conversation (voice features and face features), predict "
  "their engagement as a number between 0 and 1, and measure how well this prediction transfers from one language to "
  "another. This is a regression task, scored with the Concordance Correlation Coefficient (CCC).")
h2("1.2 Research questions")
bullets([
    "RQ1. How well can engagement be predicted from non-verbal behaviour alone, on conversations the model has never seen?",
    "RQ2. How much accuracy is lost when the model is tested on a different language?",
    "RQ3. Which modality, voice or face, carries engagement across languages?",
    "RQ4. Which deep learning architectures work best, and do large pretrained Transformers help?",
    "RQ5. Can a small amount of data from a new language recover the lost accuracy (transfer learning)?",
    "RQ6. Do temporal context, the partner's behaviour and feature fusion improve prediction, and are the gains significant?",
], style="List Number")
h2("1.3 Objectives")
bullets([
    "Prepare English, French and German NoXi conversations and align voice, face and engagement labels.",
    "Turn 25-frames-per-second data into one-second windows a model can learn from.",
    "Explore the data: engagement distribution, language and role differences, which features matter.",
    "Train and tune models from every syllabus unit and compare them fairly.",
    "Measure transfer between every pair of languages, and separate the effect of voice and face.",
    "Test transfer learning and pretrained Transformers.",
    "Build a demo application and document everything (paper, presentation, poster, lab manual, this report).",
], style="List Number")

# ------------------------------------------------------------------ 2 literature
h1("2. Literature Review and Research Gap")
p(f"We reviewed {len(lit)} papers on engagement, non-verbal behaviour, the NoXi dataset, cross-language and "
  "cross-cultural modelling, and the deep learning methods we use. The full review with objectives, datasets, methods, "
  "outcomes and gaps is in Literature_Review.xlsx; Table 1 lists the papers.")
rows = [(int(r["S.no."]), str(r["Title/Paper Name"]), str(r["Authors"]).split(",")[0] + (" et al." if "," in str(r["Authors"]) else ""),
         int(r["Year"]), str(r["Journal/Venue"])) for _, r in lit.iterrows()]
table(["#", "Paper", "First author", "Year", "Venue"], rows, "Papers reviewed (from Literature_Review.xlsx).",
      widths=[0.8, 8.6, 2.8, 1.2, 3.0], size=8.5)
h2("2.1 What the literature shows")
bullets([
    ("Engagement is carried by non-verbal cues. ", "Classic work defines engagement through gaze, nods, gestures and "
     "backchannels (Sidner et al., 2005; Rich et al., 2010) and recognises it from the face (Whitehill et al., 2014)."),
    ("NoXi is the standard dataset for this task. ", "Cafaro et al. (2017) recorded expert-novice conversations in several "
     "languages with continuous engagement labels. The MultiMediate challenges (Muller et al., 2022, 2023, 2024) built "
     "engagement benchmarks on it with deep sequence and attention models scored by CCC; NoXi+J (Okada et al., 2024) added "
     "Japanese and Chinese."),
    ("Models degrade across languages and cultures. ", "Cross-language emotion recognition loses accuracy (Feraru et al., "
     "2015), facial expressions are not fully universal (Jack et al., 2012), and recognition shows an in-group advantage "
     "(Elfenbein and Ambady, 2002)."),
])
h2("2.2 Research gap")
bullets([
    "Most cross-language work studies emotion, not engagement.",
    "Many engagement systems rely on words, which cannot transfer between languages; few use only face and voice.",
    "Datasets with several languages are rarely used for a clean train-on-one, test-on-another experiment, and the "
    "contribution of voice and face to transfer is rarely separated.",
    "Few student-scale studies check for data leakage between neighbouring seconds of the same conversation.",
])
p("This project addresses all four: it predicts engagement, uses only non-verbal signals, runs a full language-by-"
  "language transfer matrix with a voice/face ablation, and evaluates every final model on unseen conversations.")

# ------------------------------------------------------------------ 3 dataset
h1("3. Dataset and Exploratory Analysis")
p("NoXi (Novice-Expert Interaction) contains natural, unscripted conversations recorded over video link, in which an "
  "expert explains a topic to a novice. Engagement was annotated continuously, 25 times per second, on a 0 to 1 scale. "
  "Because the conversations are real rather than acted, engagement rises and falls on its own.")
h2("3.1 Data used")
table(["Language", "Conversations", "Speakers", "1-second windows", "Mean engagement", "Std"],
      [(r.language, 3, 6, f"{r['count']:,}", f3(r['mean']), f3(r['std'])) for _, r in eda.iterrows()]
      + [("Total", 9, 18, f"{eda['count'].sum():,}", "", "")],
      "Conversations and windows per language.", widths=[2.6, 2.6, 2.0, 3.0, 3.0, 2.0])
table(["Input", "Source", "Size per window", "Used for"],
      [("Voice", "eGeMAPS v02 functionals (openSMILE)", "88", "all experiments"),
       ("Face", "OpenFace 2.0: action units, gaze, head pose, landmarks", "709 (714 minus 5 bookkeeping columns)", "all experiments"),
       ("Pretrained speech", "w2v-BERT 2.0 embeddings", "1,024", "pretrained experiment"),
       ("Pretrained text", "XLM-RoBERTa embeddings of the transcript", "768", "comparison only"),
       ("Pretrained video", "CLIP, DINOv2, Swin, VideoMAE embeddings", "512 to 1,408", "pretrained experiment"),
       ("Label", "Continuous engagement annotation", "1 value (0 to 1)", "target")],
      "Features available for every one-second window.", widths=[2.8, 6.0, 4.4, 3.2])
h2("3.2 Exploratory findings")
bullets([
    ("Languages are balanced and similar in level. ", "French 6,568, German 5,630 and English 4,976 windows; mean engagement "
     "0.592, 0.594 and 0.558. An ANOVA finds the small difference significant (F = 84.67, p < 0.001) because there are many windows."),
    ("Experts are more engaged than novices: ", "mean 0.659 vs 0.506."),
    ("Voice is linked to engagement about twice as strongly as the face: ", "mean absolute correlation 0.391 vs 0.187."),
    ("Engagement clusters in the middle of the scale; ", "very low and very high values are rare."),
])
for f, cap in (("engagement_distribution.png", "Distribution of engagement over all windows."),
               ("engagement_by_language.png", "Engagement by language."),
               ("engagement_by_role.png", "Engagement of experts and novices."),
               ("voice_vs_face.png", "Average correlation with engagement: voice vs face features."),
               ("top_features.png", "Features most correlated with engagement."),
               ("pca_by_language.png", "Windows projected on two principal components, coloured by language.")):
    figure(os.path.join(FIG, f), cap, width=12.5)
figure(os.path.join(SHOTS, "console_eda.png"), "Console output of src/03_eda.py.", width=15)

# ------------------------------------------------------------------ 4 timeline
h1("4. Project Timeline")
p("The project ran in four stages. Dates are taken from the files in the project folder.")
table(["When (2026)", "Stage", "Work done", "Scripts and outputs"],
      [("7-9 Sep", "Data", "Extracted the needed NoXi files, built one-second windows, explored the data, first ML baselines, "
        "dataset description and first report", "01, 02, 03, 04"),
       ("9-23 Sep", "Development", "ANN and its tuning (13 runs), sequence models, CNN and its tuning (8 runs), LeNet / VGG / "
        "ResNet-style CNNs, Transformer encoder, first cross-language test; literature review (26 papers)", "06, 07, 08, 09, 11, 12"),
       ("13 Oct", "Development", "LSTM; first research paper draft", "13"),
       ("26-27 Oct", "Final evaluation", "Found data leakage in the random split; re-evaluated every model on unseen "
        "conversations; added Simple RNN, GRU and an autoencoder; voice/face ablation; transfer learning redone by "
        "conversation; master results table; demo app; presentation, poster, lab manual, paper v2", "05, 10, 14, 15, 16, 17, 18, app.py"),
       ("3 Nov", "Pretrained Transformers", "Extracted six pretrained Transformer embeddings and trained heads on them; "
        "all-results tables", "19, 20"),
       ("7 Nov", "Reporting", "First version of this report", "tools/"),
       ("7-8 Nov", "Improvements", "Prediction smoothing, partner's behaviour, past context, feature fusion (best model), "
        "Transformer with 10 s of input", "21, 22, 23, 24, 25"),
       ("9 Nov", "Checks", "Significance test per speaker; person-disjoint evaluation; results summary for the supervisor",
        "26, 27, splits.py"),
       ("12-16 Nov", "Dissemination", "Research paper v4 (IEEE format), simple notebooks of the main steps, study guides, "
        "this updated report", "notebooks/, tools/")],
      "Project timeline.", widths=[2.2, 2.6, 8.6, 3.2], size=9)
figure(os.path.join(FIG, "report_pipeline.png"), "The pipeline from raw data to results.", width=16.4)

# ------------------------------------------------------------------ 5 methodology
h1("5. Methodology")
h2("5.1 Preprocessing")
bullets([
    "Read the voice, face and engagement streams of each speaker and trim them to the same length (they differ by a frame or two).",
    "Group every 25 frames (one second) into a window, average the features and the label, and drop windows without a valid label.",
    "Drop the 5 OpenFace bookkeeping columns (frame number, face id, timestamp, confidence, success): they describe the "
    "recording, not behaviour. This leaves 797 features.",
    "Keep the raw 25 frames of every window as a sequence (25 x 797) for the CNN, RNN and Transformer models.",
    "Standardise features with a scaler fitted on the training conversations only.",
    "For neural networks, clip standardised values to [-5, 5]. A few windows in unseen conversations reach values up to "
    "100,000 standard deviations, which do not disturb trees but break a neural network (ANN CCC rose from 0.337 to 0.591 after clipping).",
], style="List Number")
h2("5.2 Evaluation protocols")
table(["Protocol", "Train", "Test", "Used for"],
      [("Random split (development only)", "random 80% of windows", "the other 20%", "building and tuning models; leaky"),
       ("Session-wise 3-fold", "6 conversations (2 per language)", "3 unseen conversations (1 per language)", "the main comparison of all models"),
       ("Within-language", "2 conversations of a language", "the 3rd conversation of that language", "the diagonal of the language matrix"),
       ("Cross-language", "all 3 conversations of language A", "all 3 conversations of language B", "the 6 off-diagonal pairs"),
       ("Transfer learning", "2 languages + part of 1 conversation of the 3rd", "the other 2 conversations of the 3rd", "zero-shot / head-only / fine-tune / scratch")],
      "How models are trained and tested.", widths=[3.8, 4.2, 4.4, 4.2], size=9)
p("Fold k of the session-wise split tests on the k-th conversation of each language: fold 1 = 027, 001, 070; "
  "fold 2 = 028, 013, 072; fold 3 = 030, 021, 077. Results are the mean and standard deviation over the three folds. "
  "The drop across languages is 100 x (within - cross) / within.")
h2("5.3 Metric")
p("The Concordance Correlation Coefficient measures agreement between predicted and true engagement in both shape "
  "and level; 1 is perfect, 0 is no agreement. It is the metric used by the NoXi engagement benchmarks.")
p("CCC = 2 cov(y, y') / ( var(y) + var(y') + (mean(y) - mean(y'))^2 )", italic=True, align=WD_ALIGN_PARAGRAPH.CENTER)
p("We also report Pearson correlation and mean absolute error (MAE) where available.")
h2("5.4 Models by syllabus unit")
table(["Unit", "Model", "Input", "Architecture and training"],
      [("ML", "Linear Regression, Random Forest, Gradient Boosting, XGBoost", "797 features",
        "RF 100 trees; HistGradientBoosting 300 iterations; XGBoost 300 trees, depth 6, learning rate 0.1"),
       ("U1 ANN", "MLP", "797 features", "797-256-128-1, ReLU, dropout 0.1, Adam 1e-3, MSE, 30 epochs; tuned over dropout, "
        "learning rate, layer sizes and optimiser"),
       ("U2 CNN", "1-D CNN, LeNet / VGG / ResNet styles", "25 x 797 sequence",
        "final VGG style: 2 blocks of two Conv1D layers (32, 64 filters, kernel 3) + max pooling, then dropout 0.1, Dense 64, Dense 1"),
       ("U2 transfer", "CNN pretrained on 2 languages", "25 x 797 sequence",
        "zero-shot, head-only, full fine-tune (lr 1e-4), or scratch on part of one conversation of the 3rd language"),
       ("U4 RNN", "Simple RNN, LSTM, GRU", "25 x 797 sequence", "one recurrent layer of 128 units + the same head"),
       ("U5 Autoencoder", "Autoencoder", "797 features", "797-256-32-256-797; the 32-number code feeds a dense head or XGBoost"),
       ("U5 Transformer", "Encoder (our own)", "25 x 797 sequence",
        "Dense 64 projection + learned positional encoding, 2 encoder blocks (4-head self-attention, feed-forward 128, "
        "residual + layer norm), average pooling, head; about 124,000 parameters"),
       ("U5 pretrained", "XLM-RoBERTa, w2v-BERT 2.0, CLIP, DINOv2, Swin, VideoMAE", "embeddings per window",
        "Transformer frozen; a trained XGBoost head and a dense head (256-128)")],
      "Models trained in the project.", widths=[2.2, 3.8, 2.8, 7.8], size=8.8)
p("U3 (NLP) is outside the scope by design, because the study is non-verbal. XLM-RoBERTa embeddings of the "
  "transcript are used only as a comparison point.")

# ------------------------------------------------------------------ 6 implementation
h1("6. Implementation")
h2("6.1 Environment")
table(["Item", "Version"],
      [("Python", "3.12 (virtual environment .venv)"), ("TensorFlow / Keras", "2.21 / 3.15"), ("scikit-learn", "1.4.2"),
       ("XGBoost", "3.4.0"), ("pandas / NumPy", "2.1.4 / 1.26.4"), ("Matplotlib / seaborn", "3.7.5 / 0.13.2"),
       ("Streamlit", "1.66.1"), ("Hardware", "Windows 11 laptop, CPU only, 16 GB RAM")],
      "Software environment (full list in requirements.txt).", widths=[5, 8])
h2("6.2 Project structure")
figure(os.path.join(SHOTS, "console_tree.png"), "Project folder: pipeline scripts in src/, document generators in tools/.", width=12)
table(["Script", "What it does"],
      [("01_extract_data.py", "Pull voice, face, label and language files out of the NoXi zips"),
       ("02_build_features.py", "Build the one-second window table and the 25-frame sequences"),
       ("03_eda.py", "Exploratory analysis, charts and statistics"),
       ("04_baselines.py", "ML baselines (random split, development)"),
       ("05_cross_lingual.py", "Train on one language, test on another (3 x 3 matrix)"),
       ("06_deep_learning.py / 07_tuning.py", "ANN and its tuning"),
       ("08_sequence_models.py / 09_cnn.py", "XGBoost vs MLP vs 1-D CNN; CNN tuning"),
       ("10_transfer_learning.py", "Cross-language transfer learning by conversation"),
       ("11_cnn_architectures.py", "LeNet, VGG and ResNet-style CNNs"),
       ("12_transformer.py / 13_lstm.py", "Transformer encoder and LSTM (development)"),
       ("14_session_eval.py", "Final evaluation of ML models and the ANN on unseen conversations"),
       ("15_session_sequence.py", "Final evaluation of CNN, Simple RNN, LSTM, GRU, Transformer"),
       ("16_autoencoder.py", "Autoencoder and regression on its code"),
       ("17_ablation.py", "Voice vs face vs both"),
       ("18_master_results.py", "Master results table and chart"),
       ("19_pretrained_features.py", "Pretrained Transformer embeddings per window"),
       ("20_pretrained_transformers.py", "Trained heads on the frozen pretrained Transformers"),
       ("21_smoothing.py", "Smoothing predictions over the last 5 seconds"),
       ("22_partner.py", "Adding the other speaker's features"),
       ("23_context.py", "Adding the mean of the last 5 s and 10 s (past context)"),
       ("24_fusion.py", "Fusion of eGeMAPS, w2v-BERT 2.0 and VideoMAE with context (best model)"),
       ("25_transformer_context.py", "Our Transformer with 10 s of input and the cross-language test"),
       ("26_significance.py", "Wilcoxon test per speaker, bootstrap intervals, Holm correction"),
       ("27_person_disjoint.py / splits.py", "Re-evaluation with no person shared between training and test"),
       ("notebooks/", "Simple Jupyter versions of the 12 main steps (same results)"),
       ("app.py", "Streamlit demo application")],
      "Pipeline scripts.", widths=[5.6, 10.8], size=9)
h2("6.3 Key code")
p("The metric, used by every script:")
code("""def ccc(yt, yp):
    yt, yp = np.asarray(yt), np.asarray(yp)
    cov = ((yt - yt.mean()) * (yp - yp.mean())).mean()
    return (2 * cov) / (yt.var() + yp.var() + (yt.mean() - yp.mean()) ** 2 + 1e-9)""")
p("Session-wise folds: each fold holds out one whole conversation per language.")
code("""sess = df.groupby("language")["session"].unique().apply(sorted)
folds = [[s[k] for s in sess] for k in range(3)]
for test_sess in folds:
    te = df["session"].isin(test_sess).to_numpy()
    pipe = make_pipeline(StandardScaler(), XGBRegressor(...)).fit(X[~te], y[~te])
    score = ccc(y[te], pipe.predict(X[te]))""")
p("Scaling for neural networks: fitted on training conversations only, extreme values clipped.")
code("""sc = StandardScaler().fit(X[tr])
X_tr = np.clip(sc.transform(X[tr]), -5, 5)
X_te = np.clip(sc.transform(X[te]), -5, 5)""")
p("Our Transformer encoder block (Keras):")
code("""def encoder_block(x, drop=0.1):
    attn = layers.MultiHeadAttention(num_heads=4, key_dim=16, dropout=drop)(x, x)
    x = layers.LayerNormalization(epsilon=1e-6)(layers.Add()([x, attn]))
    ff = layers.Dense(128, activation="relu")(x)
    ff = layers.Dense(64)(layers.Dropout(drop)(ff))
    return layers.LayerNormalization(epsilon=1e-6)(layers.Add()([x, ff]))""")
p("Pretrained Transformers: frame embeddings are averaged into the same one-second windows, then only a head is trained.")
code("""E = read_zip_stream(z, f"{sess}/{role}.{stream}.stream")      # e.g. w2vbert2, videomae
win = np.stack([np.nanmean(E[w*25:(w+1)*25], 0) for w in keep])  # one row per second
X = np.concatenate([np.load(f"pretrained_{p}.npy") for p in parts], axis=1)
xgb_f.append(xgb_score(~te, te)); dense_f.append(dense_score(~te, te))""")
h2("6.4 Console output")
for name, cap in (("cross_lingual", "src/05_cross_lingual.py: the language-by-language matrix."),
                  ("master", "src/18_master_results.py: all models on unseen conversations."),
                  ("pretrained_features", "src/19_pretrained_features.py: pretrained embeddings aligned with every window."),
                  ("pretrained_eval", "src/20_pretrained_transformers.py: frozen pretrained Transformers with trained heads.")):
    path = os.path.join(SHOTS, f"console_{name}.png")
    if os.path.exists(path):
        figure(path, f"Console output of {cap}", width=16)

# ------------------------------------------------------------------ 7 results
h1("7. Results")
h2("7.1 Data leakage: random split vs unseen conversations")
p(f"The first experiments split windows at random. Because neighbouring seconds of one conversation are almost "
  f"identical, the test set contained near-copies of the training data, and every model looked far better than it is. "
  f"Holding out whole conversations removed the leak: XGBoost fell from {xgb.random_split_ccc:.3f} to {xgb.session_ccc:.3f}. "
  f"All results after this section use unseen conversations.")
figure(os.path.join(FIG, "report_leakage.png"), "The same models scored with a random split and on unseen conversations.", width=15)
h2("7.2 All models on unseen conversations")
figure(os.path.join(FIG, "report_all_models.png"), "CCC of every final model on unseen conversations (mean and std over 3 folds).", width=16)
rows = [(r.model, r.family, f"{r.session_ccc:.3f} ± {r.session_std:.3f}", f3(r.pearson), f3(r.mae),
         "" if pd.isna(r.random_split_ccc) else f3(r.random_split_ccc)) for r in ms.itertuples()]
table(["Model", "Family", "CCC (unseen)", "Pearson", "MAE", "CCC (random split)"], rows,
      "Models trained from scratch on eGeMAPS + OpenFace features.", widths=[4.4, 2.6, 3.2, 1.8, 1.6, 2.8], size=9)
p(f"Tree ensembles are the strongest models on our own features (Gradient Boosting {gb.session_ccc:.3f}). Among neural "
  "networks, the ANN and our Transformer come closest. The sequence models (RNN, LSTM, GRU) vary most between folds, "
  "which suggests they overfit the six training conversations. Linear Regression fails, so the relation between "
  "behaviour and engagement is not linear.")
h2("7.3 Cross-language transfer")
figure(os.path.join(FIG, "report_cross_lingual.png"), f"CCC when training on one language and testing on another (Random Forest, voice + face).", width=11)
p(f"Same-language CCC averages {diag:.3f}; other-language CCC averages {off:.3f}, a {drop}% drop. The drop is uneven: "
  f"a German-trained model transfers well to French ({cm.loc['German', 'French']:.3f}), while a French-trained model "
  f"almost fails on English ({cm.loc['French', 'English']:.3f}).")
h2("7.4 Voice vs face (ablation)")
table(["Input", "Features", "CCC (unseen)", "Within-language", "Cross-language", "Drop"],
      [(r.Index, r.n_features, f"{r.session_ccc:.3f} ± {r.session_std:.3f}", f3(r.within_ccc), f3(r.cross_ccc), f"{r.drop_pct:.0f}%")
       for r in ab.set_index("modality").itertuples()],
      "XGBoost with voice only, face only, and both.", widths=[2.4, 2.2, 3.4, 3.0, 3.0, 2.0])
p(f"Voice alone ({abl.loc['voice', 'session_ccc']:.3f}) beats voice + face ({abl.loc['both', 'session_ccc']:.3f}), and it "
  f"keeps most of its accuracy in a new language ({abl.loc['voice', 'drop_pct']:.0f}% drop). Face features lose "
  f"{abl.loc['face', 'drop_pct']:.0f}%. Section 8 shows these next to the pretrained Transformers.")
h2("7.5 Transfer learning")
figure(os.path.join(FIG, "report_transfer.png"), "Adapting a CNN pretrained on two languages to the third.", width=14)
byt = tr[tr.fraction == 1.0].groupby("target")[["zero_shot", "head_only", "fine_tune", "scratch"]].mean()
table(["Target language", "Zero-shot", "Head only", "Fine-tune", "From scratch"],
      [(l, *[f3(v) for v in r]) for l, r in byt.iterrows()],
      "Transfer learning by target language, using 100% of one adaptation conversation.", widths=[3.4, 2.8, 2.8, 2.8, 2.8])
p(f"Full fine-tuning is the best strategy at every amount of target data. With only 10% of one conversation it reaches "
  f"{gtr.fine_tune.iloc[0]:.3f}, while a model trained from scratch on the same data reaches {gtr.scratch.iloc[0]:.3f}. "
  "Training only the head does not beat zero-shot, so the lower layers need to adapt too.")
h2("7.6 Development stage (random split)")
dev = [("ANN, best of 13 tuning runs (256-128, dropout 0.1, Adam 1e-3)", "U1", f3(R("tuning_results").val_ccc.max()), "validation"),
       ("CNN, best of 8 tuning runs (32 filters, kernel 5, dropout 0.1)", "U2", f3(R("cnn_tuning_results").val_ccc.max()), "validation")]
dev += [(f"CNN {r.model.replace('_', '-')}", "U2", f3(r.test_ccc), "test") for r in R("cnn_architectures").itertuples()]
dev += [(f"{r.model} (sequence experiment)", "ML / U1 / U2", f3(r.ccc), "test") for r in R("sequence_results").itertuples()]
dev += [(r.model, "U4", f3(r.test_ccc), "test") for r in R("lstm_results").itertuples()]
dev += [(r.model, "U5", f3(r.test_ccc), "test") for r in R("transformer_results").itertuples()]
table(["Experiment", "Unit", "CCC", "Split"], dev,
      "Development-stage results. These use the leaky random split and are not comparable with Sections 7.1-7.5.",
      widths=[9.4, 2.4, 1.8, 2.4], size=9)
p("Tuning showed that light dropout (0.1) works better than heavy dropout (0.5), Adam beats SGD, and the VGG-style "
  "CNN is the best of the three CNN designs. These settings were carried into the final evaluation.")

# ------------------------------------------------------------------ 8 pretrained
h1("8. Pretrained Transformers")
p("Large Transformers pretrained on millions of examples can serve as feature extractors. The NoXi release provides "
  "frame-level embeddings from six of them, computed by the dataset authors. We averaged each into our one-second "
  "windows, kept the Transformer frozen, and trained only a head on top: this is transfer learning by feature "
  "extraction. Fine-tuning the Transformers end to end needs a GPU and was not possible on our laptop.")
table(["Model", "Type", "Input", "Dims", "XGBoost head", "Dense head", "Within", "Cross", "Drop"],
      [(r.model, t_, r.input, f"{r.dims:,}", f"{r.xgb_ccc:.3f} ± {r.xgb_std:.3f}", f"{r.dense_ccc:.3f} ± {r.dense_std:.3f}",
        f3(r.within_ccc), f3(r.cross_ccc), f"{max(r.drop_pct, 0):.0f}%")
       for r, t_ in zip(pt.itertuples(), ["multilingual BERT family", "speech (wav2vec2 / BERT style)", "image encoder",
                                          "Vision Transformer", "hierarchical ViT", "video Transformer", "fusion"])],
      "Frozen pretrained Transformers with a trained head, on unseen conversations.",
      widths=[2.9, 2.6, 1.6, 1.2, 2.2, 2.2, 1.3, 1.3, 1.1], size=8)
figure(os.path.join(FIG, "report_within_vs_cross.png"), "Same-language vs other-language CCC for every input.", width=15.5)
bullets([
    ("Best overall: ", f"w2v-BERT 2.0 + VideoMAE with a dense head, CCC {best_pt_ccc:.3f} ± {best_pt.dense_std:.3f}, the "
     f"highest and one of the most stable results in the project."),
    ("Speech transfers perfectly: ", f"w2v-BERT 2.0 scores {w2v.within_ccc:.3f} within a language and {w2v.cross_ccc:.3f} across."),
    ("Video models fail across languages: ", "CLIP, DINOv2 and Swin lose 41% to 106%, like our OpenFace features."),
    ("Text is weak: ", "XLM-RoBERTa on the transcript reaches only 0.393, which supports the non-verbal approach."),
])
p("w2v-BERT 2.0 is a speech model and may encode some word content as well as tone of voice, so we describe it as "
  "pretrained speech features rather than purely non-verbal ones.", italic=True)
doc.paragraphs[-2].paragraph_format.keep_with_next = True

# ------------------------------------------------------------------ 9 improvements and checks
h1("9. Improvements and Checks")
p("After the main comparison we tried five improvements, each with settings fixed in advance (not tuned on the test "
  "folds), on the same three folds of unseen conversations. Then we checked the best result in two ways.")
h2("9.1 Improvements")
table(["Experiment", "Script", "CCC (unseen)", "Within", "Cross", "Drop"],
      [("Baseline: Gradient Boosting, voice + face, 1 s", "14", f"{gb_sm.raw_ccc:.3f} ± {gb_sm.raw_std:.3f}", f3(gb_sm.raw_within), f3(gb_sm.raw_cross), f"{gb_sm.raw_drop_pct:.0f}%"),
       ("Smoothing predictions over the last 5 s", "21", f"{gb_sm.smooth_ccc:.3f} ± {gb_sm.smooth_std:.3f}", f3(gb_sm.smooth_within), f3(gb_sm.smooth_cross), f"{gb_sm.smooth_drop_pct:.0f}%"),
       ("Adding the partner's features", "22", f"{gb_pa.ccc:.3f} ± {gb_pa['std']:.3f}", f3(gb_pa.within_ccc), f3(gb_pa.cross_ccc), f"{gb_pa.drop_pct:.0f}%"),
       ("Adding past context (last 5 s and 10 s)", "23", f"{gb_ctx.ccc:.3f} ± {gb_ctx['std']:.3f}", f3(gb_ctx.within_ccc), f3(gb_ctx.cross_ccc), f"{max(gb_ctx.drop_pct, 0):.0f}%"),
       ("Fusion: eGeMAPS + w2v-BERT 2.0 + VideoMAE, 1 s", "24", f"{fu1.ccc:.3f} ± {fu1['std']:.3f}", "-", "-", "-"),
       ("Fusion + past context (best model)", "24", f"{best.ccc:.3f} ± {best['std']:.3f}", f3(best.within_ccc), f3(best.cross_ccc), f"{max(best.drop_pct, 0):.0f}%"),
       ("Own Transformer, 1 s of input", "25", f"{t1.ccc:.3f} ± {t1['std']:.3f}", f3(t1.within_ccc), f3(t1.cross_ccc), f"{t1.drop_pct:.0f}%"),
       ("Own Transformer, 10 s of input", "25", f"{t10.ccc:.3f} ± {t10['std']:.3f}", f3(t10.within_ccc), f3(t10.cross_ccc), f"{t10.drop_pct:.0f}%")],
      "Improvements (Gradient Boosting unless stated), on unseen conversations.", widths=[5.6, 1.3, 2.6, 1.6, 1.6, 1.4], size=9)
bullets([
    ("Smoothing ", f"adds a little ({gb_sm.raw_ccc:.3f} to {gb_sm.smooth_ccc:.3f}): engagement changes slowly, so averaging recent predictions removes noise."),
    ("The partner's features ", f"do not raise accuracy ({gb_pa.ccc:.3f}) but halve the cross-language drop ({gb_sm.raw_drop_pct:.0f}% to {gb_pa.drop_pct:.0f}%)."),
    ("Past context ", f"gives the largest single gain ({gb_ctx.ccc:.3f}), removes the language drop and makes the folds very stable (± {gb_ctx['std']:.3f})."),
    ("Fusion with context ", f"gives the best model of the project: CCC {best.ccc:.3f}, {max(best.drop_pct, 0):.0f}% drop."),
    ("Our Transformer ", f"also gains from a longer input: {t1.ccc:.3f} with one second, {t10.ccc:.3f} with ten, and its drop falls from {t1.drop_pct:.0f}% to {t10.drop_pct:.0f}%."),
])
h2("9.2 Is the improvement real? Significance test")
p("Three folds are too few for a test on fold scores, so the models are compared person by person: every one of the 18 "
  "speakers is predicted by a model that never saw their conversation, CCC is computed per speaker, and pairs of models "
  "are compared with a Wilcoxon signed-rank test, a bootstrap 95% interval and a Holm correction for the three comparisons.")
table(["Comparison", "Mean difference", "95% interval", "Speakers better", "p (Holm)"],
      [({"C vs A": "Best vs baseline", "B vs A": "Context vs baseline", "C vs B": "Best vs context"}[c], f"+{r.mean_diff:.3f}", f"[{r.ci_low:.3f}, {r.ci_high:.3f}]", r.a_better, f"{r.p_holm:.4f}")
       for c, r in s_spk.iterrows()],
      "Speaker-level significance (A = baseline, B = + context, Best = fusion + context).", widths=[4.6, 2.8, 3.4, 2.8, 2.6], size=9.5)
p("All three gains are significant (p < 0.05); they also stay significant when the 9 conversations are used instead of the 18 speakers.")
h2("9.3 Unseen people: person-disjoint evaluation")
p("Two NoXi participants appear in two of our conversations each, so a conversation-disjoint split could still place "
  "the same person in training and test. The key models were re-evaluated with folds that keep every person's "
  "conversations together.")
table(["Input (Gradient Boosting)", "Unseen conversations", "Unseen people", "Drop (unseen people)"],
      [(i, f3(r.ccc_old), f"{r.ccc_new:.3f} ± {r.std_new:.3f}", f"{max(r.drop_new, 0):.0f}%") for i, r in pdj.iterrows()],
      "Conversation-disjoint vs person-disjoint folds.", widths=[5.2, 3.6, 3.6, 3.6], size=9.5)
p(f"Scores fall by about 0.02-0.04 for voice-based inputs and by 0.09 for face (the face model partly recognised familiar "
  f"people). The best model keeps CCC {best_new.ccc_new:.3f} with no language drop, so the conclusions hold.")

# ------------------------------------------------------------------ 10 demo
h1("10. Demo Application")
p("The Streamlit app (streamlit run app.py) shows the final models working on conversations they never saw. In the "
  "Live prediction tab the user picks a conversation, a speaker and an input (voice + face, voice only, or face only), "
  "and the app plots predicted against true engagement second by second with CCC and Pearson for that speaker. It always "
  "uses the fold model that held that conversation out. The Results tab shows every results table.")
figure(os.path.join(SHOTS, "app_live.png"), "Live prediction tab: an English conversation the model never saw.", width=16)
figure(os.path.join(SHOTS, "app_results.png"), "Results tab: all models, pretrained Transformers, ablation, cross-lingual matrix and transfer learning.", width=13)

# ------------------------------------------------------------------ 10 discussion
h1("11. Discussion")
h2("11.1 Answers to the research questions")
table(["Question", "Answer"],
      [("RQ1. Prediction on unseen conversations", f"Yes: CCC {gb.session_ccc:.3f} with our features, {best_pt_ccc:.3f} with pretrained Transformers, {best.ccc:.3f} with fusion and context."),
       ("RQ2. Cost of a new language", f"{drop}% on average (CCC {diag:.3f} to {off:.3f}), and very uneven between language pairs."),
       ("RQ3. Voice or face", f"Voice: it is the stronger signal and loses only {abl.loc['voice', 'drop_pct']:.0f}% across languages; face loses {abl.loc['face', 'drop_pct']:.0f}%."),
       ("RQ4. Best architectures", "Tree ensembles on strong features. Among deep models trained from scratch, our Transformer is the most stable; frozen pretrained speech and video Transformers give the strongest features."),
       ("RQ5. Transfer learning", f"Yes: fine-tuning on 10% of one conversation reaches {gtr.fine_tune.iloc[0]:.3f} vs {gtr.scratch.iloc[0]:.3f} from scratch."),
       ("RQ6. Context, partner, fusion", f"Past context helps most; the partner does not raise accuracy; fusion with context gives the best model ({best.ccc:.3f}), significantly better than the baseline (p = {s_spk.loc['C vs A', 'p_holm']:.3f}).")],
      "Summary of answers.", widths=[5.2, 11.2], size=9.5)
h2("11.2 Why the face transfers worse than the voice")
p("Average engagement is almost the same in all three languages, so people are engaged to a similar degree but the face "
  "features change between groups. Part of this may be cultural, as the literature on facial expressions suggests. Part "
  "may be technical: each language was recorded at a different site, with a different room, camera and lighting, which "
  "affects face and video features much more than voice. Our data cannot separate the two causes.")
h2("11.3 Comparison with published NoXi work")
p("The NoXi paper (Cafaro et al., 2017) introduced the dataset and did not train engagement models. The MultiMediate "
  "challenges built engagement benchmarks on the full dataset with deep sequence and attention models, often using both "
  "speakers together. Our setting is different: 9 conversations, one-second windows, one speaker at a time, and session-"
  "held-out folds, so our CCC values cannot be compared directly with challenge results. Our contribution is the "
  "controlled study: the full language matrix, the voice/face separation, the leakage analysis, transfer learning, and "
  "a broad comparison of model families under one protocol.")
p("Our single-feature results are close to the MultiMediate'24 baseline on the NoXi test set (w2v-BERT 2.0: 0.631 vs "
  "0.64; XLM-RoBERTa: 0.393 vs 0.40), which supports the correctness of the pipeline. The same patterns appear: OpenFace "
  "features lost 54% on new languages there and 55% here, and the CEAM model improved with a longer window (0.691 to "
  "0.711) while cross-attention to the partner did not add more. The best published NoXi systems reach 0.71-0.76 on the "
  "official test set; our 0.777 is in the same range but not directly comparable.")
h2("11.4 Limitations")
bullets([
    "Only 9 conversations (3 per language) are used, so each fold tests on just 3 conversations and the standard deviations are large.",
    "Language is confounded with recording site.",
    "The partner's behaviour was added only by placing the features side by side; cross-attention between speakers was not tried.",
    "Pretrained Transformers were used frozen, without end-to-end fine-tuning (no GPU; the licensed data cannot be uploaded to cloud services).",
    "One-second averaging may hide short events such as nods or brief smiles.",
    "Two participants appear in two conversations each; the person-disjoint check (section 9.3) shows this changes the scores only slightly.",
    "The settings of the improvements were fixed in advance, but several variants were compared on the same three folds; the significance test addresses this for the main comparisons.",
])

# ------------------------------------------------------------------ 11 conclusion
h1("12. Conclusion and Future Work")
p(f"We built a complete pipeline that predicts engagement from non-verbal behaviour and evaluated {n_models} models from "
  f"every syllabus unit on conversations they never saw. The study shows that a random split badly overstates accuracy, "
  f"that moving to a new language costs about {drop}%, that the voice carries engagement across languages far better than "
  f"the face, and that pretrained speech and video Transformers give strong features. Fine-tuning with a small amount of "
  f"target-language data recovers much of the lost accuracy. Past context and feature fusion produced the best model, "
  f"CCC {best.ccc:.3f} with a {max(best.drop_pct, 0):.0f}% language drop, significantly better than the baseline and "
  f"robust to a person-disjoint evaluation (CCC {best_new.ccc_new:.3f}).")
h2("12.1 Possible next steps")
table(["Step", "What it adds", "Effort"],
      [("More NoXi conversations", "About 20 conversations were prepared (6-7 per language); retrain and compare 9 vs 20", "about 1 day"),
       ("Fine-tune the pretrained Transformers", "Let w2v-BERT 2.0 and VideoMAE learn engagement directly", "needs a university GPU"),
       ("Cross-attention between speakers", "Let each speaker's model attend to the partner over 30 s, as in recent work", "1-2 days"),
       ("Japanese and Chinese (NoXi+J)", "Test transfer to Asian languages and cultures", "several days"),
       ("Separate language from recording site", "Expert vs novice and per-site analysis", "1-2 days")],
      "Possible next steps, for discussion with the supervisor.", widths=[4.8, 8.6, 3.0], size=9.5)

# ------------------------------------------------------------------ 12 ethics
h1("13. Ethics, Data Licence and Use of AI Tools")
bullets([
    ("Data licence. ", "NoXi is used under its End-User Licence Agreement, signed by the supervisor. The data and anything "
     "derived from it (feature tables, embeddings) stay on the project computer and are excluded from the GitHub repository; "
     "they are never uploaded to online services."),
    ("Privacy. ", "Results are reported only as aggregate scores. No raw recordings or personal data appear in this report."),
    ("Responsible use. ", "Engagement predictions are estimates with moderate accuracy and should support, not replace, human judgement."),
    ("Use of AI tools. ", "An AI coding assistant (Claude) helped write code, run experiments and draft documents, including "
     "this report. All results come from running the code on our own machine. [Edit this statement to describe your own use.]"),
])

# ------------------------------------------------------------------ references
h1("References")
for n, (_, r) in enumerate(lit.iterrows(), 1):
    para = doc.add_paragraph()
    para.paragraph_format.left_indent = Cm(0.9)
    para.paragraph_format.first_line_indent = Cm(-0.9)
    para.paragraph_format.space_after = Pt(3)
    run = para.add_run(f"[{n}]  " + str(r["APA Ref (Google Scholar Cite)"]).strip())
    run.font.size = Pt(9.5)

# ------------------------------------------------------------------ appendix
h1("Appendix A. How to Run")
p("From the project folder, in a terminal:")
code("""py -3.12 -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt

python src/01_extract_data.py "C:/path/to/train.zip" "C:/path/to/027.zip"
python src/02_build_features.py
python src/03_eda.py
python src/05_cross_lingual.py
python src/14_session_eval.py
python src/15_session_sequence.py          # about 30 minutes
python src/16_autoencoder.py
python src/17_ablation.py
python src/10_transfer_learning.py
python src/18_master_results.py
python src/19_pretrained_features.py "C:/path/to/train.zip" "C:/path/to/027.zip"
python src/20_pretrained_transformers.py   # add --retrain to train again
python src/21_smoothing.py
python src/22_partner.py
python src/23_context.py
python src/24_fusion.py                    # best model, about 1 hour
python src/25_transformer_context.py
python src/26_significance.py
python src/27_person_disjoint.py
streamlit run app.py""")
p("The notebooks/ folder holds simple versions of the 12 main steps; each one ends by comparing its results with the "
  "results saved by the scripts.")
h1("Appendix B. Deliverables", new_page=False)
table(["Deliverable", "File", "Status"],
      [("Code and trained models", "src/, tools/, reports/", "complete"),
       ("Demo application", "app.py", "complete"),
       ("All results tables", "All_Results_Tables.docx / .xlsx", "complete"),
       ("Literature review", "Literature_Review.xlsx", "complete"),
       ("Project report", "Project_Report_Final.docx (this file)", "complete"),
       ("Research paper (IEEE)", "Research_Paper_Draft_v4.docx", "complete draft; to submit"),
       ("Simple notebooks", "notebooks/ (12 notebooks)", "complete"),
       ("Presentation and poster", "Project_Presentation.pptx, Research_Poster.pptx", "to update with the improvements"),
       ("Laboratory manual", "Laboratory_Manual.docx", "to update with steps 19-27"),
       ("Demo video", "-", "to record")],
      "Project deliverables.", widths=[4.6, 7.6, 4.2], size=9.5)

out = "Project_Report_Final.docx"
doc.save(out)
print(f"saved {out}: {counters['Figure']} figures, {counters['Table']} tables")
