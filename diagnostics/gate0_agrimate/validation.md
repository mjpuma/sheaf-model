# Agrimate Gate 0 wheat — validation snapshot

Command: `python scripts/run_agrimate_wheat.py --start-year 2003 --end-year 2011`

Independent implementation of Kuhla et al. (2025) §D. Author code
https://doi.org/10.5281/zenodo.14022004 retrieved 2026-09-16 as the
executable specification (not copied into this package). Data deposit
10688435 (150 MB) not unpacked.

- regions: 27
- failed supplier solves: 0
- fallback: 0
- unconverged (feasible but scipy not success): 1628
- inverse-demand floor binds (offers): 0
- max plan residual: 0.000e+00
- runtime: 19.5s
- Nash IBR: 0 err=2.100126312591429e-16 success=True
- min S_p / S_c: 0.0000 / 0.0000
- price index min/max: 0.0105 / 3.1681
- 2006–11 Pink Sheet corr: -0.160
- 2007/08 hike model/obs: ×4.53 / ×1.88

A worse Pink-Sheet fit than the legacy host is not a reason to restore
fill-target, calm pin, scarcity blend, or rival markup.

## G0-N (supplier programme)

Always-feasible `(fd, fi) ∈ [0, 1]` map of D.11–D.21; rolling forthcoming
year `[t, t+Nyear)`; Jacobi IBR against D.22 expected rivals; D.7 argument
`(XI_r + Q_{-r}) / XI*_world`. Not L1–L8. Success = finite and `S ≥ 0`.

## G0-S (source)

Wheat defaults follow author `AgrimateParams` (αI=3.2, τ=0.1, σ=2, εc=0.1,
p_sto=0.1/Nyear, x_min=0.2 penalty, ζ=0). C.1 wheat nodes are the 27-name
`AgrimateRegionsWheat` list. E.27 and D.1 weights match author harvest and
`expected_harvests.jl`. Tbl. D.8 αI=3.5 / τ=0.2 kept as `wheat_table_d8_defaults()`.
Unresolved: β/τ_P local price, nested purchaser D.30a, FAOSTAT FB (A1),
Fig. 4 author series (data zip not unpacked).

2006-only smoke: failed=0, fallback=0, offer-floor=0, price index ≈ 0.045–3.67.
