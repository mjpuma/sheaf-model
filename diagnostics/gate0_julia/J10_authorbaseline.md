# J10 — the author's own calibrated baseline as input

Status: inputs built and verified at `t_max = 0`; 312-step run in progress.

## Why

J8 put the author's region parameters (`ψ`, `A_d*`, `A_c*`) into our inputs
and J9 put their per-region export restrictions in. Neither reproduced the
published wheat magnitudes: after J9 the 07/08 price ratio was 1.253 against
their 1.361 and world stocks at end-2008 were +23%. J9's gap diagnosis put
roughly 54% of the price shortfall in the harvest-shock channel, 26% in a
baseline price-level drift visible in 2000–2005 with no shock at all, and
the stock gap in six regions where our reconstructed food-balance and trade
tables are furthest off — that is, in the *quantity* inputs.

The author's published NetCDF contains their entire calibrated baseline
(`baseline harvest`, `baseline demand`, `baseline transaction quantity`,
`baseline share foreign sales`, `α domestic`, `baseline price`, …) and their
realized 312-step `harvest` including the shock. J10 inverts those arrays
back into the CSV inputs, so that the only SHEAF content left in the run is
the code's own dynamics. Nothing is fitted and no Julia source or `Params`
default was touched: each replaced CSV is the algebraic inverse of a
published array.

## What `simulate()` derives from which CSV

`src/simulation.jl` 59–102 builds the baseline from three quantity files
plus the parameter file:

| CSV | derived quantity |
|---|---|
| trade-flows (country Origin/Destination/Trade Flow) | region × region off-diagonal flows, via `aggregate_areas` |
| food-balance (Consumption, Imports) | the region's own internal flow (the diagonal), via `infer_trade_flows` as Consumption − Imports |
| both ÷ `N_year` | `baseline_transactions` → production (row sums), consumption (column sums), `sales_share_foreign_baseline`, `alpha_domestic`, market size, purchaser shares, supplier sets, and the target of the baseline trade QP |
| food-balance Production | country weights inside `aggregate_harvest_distributions` only |
| harvest-distributions (365 daily shares) | `baseline harvest` (24 per producer) |
| harvest-anomalies / harvest-trends | `harvest_forcings = 1 + anomaly/trend` → `harvest` (312) |

## Invertibility

**Exactly invertible from the published arrays.** Annual production per
region = Σ over steps of `baseline harvest`; annual consumption = Σ
`baseline demand`, rescaled by Σproduction/Σdemand (the factor is 1 − 5e−10);
the diagonal of the annual flow matrix = production × (1 − `baseline share
foreign sales`); the daily harvest distribution from `baseline harvest`; the
daily harvest forcing from `harvest`. `α domestic` follows from the three
marginals and serves as an independent check (max |calc − author| = 1.6e−4).

**Over-determined, recovered approximately.** `baseline transaction
quantity` (24×28×28). Its annual sums are the CSV bilateral flows in
principle, but the array is a QP solution at `baseline_tol = 1e-4` with
negatives clipped, so its own marginals are off by up to 10% (demand side)
and 21% (sales side) from the exact `baseline demand` / `baseline sales`. It
is therefore used only as the *prior* for the off-diagonal flows, which are
then rescaled onto the exact marginals by iterative proportional fitting
(36 sweeps, max marginal error 5.1e−10 kt).

**Not recoverable.** The author's *pre-cutoff* trade network:
`apply_cutoffs_to_trade_network` drops flows below 1% of both partners
before anything is written out, and `aggregate_export_restrictions` reads
the pre-cutoff network for each exporter's `export_fraction`. Also the eight
solver outputs (producer Nash equilibrium, consumer baseline fixed point,
baseline trade QP) — these cannot be set from CSVs and are the test.

## Construction choices

- Each region's quantities are carried by a single hub country, so
  aggregation is an identity rather than a sum. For the ten restricted
  regions the hub is the country J9 used, so `export_fraction` is exactly 1
  and the restriction Value is the author's value verbatim.
- Three regions (Pakistan, Rest of Europe, Rest of Southern Asia) have zero
  post-cutoff foreign sales, so a 1e−6 kt pseudo-flow keeps their
  restriction rows alive. Those pseudo-flows are removed by the cutoff and
  never enter the baseline. This is what lets J10 match **all ten** of the
  author's restricted regions, where J9 matched nine.
- Middle Africa is given a food-balance Consumption below its imports, so
  its inferred internal flow is negative, `infer_trade_flows` skips it, and
  the region has no producer — as in the author's file.

## Verification at `t_max = 0`

`scripts/check_agrimate_authorbase_t0.jl`, log
`agrimate-2025/j10_check.log`. Part A re-runs the paper's own input pipeline;
part B compares a `t_max = 0` run's solver outputs; part C is the J8/J9
input set as the before/after control.

Input-derived (part A), max relative difference against the author:

| quantity | max abs | max rel |
|---|---|---|
| baseline harvest (24×28) | 5.2e−3 kt | 1.4e−7 |
| annual production (28) | 4.8e−5 kt | 3.7e−10 |
| annual consumption (28) | 4.8e−5 kt | 4.0e−10 |
| baseline share foreign sales | 4.9e−5 | 4.9e−5 |
| α domestic | 2.0e−4 | 2.0e−4 |
| ψ, A_d*, A_c* | 0 | 0 |
| harvest (312×28) | 7.7e−3 kt | 2.1e−7 |
| export restriction (312×28) | 0 | 0 |

All ten restricted regions match the author at every step, with identical
active-step counts and maxima.

Solver outputs (part B) against the control (part C):

| quantity | J10 max rel | J8/J9 control max rel |
|---|---|---|
| baseline price | 0 | 3.1e−2 |
| baseline sales | 5.2e−8 | 1.5e−1 |
| baseline producer storage | 3.6e−8 | 3.9e−1 |
| baseline demand | 2.0e−8 | 4.7e−2 |
| baseline consumer storage | 4.9e−9 | 2.0e−2 |
| baseline consumption | 2.0e−8 | 4.5e−2 |
| baseline consumer price | 0 | 1.9e−2 |
| baseline transaction quantity | 6.3e−3 | 1.3e−1 |

The baseline state the model initializes from is now the author's, to
solver tolerance. The one residual is `baseline transaction quantity` at
0.63% relative (30 kt max), which is the baseline trade QP: our IPF-rescaled
flow prior is not bit-identical to their pre-cutoff network, and the QP
target differs slightly as a result. The control column is the same
comparison for the J9 inputs, where the baseline was off by 15–39%.

## Run

`agrimate-2025/run_j10.sh` → `run_j10_authorbase_harvest_restrictions.jl`,
inputroot `data/agrimate_input_authorbase`, outputroot `data_authorbase`,
logs `j10_harvest_restrictions.{log,start,end}`. Scenario is unchanged from
J9: `production_anomalies="FAOsince-2005"`, `export_restrictions="2007-2011"`,
312 steps.

## What this run tests

With parameters, restrictions, the realized harvest series and the
initialization baseline all the author's own, a remaining gap in the crisis
dynamics can no longer be attributed to our reconstructed inputs. It would
have to come from the code path itself — package versions, solver behaviour,
or a difference between the published `agrimate-equal-sales-penalty` tree
and what produced the published NetCDF. A matching run would say the
published code reproduces the published results and that our input
reconstruction was the whole of the earlier gap.

## Interim result at step 240 of 312 (2026-10-06)

The output NetCDF is rewritten whole after each 24-step chunk, so the
completed prefix is valid output and can be scored while the run continues
(`scripts/peek_agrimate_partial_run.jl`, price and stock definitions copied
from `compare_agrimate_julia_runs.jl`). Through 2009-12:

| metric | J9 | **J10** | author |
|---|---|---|---|
| 2000–2005 mean world price | — | **1.0589** | 1.0590 |
| 2007/08 price ratio (Jul 07 – Jun 08) | 1.253 | **1.359** | 1.361 |
| peak world price | 1.767 (Jun 08) | **2.216 (May 08)** | 2.223 (May 08) |
| monthly price correlation | 0.847 | **1.000** | — |
| end-2008 world stocks | +22.7 % | **+0.1 %** | — |

End-of-year world stocks are within 0.5 % for every year 2000–2009 and
within 0.05 % for seven of the ten. The baseline price-level drift that J4
flagged is gone.

**This is a reproduction.** The published code, given the authors' own
calibration, reproduces their published wheat results. The gap measured in
J4, J8 and J9 was SHEAF's reconstruction of the unpublished input tables —
not the code, the parameters, the restriction series, or a misreading of
the model. Classification **H** for the code path, **F** for the public
reproducibility of the inputs; confidence 95–100 % on the metrics above,
which are directly reproduced.

Still open until the run finishes: the 2010/11 price ratio (author 1.219),
which needs steps through mid-2011, and the end-2012 stock level.

## Run cost

The 2010–2013 window is solving far more slowly than the rest of the run
(20–36 min/step against 2–3 min/step earlier, with Julia holding a full
core, so this is solver difficulty rather than system load). The
`Internal error: encountered unexpected error in runtime` traces in the log
are a known Julia 1.6 inference hiccup that the runtime recovers from; the
same 16 appear in the J2, J3 and J9 logs, all of which completed with
exit 0.

Final scoring to follow against the author's harvest+restrictions run,
using the J4/J8/J9 metrics.
