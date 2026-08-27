# Gate 1 handoff (read this first)

**Date:** 2026-08-27. Experiments **E0–E8** are done. Substitution draft
is written. Do not re-run the σ band or E5/E6 unless reproducing. Do not
pick σ*. The game is a **layer** on the Gate 0 spine, not papers “P4”
and “P5” (`diagnostics/PAPER_STACK.md`). Headey clock:
`diagnostics/GAME_CLOCK.md`. **Do not re-run Gate 0 or Gate 1** to host
the game.

Living Overleaf note: `overleaf/gate1_substitution/` (zip that folder).
**Substitution draft to upload:** `overleaf/gate1_whitepaper/` (zip that folder).
Protocol twin: this file + `diagnostics/GATE1_PLAN.md`.

## What the new agent should do

**Stop** on substitution unless asked to revise that draft.

If asked for the game: `diagnostics/GAME_CLOCK.md` then
`diagnostics/GATE2_PLAN.md`. Next model step is **more than one
government** on that clock (cascade), still not a 2008 score.

The writeup is `overleaf/gate1_whitepaper/`. Frozen claim still lives in
`overleaf/gate1_substitution/sections/claim.tex` (unchanged). Optional
consumption vs PSD diagnostic is scored (`diagnostics/gate1_consumption_report.md`);
it is not a retune target.

Zip for Overleaf:

```
cd overleaf && zip -r gate1_whitepaper.zip gate1_whitepaper -x "*.DS_Store"
```

## What the new agent must not do

- Pick σ\* on 2008 rice+maize, or because 2022 wheat corr rose
- Densify `{0, 0.3, 0.6}`
- Retune Gate 0 `CropParams`, warehouse, asks, or `RHO`
- Unpause `sheaf/dynamic_grains.py` / `scripts/score_subannual_spillover.py`
- Start a “club” or “tipping” writeup, or an endogenous-network paper.
  The game beta is a mechanism check (`diagnostics/GATE2_PLAN.md`); do
  not turn it into a 2008/10 score. Do not re-run Gate 0 or Gate 1
  (`GAME_CLOCK.md`). Next model step, if asked, is a **second player**
  on the Headey clock — still not a new manuscript name.
- Graft annual Slutsky `M_i` / `OWN_ELAST` into the 24-step spine
- Commit `assets/SHEAF_model_walkthrough.pptx`
- Push unless asked

## Locked claim (E7)

Isoelastic food/feed substitution on the **locked Gate 0 spine**, Jacobi
demand-then-market. Own ε = `CropParams.elast` (not `calibration.OWN_ELAST`).
Industrial/ethanol does not substitute. Dual host vs README §1 — disclose,
do not equate.

σ ∈ `{0, 0.3, 0.6}` is a **pre-declared sensitivity band**, not a fit.

| Bar | Result |
|---|---|
| σ=0 identity vs Gate 0 (2006–11 and 2021–23) | PASS (~1e-16) |
| 2007/08 spillover sign (rice/maize hikes do not fall) | PASS |
| Wheat 2008 restriction-led, 2010 production-led | PASS at every σ |
| Rice AMIS still carries 2008 rice | PASS (~97–104%) |
| 2022 wheat still AMIS-led | PASS |
| 2022 maize stays flat (no invented spike) | PASS (×1.01 vs obs ×1.09) |

**Disclosed leftovers (not retune targets):**

- 2010 maize hike ×1.70 → ×1.15 at σ=0.6 is a **higher Jun-2009 base**
  ($182 → $283) from wheat–maize ρ after 2008; Feb-2011 peak is slightly
  *up*. E5: zero ρ_wm restores 87%; freeze rice 2%.
- 2022 rice drifts ×0.99 → ×1.18 vs obs ×0.91 (corr +0.61 → +0.46). Soft
  wrong-way miss. Do not pick σ=0.6 because wheat corr rose (+0.69 → +0.75).
- Rice 2008 in the *data* is primarily own-ban (India/Vietnam), not a clean
  wheat→rice substitution fingerprint.
- Consumption vs PSD: σ=0 inherits Gate 0 leftover; σ=0.6 ticks mean ratios
  up slightly (wheat ×0.92→×0.94) and makes maize corr worse (−0.64→−0.84).
  Δcons signs unchanged. Diagnostic only.

## Code

| Path | Role |
|---|---|
| `overleaf/gate1_whitepaper/` | **P3 draft** (E8) |
| `sheaf/dynamic_coupled.py` | Coupling; `p0` dict; `zero_pairs`; `freeze_price` |
| `sheaf/dynamic_crop.py` | `prepare_crop_run` / Gate 0 market (locked params) |
| `scripts/score_gate1.py` | 2006–11 band + hard bars |
| `scripts/score_gate1_e5.py` | Maize 2010 counterfactuals |
| `scripts/score_gate1_e6.py` | 2021–23 hold-out |
| `scripts/score_gate1_consumption.py` | Optional world use vs PSD (diagnostic) |
| `diagnostics/gate1_report.md` | E4 scores |
| `diagnostics/gate1_e5_report.md` | E5 classification |
| `diagnostics/gate1_e6_report.md` | E6 hold-out |
| `diagnostics/gate1_consumption_report.md` | E8 consumption diagnostic |

Official P1 flags: `use_demand=False`, harvest+AMIS, maize industrial on.
Ukraine window: years 2021–23, stock seed 2020, FAOSTAT 2019–21, per-crop
`p0` = 2021 Pink Sheet mean.

After an experiment: edit `overleaf/gate1_substitution/tables/status.tex`,
append `tables/log.tex`, replace `sections/next.tex`. Do not rewrite locked
math/identification. The P3 prose lives in `overleaf/gate1_whitepaper/`.
