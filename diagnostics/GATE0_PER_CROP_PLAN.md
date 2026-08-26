# Gate 0 plan: per-crop Agrimate-style market before substitution / Level 2

**Status:** accepted (2026-08-25). Official P1 scores, white paper, and
Ukraine-war price hindcast are in `overleaf/gate0_whitepaper/`. Substitution
(P3) is next; do not retune Gate 0 leftovers with crisis knobs.  
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
4. **Only then** re-enable multi-commodity substitution tests (**Gate 1**,
   handoff `diagnostics/GATE1_HANDOFF.md`, living note
   `overleaf/gate1_substitution/`). E0–E7 done; next is the P3 draft.
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
3. World stock vs PSD at the crop MY-end month (wheat May, maize August,
   rice **August** — not calendar December), **with and without China**
   (rice: also without India). FAO/AMIS tightness; China stays a named node.
   Country stocks vs PSD at each node’s USDA local MY-end
   (`sheaf/marketing_years.py`). No 28-region maps.
   World **consumption** vs country-sum PSD (calendar year): levels, corr,
   Δcons as % of mean PSD use. Not Agrimate Fig. 4 (supply + Δstocks).
   Do not use `load_crop_world` consumption as the bar (omits the EU).
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
- [x] White paper (`overleaf/gate0_whitepaper/`) + 2021–23 Ukraine-war prices.

### Official P1 snapshot (matched: harvest + AMIS, mean flex, USA maize industrial)

Source: `diagnostics/gate0_{crop}_report.md`. Authority for numbers: the white
paper, not this table if they diverge.

| Crop | full corr | 2007/08 full / obs | 2010/11 full / obs | Asserts |
|---|---:|---:|---:|---|
| wheat | +0.72 | ×2.27 / ×1.82 | ×1.45 / ×1.16 | PASS |
| maize | +0.71 | ×1.97 / ×1.84 | ×1.70 / ×1.44 | PASS (isolated τ must not cut) |
| rice | +0.68 | ×1.72 / ×1.84 | ×0.82 / ×0.79 | PASS |

Industrial/ethanol: USA maize FSI excess vs 2000–04, inelastic. Substitution
(P3) is next; Level 2 stays after that. Leftovers are listed in
`GATE0_PARAMETERIZATION.md` §6 and the white paper — not a retune list.

## Official P1 scoring split (Agrimate-matched)

Headline series: `use_demand=False`, `use_industrial=True` when
`industrial_nodes` is nonempty (mean flex; USA maize RFS residual still on).
Twin / climatology baseline pass `use_industrial=False`.
Year-by-year world food/feed is a sensitivity. Also score consumption vs PSD
and AMIS exporter shipment signs — not Pink Sheet alone.

Long-term papers P2–P5 and the calibration plan:
[`PAPER_STACK.md`](PAPER_STACK.md).

## Multi-agent Gate 0 (diagnosis vs implementation)

**Parallel (independent, no inherited conclusions):** (A) ask/τ world-price
composition; (B) warehouse / lean-season dump; (C) demand default; (D) rice
2008 matched peak. Verification protocol per `CLAUDE.md`.

**Serial:** one writer on `sheaf/dynamic_crop.py`. Then parallel crop scores.

**Pass (matched split, locked):** wheat 2007/08 hike ≳ ×1.4 and no 2006/07
spike > 2008; wheat 2010 hike > 1.0. After LOWESS harvest anomalies, 2010 wheat
is **production-led** (`shocks` > `tau`); do not force restriction > harvest
with a 2010 dummy. Maize 2008 matched ≳ ×1.4 and matched > harvest-only
(isolated τ must not cut the 14-month mean world price); maize 2011
harvest-only > τ; rice 2008 ≳ ×1.5 restriction-led, 2010 not a false spike;
corr wheat/rice ≳ +0.5, maize > 0; world MY-end STU on PSD (~×1.0–1.1).

## Explicit non-goals of Gate 0 (still out of scope)

- Fitting substitution scales on joint W/R/M crises (P3).
- Endogenous restriction Nash / IBR, cooperative club, or tipping (Level 2 / P4–P5).
- Endogenous trade network without FAOSTAT E0 (P2).
- Replacing Pink Sheet with Agrimate’s private series (use published Pink Sheet).
- Crisis-specific knobs (e.g. boost κ only in 2008).
