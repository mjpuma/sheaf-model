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
5. **Level 2:** endogenous restriction game on the same sub-annual clock
   (held-out identification — after Gate 0).

### Keep from current SHEAF

- Multi-commodity demand / substitution as the differentiator vs Agrimate.
- Node set + USDA/AMIS/Pink Sheet data plumbing (re-timed to steps).
- Export-restriction *idea*; re-host on sub-annual information sets.

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

1. Document + freeze clock (`STEPS_PER_YEAR=24`, 24-vs-26 note) — **done**.
2. Sub-annual calendar helper (step ↔ date ↔ month; agricultural year) — **done**
   (`sheaf/calendar24.py`).
3. Seasonal production allocation from harvest calendars + PSD annual totals —
   **done** (`sheaf/seasonal.py`, `data/crop_calendars/`; triangular peak months).
4. Minimal dynamic core: stocks + trade + exogenous AMIS cuts (wheat first) —
   **bilateral Gate 0 spine with adaptive asks** (`sheaf/dynamic_wheat.py`):
   - lean foresight (seasonal/realized blend) + gradual stock rebuild
   - FAOSTAT Armington clear; ask prices adapt to fill rates
   - world $p$ blends trade-weighted asks with twin scarcity / preferred-block
   - hard asserts: twin identity, AMIS price lift, Russia offer cut, no spring spike
   - equations: README §8
5. Score monthly prices vs Pink Sheet — hike signs + peak months on full leg;
   multi-commodity / Level-2 still open. Wheat Gate 0: `score_subannual_wheat.py`.
6. Add multi-commodity substitution on the sub-annual spine — **done (pool trade)**:
   `sheaf/dynamic_grains.py` + rice/maize calendars; cross-price via
   `OWN_ELAST`/`RHO`/`subst_scale`; per-grain AMIS; twin free identity.
   Spillover score: `scripts/score_subannual_spillover.py` (subst on vs off).
   Bilateral E0 for rice/maize and Level-2 game still open.
7. Add endogenous restriction game (Level 2).

Commands:
```bash
python scripts/fetch_external_data.py --prices-only   # annual + monthly Pink Sheet
python scripts/run_subannual_wheat.py
python scripts/score_subannual_wheat.py               # Gate 0 monthly wheat score
python scripts/score_subannual_spillover.py           # W/R/M subst on vs off
```

## References

- Kuhla, K., Kubiczek, P., Otto, C. (2025). Understanding agricultural market
  dynamics in times of crisis: the dynamic agent-based network model Agrimate.
  *Ecological Economics* 231, 108546. §4.1 (24 steps/yr), §5 (monthly hindcast).
- Sacks et al. (2010) / SAGE crop calendars; USDA FAS crop calendar charts.
- Otto et al. acclimate (disequilibrium network lineage).
