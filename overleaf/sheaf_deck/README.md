# SHEAF first-principles Beamer deck

Zip **this folder** (`main.tex`, `refs.bib`, `sections/`, `figures/`,
`tables/`, `verify_claims.py`) and upload to Overleaf:
New Project $\to$ Upload Project. Compile **pdfLaTeX + BibTeX**.

From the repository root:

```
cd overleaf && zip -r sheaf_deck.zip sheaf_deck -x "*.DS_Store" -x "*verify_claims.py"
```

(`verify_claims.py` is a repo-root runnable; it does not need to go to
Overleaf.)

## What this is

A long, one-claim-per-slide walkthrough of SHEAF for a joint sitting with
the Agrimate authors. Every equation is grounded in `README.md` and the
live hosts (`sheaf/dynamic_crop.py`, `dynamic_coupled.py`,
`dynamic_policy.py`). `sheaf/core.py` is labelled leftover.

The sitting map (early in the deck) jumps to lineage, the one-step spine,
CropParams, Gate 0 scores, Gate 1, Gate 2, the leftover host (skip unless
README §§1–6 is the question), and the five Agrimate questions. Do not
read the leftover section as the 2007/08 model.

Green banners are README/code matches. README §8 is the crisis-host
specification (the former documentation gaps are written there). Grey
is the leftover annual SPE. The companion script:

```
python3 overleaf/sheaf_deck/verify_claims.py
```

re-derives the banners (45 OK, 0 divergences, 0 failures on
the branch that ships this folder).

## What this is not

Not a retune of `CropParams` or $\sigma$. Not a 2008 who-restricts score.
Not an unpause of `dynamic_grains.py`.
