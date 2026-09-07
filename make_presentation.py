"""Generate the project presentation (PowerPoint)."""
import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION

NAVY = RGBColor(0x0D, 0x27, 0x38)
TEAL = RGBColor(0x02, 0x80, 0x90)
MINT = RGBColor(0x02, 0xC3, 0x9A)
INK = RGBColor(0x1A, 0x2A, 0x33)
MUTED = RGBColor(0x5F, 0x70, 0x7A)
LIGHT = RGBColor(0xFF, 0xFF, 0xFF)
CLOUD = RGBColor(0xED, 0xF3, 0xF5)
HEAD, BODY = "Cambria", "Calibri"

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]
W, H = prs.slide_width, prs.slide_height
FIG = os.path.join("reports", "figures")


def slide(bg=LIGHT):
    s = prs.slides.add_slide(BLANK)
    r = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, W, H)
    r.fill.solid(); r.fill.fore_color.rgb = bg
    r.line.fill.background(); r.shadow.inherit = False
    s.shapes._spTree.remove(r._element); s.shapes._spTree.insert(2, r._element)
    return s


def box(s, x, y, w, h, text, size, color, bold=False, font=BODY, align=PP_ALIGN.LEFT,
        anchor=MSO_ANCHOR.TOP, italic=False, sp=6):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, ln in enumerate(text if isinstance(text, list) else [text]):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align; p.space_after = Pt(sp)
        r = p.add_run(); r.text = ln
        r.font.size = Pt(size); r.font.bold = bold; r.font.italic = italic
        r.font.name = font; r.font.color.rgb = color
    return tb


def chip(s, x, y, w, h, fill, text, size, tc, shape=MSO_SHAPE.ROUNDED_RECTANGLE):
    sh = s.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.fill.solid(); sh.fill.fore_color.rgb = fill
    sh.line.fill.background(); sh.shadow.inherit = False
    tf = sh.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = text
    r.font.size = Pt(size); r.font.bold = True; r.font.name = BODY; r.font.color.rgb = tc
    return sh


def card(s, x, y, w, h, fill=CLOUD):
    c = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    c.fill.solid(); c.fill.fore_color.rgb = fill
    c.line.fill.background(); c.shadow.inherit = False
    return c


def title(s, t, num=None):
    if num:
        chip(s, 0.85, 0.5, 0.62, 0.62, TEAL, num, 20, LIGHT, shape=MSO_SHAPE.OVAL)
        box(s, 1.68, 0.5, 10.8, 0.85, t, 32, NAVY, bold=True, font=HEAD, anchor=MSO_ANCHOR.MIDDLE)
    else:
        box(s, 0.85, 0.5, 11.6, 0.85, t, 32, NAVY, bold=True, font=HEAD, anchor=MSO_ANCHOR.MIDDLE)


def img(s, path, x, y, w=None):
    if os.path.exists(path):
        s.shapes.add_picture(path, Inches(x), Inches(y), width=Inches(w) if w else None)


def table(s, data, x, y, w, h, colw=None, highlight_diag=False):
    t = s.shapes.add_table(len(data), len(data[0]), Inches(x), Inches(y), Inches(w), Inches(h)).table
    if colw:
        for i, cw in enumerate(colw):
            t.columns[i].width = Inches(cw)
    for ri, row in enumerate(data):
        for ci, val in enumerate(row):
            c = t.cell(ri, ci); c.fill.solid()
            if ri == 0 or (highlight_diag and ci == 0):
                c.fill.fore_color.rgb = NAVY
            elif highlight_diag and ri == ci:
                c.fill.fore_color.rgb = MINT
            else:
                c.fill.fore_color.rgb = CLOUD if ri % 2 else LIGHT
            p = c.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER if highlight_diag else PP_ALIGN.LEFT
            r = p.add_run(); r.text = str(val)
            r.font.size = Pt(13); r.font.name = BODY
            r.font.bold = (ri == 0 or ci == 0 or (highlight_diag and ri == ci))
            r.font.color.rgb = LIGHT if (ri == 0 or (highlight_diag and ci == 0)) else INK
    return t


def bar_chart(s, x, y, w, h, cats, vals, maxv=1.0, horizontal=False):
    cd = CategoryChartData(); cd.categories = cats; cd.add_series("CCC", vals)
    kind = XL_CHART_TYPE.BAR_CLUSTERED if horizontal else XL_CHART_TYPE.COLUMN_CLUSTERED
    gf = s.shapes.add_chart(kind, Inches(x), Inches(y), Inches(w), Inches(h), cd)
    ch = gf.chart; ch.has_legend = False; ch.has_title = False
    pl = ch.plots[0]; pl.has_data_labels = True
    pl.data_labels.number_format = '0.000'; pl.data_labels.number_format_is_linked = False
    pl.data_labels.font.size = Pt(11); pl.data_labels.font.bold = True
    pl.data_labels.position = XL_LABEL_POSITION.OUTSIDE_END
    ch.series[0].format.fill.solid(); ch.series[0].format.fill.fore_color.rgb = TEAL
    va = ch.value_axis; va.minimum_scale = 0; va.maximum_scale = maxv
    va.tick_labels.font.size = Pt(11); ch.category_axis.tick_labels.font.size = Pt(12)
    return ch


# ============ 1. TITLE ============
s = slide(NAVY)
chip(s, 0.9, 1.35, 3.4, 0.5, TEAL, "DEEP LEARNING  ·  PROJECT EVALUATION", 11, LIGHT)
box(s, 0.9, 2.05, 11.6, 2.3,
    ["Cross-Lingual Prediction of Engagement", "from Non-Verbal Behaviour in Conversations"],
    38, LIGHT, bold=True, font=HEAD, sp=6)
box(s, 0.9, 4.5, 11.0, 0.6,
    "Can an AI tell how engaged you are — from your face and voice alone — in any language?",
    17, MINT, italic=True)
box(s, 0.9, 6.25, 11.5, 0.8,
    ["Team: [Student 1]  ·  [Student 2]  ·  [Student 3]",
     "Dataset: NoXi   |   Framework: TensorFlow / Keras"], 13, CLOUD, sp=2)

# ============ 2. AGENDA ============
s = slide(); title(s, "Agenda")
items = [("1", "Research Problem"), ("2", "Dataset"), ("3", "EDA"),
         ("4", "Baseline Models"), ("5", "Cross-Lingual Experiment"),
         ("6", "Deep Learning + Tuning"), ("7", "Research Gap & Methodology"),
         ("8", "Literature Review"), ("9", "Conclusion")]
for i, (n, t) in enumerate(items):
    col, row = i // 5, i % 5
    x, y = 1.0 + col * 6.0, 1.7 + row * 1.02
    chip(s, x, y, 0.6, 0.6, TEAL, n, 17, LIGHT, shape=MSO_SHAPE.OVAL)
    box(s, x + 0.85, y, 4.7, 0.6, t, 18, INK, anchor=MSO_ANCHOR.MIDDLE)

# ============ 3. RESEARCH PROBLEM ============
s = slide(); title(s, "Research Problem", "1")
box(s, 0.9, 1.75, 7.0, 4.4, [
    "Most meaning in conversation is carried non-verbally — through tone of voice and facial "
    "expression, not the words.",
    "",
    "Engagement — how interested and involved a person is — is one of the most important of "
    "these non-verbal signals.",
    "",
    "The problem: can we predict engagement automatically, and does it work the SAME across "
    "different languages and cultures?"], 17, INK, sp=10)
for i, (n, t) in enumerate([("2", "non-verbal channels used:\nface + voice"),
                            ("3", "languages compared:\nFrench, English, German"),
                            ("0–1", "engagement predicted as a\ncontinuous value")]):
    y = 1.75 + i * 1.5
    card(s, 8.4, y, 4.0, 1.28)
    box(s, 8.65, y + 0.15, 1.5, 0.98, n, 30, TEAL, bold=True, font=HEAD, anchor=MSO_ANCHOR.MIDDLE)
    box(s, 10.15, y + 0.2, 2.1, 0.9, t.split("\n"), 11, MUTED, anchor=MSO_ANCHOR.MIDDLE, sp=1)
box(s, 0.9, 6.45, 11.6, 0.6,
    "Why it matters:  online education  ·  social robots & virtual agents  ·  fair AI for all languages",
    14, TEAL, bold=True)

# ============ 4. NON-VERBAL ============
s = slide(); title(s, "What 'Non-Verbal' Means")
box(s, 0.9, 1.5, 11.6, 0.5,
    "Non-verbal = everything EXCEPT the words. The spoken text is never used.",
    16, MUTED, italic=True)
for i, (t, d, e) in enumerate([
        ("VISUAL  ·  FACE", "Facial expressions, action units, gaze direction and head pose",
         "extracted with OpenFace 2.0  →  714 features"),
        ("VOCAL  ·  VOICE", "Pitch, loudness, rhythm and voice quality — how the voice sounds",
         "extracted with openSMILE / eGeMAPS  →  88 features")]):
    x = 0.9 + i * 6.05
    card(s, x, 2.25, 5.7, 3.3)
    chip(s, x + 0.35, 2.6, 3.4, 0.55, TEAL if i == 0 else MINT, t, 14, LIGHT if i == 0 else NAVY)
    box(s, x + 0.35, 3.45, 5.0, 1.3, d, 16, INK)
    box(s, x + 0.35, 4.85, 5.0, 0.5, e, 12, MUTED, italic=True)
box(s, 0.9, 6.1, 11.6, 0.7,
    "The same sentence said with an engaged vs. bored tone looks and sounds different — "
    "that difference is the non-verbal signal we learn from.", 14, TEAL, bold=True)

# ============ 5. RESEARCH QUESTIONS ============
s = slide(); title(s, "Research Questions")
for i, q in enumerate([
        "Can engagement be predicted from non-verbal cues (face + voice) alone?",
        "How do engagement patterns differ across languages?",
        "Does a model trained on one language transfer to speakers of another?"]):
    y = 2.0 + i * 1.45
    chip(s, 1.0, y, 0.85, 0.85, TEAL, str(i + 1), 26, LIGHT, shape=MSO_SHAPE.OVAL)
    box(s, 2.2, y, 10.2, 1.0, q, 19, INK, anchor=MSO_ANCHOR.MIDDLE)
box(s, 0.9, 6.4, 11.6, 0.6,
    "Question 3 is the core of this project — and the gap in existing research.", 15, TEAL, bold=True)

# ============ 6. DATASET ============
s = slide(); title(s, "Dataset — NoXi", "2")
table(s, [["Property", "Detail"],
          ["Source", "NoXi (Novice–Expert Interaction) database"],
          ["Content", "Real screen-mediated conversations"],
          ["Roles", "One expert + one novice per session"],
          ["Languages", "French, English, German (3 sessions each)"],
          ["Modalities", "Video (face) + Audio (voice)"],
          ["Label", "Engagement, continuous 0–1, at 25 Hz"]],
      0.9, 1.7, 7.5, 4.1, colw=[2.3, 5.2])
card(s, 8.7, 1.7, 3.7, 4.1, NAVY)
box(s, 8.95, 2.0, 3.3, 1.0, "17,174", 34, MINT, bold=True, font=HEAD)
box(s, 8.95, 2.9, 3.3, 0.5, "one-second windows", 13, CLOUD)
box(s, 8.95, 3.6, 3.3, 1.0, "802", 34, MINT, bold=True, font=HEAD)
box(s, 8.95, 4.5, 3.3, 1.1, ["features per window", "", "88 voice (eGeMAPS)",
                             "714 face (OpenFace 2.0)"], 12, CLOUD, sp=2)

# ============ 7. PREPROCESSING ============
s = slide(); title(s, "Preprocessing Pipeline")
for i, (n, t, dsc) in enumerate([
        ("1", "Extract", "Keep only voice, face\nand label files"),
        ("2", "Align", "Match features with\nengagement labels"),
        ("3", "Window", "Group 25 frames\ninto 1 second"),
        ("4", "Average", "Mean features and\nmean engagement"),
        ("5", "Scale", "Standardise all\nfeatures")]):
    x = 0.9 + i * 2.42
    card(s, x, 2.4, 2.15, 2.9)
    chip(s, x + 0.72, 2.65, 0.7, 0.7, TEAL, n, 21, LIGHT, shape=MSO_SHAPE.OVAL)
    box(s, x + 0.15, 3.5, 1.85, 0.5, t, 15, NAVY, bold=True, align=PP_ALIGN.CENTER, sp=0)
    box(s, x + 0.15, 4.1, 1.85, 1.0, dsc.split("\n"), 11, MUTED, align=PP_ALIGN.CENTER, sp=1)
    if i < 4:
        box(s, x + 2.08, 3.5, 0.35, 0.5, "→", 20, MINT, bold=True, align=PP_ALIGN.CENTER)
box(s, 0.9, 5.7, 11.6, 0.9,
    ["Result: a clean table of 17,174 rows × 802 features, each row labelled with its engagement.",
     "Missing values: 0   |   Balanced across languages"], 15, TEAL, bold=True, sp=4)

# ============ 8. EDA FINDINGS ============
s = slide(); title(s, "Exploratory Data Analysis — Findings", "3")
box(s, 0.9, 1.7, 5.6, 4.6, [
    "•  Balanced data:  French 6,568  |  German 5,630  |  English 4,976",
    "",
    "•  Engagement is mostly medium (~0.5); extremes are rare",
    "",
    "•  Experts are more engaged than novices  (0.66 vs 0.51)",
    "",
    "•  Voice features correlate with engagement more than face  (0.39 vs 0.19)",
    "",
    "•  ANOVA: languages differ significantly  (p < 0.001)"], 15, INK, sp=6)
img(s, os.path.join(FIG, "engagement_by_language.png"), 6.8, 1.9, w=6.1)

# ============ 9. EDA CHARTS ============
s = slide(); title(s, "EDA — Visualisations")
img(s, os.path.join(FIG, "engagement_distribution.png"), 0.7, 1.6, w=5.9)
img(s, os.path.join(FIG, "engagement_by_role.png"), 6.8, 1.6, w=5.9)
box(s, 0.9, 5.5, 11.6, 1.0,
    ["Left:  engagement is centred around 0.5 — people are rarely fully bored or fully absorbed.",
     "Right:  experts (0.66) are consistently more engaged than novices (0.51)."],
    14, MUTED, sp=4)

# ============ 10. EDA MODALITY ============
s = slide(); title(s, "EDA — Which Cues Matter?")
img(s, os.path.join(FIG, "voice_vs_face.png"), 0.9, 1.7, w=5.4)
img(s, os.path.join(FIG, "top_features.png"), 6.8, 1.7, w=5.9)
box(s, 0.9, 5.7, 11.6, 0.9,
    ["Voice features relate to engagement about twice as strongly as facial features (0.39 vs 0.19).",
     "This suggests vocal prosody is the stronger engagement signal in conversation."],
    15, TEAL, bold=True, sp=4)

# ============ 11. BASELINES ============
s = slide(); title(s, "Baseline Machine-Learning Models", "4")
bar_chart(s, 0.9, 1.8, 7.4, 4.6,
          ["Random Forest", "SVR", "Linear Regression"], (0.886, 0.827, 0.284))
card(s, 8.7, 2.0, 3.7, 3.7)
box(s, 8.95, 2.2, 3.3, 0.9, "0.886", 38, TEAL, bold=True, font=HEAD)
box(s, 8.95, 3.1, 3.3, 2.4, [
    "Best baseline: Random Forest",
    "",
    "Metric: CCC (0–1, higher is better)",
    "",
    "Linear Regression fails (R² = −3.4) — the data is not linear, which justifies "
    "using more powerful models."], 13, INK, sp=6)

# ============ 12. CROSS-LINGUAL ============
s = slide(); title(s, "Cross-Lingual Experiment — Key Result", "5")
box(s, 0.9, 1.45, 11.6, 0.45,
    "Train on one language, test on another. Each cell is a CCC score.",
    14, MUTED, italic=True)
table(s, [["Train \\ Test", "English", "French", "German"],
          ["English", "0.470", "0.354", "0.494"],
          ["French", "0.105", "0.596", "0.310"],
          ["German", "0.412", "0.665", "0.587"]],
      0.9, 2.1, 7.0, 2.9, colw=[1.9, 1.7, 1.7, 1.7], highlight_diag=True)
box(s, 8.3, 2.1, 4.2, 3.0, [
    "Green = same language",
    "",
    "Within-language average:  0.55",
    "Cross-language average:  0.39",
    "",
    "Performance drops when the model meets a new language."], 15, INK, sp=8)
box(s, 0.9, 5.5, 11.6, 1.2,
    ["FINDING:  Engagement is partly language-specific — a model trained on one language does "
     "not fully transfer to another.",
     "Engagement LEVELS are similar across languages, but HOW people express it differs."],
    15, TEAL, bold=True, sp=6)

# ============ 13. DEEP LEARNING ============
s = slide(); title(s, "Deep Learning Model — ANN", "6")
box(s, 0.9, 1.75, 6.4, 4.5, [
    "Model:  MLP (Multi-Layer Perceptron) — TensorFlow / Keras",
    "",
    "Architecture:   802  →  256  →  128  →  1",
    "Activation:  ReLU        Dropout:  0.1 (tuned)",
    "Optimizer:  Adam        Loss:  MSE",
    "",
    "Result:  CCC 0.883 after tuning  (0.861 before)",
    "",
    "Also implemented in PyTorch as a cross-check — both frameworks found the same best "
    "configuration."], 16, INK, sp=8)
card(s, 7.8, 1.95, 4.6, 3.9, NAVY)
box(s, 8.05, 2.25, 4.1, 0.95, "0.883", 42, MINT, bold=True, font=HEAD)
box(s, 8.05, 3.2, 4.1, 2.4, [
    "Tuned ANN — test CCC",
    "",
    "Matches the Random Forest baseline (0.886)",
    "",
    "Trained for 60 epochs on 802 non-verbal features"], 13, CLOUD, sp=6)

# ============ 14. TUNING ============
s = slide(); title(s, "Hyperparameter Tuning — Model Improvement")
box(s, 0.9, 1.45, 11.6, 0.5,
    "Grid search over dropout, learning rate, architecture and optimizer. "
    "Compared on a separate VALIDATION set; only the winner scored on TEST.",
    14, MUTED, italic=True)
table(s, [["Dropout", "Best validation CCC"],
          ["0.1", "0.857   ← best"],
          ["0.3", "0.828"],
          ["0.5", "0.669 – 0.784   ← worst"]],
      0.9, 2.2, 5.6, 2.3, colw=[2.2, 3.4])
box(s, 6.9, 2.2, 5.5, 3.6, [
    "BEST CONFIGURATION",
    "",
    "•  Dropout:  0.1",
    "•  Learning rate:  0.001",
    "•  Architecture:  256 – 128",
    "•  Optimizer:  Adam  (beat SGD 0.873 vs 0.817)",
    "",
    "Test CCC improved:  0.861  →  0.883"], 15, INK, sp=6)
box(s, 0.9, 5.8, 11.6, 0.9,
    ["Finding: lower dropout (0.1) works best — this dataset does not need heavy regularization.",
     "PyTorch and TensorFlow independently found the same optimum, confirming the result."],
    14, TEAL, bold=True, sp=4)

# ============ 15. RESULTS SUMMARY ============
s = slide(); title(s, "Results Summary")
bar_chart(s, 0.9, 1.8, 11.5, 4.3,
          ["Random Forest", "Tuned ANN", "ANN (untuned)", "SVR", "Linear Regression"],
          (0.886, 0.883, 0.861, 0.827, 0.284))
box(s, 0.9, 6.3, 11.6, 0.7,
    "The tuned neural network (0.883) matches the best classical baseline (0.886) — "
    "and both far exceed Linear Regression, confirming the task is non-linear.",
    14, TEAL, bold=True)

# ============ 16. RESEARCH GAP ============
s = slide(); title(s, "Research Gap", "7")
for i, (t, dsc) in enumerate([
        ("Engagement, not just emotion",
         "Cross-lingual transfer has been studied mainly for EMOTION recognition, rarely for "
         "continuous ENGAGEMENT."),
        ("Non-verbal only",
         "Many systems rely partly on the spoken WORDS, which cannot transfer across languages. "
         "Few use purely face + voice."),
        ("Explicit cross-lingual evaluation",
         "A controlled train-on-one-language, test-on-another analysis is rarely reported, even "
         "on multilingual corpora.")]):
    y = 1.75 + i * 1.5
    chip(s, 0.95, y, 0.75, 0.75, TEAL, str(i + 1), 22, LIGHT, shape=MSO_SHAPE.OVAL)
    box(s, 2.0, y - 0.05, 10.4, 0.5, t, 18, NAVY, bold=True)
    box(s, 2.0, y + 0.45, 10.4, 0.9, dsc, 14, MUTED)
box(s, 0.9, 6.35, 11.6, 0.7,
    "This project fills all three: engagement, non-verbal only, and an explicit cross-lingual test.",
    15, TEAL, bold=True)

# ============ 17. METHODOLOGY ============
s = slide(); title(s, "Proposed Methodology")
for i, (t, dsc) in enumerate([
        ("Features", "eGeMAPS (voice)\n+ OpenFace (face)"),
        ("Baselines", "Linear Regression,\nRandom Forest, SVR"),
        ("Deep model", "MLP now →\nLSTM next"),
        ("Cross-lingual", "Train language A,\ntest language B"),
        ("Evaluate", "CCC + within vs\ncross-language gap")]):
    x = 0.9 + i * 2.42
    card(s, x, 2.4, 2.15, 2.8)
    box(s, x + 0.15, 2.7, 1.85, 0.6, t, 15, NAVY, bold=True, align=PP_ALIGN.CENTER, sp=0)
    box(s, x + 0.15, 3.5, 1.85, 1.3, dsc.split("\n"), 12, MUTED, align=PP_ALIGN.CENTER, sp=2)
    if i < 4:
        box(s, x + 2.08, 3.4, 0.35, 0.5, "→", 20, MINT, bold=True, align=PP_ALIGN.CENTER)
box(s, 0.9, 5.6, 11.6, 1.0,
    ["Next step: an LSTM, which uses the time-order of the windows — engagement rises and falls "
     "during a conversation, and an MLP ignores that ordering.",
     "Then: wider tuning, more languages (NoXi+J), and multimodal attention fusion."],
    14, INK, sp=6)

# ============ 18. LITERATURE ============
s = slide(); title(s, "Literature Review — 25 Papers", "8")
box(s, 0.9, 1.6, 11.6, 0.45, "Reviewed across five themes:", 15, MUTED, italic=True)
for i, (t, dsc) in enumerate([
        ("NoXi & engagement  (9)", "NoXi database, MultiMediate '22–'24, NoXi+J, recent attention-based methods"),
        ("Feature tools  (3)", "eGeMAPS, OpenFace 2.0, openSMILE"),
        ("Cross-lingual transfer  (2)", "Schuller (cross-corpus), Feraru (cross-language emotion)"),
        ("Engagement & affect  (2)", "DAiSEE dataset, affective-state dynamics"),
        ("Models & multimodal  (9)", "LSTM, Random Forest, Dropout, Adam, IEMOCAP, MELD, surveys")]):
    y = 2.15 + i * 0.85
    card(s, 0.9, y, 4.3, 0.7)
    box(s, 1.1, y, 4.0, 0.7, t, 14, NAVY, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    box(s, 5.5, y, 7.0, 0.7, dsc, 13, INK, anchor=MSO_ANCHOR.MIDDLE)
box(s, 0.9, 6.5, 11.6, 0.6,
    "Together they establish the task, the tools, and the gap this project addresses.",
    14, TEAL, bold=True)

# ============ 19. LIMITATIONS ============
s = slide(); title(s, "Limitations & Future Work")
card(s, 0.9, 1.8, 5.7, 4.4)
chip(s, 1.2, 2.05, 2.6, 0.5, TEAL, "LIMITATIONS", 14, LIGHT)
box(s, 1.2, 2.8, 5.1, 3.2, [
    "•  Only 3 languages, 9 sessions",
    "•  Tuned ANN matches but does not beat Random Forest",
    "•  1-second averaging loses fine detail",
    "•  Cross-lingual test uses one model family",
    "•  No verbal/text information used (by design)"], 14, INK, sp=8)
card(s, 6.85, 1.8, 5.6, 4.4)
chip(s, 7.15, 2.05, 2.6, 0.5, MINT, "FUTURE WORK", 14, NAVY)
box(s, 7.15, 2.8, 5.0, 3.2, [
    "•  LSTM to model engagement over time",
    "•  Wider hyperparameter search",
    "•  Add Japanese & Chinese (NoXi+J)",
    "•  Multimodal attention fusion",
    "•  Live demo application"], 14, INK, sp=8)

# ============ 20. CONCLUSION ============
s = slide(NAVY)
chip(s, 0.9, 1.5, 2.0, 0.5, TEAL, "CONCLUSION", 13, LIGHT)
box(s, 0.9, 2.25, 11.6, 1.1, "Engagement is partly language-specific",
    36, LIGHT, bold=True, font=HEAD)
box(s, 0.9, 3.6, 11.6, 2.0, [
    "We built a complete non-verbal (face + voice) engagement-prediction pipeline on NoXi: "
    "EDA, three baselines (Random Forest 0.886), a tuned neural network (0.883), and an "
    "explicit cross-lingual experiment.",
    "",
    "Models perform well within a language (0.55) but drop across languages (0.39) — showing "
    "that how people express engagement differs between cultures."], 17, CLOUD, sp=8)
box(s, 0.9, 6.3, 11.6, 0.6, "Thank you  —  Questions?", 20, MINT, bold=True, font=HEAD)

prs.save("Presentation.pptx")
print("Saved Presentation.pptx with", len(prs.slides._sldIdLst), "slides")
