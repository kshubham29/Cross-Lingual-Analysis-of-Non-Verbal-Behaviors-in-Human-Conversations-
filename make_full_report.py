"""Generate the complete Project Report (all rubric sections)."""
import os
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT

NAVY = RGBColor(0x1E, 0x2C, 0x3F)
TEAL = RGBColor(0x02, 0x80, 0x90)
FIG = os.path.join("reports", "figures")

d = Document()
n = d.styles["Normal"]
n.font.name = "Calibri"; n.font.size = Pt(11)
n.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
n.paragraph_format.space_after = Pt(6)


def H(t, l=1):
    h = d.add_heading(t, level=l)
    for r in h.runs:
        r.font.color.rgb = NAVY


def body(t):
    p = d.add_paragraph(t); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY


def bullet(t):
    d.add_paragraph(t, style="List Bullet")


def num(t):
    d.add_paragraph(t, style="List Number")


def caption(t):
    p = d.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(t); r.italic = True; r.font.size = Pt(9.5); r.font.color.rgb = TEAL


def tbl(headers, rows, widths=None):
    t = d.add_table(rows=1, cols=len(headers))
    t.style = "Light Grid Accent 1"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]; c.text = ""
        r = c.paragraphs[0].add_run(h); r.bold = True; r.font.size = Pt(10)
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            r = cells[i].paragraphs[0].add_run(str(v)); r.font.size = Pt(10)
    if widths:
        for i, w in enumerate(widths):
            for row in t.rows:
                row.cells[i].width = Inches(w)
    d.add_paragraph()
    return t


def figure(name, width=5.6):
    p = os.path.join(FIG, name)
    if os.path.exists(p):
        d.add_picture(p, width=Inches(width))
        d.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER


# ==================== TITLE PAGE ====================
for _ in range(4):
    d.add_paragraph()
p = d.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("Cross-Lingual Prediction of Engagement\nfrom Non-Verbal Behaviour in Human Conversations")
r.bold = True; r.font.size = Pt(22); r.font.color.rgb = NAVY
p = d.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("Project Report"); r.italic = True; r.font.size = Pt(14); r.font.color.rgb = TEAL
for _ in range(8):
    d.add_paragraph()
p = d.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.add_run("Team: [Student 1]   ·   [Student 2]   ·   [Student 3]\n"
          "Course: Deep Learning\n[University / Department]\n[Date]").font.size = Pt(12)
d.add_page_break()

# ==================== ABSTRACT ====================
H("Abstract")
body("Engagement — how attentive and involved a person is in a conversation — is expressed largely "
     "through non-verbal behaviour such as facial expression and vocal prosody. This project "
     "investigates whether engagement can be predicted from non-verbal cues alone, and whether such "
     "models transfer across languages. Using the multilingual NoXi corpus of expert–novice "
     "conversations in French, English and German, we extracted 88 vocal (eGeMAPS) and 714 facial "
     "(OpenFace 2.0) features, aggregated them into 17,174 one-second windows, and trained both "
     "classical and deep-learning regressors to predict a continuous engagement value. Random Forest "
     "achieved a Concordance Correlation Coefficient (CCC) of 0.886 and a tuned neural network "
     "reached 0.883. A controlled cross-lingual experiment showed within-language performance of "
     "0.55 CCC falling to 0.39 across languages, indicating that engagement expression is partly "
     "language-specific. Voice features were found to correlate with engagement approximately twice "
     "as strongly as facial features.")
d.add_page_break()

# ==================== 1. INTRODUCTION ====================
H("1. Introduction")
body("Human communication is only partly carried by the words that are spoken. A substantial share "
     "of meaning is conveyed non-verbally, through facial expressions, head movements, gaze and the "
     "prosody of the voice. One of the most important social signals expressed by these cues is "
     "engagement: the degree to which a person is attentive, interested and involved in an interaction.")
body("Automatically estimating engagement from non-verbal behaviour has become an active research "
     "problem in affective computing and human–computer interaction, driven in particular by the NoXi "
     "database and the MultiMediate challenge series. Reliable engagement estimation would allow "
     "online-learning platforms to detect when a learner loses attention, virtual agents and social "
     "robots to adapt their behaviour, and video-conferencing tools to give speakers feedback on "
     "their audience. Because engagement changes continuously from moment to moment, it is modelled "
     "as a continuous, time-varying signal rather than a single discrete label.")
body("A crucial but often overlooked question is whether such models generalise across languages and "
     "cultures. Display rules for engagement differ between cultures and prosodic patterns differ "
     "between languages, so a model trained on speakers of one language may fail on speakers of "
     "another. As affective-computing systems are deployed globally, understanding this behaviour is "
     "essential for building systems that are fair and effective for all users.")
body("This project therefore studies cross-lingual engagement prediction from purely non-verbal "
     "behaviour. We extract vocal and facial features from the multilingual NoXi corpus, train "
     "machine-learning and deep-learning models to predict a continuous engagement signal, and "
     "evaluate explicitly whether a model trained on one language transfers to another.")

# ==================== 2. LITERATURE REVIEW ====================
H("2. Literature Review")
H("2.1 Engagement and Non-Verbal Behaviour", 2)
body("Engagement has been studied extensively in learning and interaction contexts. D'Mello and "
     "Graesser (2012) modelled the dynamics of affective states such as engagement, boredom and "
     "confusion during learning, showing that these states evolve over time and are reflected in "
     "observable behaviour. Gupta et al. (2016) introduced the DAiSEE dataset for recognising "
     "engagement, boredom and frustration from video of e-learning users, establishing engagement "
     "recognition as a computer-vision problem. Together these works motivate treating engagement as "
     "a continuous, behaviourally grounded signal rather than a fixed label.")
H("2.2 The NoXi Corpus and Related Datasets", 2)
body("Cafaro et al. (2017) presented the NoXi database (NOvice–eXpert Interaction), a corpus of "
     "screen-mediated dyadic novice–expert conversations recorded across several languages, including "
     "French, English and German, with continuous frame-wise engagement annotations on a 0–1 scale. "
     "The NoXi base set contains 48 training and 16 test sessions, approximately 84 dialogues and "
     "87 participants, giving roughly 25 hours of synchronised audio-visual data at 25 frames per "
     "second. Okada et al. (2024) extended it with NoXi+J, adding Japanese and Chinese sessions to "
     "study Asian–European differences in non-verbal behaviour. NoXi is particularly suited to "
     "cross-lingual work because all languages follow the same recording protocol, which reduces the "
     "confound between language and recording conditions. For broader context, Busso et al. (2008) "
     "released IEMOCAP and Poria et al. (2019) released MELD, both standard multimodal conversational "
     "emotion datasets, though these are English-only.")
H("2.3 Non-Verbal Feature Extraction", 2)
body("Robust feature extraction underpins behaviour analysis. Eyben et al. (2010) developed "
     "openSMILE for acoustic feature extraction, and Eyben et al. (2016) standardised the Geneva "
     "Minimalistic Acoustic Parameter Set (eGeMAPS), a compact set of 88 prosodic and voice-quality "
     "features including pitch, loudness, jitter and shimmer. For the visual modality, Baltrušaitis "
     "et al. (2018) released OpenFace 2.0, which extracts facial action units, head pose and eye gaze "
     "from video. These toolkits provide the standard non-verbal descriptors used throughout the "
     "field and are the pre-extracted features supplied with NoXi.")
H("2.4 Engagement Estimation on NoXi", 2)
body("The MultiMediate challenge series has driven progress on automatic engagement estimation. "
     "Müller et al. (2022) organised tasks on backchannel detection and agreement estimation; Müller "
     "et al. (2023) introduced continuous engagement estimation and bodily behaviour recognition on "
     "NoXi; and Müller et al. (2024) posed multi-domain engagement estimation, explicitly evaluating "
     "generalisation across language, culture, group size and setting. Recent state-of-the-art "
     "entries use attention-based multimodal fusion: the Dialogue Cross-Enhanced Central Engagement "
     "Attention Model (2024) and Generalizable Engagement Estimation via Domain Prompting and "
     "Parallel Attention (2025) align the behaviour of both participants to improve prediction. These "
     "works establish both the task formulation and the CCC evaluation protocol adopted here.")
H("2.5 Cross-Lingual and Cross-Cultural Generalisation", 2)
body("The question of whether affective models transfer across languages has a longer history in "
     "speech-emotion research. Schuller et al. (2010) analysed cross-corpus acoustic emotion "
     "recognition and reported substantial performance drops when models were applied to corpora "
     "other than their training set. Feraru, Schuller et al. (2015) surveyed cross-language acoustic "
     "emotion recognition and found consistent degradation across languages, particularly between "
     "distant language families. The cross-cultural focus of MultiMediate'24 and the NoXi+J corpus "
     "extends this question to engagement, but systematic cross-lingual evaluation of engagement "
     "models remains limited. Broad surveys (Baltrušaitis et al., 2019; Ramaswamy and Palaniswamy, "
     "2024) note that most corpora are culture-specific and that cross-cultural generalisation "
     "remains an open challenge.")

# ==================== 3. RESEARCH GAP ====================
H("3. Research Gap")
body("Three gaps emerge from the reviewed literature:")
num("Engagement rather than emotion. Cross-lingual transfer has been studied mainly for discrete "
    "emotion recognition (Schuller et al., 2010; Feraru et al., 2015). Far less work systematically "
    "evaluates cross-lingual transfer for continuous engagement.")
num("Non-verbal-only modelling. Many systems rely partly on linguistic (verbal) content, which does "
    "not transfer across languages. The extent to which purely non-verbal cues — prosody and facial "
    "behaviour — support engagement prediction across languages is under-explored.")
num("Explicit cross-lingual evaluation. Although NoXi is multilingual and the MultiMediate challenges "
    "test multi-domain generalisation, a controlled train-on-one-language, test-on-another analysis "
    "that isolates the effect of language is rarely reported.")
body("This project addresses all three by predicting engagement from non-verbal cues alone and "
     "evaluating transfer explicitly across French, English and German.")

# ==================== 4. PROBLEM STATEMENT ====================
H("4. Problem Statement")
p = d.add_paragraph(); p.paragraph_format.left_indent = Inches(0.3)
r = p.add_run("Given short windows of a person's non-verbal behaviour in a NoXi conversation — vocal "
              "prosody (eGeMAPS) and facial behaviour (OpenFace 2.0 action units, gaze and head pose) "
              "— predict their continuous level of engagement, and determine to what extent an "
              "engagement model trained on one language generalises to speakers of another language.")
r.italic = True
body("The task is formulated as regression, since engagement is continuous in the range [0, 1], and "
     "is evaluated with the Concordance Correlation Coefficient (CCC) following the MultiMediate "
     "protocol. The cross-lingual question is assessed by measuring the gap between within-language "
     "and cross-language performance.")

# ==================== 5. OBJECTIVES ====================
H("5. Research Objectives")
for o in [
    "Assemble a multilingual subset of NoXi (French, English, German) and align its pre-extracted "
    "eGeMAPS and OpenFace 2.0 feature streams with the frame-wise engagement annotations.",
    "Aggregate frame-level features into fixed one-second windows suitable for machine learning, "
    "retaining both vocal and facial modalities.",
    "Perform exploratory data analysis to characterise the distribution of engagement, class balance, "
    "and differences between languages and participant roles.",
    "Train and evaluate at least two classical baseline regressors and compare them using CCC.",
    "Design, train and tune a deep-learning model (an artificial neural network) and compare it "
    "against the baselines.",
    "Quantify cross-lingual transfer using a train-language × test-language CCC matrix and measure "
    "the gap between within-language and cross-language performance.",
    "Analyse the relative contribution of the vocal and facial modalities.",
]:
    num(o)

# ==================== 6. DATASET ====================
H("6. Dataset")
body("The NoXi corpus of screen-mediated dyadic novice–expert conversations is used. In each session "
     "one participant acts as an expert on a topic and the other as a novice, and the two hold a "
     "natural conversation over a screen. Because the interaction is spontaneous rather than acted, "
     "engagement varies naturally throughout each session.")
tbl(["Property", "Detail"],
    [["Source", "NoXi (Novice–Expert Interaction) database"],
     ["Access", "Free for academic research under a signed EULA"],
     ["Sessions used", "9 (3 French, 3 English, 3 German)"],
     ["Participants per session", "2 (one expert, one novice)"],
     ["Modalities", "Video (facial behaviour) and audio (voice)"],
     ["Sampling rate", "25 frames per second"],
     ["Vocal features", "eGeMAPS, 88 dimensions (pitch, loudness, voice quality)"],
     ["Facial features", "OpenFace 2.0, 714 dimensions (action units, gaze, head pose)"],
     ["Label", "Engagement, continuous 0–1, annotated frame-wise"]],
    widths=[2.0, 4.3])
body("Only non-verbal information is used. The spoken words are never employed, which makes the "
     "approach language-independent by construction.")

# ==================== 7. PREPROCESSING ====================
H("7. Preprocessing")
body("The raw feature streams and engagement annotations arrive at 25 Hz, which is too fine-grained "
     "and too noisy for direct modelling. The following preprocessing steps were applied:")
num("Extraction: only the required files (vocal features, facial features, engagement labels and the "
    "language annotation) were extracted from each session archive.")
num("Alignment: the vocal, facial and engagement streams were trimmed to a common length, since they "
    "can differ by one or two frames.")
num("Windowing: frames were grouped into non-overlapping one-second windows of 25 frames.")
num("Aggregation: each window is represented by the mean of its features and labelled with the mean "
    "engagement over that window. Windows whose label was missing were discarded.")
num("Standardisation: features were scaled to zero mean and unit variance, fitted on the training "
    "split only to avoid information leaking from the test data.")
body("The resulting dataset contains 17,174 windows described by 802 features (88 vocal and 714 "
     "facial), each labelled with a continuous engagement value, and tagged with its language, "
     "session and participant role. No missing feature values remained after preprocessing.")

# ==================== 8. EDA ====================
H("8. Exploratory Data Analysis")
body("Exploratory analysis was carried out before any modelling in order to understand the "
     "distribution of the data and to identify patterns worth testing.")
tbl(["Language", "Windows", "Mean engagement", "Std. dev."],
    [["French", "6,568", "0.592", "0.170"],
     ["German", "5,630", "0.594", "0.157"],
     ["English", "4,976", "0.558", "0.155"],
     ["Total", "17,174", "—", "—"]],
    widths=[1.6, 1.5, 1.8, 1.4])
body("The dataset is reasonably balanced across the three languages, and mean engagement is similar "
     "in each (0.56–0.59), which makes them directly comparable. The following observations emerged:")
bullet("Engagement is concentrated around the middle of the scale (approximately 0.5). Fully "
       "disengaged and fully absorbed moments are both rare, which is consistent with sustained "
       "conversational interaction.")
bullet("Experts are consistently more engaged than novices (mean 0.659 versus 0.506). This is "
       "intuitive, since the expert leads the exchange while the novice listens.")
bullet("Vocal features correlate with engagement roughly twice as strongly as facial features "
       "(mean absolute correlation 0.391 versus 0.187), suggesting prosody is the stronger "
       "engagement signal in this corpus.")
bullet("A one-way ANOVA confirmed that engagement differs significantly across the three languages "
       "(F = 84.67, p < 0.001), so language is a meaningful factor and not random variation.")
figure("engagement_distribution.png", 5.2)
caption("Figure 1. Distribution of engagement across all windows.")
figure("engagement_by_language.png", 5.2)
caption("Figure 2. Engagement by language — levels are similar across the three languages.")
figure("voice_vs_face.png", 4.4)
caption("Figure 3. Mean absolute correlation with engagement: vocal features exceed facial features.")

# ==================== 9. METHODOLOGY ====================
H("9. Methodology")
H("9.1 Baseline Models", 2)
body("Three classical regressors were selected as baselines because they represent three different "
     "model families: Linear Regression (linear), Random Forest (tree ensemble) and Support Vector "
     "Regression (kernel-based). Comparing across families indicates which class of approach best "
     "suits the data. Each model was placed in a pipeline that first standardises the features. The "
     "data was split 80% for training and 20% for testing. Because SVR scales poorly with sample "
     "size, it was trained on a random subsample of 4,000 rows.")
H("9.2 Deep-Learning Model", 2)
body("The deep-learning model is a multilayer perceptron (MLP) implemented in TensorFlow/Keras. It "
     "takes the 802 features as input and passes them through two hidden layers of 256 and 128 "
     "neurons, each using the ReLU activation function and followed by a dropout layer, before a "
     "single output neuron produces the predicted engagement value. ReLU introduces non-linearity, "
     "without which the network could only represent linear relationships; dropout randomly "
     "deactivates a proportion of neurons during training to reduce overfitting. Training uses the "
     "Adam optimiser and mean squared error loss. An equivalent implementation in PyTorch was also "
     "produced as a cross-check.")
H("9.3 Hyperparameter Tuning", 2)
body("A grid search was performed over dropout rate (0.1, 0.3, 0.5), learning rate (0.001, 0.0005) "
     "and architecture (256–128, 512–256), together with a comparison of the Adam and SGD optimisers. "
     "To keep the evaluation honest, the data was divided into 60% training, 20% validation and 20% "
     "test: configurations were compared on the validation set and only the winning configuration was "
     "scored on the untouched test set.")
H("9.4 Cross-Lingual Protocol", 2)
body("Cross-lingual transfer was measured by training on all sessions of one language and testing on "
     "all sessions of another, for every pair of languages. For the same-language cells of the matrix "
     "a leave-one-session-out procedure was used, so that training and testing never share a "
     "conversation. This avoids the inflated scores that occur when windows from the same session "
     "appear in both splits.")
H("9.5 Evaluation Metric", 2)
body("The primary metric is the Concordance Correlation Coefficient (CCC), which measures agreement "
     "between predicted and true values in both trend and absolute level, and is the standard metric "
     "for continuous affect and engagement. Pearson correlation, mean absolute error and the "
     "coefficient of determination (R²) are reported alongside it. Classification accuracy is not "
     "applicable because the target is continuous.")

# ==================== 10. RESULTS ====================
H("10. Results")
H("10.1 Baseline Models", 2)
tbl(["Model", "CCC", "Pearson", "MAE", "R²"],
    [["Random Forest", "0.886", "0.896", "0.051", "0.802"],
     ["Support Vector Regression", "0.827", "0.841", "0.066", "0.707"],
     ["Linear Regression", "0.284", "0.385", "0.076", "−3.412"]],
    widths=[2.4, 1.0, 1.1, 1.0, 1.1])
body("Random Forest performed best. Linear Regression produced a negative R², meaning its predictions "
     "were worse than simply predicting the mean engagement; this indicates that the relationship "
     "between the features and engagement is strongly non-linear and justifies the use of ensemble "
     "and neural models.")
H("10.2 Deep-Learning Model and Tuning", 2)
tbl(["Configuration", "Validation CCC"],
    [["Dropout 0.1 (best)", "0.857"],
     ["Dropout 0.3", "0.828"],
     ["Dropout 0.5", "0.669 – 0.784"],
     ["Adam optimiser", "0.873"],
     ["SGD optimiser", "0.817"]],
    widths=[3.0, 2.0])
body("The best configuration was dropout 0.1, learning rate 0.001, a 256–128 architecture and the "
     "Adam optimiser. Tuning improved test CCC from 0.861 to 0.883. Lower dropout consistently "
     "outperformed higher values, indicating that this dataset does not require heavy regularisation. "
     "The PyTorch implementation independently selected the same configuration, which supports the "
     "reliability of the result.")
H("10.3 Overall Model Comparison", 2)
tbl(["Model", "CCC"],
    [["Random Forest (baseline)", "0.886"],
     ["Tuned neural network (ANN)", "0.883"],
     ["Neural network (untuned)", "0.861"],
     ["Support Vector Regression", "0.827"],
     ["Linear Regression", "0.284"]],
    widths=[3.4, 1.4])
H("10.4 Cross-Lingual Transfer", 2)
body("The table below reports CCC for every training–testing language pair. Diagonal entries are "
     "within-language results obtained with leave-one-session-out validation.")
tbl(["Train \\ Test", "English", "French", "German"],
    [["English", "0.470", "0.354", "0.494"],
     ["French", "0.105", "0.596", "0.310"],
     ["German", "0.412", "0.665", "0.587"]],
    widths=[1.6, 1.4, 1.4, 1.4])
body("The average within-language CCC is 0.551, while the average cross-language CCC is 0.390. "
     "Transfer is also asymmetric: a German-trained model generalises comparatively well to French "
     "(0.665) and English (0.412), whereas a French-trained model performs poorly on English (0.105).")

# ==================== 11. DISCUSSION ====================
H("11. Discussion")
body("The results support the hypothesis that engagement can be predicted from non-verbal behaviour "
     "alone: within a single language, models reach a CCC of approximately 0.55 under strict "
     "session-separated evaluation, and considerably higher under a standard random split. This "
     "confirms that facial and vocal cues carry substantial information about engagement without any "
     "use of the spoken words.")
body("The central finding concerns cross-lingual transfer. Performance drops from 0.551 within a "
     "language to 0.390 across languages. Notably, the exploratory analysis showed that mean "
     "engagement levels are almost identical across the three languages (0.56–0.59). Taken together, "
     "these two observations suggest that people in different language communities are engaged to a "
     "similar degree, but express that engagement through different non-verbal patterns. In other "
     "words, the signal itself is culture-dependent even when the underlying state is not.")
body("A further observation is that vocal features correlate with engagement about twice as strongly "
     "as facial features. Since prosody is also the modality most affected by language, this may "
     "partly explain why cross-lingual transfer degrades: the most informative modality is also the "
     "most language-specific.")
body("Finally, the tuned neural network (0.883) matched but did not exceed the Random Forest baseline "
     "(0.886). This is consistent with the literature: on tabular, aggregated feature representations, "
     "tree ensembles are highly competitive with neural networks. A model that exploits the temporal "
     "ordering of windows, such as an LSTM, would be better placed to exceed this baseline.")

# ==================== 12. LIMITATIONS ====================
H("12. Limitations")
bullet("Only nine sessions across three languages were used, so the results should be regarded as "
       "preliminary rather than definitive.")
bullet("Averaging features over one-second windows discards fine-grained temporal detail that may "
       "carry engagement information.")
bullet("The cross-lingual matrix was produced with a single model family (Random Forest); other "
       "model families might transfer differently.")
bullet("The tuned network matches but does not surpass the strongest classical baseline.")
bullet("Verbal content was deliberately excluded, so any engagement information carried by what is "
       "said is not captured by design.")

# ==================== 13. CONCLUSION ====================
H("13. Conclusion and Future Work")
body("This project built a complete pipeline for predicting engagement from non-verbal behaviour on "
     "the multilingual NoXi corpus, comprising feature preparation, exploratory analysis, three "
     "classical baselines, a tuned neural network, and a controlled cross-lingual experiment. Random "
     "Forest achieved a CCC of 0.886 and the tuned neural network 0.883. The principal finding is "
     "that engagement models transfer only partially across languages: performance falls from 0.551 "
     "within a language to 0.390 across languages, indicating that the non-verbal expression of "
     "engagement is partly language- and culture-specific.")
body("Future work will focus on temporal modelling using recurrent architectures such as LSTM or GRU, "
     "which can exploit the fact that engagement rises and falls over the course of a conversation. "
     "Further directions include extending the analysis to additional languages using the NoXi+J "
     "corpus, applying attention-based multimodal fusion of the vocal and facial streams, exploring "
     "domain-adaptation techniques to improve cross-lingual transfer, and deploying the trained model "
     "in a demonstration application.")

# ==================== REFERENCES ====================
d.add_page_break()
H("References")
refs = [
 "Baltrušaitis, T., Ahuja, C., & Morency, L.-P. (2019). Multimodal Machine Learning: A Survey and Taxonomy. IEEE Transactions on Pattern Analysis and Machine Intelligence, 41(2), 423–443.",
 "Baltrušaitis, T., Zadeh, A., Lim, Y. C., & Morency, L.-P. (2018). OpenFace 2.0: Facial Behavior Analysis Toolkit. IEEE International Conference on Automatic Face and Gesture Recognition.",
 "Breiman, L. (2001). Random Forests. Machine Learning, 45(1), 5–32.",
 "Busso, C., Bulut, M., Lee, C.-C., et al. (2008). IEMOCAP: Interactive Emotional Dyadic Motion Capture Database. Language Resources and Evaluation, 42(4), 335–359.",
 "Cafaro, A., Wagner, J., Baur, T., et al. (2017). The NoXi Database: Multimodal Recordings of Mediated Novice-Expert Interactions. ICMI, 350–359.",
 "Cortes, C., & Vapnik, V. (1995). Support-Vector Networks. Machine Learning, 20(3), 273–297.",
 "D'Mello, S., & Graesser, A. (2012). Dynamics of Affective States during Complex Learning. Learning and Instruction, 22(2), 145–157.",
 "Eyben, F., Scherer, K., Schuller, B., et al. (2016). The Geneva Minimalistic Acoustic Parameter Set (eGeMAPS) for Voice Research and Affective Computing. IEEE Transactions on Affective Computing, 7(2), 190–202.",
 "Eyben, F., Wöllmer, M., & Schuller, B. (2010). openSMILE: The Munich Versatile and Fast Open-Source Audio Feature Extractor. ACM Multimedia, 1459–1462.",
 "Feraru, S. M., Schuller, D., & Schuller, B. (2015). Cross-Language Acoustic Emotion Recognition: An Overview and Some Tendencies. ACII.",
 "Gupta, A., D'Cunha, A., Awasthi, K., & Balasubramanian, V. (2016). DAiSEE: Towards User Engagement Recognition in the Wild. arXiv:1609.01885.",
 "Hochreiter, S., & Schmidhuber, J. (1997). Long Short-Term Memory. Neural Computation, 9(8), 1735–1780.",
 "Kingma, D. P., & Ba, J. (2015). Adam: A Method for Stochastic Optimization. ICLR.",
 "Müller, P., Balazia, M., et al. (2022). MultiMediate'22: Backchannel Detection and Agreement Estimation in Group Interactions. ACM Multimedia.",
 "Müller, P., Balazia, M., et al. (2023). MultiMediate'23: Engagement Estimation and Bodily Behaviour Recognition in Social Interactions. ACM Multimedia.",
 "Müller, P., Balazia, M., et al. (2024). MultiMediate'24: Multi-Domain Engagement Estimation. ACM Multimedia.",
 "Okada, S., et al. (2024). Multilingual Dyadic Interaction Corpus NoXi+J: Toward Understanding Asian-European Non-Verbal Cultural Characteristics. ACM ICMI.",
 "Poria, S., Hazarika, D., Majumder, N., et al. (2019). MELD: A Multimodal Multi-Party Dataset for Emotion Recognition in Conversations. ACL.",
 "Ramaswamy, M. P. A., & Palaniswamy, S. (2024). Multimodal Emotion Recognition: A Comprehensive Review, Trends, and Challenges. WIREs Data Mining and Knowledge Discovery.",
 "Schuller, B., Vlasenko, B., Eyben, F., et al. (2010). Cross-Corpus Acoustic Emotion Recognition: Variances and Strategies. IEEE Transactions on Affective Computing, 1(2), 119–131.",
 "Srivastava, N., Hinton, G., Krizhevsky, A., Sutskever, I., & Salakhutdinov, R. (2014). Dropout: A Simple Way to Prevent Neural Networks from Overfitting. JMLR, 15(1), 1929–1958.",
 "Vaswani, A., et al. (2017). Attention Is All You Need. NeurIPS.",
 "Yu, J., et al. (2024). Dialogue Cross-Enhanced Central Engagement Attention Model for Real-Time Engagement Estimation. IJCAI.",
 "Expert-Novice Interaction: Annotation and Analysis (2018). LREC Workshop.",
 "Generalizable Engagement Estimation in Conversation via Domain Prompting and Parallel Attention (2025). arXiv:2508.14448.",
]
for i, rr in enumerate(refs, 1):
    p = d.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.35)
    p.paragraph_format.first_line_indent = Inches(-0.35)
    p.paragraph_format.space_after = Pt(4)
    p.add_run(f"[{i}]  {rr}").font.size = Pt(10)

d.save("Project_Report.docx")
print("Saved Project_Report.docx")
