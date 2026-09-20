# Agrimate Fig. 4 — author series vs this host (P7 / S5)

Independent implementation. Do **not** claim replication.
S5 re-scores the S1 member-sum CSVs. Not R11: the NLP runner
was not re-run. `wheat_params()` stay αI=3.2.

## G0-U items 1–3 (before historical fit)

Pass rule from `DEVELOPMENT.md`: items 1–3 must be honest before
judging item 5. P2 drift remains unexplained; this page still
compares, and it does not claim replication.

1. **Source fidelity.** Met for retrieved Zenodo 14022004 code with
   labelled S3/S4/A1–A6/N5. The Fig. 4 NetCDF is a *different*
   executable than that host (see experiment mismatch below).
2. **Numerical reliability.** Plans are feasible (residual 0,
   failed/fallback 0) but **not** first-order stationary: harvest+AMIS
   unconverged scipy 2304/5832 (N5). Counted, not papered over.
3. **Undisturbed dynamics.** Seasonal shape repeats (corr 0.98) but
   the annual-mean world-price ratio 2011/2006 is **1.444** (`item3.md`).
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
  transaction price, not D.7 on world XI*. Host scores XI-weighted
  lagged D.7 offers × p0 / p0 (`world_price.md`). Author
  `plot_wm_price_timeseries` is not in-tree.
- PDF digitisation in `diagnostics/redteam/r5/` was **not** used.

Host defaults stay 14022004 `AgrimateParams` (αI=3.2, ζ=0 penalty on,
N_for=3 months). No retune to Fig. 4 knobs or to Bai α_foreign=10.

Score window 2006–2011. Pink Sheet stays a side column;
the target here is the author series.

## World-market price index vs Fig. 4d

| scenario | corr (index) | RMSE index | corr (2006=1) | 2008 hike host | hike author | 2006 mean host | 2006 author |
|---|---:|---:|---:|---:|---:|---:|---:|
| undisturbed | 0.893 | 0.835 | 0.893 | ×4.87 | ×1.12 | 0.215 | 1.113 |
| harvest | 0.594 | 0.766 | 0.594 | ×3.85 | ×1.44 | 0.381 | 1.183 |
| harvest_amis | 0.612 | 0.801 | 0.612 | ×3.71 | ×1.62 | 0.381 | 1.183 |

Author harvest+AMIS 2008 hike is the published-experiment number to
beat, not Pink Sheet ×1.88. Host hike remains several times larger (×3.71 vs ×1.62)
and 2006 levels are 0.38 vs author 1.18. Correlation of the raw
index is not a replication claim.

## World supply / consumption / stocks vs Fig. 4 series

Author units 1000 t, converted /1000 → MMT. Host is the 27-node USDA
sum (A1, S1 member-sum). Level bias is expected. Undisturbed production corr is nan
because both series are constant (author repeating FAO baseline,
host repeating USDA 2007–09 mean) at different levels (662 vs 631 MMT).

| scenario | field | corr | RMSE | mean host | mean author |
|---|---|---:|---:|---:|---:|
| undisturbed | production | nan | 30.69 | 662.04 | 631.35 |
| undisturbed | consumption | -0.228 | 52.36 | 672.82 | 631.69 |
| undisturbed | exports | 0.426 | 96.52 | 218.29 | 123.04 |
| undisturbed | ending_stocks | -0.245 | 110.05 | 214.02 | 322.93 |
| harvest | production | 0.999 | 37.08 | 661.38 | 624.33 |
| harvest | consumption | 0.564 | 37.08 | 657.00 | 623.19 |
| harvest | exports | -0.254 | 56.68 | 179.42 | 124.78 |
| harvest | ending_stocks | 0.954 | 76.49 | 239.22 | 314.85 |
| harvest_amis | production | 0.999 | 37.08 | 661.38 | 624.33 |
| harvest_amis | consumption | 0.303 | 43.44 | 649.20 | 620.22 |
| harvest_amis | exports | -0.035 | 47.99 | 176.67 | 132.08 |
| harvest_amis | ending_stocks | 0.870 | 69.46 | 259.41 | 325.36 |

## Regional (host tables that exist: Ukraine, Eastern Africa)

Author Egypt is a split node; host folds Egypt into Northern Africa.
EU-28 vs EU-27 is labelled, not equated. Only shared names below.

| scenario | region | field | corr | RMSE | mean host | mean author |
|---|---|---|---:|---:|---:|---:|
| undisturbed | Ukraine | production | nan | 1.13 | 20.23 | 19.10 |
| undisturbed | Ukraine | consumption | 0.149 | 4.17 | 8.97 | 12.17 |
| undisturbed | Ukraine | exports | 0.517 | 6.23 | 11.87 | 6.94 |
| undisturbed | Ukraine | S_producer | -0.304 | 7.70 | 0.16 | 7.86 |
| undisturbed | Ukraine | S_consumer | 0.453 | 1.64 | 0.77 | 2.09 |
| undisturbed | Eastern Africa | production | nan | 0.22 | 3.31 | 3.09 |
| undisturbed | Eastern Africa | consumption | 0.715 | 3.67 | 9.40 | 6.00 |
| undisturbed | Eastern Africa | exports | 0.569 | 0.41 | 0.23 | 0.61 |
| undisturbed | Eastern Africa | S_producer | 0.364 | 1.56 | 0.00 | 1.56 |
| undisturbed | Eastern Africa | S_consumer | -0.691 | 2.13 | 2.68 | 0.62 |
| harvest | Ukraine | production | 0.998 | 1.72 | 20.21 | 18.53 |
| harvest | Ukraine | consumption | 0.078 | 3.81 | 9.87 | 11.09 |
| harvest | Ukraine | exports | 0.003 | 4.29 | 9.74 | 7.52 |
| harvest | Ukraine | S_producer | 0.925 | 3.76 | 4.58 | 7.95 |
| harvest | Ukraine | S_consumer | -0.476 | 2.15 | 2.21 | 2.17 |
| harvest | Eastern Africa | production | 0.658 | 0.38 | 3.25 | 2.94 |
| harvest | Eastern Africa | consumption | 0.159 | 2.52 | 8.10 | 5.90 |
| harvest | Eastern Africa | exports | 0.681 | 0.59 | 0.37 | 0.83 |
| harvest | Eastern Africa | S_producer | -0.442 | 1.30 | 0.00 | 1.29 |
| harvest | Eastern Africa | S_consumer | -0.049 | 1.41 | 1.98 | 0.62 |
| harvest_amis | Ukraine | production | 0.998 | 1.72 | 20.21 | 18.53 |
| harvest_amis | Ukraine | consumption | -0.332 | 5.38 | 8.12 | 11.08 |
| harvest_amis | Ukraine | exports | -0.601 | 6.66 | 10.95 | 7.67 |
| harvest_amis | Ukraine | S_producer | 0.897 | 3.16 | 4.79 | 7.56 |
| harvest_amis | Ukraine | S_consumer | 0.434 | 2.40 | 2.43 | 2.20 |
| harvest_amis | Eastern Africa | production | 0.658 | 0.38 | 3.25 | 2.94 |
| harvest_amis | Eastern Africa | consumption | 0.324 | 2.50 | 7.90 | 5.80 |
| harvest_amis | Eastern Africa | exports | -0.018 | 0.76 | 0.41 | 0.95 |
| harvest_amis | Eastern Africa | S_producer | -0.102 | 1.19 | 0.00 | 1.17 |
| harvest_amis | Eastern Africa | S_consumer | -0.570 | 1.45 | 2.03 | 0.61 |

## Verdict

Independent implementation, Fig. 4 series **in hand**, scored, **not
a replication**. G0-U (3) fails on the host (drift 1.444 vs author
1.00). G0-U (2) is N5, not a unique maximizer. Items 1–3 did **not**
newly pass. Do not restore L1–L8. Do not adopt Bai αI=10. Do not pin
2006. Do not retune αI. Do not start G1. See `hindcast.md` (S5) for
the G0-H score.

## Files

- `author_fig4/PROVENANCE.txt`
- `author_fig4/monthly_world.csv`, `annual_world.csv`, `annual_regional.csv`
- `score_fig4_prices.csv`, `score_fig4_supply.csv`, `score_fig4_regional.csv`
- `figures/fig4_author_vs_host_prices.png` (diagnostic overlay)

