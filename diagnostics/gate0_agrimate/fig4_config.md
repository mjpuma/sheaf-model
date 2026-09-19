# Fig. 4 configuration comparison (R2)

**Labelled comparison, not a retune.** `fig4_experiment_params()`
copies the NetCDF knobs that live on `AgrimateParams`.
`wheat_params()` stay 14022004 defaults (αI=3.2, p_sto=0.1,
xmin=0.2, ζ=0, N_for=3). L1–L8 stay rejected. Bai α_foreign=10
not adopted. G1/G2 not opened. The 2003–11 three-scenario CSVs
were not overwritten.

Window: harvest+AMIS and undisturbed **2006–2008
simulation** (same short window as P6 OAT). Same USDA
`prepare_wheat` quantities for both arms; residual αD follows
D.10 at that arm's αI. Tbl. D.9 named-exporter αD unchanged.

## What this object sets vs cannot set (A7)

**Can set** (copied onto `fig4_experiment_params()`):

- `alpha_i=3.5`
- `alpha_nash=3.0`
- `zeta_penalty=1.0`
- `n_for_months=6`

**Cannot set** (not in the repo / not a param field):

- FAOSTAT Food Balances (A1)
- AgrimateEU28 + Egypt extra (host is AgrimateRegionsWheat: EU-27, Brazil named, Egypt in Northern Africa)
- start 2000-01-01
- FAO production anomalies since 2005
- git old-demand-dynamics
- Zenodo 14022004 author Julia

Host regions: 27 AgrimateRegionsWheat;
Egypt node=False; EU-28=False. FAOSTAT FB files: none. USDA remains
`prepare_wheat` default=True.
`fig4_experiment_region_path()` is `None`.

## harvest+AMIS 2006–08

| arm | αI | ζ | N_for | hike 2008 | moy max/min | failed | unconv / n |
|---|---:|---:|---:|---:|---:|---:|---:|
| default (`wheat_params`) | 3.2 | 0 | 3 | ×2.31 | 26.8× | 0 | 611/1944 |
| Fig. 4 knobs | 3.5 | 1 | 6 | ×2.22 | 13.3× | 0 | 553/1944 |
| author Fig. 4d (this window) | 3.5 | 1 | 6 | ×1.62 | 1.51× | — | — |
| author Fig. 4d (published 2006–11) | 3.5 | 1 | 6 | ×1.62 | 1.45× | — | — |

2003–11 harvest+AMIS on the default host (not re-run here) remains
hike ×4.54, moy max/min ~17.8×, unconverged 1743/5832. This short
window has no 2003–05 spin-up, so default hike is the P6 OAT
number (~×2.31), not ×4.54.

## undisturbed 2006–08 last/first

| arm | last/first | moy max/min | failed | unconv |
|---|---:|---:|---:|---:|
| default | 0.618 | 29.5× | 0 | 583 |
| Fig. 4 knobs | 0.409 | 27.2× | 0 | 432 |
| author (2006–08 on Fig. 4d) | 1.006 | 1.31× | — | — |
| author (2006–11 published) | 1.004 | — | — | — |

Host 2003–11 undisturbed last/first remains **1.63** (not re-run).

## Did the knobs move Fig. 4 metrics?

Hike default ×2.31 → comparison ×2.22 vs author ×1.62 (this window).
Toward author hike: **False**.
moy max/min 26.8× → 13.3× vs author 1.51×. Drop ≥2: **True**.
Adaptive `moved`: **True**.

This is not a reason to adopt the comparison knobs as
`wheat_params()`. ζ=1 turns the xmin penalty *off*; that is the
Fig. 4 experiment, not a Pink-Sheet fit.

Next paste from the adaptive table: **R10**. moy max/min 26.8×→13.3×; score vs author series before treating it as a win.
R11 skipped (`wheat_params` unchanged). R6 remains obtain-or-leave.

## Files

- `score_fig4_config.csv` — two arms × harvest+AMIS + undisturbed
- this note (`fig4_config.md`)

Protected (not written): `prices_three_scenarios.csv`, `score_prices.csv`, `score_supply_stocks.csv`, `annual_undisturbed.csv`, `annual_harvest.csv`, `annual_harvest_amis.csv`.

