# Cross-Lingual Prediction of Engagement from Non-Verbal Behaviour

Predicting how **engaged** a person is in a conversation (a score from 0 to 1) from **non-verbal behaviour only**
(voice and face, never the words), and testing whether a model trained on one language still works on another.

**Author:** Shubham Kumar (23CSU388), Department of Computer Science and Engineering, The NorthCap University, Gurugram

**Dataset:** [NoXi](https://multimediate.perceptualui.org/datasets/Dataset_NoXi/) - expert-novice conversations in
English, French and German (licensed, **not included** in this repository).
Paper: [Cafaro et al., ICMI 2017](https://eprints.nottingham.ac.uk/45827) - extension: [NoXi+J (arXiv)](https://arxiv.org/abs/2409.13726) -
data access: noxi@hcai.eu (if the dataset page is offline).

---

## Key results

| | |
|---|---|
| **Best model** | Gradient Boosting on eGeMAPS voice + w2v-BERT 2.0 + VideoMAE features with past context (last 5 s and 10 s) |
| **CCC on unseen conversations** | **0.777 ± 0.063** |
| **Drop on a new language** | **1%** |
| **Significance** | better than the baseline for 15 of 18 speakers, Holm-corrected p = 0.006 |
| **Unseen people** | 0.760 when no person is shared between training and test |

**Main findings**
1. **Random splits overstate performance.** Neighbouring seconds of one conversation land in both training and test
   (about 0.90 CCC). Holding out whole conversations gives about 0.62. All results below use unseen conversations.
2. **A new language costs 29%** on average (within-language 0.556 vs cross-language 0.393).
3. **Voice transfers across languages, face does not:** voice features lose 12%, OpenFace face features 55%.
4. **Past context helps most** (0.633 → 0.719); the partner's features do not raise accuracy.
5. **Pretrained Transformer features + Gradient Boosting work best** on this small dataset.

## Results (unseen conversations, 3 folds)

| Rank | Model | CCC | Language drop |
|---|---|---|---|
| 1 | Gradient Boosting: eGeMAPS + w2v-BERT 2.0 + VideoMAE + context | **0.777 ± 0.063** | 1% |
| 2 | Gradient Boosting: voice + face + context | 0.719 ± 0.009 | 0% |
| 3 | w2v-BERT 2.0 + VideoMAE (frozen) + dense head | 0.663 ± 0.020 | 5% |
| 4 | Own Transformer, 10 s of input | 0.637 ± 0.070 | 14% |
| 5 | Gradient Boosting (voice + face) | 0.633 ± 0.063 | 20% |
| 6 | Random Forest | 0.631 ± 0.050 | - |
| 7 | XGBoost | 0.620 ± 0.052 | - |
| 8 | ANN (MLP) | 0.591 ± 0.154 | - |
| 9 | Own Transformer, 1 s | 0.583 ± 0.038 | 34% |
| 10 | CNN (VGG style) | 0.577 ± 0.101 | - |
| 11 | Autoencoder + XGBoost / dense head | 0.577 / 0.564 | - |
| 12 | GRU / LSTM / SimpleRNN | 0.528 / 0.512 / 0.510 | - |
| 13 | Linear Regression | 0.240 ± 0.286 | - |

### Voice vs face (XGBoost)

| Input | Features | Unseen | Within language | Cross language | Drop |
|---|---|---|---|---|---|
| Voice (eGeMAPS) | 88 | 0.652 | 0.596 | 0.522 | **12%** |
| Face (OpenFace 2.0) | 709 | 0.397 | 0.322 | 0.145 | **55%** |
| Both | 797 | 0.631 | 0.571 | 0.451 | 21% |

### Pretrained Transformers (frozen, trained head)

| Model | Input | Best CCC | Drop |
|---|---|---|---|
| XLM-RoBERTa | text | 0.393 | 33% |
| w2v-BERT 2.0 | audio | 0.631 | **0%** |
| CLIP | video | 0.304 | 106% |
| DINOv2 | video | 0.485 | 58% |
| Swin | video | 0.449 | 41% |
| VideoMAE | video | 0.553 | 22% |
| w2v-BERT 2.0 + VideoMAE | audio + video | 0.663 | 5% |

### Cross-lingual CCC (Random Forest; rows = train, columns = test)

| Train \ Test | English | French | German |
|---|---|---|---|
| **English** | 0.474 | 0.349 | 0.516 |
| **French** | 0.092 | 0.604 | 0.336 |
| **German** | 0.408 | 0.658 | 0.590 |

All result tables are in `reports/` (CSV) and the full write-up is in `Project_Report_Final.pdf`.

---

## Repository

| Folder / file | Content |
|---|---|
| `src/` | The 27 steps of the project (`01_...py` to `27_...py`) and `splits.py` |
| `notebooks/` | One Jupyter notebook per step, each with the dataset information at the top |
| `reports/` | All result tables (CSV) and charts (`reports/figures/`) |
| `app.py` | Demo app: `streamlit run app.py` |
| `Project_Report_Final.pdf` | Full project report |
| `Research_Paper_Draft_v4.pdf` | Research paper (IEEE format) |
| `Results_Summary_9_Conversations.pdf` | All results in one document |
| `Literature_Review.xlsx` | Literature review (40 papers) |
| `Dataset_Description.docx`, `Laboratory_Manual.docx` | Dataset description and laboratory manual |
| `Project_Presentation.pptx`, `Research_Poster.pptx` | Presentation and poster |

## Pipeline (run from the project folder, in order)

| Step | What it does |
|---|---|
| 01 extract_data | Pull the needed files out of the NoXi zips |
| 02 build_features | 1-second windows: 17,174 rows x 797 features, plus 25-frame sequences |
| 03 eda | Exploratory analysis: statistics and charts |
| 04 baselines | ML baselines (random split, development) |
| 05 cross_lingual | Train on one language, test on another |
| 06-07 deep_learning, tuning | ANN and its tuning |
| 08-09 sequence_models, cnn | Sequence models; CNN and its tuning |
| 10 transfer_learning | CNN transfer learning across languages |
| 11 cnn_architectures | LeNet, VGG and ResNet styles |
| 12-13 transformer, lstm | Transformer encoder and LSTM (development) |
| 14 session_eval | **Final evaluation:** ML models + ANN on unseen conversations |
| 15 session_sequence | **Final evaluation:** CNN, SimpleRNN, LSTM, GRU, Transformer |
| 16 autoencoder | Autoencoder (797 → 32) + regression on the code |
| 17 ablation | Voice vs face vs both |
| 18 master_results | Master results table |
| 19 pretrained_features | Embeddings of six pretrained Transformers per window |
| 20 pretrained_transformers | Trained heads on the frozen pretrained Transformers |
| 21 smoothing | Smoothing predictions over 5 s |
| 22 partner | Adding the partner's features |
| 23 context | Adding the mean of the last 5 s and 10 s |
| 24 fusion | **Best model:** fusion + context |
| 25 transformer_context | Own Transformer with 10 s of input |
| 26 significance | Wilcoxon test per speaker, bootstrap intervals, Holm correction |
| 27 person_disjoint | Re-evaluation with no person shared between training and test |

Steps 04-13 are the development stage (random split); steps 14 onwards use whole held-out conversations.

## Setup

```bash
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Then download the NoXi data (see the links above) and run the scripts in `src/` or the notebooks in `notebooks/` in order.

## Data

| Property | Value |
|---|---|
| Source | NoXi (Novice-Expert Interaction) |
| Conversations used | 9 (3 English, 3 French, 3 German), 2 speakers each |
| Rows | 17,174 one-second windows |
| Features | 797: 88 voice (eGeMAPS) + 709 face (OpenFace 2.0); plus six pretrained Transformer embeddings |
| Target | Engagement, continuous 0-1 |
| Metric | CCC (Concordance Correlation Coefficient) |

The NoXi data is licensed under an End-User Licence Agreement and is **not** included in this repository.
