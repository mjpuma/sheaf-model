# Reconstructed simulate() inputs

Built by `inputs/from_data.py --crop wheat`. These are not the author
input files. Zenodo data v3 has model output only.

Written to `inputs/generated/agrimate_input/` (gitignored). `drivers/run.py`
passes that directory to `simulate()` as `inputroot`.

Quantities are thousand tonnes. World wheat production in the food-balance
file is 661,168 (661 MMT) for the 2007–2009 mean. International trade sums
to 131,311 (131 MMT).

| File | Source |
|---|---|
| `food-balance_baseline=2007-2009_crop=wheat.csv` | USDA PSD wheat, mean 2007–2009, one row per AgrimateEU28 ISO code |
| `trade-flows_baseline=2007-2009_crop=wheat.csv` | FAOSTAT E0 wheat, 2006–07 window, each exporter rescaled to its USDA export total |
| `harvest-distributions_crop=wheat.csv` | `data/crop_calendars/wheat_harvest_months.csv`, raised cosine on days 1–365 |
| `parameters_baseline=2007-2009_crop=wheat_source=empirical.csv` | STU = ending stocks / consumption; A_d from the import share; A_c from income bands |
| `harvest-anomalies_crop=wheat_source=FAOsince-2005.csv` | USDA production minus a LOWESS trend, zero before 2005, repeated on every day of the year. Columns `2000-1` through `2016-365`. Exact 0 wherever the trend is 0 |
| `harvest-trends_crop=wheat_source=FAOsince-2005.csv` | That LOWESS trend, same columns, never negative. Forcing in the paper code is `1 + anomaly/trend` |
| `export-restrictions_crop=wheat_source=2007-2011.csv` | AMIS wheat measures. Cuts: prohibition 0.95, quota 0.70, tax 0.50. Licensing is left out. Clipped to 2007-01-01 … 2011-12-31, then merged per exporter into non-overlapping intervals at the daily maximum cut |

17 restriction intervals, all inside 2007–2011. Exporters: ARG, CHN, EGY, IND, KAZ, RUS, UKR.

The window clip was added 2026-10-01 after J4 (`J4.md`, data problem 1).
The earlier file held 49 intervals running to 2024, and `simulate()`
applies every row, so ARG, CHN, EGY, IND and UKR stayed restricted to the
end of the run (2012-12). The 17 new intervals are the old in-window ones
with end dates cut at 2011-12-31 (ARG, CHN, EGY, IND, UKR). The other six
input files and `README.txt` were byte-identical after the rebuild. The
previous files are kept in `agrimate-2025/agrimate_input_backup_pre_j4window_20261001/`.

Two rules the paper code forces on these files (fixed 2026-09-30 after J3
failed; see `J3.md`):

- The anomaly and trend files are summed over each region's countries
  before `1 + anomaly/trend` is formed. A blank or NaN in one country voids
  the whole region, so non-producers carry exact zeros. The first build left
  0/0 = NaN blanks for 44 non-producing countries.
- `aggregate_export_restrictions` adds overlapping values for one exporter
  and caps at 1. AMIS repeats a measure once per rate revision (four
  Argentine export-tax rows start 2007-05-15), so raw rows stacked to a
  100% cut on Argentina from May 2007 to May 2012 and on China in 2008. The
  file now holds one interval set per exporter at the daily maximum.

Food balance, trade flows, harvest distributions and parameters were
byte-identical after the fix, so the J2 baseline still matches these inputs.

Blank `STU` and `A_d` cells in the parameters file (138 zero-consumption
countries) are intended. The paper code reads them as `missing` and fills
regional medians before the consumption-weighted average.

USDA reports the European Union as one country (code E4), not as member states. That total is stored on DEU (137,492 thousand tonnes) so the AgrimateEU28 sum is still the USDA EU total. FAOSTAT trade among EU members is dropped. EU exports to the rest of the world are also attached to DEU and scaled to the USDA EU export total.

Egypt stays inside Northern Africa in these tables. The paper run pulls EGY out as its own region when `simulate()` is called. That split is not baked into the CSVs.
