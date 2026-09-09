# SHEAF Gate 0 discussion — Overleaf project

Zip **this folder** (`main.tex`, `refs.bib`, `sections/`, `figures/`) and
upload to Overleaf: New Project → Upload Project.

```
cd overleaf && zip -r gate0_discussion.zip gate0_discussion -x "*.DS_Store"
```

Compile **pdfLaTeX + BibTeX**.

## What this note is

A discussion of the Gate 0 two-week market after the Agrimate sitting:
the recursion in words, then as numbered equations with every symbol
defined **in place**, with units; then the sitting questions, each set
against the equation it would replace; then the diagnostics that would
settle them. **Four figures**, drawn at page width with 11pt labels.

Compiles clean (17 pp., no undefined references or citations); verified
locally with `tectonic -X compile main.tex`.

Not the hindcast white paper (`../gate0_whitepaper/`).

## Figures in the compile

| File | Role |
|---|---|
| `01_current_fortnight.pdf` | Order of operations within one step |
| `02_baselines_four_objects.pdf` | Four objects called “baseline” |
| `10_storage_cover_rule.pdf` | Partition of available grain: `d`, `T`, `O` |
| `20_four_ways_p.pdf` | Four hosts that can produce a world price |

## Regenerate

```
python scripts/render_gate0_flows.py
```
