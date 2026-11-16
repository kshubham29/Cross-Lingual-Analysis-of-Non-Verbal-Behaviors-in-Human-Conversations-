"""Writes Research_Paper_Draft_v4.docx: the v3 content in the IEEE two-column
layout of Research_Paper_Draft_v2.docx (US Letter, 0.75 in margins, one-column
title block, two-column body). Every paragraph and table is cloned from a v2
example of the same kind, so fonts, sizes and spacing are exactly v2's.
The text, numbers and references come from tools/make_paper_v3.py.
Run from the project folder: python tools/make_paper_v4.py"""
import copy
import re
import pandas as pd
from docx import Document
from docx.shared import Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

SRC = open("tools/make_paper_v3.py", encoding="utf-8").read()
d = Document("Research_Paper_Draft_v2.docx")
body = d.element.body
el = list(body)
E = {k: copy.deepcopy(el[i]) for k, i in dict(title=0, authors=1, affil=2, email=3, abstract=4, index=5, colbreak=6,
                                               h1=7, text=8, h2=12, tabnum=25, tabtitle=26, table=27, blank=28,
                                               lead=40, ref=92).items()}
for x in el[:-1]:                 # keep only the final sectPr (the two-column body section)
    body.remove(x)


def put(x):
    body.insert(len(body) - 1, x)
    return x


def set_runs(p, texts):
    """Keep the first len(texts) runs of a cloned paragraph and give them new text."""
    runs = p.findall(qn("w:r"))
    for r in runs[len(texts):]:
        p.remove(r)
    for r, t in zip(runs, texts):
        ts = r.findall(qn("w:t"))
        for extra in ts[1:]:
            r.remove(extra)
        tnode = ts[0] if ts else r.append(OxmlElement("w:t")) or r.findall(qn("w:t"))[0]
        tnode.text = t
        tnode.set(qn("xml:space"), "preserve")
    return p


def renum(t):   # v3 text was written for 43 references; entry [15] was dropped there
    return re.sub(r"\[(\d+)\]", lambda m: f"[{int(m.group(1)) - 1 if int(m.group(1)) > 15 else m.group(1)}]", t)


class W:
    """Writer with the helper names used by the v3 content."""
    seen_index = False

    @staticmethod
    def para(text, bold_lead=None, align=None):
        text = renum(text)
        if bold_lead and bold_lead.startswith("Abstract"):
            put(set_runs(copy.deepcopy(E["abstract"]), ["Abstract", "—" + text]))
        elif bold_lead and bold_lead.startswith("Index Terms"):
            put(set_runs(copy.deepcopy(E["index"]), ["Index Terms", "—" + text]))
            put(copy.deepcopy(E["colbreak"]))             # end of the one-column title block
        elif bold_lead:
            put(set_runs(copy.deepcopy(E["lead"]), [bold_lead, text]))
        else:
            put(set_runs(copy.deepcopy(E["text"]), [text]))

    @staticmethod
    def center(text, size=10.5, bold=False, italic=False):
        kind = "title" if size >= 14 else "affil" if italic else "email" if "@" in text else "authors"
        put(set_runs(copy.deepcopy(E[kind]), [text]))

    @staticmethod
    def H1(t):
        num, _, rest = t.partition(" ")
        put(set_runs(copy.deepcopy(E["h1"]), [f"{num} {rest.upper()}" if rest else t.upper()]))

    @staticmethod
    def H2(t):
        put(set_runs(copy.deepcopy(E["h2"]), [t]))

    @staticmethod
    def table(num, title, header, rows):
        if len(header) == 8:      # Table IV: keep the better head so it fits one column
            best = lambda r: r[3] if float(r[3].split()[0]) >= float(r[4].split()[0]) else r[4]
            header = ["Model", "Input", "CCC (best head)", "Within", "Cross", "Drop"]
            rows = [(r[0], r[1], best(r), r[5], r[6], r[7]) for r in rows]
        put(set_runs(copy.deepcopy(E["tabnum"]), [f"TABLE {num}"]))
        put(set_runs(copy.deepcopy(E["tabtitle"]), [title.upper()]))
        tbl = copy.deepcopy(E["table"])
        trs = tbl.findall(qn("w:tr"))
        h_tr, b_tr = trs[0], trs[1]
        for tr in trs:
            tbl.remove(tr)
        total = sum(int(g.get(qn("w:w"))) for g in tbl.find(qn("w:tblGrid")))
        n = len(header)
        widths = [total // n] * n
        grid = tbl.find(qn("w:tblGrid"))
        for g in list(grid):
            grid.remove(g)
        for w in widths:
            g = OxmlElement("w:gridCol"); g.set(qn("w:w"), str(w)); grid.append(g)

        def row(tmpl, values):
            tr = copy.deepcopy(tmpl)
            tcs = tr.findall(qn("w:tc"))
            first, other = tcs[0], tcs[1] if len(tcs) > 1 else tcs[0]
            for tc in tcs:
                tr.remove(tc)
            for i, v in enumerate(values):
                tc = copy.deepcopy(first if i == 0 else other)
                tc.find(qn("w:tcPr")).find(qn("w:tcW")).set(qn("w:w"), str(widths[i]))
                set_runs(tc.find(qn("w:p")), [str(v)])
                tr.append(tc)
            return tr

        tbl.append(row(h_tr, header))
        for r in rows:
            tbl.append(row(b_tr, r))
        put(tbl)
        put(copy.deepcopy(E["blank"]))

    @staticmethod
    def figure(path, caption, *_):
        pic = d.add_paragraph()                         # added before the final sectPr, i.e. in order
        pic.add_run().add_picture(path, width=Cm(8.2))
        pic.alignment = WD_ALIGN_PARAGRAPH.CENTER
        put(set_runs(copy.deepcopy(E["tabtitle"]), [caption]))

    @staticmethod
    def note(text):
        put(set_runs(copy.deepcopy(E["affil"]), [text]))


# ---- run the v3 content with the IEEE writer ----
content = SRC.split("# ---------------- numbers from the result files ----------------")[1].split("# ---------------- References")[0]
content = content.replace('p = doc.add_paragraph(); r = p.add_run("[Draft v3 - rewrite in your own words before submission; delete this line]")\n'
                          'r.italic = True; r.font.size = Pt(9)\n',
                          'note("[Draft v4 - rewrite in your own words before submission; delete this line]")\n')
content = content.replace('doc.add_picture("reports/figures/report_cross_lingual.png", width=Cm(10))\n'
                          'doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER\ncenter(',
                          'figure("reports/figures/report_cross_lingual.png", ')
assert "doc." not in content, "unexpected direct document call in the v3 content"
R = lambda f: pd.read_csv(f"reports/{f}.csv")
ns = dict(pd=pd, R=R, f3=lambda x: f"{x:.3f}", pm=lambda m, s: f"{m:.3f} ± {s:.3f}", pc=lambda x: f"{max(x, 0):.0f}%",
          para=W.para, center=W.center, H1=W.H1, H2=W.H2, table=W.table, figure=W.figure, note=W.note)
exec(content, ns)

# ---- references ----
refs_src = "refs = [" + SRC.split("refs = [", 1)[1].split("\n]\n", 1)[0] + "\n]\n"
exec(refs_src, ns)
W.H1("References")
for i, ref in enumerate(ns["refs"], 1):
    put(set_runs(copy.deepcopy(E["ref"]), [f"[{i}]\t{ref}"]))

d.save("Research_Paper_Draft_v4.docx")
print(f"saved Research_Paper_Draft_v4.docx ({len(ns['refs'])} references)")
