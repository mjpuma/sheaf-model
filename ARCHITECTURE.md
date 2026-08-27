# SHEAF architecture decision: Agrimate-aligned sub-annual dynamics

**Decision date:** 2026-08-23  
**Status:** Locked — replaces annual SPE-as-heartbeat for crisis validation.

## Scientific goal

Reproduce **crisis shock dynamics** (2007/08, 2010/11): sub-annual world
price paths, stock drawdowns, restriction cascades, and (SHEAF’s addition)
cross-commodity substitution + endogenous export restrictions.

We are **not** optimizing for a once-per-year market equilibrium paper.
Annual SPE remains useful as a *reference* or outer diagnostic, not the clock.

## Locked choices

| Axis | Choice | Notes |
|---|---|---|
| Time step | **24 steps / year** (~15.2 days) | Match Agrimate (Kuhla et al. 2025, §4.1) |
| Dynamics | Out-of-equilibrium agent / stock–trade adjustment | Not full SPE clear every step |
| Forcing | Production anomalies + AMIS restrictions (Level 1) | Then endogenous game (Level 2) |
| Price target | **Monthly** Pink Sheet (deflated), not annual averages | Agrimate’s published bar |
| Lineage | Agrimate / acclimate-style timing; SHEAF keeps multi-commodity + game | TWIST annual frame demoted |

## Why 24 steps/year — and why not 26?

Agrimate (§4.1): *“flexible regional and temporal resolution… we use 24 time
steps per year, so about 15 days (roughly two weeks) per time step.”*

They do **not** publish an explicit “why not 26 fortnights” argument. SHEAF
adopts 24 for lineage alignment and documents the tradeoffs:

### Why 24 is the right default (follow Agrimate)

1. **Exact month tiling.** 24 = 2 × 12. Each calendar month is two equal
   half-months. Validation targets are **monthly** world prices (Pink Sheet /
   Agrimate Figs. 4–7). Mapping model output → month is trivial: average the
   two steps in that month.
2. **Harvest calendars are monthly.** SAGE / USDA FAS crop calendars used to
   spread annual production into the year are month-resolution. 24 steps let
   each month own two identical-length bins without fractional month weights.
3. **Agricultural-year bookkeeping.** Agrimate’s storage narratives run on a
   July–June crop year. 24 equal steps = 12 months × 2, clean spin-up
   (Agrimate uses 4 years = 96 steps) and annually-periodic Nash baselines.
4. **Equal step length.** Δt ≈ 365.25/24 ≈ 15.22 days. No leap-week or
   52-vs-365 mismatch inside the year.

### Why someone might want 26 (true fortnights) — and why we don’t (yet)

1. **52 weeks / 2 = 26** is the literal fortnight calendar. Slightly closer to
   “bi-weekly” in common speech.
2. **Cost:** months no longer divide evenly (28–31 day months → some months
   get two steps, some three, or you abandon month alignment). Monthly price
   scores and AMIS start/end dates (often month-stamped) need a custom
   calendar map.
3. Agrimate’s published hindcasts and figures are monthly aggregates of a
   24-step year. Matching **their** results means matching **their** clock.

**SHEAF policy:** default `STEPS_PER_YEAR = 24`. If a sensitivity run ever
uses 26, it must ship an explicit month↔step map and re-score monthly
targets; it is not the Gate 0 clock.

```text
Δt_24 ≈ 15.22 d    month m ↔ steps {2m, 2m+1}   (0-based) or {2m-1, 2m}
Δt_26 ≈ 14.05 d    month mapping: non-uniform — avoid for Gate 0
```

## What changes in the model (high level)

### Demote

- Period = calendar year as the sole dynamics.
- Full spatial price equilibrium QP every period as the only market clear
  (annual SPE may remain a diagnostic / slow outer loop).

### Promote (Agrimate-aligned core)

1. **Sub-annual state:** stocks, orders/shipments, offer prices, restriction
   flags evolve each ~15-day step.
2. **Seasonal baseline:** annually-periodic Nash (or SPE) baseline from
   FAOSTAT/PSD + harvest calendars; crises = anomalies around that baseline.
3. **Disequilibrium adjustment:** suppliers/purchasers with finite foresight
   and adaptive expectations (Agrimate agents); SHEAF adds cross-grain
   substitution in demand and an endogenous restriction layer for Level 2.
4. **Level 1:** impose AMIS restrictions as quantity cuts (ban≈95%, tax≈50%)
   or equivalent, not only mild annual $/t wedges.
5. **Level 2:** endogenous restriction **actions** on the same sub-annual
   clock. **Types** (food-security weights, who plays) are slow;
   **actions** `τ_{i,t}` respond to conditions — Headey (2011), not an
   annual Nash leftover. See `diagnostics/GAME_CLOCK.md`. Held-out
   identification comes after Gate 0; Gate 0 and Gate 1 are **not**
   re-run to host that game.

### Keep from current SHEAF

- Multi-commodity demand / substitution as the differentiator vs Agrimate.
- Node set + USDA/AMIS/Pink Sheet data plumbing (re-timed to steps).
- Export-restriction *idea*; re-host on sub-annual information sets.
  `sheaf/core.py` keeps the annual prototype (`demo.py`). It is not the
  crisis game. Headey (2011) is the clock: India/Vietnam October,
  Thailand-in-March *discussing* a ban, Japan-in-May announcing stocks.

## Gate 0 (rewritten)

| Gate | Criterion |
|---|---|
| Hard | Monthly wheat world price path 2006–2011: sign and rough timing of
| | 2007/08 and 2010/11 hikes vs Pink Sheet (and Agrimate published series) |
| Soft | Annual regional supply / stock-to-use signs (Agrimate Fig. 4 style) |
| Soft | Attribution: 2007 production/stock-led vs 2010 restriction-led |
| Block | No Level-2 endogenous-game fitting until Hard gate is green |

Annual hike-ratio scoring (`scripts/score_level1.py` as of 2026-08-22) is
**provisional / demoted** — useful for data plumbing checks only, not Gate 0.

## Implementation order (do not skip)

**Locked reorder (2026-08-24):** finish **per-crop Agrimate-style markets** and
detailed diagnostics **before** substitution or Level 2. See
[`diagnostics/GATE0_PER_CROP_PLAN.md`](diagnostics/GATE0_PER_CROP_PLAN.md).

1. Document + freeze clock (`STEPS_PER_YEAR=24`, 24-vs-26 note) — **done**.
2. Sub-annual calendar helper (step ↔ date ↔ month; agricultural year) — **done**
   (`sheaf/calendar24.py`).
3. Seasonal production allocation from harvest calendars + PSD annual totals —
   **done** (`sheaf/seasonal.py`, `data/crop_calendars/`; triangular peak months).
4. **Per-crop dynamic core** (wheat → maize → rice), each alone:
   stocks + bilateral trade + adaptive ask prices + exogenous AMIS —
   world $p$ **ask-dominated** (`sheaf/dynamic_crop.py`; wheat wrap in
   `dynamic_wheat.py`). Twin path = identity diagnostic only.
   Parameters and defensibility: `diagnostics/GATE0_PARAMETERIZATION.md`.
5. **Detailed per-crop Gate 0 diagnostics** (`scripts/score_subannual_crop.py`)
   — price legs, stocks/STU, exporter AMIS bite, attribution, markdown report.
   Wheat also keeps `score_subannual_wheat.py` as a thin entry point.
6. Multi-commodity substitution on the sub-annual spine — **paused** until
   step 5 is green for wheat, maize, and rice. (`dynamic_grains` / spillover
   remain a prototype only.)
7. Endogenous restriction **actions** on the 24-step spine (Level 2) —
   types slow, Headey clock. Gate 0 hard bars are green; **do not re-run
   P1 or P3** to say this (`diagnostics/GAME_CLOCK.md`).
   `sheaf/dynamic_policy.py` is the beta; `core.py` IBR stays a leftover.

Commands:
```bash
python scripts/fetch_external_data.py --prices-only
python scripts/score_subannual_crop.py --crop wheat
python scripts/score_subannual_crop.py --crop maize
python scripts/score_subannual_crop.py --crop rice
# (legacy) python scripts/score_subannual_wheat.py
```

## References

- Kuhla, K., Kubiczek, P., Otto, C. (2025). Understanding agricultural market
  dynamics in times of crisis: the dynamic agent-based network model Agrimate.
  *Ecological Economics* 231, 108546. §4.1 (24 steps/yr), §5 (monthly hindcast).
- Headey, D. (2011). Rethinking the global food crisis: The role of trade
  shocks. *Food Policy* 36(2), 136–146. Monthly export volumes, dated
  restrictions, import surges, announcement effects — the crisis game clock.
- Sacks et al. (2010) / SAGE crop calendars; USDA FAS crop calendar charts.
- Otto et al. acclimate (disequilibrium network lineage).
