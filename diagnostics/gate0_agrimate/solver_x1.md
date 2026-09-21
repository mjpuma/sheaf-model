# Solver — current x1 from demand, SLSQP on the rest

Independent Python of the sourced 14022004 wheat supplier
programme (T2 rows 7–8). Not a freeze. Not a pin. Not L1–L8.
Not an αI retune. Not Fig. 4. Do not copy Julia.
`wheat_params()` stay αI=3.2, ζ=0,
N_for=3, plan_maxiter=40.
G1/G2 stay blocked. D.22 vector+shift stays live.

## Verification protocol (CLAUDE.md)

1. **Claim.** Author wheat fixes current sales to demand
   requests (`producer.jl` 116–117) and optimises only future
   steps with NLopt `:LD_SLSQP` (`producer_optimization.jl`
   68–72, 280, 333–355). Host was L-BFGS-B with current sales
   free (`optimize.py`).

2. **Implementation.** `solve_supplier_plan(..., x1=(xd0,xi0))`
   clips `min(D, H+S)` domestic-first, locks step 0, and runs
   scipy SLSQP on the remaining fractions. Live `AgrimateSim.run`
   builds D from last origin-by-buyer requests (iota floor).
   R5 `x1_from_demand` (consumer inflow) stays default off.

3. **Match.** Decision set (x1 fixed) and algorithm family
   (SLSQP) now follow the sourced wheat law. Fraction map still
   enforces S≥0 identically (already equivalent to availability).
   Author used `maxtime=60`; host keeps `plan_maxiter=40` (N5).
   Host horizon is `N_hor` including now, so the free block is
   `N_hor-1` future steps (author stores `N_hor+1` and frees
   `N_hor`). Documented.

4. **Counterexample (pre-change).** L-BFGS-B with free current
   sales is not author wheat. D.22 last/first **0.772** vs author
   **1.004** was that mix: Agrimate eyes, non-Agrimate hands.

5. **Correctness.** Author *does* fix x1 and *does* use SLSQP.
   scipy SLSQP is the independent equivalent (task allowed it).
   Do not vendor NLopt. Do not copy Julia. Do not pin 2006.
   Do not freeze D.22. Do not raise `plan_maxiter`.

6. **Change.** Live supplier programme. Undisturbed 2003–11
   re-measured. Harvest+AMIS three-scenario CSVs untouched.
   Fig. 4 later. Do not start G1.

## Live score (undisturbed, 2006–11)

| object | last/first | 2006 mean | 2011 mean |
|---|---:|---:|---:|
| Host D.22 + x1-SLSQP | 0.812 | $304.92/t | $247.53/t |
| Author Fig. 4 baseline | 1.004 | 1.113 (index) | 1.117 (index) |
| D.22 only (L-BFGS-B, x1 free) | 0.772 | $456.49/t | $352.48/t |
| S1 three-scenario (pre-D.22) | 1.444 | 45.82 | 66.15 |

G0-P item 3 is **fail** (two-sided [1/1.1, 1.1]).
Unconverged 1091/5832; failed 0. Method SLSQP, x1 fixed.
Do not start G1.

**Next paste: leave labelled.** Solver implemented. Exact Fig. 4
is later. Do not copy Julia. Do not write `freeze_q_oth` into
`wheat_params()`.

