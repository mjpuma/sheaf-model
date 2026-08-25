# SHEAF Gate 0 white paper — Overleaf project

Zip **this folder** (`main.tex`, `refs.bib`, `sections/`, `tables/`, `figures/`)
and upload to Overleaf: New Project → Upload Project.

From the repo root:

```
cd overleaf && zip -r gate0_whitepaper.zip gate0_whitepaper -x "*.DS_Store"
```

The zip is gitignored; the folder is what to commit. Compile with **pdfLaTeX + BibTeX**.

## What this paper is

Gate 0 only: **substitution off**, **endogenous export game off**. One crop at
a time, 24 steps/year, exogenous AMIS cuts. Hindcasts 2007/08, 2010/11, and
the 2021–23 Ukraine-war window.

The older short note `../gate0_agrimate/` is a figure factory for the
Agrimate scenario-split panels. **This folder is the writeup to upload.** Do not
upload gitignored `agrimate/*.pdf` (copyright).

## Regenerate from the repo root

```
python scripts/score_subannual_crop.py --crop wheat
python scripts/score_subannual_crop.py --crop maize
python scripts/score_subannual_crop.py --crop rice
python scripts/make_agrimate_comparison.py
python scripts/score_ukraine_war.py
python scripts/assemble_whitepaper.py
```

`assemble_whitepaper.py` copies PDFs/PNGs into `figures/`. Tables under
`tables/` are locked to the scored numbers; re-score before editing them.
