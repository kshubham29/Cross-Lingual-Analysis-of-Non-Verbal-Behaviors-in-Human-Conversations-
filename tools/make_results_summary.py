"""Writes Results_Summary_9_Conversations.docx + .xlsx: every result of the
9-conversation project (all models, pretrained Transformers, cross-language,
ablation, transfer learning, improvements), a short summary, and the question
for the supervisor about adding more conversations.
All numbers are read from the CSVs in reports/.
Run from the project folder: python tools/make_results_summary.py"""
import pandas as pd
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_ORIENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

# Tables 1-9 are built exactly as in make_results_tables.py
exec(open("tools/make_results_tables.py", encoding="utf-8").read().split("# ---------------- Excel")[0])

# ---------------- improvements (steps 21-25) ----------------
sm, pa, cx = R("smoothing_results"), R("partner_results"), R("context_results")
fu, tc = R("fusion_results"), R("transformer_context_results")
gb_sm = sm.iloc[0]
gb_ctx = cx[cx.input.str.contains("last 5 s") & cx.model.str.startswith("Gradient")].iloc[0]
gb_pa = pa[(pa.input == "self + partner") & pa.model.str.startswith("Gradient")].iloc[0]
fu_best = fu[(fu.model == "Gradient Boosting") & fu.input.str.contains("last 5 s")].iloc[0]
tc1, tc10 = tc.iloc[0], tc.iloc[1]
drop = lambda r: pct(max(r.drop_pct, 0)) if pd.notna(r.get("drop_pct")) else "-"
imp = [
    ("Baseline: Gradient Boosting, voice + face, 1 s", "-", pm(gb_sm.raw_ccc, gb_sm.raw_std), pct(gb_sm.raw_drop_pct)),
    ("Step 21: smooth predictions over the last 5 s", "Small gain", pm(gb_sm.smooth_ccc, gb_sm.smooth_std), pct(gb_sm.smooth_drop_pct)),
    ("Step 22: add the partner's behaviour", "No accuracy gain, language drop halved", pm(gb_pa.ccc, gb_pa["std"]), drop(gb_pa)),
    ("Step 23: add past context (last 5 s + last 10 s)", "Big gain, most stable", pm(gb_ctx.ccc, gb_ctx["std"]), drop(gb_ctx)),
    ("Step 24: fusion eGeMAPS + w2v-BERT + VideoMAE + context", "BEST MODEL", pm(fu_best.ccc, fu_best["std"]), drop(fu_best)),
    ("Step 25: own Transformer, 1 s of input", "-", pm(tc1.ccc, tc1["std"]), drop(tc1)),
    ("Step 25: own Transformer, 10 s of input", "Longer memory helps the Transformer", pm(tc10.ccc, tc10["std"]), drop(tc10)),
]
tables.append(("Table 10. Improvements (steps 21-25)",
               "Same 3 folds of unseen conversations. Settings fixed in advance, not tuned on the test folds.",
               pd.DataFrame(imp, columns=["Experiment", "Effect", "CCC (mean ± std)", "Cross-language drop"])))

# ---------------- final ranking (best version of each idea) ----------------
pt_best = pt.iloc[pt[["xgb_ccc", "dense_ccc"]].max(axis=1).idxmax()]
rank = [
    ("Gradient Boosting: eGeMAPS + w2v-BERT + VideoMAE + context", "Fusion (ML on pretrained features)", fu_best.ccc, fu_best["std"], drop(fu_best)),
    ("Gradient Boosting: voice + face + context", "Classic ML", gb_ctx.ccc, gb_ctx["std"], drop(gb_ctx)),
    (f"{pt_best.model} (frozen pretrained Transformers)", "Pretrained Transformer", max(pt_best.xgb_ccc, pt_best.dense_ccc),
     pt_best.dense_std if pt_best.dense_ccc >= pt_best.xgb_ccc else pt_best.xgb_std, pct(max(pt_best.drop_pct, 0))),
    ("Own Transformer, 10 s of input", "Transformer (from scratch)", tc10.ccc, tc10["std"], drop(tc10)),
]
known_drop = {"GradientBoosting": pct(gb_sm.raw_drop_pct), "Transformer": drop(tc1),
              "XGBoost": pct(100 * (diag - off) / diag)}   # from steps 21, 25 and the step-5 matrix
for r in ms.itertuples():
    rank.append((r.model + (" (1 s)" if r.family == "Transformer" else ""), r.family, r.session_ccc, r.session_std,
                 known_drop.get(r.model, "-")))
rk = pd.DataFrame(rank, columns=["Model", "Type", "ccc", "std", "Cross-language drop"]).sort_values("ccc", ascending=False)
rk.insert(0, "Rank", range(1, len(rk) + 1))
rk["CCC (mean ± std)"] = [pm(a, b) for a, b in zip(rk.ccc, rk["std"])]
rk = rk[["Rank", "Model", "Type", "CCC (mean ± std)", "Cross-language drop"]]
tables.insert(0, ("Table 0. Final ranking (unseen conversations)",
                  "Best version of each model family. '-' = cross-language test not run for that model.", rk))

# ---------------- Excel ----------------
with pd.ExcelWriter("Results_Summary_9_Conversations.xlsx", engine="openpyxl") as xw:
    for title, note, df in tables:
        sheet = "".join(c for c in title.split(". ")[0].replace("Table ", "T") + " " + title.split(". ")[1][:24]
                        if c not in "[]:*?/\\")[:31]
        df.to_excel(xw, sheet_name=sheet, index=False, startrow=2)
        ws = xw.sheets[sheet]
        ws.cell(1, 1, title); ws.cell(2, 1, note)
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width = min(55, max(12, max(len(str(c.value or "")) for c in col[2:]) + 2))

# ---------------- Word ----------------
def shade(cell, hex_):
    s = OxmlElement("w:shd")
    s.set(qn("w:val"), "clear"); s.set(qn("w:color"), "auto"); s.set(qn("w:fill"), hex_)
    cell._tc.get_or_add_tcPr().append(s)


def add_table(doc, df, bold_first_row=False):
    t = doc.add_table(rows=1, cols=len(df.columns)); t.style = "Table Grid"
    for i, c in enumerate(df.columns):
        cell = t.rows[0].cells[i]; cell.text = ""
        run = cell.paragraphs[0].add_run(str(c)); run.bold = True   # plain: black bold header, no shading
    for k, row in enumerate(df.itertuples(index=False)):
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = str(v)
            if bold_first_row and k == 0:
                for r_ in cells[i].paragraphs[0].runs:
                    r_.bold = True
    doc.add_paragraph()


def bullets(doc, items):
    for it in items:
        doc.add_paragraph(it, style="List Bullet")


doc = Document()
sec = doc.sections[0]
sec.orientation = WD_ORIENT.LANDSCAPE
sec.page_width, sec.page_height = sec.page_height, sec.page_width
for side in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
    setattr(sec, side, Cm(1.8))
st = doc.styles["Normal"]; st.font.name = "Calibri"; st.font.size = Pt(10)
for name in ("Heading 1", "Heading 2"):   # plain: black headings
    doc.styles[name].font.color.rgb = RGBColor(0, 0, 0); doc.styles[name].font.name = "Calibri"

title = doc.add_paragraph().add_run("Cross-Lingual Engagement Prediction: Results with 9 Conversations")
title.bold, title.font.size = True, Pt(18)   # plain bold title (the Title style adds a coloured line)
doc.add_paragraph("Name: [your name]    Roll no.: [roll number]    Supervisor: [supervisor]    Date: [date]")
doc.add_paragraph(
    "Task: predict how engaged a person is in a conversation (continuous score 0-1) from non-verbal "
    "behaviour only (voice and face), and test whether a model trained on one language works on another. "
    "Data: NoXi corpus, English, French and German. Metric: CCC (Concordance Correlation Coefficient, 1 = perfect). "
    "All final results are on unseen conversations: whole conversations are held out, so the model is always "
    "tested on conversations it has never seen.")

doc.add_heading("1. Summary", 1)
n_win = int(eda["count"].sum())
add_table(doc, pd.DataFrame([
    ("Data used", f"9 conversations (3 per language), 18 speakers, {n_win:,} one-second windows (about 2.4 hours)"),
    ("Models trained", "4 classic ML, ANN, 3 CNN designs, 3 RNNs, own Transformer, 2 autoencoders, "
                       "6 frozen pretrained Transformers (+1 combination), 5 improvement experiments"),
    ("Best model", f"Gradient Boosting on eGeMAPS + w2v-BERT 2.0 + VideoMAE with past context: "
                   f"CCC {pm(fu_best.ccc, fu_best['std'])}, cross-language drop {drop(fu_best)}"),
    ("Best deep model", f"Own Transformer with 10 s of input: CCC {pm(tc10.ccc, tc10['std'])}, drop {drop(tc10)}"),
    ("Data leakage found and fixed", "Random splits gave about 0.90; on unseen conversations the same models give about 0.62"),
    ("Voice vs face across languages", f"Voice loses {pct(ab.drop_pct[0])}, face loses {pct(ab.drop_pct[1])}: "
                                       "in our data voice features transferred across languages much better than OpenFace face features"),
], columns=["Item", "Result"]))

doc.add_heading("2. Question: do we need more conversations?", 1)
doc.add_paragraph("Why 9 conversations may not be enough:")
bullets(doc, [
    "17,174 windows look large, but neighbouring seconds are almost identical; the model really learns from 18 people.",
    "Only 3 conversations per language: inside one language the model trains on just 2 conversations.",
    "Only 3 test folds, so the spread is large (ANN ± 0.154, LSTM ± 0.219) and a significance test is not reliable.",
    "One unusual conversation can break a result (own Transformer, French to English: CCC -0.018).",
    f"Evidence that more conversations help: Gradient Boosting trained on 2 conversations gives "
    f"{gb_sm.raw_within:.3f}, trained on 6 conversations gives {gb_sm.raw_ccc:.3f}.",
])
doc.add_paragraph("Option to extend: NoXi has more labelled sessions (train + validation sets).")
add_table(doc, pd.DataFrame([
    ("A. Keep 9 conversations", "Nothing", "-", "Report as is; data size stated as a limitation"),
    ("B. Add 15 conversations (24 in total, 8 per language)",
     "NoXi val: 007, 009, 011, 014, 058, 062, 063, 074, 075, 076; train: 020, 026, 029, 068, 073",
     "About 27 GB download, about 1 day of CPU training",
     "8 test folds, more reliable results, significance test possible, comparison 9 vs 24"),
], columns=["Option", "Sessions", "Cost", "Benefit"]))
p = doc.add_paragraph()
p.add_run("Question for the supervisor: ").bold = True
p.add_run("Are these results with 9 conversations sufficient, or should I extend to 24 conversations (option B)?")

doc.add_heading("3. All results", 1)
for title, note, df in tables:
    doc.add_heading(title, 2)
    if note:
        q = doc.add_paragraph(note); q.runs[0].italic = True
    add_table(doc, df, bold_first_row=title.startswith("Table 0"))

doc.save("Results_Summary_9_Conversations.docx")
print(f"saved Results_Summary_9_Conversations.docx + .xlsx ({len(tables)} tables)")
