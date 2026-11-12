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

(results below)
