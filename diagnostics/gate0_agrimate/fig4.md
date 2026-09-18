# Agrimate Fig. 4 — author series vs this host (P7)

Independent implementation. Do **not** claim replication.

## G0-U items 1–3 (before historical fit)

Pass rule from `DEVELOPMENT.md`: items 1–3 must be honest before
judging item 5. P2 drift remains unexplained; this page still
compares, and it does not claim replication.

1. **Source fidelity.** Met for retrieved Zenodo 14022004 code with
   labelled S3/S4/A1–A6/N5. The Fig. 4 NetCDF is a *different*
   executable than that host (see experiment mismatch below).
2. **Numerical reliability.** Plans are feasible (residual 0,
   failed/fallback 0) but **not** first-order stationary: harvest+AMIS
   unconverged scipy 1743/5832 (N5). Counted, not papered over.
3. **Undisturbed dynamics.** Seasonal shape repeats (corr 0.98) but
   the annual-mean world-price ratio 2011/2006 is **1.63** (`undisturbed.md`).
   Author Fig. 4 baseline on the same window is repeating
   (last/first = 1.004,
   seasonal corr 0.991).
   P2 drift is unexplained. Not a price pin.

## Author experiment (Zenodo 10688435 main_output)

- record: 10.5281/zenodo.10688435; data.zip md5 `2f3809c66e78b72b3c74971051f89529`.
- region set: `AgrimateEU28` + extra Egypt=EGY (27 nodes;
  Egypt split out; EU-28 not EU-27;
  Brazil is inside Rest of South America). Host is AgrimateRegionsWheat
  (Brazil named, EU-27, Egypt inside Northern Africa).
- α_foreign=`3.5`; α=`3.0`;
  ζ=`1.0`; N_for=`6`;
  p_sto=`0.1`; σ=`2.0`; ε_c=`0.1`.
- anomalies: FAO since 2005; restrictions 2007–2011; baseline 2007–2009;
  start `2000-01-01`; crop `wheat`.
- gitcommit `old-demand-dynamics-150-gbfc02cb-dirty` (old-demand-dynamics, not
  the later 14022004 equal-sales-penalty tree).
- World price in Fig. 4d is the volume-weighted international
  transaction price, not D.7 on world XI*. Host scores D.7 × p0 / p0.
- PDF digitisation in `diagnostics/redteam/r5/` was **not** used.

Host defaults stay 14022004 `AgrimateParams` (αI=3.2, ζ=0 penalty on,
N_for=3 months). No retune to Fig. 4 knobs or to Bai α_foreign=10.

Score window 2006–2011. Pink Sheet stays a side column;
the target here is the author series.

## World-market price index vs Fig. 4d

| scenario | corr (index) | RMSE index | corr (2006=1) | 2008 hike host | hike author | 2006 mean host | 2006 author |
|---|---:|---:|---:|---:|---:|---:|---:|
| undisturbed | 0.912 | 0.846 | 0.912 | ×4.78 | ×1.12 | 0.202 | 1.113 |
| harvest | 0.403 | 0.848 | 0.403 | ×4.53 | ×1.44 | 0.306 | 1.183 |
| harvest_amis | 0.577 | 0.856 | 0.577 | ×4.54 | ×1.62 | 0.306 | 1.183 |

Author harvest+AMIS 2008 hike is the published-experiment number to
beat, not Pink Sheet ×1.88. Host hike remains several times larger
and 2006 levels are ~0.3 vs author ~1.1. Correlation of the raw
index is not a replication claim.

## World supply / consumption / stocks vs Fig. 4 series

Author units 1000 t, converted /1000 → MMT. Host is the 27-node USDA
sum (A1). Level bias is expected. Undisturbed production corr is nan
because both series are constant (author repeating FAO baseline,
host repeating USDA 2007–09 mean) at different levels (542 vs 631 MMT).

| scenario | field | corr | RMSE | mean host | mean author |
|---|---|---:|---:|---:|---:|
| undisturbed | production | nan | 89.10 | 542.25 | 631.35 |
| undisturbed | consumption | -0.153 | 96.89 | 538.80 | 631.69 |
| undisturbed | exports | 0.586 | 87.83 | 210.11 | 123.04 |
| undisturbed | ending_stocks | -0.859 | 124.26 | 200.88 | 322.93 |
| harvest | production | 0.986 | 82.97 | 541.54 | 624.33 |
| harvest | consumption | 0.224 | 97.69 | 531.38 | 623.19 |
| harvest | exports | 0.055 | 83.53 | 193.34 | 124.78 |
| harvest | ending_stocks | 0.740 | 73.05 | 245.64 | 314.85 |
| harvest_amis | production | 0.986 | 82.97 | 541.54 | 624.33 |
| harvest_amis | consumption | 0.517 | 94.13 | 531.64 | 620.22 |
| harvest_amis | exports | -0.197 | 64.30 | 183.20 | 132.08 |
| harvest_amis | ending_stocks | 0.823 | 80.24 | 248.09 | 325.36 |

## Regional (host tables that exist: Ukraine, Eastern Africa)

Author Egypt is a split node; host folds Egypt into Northern Africa.
EU-28 vs EU-27 is labelled, not equated. Only shared names below.

| scenario | region | field | corr | RMSE | mean host | mean author |
|---|---|---|---:|---:|---:|---:|
| undisturbed | Ukraine | production | nan | 1.13 | 20.23 | 19.10 |
| undisturbed | Ukraine | consumption | -0.031 | 3.20 | 9.34 | 12.17 |
| undisturbed | Ukraine | exports | 0.016 | 4.83 | 11.44 | 6.94 |
| undisturbed | Ukraine | S_producer | 0.322 | 7.82 | 0.04 | 7.86 |
| undisturbed | Ukraine | S_consumer | -0.007 | 1.72 | 0.66 | 2.09 |
| undisturbed | Eastern Africa | production | nan | 2.76 | 0.33 | 3.09 |
| undisturbed | Eastern Africa | consumption | 0.664 | 0.80 | 6.67 | 6.00 |
| undisturbed | Eastern Africa | exports | 0.650 | 0.59 | 0.01 | 0.61 |
| undisturbed | Eastern Africa | S_producer | nan | 1.56 | 0.00 | 1.56 |
| undisturbed | Eastern Africa | S_consumer | -0.391 | 2.30 | 2.76 | 0.62 |
| harvest | Ukraine | production | 0.998 | 1.72 | 20.21 | 18.53 |
| harvest | Ukraine | consumption | -0.083 | 4.52 | 9.82 | 11.09 |
| harvest | Ukraine | exports | -0.677 | 4.82 | 9.84 | 7.52 |
| harvest | Ukraine | S_producer | 0.909 | 4.00 | 4.35 | 7.95 |
| harvest | Ukraine | S_consumer | -0.488 | 1.98 | 1.99 | 2.17 |
| harvest | Eastern Africa | production | 0.658 | 2.62 | 0.33 | 2.94 |
| harvest | Eastern Africa | consumption | -0.336 | 1.21 | 5.95 | 5.90 |
| harvest | Eastern Africa | exports | -0.078 | 0.91 | 0.02 | 0.83 |
| harvest | Eastern Africa | S_producer | 0.517 | 1.30 | 0.00 | 1.29 |
| harvest | Eastern Africa | S_consumer | -0.088 | 2.30 | 2.46 | 0.62 |
| harvest_amis | Ukraine | production | 0.998 | 1.72 | 20.21 | 18.53 |
| harvest_amis | Ukraine | consumption | -0.233 | 3.64 | 10.03 | 11.08 |
| harvest_amis | Ukraine | exports | 0.423 | 3.90 | 9.29 | 7.67 |
| harvest_amis | Ukraine | S_producer | 0.905 | 3.27 | 4.81 | 7.56 |
| harvest_amis | Ukraine | S_consumer | 0.504 | 1.77 | 2.26 | 2.20 |
| harvest_amis | Eastern Africa | production | 0.658 | 2.62 | 0.33 | 2.94 |
| harvest_amis | Eastern Africa | consumption | -0.142 | 1.17 | 5.65 | 5.80 |
| harvest_amis | Eastern Africa | exports | -0.280 | 1.07 | 0.02 | 0.95 |
| harvest_amis | Eastern Africa | S_producer | 0.689 | 1.19 | 0.00 | 1.17 |
| harvest_amis | Eastern Africa | S_consumer | -0.302 | 1.69 | 1.86 | 0.61 |

## Verdict

Independent implementation, Fig. 4 series **in hand**, scored, **not
a replication**. G0-U (3) fails on the host (drift 1.63 vs author
1.00). G0-U (2) is N5, not a unique maximizer. Do not restore L1–L8.
Do not retune αI. See `hindcast.md` (P8) for the G0-H score.

## Files

- `author_fig4/PROVENANCE.txt`
- `author_fig4/monthly_world.csv`, `annual_world.csv`, `annual_regional.csv`
- `score_fig4_prices.csv`, `score_fig4_supply.csv`, `score_fig4_regional.csv`
- `figures/fig4_author_vs_host_prices.png` (diagnostic overlay)

