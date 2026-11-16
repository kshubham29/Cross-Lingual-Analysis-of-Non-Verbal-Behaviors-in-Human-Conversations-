// Builds Research_Poster.pptx (A1 portrait) from reports/results_summary.json.
// Usage: node tools/make_poster.js <project_dir> <apply_theme.js path>
const path = require("path");
const fs = require("fs");
const pptxgen = require("pptxgenjs");

const ROOT = process.argv[2];
const J = JSON.parse(fs.readFileSync(path.join(ROOT, "reports", "results_summary.json"), "utf8"));
const OUT = path.join(ROOT, "Research_Poster.pptx");
const COL = { ink: "1F2A1C", forest: "2C5F2D", moss: "97BC62", pale: "EEF3E8", amber: "D08A2E", rust: "A84B3A",
              grey: "5F6B5C", white: "FFFFFF", line: "D5DECB" };
const THEME = { name: "Forest Moss", headFontFace: "Cambria", bodyFontFace: "Calibri",
  colors: { dk1: COL.ink, lt1: COL.white, dk2: COL.forest, lt2: COL.pale, accent1: COL.forest, accent2: COL.moss,
            accent3: COL.amber, accent4: "6B8F71", accent5: COL.rust, accent6: "4F6D5A", hlink: COL.forest, folHlink: "6B8F71" } };
const H = "Cambria", B = "Calibri";
const f3 = (x) => Number(x).toFixed(3);

const pres = new pptxgen();
pres.defineLayout({ name: "A1P", width: 23.39, height: 33.11 });
pres.layout = "A1P";
pres.theme = { headFontFace: H, bodyFontFace: B };
const s = pres.addSlide();
s.background = { color: COL.white };

const text = (t, o) => s.addText(t, Object.assign({ isTextBox: true, fontFace: B, fontSize: 24, color: COL.ink, margin: 0, valign: "top" }, o));
function section(x, y, w, num, title) {
  s.addShape(pres.shapes.OVAL, { x, y, w: 0.8, h: 0.8, fill: { color: COL.forest }, line: { color: COL.forest } });
  text(String(num), { x, y, w: 0.8, h: 0.8, fontFace: H, fontSize: 28, bold: true, color: COL.white, align: "center", valign: "middle" });
  text(title, { x: x + 1.05, y: y - 0.02, w: w - 1.05, h: 0.85, fontFace: H, fontSize: 36, bold: true, color: COL.forest, valign: "middle" });
}
const chartBase = () => ({
  catAxisLabelColor: COL.grey, valAxisLabelColor: COL.grey, catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt",
  catAxisLabelFontSize: 20, valAxisLabelFontSize: 18, dataLabelFontFace: "+mn-lt", dataLabelFontSize: 18, dataLabelColor: COL.ink,
  valGridLine: { color: COL.line, size: 1 }, catGridLine: { style: "none" }, legendFontFace: "+mn-lt", legendFontSize: 20, legendColor: COL.ink,
});

// ---------- data ----------
const master = (J.master || []).filter((r) => r.model !== "LinearRegression");
const best = master[0];
const abl = Object.fromEntries(J.ablation.map((r) => [r.modality, r]));
const cm = J.cross.matrix, langs = J.cross.langs;
const diag = cm.reduce((a, r, i) => a + r[i], 0) / 3;
const off = (cm.flat().reduce((a, b) => a + b, 0) - diag * 3) / 6;
const drop = Math.round((100 * (diag - off)) / diag);
const OLD = { RandomForest: 0.885, GradientBoosting: 0.901, XGBoost: 0.906, "ANN (MLP)": 0.881 };
const pretty = { GradientBoosting: "Grad. Boosting", RandomForest: "Random Forest", XGBoost: "XGBoost", "ANN (MLP)": "ANN (MLP)",
  CNN_VGG: "CNN (VGG)", SimpleRNN: "Simple RNN", LSTM: "LSTM", GRU: "GRU", Transformer: "Transformer",
  "Autoencoder + XGBoost": "AE + XGBoost", "Autoencoder + dense head": "AE + dense" };
const P = (m) => pretty[m] || m;

// ---------- header ----------
s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 23.39, h: 4.4, fill: { color: COL.forest }, line: { color: COL.forest } });
text("How Much Is Lost in Translation?", { x: 0.9, y: 0.55, w: 21.6, h: 1.3, fontFace: H, fontSize: 72, bold: true, color: COL.white });
text("Cross-lingual prediction of conversational engagement from non-verbal behaviour", { x: 0.9, y: 1.85, w: 21.6, h: 0.9, fontFace: H, fontSize: 40, color: "DCE8CF" });
text("[Team member names]  ·  Supervisor: [name]  ·  [Department, University]", { x: 0.9, y: 3.05, w: 21.6, h: 0.7, fontSize: 28, color: COL.white });

// ---------- headline stats ----------
const stats = [[`${drop}%`, "loss of concordance when a model meets a new language", COL.rust],
               [`${Math.round(abl.voice.drop_pct)}% vs ${Math.round(abl.face.drop_pct)}%`, "cross-language drop of voice vs face features", COL.forest],
               [f3(best.session_ccc), `CCC on unseen conversations (${P(best.model)})`, COL.forest]];
stats.forEach(([big, small, c], i) => {
  const x = 0.9 + i * 7.3;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 4.9, w: 6.95, h: 2.55, rectRadius: 0.15, fill: { color: COL.pale }, line: { color: COL.pale } });
  text(big, { x: x + 0.4, y: 5.1, w: 6.2, h: 1.25, fontFace: H, fontSize: 64, bold: true, color: c });
  text(small, { x: x + 0.4, y: 6.35, w: 6.2, h: 0.95, fontSize: 22, color: COL.grey });
});

const LX = 0.9, RX = 12.05, W = 10.45;
// ---------- left column ----------
let y = 8.0;
section(LX, y, W, 1, "Problem");
text("Engagement models for tutors, agents and video calls are trained and tested in one language. Using voice tone and facial behaviour only - never the words - we measure how much survives in a language the model has never seen.",
  { x: LX, y: y + 1.05, w: W, h: 2.1 });
y += 3.4;
section(LX, y, W, 2, "Data and method");
text([
  { text: "NoXi: 9 expert-novice conversations, English / French / German", options: { bullet: true, breakLine: true } },
  { text: "17,174 one-second windows; 88 eGeMAPS voice + 709 OpenFace face features", options: { bullet: true, breakLine: true } },
  { text: "12 models: classic ML, ANN, CNN, RNN, LSTM, GRU, Transformer, autoencoder", options: { bullet: true, breakLine: true } },
  { text: "Every score on held-out conversations (3 session-disjoint folds)", options: { bullet: true } },
], { x: LX, y: y + 1.05, w: W, h: 3.0, paraSpaceAfter: 8 });
y += 4.3;
section(LX, y, W, 3, "Random splits overstate performance");
const keep = (J.flat || []).filter((r) => OLD[r.model] !== undefined);
s.addChart(pres.charts.BAR, [
  { name: "Random split", labels: keep.map((r) => P(r.model)), values: keep.map((r) => OLD[r.model]) },
  { name: "Unseen conversations", labels: keep.map((r) => P(r.model)), values: keep.map((r) => r.ccc) },
], Object.assign(chartBase(), { x: LX, y: y + 1.0, w: W, h: 5.0, barDir: "col", barGapWidthPct: 55, chartColors: [COL.line, COL.forest],
  showValue: true, dataLabelFormatCode: "0.00", dataLabelPosition: "outEnd", valAxisMinVal: 0, valAxisMaxVal: 1,
  valAxisLabelFormatCode: "0.0", showLegend: true, legendPos: "b" }));
y += 6.3;
section(LX, y, W, 4, "All models on unseen conversations");
const rows = master.slice().reverse();
s.addChart(pres.charts.BAR, [{ name: "CCC", labels: rows.map((r) => P(r.model)), values: rows.map((r) => r.session_ccc) }],
  Object.assign(chartBase(), { x: LX, y: y + 1.0, w: W, h: 5.6, barDir: "bar", barGapWidthPct: 40, chartColors: [COL.forest],
    showValue: true, dataLabelFormatCode: "0.000", dataLabelPosition: "outEnd", valAxisMinVal: 0, valAxisMaxVal: 0.8,
    valAxisLabelFormatCode: "0.0", showLegend: false }));

// ---------- right column ----------
y = 8.0;
section(RX, y, W, 5, `A new language costs ${drop}%`);
const shade = (v, d) => (d ? COL.forest : v >= 0.5 ? "B7CF96" : v >= 0.3 ? "DCE8CF" : "F3D9D3");
const trows = [[{ text: "Train \\ Test", options: { bold: true, fill: { color: COL.pale } } },
  ...langs.map((l) => ({ text: l, options: { bold: true, fill: { color: COL.pale }, align: "center" } }))]];
cm.forEach((r, i) => trows.push([{ text: langs[i], options: { bold: true, fill: { color: COL.pale } } },
  ...r.map((v, j) => ({ text: f3(v), options: { align: "center", fill: { color: shade(v, i === j) }, color: i === j ? COL.white : COL.ink, bold: i === j } }))]));
s.addTable(trows, { x: RX, y: y + 1.1, w: 6.6, colW: [1.95, 1.55, 1.55, 1.55], fontFace: B, fontSize: 22, color: COL.ink,
  border: { type: "solid", pt: 2, color: COL.white }, rowH: 0.7 });
text([{ text: `Same language ${f3(diag)}`, options: { breakLine: true, bold: true, color: COL.forest } },
      { text: `Other language ${f3(off)}`, options: { bold: true, color: COL.rust } }],
  { x: RX + 7.0, y: y + 1.3, w: 3.45, h: 1.6, fontSize: 24 });
text("CCC, rows = training language", { x: RX + 7.0, y: y + 2.9, w: 3.45, h: 0.8, fontSize: 20, color: COL.grey });
y += 4.3;
section(RX, y, W, 6, "Voice travels, faces do not");
s.addChart(pres.charts.BAR, [
  { name: "Same language", labels: ["Voice (88)", "Face (709)", "Both (797)"], values: [abl.voice.within_ccc, abl.face.within_ccc, abl.both.within_ccc] },
  { name: "Other language", labels: ["Voice (88)", "Face (709)", "Both (797)"], values: [abl.voice.cross_ccc, abl.face.cross_ccc, abl.both.cross_ccc] },
], Object.assign(chartBase(), { x: RX, y: y + 1.0, w: 6.6, h: 5.0, barDir: "col", barGapWidthPct: 55, chartColors: [COL.forest, COL.amber],
  showValue: true, dataLabelFormatCode: "0.00", dataLabelPosition: "outEnd", valAxisMinVal: 0, valAxisMaxVal: 0.8,
  valAxisLabelFormatCode: "0.0", showLegend: true, legendPos: "b" }));
text(`Voice alone: ${f3(abl.voice.session_ccc)} on unseen conversations, better than voice + face (${f3(abl.both.session_ccc)}). Face features lose ${Math.round(abl.face.drop_pct)}% in a new language - partly culture, partly different cameras at each site.`,
  { x: RX + 6.9, y: y + 1.2, w: 3.55, h: 4.6, fontSize: 22 });
y += 6.3;
section(RX, y, W, 7, "Transfer learning");
if (J.transfer_by_fraction) {
  const T = J.transfer_by_fraction, labels = T.map((r) => `${Math.round(r.fraction * 100)}%`);
  s.addChart(pres.charts.LINE, [
    { name: "Head-only", labels, values: T.map((r) => r.head_only) },
    { name: "Fine-tune", labels, values: T.map((r) => r.fine_tune) },
    { name: "Scratch", labels, values: T.map((r) => r.scratch) },
    { name: "Zero-shot", labels, values: T.map((r) => r.zero_shot) },
  ], Object.assign(chartBase(), { x: RX, y: y + 1.0, w: 6.6, h: 4.3, chartColors: [COL.forest, COL.moss, COL.rust, COL.grey],
    lineSize: 3, lineDataSymbol: "circle", lineDataSymbolSize: 10, valAxisMinVal: 0, valAxisLabelFormatCode: "0.0",
    showLegend: true, legendPos: "b" }));
}
text("CNN pretrained on two languages, adapted with part of one conversation of the third (x-axis), tested on its other two conversations.",
  { x: RX + 6.9, y: y + 1.2, w: 3.55, h: 4.0, fontSize: 22 });
y += 5.5;
section(RX, y, W, 8, "AI prototype");
const img = path.join(ROOT, "reports", "figures", "demo_app.jpg");
if (fs.existsSync(img)) s.addImage({ path: img, x: RX, y: y + 1.0, w: 4.8, h: 3.6 });
text("Streamlit app: pick a conversation and speaker, switch voice / face / both, and see predicted vs real engagement second by second, always from a model that never saw that conversation.",
  { x: RX + 5.1, y: y + 1.1, w: 5.35, h: 3.5, fontSize: 22 });

// ---------- conclusion + references ----------
y = 29.0;
s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: LX, y, w: 21.6, h: 2.6, rectRadius: 0.15, fill: { color: COL.forest }, line: { color: COL.forest } });
text([
  { text: "Conclusion. ", options: { bold: true } },
  { text: `Judge engagement models on unseen conversations - random splits added about 0.28 CCC. A new language costs ${drop}%, and most of the loss is in the face. Voice is the more language-independent engagement cue.` },
], { x: LX + 0.5, y: y + 0.35, w: 20.6, h: 1.9, fontSize: 28, color: COL.white, valign: "middle" });
text("References: Cafaro et al., ICMI 2017 (NoXi) · Eyben et al., IEEE TAC 2016 (eGeMAPS) · Baltrušaitis et al., FG 2018 (OpenFace 2.0) · Müller et al., ACM MM 2024 (MultiMediate) · Funk, Okada & André, ICMI 2024 (NoXi+J). NoXi data used under its licence and not redistributed.",
  { x: LX, y: 31.9, w: 21.6, h: 0.9, fontSize: 16, color: COL.grey });

(async () => {
  await pres.writeFile({ fileName: OUT });
  const { applyTheme } = require(process.argv[3]);
  await applyTheme(OUT, THEME);
  console.log("saved", OUT);
})();
