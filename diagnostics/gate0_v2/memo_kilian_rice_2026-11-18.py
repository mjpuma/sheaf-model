#!/usr/bin/env python3
"""Follow-up memo: rice on four shock settings.

    python3 diagnostics/gate0_v2/memo_kilian_rice_2026-11-18.py
"""
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt

HERE = Path(__file__).resolve().parent
OUT = HERE / "memo_kilian_rice_2026-11-18.docx"
FIG = HERE / "gate0_v2_rice_scenarios.png"

doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Inches(8.5), Inches(11)
sec.left_margin = sec.right_margin = Inches(0.7)
sec.top_margin = sec.bottom_margin = Inches(0.55)
normal = doc.styles["Normal"]
normal.font.name = "Calibri"
normal.font.size = Pt(10)
normal.paragraph_format.space_after = Pt(3)
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
    r.font.size = Pt(11)
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(2)


para("Rice follow-up: the problem is there with no shocks", size=13, after=1).runs[0].bold = True
para("To: Kilian Kuhla   cc: Christian   From: Michael Puma   18 November 2026", size=9, after=6)

para("Following the four-crop note: I reran rice on your 18 November inputs four ways, "
     "to see whether the export bans cause the missing 2008 spike and the later collapse. "
     "They don't. Rice misbehaves with no shocks at all.")

pic = doc.add_paragraph()
pic.alignment = WD_ALIGN_PARAGRAPH.CENTER
pic.paragraph_format.space_after = Pt(1)
pic.add_run().add_picture(str(FIG), width=Inches(6.7))
cap = para("Top: world rice price, same index as in your plot_wm_price_timeseries, clipped at 4. "
           "Brown is Thai 5% (World Bank, deflated, scaled to the full run's 2000–2012 mean). "
           "Shaded: July–June 2007/08 and 2010/11. Bottom: Southeast Asia supplier storage. "
           "Harvest there is 187 Mt/yr.", size=8, after=6)
cap.runs[0].italic = True

para("spikes to 11 in March 2002 and falls apart after 2008 (2010/11 ratio 0.42). "
     "Cross-border trade roughly doubles by 2012, against a 38 Mt/yr baseline.",
     bold_lead="No shocks (grey). ")
para("looks much the same: 2007/08 ratio 0.82, and a May 2010 spike to 12.",
     bold_lead="Harvest shocks only (blue). ")
para("does lift prices, but not into a 2008 spike. It peaks at 68 in September 2011 "
     "(off the chart), and 2010/11 comes out at 0.24.",
     bold_lead="Export restrictions only (orange). ")
para("is the run in the earlier figure: 2007/08 ratio 0.99 against 1.89 observed, "
     "and 2010/11 at 0.29 against 1.77.",
     bold_lead="Both (red). ")

para("The bottom panel is the same in every run. Southeast Asia is the main exporter and holds "
     "almost nothing: the stock is empty most steps, and peaks around 15–20 Mt. When it does sell "
     "abroad the price jumps (up to 48× baseline in the no-shock run). Its stock target ψ is 0.14 "
     "and its import share A_d is 0.19.")

heading("Questions")
for q in [
    "Does your own rice run look like the red line, or closer to the brown observed line?",
    "Is Southeast Asia meant to hold this little? A 187 Mt harvest with a stock that is usually empty "
    "seems wrong, and it happens before any shock.",
    "Two smaller ones from before: is rice on a paddy basis (world use comes out at 664 Mt), and is the "
    "Thailand restriction (May 2008 – October 2009) intended?",
]:
    para(q, style="List Number", after=2)

heading("What I'll do next")
para("Look at why Southeast Asia's stock runs empty: harvest timing within the year, and whether the "
     "stock target is actually applied. Rice can't be judged, or used in the substitution runs, until "
     "the no-shock case is steady. Maize is steady without shocks; I can send that figure the same way "
     "if it's useful.")

doc.save(OUT)
print(OUT)
