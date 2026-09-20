# A1 — FAOSTAT Food Balances: raw FBSH vendored; USDA still default

**Leave A1. USDA remains the 2006–11 default.** Labelled parallel
`WheatData` is `fb_wheatdata.md` (**not adopted**). No three-scenario
FAO run. `wheat_params()` stay
αI=3.2, p_sto=0.1, xmin=0.2. L1–L8 stay rejected. Bai
α_foreign=10 not adopted. Bai's 2020–24 FAO-anomaly finding is a
different window; it is not a reason to switch this wheat run.

R6 obtain vendored FAOSTAT **FBSH** (Food Balances −2013, old
methodology) wheat item 2511, years 2006–2011, unit 1000 t.
That extract is **not** bit-identical Agrimate cleaned
`wheat_food_balance_fao.csv`. A labelled host reconstruction of
`impute_food_balance_fao` now lives under `data/food_balances/`
(not adopted as `prepare_wheat`).
Do not mix FBS 2010+ (new methodology) into this vintage.
R6 `prepare_wheat_fbsh` is a labelled parallel vs USDA on one
harvest+AMIS window; **not adopted**.

## Inventory

Agrimate E.1.1 baseline quantities are FAOSTAT Food Balances.
This host uses USDA PSD 2007–09 means (labelled A1) plus FAOSTAT
**E0 trade shares** (A2), not FB production/consumption/stocks.

Checked `data/faostat_network/` (the tree at
`/Users/mjp38/GitHub/sheaf-model/data/faostat_network` on the
laptop; this checkout has the same E0 files). Contents are square
bilateral **E0** matrices (exporter × FAOSTAT area code) plus a
country conversion table. Wheat 2006–07 / 2010–11 / 2019–21 E0
are trade, not production/consumption/stocks.

- E0 files: Maize_Avg20192021E0.csv, Maize_Avg_2006_2007E0.csv, Maize_Avg_2010_2011E0.csv, Rice_Avg20192021E0.csv, Rice_Avg_2006_2007E0.csv, Rice_Avg_2010_2011E0.csv, Wheat_Avg20192021E0.csv, Wheat_Avg_2006_2007E0.csv, Wheat_Avg_2010_2011E0.csv.
- P0 / Production / R0 / Reserves in that folder: none.
- Author-cleaned `wheat_food_balance*.csv` under `data/`: data/food_balances/wheat_food_balance_fao.csv.
- Raw FBSH wheat extract (`data/faostat_fb/`): wheat_fbsh_2006_2011.csv, wheat_fbsh_2006_2011_long.csv.
- Laptop `/Users/mjp38/GitHub/sheaf-model/data` mounted: no (FB hits: none).
- Author AgriculturalData (Zenodo 14022004) expects cleaned
  `wheat_food_balance_fao.csv` / `wheat_food_balance.csv` /
  `wheat_production.csv`. A labelled host reconstruction of
  `wheat_food_balance_fao.csv` is under `data/food_balances/`
  (not bit-identical; not adopted). The other two names are still
  absent.
- Upstream `mjpuma/FoodTradeNetwork` `inputs_processed/` has
  Wheat P0/Production/Reserves only as **2015–21 window averages**,
  not 2006–11 annual Food Balances. Copying those would not force
  this Agrimate wheat window. Not vendored.

`data/faostat_network/PROVENANCE.txt` already says production (P0)
and reserves (R0) are **not** taken from FAOSTAT: FAO stocks are
food-balance residuals. `sheaf/data_faostat.py` loads the trade
network only. FBSH Stock Variation is element **5074** (not FBS
5072). It is a residual, not USDA ending stocks.

## Obtain (this run)

JSON API `fenixservices.fao.org/.../data/FBSH` returned HTTP 521.
Bulk zip from `bulks-faostat.fao.org` returned 200 (~72.5 MB,
gitignored). Extract: 1259 area-years, 210 areas. Sanity 2007
production (1000 t): United States of America 55820; World 608672;
China, mainland 109298; European Union (27) 107883.

Refresh: `PYTHONPATH=. python scripts/fetch_external_data.py --faostat-fb`. Opt-in; not in the default PSD/AMIS/Pink fetch.
Does not change `wheat_params` or `prepare_wheat`.

## Places that look like FAO but are not Agrimate FB

1. **Fig. 4 NetCDF** (`production_anomalies=FAOsince-2005`).
   Zenodo 10688435 `data.zip` is model *output* (NetCDF + PDFs).
   No CSV/XLSX Food Balance inputs. The zip is not vendored.
   Those harvest series were scored in P7 on AgrimateEU28+Egypt;
   they are not a 27-node `WheatData` substitute.
2. **Author code** `AgriculturalData` (14022004) has the
   preprocess (`impute_food_balance_fao`, QCL+TCL merge,
   rebalance). The author's local CSV is still unpublished.
   This host reconstructed `impute_food_balance_fao` for 2006–11
   under `data/food_balances/` (labelled; not adopted).
3. This **raw FBSH dump** is official FAOSTAT, not that pipeline.
   Old FBS vs new Food Balances also breaks across ~2010; this
   extract stays on FBSH through 2011.

## Verification protocol (leave A1)

1. **Claim.** Agrimate E.1 uses FAOSTAT Food Balances.
2. **Implementation.** `prepare_wheat` (`wheat_data.py`) groups
   USDA PSD 2007–09 and notes "not FAOSTAT Food Balances (E.1.1)."
3. **Match.** They do not, by labelled adaptation A1.
4. **Counterexample.** Raw FBSH is on disk. A labelled
   reconstruction of `wheat_food_balance_fao.csv` is also on
   disk (`inventory()["food_balance_files"]`); it is not
   bit-identical author output and is **not adopted**.
   `prepare_wheat` still USDA.
5. **Correctness of stopping.** E0 is present and used. Wiring
   FBSH into the 27-node host needs region maps, stock treatment,
   and a labelled parallel WheatData (`fb_wheatdata.md`, not
   adopted). Switching the host would retune 2006–11 quantities.
6. **Change.** None to economics. USDA stays default until G0-P.

`prepare_wheat` default note holds; αI=3.2.

## Files

- this note
- `data/faostat_fb/PROVENANCE.txt`
- `data/food_balances/PROVENANCE.txt` (host reconstruction)
- `data/faostat_network/PROVENANCE.txt` (E0 only)

Next paste: **R7** (A8 mean-vs-sum). Not G1. Do not retune
αI / p_sto / xmin. Do not adopt FBSH as prepare_wheat.

