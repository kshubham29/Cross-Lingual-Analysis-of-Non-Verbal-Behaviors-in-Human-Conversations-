"""
Engagement demo (Streamlit) - the AI prototype.
Pick a conversation and a speaker. The XGBoost model that NEVER saw that
conversation (saved by step 14) predicts engagement second by second from
voice + face only, and the chart compares it with the real annotation.
Run:   streamlit run app.py
Needs: data/features/noxi_engagement.parquet + reports/xgb_fold{1,2,3}.joblib
"""

import os
import joblib
import numpy as np
import pandas as pd
import streamlit as st
from sklearn.base import clone
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

FEAT = os.path.join("data", "features", "noxi_engagement.parquet")
R = "reports"
MODELS = [os.path.join(R, f"xgb_fold{k}.joblib") for k in (1, 2, 3)]


# metric: 1.0 = perfect
def ccc(yt, yp):
    yt, yp = np.asarray(yt), np.asarray(yp)
    cov = ((yt - yt.mean()) * (yp - yp.mean())).mean()
    return (2 * cov) / (yt.var() + yp.var() + (yt.mean() - yp.mean()) ** 2 + 1e-9)


@st.cache_data
def load_data():
    return pd.read_parquet(FEAT)


@st.cache_resource
def load_models():
    return [joblib.load(p) for p in MODELS]


# voice-only / face-only model for one fold: same XGBoost as step 14, trained on
# the same 6 training conversations, only the input columns change
@st.cache_resource
def modality_model(fold, modality):
    m = load_models()[fold]
    cols = [c for c in m["cols"] if c.startswith(modality)]
    tr = df[~df.session.isin(m["test_sessions"])]
    pipe = make_pipeline(StandardScaler(), clone(m["pipe"][-1]))
    pipe.fit(tr[cols].fillna(0).to_numpy("float32"), tr["engagement"])
    return pipe, cols


st.set_page_config(page_title="Engagement Demo", layout="wide")
st.title("Engagement from non-verbal behaviour")
st.caption("Voice (eGeMAPS) + face (OpenFace) only - no words. NoXi conversations in English, French and German.")

if not all(os.path.exists(p) for p in MODELS):
    st.error("Trained models not found - run `python src/14_session_eval.py` first.")
    st.stop()
df = load_data()
models = load_models()

tab_live, tab_results = st.tabs(["Live prediction", "Results"])


# ---------- tab 1: predict one conversation ----------
with tab_live:
    sessions = df[["language", "session"]].drop_duplicates().sort_values(["language", "session"])
    label = {s: f"{l} - session {s}" for l, s in sessions.values}
    c1, c2, c3, c4 = st.columns(4)
    s = c1.selectbox("Conversation", list(label), format_func=label.get)
    role = c2.radio("Speaker", ["expert", "novice"], horizontal=True)
    modality = c3.radio("Input", ["voice + face", "voice", "face"], horizontal=True)
    smooth = c4.slider("Smoothing (seconds)", 1, 15, 5)

    # use the model whose test fold contains this conversation, so it is truly unseen
    clip = df[(df.session == s) & (df.role == role)]
    fold = next(k for k, m in enumerate(models) if s in m["test_sessions"])
    if modality == "voice + face":
        pipe, cols = models[fold]["pipe"], models[fold]["cols"]
    else:
        with st.spinner(f"Training the {modality}-only model on the other 6 conversations..."):
            pipe, cols = modality_model(fold, modality)
    real = clip["engagement"].to_numpy()
    pred = pipe.predict(clip[cols].fillna(0).to_numpy("float32"))

    chart = pd.DataFrame({"actual": real, "predicted": pred},
                         index=pd.RangeIndex(len(real), name="second"))
    st.line_chart(chart.rolling(smooth, min_periods=1).mean(), color=["#3f6b35", "#d08a2e"],
                  x_label="time (seconds)", y_label="engagement (0-1)")

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("CCC", f"{ccc(real, pred):.3f}")
    k2.metric("Pearson", f"{np.corrcoef(real, pred)[0, 1]:.3f}")
    k3.metric("Mean actual", f"{real.mean():.3f}")
    k4.metric("Mean predicted", f"{pred.mean():.3f}")
    st.info(f"{len(real)} seconds. This conversation was held out - the model was trained on "
            f"the other 6 conversations and never saw it.")


# ---------- tab 2: saved experiment results ----------
with tab_results:
    tables = [("master_results.csv", "All models - unseen conversations (3 session-wise folds)"),
              ("pretrained_results.csv", "Pretrained Transformers (frozen) + trained head - unseen conversations"),
              ("ablation_results.csv", "Ablation - voice vs face vs both"),
              ("noxi_crosslingual_ccc.csv", "Cross-lingual CCC (row = train language, column = test language)")]
    for f, title in tables:
        p = os.path.join(R, f)
        if os.path.exists(p):
            st.subheader(title)
            st.dataframe(pd.read_csv(p).rename(columns={"Unnamed: 0": "train language"}).round(3),
                         hide_index=True)

    p = os.path.join(R, "transfer_results.csv")
    if os.path.exists(p):
        t = pd.read_csv(p)
        if "fraction" in t.columns:
            st.subheader("Transfer learning - CCC vs share of one new-language conversation used")
            st.dataframe(t.groupby("fraction")[["zero_shot", "head_only", "fine_tune", "scratch"]]
                         .mean().round(3))

    p = os.path.join(R, "figures", "master_ccc.png")
    if os.path.exists(p):
        st.image(p, width=700)
