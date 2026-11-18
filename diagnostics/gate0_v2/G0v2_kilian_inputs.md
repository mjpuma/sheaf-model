# Gate 0 v2 — Kilian's 2026 input package (four crops)

## A_c (resolved 2026-11-18 by `kilian_v2`; placeholder runs stay non-results)

Kilian's `parameters_baseline=2007-2009_crop=*_source=empirical.csv` files
have an empty `A_c` column for wheat, rice, maize and soybean. With
`A_c_star = :empirical` the run fails at startup (median of an empty column,
`src/preprocess.jl:89`). Values requested from Kilian.

A_c is the baseline budget share of the crop. The household budget is
calibrated so baseline consumption does not depend on it, but it sets how
much consumers cut back when prices rise, so it feeds directly into crisis
price peaks. Published wheat values range from 0.06 to 0.52 by region.

Until Kilian's values arrive, runs labelled `kilian_placeholder_ac` use
`A_c_star = 0.2` in every region (the value left commented out in `Params`).
They check that his other inputs load and run. **They are not Gate 0
results.** Do not score them against bars, quote their prices or stocks, or
use them as references. Rerun everything with his A_c before any finding is
final.

## Parameter files received 2026-11-18

Four `parameters_baseline=2007-2009_crop=*_source=empirical.csv`, received
in `~/Agrimate/Agrimate parameters/` (originals left there). sha256:
wheat `e44434d3…`, rice `d0c88dab…`, maize `e8026b48…`, soybean `a575525e…`.
Input set `kilian_v2` = these four plus the other 24 files of the earlier
package, in `agrimate/data/gate0_v2/inputs_kilian_2026-11-18/` (git-ignored).
The earlier package in `agrimate/data/agrimate_input/` is unchanged.

- A_c is filled: wheat 193/196 areas, rice 193/194, maize 181/181, soybean
  173/174; range 0.064–0.590, none ≤ 0. Missing areas (ANT, COK, NIU) are
  imputed by the code from regional medians.
- A_c is per country, not per crop: the 167 areas present in all four files
  have the same value in every crop.
- Wheat A_c differs from the published 2025 regional values (equal in 12 of
  193 areas, correlation 0.71).
- These are a revision, not just the old files with A_c added. STU and A_d
  change for a few countries per crop (e.g. wheat Egypt STU 0.276 → 0.229,
  Turkmenistan A_d 0.075 → 0.105; rice Paraguay STU 1.222 → 0.229, Colombia
  0.114 → 0.049), a few values go blank, and small islands are dropped
  (wheat FSM, MHL, PLW; rice MHL, PLW; soybean FSM, MHL). The dropped areas
  are still in the food-balance files, so they just leave the regional
  averages.

Open: whether the other 24 files were also revised on their side.

Scope, per Kilian (2026-11-18): these inputs are for reproducing the
2007/08 and 2010/11 crisis peaks. A 2007–2009 trade network is not expected
to reproduce later prices (2022 Ukraine, 2025). Gate 0 uses them only for
2000–2012. Any later-episode work (e.g. the 2022 and 2023 cases in
`GATE2_TYPOLOGY.md`) needs a later baseline network.

## Startup check with placeholder A_c

`gate0_4crop.jl CROP 0 kilian_placeholder_ac`, sheaf commit `7113680`,
four crops in parallel. Logs `agrimate/data/gate0_v2/logs/*_t0_placeholder_ac.log`.

All four reach a saved baseline (90–134 s). All saved variables finite, none
negative. World baseline consumption: wheat 631.6, rice 663.6, maize 799.3,
soybean 259.2 Mt. A numeric `A_c_star` is not written to the NetCDF; it is
in `provenance.txt`.

Startup warnings (wheat matches the published-input startup, which has the
same internal-flow and tolerance warnings):

| crop | negative internal flow set to zero (% of consumption) | baseline trade tolerance reached | supplier not converged |
|---|---|---|---|
| wheat | Southeast Asia −5.4, Western Africa −1.1, Middle Africa −0.6 | 0.000215 (published: 0.000215) | — |
| rice | Canada −29.0, Rest of Western Asia −8.5, Southern Africa −3.2, Australia −2.3 | 0.001 | Ukraine (X_avg 4.6 kt) |
| maize | — | 0.002154 | Western Africa (X_avg 566 kt) |
| soybean | Pakistan −90.3, Rest of Oceania −6.5 | 0.0001 | Rest of Central Asia (X_avg 0.06 kt) |

Questions for Kilian, not fixed here (F, 60–80 %):

- Rice at 664 Mt is near FAOSTAT paddy (≈ 685 Mt in 2008), not USDA milled
  (≈ 440 Mt). Which basis is intended?
- Pakistan soybean and Canada rice: food balance and trade flows disagree
  enough that a large share of consumption has no internal supply.
- Maize Western Africa is not a marginal supplier, unlike the other two
  non-converged cases, and maize needed the loosest trade tolerance.

These are input-consistency observations; A_c does not enter them, so they
should survive the rerun with his values.

## Four-crop runs on `kilian_v2` (2026-11-18)

`gate0_4crop.jl CROP {0,312} kilian_v2`, crisis scenario, four crops in
parallel; sheaf commit `a3fee26`. Startup warnings are identical to the
placeholder runs (A_c does not enter them); the full runs add none. Full
runs 185–265 s.

Bookkeeping, all four crops: supplier and consumer storage balance to 1e-4
kt, sales equal summed transactions, deliveries equal purchases two steps
earlier, no negative quantities, no infinite values.

### Wheat against the published run (Kuhla et al. 2025)

| measure | kilian_v2 | published | J10 bar |
|---|---:|---:|---|
| 2007/08 ratio | 1.3607 | 1.3607 | 1.359 ± 0.01: pass |
| 2010/11 ratio | 1.2125 | 1.2187 | 1.213 ± 0.01: pass |
| peak (May 2008) | 2.2148 | 2.2227 | 2.216 ± 0.01: pass |
| year-end stocks | within 0.05 % for 2000–2010, −0.19 % 2011 | | ±0.5 %: **2012 +0.81 %** (Argentina +0.89 pp) |

Much closer to the published run than the J10 author-parameter set on this
host (2000–2010 stocks within 0.05 % against up to 0.33 %). The only miss is
2012 stocks, driven by Argentina, which is also the largest contributor to
the 2011 gaps in every earlier run. Given the run-to-run spread in
`G0v2_code_checks.md` §4 (0.75 pp on 2011 stocks), a single 2012 miss is
weak evidence either way.

### Rice, maize, soybean (no published reference on disk)

| crop | 2000–05 mean price | 2007/08 ratio | 2010/11 ratio | peak (month) | stocks 2000 → 2012 (Mt) |
|---|---:|---:|---:|---:|---|
| rice | 1.043 | 0.987 | 0.293 | 12.87 (2010-06) | 295 → 325 |
| maize | 1.244 | 1.243 | 1.067 | 4.20 (2011-10) | 463 → 351 |
| soybean | 1.154 | 1.136 | 0.976 | 2.13 (2009-06) | 150 → 128 |

These are not judged against any bar. Observations:

- Rice cross-border trade nearly stops in 15 steps (below 10 % of its
  2000–05 median of 1287 kt/step; as low as 1 kt), all in 2006–2012. In
  those steps a few small trades at extreme prices set the world index.
  The June 2010 monthly peak (12.9) is Southeast Asia as almost the only
  seller: 18 kt at 69× baseline, then 817 kt at 12.2×. There is no 2008
  spike (2007/08 ratio 0.99), although the rice restriction file has India
  at 0.95 from 2007-10 to 2011-09, Vietnam 2007-07 to 2009-04 and Thailand
  2008-05 to 2009-10. Gate 1 hard bar 4 (rice bans carry the 2008 rice
  spike) cannot be tested until this is understood. Not investigated. C/F,
  40–60 %.
- Maize: the 4.2 monthly peak is October 2011, with the USA almost the only
  seller (trade about 25 % of normal, 3.8–4.7× baseline). One separate thin
  step (2001-10, 116 kt). The index starts above 1 (2000 mean 1.36). Stocks
  fall 25 % over the run.
- Soybean has no thin steps; its 2009 peak is set by large flows.
- Price index decision (2026-11-18): keep the one used here for all crops.
  It is the branch's own `plot_wm_price_timeseries` (`src/plot.jl`,
  "WM price index": monthly Σ(quantity × price) / Σ quantity over
  cross-border flows), which PIK's plot code applies to wheat, maize and rice
  alike. Thin-trade spikes are therefore model output, not a scoring
  artefact. Observed comparison series in that code: World Bank deflated US
  HRW wheat, US maize, Thai 5% rice (`data/clean/prices/commodity_prices.csv`,
  not in the snapshot); soybean has no entry.

### Observed prices (World Bank Pink Sheet, MUV-deflated)

`data/world_prices/` (US HRW wheat, Thai 5% rice, US maize; soybeans read
from the monthly workbook and deflated by the same per-year ratio). Scaled to
the model's 2000–2012 mean, as `plot_wm_price_timeseries` does. July–June
mean over 2000–05 mean, model (observed): wheat 1.36 (1.98), 1.21 (1.61);
rice 0.99 (1.89), 0.29 (1.77); maize 1.24 (1.64), 1.07 (1.96); soybean 1.14
(1.68), 0.98 (1.64). PIK's own deflated series not on disk; MUV used for now.

### Rice and maize by scenario (2026-11-18, driver `6fda0f9`)

Each crop run four ways on `kilian_v2`: no shocks, harvest anomalies only,
export restrictions only, both (crisis).

| crop, scenario | 07/08 | 10/11 | peak (month) | thin steps | trade Mt/yr 2000 → 2012 |
|---|---:|---:|---|---:|---|
| rice, no shocks | 0.92 | 0.42 | 11.2 (2002-03) | 11 | 43 → 85 |
| rice, anomalies only | 0.82 | 0.46 | 12.2 (2010-05) | 8 | 45 → 71 |
| rice, restrictions only | 1.15 | 0.24 | 67.7 (2011-09) | 11 | 43 → 51 |
| rice, both | 0.99 | 0.29 | 12.9 (2010-06) | 15 | 45 → 55 |
| maize, no shocks | 1.02 | 1.04 | 1.63 (2000-07) | 0 | 86 → 97 |
| maize, anomalies only | 1.17 | 1.05 | 1.88 (2003-10) | 1 | 84 → 90 |
| maize, restrictions only | 1.05 | 1.04 | 1.83 (2008-07) | 0 | 86 → 95 |
| maize, both | 1.24 | 1.07 | 4.20 (2011-10) | 1 | 84 → 92 |

Rice is unstable with no shocks at all (95 %): a 2002 spike to 11.2, 11 thin
steps, cross-border trade doubling against a baseline of 37.7 Mt/yr. The
export bans are not the cause. The instability centres on Southeast Asia (top
seller, 187 Mt/yr harvest, ψ 0.139, A_d* 0.194): its supplier storage is
empty in most steps (median 0.6 Mt, max 14.9 Mt), it alternates between
exporting almost nothing and 10.8 Mt in one step, and its export price
swings from 0.6 to 48× (31 steps above 5×). Why, unknown (inputs, harvest
distribution or the 0.001 baseline-trade fit): F/D, 40–60 %. Rice Gate 0
cannot be judged until the no-shock run is stable.

Maize is stable with no shocks (index flat at 1.2–1.3, stocks settle at
≈ 395 Mt after spin-up, like wheat). Each shock alone moves it little; the
October 2011 4.2 peak appears only with both. The maize index sits at
≈ 1.23 rather than 1 in the no-shock run (cross-border baseline prices
above 1); not investigated.
