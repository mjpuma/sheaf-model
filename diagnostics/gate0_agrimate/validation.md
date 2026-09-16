# Agrimate Gate 0 wheat — validation snapshot

Command: `python scripts/run_agrimate_wheat.py --start-year 2003 --end-year 2011`

Independent implementation of Kuhla et al. (2025) §D; not a bit-reproduction
of Zenodo 14022004 (code not retrieved).

- regions: 28
- failed supplier solves: 0
- fallback: 0
- unconverged (feasible but scipy not success): 1043
- inverse-demand floor binds (offers): 0
- max plan residual: 0.000e+00
- runtime: 14.0s
- Nash IBR: 0 err=1.674881360693689e-16 success=True
- min S_p / S_c: 0.0000 / 0.0000
- price index min/max: 0.0066 / 5.0159
- 2006–11 Pink Sheet corr: -0.204
- 2007/08 hike model/obs: ×2.62 / ×1.88

A worse Pink-Sheet fit than the legacy host is not a reason to restore
fill-target, calm pin, scarcity blend, or rival markup.

## G0-N (supplier programme)

Always-feasible `(fd, fi) ∈ [0, 1]` map of D.11–D.21; rolling forthcoming
year `[t, t+Nyear)`; Jacobi IBR against D.22 expected rivals; D.7 argument
`(XI_r + Q_{-r}) / XI*_world`. Not L1–L8. Success = finite and `S ≥ 0`.
Unconverged counts scipy `success=False` on a still-feasible point.
Plan-path floor hits are mostly off-season `XD = 0` when `H = S = 0`
(domestic `q` at the numerical floor with zero sales). Offer-floor binds
are the market-relevant count.

2006-only smoke (same host): failed=0, fallback=0, offer-floor=0,
price index ≈ 0.010–2.95, runtime ≈ 1.5 s. Pre-G0-N host: failed 344,
fallback 417 of 672, price index ≈ 0.0006–1.00 because failed plans kept
Nash offers.
