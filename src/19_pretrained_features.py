"""
STEP 19: Pretrained Transformer features.
The NoXi zips also ship embeddings from large pretrained Transformers, computed
frame by frame by the dataset authors:
  xlm_roberta : XLM-RoBERTa (multilingual BERT family) on the speech transcript - TEXT
  w2vbert2    : w2v-BERT 2.0 (wav2vec2 + BERT style speech model) on the audio   - AUDIO
  clip        : CLIP image encoder on the video frames                            - FACE/VIDEO
  dino        : DINOv2 (self-supervised Vision Transformer) on the video frames   - FACE/VIDEO
  swin        : Swin Transformer on the video frames                              - FACE/VIDEO
  videomae    : VideoMAE (video Transformer) on short clips                       - FACE/VIDEO
They are at 25 frames per second like our eGeMAPS / OpenFace features, so we cut
them into exactly the same 1-second windows as step 2 and average each window.
Row i of every output matches row i of noxi_engagement.parquet.
Input:  NoXi zips + data/noxi/  ->  Output: data/features/pretrained_<name>.npy
Run: python src/19_pretrained_features.py "C:/Users/SHUBHAM KUMAR/Downloads/train.zip" "C:/Users/SHUBHAM KUMAR/Downloads/027.zip"
"""

import os
import sys
import zipfile
import warnings
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd

NOXI_ROOT = os.path.join("data", "noxi")
FEAT = os.path.join("data", "features", "noxi_engagement.parquet")
WINDOW = 25
EMB = {
    "xlm_roberta": "audio.xlm_roberta_embeddings",
    "w2vbert2": "audio.w2vbert2_embeddings",
    "clip": "clip",
    "dino": "dino",
    "swin": "swin",
    "videomae": "videomae",
}
warnings.filterwarnings("ignore", category=RuntimeWarning)   # nanmean of an all-NaN window


# same reader as step 2, for files already in data/noxi/
def read_stream(header_path):
    info = ET.parse(header_path).getroot().find("info")
    dim = int(info.get("dim"))
    data = np.fromfile(header_path + "~", dtype=np.float32)
    return data[: data.size // dim * dim].reshape(-1, dim)


# same idea, but read the header + binary straight out of a zip
def read_zip_stream(z, name):
    dim = int(ET.fromstring(z.read(name)).find("info").get("dim"))
    data = np.frombuffer(z.read(name + "~"), dtype=np.float32)
    return data[: data.size // dim * dim].reshape(-1, dim)


# which zip holds which session
index = {}
for zp in sys.argv[1:]:
    z = zipfile.ZipFile(zp)
    for n in z.namelist():
        if n.endswith(".clip.stream"):
            index[n.split("/")[-2]] = z
if not index:
    sys.exit("Pass the NoXi zip paths (train.zip, 027.zip).")

out = {k: [] for k in EMB}
eng_check = []
for sess in sorted(os.listdir(NOXI_ROOT)):
    folder, z = os.path.join(NOXI_ROOT, sess), index[sess]
    for role in ("expert", "novice"):
        eng_path = os.path.join(folder, f"{role}.engagement.annotation.csv")
        if not os.path.exists(eng_path):
            continue

        # rebuild the window list exactly as step 2 did
        ege = read_stream(os.path.join(folder, f"{role}.audio.egemapsv2.stream"))
        face = read_stream(os.path.join(folder, f"{role}.openface2.stream"))
        y = pd.to_numeric(pd.read_csv(eng_path, header=None).iloc[:, 0], errors="coerce").to_numpy("float32")
        T = min(len(ege), len(y), len(face))
        keep = [w for w in range(T // WINDOW) if not np.isnan(np.nanmean(y[w * WINDOW:(w + 1) * WINDOW]))]
        eng_check += [np.nanmean(y[w * WINDOW:(w + 1) * WINDOW]) for w in keep]

        # average every embedding over the same windows
        for k, stream in EMB.items():
            E = read_zip_stream(z, f"{sess}/{role}.{stream}.stream")
            win = np.stack([np.nanmean(E[w * WINDOW:(w + 1) * WINDOW], 0) if w * WINDOW < len(E)
                            else np.full(E.shape[1], np.nan, np.float32) for w in keep])
            out[k].append(np.nan_to_num(win, nan=0.0).astype(np.float32))
    print(f"  {sess} done", flush=True)

# check the rows line up with the main feature table (prints only True/False and counts)
ref = pd.read_parquet(FEAT, columns=["engagement"])["engagement"].to_numpy()
print(f"\nwindows {len(eng_check)} vs table {len(ref)} | labels match: "
      f"{len(eng_check) == len(ref) and np.allclose(eng_check, ref, atol=1e-5)}")
for k, parts in out.items():
    arr = np.concatenate(parts)
    np.save(os.path.join("data", "features", f"pretrained_{k}.npy"), arr)
    print(f"  {k:12s} {arr.shape}")
print("Saved -> data/features/pretrained_<name>.npy")
