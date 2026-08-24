# Gate 0 plan: per-crop Agrimate-style market before substitution / Level 2

**Status:** active (locked 2026-08-24)  
**Replaces:** jumping to multi-grain substitution (`dynamic_grains` / spillover) before
single-crop markets are proven.

## Principle

Agrimate is **single-commodity**. SHEAF’s differentiators (cross-grain substitution,
endogenous export game) are only interpretable after each crop’s sub-annual market
clears and stocks/trade behave on their own.

**Order (do not skip):**

1. **Per-crop Gate 0** — wheat, then maize, then rice — each alone (`subst = 0`).
2. **Detailed diagnostics** proving reproduction vs Pink Sheet / PSD / AMIS.
3. **Commit** when each crop’s hard bar is green.
4. **Only then** re-enable multi-commodity substitution tests.
5. **Only then** Level 2 endogenous restriction game.

The existing `sheaf/dynamic_grains.py` + `score_subannual_spillover.py` path is
**paused / demoted** to a prototype until steps 1–3 are green for all three grains.

## What “Agrimate-style market every step” means here

Each ~15-day step, for one crop:

| Piece | Requirement |
|---|---|
| State | Stocks, harvest inflow, food use, export cuts |
| Suppliers | Physical offers after food + lean targets; AMIS quantity cuts |
| Offer prices | Exporter **ask** prices adapt to fill rates |
| Trade | FAOSTAT bilateral Armington clear (destination + source shares) |
| World price | Dominated by **trade-weighted asks** (market outcome), not a twin-scarcity formula |
| Twin path | Diagnostic only: no-shock/no-AMIS identity (flat at \(p_0\)); not the main price law |
| Forcing (Level 1) | PSD production anomalies + exogenous AMIS cuts |

Annual SPE remains a reference, not this clock.

## Per-crop hard / soft bars

| Crop | Hard | Soft | Notes |
|---|---|---|---|
| **Wheat** | Monthly price signs/timing 2007/08 & 2010/11 vs Pink Sheet; twin identity; AMIS lifts price; Russia offer cut 2010; no fake spring spike | Regional stocks / STU signs; shocks vs τ attribution | Agrimate’s published bar |
| **Maize** | Same machinery; monthly corr/hike signs vs Pink Sheet maize; twin identity; AMIS cuts bind where policies exist | Stocks / top exporters | No Agrimate maize figure set — Pink Sheet + PSD is the bar |
| **Rice** | Same; Pink Sheet rice; India/Vietnam-era AMIS bite in 2007/08 where data allow | Stocks / top exporters | Rice had its own ban panic; still scored **alone** first |

## Diagnostics required (each crop)

Script: `python scripts/score_subannual_crop.py --crop {wheat,maize,rice}`

Must write and print:

1. Robustness asserts (twin / AMIS / seasonality / exporter cut where applicable).
2. Legs: `full`, `shocks`, `tau` monthly prices vs Pink Sheet (corr + crisis hike ratios).
3. World stock and stock-to-use path (model) vs PSD annual ending stocks (soft).
4. Top exporters’ offers/shipments in crisis windows (AMIS effect visible).
5. Attribution one-liner: which leg carries 2007/08 vs 2010/11.
6. Figure panel + CSV under `diagnostics/` and `figures/`.
7. Short markdown report: `diagnostics/gate0_{crop}_report.md`.

## Implementation checklist

- [x] Document this plan (ARCHITECTURE + VALIDATION + this file).
- [x] Vendor maize/rice FAOSTAT E0 crisis windows (bilateral structure).
- [x] Single-crop spine `sheaf/dynamic_crop.py` (ask-dominant world price, ω=0.80).
- [x] Wheat thin-wrap (`dynamic_wheat.py`); Gate 0 wheat asserts still pass.
- [x] Maize and rice runs + reports (`scripts/score_subannual_crop.py`).
- [x] Commit this Gate 0 per-crop baseline.

### Soft score snapshot (2026-08-24 parameterization retune)

See `GATE0_PARAMETERIZATION.md` for the equation/parameter audit.

| Crop | full corr | 2007/08 full hike | Asserts |
|---|---|---|---|
| wheat | ~+0.68 | ~×1.4 | PASS |
| maize | ~+0.36 | ~×1.5+ | PASS (shortfalls-only shocks) |
| rice | ~+0.80 | ~×2.2 | PASS |

**Before subst / Level 2:** maize soft bar is improved but still the weakest;
further gains need an explicit demand block, not more κ fitting.

## Explicit non-goals until Gate 0 per crop is green

- Fitting substitution scales on joint W/R/M crises.
- Endogenous restriction Nash / IBR on the sub-annual clock (Level 2).
- Replacing Pink Sheet with Agrimate’s private series (use published Pink Sheet).
