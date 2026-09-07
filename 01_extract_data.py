"""
STEP 1: Get the data ready.
Opens the big NoXi zips and keeps only the small files we need
(voice features, face features, engagement labels, language).
Input: NoXi zips  ->  Output: data/noxi/<session>/
Run: python src/01_extract_data.py "C:/Users/SHUBHAM KUMAR/Downloads/train.zip"
"""

# ---------------------------------------------------------------------------
# BLOCK 1 - IMPORTS
# os/glob handle file paths, sys reads the command-line argument (the zip path),
# and zipfile lets us open the downloaded NoXi archives.
# ---------------------------------------------------------------------------
import os
import sys
import glob
import zipfile

# ---------------------------------------------------------------------------
# BLOCK 2 - WHAT TO KEEP
# A NoXi session zip is about 1.2 GB, but most of that is raw video and large
# deep-learning embeddings we never use. This list names the only file types we
# keep: the voice features, the face features, the engagement labels and the
# language tag. Everything else is skipped, saving roughly 90% of the space.
# ---------------------------------------------------------------------------
DEST = os.path.join("data", "noxi")

KEEP_SUFFIXES = (
    ".audio.egemapsv2.stream", ".audio.egemapsv2.stream~",   # voice features
    ".openface2.stream", ".openface2.stream~",               # face features
    ".engagement.annotation.csv",                            # the labels
    "language.annotation.csv",                               # the language
)


# ---------------------------------------------------------------------------
# BLOCK 3 - HELPER: IS THIS FILE WANTED?
# Returns True only for the file types listed above.
# ---------------------------------------------------------------------------
def wanted(name):
    return name.endswith(KEEP_SUFFIXES)


# ---------------------------------------------------------------------------
# BLOCK 4 - EXTRACT FROM ONE ZIP
# Open a zip, look at every file inside it, and pull out only the wanted ones
# into data/noxi/. Folders are skipped.
# ---------------------------------------------------------------------------
def process_zip(zip_path):
    kept = 0
    with zipfile.ZipFile(zip_path) as z:
        for member in z.namelist():
            if member.endswith("/"):
                continue
            if wanted(os.path.basename(member)) or wanted(member):
                z.extract(member, DEST)
                kept += 1
    print(f"  {os.path.basename(zip_path)} -> kept {kept} files")


# ---------------------------------------------------------------------------
# BLOCK 5 - MAIN
# Work out which zips to process. You can pass exact zip paths, or a folder -
# in which case we look for NoXi-looking zips (numbered ones like 027.zip, or
# train.zip). Then extract from each in turn.
# ---------------------------------------------------------------------------
def main():
    args = sys.argv[1:] or ["."]
    zips = []
    for a in args:
        if a.lower().endswith(".zip"):
            zips.append(a)
        else:
            for z in glob.glob(os.path.join(a, "*.zip")):
                base = os.path.splitext(os.path.basename(z))[0]
                if base.isdigit() or base == "train":
                    zips.append(z)
    if not zips:
        print("No session zips found. Pass a folder or zip paths.")
        return

    os.makedirs(DEST, exist_ok=True)
    print(f"Extracting needed files from {len(zips)} zip(s) -> {DEST}/")
    for z in sorted(zips):
        process_zip(z)
    print("\nDone. Next: python src/02_build_features.py")


if __name__ == "__main__":
    main()
