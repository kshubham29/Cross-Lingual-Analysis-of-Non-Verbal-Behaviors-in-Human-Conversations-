"""Build the Literature Review Excel sheet."""
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Literature Review"

COLS = [
    "S.no.", "DOI", "Title/Paper Name", "APA Ref (Google Scholar Cite)", "Authors",
    "Year", "Journal/Venue", "Indexing (Scopus/WoS)", "Objectives of Paper",
    "Dataset(s) Used", "Sample Size", "Modality (text/signal/image/video)",
    "Input Type", "Features", "Methodology/Model/Architecture", "Evaluation Metric",
    "Outcome", "Research Gap", "Future Scope", "Paper Link",
    "Other Links (Dataset/GitHub/PMC)", "Google Drive Link (PDF)",
    "Name/Roll No. of Reader", "Remarks (your own insights)",
]

# ---- header ----
navy = PatternFill("solid", fgColor="1E2C3F")
hfont = Font(name="Arial", bold=True, color="FFFFFF", size=10)
thin = Side(style="thin", color="BBBBBB")
border = Border(left=thin, right=thin, top=thin, bottom=thin)
for j, name in enumerate(COLS, 1):
    c = ws.cell(row=1, column=j, value=name)
    c.fill = navy; c.font = hfont; c.border = border
    c.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")

# ---- paper rows ----
# fields per paper matched to COLS order (S.no filled automatically)
P = [
 dict(doi="10.1145/3136755.3136780", title="The NoXi Database: Multimodal Recordings of Mediated Novice-Expert Interactions",
   apa="Cafaro, A., et al. (2017). The NoXi database. Proceedings of ICMI, 350-359.",
   authors="Cafaro, Wagner, Baur, Dermouche, Torres, Pelachaud, Andre, Valstar", year=2017,
   venue="ACM ICMI", index="Scopus",
   obj="Introduce a multilingual multimodal corpus of dyadic novice-expert conversations for non-verbal behaviour research.",
   data="NoXi (own)", n="~84 sessions, 7 languages", modality="video + audio",
   inp="Audio-visual recordings", feat="Gestures, smiles, gaze, turn-taking, engagement annotations",
   method="Database creation + annotation protocol", metric="N/A (dataset paper)",
   out="Released a rich multilingual corpus with continuous non-verbal annotations.",
   gap="Prior corpora were mostly single-language and acted.",
   fut="Use for engagement/interest modelling across languages.",
   link="https://dl.acm.org/doi/10.1145/3136755.3136780",
   other="https://multimediate-challenge.org/datasets/Dataset_NoXi/"),
 dict(doi="10.1145/3664647.3689004 (arXiv:2408.16625)", title="MultiMediate'24: Multi-Domain Engagement Estimation",
   apa="Muller, P., et al. (2024). MultiMediate'24: Multi-Domain Engagement Estimation. ACM Multimedia.",
   authors="Muller, Balazia, et al.", year=2024, venue="ACM Multimedia", index="Scopus",
   obj="Benchmark engagement estimation and its generalisation across language, culture and setting.",
   data="NoXi, MPIIGroupInteraction", n="Challenge sets", modality="video + audio",
   inp="Multimodal features", feat="Audio + visual behaviour features",
   method="Transformer / attention-based fusion", metric="CCC",
   out="Showed engagement models struggle to generalise across domains/cultures.",
   gap="Cross-domain / cross-cultural engagement generalisation is unsolved.",
   fut="Domain adaptation for engagement across cultures.",
   link="https://arxiv.org/abs/2408.16625", other=""),
 dict(doi="arXiv:2409.13726", title="Multilingual Dyadic Interaction Corpus NoXi+J",
   apa="Okada, S., et al. (2024). Multilingual Dyadic Interaction Corpus NoXi+J. arXiv:2409.13726.",
   authors="Okada, et al.", year=2024, venue="arXiv / LREC", index="Not indexed (preprint)",
   obj="Extend NoXi with Japanese and Chinese to study Asian-European non-verbal differences.",
   data="NoXi+J", n="+66 sessions (JP/ZH)", modality="video + audio",
   inp="Audio-visual", feat="Non-verbal cues + engagement",
   method="Cross-cultural analysis", metric="Correlation / CCC",
   out="Found cultural differences in non-verbal behaviour and engagement.",
   gap="Asian-European non-verbal differences under-studied.",
   fut="Broader cross-cultural engagement modelling.",
   link="https://arxiv.org/abs/2409.13726", other=""),
 dict(doi="10.1109/TAFFC.2015.2457417", title="The Geneva Minimalistic Acoustic Parameter Set (eGeMAPS)",
   apa="Eyben, F., et al. (2016). The Geneva Minimalistic Acoustic Parameter Set (eGeMAPS). IEEE TAC, 7(2), 190-202.",
   authors="Eyben, Scherer, Schuller, et al.", year=2016, venue="IEEE Trans. Affective Computing", index="Scopus + WoS",
   obj="Define a compact standard acoustic feature set for affective computing.",
   data="Multiple emotion corpora", n="Varies", modality="signal (audio)",
   inp="Speech audio", feat="88 prosodic/voice-quality features (pitch, loudness, jitter, shimmer)",
   method="Expert-designed feature set", metric="Recognition accuracy",
   out="Provided the widely-used eGeMAPS feature set.",
   gap="Feature sets were large and inconsistent across studies.",
   fut="Standard features for affect/engagement tasks.",
   link="https://doi.org/10.1109/TAFFC.2015.2457417", other=""),
 dict(doi="10.1109/FG.2018.00019", title="OpenFace 2.0: Facial Behavior Analysis Toolkit",
   apa="Baltrusaitis, T., et al. (2018). OpenFace 2.0. IEEE FG.",
   authors="Baltrusaitis, Zadeh, Lim, Morency", year=2018, venue="IEEE FG", index="Scopus",
   obj="Provide an open toolkit for facial behaviour analysis.",
   data="Various face datasets", n="Varies", modality="image/video",
   inp="Face video", feat="Facial Action Units, gaze, head pose, landmarks",
   method="CNN-based facial analysis toolkit", metric="AU detection accuracy",
   out="Open toolkit extracting facial features (used for our face features).",
   gap="No accessible real-time facial behaviour tool.",
   fut="Non-verbal facial features for affect/engagement.",
   link="https://doi.org/10.1109/FG.2018.00019",
   other="https://github.com/TadasBaltrusaitis/OpenFace"),
 dict(doi="10.1109/T-AFFC.2010.8", title="Cross-Corpus Acoustic Emotion Recognition: Variances and Strategies",
   apa="Schuller, B., et al. (2010). Cross-Corpus Acoustic Emotion Recognition. IEEE TAC, 1(2), 119-131.",
   authors="Schuller, Vlasenko, Eyben, et al.", year=2010, venue="IEEE Trans. Affective Computing", index="Scopus + WoS",
   obj="Study how emotion models transfer between different corpora.",
   data="6 emotion corpora", n="Multiple", modality="signal (audio)",
   inp="Speech", feat="Acoustic features", method="SVM cross-corpus experiments", metric="Recognition rate",
   out="Large performance drops when models are used on other corpora.",
   gap="Models do not generalise across corpora/conditions.",
   fut="Normalisation and adaptation strategies.",
   link="https://doi.org/10.1109/T-AFFC.2010.8", other=""),
 dict(doi="10.1109/ACII.2015.7344561", title="Cross-Language Acoustic Emotion Recognition: An Overview and Some Tendencies",
   apa="Feraru, S. M., Schuller, D., & Schuller, B. (2015). Cross-Language Acoustic Emotion Recognition. ACII.",
   authors="Feraru, Schuller, Schuller", year=2015, venue="IEEE ACII", index="Scopus",
   obj="Survey how emotion recognition transfers across languages.",
   data="Multiple language emotion corpora", n="Multiple", modality="signal (audio)",
   inp="Speech", feat="Acoustic features", method="Cross-language recognition experiments", metric="Accuracy / UAR",
   out="Recognition degrades across languages, worse for distant language families.",
   gap="Cross-language emotion transfer is limited.",
   fut="Language-robust emotion models.",
   link="https://doi.org/10.1109/ACII.2015.7344561", other=""),
 dict(doi="arXiv:1609.01885", title="DAiSEE: Towards User Engagement Recognition in the Wild",
   apa="Gupta, A., et al. (2016). DAiSEE: Towards User Engagement Recognition in the Wild. arXiv:1609.01885.",
   authors="Gupta, D'Cunha, Awasthi, Balasubramanian", year=2016, venue="arXiv", index="Not indexed (preprint)",
   obj="Introduce a dataset for engagement/affect recognition in e-learning.",
   data="DAiSEE", n="9,068 video snippets, 112 users", modality="video",
   inp="Face video", feat="Facial behaviour", method="CNN/LSTM baselines", metric="Accuracy",
   out="Released engagement dataset with deep-learning baselines.",
   gap="Few engagement datasets in real-world settings.",
   fut="Better engagement recognition models.",
   link="https://arxiv.org/abs/1609.01885", other=""),
 dict(doi="10.1007/s10579-008-9076-6", title="IEMOCAP: Interactive Emotional Dyadic Motion Capture Database",
   apa="Busso, C., et al. (2008). IEMOCAP. Language Resources and Evaluation, 42(4), 335-359.",
   authors="Busso, Bulut, Lee, et al.", year=2008, venue="Language Resources and Evaluation", index="Scopus + WoS",
   obj="Provide a multimodal dyadic emotional interaction database.",
   data="IEMOCAP (own)", n="~12 hours, 10 actors", modality="audio + video + text + mocap",
   inp="Audio-visual dyadic interaction", feat="Speech, facial mocap, text",
   method="Database + annotation", metric="N/A (dataset)",
   out="Standard multimodal emotion benchmark.",
   gap="Lack of multimodal dyadic emotional data.",
   fut="Multimodal emotion/engagement modelling.",
   link="https://sail.usc.edu/iemocap/", other="https://doi.org/10.1007/s10579-008-9076-6"),
 dict(doi="10.1109/TPAMI.2018.2798607 (arXiv:1705.09406)", title="Multimodal Machine Learning: A Survey and Taxonomy",
   apa="Baltrusaitis, T., Ahuja, C., & Morency, L.-P. (2019). Multimodal Machine Learning: A Survey and Taxonomy. IEEE TPAMI, 41(2), 423-443.",
   authors="Baltrusaitis, Ahuja, Morency", year=2019, venue="IEEE TPAMI", index="Scopus + WoS",
   obj="Survey and organise multimodal machine-learning methods.",
   data="Review (many)", n="N/A", modality="multi (text/audio/video)",
   inp="Multimodal", feat="Various", method="Survey/taxonomy (fusion, alignment...)", metric="N/A",
   out="Taxonomy of multimodal learning challenges and fusion methods.",
   gap="Fragmented multimodal learning literature.",
   fut="Better fusion and cross-modal methods.",
   link="https://arxiv.org/abs/1705.09406", other=""),
 dict(doi="10.1145/1873951.1874246", title="openSMILE: The Munich Versatile and Fast Open-Source Audio Feature Extractor",
   apa="Eyben, F., Wollmer, M., & Schuller, B. (2010). openSMILE. ACM Multimedia, 1459-1462.",
   authors="Eyben, Wollmer, Schuller", year=2010, venue="ACM Multimedia", index="Scopus",
   obj="Provide an open, fast audio feature extraction toolkit.",
   data="N/A (tool)", n="N/A", modality="signal (audio)",
   inp="Audio", feat="Prosodic/spectral acoustic features", method="Feature extraction toolkit", metric="N/A",
   out="Widely-used tool (used to extract our eGeMAPS features).",
   gap="No standard fast audio feature extractor.",
   fut="Standard acoustic features for affect tasks.",
   link="https://doi.org/10.1145/1873951.1874246", other="https://www.audeering.com/research/opensmile/"),
 dict(doi="10.18653/v1/P19-1050", title="MELD: A Multimodal Multi-Party Dataset for Emotion Recognition in Conversations",
   apa="Poria, S., et al. (2019). MELD. Proceedings of ACL.",
   authors="Poria, Hazarika, Majumder, et al.", year=2019, venue="ACL", index="Scopus",
   obj="Provide a multimodal multi-party conversational emotion dataset.",
   data="MELD (own)", n="~13,000 utterances", modality="audio + video + text",
   inp="Conversation clips", feat="Audio, visual, text", method="Dataset + RNN baselines", metric="F1",
   out="Multimodal conversational emotion benchmark.",
   gap="Few multi-party conversational emotion datasets.",
   fut="Context-aware multimodal emotion models.",
   link="https://aclanthology.org/P19-1050/", other="https://affective-meld.github.io/"),
 dict(doi="10.1016/j.learninstruc.2011.10.001", title="Dynamics of Affective States during Complex Learning",
   apa="D'Mello, S., & Graesser, A. (2012). Dynamics of Affective States during Complex Learning. Learning and Instruction, 22(2), 145-157.",
   authors="D'Mello, Graesser", year=2012, venue="Learning and Instruction", index="Scopus + WoS",
   obj="Model how engagement/boredom/confusion evolve during learning.",
   data="Learning session data", n="Study participants", modality="signal/behaviour",
   inp="Behaviour + interaction", feat="Affective state transitions", method="Statistical dynamics model", metric="Transition likelihoods",
   out="Showed affective states (incl. engagement) evolve over time.",
   gap="Limited understanding of affect dynamics.",
   fut="Real-time affect-aware systems.",
   link="https://doi.org/10.1016/j.learninstruc.2011.10.001", other=""),
 dict(doi="10.1002/widm.1563", title="Multimodal Emotion Recognition: A Comprehensive Review, Trends, and Challenges",
   apa="Ramaswamy, M. P. A., & Palaniswamy, S. (2024). Multimodal Emotion Recognition: A Comprehensive Review. WIREs DMKD.",
   authors="Ramaswamy, Palaniswamy", year=2024, venue="WIREs Data Mining & Knowledge Discovery", index="Scopus + WoS",
   obj="Review multimodal emotion recognition methods and challenges.",
   data="Review (many)", n="N/A", modality="multi (audio/video/text)",
   inp="Multimodal", feat="Various", method="Survey", metric="N/A",
   out="Summarised trends; noted cross-cultural generalisation is open.",
   gap="Most corpora are culture-specific.",
   fut="Culturally robust multimodal models.",
   link="https://doi.org/10.1002/widm.1563", other=""),
 dict(doi="10.1145/3503161.3551591 (arXiv:2209.09578)", title="MultiMediate'22: Backchannel Detection and Agreement Estimation in Group Interactions",
   apa="Muller, P., et al. (2022). MultiMediate'22. ACM Multimedia.",
   authors="Muller, et al.", year=2022, venue="ACM Multimedia", index="Scopus",
   obj="Benchmark backchannel detection and agreement estimation.",
   data="NoXi, MPIIGroupInteraction", n="Challenge sets", modality="video + audio",
   inp="Multimodal", feat="Audio-visual behaviour", method="Deep learning baselines", metric="Accuracy / F1",
   out="Benchmarks for social signal analysis in interactions.",
   gap="Automatic backchannel/agreement analysis under-explored.",
   fut="Better social-signal models for mediation.",
   link="https://arxiv.org/abs/2209.09578", other=""),
]

body = Font(name="Arial", size=9)
wrap = Alignment(wrap_text=True, vertical="top")
for i, p in enumerate(P, 1):
    row = i + 1
    vals = [i, p["doi"], p["title"], p["apa"], p["authors"], p["year"], p["venue"],
            p["index"], p["obj"], p["data"], p["n"], p["modality"], p["inp"], p["feat"],
            p["method"], p["metric"], p["out"], p["gap"], p["fut"], p["link"], p["other"],
            "[add your Drive link]", "[your name / roll no.]",
            "[write your own 1-2 line insight]"]
    for j, v in enumerate(vals, 1):
        c = ws.cell(row=row, column=j, value=v)
        c.font = body; c.alignment = wrap; c.border = border

# column widths
widths = [5, 22, 34, 40, 26, 6, 22, 16, 34, 18, 16, 16, 18, 30, 28, 16, 34, 28, 24, 30, 26, 18, 18, 30]
for j, w in enumerate(widths, 1):
    ws.column_dimensions[openpyxl.utils.get_column_letter(j)].width = w

ws.freeze_panes = "A2"
ws.row_dimensions[1].height = 42

wb.save("Literature_Review.xlsx")
print("Saved Literature_Review.xlsx with", len(P), "papers")
