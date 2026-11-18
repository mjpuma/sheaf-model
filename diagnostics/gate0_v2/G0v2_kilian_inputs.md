# Gate 0 v2 — Kilian's 2026 input package (four crops)

## Open issue before anything is final: A_c is missing

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
