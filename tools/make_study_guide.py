"""Writes Project_Study_Guide.docx: the whole project explained simply (concepts, data,
every step, every model, results, comparison with research, limitations, files) and
a full question-and-answer bank for the evaluation. Plain black and white.
Run from the project folder: python tools/make_study_guide.py"""
from docx import Document
from docx.shared import Pt, Cm, RGBColor

doc = Document()
for side in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
    setattr(doc.sections[0], side, Cm(2))
doc.styles["Normal"].font.name = "Calibri"; doc.styles["Normal"].font.size = Pt(11)
for h in ("Heading 1", "Heading 2"):
    doc.styles[h].font.color.rgb = RGBColor(0, 0, 0)


def P(text, bold_lead=None):
    p = doc.add_paragraph()
    if bold_lead:
        p.add_run(bold_lead).bold = True
    p.add_run(text)


def B(items):
    for it in items:
        if isinstance(it, tuple):
            p = doc.add_paragraph(style="List Bullet"); p.add_run(it[0]).bold = True; p.add_run(it[1])
        else:
            doc.add_paragraph(it, style="List Bullet")


def T(header, rows):
    t = doc.add_table(rows=1, cols=len(header)); t.style = "Table Grid"
    for i, h in enumerate(header):
        t.rows[0].cells[i].text = ""
        t.rows[0].cells[i].paragraphs[0].add_run(h).bold = True
    for r in rows:
        cells = t.add_row().cells
        for i, v in enumerate(r):
            cells[i].text = str(v)
    doc.add_paragraph()


H1 = lambda t: doc.add_heading(t, 1)
H2 = lambda t: doc.add_heading(t, 2)

# ============================================================ title
t = doc.add_paragraph().add_run("Project Study Guide"); t.bold, t.font.size = True, Pt(20)
doc.add_paragraph("Cross-Lingual Prediction of Engagement from Non-Verbal Behaviour in Human Conversations")
doc.add_paragraph("Everything about the project explained simply, and the questions you can be asked, with answers.")
doc.add_paragraph("Contents: 1 Project in one page | 2 Key ideas | 3 Dataset | 4 Steps from start to end | 5 Models | "
                  "6 Results | 7 Comparison with research | 8 Limitations and future work | 9 Project files | 10 Questions and answers")

# ============================================================ 1
H1("1. The project in one page")
B([("Aim: ", "predict how engaged a person is in a conversation (a score from 0 to 1) from non-verbal behaviour only "
             "(voice and face, not the words), and check whether a model trained on one language still works on another."),
   ("Why it matters: ", "online teaching, video calls, social robots and tutoring systems need to know if a person is "
                        "engaged; such systems are used in many languages."),
   ("Data: ", "the NoXi corpus: 9 recorded conversations (3 English, 3 French, 3 German), 18 people, 17,174 one-second windows."),
   ("Features: ", "88 voice features (eGeMAPS) + 709 face features (OpenFace) = 797 per second; plus features from six "
                  "pretrained Transformers."),
   ("Models: ", "Linear Regression, Random Forest, Gradient Boosting, XGBoost, ANN, CNN, SimpleRNN, LSTM, GRU, our own "
                "Transformer, autoencoders, and six frozen pretrained Transformers."),
   ("Test: ", "always on conversations the model has never seen; and across languages (train on A, test on B)."),
   ("Best result: ", "Gradient Boosting on voice + w2v-BERT 2.0 + VideoMAE features with past context: CCC 0.777, only "
                     "1% drop on a new language. Statistically significant (p = 0.006) and still 0.760 for completely unseen people."),
   ("Main findings: ", "(1) random splits give falsely high scores; (2) voice transfers across languages, face does not "
                       "(12% vs 55% drop); (3) past context helps most; (4) pretrained Transformer features + Gradient "
                       "Boosting work best on small data.")])

# ============================================================ 2
H1("2. Key ideas explained simply")
T(["Term", "Simple meaning"], [
    ("Engagement", "How involved and attentive a person is in the conversation. Rated by humans continuously, 0 (not engaged) to 1 (fully engaged)."),
    ("Non-verbal behaviour", "Everything except the words: tone of voice, loudness, pitch, facial expressions, gaze, head movement."),
    ("Cross-lingual", "Across languages: train on English, test on French, for example."),
    ("Feature", "A number that describes behaviour, e.g. the pitch of the voice or how much a person smiles."),
    ("eGeMAPS", "A standard set of 88 voice features (pitch, loudness, voice quality) made with the openSMILE tool."),
    ("OpenFace", "A tool that measures the face from video: facial action units, gaze, head pose, landmarks (709 features after cleaning)."),
    ("1-second window", "The data has 25 frames per second; we average 25 frames into one row, so each row = one second of behaviour."),
    ("Regression", "Predicting a number (engagement 0-1), not a class."),
    ("CCC", "Concordance Correlation Coefficient, the score we use. 1 = predictions match the human ratings perfectly. It "
            "checks both the pattern and that the values are not shifted or wrongly scaled."),
    ("Data leakage", "When information about the test data gets into training. Here: neighbouring seconds of the same "
                     "conversation in both training and test, which gave falsely high scores (about 0.90)."),
    ("Held-out conversations / folds", "Whole conversations are kept apart for testing. 3 folds: each tests on 3 conversations (one per language) and trains on the other 6."),
    ("Within-language / cross-language", "Within: train and test in the same language (on different conversations). Cross: train on one language, test on another."),
    ("Language drop", "How much the score falls in a new language: 100 x (within - cross) / within."),
    ("Ablation", "Removing or isolating a part of the input to see what it contributes (voice only vs face only)."),
    ("Transfer learning", "Reusing knowledge learned on one task or data for another (a CNN trained on 2 languages adapted to the 3rd)."),
    ("Pretrained Transformer", "A large model trained by others on huge data (e.g. w2v-BERT 2.0 on 4.5 million hours of audio)."),
    ("Frozen", "The pretrained model is not changed; only a small model on top of it is trained."),
    ("Fine-tuning", "Also updating the pretrained model's own weights; needs a GPU and more data (future work)."),
    ("Context", "Adding the mean of the person's last 5 and 10 seconds, so the model sees recent history."),
    ("Smoothing", "Averaging the predictions over the last 5 seconds to remove jumps."),
    ("Fusion", "Combining features from several sources (voice + speech model + video model) into one input."),
    ("Significance test", "A statistical check that a better score is not just luck (Wilcoxon test, p < 0.05)."),
    ("Person-disjoint", "No person appears in both training and test. Two NoXi participants appear in two of our conversations, so we checked this too."),
])

# ============================================================ 3
H1("3. The dataset: NoXi")
B(["NoXi (Novice-Expert Interaction): video calls in which an expert explains a topic to a novice. Recorded in Paris, Nottingham and Augsburg.",
   "Each person's engagement is rated by human annotators 25 times per second, on a 0-1 scale.",
   "The corpus also provides ready-made features: eGeMAPS (voice), OpenFace (face), and embeddings of pretrained Transformers.",
   "We used 9 conversations: 001, 013, 021 (French); 027, 028, 030 (English); 070, 072, 077 (German).",
   "17,174 one-second windows: French 6,568, German 5,630, English 4,976.",
   "Average engagement: English 0.558, French 0.592, German 0.594; experts 0.659, novices 0.506.",
   "Licence: the data is licensed through the supervisor; it must not be shared or uploaded anywhere."])

# ============================================================ 4
H1("4. What we did, step by step")
steps = [
    ("01 Extract data", "Copied only the needed files (voice, face, labels, language) from the 14 GB zips.", "9 conversation folders."),
    ("02 Build features", "Aligned voice, face and labels; cut into 1-second windows; averaged each window.", "17,174 rows x 797 features; also the 25-frame sequences."),
    ("03 EDA", "Explored the data: counts, averages, ANOVA, charts, correlations, PCA.", "Languages differ slightly (F = 84.67); voice correlates more than face (0.391 vs 0.187)."),
    ("04 Baselines", "First ML models on a random split.", "About 0.90 (later found to be leakage)."),
    ("05 Cross-lingual", "Trained on one language, tested on another, all 6 pairs.", "Within 0.556, cross 0.393: 29% drop."),
    ("06-07 ANN + tuning", "First neural network; 13 settings tried.", "Best: 256-128 neurons, dropout 0.1, Adam 0.001."),
    ("08-13 Deep models", "Sequence models, CNN (tuning, LeNet/VGG/ResNet), transfer learning, Transformer, LSTM.", "VGG-style CNN best; transfer learning works (fine-tune 0.569 vs scratch 0.230 with 10% data)."),
    ("14 Session evaluation", "Found the leakage and re-tested the ML models + ANN on unseen conversations (3 folds).", "Gradient Boosting 0.633 (was 0.90 with random split)."),
    ("15 Sequence models", "CNN, SimpleRNN, LSTM, GRU, Transformer on unseen conversations.", "Transformer 0.583, CNN 0.577, LSTM 0.512."),
    ("16 Autoencoder", "Compressed 797 features to 32, then predicted.", "0.564-0.577."),
    ("17 Ablation", "Voice only vs face only vs both.", "Voice 0.652 (12% drop), face 0.397 (55% drop)."),
    ("18 Master results", "One table of all models.", "Tree models best."),
    ("19 Pretrained features", "Read the features of six pretrained Transformers and averaged them per second.", "Aligned to the same 17,174 windows."),
    ("20 Pretrained Transformers", "Trained XGBoost / dense heads on each frozen Transformer's features.", "w2v-BERT 0.631 with 0% drop; w2v-BERT + VideoMAE 0.663."),
    ("21 Smoothing", "Averaged predictions over 5 s.", "Small gain (0.633 -> 0.649)."),
    ("22 Partner", "Added the other speaker's features.", "No gain in accuracy."),
    ("23 Context", "Added the past 5 s and 10 s.", "Biggest gain: 0.633 -> 0.719, 0% drop."),
    ("24 Fusion", "Voice + w2v-BERT + VideoMAE + context with Gradient Boosting.", "Best model: 0.777, 1% drop."),
    ("25 Transformer context", "Our Transformer with 10 s of input instead of 1 s.", "0.583 -> 0.637; drop 34% -> 14%."),
    ("26 Significance", "Wilcoxon test per speaker with bootstrap intervals and Holm correction.", "Best vs baseline: better for 15/18 speakers, p = 0.006."),
    ("27 Person-disjoint", "Re-tested with no shared participants between training and test.", "Best model still 0.760, 0% drop."),
]
T(["Step", "What we did", "Result"], steps)

# ============================================================ 5
H1("5. The models explained")
models = [
    ("Linear Regression", "Fits a straight-line formula: engagement = w1 x feature1 + w2 x feature2 + ...", "0.240", "Too simple: engagement is not a straight-line function of the features, and extreme values hurt it."),
    ("Random Forest", "Many decision trees, each trained on a random part of the data; their answers are averaged.", "0.631", "Strong and stable on tabular data."),
    ("Gradient Boosting", "Trees built one after another; each new tree fixes the errors of the previous ones (300 trees).", "0.633", "Best basic model: good with small data and many features, ignores noisy ones."),
    ("XGBoost", "A fast, popular version of gradient boosting (300 trees, depth 6, learning rate 0.1).", "0.620", "Similar to Gradient Boosting."),
    ("ANN (MLP)", "Neural network: 797 inputs -> 256 -> 128 -> 1, ReLU, dropout 0.1, Adam.", "0.591", "Unstable across folds (+-0.154): too little data for a neural network."),
    ("CNN (VGG style)", "Convolution filters slide over the 25 frames to find short patterns; pooling reduces size.", "0.577", "Finds local patterns, but one second is short."),
    ("SimpleRNN", "Reads the frames one by one with a memory; forgets quickly (vanishing gradient).", "0.510", "Weakest family."),
    ("LSTM", "RNN with 3 gates (forget, input, output) and a memory cell for longer memory.", "0.512", "Did not help on 1-second input; unstable."),
    ("GRU", "Simpler LSTM with 2 gates (update, reset).", "0.528", "Similar to LSTM."),
    ("Own Transformer", "Self-attention: every frame looks at every other frame. Positional encoding gives the order. 2 encoder blocks, 4 heads.", "0.583 (1 s), 0.637 (10 s)", "Most stable deep model; improves with longer input."),
    ("Autoencoder", "Squeezes 797 features into 32 and rebuilds them (no labels); then a predictor uses the 32 numbers.", "0.564-0.577", "Compression loses some information."),
    ("Pretrained Transformers (frozen)", "XLM-RoBERTa (text), w2v-BERT 2.0 (speech), CLIP, DINOv2, Swin, VideoMAE (video); a small head is trained on their features.", "up to 0.663", "Bring knowledge from huge datasets; w2v-BERT transfers across languages with no drop."),
    ("Best model (fusion + context)", "Gradient Boosting on voice + w2v-BERT + VideoMAE features, plus the mean of the last 5 s and 10 s (7,560 features).", "0.777", "Combines the strongest signals and recent history."),
]
T(["Model", "How it works", "CCC", "Why this result"], models)

# ============================================================ 6
H1("6. Results")
H2("All models on unseen conversations")
T(["Rank", "Model", "CCC", "Language drop"], [
    (1, "Gradient Boosting: voice + w2v-BERT + VideoMAE + context", "0.777 +- 0.063", "1%"),
    (2, "Gradient Boosting: voice + face + context", "0.719 +- 0.009", "0%"),
    (3, "w2v-BERT 2.0 + VideoMAE (frozen) + dense head", "0.663 +- 0.020", "5%"),
    (4, "Own Transformer, 10 s", "0.637 +- 0.070", "14%"),
    (5, "Gradient Boosting (voice + face)", "0.633 +- 0.063", "20%"),
    (6, "Random Forest", "0.631 +- 0.050", "-"),
    (7, "XGBoost", "0.620 +- 0.052", "29% (matrix)"),
    (8, "ANN (MLP)", "0.591 +- 0.154", "-"),
    (9, "Own Transformer, 1 s", "0.583 +- 0.038", "34%"),
    (10, "CNN (VGG style)", "0.577 +- 0.101", "-"),
    (11, "Autoencoder + XGBoost / dense", "0.577 / 0.564", "-"),
    (12, "GRU / LSTM / SimpleRNN", "0.528 / 0.512 / 0.510", "-"),
    (13, "Linear Regression", "0.240 +- 0.286", "-"),
])
H2("Cross-language matrix (Random Forest, rows = train, columns = test)")
T(["", "English", "French", "German"], [("English", "0.474", "0.349", "0.516"), ("French", "0.092", "0.604", "0.336"),
                                        ("German", "0.408", "0.658", "0.590")])
P("Within (diagonal) 0.556, cross 0.393: a new language costs 29%.")
H2("Voice vs face (XGBoost)")
T(["Input", "Unseen", "Within", "Cross", "Drop"], [("Voice (88)", "0.652", "0.596", "0.522", "12%"),
                                                    ("Face (709)", "0.397", "0.322", "0.145", "55%"),
                                                    ("Both (797)", "0.631", "0.571", "0.451", "21%")])
H2("Pretrained Transformers (frozen)")
T(["Model", "Type", "Best CCC", "Drop"], [("XLM-RoBERTa", "text", "0.393", "33%"), ("w2v-BERT 2.0", "audio", "0.631", "0%"),
                                          ("CLIP", "video", "0.304", "106%"), ("DINOv2", "video", "0.485", "58%"),
                                          ("Swin", "video", "0.449", "41%"), ("VideoMAE", "video", "0.553", "22%"),
                                          ("w2v-BERT + VideoMAE", "audio + video", "0.663", "5%")])
H2("Checks")
B(["Significance: best model vs baseline +0.159 CCC per speaker, better for 15 of 18 speakers and all 9 conversations, Holm p = 0.006.",
   "Unseen people: with no shared participants, the best model scores 0.760 (was 0.777) with 0% language drop.",
   "XGBoost shows 0.620 in one table and 0.631 in another: small numerical differences (number precision, random sampling), far smaller than the fold spread."])

# ============================================================ 7
H1("7. Comparison with research papers")
T(["", "Research (MultiMediate challenges, IJCAI-24)", "This project"], [
    ("Best CCC on NoXi", "0.71-0.76 on the official test set", "0.777 on our own held-out conversations (not directly comparable)"),
    ("w2v-BERT 2.0 alone", "0.64 (MultiMediate'24 baseline)", "0.631"),
    ("XLM-RoBERTa alone", "0.40", "0.393"),
    ("Face transfer to new languages", "OpenFace drops 54%", "OpenFace drops 55%"),
    ("Longer context", "2.5 s -> 10 s: 0.691 -> 0.711 (CEAM)", "1 s -> context: 0.633 -> 0.719"),
    ("Partner features", "Small or no gain (0.704 vs 0.711)", "No gain"),
    ("Data and hardware", "Full NoXi train set, GPUs", "9 conversations, CPU only"),
])
P("Our single-feature results match the official baseline closely, which shows the pipeline is correct, and our "
  "findings (speech transfers, face does not; context helps) agree with the published work.")

# ============================================================ 8
H1("8. Limitations and future work")
B([("Limitations: ", "only 9 conversations; our own test split, not the official test set; 1-second resolution; "
                    "pretrained models frozen (no GPU); only 3 European languages; simple partner modelling."),
   ("Future work: ", "more NoXi conversations (about 20 were prepared); fine-tune the pretrained models on a GPU; "
                     "cross-attention between both speakers; test on Japanese and Chinese (NoXi+J); domain adaptation.")])

# ============================================================ 9
H1("9. Project files")
T(["File / folder", "What it is"], [
    ("src/01 ... 27 .py", "The 27 steps of the project (main code)."),
    ("src/splits.py", "Person-disjoint folds (used by step 27)."),
    ("notebooks/", "Simple Jupyter versions of the 12 main steps, same results, easy to explain."),
    ("data/", "NoXi data and the feature tables (licensed, never upload)."),
    ("reports/", "All result tables (CSV), saved models and figures."),
    ("tools/", "Scripts that build the documents, tables and figures."),
    ("app.py", "Demo app (Streamlit) showing predicted engagement."),
    ("Project_Report_Final.docx/pdf", "Full project report."),
    ("Research_Paper_Draft_v4.docx/pdf", "The research paper in IEEE format."),
    ("Results_Summary_9_Conversations.docx", "All results, sent to the teacher."),
    ("Notebook_Code_Explanation.docx", "Every notebook cell explained."),
    ("Viva_Questions.docx / Syllabus_Viva_Questions.docx", "Question banks (project / syllabus)."),
])

# ============================================================ 10
H1("10. Questions and answers")
QA = [
 ("About the project", [
  ("What is your project about?", "Predicting engagement in conversations from voice and face only, and testing whether it works across languages."),
  ("Why non-verbal and not the words?", "Words are language-specific; tone, loudness, expressions and gaze may carry across languages."),
  ("What is your research question?", "How well can engagement be predicted on unseen conversations, how much is lost in a new language, and which signal transfers better, voice or face?"),
  ("What is the research gap?", "Most engagement work uses one language; cross-language engagement prediction has not been measured systematically."),
  ("Applications?", "Online teaching, video meetings, social robots, interviews, telehealth."),
  ("What is new in your work?", "A systematic 6-direction language test, the voice vs face transfer analysis, the leakage check, and a fair comparison of many model families."),
 ]),
 ("Data and features", [
  ("Which dataset and why?", "NoXi: multilingual conversations with continuous engagement labels; one of very few such datasets."),
  ("How much data?", "9 conversations, 18 people, 17,174 one-second windows (about 2.4 hours)."),
  ("Why only 9 conversations?", "That is what was downloaded and processed. About 20 were prepared later as an extension."),
  ("Which features?", "88 eGeMAPS voice features and 709 OpenFace face features; 5 bookkeeping columns were removed."),
  ("Why remove 5 OpenFace columns?", "Frame number, face id, timestamp, confidence and success describe the recording, not behaviour."),
  ("Why 1-second windows?", "25 frames per second are noisy; one second is stable and still detailed."),
  ("Is the data balanced?", "Roughly: about 5,000-6,500 windows per language."),
  ("Any licence issue?", "NoXi is licensed; the data is never shared or uploaded."),
 ]),
 ("Evaluation", [
  ("What is CCC and why use it?", "Concordance Correlation Coefficient; it checks pattern, scale and offset together. It is the standard metric for NoXi engagement."),
  ("CCC vs Pearson correlation?", "Pearson only checks whether values move together; CCC also punishes shifted or wrongly scaled predictions."),
  ("What is data leakage and how did you find it?", "A random split put neighbouring seconds of the same conversation in training and test. Scores were about 0.90; with whole conversations held out they fell to about 0.62."),
  ("How did you split the data?", "3 folds; each tests on one whole conversation per language and trains on the other 6."),
  ("Why fit the scaler only on training data?", "Otherwise test information leaks into training."),
  ("Could the same person be in training and test?", "Two participants appear in two conversations each. With person-disjoint folds the best model still scores 0.760 with 0% drop."),
  ("How did you prove the improvement is real?", "Wilcoxon test per speaker with bootstrap intervals and Holm correction: better for 15 of 18 speakers, p = 0.006."),
  ("What does +- mean in your results?", "The spread (standard deviation) across the 3 folds; smaller means more stable."),
 ]),
 ("Models", [
  ("Which models did you use?", "Linear Regression, Random Forest, Gradient Boosting, XGBoost, ANN, CNN, SimpleRNN, LSTM, GRU, own Transformer, autoencoders, six pretrained Transformers."),
  ("Which model is best and why?", "Gradient Boosting on voice + w2v-BERT + VideoMAE with context (0.777): strong pretrained features, recent history, and a tree model that suits small data."),
  ("Why do tree models beat deep learning here?", "Only 9 conversations; features are already meaningful; trees ignore noisy features and overfit less."),
  ("Which is best: ANN, CNN or Transformer?", "Nearly tied at 1 s (0.58-0.59). The Transformer is most stable and reaches 0.637 with 10 s of context."),
  ("Explain your ANN.", "797 -> 256 -> 128 -> 1, ReLU, dropout 0.1, Adam 0.001, MSE loss, 30 epochs; chosen from 13 settings."),
  ("Explain your CNN.", "1-D convolutions over the 25 frames: two blocks of two convolutions (32, then 64 filters) with max pooling, then a small head."),
  ("Explain LSTM vs GRU.", "LSTM has 3 gates and a memory cell; GRU has 2 gates and is simpler. Both fix the short memory of a simple RNN."),
  ("Explain your Transformer.", "Each frame -> 64 numbers, learned positional encoding, 2 encoder blocks (4-head self-attention + feed-forward, add & normalise), average, head."),
  ("What is self-attention?", "Each time step scores how relevant every other step is and combines them."),
  ("Why positional encoding?", "Attention has no sense of order; positions are added."),
  ("What did the autoencoder do?", "Compressed 797 features to 32 without labels; a predictor then used the 32 numbers (0.564-0.577)."),
  ("What transfer learning did you do?", "A CNN trained on 2 languages was adapted to the 3rd; fine-tuning with 10% of one conversation gave 0.569 vs 0.230 from scratch."),
  ("Which pretrained Transformers and why?", "XLM-RoBERTa, w2v-BERT 2.0, CLIP, DINOv2, Swin, VideoMAE, to test whether knowledge from huge models helps. Used frozen."),
  ("Why not fine-tune them?", "No GPU, the licence prevents cloud GPUs, and 9 conversations would overfit."),
  ("Which pretrained model was best?", "w2v-BERT 2.0 (speech): 0.631 with no language drop."),
 ]),
 ("Findings", [
  ("How much is lost in a new language?", "29% on average for the baseline; only 1% for the best model."),
  ("Why does voice transfer and face not?", "Facial expression and gaze habits differ between cultures; MultiMediate'24 found the same (OpenFace -54%)."),
  ("Why does context help?", "Engagement builds up over several seconds; the past is informative."),
  ("Why did the partner's features not help?", "Simple concatenation adds noise; published work also found only a small gain."),
  ("Why did French -> English fail (0.092)?", "Only 3 conversations per language, so one unusual speaker can break a single pair."),
  ("Is 0.777 good?", "Yes, above 0.7 is very good agreement; published NoXi systems reach 0.71-0.76, but on a different test set."),
  ("How does your work compare with the papers?", "Single-feature results match the MultiMediate'24 baseline (w2v-BERT 0.631 vs 0.64) and the same patterns hold."),
 ]),
 ("Limitations, implementation and general", [
  ("Limitations?", "Small data, own test split, 1-second resolution, no fine-tuning, 3 European languages."),
  ("Future work?", "More conversations, fine-tuning on a GPU, cross-attention between speakers, Japanese and Chinese (NoXi+J)."),
  ("Which tools?", "Python, pandas, NumPy, scikit-learn, XGBoost, TensorFlow/Keras, Matplotlib, Streamlit."),
  ("Hardware and time?", "CPU only; most models take minutes, the largest up to about an hour."),
  ("Is your work reproducible?", "Yes: fixed random seeds, numbered scripts, saved results; the notebooks reproduce the same numbers."),
  ("What is in the notebooks?", "Simple versions of the 12 main steps that give the same results as the scripts."),
  ("Which syllabus units does the project cover?", "ANN (Unit 1), CNN and transfer learning (2), word embeddings lightly (3), RNN/LSTM/GRU (4), autoencoder and Transformer (5)."),
  ("What is beyond the syllabus?", "Tree models, pretrained Transformers, CCC, leakage and person-disjoint checks, cross-language tests, significance tests."),
  ("Did you use AI tools?", "Answer honestly about how you used them; the course requires ethical, declared use."),
  ("What was your own contribution? (team of 3)", "Prepare a clear answer about who did what."),
 ]),
]
n = 0
for section, qs in QA:
    H2(section)
    for q, a in qs:
        n += 1
        p = doc.add_paragraph(); p.add_run(f"Q{n}. {q}").bold = True
        p.paragraph_format.space_after = Pt(1)
        a_p = doc.add_paragraph(a); a_p.paragraph_format.left_indent = Cm(0.6); a_p.paragraph_format.space_after = Pt(6)

doc.save("Project_Study_Guide.docx")
print(f"saved Project_Study_Guide.docx ({n} questions)")
