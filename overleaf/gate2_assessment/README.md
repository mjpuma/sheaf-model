# SHEAF Gate 2 beta — Overleaf assessment note

Zip **this folder** (`main.tex`, `refs.bib`, `sections/`, `tables/`, `figures/`)
and upload to Overleaf: New Project → Upload Project.

From the repo root:

```
cd overleaf && zip -r gate2_assessment.zip gate2_assessment -x "*.DS_Store"
```

The zip is gitignored; the folder is what to commit. Compile with **pdfLaTeX + BibTeX**.

## What this note is

An **assessment** of the Gate 2 mechanism check: two exporters, same slow
type, state-contingent `τ_t` on the locked Gate 0 24-step wheat spine.
Headey (2011) is the clock. It is **not** a 2008/10 score, not a policy
paper, and not a reason to re-run Gate 0 or Gate 1.

Protocol twin: `../../diagnostics/GATE2_PLAN.md`. Clock lock:
`../../diagnostics/GAME_CLOCK.md`. Score script:
`python3 scripts/score_gate2_beta.py` (copies line plots **and choropleths**
into `figures/` here). Maps are a regular part of this score: who plays,
fortnights on, open-path stock ratio. Helper: `sheaf/maps.py`.

Do not retune `CropParams`, densify σ, unpause `sheaf/dynamic_grains.py`,
or estimate knobs on 2008.
