# R9 — Unconverged plans on the Fig. 4 comparison object

Repeat of P5 (`solver.md`) on `fig4_experiment_params()`
harvest+AMIS **2006–2008** (short window; USDA 27-node).
**Not a retune.** `wheat_params()` stay αI=3.2, ζ=0, N_for=3,
`plan_maxiter=40`. Fig. 4 knobs are not adopted. L1–L8 stay
rejected. Unforced price is not pinned. G1/G2 stay blocked.

Failed = infeasible (`success=False`). Fallback = non-finite
or infeasible `res.x`, replaced by the start. Unconverged =
feasible accepted plan with scipy L-BFGS-B `success=False`.
Counted separately. Not dropped.

## Failed vs unconverged vs maxiter

| label | maxiter | failed | fallback | unconverged | maxiter-hit | ABNORMAL | n_solves |
|---|---:|---:|---:|---:|---:|---:|---:|
| default (ζ=0) | 40 | 0 | 0 | 611/1944 | 353 | 258 | 1944 |
| fig4 knobs (ζ=1) | 40 | 0 | 0 | 553/1944 | 455 | 98 | 1944 |
| fig4 knobs probe | 200 | 0 | 0 | 115/1944 | 18 | 97 | 1944 |
| fig4 knobs probe | 400 | 0 | 0 | 117/1944 | 0 | 117 | 1944 |

Default 40: unconverged 611/1944, failed=0, fallback=0, residual=0; buckets maxiter=353, ABNORMAL=258.
Knobs 40: unconverged 553/1944, failed=0, fallback=0; maxiter-hit 455, ABNORMAL 98. Median nit=40; pgnorm median 0.3.

P5 on 2003–11 wheat defaults was 1743/5832 (maxiter 1033 +
ABNORMAL 710). This short-window Fig. 4 object is a different
path (ζ=1 turns the xmin quadratic **off**). ABNORMAL here is
evidence about that kink, not a reason to raise the default cap.

## Does a tighter cap unique the knobs path?

| maxiter | unconverged | pidx mean | vs 40 RMSE p | vs 40 max \|Δp\| | vs 40 max \|ΔXI\| |
|---:|---:|---:|---:|---:|---:|
| 40 | 553 | 1.479 | 0 | 0 | 0 |
| 200 | 115 | 1.113 | 0.879 | 4.013 | 22.9 |
| 400 | 117 | 1.007 | 0.997 | 4.013 | 33.5 |

200 vs 400: RMSE p=0.243, max \|Δp\|=1.005, corr=0.988.

**Leave `plan_maxiter=40`.** Raising it on the comparison object
moves p_w without a unique stationary point to adopt. Do not
change `wheat_params().plan_maxiter`. Do not paper over with
L1–L8. Do not adopt Fig. 4 knobs.

Classification **C** (N5 on this object). Not a 2006 pin.

**Next paste: R4.** Item 3 / XI split is still open. R9 does not
unlock G1.
