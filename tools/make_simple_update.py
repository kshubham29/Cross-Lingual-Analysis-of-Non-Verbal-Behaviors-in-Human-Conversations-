"""Writes Project_Update.docx: a plain, one-to-two page summary of the work from
start to end (up to step 25), black text only, no colours or shading.
Numbers are read from reports/*.csv.
Run from the project folder: python tools/make_simple_update.py"""
import pandas as pd
from docx import Document
from docx.shared import Pt, Cm, RGBColor

R = lambda f: pd.read_csv(f"reports/{f}.csv")
ms, pt, ab = R("master_results").set_index("model"), R("pretrained_results").set_index("model"), R("ablation_results").set_index("modality")
fu, cx, tc, sm = R("fusion_results"), R("context_results"), R("transformer_context_results"), R("smoothing_results")
best = fu[(fu.model == "Gradient Boosting") & fu.input.str.contains("last 5 s")].iloc[0]
gbc = cx[cx.model.str.startswith("Gradient") & cx.input.str.contains("last 5 s")].iloc[0]
c = lambda m: f"{ms.loc[m, 'session_ccc']:.3f}"

doc = Document()
for side in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
    setattr(doc.sections[0], side, Cm(2.2))
for name in ("Normal", "Title", "Heading 1", "List Number"):
    s = doc.styles[name]
    s.font.name = "Calibri"; s.font.color.rgb = RGBColor(0, 0, 0)
doc.styles["Normal"].font.size = Pt(11)
doc.styles["Title"].font.size = Pt(18)
doc.styles["Heading 1"].font.size = Pt(13)


def heading(text):
    doc.add_heading(text, 1)


def numbered(items):
    for i, t in enumerate(items, 1):
        doc.add_paragraph(f"{i}. {t}")


title = doc.add_paragraph().add_run("Project Update")   # plain bold title (the Title style adds a coloured line)
title.bold, title.font.size = True, Pt(18)
doc.add_paragraph("Cross-Lingual Prediction of Engagement from Non-Verbal Behaviour in Human Conversations")
doc.add_paragraph("Team: [names]          Supervisor: [name]          Date: [date]")

heading("Aim")
doc.add_paragraph("To predict how engaged a person is in a conversation (a score from 0 to 1) using only their voice "
                  "and face, without the words, and to check whether a model trained on one language also works "
                  "on another language.")

heading("What we did, from start to end")
numbered([
    "Problem and dataset: chose the NoXi dataset (expert-novice conversations with engagement labels). "
    "Used 9 conversations: 3 English, 3 French, 3 German (18 speakers).",
    "Literature review: studied 26 papers on engagement, multimodal learning and cross-language emotion recognition, "
    "and identified the research gap (cross-language engagement prediction is not well studied).",
    "Data preparation: extracted voice features (88 eGeMAPS) and face features (709 OpenFace) and cut the "
    "recordings into 1-second windows (17,174 windows in total).",
    "Exploratory data analysis: engagement distributions by language and role, feature correlations, PCA.",
    "Machine learning baselines: Linear Regression, Random Forest, Gradient Boosting and XGBoost.",
    "Data leakage check: a random split of windows gave very high scores (about 0.90) because neighbouring seconds "
    "of the same conversation were in both training and test. We changed the evaluation to hold out whole "
    "conversations (about 0.62). All later results use this fair test.",
    "Deep learning models: ANN (with hyperparameter tuning), CNN (LeNet, VGG and ResNet style), "
    "transfer learning across languages, SimpleRNN, LSTM, GRU, our own Transformer and autoencoders.",
    "Pretrained Transformers: used six large pretrained models as frozen feature extractors (XLM-RoBERTa, "
    "w2v-BERT 2.0, CLIP, DINOv2, Swin, VideoMAE) and trained a small model on top.",
    "Cross-language test: trained on one language and tested on another, in all 6 directions.",
    "Ablation study: compared voice only, face only, and both.",
    "Improvements: smoothing of predictions, adding the partner's behaviour, adding past context "
    "(last 5 and 10 seconds), combining the best features, and giving the Transformer a longer input (10 seconds).",
    "Documentation: project report, results tables, laboratory manual, paper draft, poster, presentation and a demo app.",
])

heading("Main results (tested on conversations the model has never seen)")
t = doc.add_table(rows=1, cols=3); t.style = "Table Grid"
for i, h in enumerate(["Model", "CCC", "Drop across languages"]):
    t.rows[0].cells[i].text = ""
    t.rows[0].cells[i].paragraphs[0].add_run(h).bold = True
for row in [
    ("Best: Gradient Boosting on voice + pretrained speech and video features, with past context",
     f"{best.ccc:.3f}", f"{max(best.drop_pct, 0):.0f}%"),
    ("Gradient Boosting on voice + face, with past context", f"{gbc.ccc:.3f}", f"{max(gbc.drop_pct, 0):.0f}%"),
    ("Pretrained Transformers (w2v-BERT 2.0 + VideoMAE)", f"{pt.loc['w2v-BERT 2.0 + VideoMAE', 'dense_ccc']:.3f}",
     f"{pt.loc['w2v-BERT 2.0 + VideoMAE', 'drop_pct']:.0f}%"),
    ("Own Transformer (10 seconds of input)", f"{tc.iloc[1].ccc:.3f}", f"{tc.iloc[1].drop_pct:.0f}%"),
    ("Gradient Boosting (baseline)", c("GradientBoosting"), f"{sm.iloc[0].raw_drop_pct:.0f}%"),
    ("ANN", c("ANN (MLP)"), "-"),
    ("CNN", c("CNN_VGG"), "-"),
    ("LSTM", c("LSTM"), "-"),
]:
    cells = t.add_row().cells
    for i, v in enumerate(row):
        cells[i].text = v
for r in t.rows:
    for i, w in enumerate((11.0, 2.2, 3.6)):
        r.cells[i].width = Cm(w)
doc.add_paragraph("CCC = Concordance Correlation Coefficient (1 = perfect agreement with the human ratings).")

heading("Key findings")
numbered([
    "Testing on whole unseen conversations is necessary; random splits overstate performance.",
    f"Voice features worked much better than face features across languages in our data "
    f"(drop of {ab.loc['voice', 'drop_pct']:.0f}% vs {ab.loc['face', 'drop_pct']:.0f}%).",
    "Past context gave the biggest improvement; the partner's behaviour did not improve accuracy.",
    f"The best model reaches CCC {best.ccc:.3f} with almost no drop when tested on a new language.",
])

heading("Remaining work")
numbered([
    "Add the latest results to the report, poster, presentation and laboratory manual.",
    "Finish the research paper in IEEE format and submit it.",
    "Record the demonstration video.",
    "Update the GitHub repository (without the licensed dataset).",
])

heading("Questions")
numbered([
    "Are these results sufficient, or should we add more conversations from the dataset?",
    "Is any change needed in the method, experiments or report?",
])

doc.save("Project_Update.docx")
print("saved Project_Update.docx")
