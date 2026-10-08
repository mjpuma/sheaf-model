# G1-prep rice: Nash NaN (2026-10-08)

`python drivers/run.py --crop rice --anomalies --restrictions --t-max 0`
ran ~12.5 h at 99% CPU and never wrote a NetCDF. Killed at iteration 573.

From iteration 1:

```
Max S_beg difference / X_star: NaN
Max X difference / X_star: NaN
Tolerance / X_star: NaN
```

`Tolerance / X_star` is also NaN, so global `X_star` is NaN, not a slow
solver. `X_star = sum(mean baseline harvest)`. One non-finite harvest
vector poisons the sum. Nash does not treat NaN as failure (`max_iter =
750`), then `@assert succes == true` would have killed the run.

## Cause

`aggregate_harvest_distributions` production-weights daily calendars and
divides by regional production. Two rice regions have **production 0**:

| region | production | consumption | imports | inferred internal |
|---|---:|---:|---:|---:|
| Canada | 0 | 357 | 360 | −2.7 (diagonal skipped) |
| Rest of Oceania | 0 | 197 | 197 | 0 (zero diagonal kept) |

0/0 → NaN days → `simulation.jl` maps NaN → 0 →
`generate_baseline_harvest_timeseries` does `production / sum(harvests)`
= 0/0 → NaN harvests → NaN `X_star`. Wheat has production in every
Agrimate region; maize does too on these CSVs.

## Fix

`agrimate_julia/src/preprocess.jl` (listed in `UPSTREAM.md`): if the
calendar has no mass, return zeros and do not create that producer.
Importers stay consumers. Not a `Params` change and not substitution.

Rerun after the guard: Nash in 357 iterations, `rice_exit=0`, NetCDF
written under `agrimate_julia/data_g1prep_rice/netcdf/`. Maize still
open (`--crop maize --t-max 0`).
