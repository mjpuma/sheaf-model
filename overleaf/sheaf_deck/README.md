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

A one-claim-per-slide walkthrough of SHEAF for discussion with the
Agrimate authors. Every equation is grounded in `README.md` and the
live hosts (`sheaf/dynamic_crop.py`, `dynamic_coupled.py`,
`dynamic_policy.py`). `sheaf/core.py` is labelled leftover.

### Running order

The deck is ordered as a talk, not as the repository tree:

1. `00_howto` — how to read a slide, the verification protocol, sitting map
2. `01_lineage` — TWIST → Agrimate → SHEAF, what is *not* claimed, the
   headline Gate 0 price figure, what each gate may claim, the node set
3. `01b_architecture` — the two hosts, and the one-step spine diagram
   (this is the roadmap for everything that follows)
4. `02_clock_units` — 24 steps/year, canonical units, a worked unit check
5. `03_data` — USDA PSD, FAOSTAT E0 shares, Pink Sheet, AMIS → τ, calendars
6. `04_harvest` — climatology, triangular weights, LOWESS anomalies,
   foresight blend, lean horizon
7. `05_demand_lean` — the step's first half: avail, demand, lean gap,
   target, purchase demand, offers, then the P1 scoring protocol
8. `06_trade_price` — the step's second half: Armington clear, residual
   pool, stock update, asks, locked/free, and the world price
9. `12_solution` — method of solution: an explicit map, no QP, Python lock
10. `07_params_scores` — locked `CropParams` and the Gate 0 scores
11. `08_gate1`, `09_gate2` — the two gates that sit on that locked spine
12. `10_annual` — the annual leftover (`core.py`); skip unless README §§1–6
13. `11_divergences` — what is specified, five questions, how to reproduce

Sections 5–8 follow the order `_simulate_window` actually evaluates, so a
slide never uses a quantity that a later slide computes.

The sitting map (early in the deck) jumps to lineage, the two hosts, the
one-step spine, method of solution, CropParams, Gate 0 scores, Gate 1,
Gate 2, the leftover host, and the five Agrimate questions. Do not read
the leftover section as the 2007/08 model.

Every slide carries a tiny **Symbols.** line (letter, meaning, unit) and
avoids "as on the previous slide" cross-references, so each slide can be
presented on its own.

The deck compiles with no overfull `\vbox` or `\hbox`, so nothing is cut
off at the bottom or the right of a slide. If you add prose to a frame,
check the compile log for `Overfull \vbox` before presenting.

Green banners are README/code matches. README §8 is the crisis-host
specification (the former documentation gaps are written there). Grey
is the leftover annual SPE. The companion script:

```
python3 overleaf/sheaf_deck/verify_claims.py
```

re-derives the banners (49 OK, 0 divergences, 0 failures on
the branch that ships this folder).

## What this is not

Not a retune of `CropParams` or $\sigma$. Not a 2008 who-restricts score.
Not an unpause of `dynamic_grains.py`.
