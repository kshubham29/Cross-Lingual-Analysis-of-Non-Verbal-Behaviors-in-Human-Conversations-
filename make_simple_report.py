"""Generate a PLAIN-ENGLISH draft of the project report for the student to personalise."""
import os
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING

NAVY = RGBColor(0x1E, 0x2C, 0x3F)
TEAL = RGBColor(0x02, 0x80, 0x90)
RED = RGBColor(0xB0, 0x30, 0x30)
FIG = os.path.join("reports", "figures")

d = Document()
n = d.styles["Normal"]; n.font.name = "Calibri"; n.font.size = Pt(11)
n.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
n.paragraph_format.space_after = Pt(6)


def H(t, l=1):
    h = d.add_heading(t, level=l)
    for r in h.runs:
        r.font.color.rgb = NAVY


def body(t):
    d.add_paragraph(t)


def bullet(t):
    d.add_paragraph(t, style="List Bullet")


def num(t):
    d.add_paragraph(t, style="List Number")


def note(t):
    p = d.add_paragraph()
    r = p.add_run("[YOUR TURN] " + t)
    r.italic = True; r.font.size = Pt(10); r.font.color.rgb = RED


# ---------- COVER / HOW TO USE ----------
p = d.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("Project Report — Plain English Draft"); r.bold = True
r.font.size = Pt(20); r.font.color.rgb = NAVY
p = d.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("A simple draft for you to rewrite in your own words")
r.italic = True; r.font.size = Pt(12); r.font.color.rgb = TEAL

H("How to use this document", 2)
body("This is a DRAFT written in simple language. It is not your final report. To make it your own "
     "work — and to pass the plagiarism and AI checks — do this for each section:")
num("Read the paragraph until you understand it.")
num("Cover it up. Write the same idea from memory, in the way you would say it out loud.")
num("Check that the numbers and facts are still correct.")
num("Add one sentence of your own thoughts wherever you see a [YOUR TURN] note.")
body("Your facts, numbers and findings do not change. Only the wording becomes yours. If you can "
     "explain a section out loud, you can write it in your own words — and that is also exactly what "
     "you need for the viva.")
d.add_page_break()

# ---------- 1 ----------
H("1. Introduction")
body("When people talk, the words are only part of the message. A lot of meaning comes from how "
     "someone looks and sounds — their facial expression, where they look, and the tone of their "
     "voice. These are called non-verbal signals.")
body("One important non-verbal signal is engagement. Engagement means how interested and involved a "
     "person is in a conversation. If a computer could measure engagement automatically, it would be "
     "useful in many places. Online learning platforms could tell when a student stops paying "
     "attention. Virtual assistants and robots could change their behaviour to keep a person "
     "interested. Video call software could tell a speaker whether the audience is listening.")
body("Engagement is not fixed. It goes up and down during a conversation. So we treat it as a number "
     "that changes over time, not as a fixed category like happy or sad.")
body("There is one question that people often ignore. Does a model that predicts engagement still "
     "work if the person speaks a different language? Different cultures show feelings in different "
     "ways, and different languages have different speech patterns. So a model trained on one "
     "language might fail on another. This matters because AI systems are used all over the world "
     "and should work fairly for everyone.")
body("In this project we predict engagement using only non-verbal behaviour — face and voice, never "
     "the words. We use the NoXi dataset, which has conversations in French, English and German. We "
     "then test whether a model trained on one language works on another.")
note("Add why YOU find this topic interesting or useful.")

# ---------- 2 ----------
H("2. Literature Review")
H("2.1 Engagement and non-verbal behaviour", 2)
body("Researchers have studied engagement for a long time, especially in education. D'Mello and "
     "Graesser (2012) looked at how feelings such as engagement, boredom and confusion change while "
     "a person is learning. They showed these states move over time and can be seen in behaviour. "
     "Gupta et al. (2016) built the DAiSEE dataset, which contains videos of students with labels "
     "for engagement, boredom and frustration. Their work showed that engagement can be detected "
     "from video.")
H("2.2 The NoXi dataset and similar datasets", 2)
body("Cafaro et al. (2017) created the NoXi dataset, which we use in this project. It contains real "
     "conversations between two people. One person is an expert on a topic and the other is a "
     "novice who wants to learn. The conversations were recorded in several languages, including "
     "French, English and German, with video and audio. Most importantly, someone labelled how "
     "engaged each person was, 25 times per second.")
body("Okada et al. (2024) later added Japanese and Chinese conversations in a version called NoXi+J. "
     "They used it to study differences between Asian and European non-verbal behaviour. NoXi suits "
     "our project because every language was recorded in the same way, so any difference we find is "
     "about the language and not about the recording setup.")
body("Two other well known datasets are IEMOCAP (Busso et al., 2008) and MELD (Poria et al., 2019). "
     "Both contain conversations with video, audio and text. We do not use them because they are "
     "only in English, so they cannot answer our cross-language question.")
H("2.3 Tools for extracting non-verbal features", 2)
body("To work with face and voice we need to turn them into numbers. Eyben et al. (2010) built "
     "openSMILE, a tool that extracts features from audio. The same group later defined eGeMAPS "
     "(Eyben et al., 2016), a standard set of 88 voice features such as pitch, loudness and voice "
     "quality. For the face, Baltrušaitis et al. (2018) released OpenFace 2.0, which measures facial "
     "muscle movements, gaze direction and head position. NoXi already provides both of these, so we "
     "did not have to extract them ourselves.")
H("2.4 Predicting engagement on NoXi", 2)
body("A series of research competitions called MultiMediate has used NoXi for engagement prediction. "
     "Müller et al. (2022) ran tasks on detecting backchannels and agreement. Müller et al. (2023) "
     "added continuous engagement prediction. Müller et al. (2024) went further and tested whether "
     "models still work across different languages, cultures and settings — which is very close to "
     "our question. The best recent methods use deep learning with attention, such as the Dialogue "
     "Cross-Enhanced Engagement Attention Model (2024). All of them score results using CCC, so we "
     "use the same measure.")
H("2.5 Do models work across languages?", 2)
body("This question has been studied more for emotion than for engagement. Schuller et al. (2010) "
     "tested emotion models on datasets they were not trained on, and performance dropped a lot. "
     "Feraru, Schuller et al. (2015) reviewed emotion recognition across languages and found the "
     "same pattern, especially between languages that are very different from each other. Review "
     "papers (Baltrušaitis et al., 2019; Ramaswamy and Palaniswamy, 2024) also point out that most "
     "datasets come from one culture, so working across cultures is still an open problem.")
note("Mention which paper you found most useful and why.")

# ---------- 3 ----------
H("3. Research Gap")
body("After reading these papers we found three things that are missing:")
num("Most cross-language work is about emotion, not engagement. Very few studies check whether "
    "engagement models work across languages.")
num("Many systems use the words people say. Words are different in every language, so those models "
    "cannot transfer. Few studies use only face and voice.")
num("Even when a dataset has several languages, researchers rarely run a clean test where they train "
    "on one language and test on another.")
body("Our project covers all three. We predict engagement, we use only non-verbal signals, and we "
    "run the cross-language test directly.")

# ---------- 4 ----------
H("4. Problem Statement")
p = d.add_paragraph(); p.paragraph_format.left_indent = Inches(0.3)
r = p.add_run("Given one second of a person's non-verbal behaviour in a conversation — their voice "
              "features and their facial features — predict how engaged they are, and find out "
              "whether a model trained on one language still works on another language.")
r.italic = True
body("Engagement is a number between 0 and 1, so this is a regression problem, not a classification "
     "problem. We measure how good the predictions are using CCC.")

# ---------- 5 ----------
H("5. Objectives")
for o in ["Prepare a set of NoXi conversations in French, English and German, and match the face and "
          "voice features with the engagement labels.",
          "Turn the frame-by-frame data into one-second windows that a model can learn from.",
          "Explore the data to see how engagement is spread out and whether the languages differ.",
          "Train at least two standard machine learning models and compare them.",
          "Build and tune a neural network, and compare it with those models.",
          "Measure how well models transfer between languages.",
          "Check whether voice or face features matter more for engagement."]:
    num(o)

# ---------- 6 ----------
H("6. Dataset")
body("We use the NoXi dataset. Each recording is a real conversation between an expert and a novice, "
     "held over a screen. Because the conversation is natural and not acted, engagement rises and "
     "falls on its own.")
body("We used nine sessions: three in French, three in English and three in German. Each session has "
     "two people, and for each person NoXi gives us:")
bullet("88 voice features (eGeMAPS) — pitch, loudness and voice quality.")
bullet("714 face features (OpenFace 2.0) — facial movements, gaze and head position.")
bullet("An engagement value between 0 and 1, recorded 25 times per second.")
body("We never use the words that were spoken. This is on purpose: it means our method does not "
     "depend on understanding any particular language.")

# ---------- 7 ----------
H("7. Preprocessing")
body("The raw data comes 25 times per second, which is far more detail than we need and quite noisy. "
     "We cleaned it up in these steps:")
num("We opened each session and kept only the files we need: voice features, face features, the "
    "engagement labels and the language.")
num("We cut the three streams to the same length, because they can differ by one or two frames.")
num("We grouped every 25 frames into one window, which is exactly one second.")
num("For each window we took the average of the features and the average engagement.")
num("We removed windows where the engagement label was missing.")
num("We scaled the features so they all sit on a similar range.")
body("This gave us a table with 17,174 rows and 802 features. Each row is one second of behaviour "
     "with its engagement value, and is tagged with the language, the session and whether the person "
     "was the expert or the novice. No values were missing after this.")

# ---------- 8 ----------
H("8. Exploratory Data Analysis")
body("Before training any model we looked at the data to understand it.")
body("The data is fairly balanced. French has 6,568 windows, German 5,630 and English 4,976. Average "
     "engagement is 0.59 for French, 0.59 for German and 0.56 for English, so the three languages "
     "are similar and can be compared fairly.")
body("We found four things worth reporting:")
bullet("Engagement is usually in the middle of the scale, around 0.5. Very bored and very engaged "
       "moments are both rare. This makes sense because people in a conversation are usually paying "
       "at least some attention.")
bullet("Experts are more engaged than novices. The average for experts is 0.66 and for novices 0.51. "
       "This fits the situation, because the expert is doing the explaining.")
bullet("Voice features are linked to engagement about twice as strongly as face features. The "
       "average correlation is 0.39 for voice and 0.19 for face.")
bullet("An ANOVA test showed the difference in engagement between languages is statistically real "
       "(p is less than 0.001), not just random variation.")
note("Say which of these findings surprised you.")

# ---------- 9 ----------
H("9. Methodology")
H("9.1 Baseline models", 2)
body("We first trained three simple models: Linear Regression, Random Forest and Support Vector "
     "Regression. We picked these three because they work in completely different ways, so comparing "
     "them tells us what kind of model suits our data. We split the data 80 percent for training and "
     "20 percent for testing, and scaled the features first. SVR is slow on large data, so we trained "
     "it on a random sample of 4,000 rows.")
H("9.2 Neural network", 2)
body("Our deep learning model is an MLP, built in TensorFlow and Keras. It takes the 802 features, "
     "passes them through two hidden layers of 256 and 128 neurons, and gives one number at the end: "
     "the predicted engagement.")
body("Each part has a job. ReLU is the activation function; it keeps positive values and turns "
     "negative ones into zero, which lets the network learn curved patterns instead of only straight "
     "lines. Dropout switches off some neurons at random while training, which stops the network "
     "memorising the training data. Adam is the algorithm that improves the network, and MSE measures "
     "how far the predictions are from the truth. We also wrote the same model in PyTorch to check "
     "our results.")
H("9.3 Tuning", 2)
body("Instead of guessing the settings, we tried many combinations: dropout of 0.1, 0.3 and 0.5, "
     "learning rates of 0.001 and 0.0005, and two network sizes. We also compared the Adam and SGD "
     "optimisers. To keep this fair we split the data three ways: 60 percent to train, 20 percent to "
     "compare the settings, and 20 percent kept aside. Only the winning setting was tested on that "
     "last part. If we had chosen the settings using the test data, the final score would look better "
     "than it really is.")
H("9.4 Cross-language test", 2)
body("To test transfer we trained on all sessions of one language and tested on all sessions of "
     "another, for every pair. When the training and testing language were the same, we left one "
     "whole conversation out for testing. This matters, because if parts of the same conversation "
     "appear in both training and testing the score becomes far too high.")
H("9.5 How we measure success", 2)
body("We use CCC, which checks whether the predictions follow the true values both in shape and in "
     "actual value. A score of 1 is perfect. We also report Pearson correlation, mean absolute error "
     "and R squared. We cannot use accuracy, because accuracy is for categories and we are "
     "predicting a number.")

# ---------- 10 ----------
H("10. Results")
H("10.1 Baseline models", 2)
body("Random Forest was the best baseline with a CCC of 0.886. SVR came second with 0.827. Linear "
     "Regression was far behind at 0.284, and its R squared was negative (−3.412), which means it "
     "predicted worse than simply guessing the average every time. This tells us the link between "
     "the features and engagement is not a straight line, so simple models are not enough.")
H("10.2 Neural network and tuning", 2)
body("Before tuning, the neural network reached 0.861. After tuning it reached 0.883. The best "
     "settings were dropout 0.1, learning rate 0.001, a 256–128 network and the Adam optimiser.")
body("The tuning also gave a clear pattern. Dropout of 0.1 scored 0.857, dropout of 0.3 scored 0.828, "
     "and dropout of 0.5 dropped to between 0.67 and 0.78. So less dropout works better here, which "
     "suggests our dataset does not need heavy regularisation. Adam beat SGD (0.873 against 0.817). "
     "Our PyTorch version picked the same best settings, which makes us more confident in the result.")
H("10.3 Comparing all models", 2)
body("Random Forest scored 0.886, the tuned network 0.883, the untuned network 0.861, SVR 0.827 and "
     "Linear Regression 0.284.")
H("10.4 Cross-language results", 2)
body("Training and testing on the same language gave an average CCC of 0.551. Training on one "
     "language and testing on another dropped the average to 0.390.")
body("The results are also uneven. A German-trained model did quite well on French (0.665) and on "
     "English (0.412). But a French-trained model did badly on English, scoring only 0.105.")

# ---------- 11 ----------
H("11. Discussion")
body("The results show that engagement really can be predicted from face and voice alone, without "
     "using any words. Inside a single language the models work well.")
body("The main result is what happens across languages. The score falls from 0.551 to 0.390. This is "
     "interesting when we put it next to something we saw in the EDA: average engagement is almost "
     "the same in all three languages (0.56 to 0.59). So people in these three groups are engaged to "
     "a similar degree, but they seem to show it in different ways. The feeling is similar; the "
     "signal is not.")
body("Our finding that voice matters more than face may help explain this. Voice is also the part "
     "most tied to language, since pitch and rhythm patterns differ between languages. So the most "
     "useful signal is also the least transferable one.")
body("Finally, the tuned neural network (0.883) matched but did not beat Random Forest (0.886). This "
     "is normal. On tables of summary features, tree models are very strong and often as good as a "
     "simple neural network. To do better, a model would need to use the order of the windows over "
     "time, which our MLP ignores.")
note("Add your own opinion about why the languages might differ.")

# ---------- 12 ----------
H("12. Limitations")
bullet("We used only nine sessions in three languages, so our results are early findings, not proof.")
bullet("Averaging over one second loses small details that might matter.")
bullet("The cross-language test used only one type of model, so other models might behave differently.")
bullet("The tuned network matched but did not beat the best simple model.")
bullet("We left out the words on purpose, so any engagement shown through what people say is not captured.")

# ---------- 13 ----------
H("13. Conclusion and Future Work")
body("In this project we built a complete system that predicts engagement from non-verbal behaviour "
     "using the NoXi dataset. We prepared the data, explored it, trained three standard models, built "
     "and tuned a neural network, and ran a cross-language test. Random Forest reached a CCC of 0.886 "
     "and the tuned neural network 0.883.")
body("Our main finding is that engagement models only partly transfer between languages. Performance "
     "falls from 0.551 within a language to 0.390 across languages. This suggests that how people "
     "show engagement depends on their language and culture, even though how engaged they are is "
     "similar.")
body("There are several ways to take this further. The clearest next step is an LSTM, which can use "
     "the order of the windows, since engagement builds and fades during a conversation. We could "
     "also add Japanese and Chinese from NoXi+J, try attention-based methods that combine voice and "
     "face more cleverly, test domain adaptation to improve transfer, and build a small demo app.")
note("Write one sentence about what you personally learned from this project.")

d.save("Project_Report_PlainEnglish_DRAFT.docx")
print("Saved Project_Report_PlainEnglish_DRAFT.docx")
