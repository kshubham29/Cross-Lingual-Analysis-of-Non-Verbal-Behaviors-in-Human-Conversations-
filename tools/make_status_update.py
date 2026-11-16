"""Writes Project_Status_Update.docx: what is done and what is left, mapped to
the course plan (phases, deliverables, syllabus units), with the key results
and the questions for the supervisor. Numbers are read from reports/*.csv.
Covers the work up to step 25 (the 9-conversation results).
Run from the project folder: python tools/make_status_update.py"""
import pandas as pd
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

R = lambda f: pd.read_csv(f"reports/{f}.csv")
ms, pt, ab = R("master_results").set_index("model"), R("pretrained_results").set_index("model"), R("ablation_results").set_index("modality")
fu, cx, tc = R("fusion_results"), R("context_results"), R("transformer_context_results")
best = fu[(fu.model == "Gradient Boosting") & fu.input.str.contains("last 5 s")].iloc[0]
gbc = cx[cx.model.str.startswith("Gradient") & cx.input.str.contains("last 5 s")].iloc[0]
t10 = tc.iloc[1]
pm = lambda m, s: f"{m:.3f} ± {s:.3f}"


def shade(cell, hex_):
    s = OxmlElement("w:shd"); s.set(qn("w:val"), "clear"); s.set(qn("w:color"), "auto"); s.set(qn("w:fill"), hex_)
    cell._tc.get_or_add_tcPr().append(s)


def table(doc, header, rows, widths=None):
    t = doc.add_table(rows=1, cols=len(header)); t.style = "Table Grid"
    for i, h in enumerate(header):
        c = t.rows[0].cells[i]; c.text = ""
        r = c.paragraphs[0].add_run(h); r.bold = True; r.font.color.rgb = RGBColor(255, 255, 255); shade(c, "3F6B35")
    for k, row in enumerate(rows):
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = str(v)
            if k % 2:
                shade(cells[i], "EEF3EA")
    if widths:
        for row in t.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Cm(w)
    doc.add_paragraph()


doc = Document()
for side in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
    setattr(doc.sections[0], side, Cm(2))
st = doc.styles["Normal"]; st.font.name = "Calibri"; st.font.size = Pt(10.5)

doc.add_heading("Project Progress Update", 0)
doc.add_paragraph("Project: Cross-Lingual Prediction of Engagement from Non-Verbal Behaviour in Human Conversations")
doc.add_paragraph("Team: [name 1], [name 2], [name 3]        Supervisor: [name]        Date: [date]")

doc.add_heading("1. Project in brief", 1)
doc.add_paragraph(
    "We predict how engaged a person is during a conversation (a continuous score from 0 to 1) using only "
    "non-verbal behaviour: voice (88 eGeMAPS features) and face (709 OpenFace features). We then test whether a "
    "model trained on one language still works on another. Dataset: NoXi expert-novice conversations in English, "
    "French and German (9 conversations, 18 speakers, 17,174 one-second windows). Metric: CCC. All final results "
    "are tested on whole conversations that the model has never seen.")

doc.add_heading("2. Work completed (by phase of the course plan)", 1)
table(doc, ["Phase", "Planned", "What we did", "Status"], [
    ("I. Problem & foundation (Weeks 1-4)", "Problem, dataset, EDA, 2 ML baselines, literature survey (10-15 papers), report",
     "NoXi dataset selected and processed; EDA; 4 ML baselines (Linear Regression, Random Forest, Gradient Boosting, "
     "XGBoost); literature review of 26 papers with research gap", "Done"),
    ("II. Deep learning models (Weeks 4-8)", "CNN / LSTM / Transformer / Autoencoder, tuning, mid-term",
     "ANN (13 tuning runs), CNN (LeNet / VGG / ResNet styles, tuning), transfer learning, SimpleRNN / LSTM / GRU, "
     "own Transformer, autoencoders, 6 frozen pretrained Transformers (XLM-RoBERTa, w2v-BERT 2.0, CLIP, DINOv2, "
     "Swin, VideoMAE)", "Done"),
    ("III. Contribution & dissemination (Weeks 9-15)", "Comparative analysis, novelty, ablation, paper, poster, video, final",
     "Found and fixed data leakage (random split vs held-out conversations); cross-language test in all 6 directions; "
     "voice vs face ablation; 5 improvements (smoothing, partner features, past context, fusion, longer Transformer "
     "input); report, results tables, lab manual, paper draft, poster, presentation, demo app",
     "Mostly done (see section 5)"),
], widths=[3.6, 4.2, 7.0, 2.2])

doc.add_heading("3. Syllabus units used in the project", 1)
table(doc, ["Unit", "Where it appears in the project"], [
    ("1. ANN and Deep Learning", "MLP regressor; activation functions, loss, Adam optimiser, dropout; hyperparameter tuning (13 runs)"),
    ("2. Deep Learning for Image Processing", "1-D CNN (LeNet, VGG, ResNet styles) in Keras; dropout; transfer learning across languages; "
                                              "pretrained vision Transformers (CLIP, DINOv2, Swin, VideoMAE)"),
    ("3. Natural Language Processing", "Limited, because the project is non-verbal by design. XLM-RoBERTa transcript embeddings "
                                       "were tested as a comparison (text vs voice/face)"),
    ("4. Models for Sequential Analysis", "SimpleRNN, LSTM, GRU on 25-frame sequences; past-context features"),
    ("5. Autoencoders and Generative AI", "Autoencoder (797-256-32-256-797) for feature compression; own Transformer encoder; "
                                          "GANs / VAEs not used"),
], widths=[5.0, 12.0])

doc.add_heading("4. Main results (held-out conversations, 3 folds)", 1)
table(doc, ["Model", "CCC (mean ± std)", "Cross-language drop"], [
    ("Gradient Boosting on eGeMAPS + w2v-BERT 2.0 + VideoMAE with past context (best)", pm(best.ccc, best["std"]), f"{max(best.drop_pct, 0):.0f}%"),
    ("Gradient Boosting on voice + face with past context", pm(gbc.ccc, gbc["std"]), f"{max(gbc.drop_pct, 0):.0f}%"),
    ("w2v-BERT 2.0 + VideoMAE (frozen) + dense head", pm(pt.loc["w2v-BERT 2.0 + VideoMAE", "dense_ccc"], pt.loc["w2v-BERT 2.0 + VideoMAE", "dense_std"]),
     f"{pt.loc['w2v-BERT 2.0 + VideoMAE', 'drop_pct']:.0f}%"),
    ("Own Transformer, 10 s of input", pm(t10.ccc, t10["std"]), f"{t10.drop_pct:.0f}%"),
    ("Gradient Boosting, voice + face (baseline)", pm(ms.loc["GradientBoosting", "session_ccc"], ms.loc["GradientBoosting", "session_std"]), "20%"),
    ("ANN (MLP)", pm(ms.loc["ANN (MLP)", "session_ccc"], ms.loc["ANN (MLP)", "session_std"]), "-"),
    ("CNN (VGG style)", pm(ms.loc["CNN_VGG", "session_ccc"], ms.loc["CNN_VGG", "session_std"]), "-"),
    ("LSTM", pm(ms.loc["LSTM", "session_ccc"], ms.loc["LSTM", "session_std"]), "-"),
], widths=[10.0, 3.8, 3.2])
doc.add_paragraph("Findings so far:", style=None).runs[0].bold = True
for b in [
    f"A random split of windows gives misleadingly high scores (about 0.90); holding out whole conversations gives about 0.62. "
    f"All results above use held-out conversations.",
    f"In our data, voice features transferred across languages much better than face features "
    f"(drop {ab.loc['voice', 'drop_pct']:.0f}% vs {ab.loc['face', 'drop_pct']:.0f}%).",
    "Past context (the last 5 and 10 seconds) gave the largest single improvement; adding the partner's features did not "
    "improve accuracy.",
    "Tree models did best on our small data; pretrained Transformer features plus Gradient Boosting gave the best result.",
]:
    doc.add_paragraph(b, style="List Bullet")

doc.add_heading("5. Work remaining", 1)
table(doc, ["Deliverable (course plan)", "Current state", "To do"], [
    ("Final project report", "33-page report with figures (results up to the pretrained models)", "Add the improvement results; plagiarism check (≤ 15%)"),
    ("Research paper (IEEE format)", "Draft v2 written", "Update with latest results, convert to IEEE template, choose venue and submit"),
    ("Source code on GitHub", "Code complete; last commit in September", "Commit all scripts and results (without the licensed NoXi data)"),
    ("Trained models and results", "Saved model files and result tables", "-"),
    ("Laboratory manual", "Written (covers steps 1-18)", "Add the pretrained and improvement steps"),
    ("Research poster / final presentation", "Made in October", "Update with the best model and new findings"),
    ("Demonstration video (5-10 min)", "Demo app works", "Record the video"),
    ("Dataset documentation", "Dataset description written", "-"),
], widths=[4.5, 6.0, 6.5])
doc.add_paragraph("Planned checks before final submission: a statistical significance test between the main models, "
                  "and a check that no participant appears in both training and test data.")

doc.add_heading("6. Limitations", 1)
for b in ["Only 9 conversations (3 per language), so results vary between folds.",
          "Results are on our own held-out conversations, not the official MultiMediate test set, so they are not directly "
          "comparable with challenge scores.",
          "CPU only, so the pretrained Transformers were used frozen (no fine-tuning)."]:
    doc.add_paragraph(b, style="List Bullet")

doc.add_heading("7. Questions for you", 1)
for i, q in enumerate([
    "Are the results with 9 conversations sufficient, or should we extend the dataset (we can prepare about 20 "
    "conversations from the NoXi train and validation sets)?",
    "Is there any change you would like in the method, the experiments or the report structure?",
    "Which venue should we target for the paper (conference, journal or book chapter)?",
    "Is anything else expected for Phase III before the final submission?",
], 1):
    doc.add_paragraph(f"{i}. {q}")

doc.save("Project_Status_Update.docx")
print("saved Project_Status_Update.docx")
