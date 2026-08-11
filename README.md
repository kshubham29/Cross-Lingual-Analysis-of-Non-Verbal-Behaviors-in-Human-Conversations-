# Cross-Lingual Analysis of Non-Verbal Behaviors in Human Conversations

Deep Learning semester project. This milestone covers: dataset selection, EDA,
and two baseline ML models — with a cross-lingual comparison of non-verbal
(facial + vocal) behavior.

## Idea
Extract **non-verbal features** from short audio-visual clips:
- **Vocal / paralinguistic** (openSMILE eGeMAPS + librosa): pitch, loudness, jitter, MFCC
- **Facial** (py-feat): Action Units, emotions, gaze, head pose

Tag each clip with its `language` and `label` (emotion), stack into one table, then:
1. Run automatic EDA (ydata-profiling)
2. Train baseline models (PyCaret `compare_models`)
3. **Cross-lingual test**: train on one language, test on another

## Datasets (both free)
| Dataset | Languages | Modality | Link |
|---|---|---|---|
| RAVDESS | English | audio + video | https://zenodo.org/records/1188976 |
| RML | English, Mandarin, Urdu, Punjabi, Persian, Italian | audio + video | RML Emotion Database (academic) |

Download and place the raw clips under `data/raw/<language>/`.

## Pipeline
```bash
pip install -r requirements.txt

python src/extract_features.py      # 1. clips -> data/features/features.parquet
python src/eda.py                   # 2. -> reports/eda_report.html + figures
python src/train_baselines.py       # 3. baseline leaderboard -> reports/
python src/cross_lingual.py         # 4. train lang A -> test lang B
```

## Folder layout
```
cross-lingual-nonverbal/
├── data/
│   ├── raw/         # <language>/*.mp4  (git-ignored)
│   └── features/    # features.parquet
├── src/
│   ├── extract_features.py
│   ├── eda.py
│   ├── train_baselines.py
│   └── cross_lingual.py
├── reports/         # eda_report.html, results, figures
├── docs/
│   └── problem_statement.md
├── requirements.txt
└── README.md
```
