# Problem Statement

## Title
Cross-Lingual Analysis of Non-Verbal Behaviors in Human Conversations

## Motivation
Humans communicate a large part of meaning non-verbally — through facial
expressions, gaze, head movement, and vocal prosody. These signals are shaped
by language and culture. Understanding whether machine-learning models of
non-verbal behavior **generalize across languages** matters for building fair,
culturally-aware affective computing systems.

## Problem
Given short audio-visual clips of people speaking, we extract **non-verbal
features** (facial Action Units / emotions and vocal prosody) and ask:

1. How do non-verbal behaviors differ **across languages**? (EDA)
2. Can baseline ML models predict the expressed emotion from non-verbal
   features alone? (baselines)
3. Do models trained on one language **transfer** to another, or is non-verbal
   behavior language-specific? (cross-lingual experiment)

## Data
- **RAVDESS** — English, audio-visual, 8 emotions (pipeline development)
- **RML** — 6 languages (English, Mandarin, Urdu, Punjabi, Persian, Italian),
  audio-visual (cross-lingual comparison)

Both are free for academic use.

## Deliverables (this milestone)
- [ ] Problem statement + research questions (this doc)
- [ ] Dataset links
- [ ] EDA report
- [ ] Two baseline ML results
- [ ] GitHub repository
- [ ] Presentation

## Method (high-level)
| Stage | Tool |
|---|---|
| Facial features | py-feat |
| Vocal features | openSMILE (eGeMAPS) + librosa |
| EDA | ydata-profiling |
| Baselines | PyCaret `compare_models` |
| Cross-lingual | leave-one-language-out (scikit-learn) |

## Evaluation
Macro-F1 for within-language classification (baselines) and a
train-language × test-language transfer matrix for the cross-lingual analysis.
