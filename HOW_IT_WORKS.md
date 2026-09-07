# How This Project Works — Step by Step

**Project:** Cross-Lingual Engagement Prediction from Non-Verbal Behaviour
**Goal:** Predict how engaged a person is in a conversation (from face + voice, not words),
and test if it works across languages (French, English, German).

Run every script from the project root **with the venv active** (`.venv\Scripts\activate`).

---

## The 6 steps (in order)

### `src/01_extract_data.py` — Get the data ready
Takes the downloaded NoXi conversation zips and keeps only the files we need
(voice features, face features, engagement labels) — throwing away the huge videos.
- **Output:** `data/noxi/<session>/`
- **Run:** `python src/01_extract_data.py "C:/Users/SHUBHAM KUMAR/Downloads/train.zip"`

### `src/02_build_features.py` — Build the feature table
Lines up the voice + face features with the engagement label, and turns them into
one big table (each row = 1 second of behaviour).
- **Output:** `data/features/noxi_engagement.parquet` (17,174 rows)
- **Run:** `python src/02_build_features.py`

### `src/03_eda.py` — EDA (look at the data first)
Makes charts to understand the data BEFORE modeling: engagement distribution,
engagement by language, balance, and top features. Always do EDA before training.
- **Output:** `reports/figures/*.png` + `reports/eda_summary.csv`
- **Run:** `python src/03_eda.py`

### `src/04_baselines.py` — Baseline models
Trains simple models (Linear Regression, Random Forest, SVR) to predict engagement.
Reference score using the CCC metric.
- **Output:** baseline scores (RandomForest CCC ~0.89)
- **Run:** `python src/04_baselines.py`

### `src/05_cross_lingual.py` — The main experiment
Trains on one language and tests on another (e.g. French -> German) to see if
engagement transfers across languages. The project's key finding.
- **Output:** `reports/noxi_crosslingual_ccc.csv` (the 3x3 result matrix)
- **Run:** `python src/05_cross_lingual.py`

### `src/06_deep_learning.py` — Deep learning model
Trains a neural network (MLP) to predict engagement and compares it to the baselines.
Saves the trained model for the demo.
- **Output:** `reports/noxi_mlp.pt`, MLP CCC ~0.82
- **Run:** `python src/06_deep_learning.py`

---

## Results you can show
- `reports/eda_summary.csv` + `reports/figures/` — EDA charts
- `reports/noxi_crosslingual_ccc.csv` — cross-lingual matrix (main finding)
- `reports/noxi_mlp.pt` — trained deep learning model

## Key finding
Within a language, engagement is predictable; across languages it drops — so
engagement is partly language-specific, not universal.

## How to explain it in one minute
"My project predicts how engaged someone is in a conversation, using only their
face and voice — not their words. Step 1 gets the data, step 2 builds features,
step 3 is EDA (looking at the data), step 4 runs baseline models, step 5 is the
main experiment (train on one language, test on another), and step 6 is the deep
learning model. My finding is that engagement is partly language-specific."
