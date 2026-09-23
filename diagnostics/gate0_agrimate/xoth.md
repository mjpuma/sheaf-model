# Domestic others in supplier D.7

Live `solve_supplier_plan` now uses the sourced wheat domestic inverse
demand: `p_d = P((x_dom + share_imp × expected_others_foreign) / C*)`.
`C*` is baseline consumption (`WheatData.C_star`), the same denominator
as posted-price `arg_d`. Foreign D.7 stays `(xi + others) / XI*_world`.
Independent Python. Not a Julia copy. `plan_maxiter` stays 40. αI stays
3.2. No 2006 pin. No Gate 1. x1 lock and uniform `x_init` are unchanged.
`revenue_curve` was not added.

Undisturbed 2003–11 was re-run (anomalies off, restrictions off). S1
CSVs and `prices_undisturbed_xinit.csv` were not rewritten.

## Undisturbed re-measure (scores 2006–11)

| | B2 xoth | B1 months (x-init path) | Bar B Fig. 4 |
|---|---:|---:|---:|
| last/first (volume-weight) | 1.497 | 1.189 | 1.004 |
| last/first (equal-weight) | 2.549 | 1.224 | 1.004 |
| moy max/min volume-weight | 4.60× | 4.85× | 1.32× |
| moy max/min equal-weight | 11.07× | 8.77× | 1.32× |
| seas corr 2006 vs 2011 vw / eq | 0.431 / 0.282 | 0.730 / 0.849 | 0.991 |
| 2006 mean USD vw / eq | 141 / 384 | 160 / 323 | — |
| 2011 mean USD vw / eq | 211 / 978 | 190 / 396 | — |
| unconverged / failed | 4995/5832 / 0 | 5078/5832 / 0 | — |
| runtime | 67.1s | 68.3s | — |

2006 equal-weight months, USD: 690, 693, 164, 258, 795, 495, 231, 195, 201, 179, 355, 346.
2006 volume-weight months, USD: 67, 99, 127, 149, 98, 272, 230, 195, 198, 91, 58, 104.

## 2006 half-month pulse

| step | XI MMT | USD |
|---|---:|---:|
| Jan1 | 32.0 | 45 |
| Jan2 | 0.56 | 1335 |

The half-month pulse remains (and is larger in USD than after B1).
Equal-weight January is $690; volume-weight is $67. Do not raise
`plan_maxiter`. Do not start G1. Next paste B3 (horizon `N_year+1`).
