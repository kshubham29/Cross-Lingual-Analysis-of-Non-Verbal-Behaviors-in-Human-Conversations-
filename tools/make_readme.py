"""Writes README.md with the numbers from reports/results_summary.json."""
import json

J = json.load(open("reports/results_summary.json"))
f3 = lambda x: f"{x:.3f}"
master = J["master"]
best = [r for r in master if r["model"] != "LinearRegression"][0]
abl = {r["modality"]: r for r in J["ablation"]}
cm, langs = J["cross"]["matrix"], J["cross"]["langs"]
diag = sum(cm[i][i] for i in range(3)) / 3
off = (sum(map(sum, cm)) - 3 * diag) / 6
drop = round(100 * (diag - off) / diag)

rows = "\n".join(
    f"| {r['model']} | {r['family']} | **{f3(r['session_ccc'])}** ± {f3(r['session_std'])} | "
    f"{'' if r['random_split_ccc'] is None else f3(r['random_split_ccc'])} |" for r in master)
abl_rows = "\n".join(
    f"| {m} | {int(abl[m]['n_features'])} | {f3(abl[m]['session_ccc'])} | {f3(abl[m]['within_ccc'])} | "
    f"{f3(abl[m]['cross_ccc'])} | **{abl[m]['drop_pct']:.0f}%** |" for m in ("voice", "face", "both"))
cross_rows = "\n".join(f"| **{langs[i]}** | " + " | ".join(f3(x) for x in cm[i]) + " |" for i in range(3))
transfer = ""
if "transfer_by_fraction" in J:
    transfer = "\n### Transfer learning (CNN pretrained on 2 languages, adapted on 1 conversation of the 3rd)\n\n" \
        "| Share of the adaptation conversation | Zero-shot | Head-only | Fine-tune | Scratch |\n|---|---|---|---|---|\n" + \
        "\n".join(f"| {int(r['fraction'] * 100)}% | {f3(r['zero_shot'])} | {f3(r['head_only'])} | {f3(r['fine_tune'])} | {f3(r['scratch'])} |"
                  for r in J["transfer_by_fraction"]) + "\n"

readme = f"""# Cross-Lingual Prediction of Engagement from Non-Verbal Behaviour

Predicting how **engaged** a person is in a conversation from **non-verbal behaviour only**
(voice tone + facial behaviour, never the words), and testing whether a model trained
on one language still works on another.

**Dataset:** [NoXi](https://multimediate-challenge.org/datasets/Dataset_NoXi/) - expert-novice
conversations in English, French and German (licensed, not included in this repository).

---

## Key findings

1. **Random splits overstate performance.** Neighbouring seconds of the same conversation land in
   both train and test. Holding out whole conversations drops XGBoost from 0.906 to
   {f3(next(r['session_ccc'] for r in master if r['model'] == 'XGBoost'))}. All results below are on **unseen conversations**.
2. **Best model:** {best['model']} - CCC **{f3(best['session_ccc'])}** on unseen conversations.
3. **A new language costs {drop}%:** within-language CCC {f3(diag)} vs cross-language {f3(off)}.
4. **Voice transferred better than face in our data:** voice alone loses **{abl['voice']['drop_pct']:.0f}%** across languages,
   face features **{abl['face']['drop_pct']:.0f}%**. Voice alone ({f3(abl['voice']['session_ccc'])}) even beats voice + face
   ({f3(abl['both']['session_ccc'])}).

### All models - 3 session-disjoint folds (each holds out one conversation per language)

| Model | Family | CCC on unseen conversations | Old random-split CCC |
|---|---|---|---|
{rows}

### Ablation (XGBoost)

| Input | Features | Unseen conversations | Same language | Other language | Drop |
|---|---|---|---|---|---|
{abl_rows}

### Cross-lingual CCC (rows = train, columns = test)

| Train \\ Test | {' | '.join(langs)} |
|---|---|---|---|
{cross_rows}
{transfer}
---

## Pipeline (run from the project folder, in order)

| Script | What it does |
|---|---|
| `src/01_extract_data.py` | Pull the needed files out of the NoXi zips |
| `src/02_build_features.py` | Build 1-second windows: table (17,174 x 802) + sequences (17,174 x 25 x 802) |
| `src/03_eda.py` | Exploratory analysis - charts and statistics |
| `src/04_baselines.py` | ML baselines (random split, development stage) |
| `src/05_cross_lingual.py` | **Main experiment** - train on one language, test on another |
| `src/06_deep_learning.py` | ANN (TensorFlow / Keras) |
| `src/07_tuning.py` | ANN tuning: dropout, learning rate, layer sizes, Adam vs SGD |
| `src/08_sequence_models.py` | XGBoost vs MLP vs 1-D CNN |
| `src/09_cnn.py` | LeNet-style CNN + grid search |
| `src/10_transfer_learning.py` | Transfer learning across languages (session-disjoint) |
| `src/11_cnn_architectures.py` | LeNet / VGG / ResNet styles |
| `src/12_transformer.py` | Transformer encoder |
| `src/13_lstm.py` | LSTM |
| `src/14_session_eval.py` | **Final evaluation** - classic models + ANN on unseen conversations |
| `src/15_session_sequence.py` | **Final evaluation** - CNN, Simple RNN, LSTM, GRU, Transformer |
| `src/16_autoencoder.py` | Autoencoder (797 -> 32) + regression on the code |
| `src/17_ablation.py` | Voice vs face vs both |
| `src/18_master_results.py` | One master table + chart (`reports/master_results.csv`) |
| `app.py` | Demo app: `streamlit run app.py` |

Scripts 04-13 are the development stage (random split); 14-18 give the final, leakage-free numbers.
The 5 OpenFace bookkeeping columns (frame, face id, timestamp, confidence, success) are removed in 05, 10 and 14-18,
leaving 797 features (88 voice + 709 face).

## Setup

```bash
py -3.12 -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
```

## Data

| Property | Value |
|---|---|
| Source | NoXi (Novice-Expert Interaction) |
| Sessions used | 9 (3 English, 3 French, 3 German), 2 speakers each |
| Rows | 17,174 one-second windows |
| Features | 797 - 88 voice (eGeMAPS) + 709 face (OpenFace 2.0) |
| Target | Engagement, continuous 0-1 |
| Metric | CCC (Concordance Correlation Coefficient) |

The NoXi data is licensed under an End-User Licence Agreement and is **not** included (see `.gitignore`).

## Documents

- `Research_Paper_Draft_v2.docx` - IEEE-format paper draft with the final results
- `Project_Presentation.pptx` - presentation; `Research_Poster.pptx` - A1 poster
- `Laboratory_Manual.docx` - one experiment per script, with viva questions
- `Literature_Review.xlsx` - 26 reviewed papers
- `tools/` - scripts that rebuild these documents from `reports/`
"""
open("README.md", "w", encoding="utf-8").write(readme)
print("saved README.md")
