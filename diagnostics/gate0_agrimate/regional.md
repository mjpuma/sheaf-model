# G0-H — regional USDA vs 27-node host (P9)

Global scores compare the **27-node sum** to USDA **world** PSD.
This table compares named AgrimateRegionsWheat nodes to
`psd_regional_annual()` (mapped PSD members, marketing year).
Coverage gaps stay labelled. `wheat_params()` stay αI=3.2,
p_sto=0.1, xmin=0.2. No fit to close the stock-level gap.
L1–L8 stay rejected. Bai α_foreign=10 not adopted.

Harvest is reconstructed from `H_annual × (1+anomaly)` (no NLP);
it matches the saved Ukraine mechanism CSVs year-for-year.
Consumption and ending stocks are from a dedicated three-scenario
dump. Ukraine 2006–11 consumption matches the P0c panel CSV
bit-for-bit (N5 did not move these annuals).

## Construction (A8, S1 implemented)

`prepare_wheat` 2007–09 baseline **sums** PSD members within each
year, then means over 2007–09 — the same construction as
`psd_regional_annual()`. Stocks are USDA `ending_stocks`, never
FAOSTAT FBSH Stock Variation (element 5074). Pooled country-year
`groupby.mean()` is the rejected A8 construction (R7 labelled).
2007–09 production:

| region | PSD members | host H (member-sum) | PSD sum | host/sum |
|---|---|---:|---:|---:|
| USA | 1 (United States) | 61.4 | 61.4 | 1.00 |
| China | 2 (China|Hong Kong) | 112.7 | 112.7 | 1.00 |
| Eastern Africa | 10 countries | 3.31 | 3.31 | 1.00 |

China is China+Hong Kong; HK production is ~0, so the *old* mean
was ~½ of mainland (56.4 vs 112.7 MMT). Eastern Africa's *old*
mean of 10 mapped countries was 0.33 vs 3.31. Host H now matches the sum.
EU-27 is USDA's single `European Union` aggregate, not 27 ISO3
sums (United Kingdom is Rest of Europe). Verification protocol:
the claim is A8 member-sum; the implementation matches
`psd_regional_annual()`. **S1 implemented.** Not a parameter fit.
Do not retune αI / p_sto / xmin. Do not treat FAO ΔS as stocks.

Other labelled coverage: calendar-year model stocks vs USDA
marketing year; 27-node sum vs world PSD at the global score;
FAOSTAT Food Balances still absent (A1).

## 2006–11 harvest+AMIS vs mapped PSD

| region | field | corr | mean host | mean PSD | ratio |
|---|---|---:|---:|---:|---:|
| USA | production | 0.997 | 60.5 | 57.8 | 1.05 |
| USA | consumption | -0.426 | 15.4 | 31.1 | 0.50 |
| USA | ending_stocks | 0.560 | 3.8 | 18.1 | 0.21 |
| Russia | production | 0.995 | 59.8 | 52.9 | 1.13 |
| Russia | consumption | -0.259 | 32.8 | 38.2 | 0.86 |
| Russia | ending_stocks | 0.804 | 13.2 | 9.9 | 1.33 |
| Ukraine | production | 0.972 | 20.2 | 19.0 | 1.07 |
| Ukraine | consumption | 0.350 | 10.0 | 12.5 | 0.81 |
| Ukraine | ending_stocks | 0.657 | 7.1 | 2.9 | 2.41 |
| EU-27 | production | 0.969 | 136.2 | 135.5 | 1.01 |
| EU-27 | consumption | 0.439 | 95.3 | 124.1 | 0.77 |
| EU-27 | ending_stocks | 0.740 | 28.5 | 15.5 | 1.84 |
| Argentina | production | 0.951 | 14.7 | 15.1 | 0.98 |
| Argentina | consumption | 0.197 | 5.8 | 5.7 | 1.02 |
| Argentina | ending_stocks | 0.819 | 10.1 | 1.9 | 5.34 |
| Australia | production | 0.985 | 17.8 | 20.8 | 0.86 |
| Australia | consumption | -0.636 | 4.7 | 6.5 | 0.73 |
| Australia | ending_stocks | 0.862 | 2.4 | 5.2 | 0.47 |
| Canada | production | 0.937 | 24.4 | 24.9 | 0.98 |
| Canada | consumption | -0.188 | 10.9 | 8.0 | 1.36 |
| Canada | ending_stocks | 0.376 | 16.7 | 6.5 | 2.57 |
| India | production | 0.410 | 77.4 | 78.7 | 0.98 |
| India | consumption | -0.822 | 81.4 | 77.0 | 1.06 |
| India | ending_stocks | 0.390 | 4.5 | 12.5 | 0.36 |
| China | production | -0.857 | 114.0 | 113.6 | 1.00 |
| China | consumption | -0.892 | 58.6 | 110.0 | 0.53 |
| China | ending_stocks | 0.089 | 16.8 | 48.9 | 0.34 |
| Eastern Africa | production | 0.444 | 3.3 | 3.4 | 0.95 |
| Eastern Africa | consumption | -0.705 | 5.7 | 7.0 | 0.81 |
| Eastern Africa | ending_stocks | -0.455 | 1.9 | 0.5 | 3.45 |

Named **single-row** exporters (USA, Russia, Ukraine, EU-27,
Argentina, Australia, Canada, India) sit near PSD on *mean*
production (Ukraine ratio 1.07, USA 1.05). Weather-driven series correlate
(USA 1.00; Ukraine 0.97). India (0.41) and China (-0.86) do not: host harvest is the
2007–09 mean times a LOWESS residual, while PSD is a rising
level. That is Agrimate-style anomaly forcing, not a missing
knob. China production is 1.00× mapped PSD
(A8 member-sum). Eastern Africa production is 0.95×
(A8 member-sum). Do not fit xmin or p_sto to the stock column: Ukraine
stocks are 2.41× mapped
PSD; Eastern Africa stocks are 3.45×. The world 1.58×
gap in `hindcast.md` is a different comparison (27-node sum vs
world PSD; stale until S5 re-score).

Eastern Africa *consumption* is not the old 0.1× PSD: inflows come from
T* (A2), so the purchaser can eat imported grain. Host H is now the
10-country sum (ratio 0.81). USA
consumption is 0.50× mapped
PSD (2007–08 host vs PSD ~30) — who-eats / export drain,
not xmin. Argentina ending stocks are 5.34×. Those are
labelled regional gaps. Do not fit a storage-cost knob to them.

## Harvest-only vs harvest+AMIS (regional)

Production is identical by construction (same anomalies). AMIS
moves consumption on restricting exporters: Ukraine 2007 is
1.93 MMT harvest-only vs 10.34 MMT harvest+AMIS (grain stays
home under E.4). See `ukraine_*.csv`. This table does not
restore L1–L8 or retune αI.

## Files

- `score_regional.csv` — year-level host vs mapped PSD
- `score_regional_summary.csv` — 2006–11 corr / level
- `score_regional_construction.csv` — 2007–09 mean vs sum

Next: P10 FAOSTAT FB vs USDA (A1) only if those arrays exist.

