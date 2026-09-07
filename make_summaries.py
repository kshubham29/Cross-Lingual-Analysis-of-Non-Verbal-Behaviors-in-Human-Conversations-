"""Generate a simple 'Paper Summaries' Word document for viva revision."""
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

doc = Document()
n = doc.styles["Normal"]; n.font.name = "Calibri"; n.font.size = Pt(11)
NAVY = RGBColor(0x1E, 0x2C, 0x3F); TEAL = RGBColor(0x02, 0x80, 0x90)

# title
t = doc.add_paragraph(); t.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = t.add_run("Research Paper Summaries"); r.bold = True; r.font.size = Pt(24); r.font.color.rgb = NAVY
s = doc.add_paragraph(); s.alignment = WD_ALIGN_PARAGRAPH.CENTER
rs = s.add_run("Simple summaries for viva revision — Cross-Lingual Engagement Prediction")
rs.italic = True; rs.font.size = Pt(12); rs.font.color.rgb = TEAL
doc.add_paragraph()

papers = [
 ("1. The NoXi Database (Cafaro, 2017)", "MY DATASET",
  "This paper created NoXi, the dataset I use. They recorded about 84 real conversations "
  "between an expert and a novice in 7 languages (~25 hours of video and audio). The important "
  "part is they labelled engagement continuously, so we know how interested each person is "
  "moment by moment. Before this, most datasets were acted and single-language, so NoXi was a "
  "big step because it is real, natural and multilingual.",
  "It gives me my conversations, my face + voice data, and my engagement labels."),
 ("2. MultiMediate'24 (Muller, 2024)", "MY EXACT TASK",
  "This is a research challenge that predicts engagement on NoXi, exactly my task. It tests "
  "whether models work across different languages, cultures and settings, using deep-learning "
  "attention-based fusion of audio and video, scored with CCC.",
  "It proves engagement prediction is hard across cultures, which supports my whole idea."),
 ("3. NoXi+J (Okada, 2024)", "CROSS-CULTURAL",
  "This extends NoXi by adding Japanese and Chinese conversations, to study differences in "
  "non-verbal behaviour between Asian and European people.",
  "It supports my cross-lingual angle by showing culture affects non-verbal behaviour."),
 ("4. eGeMAPS (Eyben, 2016)", "MY VOICE FEATURES",
  "This paper defined a standard set of 88 voice features (pitch, loudness, voice quality) for "
  "affective computing research.",
  "These are the exact voice features I use in my project."),
 ("5. OpenFace 2.0 (Baltrusaitis, 2018)", "MY FACE FEATURES",
  "This is an open-source tool that extracts facial features from video: action units "
  "(expressions), gaze direction and head pose.",
  "This is the tool that provides my facial features."),
 ("6. Cross-Corpus Emotion (Schuller, 2010)", "SUPPORTS MY FINDING",
  "This paper showed that emotion-recognition models perform much worse when tested on a "
  "different dataset than the one they were trained on.",
  "It backs up my finding that models do not transfer well."),
 ("7. Cross-Language Emotion (Feraru, 2015)", "MY MOTIVATION",
  "This surveys how emotion recognition works across different languages and found that it gets "
  "worse across languages, especially very different ones.",
  "This is basically my motivation, but for emotion instead of engagement."),
 ("8. DAiSEE (Gupta, 2016)", "ENGAGEMENT DATASET",
  "This introduced a dataset for recognising engagement, boredom and frustration in students "
  "watching e-learning videos, with deep-learning baselines.",
  "It shows engagement recognition is an important research problem."),
 ("9. IEMOCAP (Busso, 2008)", "BACKGROUND",
  "A classic multimodal dataset of emotional conversations with audio, video, text and motion "
  "capture. It is a standard benchmark in affective computing.",
  "Good background on how multimodal conversation datasets are built (I don't use it)."),
 ("10. Multimodal ML Survey (Baltrusaitis, 2019)", "MULTIMODAL BACKGROUND",
  "A survey that organises how different types of data (voice, face, text) can be combined, "
  "called multimodal machine learning.",
  "It helped me understand what 'multimodal' means and how to combine voice and face."),
 ("11. openSMILE (Eyben, 2010)", "FEATURE TOOL",
  "This is the open-source toolkit that extracts audio features quickly. It is the tool behind "
  "the eGeMAPS voice features.",
  "It is how the audio features in my project are actually extracted."),
 ("12. MELD (Poria, 2019)", "BACKGROUND",
  "A multimodal dataset for emotion recognition in multi-party conversations, using audio, "
  "video and text.",
  "Useful background, but English-only so not directly usable for my cross-lingual work."),
 ("13. Affective States (D'Mello, 2012)", "ENGAGEMENT IS CONTINUOUS",
  "This studied how affective states like engagement, boredom and confusion change over time "
  "during learning.",
  "It made me realise engagement is continuous and changes over time, which is why I predict "
  "it as a number, not a category."),
 ("14. Multimodal Emotion Review (Ramaswamy, 2024)", "RECENT REVIEW",
  "A recent review of multimodal emotion recognition methods, trends and challenges. It notes "
  "that most datasets are culture-specific.",
  "It points to my gap: cross-cultural generalisation is still an open challenge."),
 ("15. MultiMediate'22 (Muller, 2022)", "EARLIER CHALLENGE",
  "An earlier challenge on backchannel detection and agreement estimation in group interactions "
  "using NoXi.",
  "It shows the field has been building up to engagement estimation over the years."),
]

for title, tag, summary, relevance in papers:
    h = doc.add_paragraph()
    rh = h.add_run(title); rh.bold = True; rh.font.size = Pt(13); rh.font.color.rgb = NAVY
    tg = h.add_run(f"   [{tag}]"); tg.italic = True; tg.font.size = Pt(10); tg.font.color.rgb = TEAL
    doc.add_paragraph(summary)
    wp = doc.add_paragraph()
    wr = wp.add_run("Why it matters to my project: "); wr.bold = True
    wp.add_run(relevance)
    doc.add_paragraph()

# closing tip
doc.add_page_break()
tp = doc.add_paragraph()
tr = tp.add_run("How to explain any paper (the simple formula)"); tr.bold = True; tr.font.size = Pt(13); tr.font.color.rgb = NAVY
doc.add_paragraph("For any paper, just say: (1) what it did, (2) what it found, and (3) why it "
                  "matters to my project. That is enough to explain it confidently.")
doc.add_paragraph("30-second overall answer: \"I read papers across three areas - my dataset "
                  "(NoXi) and task (engagement, MultiMediate), my feature tools (eGeMAPS, "
                  "OpenFace), and cross-lingual transfer studies (Schuller, Feraru). Together "
                  "they show my gap: cross-lingual engagement prediction from only non-verbal "
                  "cues has not been done.\"")

doc.save("Paper_Summaries.docx")
print("Saved Paper_Summaries.docx")
