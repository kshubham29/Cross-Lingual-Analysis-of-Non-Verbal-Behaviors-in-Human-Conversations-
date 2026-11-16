# Cross-Lingual Prediction of Engagement from Non-Verbal Behaviour

Predicting how **engaged** a person is in a conversation from **non-verbal behaviour only**
(voice tone + facial behaviour, never the words), and testing whether a model trained
on one language still works on another.

**Dataset:** [NoXi](https://multimediate-challenge.org/datasets/Dataset_NoXi/) - expert-novice
conversations in English, French and German (licensed, not included in this repository).

---

## Key findings

1. **Random splits overstate performance.** Neighbouring seconds of the same conversation land in
   both train and test. Holding out whole conversations drops XGBoost from 0.906 to
   0.620. All results below are on **unseen conversations**.
2. **Best model:** GradientBoosting - CCC **0.633** on unseen conversations.
3. **A new language costs 29%:** within-language CCC 0.556 vs cross-language 0.393.
4. **Voice travels, faces do not:** voice alone loses **12%** across languages,
   face features **55%**. Voice alone (0.652) even beats voice + face
   (0.631).

### All models - 3 session-disjoint folds (each holds out one conversation per language)

| Model | Family | CCC on unseen conversations | Old random-split CCC |
|---|---|---|---|
| GradientBoosting | classic ML | **0.633** ± 0.063 | 0.901 |
| RandomForest | classic ML | **0.631** ± 0.050 | 0.885 |
| XGBoost | classic ML | **0.620** ± 0.052 | 0.906 |
| ANN (MLP) | ANN | **0.591** ± 0.154 | 0.881 |
| Transformer | Transformer | **0.583** ± 0.038 | 0.826 |
| CNN_VGG | CNN | **0.577** ± 0.101 | 0.860 |
| Autoencoder + XGBoost | Autoencoder | **0.577** ± 0.092 |  |
| Autoencoder + dense head | Autoencoder | **0.564** ± 0.099 |  |
| GRU | RNN | **0.528** ± 0.166 |  |
| LSTM | RNN | **0.512** ± 0.219 | 0.849 |
| SimpleRNN | RNN | **0.510** ± 0.201 |  |
| LinearRegression | classic ML | **0.240** ± 0.286 | 0.284 |

### Ablation (XGBoost)

| Input | Features | Unseen conversations | Same language | Other language | Drop |
|---|---|---|---|---|---|
| voice | 88 | 0.652 | 0.596 | 0.522 | **12%** |
| face | 709 | 0.397 | 0.322 | 0.145 | **55%** |
| both | 797 | 0.631 | 0.571 | 0.451 | **21%** |

### Cross-lingual CCC (rows = train, columns = test)

| Train \ Test | English | French | German |
|---|---|---|---|
| **English** | 0.474 | 0.349 | 0.516 |
| **French** | 0.092 | 0.604 | 0.336 |
| **German** | 0.408 | 0.658 | 0.590 |

### Transfer learning (CNN pretrained on 2 languages, adapted on 1 conversation of the 3rd)

| Share of the adaptation conversation | Zero-shot | Head-only | Fine-tune | Scratch |
|---|---|---|---|---|
| 10% | 0.473 | 0.501 | 0.569 | 0.230 |
| 25% | 0.473 | 0.465 | 0.533 | 0.252 |
| 50% | 0.473 | 0.467 | 0.537 | 0.301 |
| 100% | 0.473 | 0.474 | 0.555 | 0.376 |

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
.venv\Scripts\activate
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
