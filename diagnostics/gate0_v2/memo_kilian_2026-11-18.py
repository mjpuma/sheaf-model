#!/usr/bin/env python3
"""One-page memo to Kilian: four-crop status on develop-substitution-claude.

    python3 diagnostics/gate0_v2/memo_kilian_2026-11-18.py
"""
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt

HERE = Path(__file__).resolve().parent
OUT = HERE / "memo_kilian_2026-11-18.docx"
FIG = HERE / "gate0_v2_fourcrop.png"

doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Inches(8.5), Inches(11)
sec.left_margin = sec.right_margin = Inches(0.7)
sec.top_margin = sec.bottom_margin = Inches(0.55)
normal = doc.styles["Normal"]
normal.font.name = "Calibri"
normal.font.size = Pt(9.5)
normal.paragraph_format.space_after = Pt(2.5)
normal.paragraph_format.line_spacing = 1.0


def para(text="", bold_lead=None, size=None, after=None, style=None):
    p = doc.add_paragraph(style=style)
    if bold_lead:
        r = p.add_run(bold_lead)
        r.bold = True
        if size:
            r.font.size = Pt(size)
    r = p.add_run(text)
    if size:
        r.font.size = Pt(size)
    if after is not None:
        p.paragraph_format.space_after = Pt(after)
    return p


def heading(text):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.bold = True
    r.font.size = Pt(10.5)
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(1.5)


para("Agrimate develop-substitution-claude: four-crop status", bold_lead=None, size=13, after=1).runs[0].bold = True
para("To: Kilian Kuhla   cc: Christian   From: Michael Puma   18 November 2026", size=9, after=5)

para("I'm running develop-substitution-claude (a copy of develop-consumers at f492df9, no code changes) "
     "with one consumer per region, baseline 2007–2009, your suggested settings, and the parameter files "
     "you sent this week. All four crops start and run 2000–2012 in 3–4.5 minutes. Storage and trade "
     "balance at every step, nothing goes negative, and repeat runs are identical.")

pic = doc.add_paragraph()
pic.alignment = WD_ALIGN_PARAGRAPH.CENTER
pic.paragraph_format.space_after = Pt(0)
pic.add_run().add_picture(str(FIG), width=Inches(6.6))
cap = para("World market price index as in plot_wm_price_timeseries (src/plot.jl): monthly mean "
           "cross-border transaction price weighted by export volume, same for all crops. Shaded: July–June "
           "2007/08 and 2010/11. Red ticks: half-month steps where cross-border trade is below 10% of its "
           "2000–05 level. Rice and maize are clipped at 3.", size=8, after=5)
cap.runs[0].italic = True

para("2007/08 1.361 (published 1.361), 2010/11 1.213 (1.219), May 2008 peak 2.21 (2.22). World stocks "
     "within 0.05% of your run through 2010; 2012 is 0.8% high, mostly Argentina.", bold_lead="Wheat matches your published run closely. ")
para("There is nothing to compare against yet. Soybean looks reasonable. Maize peaks in October 2011 "
     "with the US almost the only seller. Rice is the problem: no 2008 spike, and cross-border trade "
     "nearly stops in 15 half-month steps between 2006 and 2012. Then a few small trades set the world "
     "price (June 2010: Southeast Asia almost the only seller, at 12–69× baseline).",
     bold_lead="Rice, maize, soybean. ")

heading("Questions")
qs = [
    "Rice: have you seen this in your runs? With India, Vietnam and Thailand restricted in 2008 I "
    "expected a spike. Is the Thailand restriction (May 2008 – Oct 2009) intended? And is rice on a "
    "paddy basis (world consumption comes out at 664 Mt)?",
    "Do you have runs for rice, maize or soybean on these inputs that I could compare against?",
    "Besides A_c, a few STU and A_d values changed from the earlier package (e.g. Egypt wheat STU "
    "0.276 → 0.229, Paraguay rice STU 1.22 → 0.23). Did any of the other input files change too?",
    "Tiny changes move the crisis numbers. One consumer vs. two identical half-size consumers gives a "
    "2007/08 wheat ratio of 1.351–1.360 and a peak of 2.19–2.21. How do you judge whether two runs agree?",
    "Most tests in src/AgrimateModel/test fail against the current code (older function signatures). "
    "Is there a newer set?",
]
for q in qs:
    p = para(q, style="List Number", after=1.5)

heading("Next steps")
steps = [
    "Rice first: rerun with export restrictions off, and with harvest anomalies off, to see which one "
    "causes the trade collapse and the missing 2008 spike.",
    "Compare each crop with the observed deflated prices your plot code uses (US HRW wheat, US maize, "
    "Thai 5% rice; World Bank soybeans for soybean).",
    "Agree Gate 0 pass rules that allow for run-to-run spread (several equivalent runs, report the range).",
    "Then start Gate 1, substitution between wheat, rice and maize, on this branch. I'll send the design "
    "questions separately.",
]
for s in steps:
    para(s, style="List Bullet", after=1.5)

doc.save(OUT)
print(OUT)
