# Gate 1: cross-grain substitution on the locked Gate 0 spine

**Status:** scored (2026-08-25). Identity PASS. Hard bars PASS on the
pre-declared band σ ∈ {0, 0.3, 0.6}. **No σ\* selected.** Soft: 2008
rice/maize hikes move the right way; maize 2010 hike/corr deteriorate at
σ=0.6 (×1.70 → ×1.15 vs obs ×1.44). See `diagnostics/gate1_report.md`.  
**Paper:** P3. Agrimate cannot do this (single commodity).  
**Does not retune** `CropParams`. Does not turn on the export game.

Gate 0 is accepted. `sheaf/dynamic_grains.py` + `scripts/score_subannual_spillover.py`
are a **paused prototype** (pool rationing, old λ/η, raw PSD harvests). Do not
unpause them. Gate 1 couples the **ask-dominated Armington** spine in
`sheaf/dynamic_crop.py`.

## Question

When wheat (or rice) spikes in 2007/08, do maize and rice prices move in a way
that isoelastic cross-price demand on the Gate 0 market can explain — and that
three independent single-crop runs cannot?

Historical hook: rice 2008 had its own export-ban panic, but was also linked to
wheat. Agrimate runs each grain alone. SHEAF’s extra claim is the spillover.

## Locked Gate 0 pieces (do not change)

- `default_crop_params()` own-price ε, STU, asks, warehouse, AMIS map, LOWESS
  harvest, mean flex, USA maize industrial, FAOSTAT E0, twin identity.
- Official P1 split: harvest + AMIS, `use_demand=False`, industrial on for maize.
- Leftovers in `GATE0_PARAMETERIZATION.md` §6 stay leftovers.

## What is new

Isoelastic food/feed demand for grain \(g\):

\[
d^g_{i,t}
= C^{g,\mathrm{flex}}_{i,t}
  \prod_h \Bigl(\frac{p^h_t}{p^h_0}\Bigr)^{\eta_{gh}}
+ C^{g,\mathrm{ind}}_{i,t}.
\]

Own exponents \(\eta_{gg}=\varepsilon_g\) from **Gate 0** `CropParams.elast`
(not `calibration.OWN_ELAST`). Cross exponents

\[
\eta_{gh}=\sigma\,\rho_{gh}\,|\varepsilon_g|
\quad(g\neq h),
\]

with \(\rho\) the illustrative substitutability matrix in `sheaf/calibration.py`
(wheat–maize strongest via feed; wheat–rice food; rice–maize weaker).
\(\sigma=\) `subst_scale`. Industrial/ethanol does **not** substitute.
At \(p=p_0\), the product is 1 for any \(\sigma\) (twin still flat).

Each grain still clears on its own FAOSTAT network and own asks. Coupling is
**demand-side only** this gate (Jacobi: all demands from \(p_t\), then all three
markets, then all three prices).

**Demand form (locked, before σ>0 scores).** Gate 1 is **not** README §1
linear Slutsky `D = a − Mp`. Dual host, not a coding bug: annual SPE uses
`OWN_ELAST` + `build_demand_system`; the crisis spine uses isoelastic
`CropParams.elast`. Switching Gate 1 own-ε to `OWN_ELAST` would break σ=0
identity (wheat −0.15 vs −0.25; maize −0.25 vs −0.30). Cross form
`σ ρ |ε_g|` is a constant-elasticity overlay (Jacobian not Slutsky-symmetric).
Do not graft `M_i` into the 24-step ask loop for P3. Industrial/ethanol stays
out of substitution (mandate-like residual). Disclose the dual host in P3
prose; do not equate Gate 1 η with annual `M_i`.

## Identification (locked before σ>0 scores)

**Rule:** \(\sigma\in\{0,0.3,0.6\}\) is a **pre-declared sensitivity band**, not
an estimate. \(0\) is Gate 0 identity; \(0.6\) is the old prototype /
`build_countries(substitution=True)` default, **not** a fitted peak; \(0.3\)
is the mid scale. Do not densify the grid after seeing coupled prices
(no adding \(0.9\), no argmax on 2008 Δcorr).

**Preferred claim (no point estimate):** report all three σ. P3 evidence =
hard bars plus hold-out soft scores. Do **not** pick σ\* on 2008 rice *and*
maize and then call that same 2008 window validation.

**If a preferred σ is required:** select only on the 2007/08
**wheat→maize** spillover margin (`RHO` wheat–maize \(=0.40\), feed).
**Hold out:** rice Pink Sheet 2007/08, plus **2010/11** and **2022**
(never used for selection). Reverse (train rice, hold maize) is
**withdrawn**: 2007/08 rice is an own-ban episode, not a clean substitution
target.

**Fitting 2008 then claiming validation** includes: maximizing 2007/08
rice/maize fit then reporting that window as the result; joint σ on
2008+2010+2022; retuning `CropParams` / `RHO` / Gate 0 leftovers to help
spillovers; peeking at coupled scores then declaring the grid.

`RHO` stays frozen illustrative structure (`calibration.py`). Own-price ε
stays Gate 0 `CropParams.elast`. No game.

| Allowed | Not allowed |
|---|---|
| Pre-declared band; optional one-margin 2007/08 selection | Fitting σ to pretty-up all three Pink Sheet series |
| Hold out the other 2007/08 grain + 2010 + 2022 | Joint fit of all crises then “validated” |
| Own-price ε stays Gate 0 | Re-estimating ε or `RHO` on crises |
| `subst_scale=0` must recover Gate 0 | Coupled run that drifts from Gate 0 at \(\sigma=0\) |

## Hard bars

1. **Identity.** Coupled \(\sigma=0\), official split, 2006–11: monthly world
   price of each grain matches the corresponding `run_crop_dynamics` to
   relative error \(\lesssim 0.5\%\) (numerical, not a new model).
2. **Sign of spillover.** In the 2007/08 stress window, \(\sigma>0\) must not
   *lower* rice and maize prices relative to \(\sigma=0\) when wheat is up
   (substitutes: wheat dear \(\Rightarrow\) more rice/maize demand). A fall is
   a bug or a wrong \(\rho\) sign.
3. **Wheat Gate 0 not wrecked.** For **every reported** \(\sigma>0\), wheat
   2007/08 stays restriction-led and 2010/11 stays production-led (same
   isolated-leg signs as Gate 0). Amplitude may move; a sign flip is a fail.
4. **Rice still has its own ban.** Isolated rice AMIS must still carry most of
   the 2008 rice hike; substitution is a spillover, not a replacement for
   India/Vietnam \(\tau\).

## Soft bars (report, do not select on)

- Hold-out \(\Delta\)corr / \(\Delta\)hike (rice 2008; 2010/11; 2022). Do not
  require a win. **Do not** use in-sample 2008 rice *and* maize soft scores
  to pick σ\*. Least-confounded cross-grain in the data is **maize**.
- Rice 2010/11 observed hike is **< 1**. σ>0 must not be scored as a win for
  inventing a rice co-spike that year.
- Consumption: substitution can raise rice/maize use when wheat is expensive.
  Score vs PSD as a diagnostic, not a retune target.

## 2007/08 data (Pink Sheet real 2010$, same `_hike` windows as Gate 0)

Not a model claim. Source: `load_price_series_monthly(deflated=True)`.

| Crisis | Window | Wheat | Rice | Maize |
|---|---|---:|---:|---:|
| **2007/08** | 2006-06 ±1 → 2008-03 ±1 | **1.82** | **1.84** | **1.84** |
| **2010/11** | 2009-06 ±1 → 2011-02 ±1 | **1.16** | **0.79** | **1.44** |

Calendar peaks vs the same Jun-2006 baseline are higher than the fixed Mar-2008
window: wheat **1.95** (Mar 2008), rice **2.54** (Apr 2008), maize **2.26**
(Jun 2008). Wheat reached ≥1.3× baseline from **2007-09**; rice not until
**2008-02**. Sep 2007–Jan 2008: wheat already 1.5–1.8× while rice stayed
~0.98–1.09×. Largest rice MoM jump was Apr 2008 while wheat was already falling.

AMIS rice measures (Viet Nam 2007-07, India from 2007-10, second wave 2008-02/04)
align with the rice cliff. **2007/08 rice is primarily own-ban**, not a clean
wheat→rice substitution fingerprint. Matching that rice spike is not a
substitution validation target (the model already feeds rice AMIS). **2010/11**
is the contrast: wheat/maize up, rice down — a pass must not invent a rice hike.

**Fair empirical bar:** wheat hike/timing in both crises; maize co-movement as
the least-confounded spillover; rice 2008 = own-policy (hard bar 4); rice 2010
= no fake co-spike. Do **not** require all three series to look equally pretty.

## Implementation

| Path | Role |
|---|---|
| `sheaf/dynamic_coupled.py` | Joint 24-step runner on Gate 0 arrays |
| `scripts/score_gate1.py` | Identity assert, \(\sigma\) grid, spillover table, figure |
| `diagnostics/GATE1_PLAN.md` | This file |
| `sheaf/dynamic_grains.py` | Stay paused (do not score Gate 1 on it) |

One writer on the coupled step loop. Do not edit Gate 0 leftovers to help
spillovers.

## Multi-agent Gate 1 (diagnosis vs implementation)

**Parallel (independent, no inherited conclusions):** (A) σ=0 identity vs
`_simulate_window` — **MATCH**, max monthly `|Δp|` ~ 4×10⁻¹⁶; (B) isoelastic
cross-price vs `core.py` Slutsky \(M_i\) — **keep isoelastic on spine**;
(C) identification / hold-out for \(\sigma\) — **band, not a 2008 fit**;
(D) 2007/08 Pink Sheet spillover as data — **rice 2008 own-ban; maize least
confounded; rice 2010 no co-spike**. Verification protocol per `CLAUDE.md`.

**Serial:** one writer on `sheaf/dynamic_coupled.py`. Do not unpause
`dynamic_grains.py`.

## Explicitly not Gate 1

- Level 2 / P4–P5 export game
- P2 endogenous network
- Linear Slutsky \(M_i\) in `sheaf/core.py` (annual SPE host; different demand)
- Fitting Agrimate’s CPI series
