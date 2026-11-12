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
