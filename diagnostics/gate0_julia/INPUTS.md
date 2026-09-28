# Reconstructed simulate() inputs

Built by `scripts/build_agrimate_paper_inputs.py`. These are not the author
input files. Zenodo data v3 has model output only, and the 2025 filenames
are not on the authors' GitHub.

Written to

`/Users/mjp38/GitHub/agrimate-2025/agrimate-equal-sales-penalty/data/agrimate_input/`

which is the default `simulate()` input directory. `simulate()` was not called.
`AgrimateModel` still does not load (see `J0.md`).

Quantities are thousand tonnes. World wheat production in the food-balance
file is 661,168 (661 MMT) for the 2007–2009 mean. International trade sums
to 131,311 (131 MMT).

| File | Source |
|---|---|
| `food-balance_baseline=2007-2009_crop=wheat.csv` | USDA PSD wheat, mean 2007–2009, one row per AgrimateEU28 ISO code |
| `trade-flows_baseline=2007-2009_crop=wheat.csv` | FAOSTAT E0 wheat, 2006–07 window, each exporter rescaled to its USDA export total |
| `harvest-distributions_crop=wheat.csv` | `data/crop_calendars/wheat_harvest_months.csv`, raised cosine on days 1–365 |
| `parameters_baseline=2007-2009_crop=wheat_source=empirical.csv` | STU = ending stocks / consumption; A_d from the import share; A_c from the income bands in `sheaf/agrimate/wheat_data.py` |
| `harvest-anomalies_crop=wheat_source=FAOsince-2005.csv` | USDA production minus a LOWESS trend, zero before 2005, repeated on every day of the year. Columns `2000-1` through `2016-365` |
| `harvest-trends_crop=wheat_source=FAOsince-2005.csv` | That LOWESS trend, same columns. Forcing in the paper code is `1 + anomaly/trend` |
| `export-restrictions_crop=wheat_source=2007-2011.csv` | AMIS wheat measures. Cuts match `sheaf/agrimate/restrictions.py`: prohibition 0.95, quota 0.70, tax 0.50. Licensing is left out |

61 of 117 restriction rows overlap 2007–2011. Exporters in that window: ARG, CHN, EGY, IND, KAZ, RUS, UKR.

USDA reports the European Union as one country (code E4), not as member states. That total is stored on DEU (137,492 thousand tonnes) so the AgrimateEU28 sum is still the USDA EU total. FAOSTAT trade among EU members is dropped. EU exports to the rest of the world are also attached to DEU and scaled to the USDA EU export total.

Egypt stays inside Northern Africa in these tables. The paper run pulls EGY out as its own region when `simulate()` is called. That split is not baked into the CSVs.
