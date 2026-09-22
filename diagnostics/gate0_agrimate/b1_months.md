# B1 — monthly scores volume-weight the two half-steps

Live `AgrimateResult.to_monthly_price` / `monthly_price` use the
off-diagonal transaction basket of the two half-steps in each calendar
month (`monthly_transaction_index`), the same construction as
`plot.jl` / `fig4.world_market_price_index`. Equal-weight months stay
on `to_monthly_price_equal`. Empty foreign volume in both half-steps
keeps the previous month.

This is a scoring change, not a new economic law. `wheat_params()`
stay αI=3.2, ζ=0, N_for months=3, plan_maxiter=40. No 2006 pin. No
Julia copy. No G1. 2003–11 was not re-run; numbers are the committed
x-init volume-weight series. S1 CSVs and `prices_undisturbed_xinit.csv`
were not rewritten.

## 2006–11 undisturbed

| | live (volume-weight) | equal-weight (diagnostic) | Bar B Fig. 4 |
|---|---:|---:|---:|
| last/first | 1.189 | 1.224 | 1.004 |
| moy max/min | 4.85× | 8.77× | 1.32× |
| seas corr 2006 vs 2011 | 0.730 | 0.849 | 0.991 |
| 2006 January USD | 86.6 | 412.1 | — |
| 2006 mean USD | 160 | 323 | — |
| 2011 mean USD | 190 | 396 | — |

The Jan1 cheap / Jan2 empty pulse is still in the step path. Scoring
no longer averages it into a $412 January. Next paste B2 (domestic
others in supplier D.7).
