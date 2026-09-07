# Cross-Lingual Prediction of Engagement from Non-Verbal Behaviour

Predicting how **engaged** a person is in a conversation using only their
**non-verbal behaviour** (facial expressions + voice tone — never the words),
and testing whether a model trained on one language works on another.

**Dataset:** [NoXi](https://multimediate-challenge.org/datasets/Dataset_NoXi/) —
real expert–novice conversations in French, English and German.

---

## Key results

| Model | CCC |
|---|---|
| Random Forest (best baseline) | **0.886** |
| Tuned MLP / ANN (TensorFlow) | **0.883** |
| MLP untuned | 0.861 |

**Main finding:** engagement is **partly language-specific** — within-language
CCC averages **0.55**, but across languages it drops to **0.39**. Engagement
*levels* are similar across languages, but *how* people express it differs.

**Tuning finding:** dropout 0.1 works best (not 0.3/0.5), Adam beats SGD, and a
256-128 architecture beats 512-256. PyTorch and TensorFlow implementations found
the **same** best configuration.

---

## The pipeline (run in order)

| Script | What it does |
|---|---|
| `src/01_extract_data.py` | Pull the needed files out of the NoXi session zips |
| `src/02_build_features.py` | Build the feature table (17,174 windows x 802 features) |
| `src/03_eda.py` | EDA — 8 charts + statistics |
| `src/04_baselines.py` | Baseline models (Linear Regression, Random Forest, SVR) |
| `src/05_cross_lingual.py` | **Main experiment** — train on one language, test on another |
| `src/06_deep_learning.py` | Deep learning ANN (TensorFlow / Keras) |
| `src/07_tuning.py` | Hyperparameter tuning (dropout, LR, architecture, optimizer) |

`src/pytorch_backup/` holds PyTorch versions of steps 6-7 (used as a cross-check).

---

## Setup

```bash
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Then run the scripts in order from the project root (steps 1-2 only when adding data).

---

## Data

| Property | Value |
|---|---|
| Source | NoXi (Novice-Expert Interaction) |
| Sessions used | 9 (3 French, 3 English, 3 German) |
| Rows | 17,174 one-second windows |
| Features | 802 — 88 voice (eGeMAPS) + 714 face (OpenFace 2.0) |
| Target | Engagement, continuous 0-1 |
| Metric | CCC (Concordance Correlation Coefficient) |

Raw NoXi data is not included in this repository (see `.gitignore`).

---

## Outputs

- `reports/figures/` — EDA charts
- `reports/eda_summary.csv` — engagement statistics per language
- `reports/noxi_crosslingual_ccc.csv` — the cross-lingual result matrix
- `reports/tuning_results.csv` — all hyperparameter configurations ranked
- `reports/noxi_mlp_tuned.keras` — the trained, tuned model

## Documents

- `Project_Report_Week2-4.docx` — introduction, literature review, gap, objectives
- `Literature_Review.xlsx` — 25 reviewed papers
- `Presentation.pptx` — project presentation
- `Project_Explanation.docx` / `Code_Explained_LineByLine.docx` — explanations
- `HOW_IT_WORKS.md` — step-by-step guide
