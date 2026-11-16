// Builds Project_Presentation.pptx from reports/results_summary.json.
// Usage: node tools/make_deck.js <project_dir> <apply_theme.js path>
const path = require("path");
const fs = require("fs");
const pptxgen = require("pptxgenjs");

const ROOT = process.argv[2];
const APPLY = process.argv[3];
const J = JSON.parse(fs.readFileSync(path.join(ROOT, "reports", "results_summary.json"), "utf8"));
const OUT = path.join(ROOT, "Project_Presentation.pptx");

// ---------- theme (Forest & Moss, no blue) ----------
const COL = {
  ink: "1F2A1C", forest: "2C5F2D", moss: "97BC62", pale: "EEF3E8", amber: "D08A2E",
  rust: "A84B3A", sage: "6B8F71", grey: "5F6B5C", white: "FFFFFF", line: "D5DECB",
};
const THEME = {
  name: "Forest Moss", headFontFace: "Cambria", bodyFontFace: "Calibri",
  colors: { dk1: COL.ink, lt1: COL.white, dk2: COL.forest, lt2: COL.pale, accent1: COL.forest,
            accent2: COL.moss, accent3: COL.amber, accent4: COL.sage, accent5: COL.rust, accent6: "4F6D5A",
            hlink: COL.forest, folHlink: COL.sage },
};
const H = "Cambria", B = "Calibri";
const f3 = (x) => Number(x).toFixed(3);

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10 x 5.625
pres.title = "Cross-Lingual Prediction of Engagement from Non-Verbal Behaviour";
pres.theme = { headFontFace: H, bodyFontFace: B };

// ---------- layouts ----------
pres.defineSlideMaster({
  title: "DARK", background: { color: COL.forest },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 1.2, w: 8.8, h: 1.6, fontFace: H,
      fontSize: 34, bold: true, color: COL.white, valign: "bottom", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.6, y: 3.0, w: 8.8, h: 1.8, fontFace: B,
      fontSize: 16, color: "DCE8CF", valign: "top", margin: 0 }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "CONTENT", background: { color: COL.white },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.28, w: 9.0, h: 0.75, fontFace: H,
      fontSize: 26, bold: true, color: COL.forest, valign: "middle", margin: 0 }, text: "" } },
  ],
  slideNumber: { x: 9.2, y: 5.2, w: 0.5, h: 0.3, fontFace: B, fontSize: 10, color: COL.grey },
});

let n = 0;
function slide(master, section, title) {
  if (section) pres.addSection({ title: section });
  const s = pres.addSlide({ masterName: master, sectionTitle: currentSection(section) });
  s.addText(title, { placeholder: "title" });
  n++;
  return s;
}
let _sec = "Introduction";
function currentSection(sec) { if (sec) _sec = sec; return _sec; }

function text(s, t, o) { s.addText(t, Object.assign({ isTextBox: true, fontFace: B, fontSize: 14, color: COL.ink, margin: 0, valign: "top" }, o)); }
function card(s, x, y, w, h, head, body, opt = {}) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.08, fill: { color: opt.fill || COL.pale },
    line: { color: opt.fill || COL.pale }, objectName: "card" });
  text(s, head, { x: x + 0.18, y: y + 0.14, w: w - 0.36, h: 0.4, fontFace: H, fontSize: 16, bold: true, color: opt.head || COL.forest });
  text(s, body, { x: x + 0.18, y: y + 0.56, w: w - 0.36, h: h - 0.68, fontSize: 13, color: opt.color || COL.ink });
}
function badge(s, x, y, label, fill) {
  s.addShape(pres.shapes.OVAL, { x, y, w: 0.5, h: 0.5, fill: { color: fill || COL.forest }, line: { color: fill || COL.forest } });
  text(s, label, { x, y, w: 0.5, h: 0.5, fontSize: 16, bold: true, color: COL.white, align: "center", valign: "middle" });
}
function stat(s, x, y, w, big, small, color) {
  text(s, big, { x, y, w, h: 0.85, fontFace: H, fontSize: 40, bold: true, color: color || COL.forest });
  text(s, small, { x, y: y + 0.85, w, h: 0.6, fontSize: 13, color: COL.grey });
}
const chartBase = () => ({
  catAxisLabelColor: COL.grey, valAxisLabelColor: COL.grey, catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt",
  catAxisLabelFontSize: 11, valAxisLabelFontSize: 10, dataLabelFontFace: "+mn-lt", dataLabelFontSize: 10, dataLabelColor: COL.ink,
  valGridLine: { color: COL.line, size: 0.5 }, catGridLine: { style: "none" }, legendFontFace: "+mn-lt", legendFontSize: 11,
  legendColor: COL.ink, titleFontFace: "+mn-lt",
});

// ---------- data ----------
const master = (J.master || []).filter((r) => r.model !== "LinearRegression");
const best = master[0];
const flat = J.flat || [];
const abl = Object.fromEntries((J.ablation || []).map((r) => [r.modality, r]));
const cross = J.cross;
const diag = cross.matrix.reduce((a, r, i) => a + r[i], 0) / 3;
const off = (cross.matrix.flat().reduce((a, b) => a + b, 0) - diag * 3) / 6;
const drop = Math.round((100 * (diag - off)) / diag);
const OLD = { LinearRegression: 0.284, RandomForest: 0.885, GradientBoosting: 0.901, XGBoost: 0.906, "ANN (MLP)": 0.881 };
const pretty = { GradientBoosting: "Gradient Boosting", RandomForest: "Random Forest", XGBoost: "XGBoost", "ANN (MLP)": "ANN (MLP)",
  CNN_VGG: "CNN (VGG-style)", SimpleRNN: "Simple RNN", LSTM: "LSTM", GRU: "GRU", Transformer: "Transformer",
  "Autoencoder + XGBoost": "Autoencoder + XGBoost", "Autoencoder + dense head": "Autoencoder + dense", LinearRegression: "Linear Regression" };
const P = (m) => pretty[m] || m;

// 1 ---------- title ----------
{
  const s = slide("DARK", "Introduction", "Cross-Lingual Prediction of Engagement from Non-Verbal Behaviour");
  s.addText([
    { text: "Deep Learning semester project", options: { breakLine: true } },
    { text: "Submitted by: [Team member names]", options: { breakLine: true } },
    { text: "Supervisor: [Supervisor name]" },
  ], { placeholder: "body" });
  s.addNotes("Introduce the team. One line: we predict how engaged a person is in a conversation from voice and face only, and test whether it works across languages.");
}

// 2 ---------- problem ----------
{
  const s = slide("CONTENT", null, "Can a model read engagement without the words?");
  text(s, "Tutoring systems, virtual agents and video calls need to know if a person is engaged. Most models are built and tested in a single language. We ask how much of that skill survives in a language the model has never heard.",
    { x: 0.5, y: 1.2, w: 9.0, h: 1.0, fontSize: 15 });
  stat(s, 0.5, 2.55, 2.8, "3", "languages: English, French, German");
  stat(s, 3.6, 2.55, 2.8, "9", "expert-novice conversations (NoXi)");
  stat(s, 6.7, 2.55, 2.8, "17,174", "one-second windows, voice + face only");
  s.addNotes("Problem statement. Words differ between languages, so we use only non-verbal cues - tone of voice and facial behaviour - which could in principle work in any language.");
}

// 3 ---------- objectives ----------
{
  const s = slide("CONTENT", null, "Research objectives");
  const objs = [
    ["Build the dataset", "Language-labelled table of 1-second windows from NoXi: 88 voice + 709 face features."],
    ["Predict engagement", "Compare classic ML with ANN, CNN, RNN, LSTM, GRU, Transformer and autoencoder."],
    ["Measure the language gap", "Train on one language, test on another, on unseen conversations."],
    ["Close the gap", "Find which modality transfers, and whether transfer learning recovers the loss."],
  ];
  objs.forEach(([h, b], i) => {
    const x = 0.5 + (i % 2) * 4.6, y = 1.25 + Math.floor(i / 2) * 1.95;
    badge(s, x, y + 0.1, `O${i + 1}`);
    text(s, h, { x: x + 0.7, y: y + 0.08, w: 3.7, h: 0.45, fontFace: H, fontSize: 17, bold: true, color: COL.forest });
    text(s, b, { x: x + 0.7, y: y + 0.55, w: 3.7, h: 1.1, fontSize: 14 });
  });
  s.addNotes("Four objectives. O3 and O4 are the research contribution.");
}

// 4 ---------- literature gap ----------
{
  const s = slide("CONTENT", null, "What the literature leaves open");
  card(s, 0.5, 1.2, 2.9, 2.35, "Engagement models", "Strong results on NoXi (MultiMediate challenges, attention models) - but trained and tested within the same data.");
  card(s, 3.55, 1.2, 2.9, 2.35, "Emotion across languages", "Speech emotion models lose accuracy across corpora and languages (Schuller 2010, Feraru 2015, AVEC 2018).");
  card(s, 6.6, 1.2, 2.9, 2.35, "Culture and behaviour", "Non-verbal expression is partly universal, partly culture-specific (Elfenbein 2002, Jack 2012, NoXi+J 2024).");
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.5, y: 3.8, w: 9.0, h: 1.15, rectRadius: 0.08, fill: { color: COL.forest }, line: { color: COL.forest } });
  text(s, [{ text: "Gap: ", options: { bold: true } }, { text: "nobody has measured how much an engagement model loses in a new language, which modality causes the loss, or how cheaply it can be recovered." }],
    { x: 0.75, y: 3.95, w: 8.5, h: 0.9, fontSize: 15, color: COL.white, valign: "middle" });
  s.addNotes("26 published papers reviewed. Three strands, one gap.");
}

// 5 ---------- dataset ----------
{
  const s = slide("CONTENT", "Data and method", "NoXi dataset and features");
  const rows = [[{ text: "Language", options: { bold: true, fill: { color: COL.pale } } },
                 { text: "Windows", options: { bold: true, fill: { color: COL.pale } } },
                 { text: "Mean engagement", options: { bold: true, fill: { color: COL.pale } } }]];
  (J.languages || []).forEach((r) => rows.push([r.language, r.windows.toLocaleString("en-US"), f3(r.mean)]));
  s.addTable(rows, { x: 0.5, y: 1.3, w: 4.5, colW: [1.5, 1.3, 1.7], fontFace: B, fontSize: 14, color: COL.ink,
    border: { type: "solid", pt: 0.75, color: COL.line }, rowH: 0.42 });
  text(s, "3 conversations per language, 2 speakers each. Engagement annotated continuously from 0 to 1 at 25 frames per second.",
    { x: 0.5, y: 3.25, w: 4.5, h: 1.2, fontSize: 13, color: COL.grey });
  card(s, 5.4, 1.3, 4.1, 1.55, "Voice - 88 features", "eGeMAPS: pitch, loudness, jitter, shimmer, spectral shape.");
  card(s, 5.4, 3.05, 4.1, 1.55, "Face - 709 features", "OpenFace 2.0: gaze, head pose, landmarks, action units.");
  s.addNotes("NoXi is licensed under an EULA, so the data is not shared. 5 OpenFace bookkeeping columns (frame, timestamp, etc.) were removed - they are not behaviour.");
}

// 6 ---------- pipeline ----------
{
  const s = slide("CONTENT", null, "Pipeline");
  const steps = [["Raw streams", "voice + face at 25 fps"], ["1-second windows", "25 frames each"],
                 ["Features", "797 per window"], ["Models", "ML + 8 deep nets"], ["Session-wise test", "unseen conversations"]];
  steps.forEach(([h, b], i) => {
    const x = 0.5 + i * 1.84;
    s.addShape(pres.shapes.OVAL, { x: x + 0.47, y: 1.45, w: 0.8, h: 0.8, fill: { color: i === 4 ? COL.amber : COL.forest }, line: { color: COL.white } });
    text(s, String(i + 1), { x: x + 0.47, y: 1.45, w: 0.8, h: 0.8, fontFace: H, fontSize: 22, bold: true, color: COL.white, align: "center", valign: "middle" });
    if (i < 4) s.addShape(pres.shapes.LINE, { x: x + 1.35, y: 1.85, w: 1.0, h: 0, line: { color: COL.moss, width: 2, endArrowType: "triangle" } });
    text(s, h, { x, y: 2.45, w: 1.74, h: 0.45, fontFace: H, fontSize: 15, bold: true, color: COL.forest, align: "center" });
    text(s, b, { x, y: 2.9, w: 1.74, h: 0.6, fontSize: 13, color: COL.grey, align: "center" });
  });
  text(s, "Every scaler is fitted on training data only. Neural-network inputs are clipped to [-5, 5] after scaling, because a few extreme values in unseen conversations destabilise them.",
    { x: 0.5, y: 4.0, w: 9.0, h: 0.9, fontSize: 14 });
  s.addNotes("Two data views: the 1-second average (for ML, ANN, autoencoder) and the full 25-frame sequence (for CNN, RNN, LSTM, GRU, Transformer).");
}

// 7 ---------- models by unit ----------
{
  const s = slide("CONTENT", null, "Models covered, by syllabus unit");
  const grid = [
    ["Baselines", "Linear Regression, Random Forest, Gradient Boosting, XGBoost"],
    ["Unit 1 - ANN", "2 hidden layers, ReLU, dropout, Adam vs SGD-momentum, grid tuning"],
    ["Unit 2 - CNN", "1-D CNN, LeNet, VGG, ResNet styles; transfer learning across languages"],
    ["Unit 4 - RNNs", "Simple RNN, LSTM, GRU over the 25-frame sequence"],
    ["Unit 5 - Autoencoder", "797 -> 32 code, then regression on the code"],
    ["Unit 5 - Transformer", "2 encoder blocks, 4-head self-attention, learned positions"],
  ];
  grid.forEach(([h, b], i) => card(s, 0.5 + (i % 3) * 3.05, 1.2 + Math.floor(i / 3) * 1.95, 2.9, 1.8, h, b));
  s.addNotes("Unit 3 (NLP) is out of scope by design - the project uses no words.");
}

// 8 ---------- leakage ----------
{
  const s = slide("CONTENT", "Results", "Random splits overstate performance");
  const keep = flat.filter((r) => OLD[r.model] !== undefined && r.model !== "LinearRegression");
  s.addChart(pres.charts.BAR, [
    { name: "Random split (leaky)", labels: keep.map((r) => P(r.model)), values: keep.map((r) => OLD[r.model]) },
    { name: "Unseen conversations", labels: keep.map((r) => P(r.model)), values: keep.map((r) => r.ccc) },
  ], Object.assign(chartBase(), { x: 0.4, y: 1.15, w: 5.6, h: 3.9, barDir: "col", barGapWidthPct: 60,
    chartColors: [COL.line, COL.forest], showValue: true, dataLabelFormatCode: "0.00", dataLabelPosition: "outEnd",
    valAxisMinVal: 0, valAxisMaxVal: 1, valAxisLabelFormatCode: "0.0", showLegend: true, legendPos: "b",
    showTitle: true, title: "CCC", titleFontSize: 12, titleColor: COL.grey }));
  text(s, "With a random split, second 100 of a conversation trains the model and second 101 tests it. The two are almost identical, so the model recognises the person instead of learning behaviour.",
    { x: 6.3, y: 1.3, w: 3.2, h: 2.2, fontSize: 14 });
  text(s, "Holding out whole conversations gives the honest score.", { x: 6.3, y: 3.6, w: 3.2, h: 0.9, fontSize: 14, bold: true, color: COL.forest });
  s.addNotes("Data leakage found and fixed. 3 session-wise folds: each holds out one full conversation per language.");
}

// 9 ---------- all models ----------
{
  const s = slide("CONTENT", null, `${P(best.model)} is the best model on unseen conversations`);
  const rows = master.slice().reverse();
  s.addChart(pres.charts.BAR, [{ name: "CCC", labels: rows.map((r) => P(r.model)), values: rows.map((r) => r.session_ccc) }],
    Object.assign(chartBase(), { x: 0.4, y: 1.1, w: 6.0, h: 4.1, barDir: "bar", barGapWidthPct: 45,
      chartColors: [COL.forest], showValue: true, dataLabelFormatCode: "0.000", dataLabelPosition: "outEnd",
      valAxisMinVal: 0, valAxisMaxVal: 0.8, valAxisLabelFormatCode: "0.0", showLegend: false }));
  const fams = {};
  master.forEach((r) => { if (!(r.family in fams)) fams[r.family] = r; });
  text(s, "Best of each family (mean over 3 folds)", { x: 6.7, y: 1.2, w: 2.8, h: 0.4, fontSize: 13, bold: true, color: COL.forest });
  text(s, Object.values(fams).map((r, i, a) => ({ text: `${r.family}: ${f3(r.session_ccc)}`, options: { bullet: true, breakLine: i < a.length - 1 } })),
    { x: 6.7, y: 1.65, w: 2.8, h: 2.4, fontSize: 14, paraSpaceAfter: 4 });
  text(s, "Small data (9 conversations) favours simple models.", { x: 6.7, y: 4.2, w: 2.8, h: 0.8, fontSize: 13, italic: true, color: COL.grey });
  s.addNotes("All models on the same 3 session-wise folds. Linear Regression is left off the chart (it collapses on one fold).");
}

// 10 ---------- deep models table ----------
{
  const s = slide("CONTENT", null, "Deep models on unseen conversations");
  const hdr = ["Model", "Input", "CCC (mean ± std)", "Pearson"].map((t) => ({ text: t, options: { bold: true, fill: { color: COL.pale } } }));
  const rows = [hdr];
  (J.sequence || []).forEach((r) => rows.push([P(r.model), "25 x 797 sequence", `${f3(r.ccc)} ± ${f3(r.std)}`, f3(r.pearson)]));
  const ann = flat.find((r) => r.model === "ANN (MLP)");
  if (ann) rows.push(["ANN (MLP)", "797 average", `${f3(ann.ccc)} ± ${f3(ann.std)}`, f3(ann.pearson)]);
  (J.autoencoder || []).forEach((r) => rows.push([P(r.model), "797 -> 32 code", `${f3(r.ccc)} ± ${f3(r.std)}`, f3(r.pearson)]));
  s.addTable(rows, { x: 0.5, y: 1.15, w: 9.0, colW: [3.0, 2.2, 2.2, 1.6], fontFace: B, fontSize: 13, color: COL.ink,
    border: { type: "solid", pt: 0.75, color: COL.line }, rowH: 0.36 });
  s.addNotes("Gated recurrent nets (LSTM, GRU) vs simple RNN; the autoencoder compresses 25x and keeps most of the signal.");
}

// 11 ---------- cross-lingual ----------
{
  const s = slide("CONTENT", null, `Engagement models lose ${drop}% in a new language`);
  const shade = (v, d) => (d ? COL.forest : v >= 0.5 ? "B7CF96" : v >= 0.3 ? "DCE8CF" : "F3D9D3");
  const rows = [[{ text: "Train \\ Test", options: { bold: true, fill: { color: COL.pale } } },
    ...cross.langs.map((l) => ({ text: l, options: { bold: true, fill: { color: COL.pale }, align: "center" } }))]];
  cross.matrix.forEach((r, i) => rows.push([{ text: cross.langs[i], options: { bold: true, fill: { color: COL.pale } } },
    ...r.map((v, j) => ({ text: f3(v), options: { align: "center", fill: { color: shade(v, i === j) }, color: i === j ? COL.white : COL.ink, bold: i === j } }))]));
  s.addTable(rows, { x: 0.5, y: 1.3, w: 5.4, colW: [1.5, 1.3, 1.3, 1.3], fontFace: B, fontSize: 15, color: COL.ink,
    border: { type: "solid", pt: 1, color: COL.white }, rowH: 0.6 });
  text(s, "Diagonal: train and test in the same language (leave-one-conversation-out).", { x: 0.5, y: 3.85, w: 5.4, h: 0.6, fontSize: 12, color: COL.grey });
  stat(s, 6.4, 1.3, 3.1, f3(diag), "same language");
  stat(s, 6.4, 2.85, 3.1, f3(off), "different language", COL.rust);
  s.addNotes("Rows = training language, columns = test language. French-trained models transfer worst to English; German-trained models transfer best.");
}

// 12 ---------- ablation ----------
{
  const v = abl.voice, fc = abl.face, b = abl.both;
  const s = slide("CONTENT", null, "Voice carries engagement across languages; face does not");
  s.addChart(pres.charts.BAR, [
    { name: "Same language", labels: ["Voice (88)", "Face (709)", "Both (797)"], values: [v.within_ccc, fc.within_ccc, b.within_ccc] },
    { name: "Other language", labels: ["Voice (88)", "Face (709)", "Both (797)"], values: [v.cross_ccc, fc.cross_ccc, b.cross_ccc] },
  ], Object.assign(chartBase(), { x: 0.4, y: 1.15, w: 5.6, h: 3.9, barDir: "col", barGapWidthPct: 60,
    chartColors: [COL.forest, COL.amber], showValue: true, dataLabelFormatCode: "0.00", dataLabelPosition: "outEnd",
    valAxisMinVal: 0, valAxisMaxVal: 0.8, valAxisLabelFormatCode: "0.0", showLegend: true, legendPos: "b" }));
  stat(s, 6.4, 1.2, 1.5, `${Math.round(v.drop_pct)}%`, "voice drop");
  stat(s, 8.0, 1.2, 1.5, `${Math.round(fc.drop_pct)}%`, "face drop", COL.rust);
  text(s, `Voice alone scores ${f3(v.session_ccc)} on unseen conversations - better than voice + face (${f3(b.session_ccc)}).`,
    { x: 6.4, y: 2.85, w: 3.1, h: 1.0, fontSize: 14 });
  text(s, "Caveat: each language was recorded at a different site, so part of the face drop may be camera setup.",
    { x: 6.4, y: 3.95, w: 3.1, h: 1.0, fontSize: 12, italic: true, color: COL.grey });
  s.addNotes("Ablation with XGBoost. Main finding of the project: tone of voice is the more language-independent engagement cue.");
}

// 13 ---------- transfer learning ----------
if (J.transfer_by_fraction) {
  const T = J.transfer_by_fraction;
  const labels = T.map((r) => `${Math.round(r.fraction * 100)}%`);
  const full = T[T.length - 1];
  const bestAdapt = Math.max(full.head_only, full.fine_tune);
  const s = slide("CONTENT", null, bestAdapt > full.scratch ? "Pretraining on other languages beats starting from scratch" : "Transfer learning across languages");
  s.addChart(pres.charts.LINE, [
    { name: "Head-only", labels, values: T.map((r) => r.head_only) },
    { name: "Fine-tune", labels, values: T.map((r) => r.fine_tune) },
    { name: "Scratch", labels, values: T.map((r) => r.scratch) },
    { name: "Zero-shot", labels, values: T.map((r) => r.zero_shot) },
  ], Object.assign(chartBase(), { x: 0.4, y: 1.15, w: 5.8, h: 3.9, chartColors: [COL.forest, COL.moss, COL.rust, COL.grey],
    lineSize: 2, lineDataSymbol: "circle", lineDataSymbolSize: 7, valAxisMinVal: 0, valAxisLabelFormatCode: "0.0",
    showLegend: true, legendPos: "b", showCatAxisTitle: true, catAxisTitle: "share of one new-language conversation used",
    catAxisTitleFontSize: 11, catAxisTitleColor: COL.grey }));
  text(s, "CNN pretrained on two languages, adapted with one conversation of the third, tested on its other two conversations.",
    { x: 6.5, y: 1.25, w: 3.0, h: 1.4, fontSize: 14 });
  stat(s, 6.5, 2.75, 1.45, f3(bestAdapt), "best adapted");
  stat(s, 8.05, 2.75, 1.45, f3(full.scratch), "scratch", COL.rust);
  s.addNotes("Head-only freezes the convolution layers; fine-tune retrains all layers with a small learning rate; scratch uses no pretraining.");
}

// 14 ---------- demo ----------
{
  const s = slide("CONTENT", "Prototype and conclusion", "AI prototype: live engagement demo");
  const img = path.join(ROOT, "reports", "figures", "demo_app.jpg");
  if (fs.existsSync(img)) s.addImage({ path: img, x: 0.5, y: 1.15, w: 5.6, h: 3.9, sizing: { type: "contain", w: 5.6, h: 3.9 } });
  else card(s, 0.5, 1.15, 5.6, 3.9, "Demo screenshot", "Run: streamlit run app.py");
  text(s, [
    { text: "Pick any conversation and speaker", options: { bullet: true, breakLine: true } },
    { text: "Switch input: voice + face, voice, face", options: { bullet: true, breakLine: true } },
    { text: "Predicted vs real engagement, second by second", options: { bullet: true, breakLine: true } },
    { text: "Always uses the model that never saw that conversation", options: { bullet: true } },
  ], { x: 6.4, y: 1.3, w: 3.1, h: 3.2, fontSize: 14, paraSpaceAfter: 8 });
  s.addNotes("Built with Streamlit. Command: streamlit run app.py, opens at localhost:8501.");
}

// 15 ---------- limitations ----------
{
  const s = slide("CONTENT", null, "Limitations");
  const L = [
    ["Small corpus", "9 conversations, 18 speakers - fold scores vary."],
    ["Language = site", "Each language recorded in a different country and setup."],
    ["Fixed seed", "Fold spread reported, but single runs per fold."],
    ["1-second windows", "Longer context (10-30 s) not yet tested."],
  ];
  L.forEach(([h, b], i) => card(s, 0.5 + (i % 2) * 4.6, 1.2 + Math.floor(i / 2) * 1.95, 4.4, 1.75, h, b));
}

// 16 ---------- conclusion ----------
{
  const s = slide("DARK", null, "Conclusion");
  s.addText([
    { text: `Honest evaluation matters: unseen-conversation CCC is about ${f3(best.session_ccc)}, not 0.906.`, options: { bullet: true, breakLine: true } },
    { text: `Engagement models lose ${drop}% in a new language.`, options: { bullet: true, breakLine: true } },
    { text: `Voice transfers far better than face (${Math.round(abl.voice.drop_pct)}% vs ${Math.round(abl.face.drop_pct)}% drop).`, options: { bullet: true, breakLine: true } },
    { text: "Future: longer windows, NoXi+J languages, label-free domain adaptation.", options: { bullet: true } },
  ], { placeholder: "body", paraSpaceAfter: 6 });
  s.addNotes("Thank the audience and invite questions.");
}

(async () => {
  await pres.writeFile({ fileName: OUT });
  const { applyTheme } = require(APPLY);
  await applyTheme(OUT, THEME);
  console.log("saved", OUT, "slides:", n);
})();
