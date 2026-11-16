"""
STEP 2: Build the feature table.
For each conversation, line up the voice + face features with the engagement
score, cut into 1-second windows, and average each window into one row.
Input: data/noxi/  ->  Output: data/features/noxi_engagement.parquet
"""

# ---------------------------------------------------------------------------
# BLOCK 1 - IMPORTS AND SETTINGS
# ElementTree reads the small XML header files that describe each feature
# stream. WINDOW = 25 because NoXi records 25 frames per second, so 25 frames
# is exactly one second of behaviour.
# ---------------------------------------------------------------------------
import os
import glob
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd

NOXI_ROOT = os.path.join("data", "noxi")
OUT = os.path.join("data", "features", "noxi_engagement.parquet")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

WINDOW = 25   # 25 frames = 1 second


# ---------------------------------------------------------------------------
# BLOCK 2 - READ A FEATURE STREAM
# NoXi stores features in two files: a small text header (.stream) saying how
# many numbers there are per frame, and a binary file (.stream~) holding the
# actual numbers. We read the header to learn the shape, then read the binary
# and reshape it into a table of (frames x features).
# ---------------------------------------------------------------------------
def read_stream(header_path):
    info = ET.parse(header_path).getroot().find("info")
    dim = int(info.get("dim"))
    dtype = {"FLOAT": np.float32, "DOUBLE": np.float64}[info.get("type")]
    data = np.fromfile(header_path + "~", dtype=dtype)
    n = data.size // dim
    return data[: n * dim].reshape(n, dim)


# ---------------------------------------------------------------------------
# BLOCK 3 - READ THE ENGAGEMENT LABEL
# One engagement value per frame. Any invalid or missing entry becomes NaN so
# it can be skipped later instead of crashing the script.
# ---------------------------------------------------------------------------
def read_engagement(csv_path):
    s = pd.read_csv(csv_path, header=None).iloc[:, 0]
    return pd.to_numeric(s, errors="coerce").to_numpy(dtype="float32")


# ---------------------------------------------------------------------------
# BLOCK 4 - READ THE LANGUAGE
# The file looks like: start;end;LANGUAGE;confidence - we take the third field.
# ---------------------------------------------------------------------------
def read_language(folder):
    p = os.path.join(folder, "language.annotation.csv")
    if os.path.exists(p):
        return open(p).read().strip().split(";")[2]
    return "unknown"


def build():
    rows = []

    # -----------------------------------------------------------------------
    # BLOCK 5 - FIND THE CONVERSATIONS
    # Each folder under data/noxi/ is one recorded session.
    # -----------------------------------------------------------------------
    sessions = sorted(d for d in glob.glob(os.path.join(NOXI_ROOT, "*")) if os.path.isdir(d))
    if not sessions:
        print(f"No session folders under {NOXI_ROOT}/ — run step 1 first.")
        return

    for folder in sessions:
        sess = os.path.basename(folder)
        lang = read_language(folder)

        # -------------------------------------------------------------------
        # BLOCK 6 - LOOP OVER BOTH PEOPLE
        # Every NoXi session has two participants: an expert and a novice.
        # Each has their own voice features, face features and engagement.
        # -------------------------------------------------------------------
        for role in ("expert", "novice"):
            eng_path = os.path.join(folder, f"{role}.engagement.annotation.csv")
            ege_path = os.path.join(folder, f"{role}.audio.egemapsv2.stream")
            face_path = os.path.join(folder, f"{role}.openface2.stream")
            if not (os.path.exists(eng_path) and os.path.exists(ege_path)):
                continue

            # ---------------------------------------------------------------
            # BLOCK 7 - LOAD AND ALIGN
            # Read voice, face and engagement, then trim all three to the
            # shortest length. They can differ by a frame or two, and they must
            # line up exactly for each row to be correct.
            # ---------------------------------------------------------------
            ege = read_stream(ege_path)
            face = read_stream(face_path) if os.path.exists(face_path) else None
            y = read_engagement(eng_path)
            T = min(len(ege), len(y), len(face) if face is not None else len(y))
            ege, y = ege[:T], y[:T]
            if face is not None:
                face = face[:T]

            # ---------------------------------------------------------------
            # BLOCK 8 - CUT INTO 1-SECOND WINDOWS
            # The raw data at 25 Hz is too fine-grained and noisy. We group each
            # 25 frames into one window, average the features over it, and take
            # the average engagement as that window's label. Each window becomes
            # one row of the final table. Windows with no valid label are skipped.
            # ---------------------------------------------------------------
            for w in range(T // WINDOW):
                s = slice(w * WINDOW, (w + 1) * WINDOW)
                eng = float(np.nanmean(y[s]))
                if np.isnan(eng):
                    continue
                feat = {f"voice_{i}": float(v) for i, v in enumerate(np.nanmean(ege[s], 0))}
                if face is not None:
                    feat.update({f"face_{i}": float(v) for i, v in enumerate(np.nanmean(face[s], 0))})
                # tag each row so we know which language/session/person it came from
                feat.update(engagement=eng, language=lang, session=sess, role=role)
                rows.append(feat)
        print(f"  {sess} ({lang}) done")

    # -----------------------------------------------------------------------
    # BLOCK 9 - SAVE THE TABLE
    # Turn all the rows into one table and save it. Parquet is a compact, fast
    # format for large tables. Then print a summary per language.
    # -----------------------------------------------------------------------
    df = pd.DataFrame(rows)
    df.to_parquet(OUT, index=False)
    print(f"\nSaved {len(df)} windows x {df.shape[1]} cols -> {OUT}")
    print("Per language:\n", df.groupby("language").agg(
        windows=("engagement", "size"), mean_engagement=("engagement", "mean")))


if __name__ == "__main__":
    build()
