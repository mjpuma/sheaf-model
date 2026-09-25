# Supplier harvest horizon N_year+1

Live `Hhat` is length `N_year+1`: slot 0 is the current harvest (raw),
slots 1:`N_year` are the existing D.1 `expected_harvest` blend on
`t+1 … t+N_year`. x1 stays locked on slot 0. The free SLSQP block is
`N_year` slots (`2 N_year` fractions). Uniform remaining-grain start
uses that free length. `harvest_weights`, `n_for`, and `tau_for` are
unchanged. Independent Python. Not a Julia copy. `plan_maxiter` stays
40. αI stays 3.2. No 2006 pin. No Gate 1. B2 domestic D.7 is unchanged.

Undisturbed 2003–11 was re-run (anomalies off, restrictions off). S1
CSVs and xoth CSVs were not rewritten.

## Undisturbed re-measure (scores 2006–11)

| | B3 horizon | B2 xoth | Bar B Fig. 4 |
|---|---:|---:|---:|
| last/first (volume-weight) | 0.822 | 1.497 | 1.004 |
| last/first (equal-weight) | 2.641 | 2.549 | 1.004 |
| moy max/min volume-weight | 4.81× | 4.60× | 1.32× |
| moy max/min equal-weight | 15.40× | 11.07× | 1.32× |
| seas corr 2006 vs 2011 vw / eq | 0.398 / 0.539 | 0.431 / 0.282 | 0.991 |
| 2006 mean USD vw / eq | 181 / 449 | 141 / 384 | — |
| 2011 mean USD vw / eq | 149 / 1187 | 211 / 978 | — |
| unconverged / failed | 5125/5832 / 0 | 4995/5832 / 0 | — |
| runtime | 70.3s | 67.1s | — |

2006 equal-weight months, USD: 606, 438, 133, 492, 1642, 549, 213, 204, 193, 166, 445, 314.
2006 volume-weight months, USD: 57, 94, 131, 189, 416, 385, 211, 204, 184, 78, 46, 181.

last/first 0.822 is not item-3 progress: moy is still 4.81×.

## 2006 half-month pulse

| step | XI MMT | USD |
|---|---:|---:|
| Jan1 | 31.0 | 45 |
| Jan2 | 0.32 | 1166 |

The half-month pulse remains. Equal-weight January is $606; volume-weight
is $57. Do not raise `plan_maxiter`. Do not start G1. Next paste B4
(leave labelled leftovers).
