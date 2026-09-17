# SHEAF Gate 1 white paper — Overleaf project (paper P3)

Zip **this folder** (`main.tex`, `refs.bib`, `sections/`, `tables/`, `figures/`)
and upload to Overleaf: New Project → Upload Project.

From the repo root:

```
cd overleaf && zip -r gate1_whitepaper.zip gate1_whitepaper -x "*.DS_Store"
```

The zip is gitignored; the folder is what to commit. Compile with **pdfLaTeX + BibTeX**.

## What this paper is

Gate 1 / paper P3: **substitution on**, **endogenous export game off**.
Isoelastic food/feed cross-price demand on the locked Gate 0 spine.
Pre-declared band σ ∈ {0, 0.3, 0.6}. No σ*.

The living protocol note is `../gate1_substitution/` (experiment log, next
sitting). **This folder is the writeup to upload.** Frozen claim:
`../gate1_substitution/sections/claim.tex`. New-agent handoff:
`../../diagnostics/GATE1_HANDOFF.md`.

## Figures

Copied from `overleaf/gate1_substitution/figures/` and, if the optional
consumption diagnostic was run, from `figures/fig_gate1_consumption.png`.
Country choropleths: `python3 scripts/score_whitepaper_maps.py`
(`fig_gate1_map_dc_{wheat,rice,maize}_2008.png`).

Do not retune `CropParams`, densify σ, unpause `sheaf/dynamic_grains.py`,
or re-run this paper to host the export game. The crisis game is types
slow / τ_t on the Gate 0 spine (`diagnostics/GAME_CLOCK.md`).
