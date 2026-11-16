"""Rebuilds Paper_Writing_Skeleton.docx so it matches Research_Paper_Draft_v2.docx.
Reuses the skeleton's own paragraph formats; numbers come from reports/results_summary.json."""
import os
import copy
import json
import shutil
import pandas as pd
from docx import Document

SRC = "Paper_Writing_Skeleton.docx"
if not os.path.exists("Paper_Writing_Skeleton_old.docx"):
    shutil.copy(SRC, "Paper_Writing_Skeleton_old.docx")
d = Document("Paper_Writing_Skeleton_old.docx")
ps = d.paragraphs
TPL = {"title": ps[0], "plain": ps[1], "h1": ps[3], "note": ps[4], "bullet": ps[6], "label": ps[17], "h2": ps[35]}
TPL = {k: copy.deepcopy(p._p) for k, p in TPL.items()}
body = d.element.body
sect = body[-1]
for el in list(body)[:-1]:
    body.remove(el)

# ---------- numbers ----------
J = json.load(open("reports/results_summary.json"))
f3 = lambda x: f"{x:.3f}"
flat = {r["model"]: r for r in J["flat"]}
seq = sorted(J["sequence"], key=lambda r: -r["ccc"])
ae = {r["model"]: r for r in J["autoencoder"]}
best = [r for r in J["master"] if r["model"] != "LinearRegression"][0]
abl = {r["modality"]: r for r in J["ablation"]}
cm, langs = J["cross"]["matrix"], J["cross"]["langs"]
diag = sum(cm[i][i] for i in range(3)) / 3
off = (sum(map(sum, cm)) - 3 * diag) / 6
drop = round(100 * (diag - off) / diag)
v, fc, both = abl["voice"], abl["face"], abl["both"]
T = {round(r["fraction"], 2): r for r in J["transfer_by_fraction"]}
full, tenth = T[1.0], T[0.1]
n10 = int(pd.read_csv("reports/transfer_results.csv").query("fraction == 0.1")["n_adapt"].mean())
gb, ann, xgb = flat["GradientBoosting"], flat["ANN (MLP)"], flat["XGBoost"]
lr = flat["LinearRegression"]
seq_txt = " > ".join(f"{r['model'].replace('CNN_VGG', 'CNN (VGG)').replace('SimpleRNN', 'simple RNN')} {f3(r['ccc'])}" for r in seq)


# ---------- writers ----------
def add(kind, text):
    el = copy.deepcopy(TPL[kind])
    sect.addprevious(el)
    runs = el.findall(".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}r")
    tnodes = runs[0].findall("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t")
    tnodes[0].text = text
    for t in tnodes[1:]:
        t.getparent().remove(t)
    for r in runs[1:]:
        r.getparent().remove(r)


def bullets(*items):
    for it in items:
        add("bullet", it)


add("title", "Research Paper — Writing Skeleton (v2, final results)")
add("plain", "How to use this: each “Paragraph” label below is ONE paragraph you write. Turn its bullets into your own sentences. "
             "Don’t open the draft while you write a section — write from these notes, then check numbers against "
             "Research_Paper_Draft_v2.docx afterwards. Keep every number exactly as written. Put citations [n] where they appear here.")
add("plain", "You may copy straight from the draft: the title, index terms, the six tables, equation (1), and the reference list. "
             "Those aren’t prose. All results are on held-out conversations unless a note says “random split”.")

add("h1", "Title")
add("note", "▸ Copy from draft.")

add("h1", "Abstract  (~200 words, one paragraph)")
bullets(
    "engagement estimation → used in tutors, virtual agents, video meetings",
    "problem: models trained + tested in ONE language; what survives in a new language, and which channel carries over = unknown",
    "data: NoXi, English / French / German; 88 eGeMAPS voice + 709 OpenFace face → 17,174 one-second windows, no words",
    f"leakage: random window split leaks conversation identity → gradient boosting 0.901 → {f3(gb['ccc'])} when whole conversations held out",
    f"best of 12 models on unseen conversations: gradient boosting {f3(best['session_ccc'])}; ahead of MLP, CNN, simple RNN, LSTM, GRU, Transformer, autoencoder",
    f"new language: CCC {f3(diag)} → {f3(off)} = {drop}% loss",
    f"ablation: voice alone {f3(v['session_ccc'])} > voice + face {f3(both['session_ccc'])}; voice loses {v['drop_pct']:.0f}% across languages, face {fc['drop_pct']:.0f}%",
    f"transfer: CNN pretrained on 2 languages + 1 conversation of the 3rd → {f3(full['fine_tune'])} vs {f3(full['scratch'])} from scratch",
)

add("h1", "Index Terms")
add("note", "▸ Copy from draft.")

add("h1", "I. Introduction")
add("label", "Paragraph 1 — what engagement is and why it matters")
bullets("definition: how people start / keep / end their connection in an interaction [1]",
        "why automate: any system that adapts to attention — tutors, social agents [2]",
        "words are unreliable → most work uses non-verbal cues: gaze, face, head, prosody [2], [3]")
add("label", "Paragraph 2 — the gap")
bullets("MultiMediate challenges: frame-level engagement labels on NoXi, scored with CCC [4], [5]",
        "models on these labels do well within the corpus [6], [7]",
        "BUT the effect of language is rarely isolated",
        "psychology: affect expression = partly universal, partly cultural [8], [9]",
        "speech emotion recognition drops across corpora and languages [10]–[12]",
        "for engagement: does the same drop happen? how big? → not measured")
add("label", "Paragraph 3 — what you did (6 things)")
bullets("(i) language-labelled table of 1-s windows, voice + face only",
        "(ii) show random window splits inflate scores → evaluate everything on held-out conversations",
        "(iii) classic regressors vs 8 deep architectures under that protocol",
        "(iv) train on each language, test on every other",
        "(v) ablation: separate voice from face",
        "(vi) can transfer learning recover the cross-lingual loss?",
        f"headline: new language → lose {drop}%; most of the loss comes from the FACE channel")

add("h1", "II. Related Work")
add("note", "▸ Unchanged from the first skeleton — same three paragraphs, same citations.")
add("h2", "A. Engagement Recognition  (one paragraph)")
bullets("Sidner: engagement in human–robot talk via gaze, nodding, mutual attention [1]",
        "Whitehill: student engagement from face ≈ human accuracy [13]",
        "D’Mello & Graesser: affective states incl. engagement change continuously → use continuous labels [14]",
        "Doherty & Doherty: HCI engagement definitions + measures inconsistent [3]",
        "Oertel: task vs social engagement; culture rarely studied [2]",
        "on NoXi: Dermouche & Pelachaud, behaviour sequences [6]; MultiMediate went backchannels → engagement → multi-domain [15], [4], [5]; attention models lead now [7]")
add("h2", "B. Non-Verbal Feature Extraction  (one short paragraph)")
bullets("eGeMAPS = 88 acoustic descriptors made for affective computing [16]; computed with openSMILE [17]",
        "OpenFace 2.0 = landmarks, head pose, gaze, action units [18]",
        "combining = multimodal fusion [19]; you use early fusion = concatenate both at each step")
add("h2", "C. Cross-Cultural and Cross-Lingual Transfer  (one paragraph)")
bullets("Schuller: emotion model trained on one corpus loses accuracy on another [10]",
        "Feraru: same across languages; closer languages transfer better [11]",
        "AVEC 2018 on SEWA: train German, test Hungarian → same drop [12], [20]",
        "NoXi+J: added Japanese + Chinese, found cultural differences in engagement cues [21]",
        "your angle: known for EMOTION; you measure it for ENGAGEMENT inside one consistently labelled corpus")

add("h1", "III. Dataset and Preprocessing")
add("h2", "A. The NoXi Corpus")
bullets("screen-mediated, expert explains a topic, novice listens [22]",
        "recorded in France, UK, Germany",
        "engagement labelled 0–1, continuously, 25 Hz",
        "9 sessions (3 per language) × 2 people = 18 recordings",
        "used under licence, not redistributed")
add("h2", "B. Features")
bullets("88 eGeMAPS [16] + OpenFace 2.0 [18], both supplied with corpus, 25 fps",
        "NEW: 5 OpenFace columns removed — frame number, face id, timestamp, confidence, success → they describe the recording, not behaviour → 709 face features",
        "no speech content / transcript — words differ by language → would confound the comparison")
add("h2", "C. Windowing and Cleaning")
bullets("align voice + face + label, trim to shortest; cut into 1-s windows = 25 frames, no overlap",
        "2 versions: (a) mean of each feature → 797 numbers → classic models, MLP, autoencoder; (b) full 25 × 797 sequence → CNN, RNNs, Transformer",
        "label = mean engagement in window; bad labels → missing; windows with no label dropped",
        "each window tagged with language, session, role",
        "result: 17,174 windows → Table I")
add("note", "▸ Table I — copy from draft.")
add("h2", "D. Exploratory Analysis")
bullets("ANOVA: languages differ (F = 84.67, p < 0.001) — but differences are small",
        "experts more engaged than novices: 0.659 vs 0.506",
        "voice correlates more than face: mean |r| 0.391 vs 0.187 → voice carries more linear signal")

add("h1", "IV. Methodology")
add("h2", "A. Evaluation Metric")
bullets("use CCC [23] → equation (1) — copy formula from draft",
        "symbols: ρ = Pearson, μ = mean, σ = std, y = truth, ŷ = prediction",
        "why CCC: unlike Pearson, it punishes being consistently too high / too low",
        "standard in MultiMediate [4], [5]; also report MAE")
add("h2", "B. Classical Baselines")
bullets("linear regression, random forest (100 trees), hist. gradient boosting (300), XGBoost [24] (300 trees, depth 6, lr 0.1, subsample 0.8)",
        "standardised inputs")
add("h2", "C. Deep Architectures")
add("label", "Paragraph — shared setup")
bullets("TensorFlow/Keras, Adam [25], MSE loss, dropout [26]; linear output — target is a number",
        "NEW: inputs standardised on training data, then clipped to [−5, 5]",
        "why: ~0.02% of values in unseen sessions are hundreds to thousands of std from the training mean → trees don’t care, neural nets break")
add("label", "Paragraph — MLP")
bullets("2 hidden layers 256 → 128, ReLU, on the window mean",
        "dropout 0.1, lr 10⁻³, widths, optimiser chosen by grid search over 13 configs on a validation split (development)")
add("label", "Paragraph — CNNs")
bullets("input is a time series, not an image → 1-D conv along the 25 frames",
        "LeNet [27] / VGG [28] (2 stacked kernel-3 convs per block) / ResNet [29] (residual + batch norm)",
        "VGG-style = best in development → represents CNNs in the final comparison")
add("label", "Paragraph — Recurrent networks  (NEW)")
bullets("simple RNN, LSTM [30], GRU — each 128 units, read the 25 frames in order",
        "final hidden state → Dense 64 → output")
add("label", "Paragraph — Transformer")
bullets("each frame → 64 dims + learned positional encoding",
        "2 encoder blocks: 4-head self-attention, 128 feed-forward, residual + layer norm [31]; average over frames → dense output")
add("label", "Paragraph — Autoencoder  (NEW)")
bullets("encoder 797 → 256 → 32, mirrored decoder, trained WITHOUT labels to rebuild the input",
        "freeze encoder → small dense head OR XGBoost predicts engagement from the 32-number code")
add("h2", "D. Evaluation Protocols  (one paragraph, three parts)")
bullets("unseen conversations: 3 session-disjoint folds; each holds out 1 whole conversation per language (both people), trains on the other 6; report mean ± sd",
        "for comparison only: classic models + MLP also scored on a random 80/20 window split",
        "cross-lingual: random forest, train on ALL of one language, test on ALL of another; diagonal = leave-one-session-out inside the language",
        "ablation: same XGBoost on voice only (88), face only (709), both (797), under both protocols")
add("h2", "E. Transfer Learning")
bullets("tuned LeNet-style CNN pretrained on the other 2 languages; scaler fitted on source languages only",
        "target: ONE conversation to adapt, its other TWO to test → adaptation and test never share a session",
        "each conversation takes a turn; 10%, 25%, 50%, 100% of it tried",
        "4 conditions: zero-shot / head-only (freeze conv) / fine-tune (all layers, lr 10⁻⁴) / scratch")

add("h1", "V. Results")
add("h2", "A. Random Split Versus Unseen Conversations")
bullets("random split: every non-linear model > 0.88",
        f"held-out conversations remove 0.25–0.29: gradient boosting 0.901 → {f3(gb['ccc'])}; MLP 0.881 → {f3(ann['ccc'])}; XGBoost 0.906 → {f3(xgb['ccc'])}",
        "why: neighbouring 1-s windows of one conversation ≈ identical → random split rewards recognising the speaker",
        "everything after this uses held-out conversations",
        f"linear regression unstable across folds: {f3(lr['ccc'])} ± {f3(lr['std'])}")
add("note", "▸ Table II — copy from draft.")
add("h2", "B. Deep Models")
bullets(f"sequence models: {seq_txt}",
        f"MLP on window mean {f3(ann['ccc'])}",
        f"autoencoder keeps most of the signal after 25× compression: {f3(ae['Autoencoder + XGBoost']['ccc'])} (XGBoost on code), {f3(ae['Autoencoder + dense head']['ccc'])} (dense head)",
        f"no deep model beats gradient boosting {f3(best['session_ccc'])}")
add("note", "▸ Table III — copy from draft.")
add("h2", "C. Cross-Lingual Transfer")
bullets(f"same-language avg {f3(diag)}, cross-language avg {f3(off)} → {drop}% drop → Table IV",
        f"asymmetric: French model → English only {f3(cm[1][0])}",
        f"German model → French {f3(cm[2][1])}, ABOVE French’s own {f3(cm[1][1])} — likely because it trains on 3 sessions not 2")
add("note", "▸ Table IV — copy from draft.")
add("h2", "D. Modality Ablation  (NEW)")
bullets(f"voice alone strongest: {f3(v['session_ccc'])} vs face {f3(fc['session_ccc'])} vs both {f3(both['session_ccc'])} → adding 709 face features slightly HURTS",
        f"voice: {f3(v['within_ccc'])} → {f3(v['cross_ccc'])} in a new language = {v['drop_pct']:.0f}% loss",
        f"face: {f3(fc['within_ccc'])} → {f3(fc['cross_ccc'])} = {fc['drop_pct']:.0f}% loss",
        "→ most of the combined model’s cross-lingual loss comes from the face → Table V")
add("note", "▸ Table V — copy from draft.")
add("h2", "E. Transfer Learning")
bullets(f"zero-shot (pretrained, unchanged): {f3(full['zero_shot'])}",
        f"adapt with 1 full conversation: head-only {f3(full['head_only'])}, fine-tune {f3(full['fine_tune'])}; scratch {f3(full['scratch'])} → Table VI",
        f"only 10% of the conversation ({n10} windows): fine-tune {f3(tenth['fine_tune'])} vs scratch {f3(tenth['scratch'])}",
        "→ pretraining on other languages beats starting from scratch at every amount of data")
add("note", "▸ Table VI — copy from draft.")

add("h1", "VI. Discussion")
add("h2", "A. Simple Models Generalise Best at This Scale")
bullets("no deep model beat gradient boosting on held-out conversations",
        "fits benchmark evidence: trees strong on medium tabular data [32]",
        "only 9 conversations → few independent speakers to learn from; MLP varied most across folds",
        "sequence models (all 25 frames) didn’t clearly beat window-mean models → variation inside 1 s ≈ noise; engagement changes slower [14]")
add("h2", "B. Voice Travels, Faces Do Not")
bullets(f"the {drop}% loss is NOT spread evenly",
        "prosody (pitch, loudness, voice quality) transfers with little loss; face loses more than half",
        "fits psychology: expression partly universal, partly cultural; facial display rules = cultural part [8], [9]",
        "practical: start from a VOICE model in a new language; a little in-language data to adapt a pretrained model > same data alone")
add("h2", "C. Language or Recording Site?")
bullets("in NoXi, language = also recording site + speakers + topics",
        "face is the most exposed: camera position + lighting differ by site → part of its drop may be recording conditions, not culture",
        "NoXi+J [21], SEWA [20] could separate them")

add("h1", "VII. Limitations  (one paragraph)")
bullets("small: 9 sessions, 18 recordings → large fold-to-fold variation; 3 folds = coarse uncertainty",
        "single training run per fold, fixed seed",
        "MLP + CNN hyperparameters chosen during development on a random split",
        "only 1-s windows; ablation used one model family")

add("h1", "VIII. Conclusion  (one paragraph)")
bullets("held-out conversations are essential: random split overstated by ≈ 0.28 CCC",
        "on unseen conversations: gradient boosting on 1-s averages beat 8 deep architectures",
        f"across languages: −{drop}%; ablation traces most of it to the face",
        f"voice = best single modality AND most language-independent ({v['drop_pct']:.0f}% vs {fc['drop_pct']:.0f}% drop)",
        "future: longer windows, NoXi+J languages, domain adaptation with no target labels")

add("h1", "References")
add("note", "▸ Copy the full list from the draft — keep the same numbers [1]–[32].")

d.save(SRC)
print("saved", SRC, "(old version kept as Paper_Writing_Skeleton_old.docx)")
