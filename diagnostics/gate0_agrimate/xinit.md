# Uniform supplier start — remaining grain / free slots

Live SLSQP (`x1` locked) starts from an even split of remaining grain
over the free domestic and foreign slots, then clips to the fraction
map. That is independent Python of producer_optimization.jl 349–351.
The previous plan is no longer the start. `plan_maxiter` stays 40.
αI stays 3.2. No Julia copy. No 2006 pin. No Gate 1.

Author months volume-weight the two half-steps (`plot.jl`). Host
`monthly_price` still averages them equally. Both are scored here.

## Undisturbed re-measure (2003–11, anomalies off, restrictions off; scores 2006–11)

| | x_init | α_adj (old start) | Bar B Fig. 4 |
|---|---:|---:|---:|
| last/first (equal-weight months) | 1.224 | 0.895 | 1.004 |
| last/first (volume-weight months) | 1.189 | — | 1.004 |
| moy max/min equal-weight | 8.77× | 20.1× | 1.32× |
| moy max/min volume-weight | 4.85× | — | 1.32× |
| 2006 mean USD equal / vw | 323 / 160 | 498 / — | — |
| 2011 mean USD equal / vw | 396 / 190 | 446 / — | — |
| unconverged / failed | 5078/5832 / 0 | 1890/5832 / 0 | — |
| runtime | 68.3s | 51.1s | — |

2006 equal-weight months, USD: 412, 552, 147, 287, 772, 380, 203, 178, 192, 177, 251, 329.
2006 volume-weight months, USD: 87, 121, 125, 172, 211, 383, 171, 177, 186, 122, 62, 101.

The half-month pulse is still there. 2006 Jan1 ships 22.1 MMT at $71;
Jan2 ships 0.5 MMT at $753. Equal-weight January is $412; volume-weight
is $87. Unconverged solves rose: a start far from last period's plan
rarely reports SLSQP success in 40 iterations. Do not raise
`plan_maxiter`. Do not start G1. S1 CSVs and `prices_undisturbed_alpha_adj.csv`
were not rewritten.
