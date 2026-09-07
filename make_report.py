"""Generate the Week 2-4 report (NoXi-focused) as a Word document."""
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING

doc = Document()
n = doc.styles["Normal"]
n.font.name = "Calibri"; n.font.size = Pt(11)
n.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
n.paragraph_format.space_after = Pt(6)
NAVY = RGBColor(0x1E, 0x2C, 0x3F)


def heading(t, l):
    h = doc.add_heading(t, level=l)
    for r in h.runs:
        r.font.color.rgb = NAVY


def body(t):
    p = doc.add_paragraph(t); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY


def num(t):
    doc.add_paragraph(t, style="List Number")


# ===== TITLE =====
for _ in range(4):
    doc.add_paragraph()
t = doc.add_paragraph(); t.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = t.add_run("Cross-Lingual Prediction of Engagement\nfrom Non-Verbal Behaviour in Human Conversations")
r.bold = True; r.font.size = Pt(22); r.font.color.rgb = NAVY
s = doc.add_paragraph(); s.alignment = WD_ALIGN_PARAGRAPH.CENTER
rs = s.add_run("Project Report — Literature Review, Research Gap, Problem Statement, Objectives and Methodology")
rs.italic = True; rs.font.size = Pt(13)
for _ in range(8):
    doc.add_paragraph()
tm = doc.add_paragraph(); tm.alignment = WD_ALIGN_PARAGRAPH.CENTER
tm.add_run("Team: [Student 1]  ·  [Student 2]  ·  [Student 3]\nCourse: Deep Learning\n[University / Department]").font.size = Pt(12)
doc.add_page_break()

# ===== 1. INTRODUCTION =====
heading("1. Introduction", 1)
for p in [
 "Human communication is only partly carried by the words that are spoken. A large share of "
 "meaning in a conversation is conveyed non-verbally, through facial expressions, head "
 "movements, gaze and the prosody of the voice (its pitch, loudness and rhythm). One of the "
 "most important social signals these non-verbal cues express is engagement: the degree to "
 "which a person is attentive, interested and involved in an interaction.",
 "Automatically estimating engagement from non-verbal behaviour has become an active research "
 "problem in affective computing and human-computer interaction, driven in particular by the "
 "NoXi database and the MultiMediate challenge series. Reliable engagement estimation would "
 "allow online-learning platforms to detect when a learner loses attention, virtual agents to "
 "adapt their behaviour, and video-conferencing tools to give speakers feedback. Because "
 "engagement is expressed continuously and changes moment to moment, it is modelled as a "
 "continuous, time-varying signal rather than a single discrete label.",
 "A crucial but often overlooked question is whether models of non-verbal behaviour generalise "
 "across languages and cultures. Display rules for engagement differ between cultures and "
 "prosodic patterns differ between languages, so a model trained on one language may fail on "
 "another. This project studies cross-lingual engagement prediction from non-verbal behaviour "
 "using the multilingual NoXi corpus: we extract vocal (prosodic) and facial features, train "
 "machine-learning and deep-learning models to predict a continuous engagement signal, and "
 "evaluate whether models trained on one language transfer to another.",
]:
    body(p)

# ===== 2. LITERATURE REVIEW =====
heading("2. Literature Review", 1)

heading("2.1 Engagement and Non-Verbal Behaviour", 2)
body("Engagement has been studied extensively in learning and interaction contexts. D'Mello and "
     "Graesser (2012) modelled the dynamics of affective states such as engagement, boredom and "
     "confusion during learning, showing they evolve over time and are reflected in observable "
     "behaviour. Gupta et al. (2016) introduced the DAiSEE dataset for recognising engagement, "
     "boredom and frustration from video of e-learning users, establishing engagement recognition "
     "as a computer-vision problem. These works motivate treating engagement as a continuous, "
     "behaviourally grounded signal.")

heading("2.2 The NoXi Corpus and Related Datasets", 2)
body("Cafaro et al. (2017) presented the NoXi database (NOvice-eXpert Interaction), a large corpus "
     "of screen-mediated dyadic novice-expert conversations recorded across several languages "
     "(including French, English and German) with continuous, frame-wise engagement annotations "
     "on a 0-to-1 scale. The NoXi Base set contains 48 training and 16 test sessions, totalling "
     "about 84 dialogues, 87 participants and roughly 25 hours of synchronised audio-visual data "
     "at 25 frames per second. Okada et al. (2024) extended it with NoXi+J, adding Japanese and "
     "Chinese sessions to study Asian-European non-verbal differences. NoXi is particularly suited "
     "to cross-lingual work because all languages follow the same recording protocol, reducing the "
     "confound between language and recording conditions. For broader context, Busso et al. (2008) "
     "released IEMOCAP and Poria et al. (2019) released MELD, standard multimodal conversational "
     "emotion datasets, though these are English-only.")

heading("2.3 Non-Verbal Feature Extraction", 2)
body("Robust feature extraction underpins behaviour analysis. Eyben et al. (2010) developed "
     "openSMILE for acoustic feature extraction, and Eyben et al. (2016) standardised the Geneva "
     "Minimalistic Acoustic Parameter Set (eGeMAPS): 88 prosodic and voice-quality features "
     "(pitch, loudness, jitter, shimmer). Baltrusaitis et al. (2018) released OpenFace 2.0, which "
     "extracts facial action units, head pose and eye gaze from video. These two toolkits provide "
     "the standard non-verbal descriptors and are the pre-extracted features supplied with NoXi.")

heading("2.4 Engagement Estimation on NoXi (MultiMediate Challenges)", 2)
body("The MultiMediate challenge series has driven progress on automatic engagement estimation "
     "from NoXi. Muller et al. (2022) organised tasks on backchannel detection and agreement "
     "estimation; Muller et al. (2023) introduced continuous engagement estimation and bodily "
     "behaviour recognition on NoXi; and Muller et al. (2024) posed multi-domain engagement "
     "estimation, explicitly evaluating generalisation across language, culture, group size and "
     "setting. Recent state-of-the-art entries use attention-based multimodal fusion: the Dialogue "
     "Cross-Enhanced Central Engagement Attention Model (2024) and Generalizable Engagement "
     "Estimation via Domain Prompting and Parallel Attention (2025) align the behaviour of both "
     "participants to improve prediction. These works establish the task formulation and the CCC "
     "(Concordance Correlation Coefficient) evaluation protocol adopted in this project.")

heading("2.5 Cross-Lingual and Cross-Cultural Generalisation", 2)
body("Whether affective models transfer across languages has a longer history in speech-emotion "
     "research. Schuller et al. (2010) analysed cross-corpus acoustic emotion recognition and "
     "showed substantial performance drops when models are applied to other corpora. Feraru, "
     "Schuller et al. (2015) surveyed cross-language acoustic emotion recognition and reported "
     "degradation across languages, especially between distant language families. The "
     "cross-cultural focus of MultiMediate'24 and NoXi+J extends this question specifically to "
     "engagement, but systematic cross-lingual evaluation of engagement models remains limited. "
     "Broad surveys (Baltrusaitis et al., 2019; Ramaswamy and Palaniswamy, 2024) note that most "
     "corpora are culture-specific and that cross-cultural generalisation is an open challenge.")

# ===== 3. RESEARCH GAP =====
heading("3. Research Gap", 1)
body("From the reviewed literature, three gaps motivate this project:")
num("Engagement, not just emotion, across languages. Cross-lingual transfer has been studied "
    "mainly for discrete emotion recognition (Schuller et al., 2010; Feraru et al., 2015); far "
    "less work systematically evaluates cross-lingual transfer for continuous engagement.")
num("Non-verbal-only, language-independent modelling. Many systems rely partly on linguistic "
    "(verbal) content, which does not transfer across languages. The extent to which purely "
    "non-verbal cues (prosody and facial behaviour) support engagement prediction across "
    "languages is under-explored.")
num("Explicit cross-lingual evaluation. Although NoXi is multilingual and the MultiMediate "
    "challenges test multi-domain generalisation, a controlled train-on-one-language, "
    "test-on-another analysis that isolates the effect of language is rarely reported.")
body("This project addresses these gaps by predicting engagement from non-verbal cues alone and "
     "evaluating transfer explicitly across French, English and German on NoXi.")

# ===== 4. PROBLEM STATEMENT =====
heading("4. Problem Statement", 1)
ps = doc.add_paragraph(); ps.paragraph_format.left_indent = Inches(0.3)
ru = ps.add_run("Given short windows of a person's non-verbal behaviour in a NoXi conversation "
                "— vocal prosody (eGeMAPS) and facial behaviour (OpenFace 2.0 action units, gaze "
                "and head pose) — predict their continuous level of engagement, and determine to "
                "what extent an engagement model trained on one language generalises to speakers "
                "of another language.")
ru.italic = True
body("The task is formulated as regression (engagement is continuous in [0, 1]) evaluated with the "
     "Concordance Correlation Coefficient (CCC), following the MultiMediate protocol. The "
     "cross-lingual question is evaluated by measuring the drop between within-language and "
     "cross-language performance.")

# ===== 5. OBJECTIVES =====
heading("5. Objectives", 1)
for o in [
 "Assemble a multilingual subset of NoXi (French, English, German) and align its pre-extracted "
 "eGeMAPS and OpenFace 2.0 feature streams with the frame-wise engagement annotations.",
 "Aggregate the frame-level features into one-second windows suitable for machine learning, "
 "retaining both vocal and facial modalities.",
 "Train and evaluate classical regressors (Linear Regression, Random Forest, SVR) as baselines "
 "for engagement prediction, scored with CCC.",
 "Design and train deep-learning models (an MLP and, subsequently, a temporal LSTM) and compare "
 "them against the baselines.",
 "Quantify cross-lingual transfer using a train-language x test-language CCC matrix.",
 "Analyse the relative contribution of the vocal and facial modalities and interpret which cues "
 "drive engagement.",
 "Document the methodology, results and limitations, and discuss implications for culturally "
 "robust affective-computing systems.",
]:
    num(o)

# ===== 6. METHODOLOGY =====
heading("6. Methodology", 1)
body("Dataset. The NoXi corpus of screen-mediated dyadic novice-expert conversations is used, "
     "grouped by recording language (French, English, German). For each participant (expert and "
     "novice) NoXi provides pre-extracted eGeMAPS audio features (88 dimensions at 25 Hz), "
     "OpenFace 2.0 visual features, and frame-wise engagement annotations.")
body("Pre-processing. Frame-level feature streams and engagement labels are aligned and segmented "
     "into one-second (25-frame) non-overlapping windows. Each window is the mean of its vocal and "
     "facial features, labelled with its mean engagement; windows with missing labels are removed "
     "and features are standardised.")
body("Models. Three families are compared: classical regressors (Linear Regression, Random Forest, "
     "SVR) as baselines; a multilayer perceptron (MLP); and a temporal LSTM that exploits the "
     "ordering of windows. Models use the Adam optimiser with dropout and weight-decay regularisation.")
body("Evaluation. The primary metric is CCC, complemented by Pearson correlation and mean absolute "
     "error. Within-language performance uses leave-one-session-out cross-validation to avoid "
     "temporal leakage. Cross-lingual performance trains on all sessions of one language and tests "
     "on all sessions of another, producing a train-language x test-language CCC matrix whose "
     "diagonal-vs-off-diagonal gap quantifies how language-specific engagement behaviour is.")
body("Tools. Feature extraction uses the eGeMAPS/openSMILE and OpenFace 2.0 descriptors supplied "
     "with NoXi; modelling uses scikit-learn (classical models) and PyTorch (deep-learning models).")

# ===== REFERENCES =====
heading("References", 1)
refs = [
 "Baltrusaitis, T., Ahuja, C., & Morency, L.-P. (2019). Multimodal Machine Learning: A Survey and Taxonomy. IEEE TPAMI, 41(2), 423-443.",
 "Baltrusaitis, T., Zadeh, A., Lim, Y. C., & Morency, L.-P. (2018). OpenFace 2.0: Facial Behavior Analysis Toolkit. IEEE FG.",
 "Busso, C., et al. (2008). IEMOCAP: Interactive Emotional Dyadic Motion Capture Database. Language Resources and Evaluation, 42(4), 335-359.",
 "Cafaro, A., et al. (2017). The NoXi Database: Multimodal Recordings of Mediated Novice-Expert Interactions. ICMI, 350-359.",
 "D'Mello, S., & Graesser, A. (2012). Dynamics of Affective States during Complex Learning. Learning and Instruction, 22(2), 145-157.",
 "Eyben, F., et al. (2016). The Geneva Minimalistic Acoustic Parameter Set (eGeMAPS). IEEE Trans. Affective Computing, 7(2), 190-202.",
 "Eyben, F., Wollmer, M., & Schuller, B. (2010). openSMILE: The Munich Versatile and Fast Open-Source Audio Feature Extractor. ACM Multimedia, 1459-1462.",
 "Feraru, S. M., Schuller, D., & Schuller, B. (2015). Cross-Language Acoustic Emotion Recognition: An Overview and Some Tendencies. ACII.",
 "Gupta, A., et al. (2016). DAiSEE: Towards User Engagement Recognition in the Wild. arXiv:1609.01885.",
 "Muller, P., et al. (2022). MultiMediate'22: Backchannel Detection and Agreement Estimation in Group Interactions. ACM Multimedia.",
 "Muller, P., et al. (2023). MultiMediate'23: Engagement Estimation and Bodily Behaviour Recognition in Social Interactions. ACM Multimedia. arXiv:2308.08256.",
 "Muller, P., et al. (2024). MultiMediate'24: Multi-Domain Engagement Estimation. ACM Multimedia. arXiv:2408.16625.",
 "Okada, S., et al. (2024). Multilingual Dyadic Interaction Corpus NoXi+J. ACM ICMI. arXiv:2409.13726.",
 "Poria, S., et al. (2019). MELD: A Multimodal Multi-Party Dataset for Emotion Recognition in Conversations. ACL.",
 "Ramaswamy, M. P. A., & Palaniswamy, S. (2024). Multimodal Emotion Recognition: A Comprehensive Review, Trends, and Challenges. WIREs DMKD.",
 "Schuller, B., et al. (2010). Cross-Corpus Acoustic Emotion Recognition: Variances and Strategies. IEEE Trans. Affective Computing, 1(2), 119-131.",
 "Yu, J., et al. (2024). Dialogue Cross-Enhanced Central Engagement Attention Model for Real-Time Engagement Estimation. IJCAI.",
 "Engagement Estimation via Domain Prompting and Parallel Attention (2025). arXiv:2508.14448.",
]
for i, rr in enumerate(refs, 1):
    p = doc.add_paragraph(); p.paragraph_format.left_indent = Inches(0.3)
    p.paragraph_format.first_line_indent = Inches(-0.3)
    p.add_run(f"[{i}] {rr}").font.size = Pt(10)

doc.save("Project_Report_Week2-4.docx")
print("Saved Project_Report_Week2-4.docx with", len(refs), "references")
