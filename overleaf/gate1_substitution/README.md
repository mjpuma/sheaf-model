# SHEAF Gate 1 — substitution strategy (living Overleaf note)

This folder is a **working protocol**, not a journal draft. The P3 paper
to upload is `../gate1_whitepaper/`. Zip either folder and upload to
Overleaf (New Project → Upload Project). Compile with **pdfLaTeX + BibTeX**.

From the repo root:

```
cp figures/fig_gate1_substitution.png overleaf/gate1_substitution/figures/
cp figures/fig_gate1_e5_maize.png overleaf/gate1_substitution/figures/
cp figures/fig_gate1_e6_ukraine.png overleaf/gate1_substitution/figures/
cp figures/fig_gate1_consumption.png overleaf/gate1_substitution/figures/
cd overleaf && zip -r gate1_substitution.zip gate1_substitution -x "*.DS_Store"
```

New-agent handoff: `diagnostics/GATE1_HANDOFF.md` (status: **stop**; P3
draft is written).

The zip is gitignored; commit the folder. After each experiment, edit the
files listed below, re-zip (or pull in Overleaf), and recompile.

## What to edit after an experiment

| File | When |
|---|---|
| `tables/status.tex` | Always. One-line **now / next / never**. |
| `tables/log.tex` | Always. **Append** a row; do not rewrite history. |
| `tables/score_band.tex` | When official-split prices or hard bars change. |
| `sections/next.tex` | Always. Replace with the *new* next experiment. |
| `sections/locked.tex` | Rarely. Only if the identification protocol itself changes. |
| `sections/math.tex` | Rarely. Only if the demand form changes. |

Do **not** densify σ, pick σ\* on 2008 rice and maize, retune Gate 0
`CropParams`, unpause `sheaf/dynamic_grains.py`, or start the export game
from this note.

Numbers source: `diagnostics/gate1_score.csv`, `diagnostics/gate1_report.md`,
plan: `diagnostics/GATE1_PLAN.md`.
