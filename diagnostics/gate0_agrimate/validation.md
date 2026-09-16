# Agrimate Gate 0 wheat — validation snapshot

Command: `python scripts/run_agrimate_wheat.py`

Independent implementation of Kuhla et al. (2025) §D on branch
`cursor/agrimate-gate0-baseline-3857`. Not a bit-reproduction of Zenodo
14022004. The Mac commit `9126e40` was never pushed; this is a source-grounded
rebuild from the first-principles deck HEAD `06d0104`.

## One-year smoke (2006)

- 28 regions; Nash δ=ρ=0 sales = harvest (max rel 2e-16)
- price index min/max ≈ 0.0006 / 1.00 (USD ≈ 0.13 / 214)
- failed supplier solves: 344; fallback: 417 of 672
- Failed/fallback plans are **not** replaced by legacy fill-target/pin/blend rules;
  the previous feasible plan is kept and the failure is counted.

12 `tests/agrimate` checks pass (equations, Nash identity, wheat data pins).

A worse or incomplete Pink-Sheet fit is not a reason to restore L1–L8.
