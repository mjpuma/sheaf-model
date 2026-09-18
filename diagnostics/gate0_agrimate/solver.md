# P5 — Unconverged supplier plans

Harvest+AMIS 2003–11 (`AgrimateParams.plan_maxiter=40`). Probe:
`PYTHONPATH=. python scripts/characterize_agrimate_solver.py`
and the maxiter sweep in `solver_maxiter.json`.

## What “unconverged” is

`solve_supplier_plan` accepts a point when the fraction map is finite and
`S ≥ 0`. `success` / `failed` are that feasibility test. `fallback` is a
non-finite or infeasible `res.x`, replaced by the feasible start.
`converged` is scipy L-BFGS-B `success` and not fallback.

On the reference path: **failed=0, fallback=0, residual=0**,
**unconverged=1743/5832**. Those 1743 are feasible accepted plans with
`scipy.optimize.minimize(..., method="L-BFGS-B")` returning `success=False`.
They stay in the count.

| scipy status | message | count |
|---|---|---:|
| 1 | `STOP: TOTAL NO. OF ITERATIONS REACHED LIMIT` | 1033 |
| 2 | `ABNORMAL:` (line search) | 710 |

Median `nit` among unconverged = 40 (the cap). Median projected-gradient
norm at the accepted point ≈ 2.2×10³ (p90 ≈ 1.3×10⁵). First-order
stationarity is not established.

## Does the accepted point substitute for a tighter solve?

**No, not uniquely; and a tighter cap is not a unique optimum either.**

Full-path harvest+AMIS, same data, only `plan_maxiter` changed:

| maxiter | unconverged | runtime s | pidx mean | vs 40 RMSE p | vs 40 max \|Δp\| | vs 40 max \|ΔXI\| |
|---:|---:|---:|---:|---:|---:|---:|
| 40 | 1743 | 20.0 | 0.547 | 0 | 0 | 0 |
| 80 | 1202 | 23.7 | 0.613 | 0.194 | 0.954 | 36.2 |
| 200 | 801 | 24.0 | 0.509 | 0.167 | 0.929 | 32.2 |
| 400 | 852 | 24.5 | 0.585 | 0.193 | 0.886 | 41.0 |

400 vs 200: RMSE p = 0.220, max \|Δp\| = 1.08, corr = 0.944 — **as large
as 40 vs 400**. At 200, 27 solves still hit the iteration cap and 774 are
ABNORMAL; at 400 every remaining failure is ABNORMAL (852). More
iterations convert maxiter-hits into a different Jacobi path, not into a
shared stationary point.

Isolated replay of 80 default-unconverged snapshots with `maxiter=400`:

- Same start: median \|Δ XI₀\| = 2.5×10⁻⁹; max = 0.20; objective never
  rises (min Δobj = −1853). Current-step international sales usually
  stick; the rest of the horizon can move, and Jacobi feeds that into
  later steps.
- Mid-fraction start: max \|Δ XI₀\| = 3.59 MMT.
- Star start: max \|Δ XI₀\| = 6.05 MMT.
- 52/80 scipy-converged at 400; projected-gradient median still ≈ 1.3×10³.

So the default accepted point is a **feasible local/truncated iterate**,
not a demonstrated unique maximizer. Raising `plan_maxiter` would move
the published price path without a target optimum to move toward.

## Decision (host)

**Leave `plan_maxiter=40`.** Do not add a penalty, pin, or L1–L8 device.
Do not drop unconverged from the count. Observability only: `nit`,
`status`, `message`, `obj`, `pgnorm` on the solve dict.

ABNORMAL line-search is consistent with the xmin quadratic penalty’s
kink (`xd < xmin` in `_plan_objective_grad`). Smoothing that kink would
change the author ζ=0 objective; not done here.

Classification **C** (numerical), confidence **95–100%** on the counts
and path RMSEs (reproduced this run); **80–95%** that ABNORMAL is the
xmin kink rather than a Jac bug (`test_supplier_plan_analytic_grad_matches_finite_difference`
is on the smooth ζ=1 slice).

## G0-N reading

Feasibility (N1) holds. First-order reliability does not: about 30% of
plans on harvest+AMIS are unconverged. That is a labelled solver fact,
not a reason to restore L1–L8 or to pick an arbitrary larger iteration
cap.
