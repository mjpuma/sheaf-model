# Level-1 interrogation — wrong-signed crisis prices (2026-08-22)

**Status:** Root cause identified for the *annual SPE* path.  
**Superseded for Gate 0:** architecture locked to Agrimate-aligned **24 steps/year**
out-of-equilibrium dynamics — see [ARCHITECTURE.md](../ARCHITECTURE.md).
This note is retained as the post-mortem for why annual equilibrium failed.

**Was this without strategy?** Yes. `play_game=False`; AMIS τ exogenous.

## Was this without strategy?

**Yes.** Every Level-1 run uses `play_game=False`. Historical restrictions enter
only as exogenous AMIS → `tau_forced`. Confirmed by counterfactual:

| Leg | Wheat 2008/2006 hike | Notes |
|---|---|---|
| Full L1 (old plumbing) | ×0.61 (obs ×1.49) | Wrong sign |
| Shocks only | ×0.56 | Same wrong sign — **shocks dominate** |
| Game ON + shocks | ≈ shocks only | Strategy is not the driver |
| Tau only (strong) | ×1.21 (obs ×1.49) | **Correct sign** |

So we were *not* looking at a flat no-shock baseline; we were looking at a
broken full Level-1 path whose production forcing overwhelmed everything.

## Root causes (ordered)

### 1. Era mismatch (implementation bug) — FIXED in Gate 0 defaults

Hindcast years 2006–11 were multiplied onto **2019–21** USDA Q/D0. Demand sat
near modern ~770 MMT wheat while crisis production is ~600–700 MMT. Defaults
are now `baseline_years=(2004,2005,2006)` and stocks seeded from PSD 2005.

### 2. World wheat harvest rose into 2008 (data + annual resolution)

PSD / LOWESS world wheat anomalies in the crisis window:

| year | world anomaly |
|---|---|
| 2006 | −4.4% |
| 2007 | −4.2% |
| **2008** | **+5.3%** |
| 2009 | +4.0% |
| 2010 | −3.5% |
| 2011 | +1.9% |

Observed Pink Sheet real prices **peak in 2008** while the annual world harvest
is a **glut vs trend**. Any SPE forced with those anomalies will cut 2008 prices.
Agrimate’s “2007/08 production-led” result uses monthly dynamics and stock-to-use;
SHEAF is annual equilibrium — world-Q alone cannot reproduce the 2008 annual
price peak. This is not a solver bug.

### 3. Prototype AMIS τ too weak — FIXED default severity

Legacy ladder (ban=120 $/t) barely moved world prices (+4–5% in tau-only).
Default `severity="agrimate"` (ban=500 $/t) recovers crisis **signs** on the
tau-only leg (wheat YoY corr ≈ +0.57; 2008/2006 ×1.21 vs obs ×1.49).

### 4. RoW was frozen at ξ=1 — FIXED

Named-node shocks left Rest-of-World at 1.0 always. RoW now uses the residual
(world − named) LOWESS anomaly.

### 5. Stocks not in market clearing (lineage gap — OPEN)

SHEAF availability is `Qξ − Δstorage`. Beginning stocks only matter through the
lagged storage rule (audit S4). TWIST/Agrimate put stocks inside the period’s
supply. Naive `A=Q+S` over-supplies and goes negative-price — needs a proper
B2 / stock-in-clearing design, not a one-line hack.

## What Gate 0 requires before Level-2

1. **Crisis-era Level-1 plumbing** (done): baseline 2004–06, stock seed 2005,
   RoW shocks, Agrimate τ severity, `play_game=False`.
2. **Attribution every score run** (done): `full` / `shocks` / `tau` legs in
   `scripts/score_level1.py`.
3. **Hard gate — tau-only wheat hike signs must PASS** vs Pink Sheet windows
   2007/08 and 2010/11.
4. **Soft gate — full leg:** 2010/11 restriction-led signal must be visible
   (tau contribution raises prices vs shocks-only). 2007/08 full-leg price peak
   is **not** required until stock-in-clearing / Agrimate quantity cuts land.
5. **Do not start Level-2** (endogenous game fit) until (3) is green and (4)’s
   soft criterion is documented with numbers.

## Reproduction targets (Agrimate / history)

| Target | Source | Level-1 status |
|---|---|---|
| Annual world price hike signs 2007/08 & 2010/11 | Pink Sheet real | Tau-only: PASS. Full: FAIL on 2007/08 (world +5% harvest). |
| 2007 production-led vs 2010 restriction-led attribution | Agrimate | Runnable via shocks vs tau legs; magnitudes not yet matched. |
| Ban≈95% / tax≈50% export quantity cuts | Agrimate/AMIS | Still $/t wedge proxy — quantity-cap mapping TODO. |
| Regional supply / stock-to-use signs | PSD | Diagnostics exist; not yet in score gate. |
| Cross-grain rice spike 2007/08 | History / SHEAF bonus | Open after wheat Gate 0. |

## Commands

```bash
python scripts/score_level1.py              # Gate 0 attribution + fig10
python scripts/run_level1_hindcast.py       # full crisis-era L1
python scripts/run_level1_hindcast.py --tau-only
python scripts/diagnose_level1_inputs.py    # observation panels
```

## Next engineering (still Gate 0 — do not skip ahead)

1. Map AMIS measures to **export quantity constraints** (Agrimate ban/tax cuts),
   not only $/t τ.
2. Design stock-in-period supply (B2 probe or TWIST-like clearing) so 2007/08
   can be production/stock-led without inventing a world harvest shortfall.
3. Add stock-to-use and regional supply sign checks to `score_level1.py`.
4. Only then: Level-2 endogenous game on held-out window.
