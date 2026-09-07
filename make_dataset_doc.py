"""Generate a Word document describing the dataset (NoXi)."""
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT

doc = Document()
normal = doc.styles["Normal"]
normal.font.name = "Calibri"
normal.font.size = Pt(11)
normal.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
normal.paragraph_format.space_after = Pt(6)
NAVY = RGBColor(0x1E, 0x2C, 0x3F)
TEAL = RGBColor(0x02, 0x80, 0x90)


def heading(text, level):
    h = doc.add_heading(text, level=level)
    for r in h.runs:
        r.font.color.rgb = NAVY


def body(text):
    p = doc.add_paragraph(text)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY


def bullet(text):
    doc.add_paragraph(text, style="List Bullet")


def make_table(headers, rows):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Light Grid Accent 1"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]
        c.text = ""
        run = c.paragraphs[0].add_run(h)
        run.bold = True
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = str(v)
    doc.add_paragraph()


# ===== TITLE =====
for _ in range(3):
    doc.add_paragraph()
t = doc.add_paragraph()
t.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = t.add_run("Dataset Description")
r.bold = True; r.font.size = Pt(28); r.font.color.rgb = NAVY
s = doc.add_paragraph()
s.alignment = WD_ALIGN_PARAGRAPH.CENTER
rs = s.add_run("The NoXi Multilingual Conversation Corpus")
rs.italic = True; rs.font.size = Pt(15); rs.font.color.rgb = TEAL
sub = doc.add_paragraph()
sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
sub.add_run("Project: Cross-Lingual Engagement Prediction from Non-Verbal Behaviour").font.size = Pt(12)
doc.add_page_break()

# ===== 1. OVERVIEW =====
heading("1. What Is the Dataset?", 1)
body("This project uses the NoXi database (\"NOvice-eXpert Interaction\"), a research "
     "corpus of natural, screen-mediated conversations between two people. In each "
     "recorded session one person plays an EXPERT (who knows about a topic) and the "
     "other plays a NOVICE (who is learning about it), and they have a real conversation. "
     "NoXi is designed for studying non-verbal behaviour in conversation, and it was "
     "recorded in several languages, which makes it well suited to a cross-lingual study.")
body("Unlike acted datasets (where people perform emotions on cue), NoXi contains "
     "spontaneous, real interactions, so the behaviour is natural.")

# ===== 2. SOURCE =====
heading("2. Source and Access", 1)
bullet("Name: NoXi database (NOvice-eXpert Interaction).")
bullet("Provider: Human-Centered AI (HCAI) group, distributed for academic research.")
bullet("Access: free for research, obtained after signing a End-User Licence Agreement (EULA).")
bullet("Format: audio-visual recordings plus pre-extracted feature files and annotations.")

# ===== 3. STRUCTURE =====
heading("3. Data Collection and Structure", 1)
body("Each conversation is called a session. A session contains two participants "
     "(expert and novice), and for every participant the dataset provides synchronised "
     "feature streams and annotations sampled at 25 frames per second (25 Hz). Sessions "
     "are grouped by the language in which the conversation took place.")
body("For this project we use a subset of NoXi covering three languages:")
make_table(["Language", "Location", "Sessions used"],
           [["French", "Paris", "3"], ["English", "Nottingham", "3"], ["German", "Augsburg", "3"]])
body("This gives 9 conversations in total, balanced across the three languages.")

# ===== 4. MODALITIES =====
heading("4. Non-Verbal Data Provided", 1)
body("NoXi provides many pre-extracted feature streams. For this project we use the two "
     "standard non-verbal channels plus the engagement label:")
make_table(["Data", "What it captures", "Size"],
           [["eGeMAPS (voice)", "Prosody: pitch, loudness, voice quality", "88 features / frame"],
            ["OpenFace 2.0 (face)", "Facial action units, gaze, head pose", "714 features / frame"],
            ["Engagement label", "How engaged the person is (0 to 1)", "1 value / frame"],
            ["Language annotation", "Language of the conversation", "1 per session"]])
body("Important: we use only NON-VERBAL information (voice tone and facial behaviour). "
     "We do NOT use the words that were spoken, so the analysis is language-independent.")

# ===== 5. PROCESSED TABLE =====
heading("5. Our Processed Feature Table", 1)
body("The raw features arrive 25 times per second, which is too fine-grained for "
     "modelling. We therefore group the frames into one-second windows (25 frames each). "
     "For every window we take the average of the features and the average engagement, "
     "so each window becomes ONE ROW in a table:")
make_table(["Property", "Value"],
           [["Rows (samples)", "17,174 windows (1 second each)"],
            ["Total columns", "806"],
            ["Feature columns", "802 (88 voice + 714 face)"],
            ["Target column", "engagement (0 to 1)"],
            ["Tag columns", "language, session, role"]])
body("Column meaning: voice_0 ... voice_87 are the voice features; face_0 ... face_713 "
     "are the face features; engagement is the value we predict; language / session / role "
     "identify where each window came from (role = expert or novice).")

# ===== 6. STATISTICS =====
heading("6. Dataset Statistics", 1)
body("The data is fairly balanced across the three languages:")
make_table(["Language", "Windows", "Average engagement"],
           [["French", "6,568", "0.59"], ["German", "5,630", "0.59"], ["English", "4,976", "0.56"]])
body("Total: 17,174 windows. Average engagement values are similar across languages "
     "(0.56 to 0.59), which shows the label is comparable between them.")

# ===== 7. TARGET =====
heading("7. Target Variable: Engagement", 1)
body("The value we predict is engagement, a continuous number between 0 (not engaged) "
     "and 1 (fully engaged). Because the target is continuous, this is a REGRESSION "
     "problem, not classification. We measure model quality with the Concordance "
     "Correlation Coefficient (CCC), the standard metric for engagement (1.0 = perfect).")

# ===== 8. SPLITTING =====
heading("8. How the Data Is Split", 1)
bullet("For baseline models: 80% of the windows are used for training and 20% for testing.")
bullet("For the cross-lingual experiment: the model is trained on all sessions of one "
       "language and tested on all sessions of another (e.g. train on French, test on German).")
bullet("Within a language, leave-one-session-out is used so training and testing never "
       "share the same conversation (this keeps the evaluation honest).")

# ===== 9. WHY =====
heading("9. Why This Dataset Suits the Project", 1)
bullet("It contains real conversations, matching the project title.")
bullet("It is multilingual (French, English, German), enabling the cross-lingual study.")
bullet("It provides both voice and face non-verbal features, ready to use.")
bullet("It includes continuous engagement labels, exactly the target we need.")
bullet("All languages follow the same recording protocol, so language differences are "
       "not confounded with different recording conditions.")

doc.save("Dataset_Description.docx")
print("Saved Dataset_Description.docx")
