# Gate 0 Bar A prompts (after x-init)

Paste **exactly one** prompt per session. Prepend the shared preamble
in [`GATE0_ALIGN_PROMPTS.md`](GATE0_ALIGN_PROMPTS.md). Template and
hard stops: [`GATE0_CONTINUE.md`](GATE0_CONTINUE.md). Living next-paste:
[`GATE0_REPRO_DISPATCH.md`](GATE0_REPRO_DISPATCH.md).

Do not copy `*.jl` into `sheaf/agrimate/`. Do not raise `plan_maxiter`.
Do not pin 2006. Do not start G1. Fig. 4 1.004 is Bar B, not the twin.

## Rank (why this order)

The half-month pulse is still the live bug (2006 Jan1 22 MMT at $71,
Jan2 0.5 MMT at $753). Equal-weight months turn that into moy 8.77×;
volume-weight months (author `plot.jl`) are 4.85×. Unconverged is
5078/5832 because uniform `x_init` starts far from last period’s plan.

`revenue_curve` on the locked current sale is a **constant** while x1
is demand. Do not spend a session on it. Do not raise `plan_maxiter`
to buy a success flag.

| If the last run showed… | Next paste | Skip |
|---|---|---|
| Live `monthly_price` still equal-weights the two half-steps | **B1** | do not re-open x_init; do not retune |
| B1 done; supplier D.7 is still `xd/XD*` with no others | **B2** | do not switch USDA; do not copy Julia |
| B2 done; host horizon is still `N_year` including now | **B3** | do not change `n_for`; `plan_maxiter` stays 40 |
| Pulse still there after B2/B3 | **B4** leave labelled | wait; do not start G1 |

---

## B1 — Score months the way `plot.jl` does

```
[SHARED PREAMBLE]

Task B1 only. Bar A monthly scores must volume-weight the two
half-steps of each calendar month by off-diagonal transaction
quantity, then volume-weight price. That is plot.jl
plot_wm_price_timeseries, already reconstructed as
fig4.world_market_price_index and as prices_undisturbed_xinit_vw.csv.
Host monthly_price / to_monthly_price still mean the two steps
equally, which is why 2006 January prints $412 instead of $87.

Implement that aggregator on AgrimateResult when tx_quantity and
tx_price exist. Keep the equal-weight series as a diagnostic column
or helper; live last/first, moy, and seas corr used in dispatch
must read the volume-weighted months. Empty foreign volume in both
half-steps keeps the previous month (same empty rule as
foreign_transaction_index).

Do not change wheat_params(). Do not raise plan_maxiter. Do not
retune. Do not pin 2006. Do not copy Julia. Do not start G1.
Do not clobber S1 three-scenario CSVs, prices_undisturbed_xinit.csv,
or score_xinit.csv.

Tests: unit test two-step basket (heavy cheap step + empty expensive
step) matches volume-weight, not the mean. pytest tests/agrimate.
You may re-score 2006–11 from the committed xinit run if you can
reproduce prices_undisturbed_xinit_vw.csv; a full 2003–11 re-run is
not required unless the live aggregator disagrees.

Read first: diagnostics/gate0_agrimate/xinit.md, world_price.md,
sheaf/agrimate/fig4.py world_market_price_index, validation.monthly_price,
model.AgrimateResult.to_monthly_price.

Write diagnostics/gate0_agrimate/b1_months.md with equal-weight vs
volume-weight last/first, moy, 2006 January. Rewrite
GATE0_REPRO_DISPATCH.md (≤20 lines). Next paste: B2.
Do not start G1.
```

---

## B2 — Domestic others in the supplier inverse demand

```
[SHARED PREAMBLE]

Task B2 only. One sourced wheat law: domestic D.7 inside
solve_supplier_plan.

Author (producer.jl 160, 808–811; initialization.jl 151):
  x_oth_domestic = share_imports_foreign_sales_other_producers
                  * expected_others_sales_foreign
  p_d = P( (x_dom + x_oth_domestic) / X_star_domestic, α_domestic, λ )
X_star_domestic is baseline consumption of that node, not XD*.
Host optimize.py still uses q_d = xd / XD* and no others.

Independent Python. Pass the existing D.22 Q row (or the
communication others_next vector used for posted prices) and
share_imp[r] into the planner. Denominator is C_star[r]
(WheatData.C_star; same object as posted-price arg_d). Foreign D.7
stays (xi + others) / XI*_world. Do not add revenue_curve. Do not
change x1 lock. Do not change uniform x_init. Do not raise
plan_maxiter. Do not copy Julia. Do not pin. Do not start G1.

wheat_params() stay αI=3.2, ζ=0, N_for months=3, plan_maxiter=40.
Fig. 4 still uses apply_alpha_i D.9 on its own path.

Re-measure undisturbed 2003–11 (anomalies off, restrictions off).
Write NEW files only: prices_undisturbed_xoth.csv,
prices_undisturbed_xoth_vw.csv, score_xoth.csv, xoth.md.
Report last/first, moy, seas corr, unconverged, and a 2006
half-month table (Jan1/Jan2 XI and usd). Do not clobber S1 CSVs
or the xinit CSVs.

Read first: xinit.md, rt_solver.md, t2_delta.md, optimize.py
_plan_objective_grad, model.py communication block, producer.jl
160 and 808–811 (inspect; do not vendor).

pytest tests/agrimate. Rewrite GATE0_REPRO_DISPATCH.md.
Next paste: B3 if the Jan1/Jan2 pulse remains; B4 if it is gone
and only labelled leftovers remain. Do not start G1.
```

---

## B3 — Horizon is current harvest plus N_hor expected slots

```
[SHARED PREAMBLE]

Task B3 only. One sourced wheat law: supplier harvest vector length.

Author: H = vcat(producer.harvest, producer.expected_harvests)
with expected_harvests[t, n] blending baseline and realised at t+n,
n = 1:N_hor (expected_harvests.jl 13–21; producer.jl 120).
Optimizer free variables are n = 2:N_hor+1 after x1 lock
(producer_optimization.jl 68–72). Host Hhat is length N_year
including now; free block is N_year−1.

Independent Python: build length N_year+1, slot 0 = current
harvest (raw), slots 1:N_year = existing expected_harvest blend
starting at t+1. Keep x1 lock on slot 0. Free SLSQP block is
then N_year slots (2 N_year fractions). Uniform remaining-grain
start uses that free length. Do not change n_for, tau_for, or
harvest_weights. Do not raise plan_maxiter. Do not copy Julia.
Do not pin. Do not start G1.

wheat_params() stay αI=3.2, ζ=0, N_for months=3, plan_maxiter=40.

Re-measure undisturbed 2003–11. NEW files only
(prices_undisturbed_horizon.csv, score_horizon.csv, horizon.md).
Report last/first, moy (equal and volume-weight), unconverged,
2006 Jan1/Jan2. Do not clobber S1 or xoth CSVs.

Read first: expected_harvests.jl (inspect), equations.expected_harvest,
model.py H_roll, optimize.solve_supplier_plan, xoth.md if present
else xinit.md.

pytest tests/agrimate. Rewrite GATE0_REPRO_DISPATCH.md.
Next paste: B4. Do not start G1.
```

---

## B4 — Leave labelled (only if B2/B3 did not kill the pulse)

```
[SHARED PREAMBLE]

Task B4 only. Inspect-only. Do not implement. Do not raise
plan_maxiter. Do not copy Julia. Do not pin. Do not start G1.

Write diagnostics/gate0_agrimate/leftovers.md, one row each:

1. revenue_curve on locked x1 (constant; why it cannot move the pulse)
2. quantity inequalities vs host fractions (S≥0 identically)
3. maxtime=60 / XTOL retries vs plan_maxiter=40
4. S_p=0 vs author baseline_storage
5. closed-form nash_ibr vs equilibrate_producers!
6. harvest-weight index (host w(1) on current vs author expected
   starting at t+1) if B3 did not already close it

Columns: author file:line, host file:line, class (C/D/E/H),
could-move-the-pulse (yes/no), implement-now (yes/no). Rank at
most one implement-now row, and only if a 2006 Jan1/Jan2
counterexample shows the host law is not the author law.

Read first: xoth.md, horizon.md, rt_solver.md, t2_delta.md,
align_inventory.md.

Do not re-run 2003–11 unless a counterexample requires a number
already not in the CSVs. Rewrite GATE0_REPRO_DISPATCH.md.
Next paste: that one implement-now row, or wait. Do not start G1.
```
