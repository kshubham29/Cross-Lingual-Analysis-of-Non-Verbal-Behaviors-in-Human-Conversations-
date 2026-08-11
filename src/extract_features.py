"""
Step 1: turn raw audio-visual clips into ONE feature table.

Put clips under:   data/raw/<language>/*.mp4
  e.g. data/raw/English/03-01-05-...-12.mp4   (RAVDESS)
       data/raw/Italian/it_sample_01.mp4      (RML, etc.)

For each clip we extract:
  - vocal features  : openSMILE eGeMAPS (88 prosodic) + librosa MFCC
  - facial features : py-feat Action Units + emotions (aggregated over frames)
and tag it with `language` (folder name) and `label` (emotion).

Output: data/features/features.parquet
"""

import os
import glob
import tempfile

import numpy as np
import pandas as pd
from tqdm import tqdm

# ----- high-level extractors -----
import librosa
import opensmile
from feat import Detector
from moviepy.editor import VideoFileClip

RAW_DIR = os.path.join("data", "raw")
OUT_DIR = os.path.join("data", "features")
os.makedirs(OUT_DIR, exist_ok=True)

# RAVDESS emotion code (position 3 of the filename) -> label
RAVDESS_EMOTION = {
    "01": "neutral", "02": "calm", "03": "happy", "04": "sad",
    "05": "angry", "06": "fearful", "07": "disgust", "08": "surprised",
}

smile = opensmile.Smile(
    feature_set=opensmile.FeatureSet.eGeMAPSv02,
    feature_level=opensmile.FeatureLevel.Functionals,
)
detector = Detector()  # loads AU + emotion + pose models once


def label_from_filename(path):
    """RAVDESS filenames encode the emotion; fall back to 'unknown' otherwise."""
    name = os.path.splitext(os.path.basename(path))[0]
    parts = name.split("-")
    if len(parts) == 7 and parts[2] in RAVDESS_EMOTION:
        return RAVDESS_EMOTION[parts[2]]
    return "unknown"


def audio_features(wav_path):
    feats = smile.process_file(wav_path).iloc[0].to_dict()
    y, sr = librosa.load(wav_path, sr=16000)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13).mean(axis=1)
    feats.update({f"mfcc_{i}": float(v) for i, v in enumerate(mfcc)})
    return feats


def face_features(video_path):
    fex = detector.detect_video(video_path, skip_frames=5)  # every 5th frame = faster
    aus = fex.aus.mean().to_dict()          # Action Unit intensities
    emos = fex.emotions.mean().to_dict()    # 7 emotion probabilities
    feats = {f"face_au_{k}": float(v) for k, v in aus.items()}
    feats.update({f"face_emo_{k}": float(v) for k, v in emos.items()})
    return feats


def extract_one(video_path):
    row = {}
    # pull audio out of the mp4 into a temp wav
    with tempfile.TemporaryDirectory() as td:
        wav = os.path.join(td, "a.wav")
        try:
            VideoFileClip(video_path).audio.write_audiofile(wav, logger=None)
            row.update(audio_features(wav))
        except Exception as e:
            print(f"  [audio skip] {video_path}: {e}")
    try:
        row.update(face_features(video_path))
    except Exception as e:
        print(f"  [face skip] {video_path}: {e}")
    return row


def language_of(path):
    """First folder under data/raw/ is the language, even if clips sit in
    deeper actor subfolders (e.g. data/raw/English/Actor_01/xx.mp4)."""
    rel = os.path.relpath(path, RAW_DIR)
    return rel.split(os.sep)[0]


def main():
    # ** = recurse into actor subfolders unzipped from RAVDESS
    clips = glob.glob(os.path.join(RAW_DIR, "**", "*.mp4"), recursive=True)
    # keep only audio-visual (RAVDESS modality code 01), skip video-only (02)
    clips = [c for c in clips if not os.path.basename(c).startswith("02-")]
    if not clips:
        print(f"No clips found under {RAW_DIR}/<language>/ — add data first.")
        return

    rows = []
    for path in tqdm(clips, desc="Extracting"):
        language = language_of(path)
        row = extract_one(path)
        if not row:
            continue
        row["language"] = language
        row["label"] = label_from_filename(path)
        row["clip"] = os.path.basename(path)
        rows.append(row)

    df = pd.DataFrame(rows)
    out = os.path.join(OUT_DIR, "features.parquet")
    df.to_parquet(out, index=False)
    print(f"\nSaved {len(df)} rows x {df.shape[1]} cols -> {out}")
    print("Languages:", df['language'].value_counts().to_dict())
    print("Labels   :", df['label'].value_counts().to_dict())


if __name__ == "__main__":
    main()
