"""Turns Results_Summary_9_Conversations.xlsx into a plain workbook:
a first 'Work done' sheet (what was done from start to end, up to step 25),
then every results table on its own sheet. Black text only: no fills,
no borders, no colours; bold only for titles and column headers.
Run after tools/make_results_summary.py, from the project folder."""
import openpyxl
from openpyxl.styles import Font, Border, PatternFill, Alignment

FILE = "Results_Summary_9_Conversations.xlsx"
wb = openpyxl.load_workbook(FILE)

# ---- plain formatting on every results sheet, short clean sheet names ----
for ws in wb.worksheets:
    num, rest = ws["A1"].value.split(". ", 1)
    name = num.replace("Table ", "") + " " + rest.split(" (")[0].split(":")[0]
    ws.title = "".join(ch for ch in name if ch not in "[]:*?/\\")[:31]
    for row in ws.iter_rows():
        for c in row:
            c.font, c.border, c.fill = Font(name="Calibri", size=11), Border(), PatternFill()
            c.alignment = Alignment(vertical="top", wrap_text=c.column == 2 and c.row > 3)
    ws["A1"].font = Font(name="Calibri", size=12, bold=True)
    ws["A2"].font = Font(name="Calibri", size=10, italic=True)
    for c in ws[3]:
        c.font = Font(name="Calibri", size=11, bold=True)

# ---- first sheet: what was done ----
ws = wb.create_sheet("Work done", 0)
lines = [
    ("Cross-Lingual Prediction of Engagement from Non-Verbal Behaviour in Human Conversations", "title"),
    ("Team: [names]    Supervisor: [name]    Date: [date]", ""),
    ("", ""),
    ("Aim", "head"),
    ("Predict how engaged a person is in a conversation (score 0 to 1) from voice and face only, and check whether a "
     "model trained on one language also works on another language.", ""),
    ("", ""),
    ("What we did, from start to end", "head"),
    ("1. Chose the NoXi dataset: 9 conversations (3 English, 3 French, 3 German), 18 speakers.", ""),
    ("2. Literature review of 26 papers and research gap (cross-language engagement prediction).", ""),
    ("3. Extracted voice (88 eGeMAPS) and face (709 OpenFace) features; 1-second windows (17,174 in total).", ""),
    ("4. Exploratory data analysis: engagement by language and role, correlations, PCA.", ""),
    ("5. Machine learning baselines: Linear Regression, Random Forest, Gradient Boosting, XGBoost.", ""),
    ("6. Data leakage check: random split about 0.90 vs whole held-out conversations about 0.62; "
     "all later results use held-out conversations.", ""),
    ("7. Deep learning: ANN with tuning, CNN (LeNet, VGG, ResNet style), transfer learning, SimpleRNN, LSTM, GRU, "
     "own Transformer, autoencoders.", ""),
    ("8. Pretrained Transformers (frozen): XLM-RoBERTa, w2v-BERT 2.0, CLIP, DINOv2, Swin, VideoMAE.", ""),
    ("9. Cross-language test: train on one language, test on another (all 6 directions).", ""),
    ("10. Ablation: voice only, face only, both.", ""),
    ("11. Improvements: smoothing, partner's behaviour, past context, feature fusion, longer Transformer input.", ""),
    ("12. Documentation: report, results tables, laboratory manual, paper draft, poster, presentation, demo app.", ""),
    ("", ""),
    ("Key results", "head"),
    ("Best model: Gradient Boosting on voice + pretrained speech and video features with past context: CCC 0.777, "
     "1% drop across languages (see sheet '0 Final ranking').", ""),
    ("Voice features transferred across languages much better than face features in our data (drop 12% vs 55%).", ""),
    ("Past context gave the biggest improvement; the partner's behaviour did not improve accuracy.", ""),
    ("", ""),
    ("Remaining work", "head"),
    ("Update report, poster, presentation and lab manual with the latest results; IEEE paper and submission; "
     "demo video; GitHub update (without the licensed dataset).", ""),
    ("", ""),
    ("Sheets in this file", "head"),
] + [(f"{s.title}: {s['A1'].value.split('. ', 1)[1]}", "") for s in wb.worksheets[1:]]

for i, (text, kind) in enumerate(lines, 1):
    c = ws.cell(i, 1, text)
    c.font = Font(name="Calibri", size=13 if kind == "title" else 11, bold=kind in ("title", "head"))
    c.alignment = Alignment(wrap_text=True, vertical="top")
ws.column_dimensions["A"].width = 120
wb.active = 0
wb.save(FILE)
print(f"saved {FILE}: {len(wb.sheetnames)} sheets -> {wb.sheetnames}")
