# Clearing loop — undisturbed re-measure

One change: prorate last period's requests (foreign × (1−Δ), price =
the reservation posted with the request); post next-step expected
prices (cap 1000); scale baseline purchase shares by expected sales /
XD* or XI* and renormalize. Delivery is the lagged buyer receipt.
`wheat_params()` stay αI=3.2, ζ=0, N_for months=3, plan_maxiter=40.
No 2006 pin. No retune. No Julia copy. S1 three-scenario CSVs and
`prices_undisturbed_solver_x1.csv` were not rewritten.

## Window

Undisturbed USDA wheat, 2003–11, anomalies off, restrictions off.
Scores are 2006–11. Bar B is Zenodo 10688435 Fig. 4 baseline
(AgrimateEU28+Egypt, FAO since 2005, α_foreign=3.5, ζ=1). It is not
the 14022004 twin. This run did not execute Julia.

| | clearing | prior solver | Bar B |
|---|---:|---:|---:|
| last/first | 1.777 | 0.812 | 1.004 |
| 2006 mean USD | 285.83 | 304.92 | — |
| 2011 mean USD | 507.87 | 247.53 | — |
| moy max/min | 5713× | 2374× | 1.32× |
| seas corr 2006 vs 2011 | 0.942 | 0.987 | 0.991 |
| unconverged / failed | 1180/5832 / 0 | 1091/5832 / 0 | — |
| runtime | 62.5s | 62s | — |

Index over the whole 2003–11 path spans about 0.00048 to the cap 1000
(mean about 27). Month-of-year amplitude is larger than the prior
solver path. The seasonal swing is still huge. Supplier leftovers
(horizon N_hor+1, revenue_curve on the locked step, domestic x_oth,
quantity inequalities, uniform x_init, maxtime=60) were not started.

## What this is

The live world price is the off-diagonal transaction index
(`foreign_transaction_index`), same construction as
`fig4.world_market_price_index`, with empty volume keeping the previous
price. `plot_wm_price_timeseries` is still absent from this tree.
Do not pin 2006. Do not start G1. `wheat_params()` unchanged.
