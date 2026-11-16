"""Writes All_Results_Tables.docx + All_Results_Tables.xlsx - every result of the
project as tables, read straight from the CSVs in reports/.
Run from the project folder: python tools/make_results_tables.py"""
import pandas as pd
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

R = lambda f: pd.read_csv(f"reports/{f}.csv")
f3 = lambda x: "" if pd.isna(x) else f"{x:.3f}"
pm = lambda m, s: f"{m:.3f} ± {s:.3f}"
pct = lambda x: f"{x:.0f}%"
tables = []   # (title, note, DataFrame)

# 1. dataset
eda = R("eda_summary")
tables.append(("Table 1. Dataset (NoXi, 1-second windows)",
               "3 conversations per language, 2 speakers each. Engagement is continuous, 0 to 1.",
               pd.DataFrame({"Language": eda.language, "Conversations": 3, "Windows": eda["count"],
                             "Mean engagement": eda["mean"].map(f3), "Std": eda["std"].map(f3)})))

# 2. leakage
ms = R("master_results")
lk = ms.dropna(subset=["random_split_ccc"])
tables.append(("Table 2. Random split vs unseen conversations (data leakage)",
               "Random split: neighbouring seconds of one conversation fall in both train and test. "
               "Unseen: whole conversations held out (3 folds).",
               pd.DataFrame({"Model": lk.model, "Random split CCC": lk.random_split_ccc.map(f3),
                             "Unseen conversations CCC": lk.session_ccc.map(f3),
                             "Drop": (lk.random_split_ccc - lk.session_ccc).map(f3)})))

# 3. main table - every model, unseen conversations
unit = {"classic ML": "ML baseline", "ANN": "U1 ANN", "CNN": "U2 CNN", "RNN": "U4 RNN",
        "Transformer": "U5 Transformer", "Autoencoder": "U5 Autoencoder"}
main = [dict(Model=r.model, Unit=unit[r.family], Input="voice + face (eGeMAPS + OpenFace)",
             Training="trained from scratch", ccc=r.session_ccc, std=r.session_std) for r in ms.itertuples()]
pt = R("pretrained_results")
for r in pt.itertuples():
    dense = r.dense_ccc >= r.xgb_ccc
    main.append(dict(Model=f"{r.model} + {'dense' if dense else 'XGBoost'} head",
                     Unit="U5 pretrained Transformer", Input=r.input + " (pretrained embeddings)",
                     Training="frozen pretrained + trained head",
                     ccc=r.dense_ccc if dense else r.xgb_ccc, std=r.dense_std if dense else r.xgb_std))
main = pd.DataFrame(main).sort_values("ccc", ascending=False)
main.insert(0, "Rank", range(1, len(main) + 1))
main["CCC (mean ± std)"] = [pm(a, b) for a, b in zip(main.ccc, main["std"])]
tables.append(("Table 3. All models on unseen conversations (main result)",
               "3 session-disjoint folds: each fold tests on one whole conversation per language. "
               "CCC = Concordance Correlation Coefficient, 1 = perfect.",
               main.drop(columns=["ccc", "std"])))

# 4. pretrained detail
tables.append(("Table 4. Pretrained Transformers (frozen) + trained head",
               "The Transformer was pretrained by its authors; only the head is trained here. "
               "Within = leave one conversation out inside a language; cross = train on one language, test on another.",
               pd.DataFrame({"Model": pt.model, "Input": pt.input, "Dims": pt.dims,
                             "XGBoost head": [pm(a, b) for a, b in zip(pt.xgb_ccc, pt.xgb_std)],
                             "Dense head": [pm(a, b) for a, b in zip(pt.dense_ccc, pt.dense_std)],
                             "Within-language": pt.within_ccc.map(f3), "Cross-language": pt.cross_ccc.map(f3),
                             "Drop": pt.drop_pct.map(lambda x: pct(max(x, 0)))})))

# 5. cross-lingual matrix
cm = R("noxi_crosslingual_ccc").rename(columns={"Unnamed: 0": "Train \\ Test"})
langs = list(cm.columns[1:])
diag = sum(cm.loc[i, l] for i, l in enumerate(langs)) / 3
off = (cm[langs].to_numpy().sum() - 3 * diag) / 6
for l in langs:
    cm[l] = cm[l].map(f3)
tables.append(("Table 5. Cross-lingual CCC (Random Forest, voice + face)",
               f"Diagonal = same language (leave one conversation out). Within {diag:.3f}, "
               f"cross {off:.3f}, drop {100 * (diag - off) / diag:.0f}%.", cm))

# 6. ablation
ab = R("ablation_results")
tables.append(("Table 6. Ablation: voice vs face (XGBoost)", "",
               pd.DataFrame({"Input": ab.modality, "Features": ab.n_features,
                             "Unseen conversations": [pm(a, b) for a, b in zip(ab.session_ccc, ab.session_std)],
                             "Within-language": ab.within_ccc.map(f3), "Cross-language": ab.cross_ccc.map(f3),
                             "Drop": ab.drop_pct.map(pct)})))

# 7-8. transfer learning
tr = R("transfer_results")
cond = ["zero_shot", "head_only", "fine_tune", "scratch"]
names = {"zero_shot": "Zero-shot", "head_only": "Head-only", "fine_tune": "Fine-tune", "scratch": "Scratch"}
byf = tr.groupby("fraction")[cond].mean().reset_index()
byf.insert(0, "Adaptation data", byf.pop("fraction").map(lambda x: f"{x * 100:.0f}% of 1 conversation"))
tables.append(("Table 7. Transfer learning (CNN pretrained on 2 languages, adapted to the 3rd)",
               "Mean over the 3 target languages and 3 adaptation conversations; tested on the other 2 conversations.",
               byf.rename(columns=names).round(3)))
byt = tr[tr.fraction == 1.0].groupby("target")[cond].mean().reset_index()
tables.append(("Table 8. Transfer learning by target language (100% of 1 conversation)", "",
               byt.rename(columns={"target": "Target language", **names}).round(3)))

# 9. development stage (random split)
dev = [("ANN (best of 13 tuning runs: 256-128, dropout 0.1, Adam 1e-3)", R("tuning_results").val_ccc.max(), "validation")]
dev.append(("CNN (best of 8 tuning runs)", R("cnn_tuning_results").val_ccc.max(), "validation"))
dev += [(f"CNN {r.model.replace('_', '-')}", r.test_ccc, "test") for r in R("cnn_architectures").itertuples()]
dev += [(r.model, r.test_ccc, "test") for r in R("transformer_results").itertuples()]
dev += [(r.model, r.test_ccc, "test") for r in R("lstm_results").itertuples()]
dev += [(f"{r.model} (sequence experiment)", r.ccc, "test") for r in R("sequence_results").itertuples()]
tables.append(("Table 9. Development stage (random split - leaky, not final)",
               "Used to build and tune the models. Not comparable with Tables 3-8.",
               pd.DataFrame(dev, columns=["Model", "CCC", "Split"]).assign(CCC=lambda d: d.CCC.map(f3))))


# ---------------- Excel ----------------
with pd.ExcelWriter("All_Results_Tables.xlsx", engine="openpyxl") as xw:
    for title, note, df in tables:
        sheet = title.split(".")[0].replace("Table ", "T") + " " + title.split(". ")[1][:24]
        sheet = "".join(c for c in sheet if c not in "[]:*?/\\")[:31]
        df.to_excel(xw, sheet_name=sheet, index=False, startrow=2)
        ws = xw.sheets[sheet]
        ws.cell(1, 1, title); ws.cell(2, 1, note)
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width = min(48, max(12, max(len(str(c.value or "")) for c in col[2:]) + 2))

# ---------------- Word ----------------
def shade(cell, hex_):
    tc = cell._tc.get_or_add_tcPr()
    s = OxmlElement("w:shd")
    s.set(qn("w:val"), "clear"); s.set(qn("w:color"), "auto"); s.set(qn("w:fill"), hex_)
    tc.append(s)

doc = Document()
st = doc.styles["Normal"]; st.font.name = "Calibri"; st.font.size = Pt(10)
doc.add_heading("Cross-Lingual Engagement Prediction - All Results", 0)
doc.add_paragraph("Every number is read from the CSV files in reports/. Metric: CCC (1 = perfect). "
                  "Final results (Tables 2-8) hold out whole conversations, so the model is always tested on conversations it has never seen.")
for title, note, df in tables:
    doc.add_heading(title, 2)
    if note:
        p = doc.add_paragraph(note); p.runs[0].italic = True
    t = doc.add_table(rows=1, cols=len(df.columns)); t.style = "Table Grid"
    for i, c in enumerate(df.columns):
        cell = t.rows[0].cells[i]; cell.text = ""
        run = cell.paragraphs[0].add_run(str(c)); run.bold = True; run.font.color.rgb = RGBColor(255, 255, 255)
        shade(cell, "3F6B35")
    for k, row in enumerate(df.itertuples(index=False)):
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = str(v)
            if i > 0 and not isinstance(v, str):
                cells[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            if k % 2:
                shade(cells[i], "EEF3EA")
    doc.add_paragraph()
doc.save("All_Results_Tables.docx")
print(f"saved All_Results_Tables.docx + All_Results_Tables.xlsx ({len(tables)} tables)")
