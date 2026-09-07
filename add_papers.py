"""Append 9 more papers to the existing Literature_Review.xlsx (keeps current rows)."""
import openpyxl
from openpyxl.styles import Font, Alignment, Border, Side

wb = openpyxl.load_workbook("Literature_Review.xlsx")
ws = wb.active

thin = Side(style="thin", color="BBBBBB")
border = Border(left=thin, right=thin, top=thin, bottom=thin)
body = Font(name="Arial", size=9)
wrap = Alignment(wrap_text=True, vertical="top")

# each paper as a dict; columns filled in the same order as the sheet
NEW = [
 dict(doi="arXiv:2308.08256", title="MultiMediate'23: Engagement Estimation and Bodily Behaviour Recognition",
   apa="Muller, P., et al. (2023). MultiMediate'23. ACM Multimedia.",
   authors="Muller, Balazia, et al.", year=2023, venue="ACM Multimedia", index="Scopus",
   obj="Benchmark continuous engagement estimation and bodily behaviour recognition on NoXi.",
   data="NoXi, MPIIGroupInteraction", n="Challenge sets", modality="video + audio",
   inp="Multimodal features", feat="Audio + visual behaviour", method="Deep learning fusion", metric="CCC",
   out="Provided engagement estimation benchmark and baselines on NoXi.",
   gap="Continuous engagement estimation still hard.", fut="Better temporal models.",
   link="https://arxiv.org/abs/2308.08256", other="",
   rem="another MultiMediate challenge on NoXi engagement really close to my task good to show the field is active"),
 dict(doi="IJCAI 2024", title="Dialogue Cross-Enhanced Central Engagement Attention Model",
   apa="Yu, J., et al. (2024). Dialogue Cross-Enhanced Central Engagement Attention Model. IJCAI.",
   authors="Yu, et al.", year=2024, venue="IJCAI", index="Scopus",
   obj="Improve real-time engagement estimation by aligning both speakers' behaviour.",
   data="NoXi", n="NoXi sessions", modality="video + audio",
   inp="Multimodal features", feat="Audio + visual", method="Cross-attention deep model", metric="CCC",
   out="State-of-the-art engagement estimation on NoXi.",
   gap="Real-time engagement modelling.", fut="Faster real-time models.",
   link="https://www.ijcai.org/proceedings/2024/0353.pdf", other="",
   rem="shows the advanced deep learning way to do my task uses attention my LSTM idea is simpler but same goal"),
 dict(doi="arXiv:2508.14448", title="Generalizable Engagement Estimation via Domain Prompting and Parallel Attention",
   apa="(2025). Generalizable Engagement Estimation via Domain Prompting and Parallel Attention. arXiv:2508.14448.",
   authors="et al.", year=2025, venue="arXiv", index="Not indexed (preprint)",
   obj="Make engagement models generalise across domains and cultures.",
   data="NoXi", n="NoXi sessions", modality="video + audio",
   inp="Multimodal features", feat="Audio + visual", method="Domain prompting + parallel attention", metric="CCC",
   out="Improved cross-domain engagement generalisation.",
   gap="Cross-cultural engagement generalisation.", fut="Stronger domain adaptation.",
   link="https://arxiv.org/abs/2508.14448", other="",
   rem="very recent 2025 shows my exact problem cross culture engagement is still being worked on so my project is relevant"),
 dict(doi="arXiv:2308.01526", title="Data Augmentation for Human Behavior Analysis in Multi-Person Conversations",
   apa="(2023). Data Augmentation for Human Behavior Analysis in Multi-Person Conversations. arXiv:2308.01526.",
   authors="et al.", year=2023, venue="arXiv / ACM MM workshop", index="Scopus",
   obj="Use data augmentation to improve behaviour analysis on NoXi.",
   data="NoXi", n="NoXi sessions", modality="video + audio",
   inp="Multimodal features", feat="Audio + visual", method="Data augmentation + deep learning", metric="CCC / accuracy",
   out="Augmentation improved engagement/behaviour prediction.",
   gap="Limited training data for behaviour analysis.", fut="More augmentation strategies.",
   link="https://arxiv.org/abs/2308.01526", other="",
   rem="useful trick if my data is small i could try augmentation to improve results good idea for future work"),
 dict(doi="LREC 2018 workshop", title="Expert-Novice Interaction: Annotation and Analysis",
   apa="(2018). Expert-Novice Interaction: Annotation and Analysis. LREC Workshop.",
   authors="et al.", year=2018, venue="LREC Workshop", index="Scopus",
   obj="Analyse how expert-novice interactions are annotated in NoXi.",
   data="NoXi", n="NoXi subset", modality="video + audio",
   inp="Annotations", feat="Engagement, roles", method="Annotation analysis", metric="N/A",
   out="Insights into how NoXi engagement is annotated.",
   gap="Understanding annotation quality.", fut="Better annotation methods.",
   link="http://lrec-conf.org/workshops/lrec2018/W20/pdf/15_W20.pdf", other="",
   rem="helps me understand how the engagement labels in my dataset were made good for explaining my data"),
 dict(doi="arXiv:2006.11477", title="wav2vec 2.0: A Framework for Self-Supervised Learning of Speech Representations",
   apa="Baevski, A., et al. (2020). wav2vec 2.0. NeurIPS.",
   authors="Baevski, Zhou, Mohamed, Auli", year=2020, venue="NeurIPS", index="Scopus",
   obj="Learn speech representations without labels (self-supervised).",
   data="LibriSpeech", n="960 hours", modality="signal (audio)",
   inp="Raw audio", feat="Learned speech embeddings", method="Self-supervised transformer", metric="Word error rate",
   out="Strong speech features with little labelled data.",
   gap="Needed labelled data for speech features.", fut="Use embeddings for downstream tasks.",
   link="https://arxiv.org/abs/2006.11477", other="",
   rem="noxi gives w2v-bert embeddings which are based on this good to know where those extra features come from"),
 dict(doi="arXiv:1706.03762", title="Attention Is All You Need",
   apa="Vaswani, A., et al. (2017). Attention Is All You Need. NeurIPS.",
   authors="Vaswani, et al.", year=2017, venue="NeurIPS", index="Scopus",
   obj="Introduce the Transformer architecture based on attention.",
   data="WMT translation", n="Large", modality="text",
   inp="Sequences", feat="Self-attention", method="Transformer", metric="BLEU",
   out="Transformer became the basis of modern deep learning.",
   gap="RNNs were slow and forgot long context.", fut="Apply attention everywhere.",
   link="https://arxiv.org/abs/1706.03762", other="",
   rem="the transformer that the newer engagement methods use foundational i mention it as an advanced option"),
 dict(doi="10.1162/neco.1997.9.8.1735", title="Long Short-Term Memory (LSTM)",
   apa="Hochreiter, S., & Schmidhuber, J. (1997). Long Short-Term Memory. Neural Computation, 9(8), 1735-1780.",
   authors="Hochreiter, Schmidhuber", year=1997, venue="Neural Computation", index="Scopus + WoS",
   obj="Introduce a recurrent network that remembers long sequences.",
   data="N/A", n="N/A", modality="signal/sequence",
   inp="Sequences", feat="Memory cells", method="LSTM recurrent network", metric="N/A",
   out="LSTM can learn long-term patterns in sequences.",
   gap="Plain RNNs forget long context.", fut="Sequence modelling tasks.",
   link="https://doi.org/10.1162/neco.1997.9.8.1735", other="",
   rem="this is the model i plan to use for my improved version because engagement changes over time so an lstm fits"),
 dict(doi="10.1023/A:1010933404324", title="Random Forests",
   apa="Breiman, L. (2001). Random Forests. Machine Learning, 45(1), 5-32.",
   authors="Breiman", year=2001, venue="Machine Learning", index="Scopus + WoS",
   obj="Introduce the Random Forest ensemble method.",
   data="Various", n="N/A", modality="tabular",
   inp="Features", feat="Decision trees", method="Ensemble of trees", metric="Accuracy/error",
   out="Random Forest is a strong, robust general model.",
   gap="Single trees overfit.", fut="Widely used baseline.",
   link="https://doi.org/10.1023/A:1010933404324", other="",
   rem="this is my best baseline model random forest good to cite the original paper for the model i actually use"),
]

start = ws.max_row + 1
for k, p in enumerate(NEW):
    sno = start + k - 1  # continue S.no numbering (row 1 header, so S.no = row-1)
    vals = [sno, p["doi"], p["title"], p["apa"], p["authors"], p["year"], p["venue"],
            p["index"], p["obj"], p["data"], p["n"], p["modality"], p["inp"], p["feat"],
            p["method"], p["metric"], p["out"], p["gap"], p["fut"], p["link"], p["other"],
            "[add your Drive link]", "[your name / roll no.]", p["rem"]]
    for j, v in enumerate(vals, 1):
        c = ws.cell(row=start + k, column=j, value=v)
        c.font = body; c.alignment = wrap; c.border = border

wb.save("Literature_Review.xlsx")
print(f"Added {len(NEW)} papers. Sheet now has {ws.max_row - 1} papers total.")
