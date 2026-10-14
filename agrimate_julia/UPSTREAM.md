# Upstream Agrimate (vendored)

This directory is a copy of the published Agrimate source from Kuhla,
Kubiczek, Puma, and Otto (2025).

## Attribution

- Kuhla, K., Kubiczek, P., Puma, M. J., & Otto, C. (2025).
  *Agrimate: a process-based model of global annual and intra-annual
  agricultural market dynamics*.
- Source snapshot: Zenodo **10.5281/zenodo.14022004**, folder
  `agrimate-equal-sales-penalty`.
- SHA-256 of `agrimate-model.zip`:
  `4853153bb216a39451a1d7d1b3de1865de8d5fbe758e63c074a1d8c4c8372088`
- Licence: **CC-BY 4.0** (see `LICENSE` in this directory).
- Authors of the Julia code: Patryk Kubiczek and co-authors as listed
  in `Project.toml`.

## What was copied

`src/`, `Project.toml`, `Manifest.toml`, `LICENSE`, and the upstream
README (as `README.upstream.md`). Run outputs and reconstructed input
CSVs were not copied. Package versions are pinned by `Manifest.toml`;
the interpreter is Julia 1.6.5 (Intel build, Rosetta on Apple Silicon).
Do not run `Pkg.update()` or `Pkg.resolve()`.

`AgrimateModel` is the local package at `src/AgrimateModel` (path pin in
the Manifest). Gate 0 verification: this tree, with the authors'
calibrated inputs inverted from their NetCDF, reproduces the published
wheat run (`diagnostics/gate0_julia/J10_authorbaseline.md`).

## Our changes

- `src/preprocess.jl` `generate_baseline_harvest_timeseries` /
  `generate_baseline_harvests`: if the harvest calendar has no mass
  (0/0 after aggregating a region with zero food-balance production),
  return zeros and **do not create that producer**. Wheat never hits
  this; rice Canada and Rest of Oceania have production 0, which made
  `X_star` NaN and Nash spin for 12 h. Not a substitution change.
- Gate 1 start (`diagnostics/GATE1_DESIGN.md`). `ξ::Float64 = 0.0` on
  `AgrimateParams` (not Armington `σ`). Consumer fields
  `substitution_factor` / `_prev` default 1. `A_d` and `A_c*` scaled
  by those factors. `procurement_step!` split into `price_index_step!`
  then `procurement_step!` (same statements, same order). New
  `coupling.jl` (`ρ` matrix, `substitution_factor`). `step_coupled!` /
  `run_model_coupled!`. `initialize_crop` / `prepare_crop_run` hold the
  per-crop setup. `simulate_coupled` at `t_max=0` is three independent
  smokes; at `t_max>0` it builds three `Run`s, checks `start`/`N_year`,
  loads undisturbed purchaser `crop_price_index` as \(\bar P\), and
  steps with `run_model_coupled!`. At `ξ=0`, `step_coupled!` calls
  `step!` on each crop (published purchaser order). The split path is
  only for `ξ≠0`. Undisturbed single-crop runs write
  `reference/crop_price_index_<crop>.csv`. Coupled NetCDF goes under
  `netcdf/coupled/`. Published observation variables are unchanged.
- `communication_step!` calls `_diag` only inside the existing `ι`
  zeroing branch and the existing 1000 price-cap branch. `diag_log`
  defaults to `nothing`, and the callback must not mutate agents.
  The threshold test, the price formula, and `Params` are unchanged.
- `optimize_sales_NLopt_two_markets` records every SLSQP call
  (crop, region, step, call number, return code, evaluations, seconds,
  and the bit pattern of the returned vector) when
  `AGRIMATE_NLOPT_LOG=1`. The file is `AGRIMATE_NLOPT_LOG_PATH`. The
  start points, `xtol_abs`, and the retry tests are unchanged.
- Reproducibility fix to the published SLSQP stop. `maxeval::Int = 116534`
  on `AgrimateParamsMix` (and therefore on `Params`) replaces
  `maxtime = 60`. The three solvers read that budget. Retries still run
  only when the return code is not `XTOL_REACHED`. `MAXEVAL_REACHED`
  appends monitor event `not_converged`. `FAILURE` appends monitor
  event `FAILURE` and the last returned vector is kept, as before.
  The objective, `xtol_abs`, ι, the 1000 cap, and the other `Params`
  defaults are unchanged.
- Performance: after `MAXEVAL_REACHED`, a retry whose start equals an
  earlier `MAXEVAL_REACHED` start is not run. NLopt's `nlopt_optimize`
  (2.7.1 `optimize.c`) zeroes `numevals` and passes that start into
  `nlopt_slsqp`, which builds a zeroed local SLSQP state, so the call
  would repeat. The stored vector is kept. The ±0.01 retries are
  different starts and still run. Retries after `FAILURE`,
  `ROUNDOFF_LIMITED`, and any other non-`XTOL` code still run. The
  periodic solver has no return-code retries. Maize `t_max=4` on
  `44694b6` with this skip was bitwise identical to the unskipped run
  (51.5 s of stepping versus 37.1 s). Objective, `xtol_abs`, ι, the
  cap, and `Params` defaults are unchanged. B_small, B_mid, and B_large
  loaded `44694b6` and were not restarted.
