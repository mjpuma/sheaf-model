# Gate 0 data cookbook

How to obtain, refresh, and *not* tune the wheat host inputs. Live code:
`sheaf/agrimate/`. Do not use `archive/legacy-gate0/` or
`diagnostics/redteam/` as a calibrator.

There is **no** fit loop. Author `AgrimateParams` stay the defaults
(`wheat_params()`: αI=3.2, p_sto=0.1, xmin=0.2, ζ=0, N_for=3). Bai
α_foreign=10 is an OAT alternative, not a download target. Pink Sheet is
for **scoring**, not calibration.

Checked 2026-09-19 (R1): script source, vendored trees, and live HTTP
HEAD/GET. USDA FAS zip **200**; World Bank commodity page **200**;
oecd.org **403** (Cloudflare); Zenodo 10688435 and 14022004 records
**200** but **not** wired into `fetch_external_data.py`.

Checked 2026-09-20 (R6 obtain): FAOSTAT JSON API FBSH **521**; bulk zip
`bulks-faostat.fao.org` **200**. `--faostat-fb` is opt-in. Laptop
`/Users/mjp38/GitHub/sheaf-model/data` is **not** mounted here.

## One-screen map

| Need | Vendored? | Command | Notes |
|---|---|---|---|
| USDA PSD country P/C/S | zip + grain extracts | `PYTHONPATH=. python scripts/fetch_external_data.py --psd-only` | No API key. Units 1000 MT → ×1e-3 MMT. S1: 2007–09 baseline is member-sum then mean (`ending_stocks` is S; never FAO ΔS). |
| USDA world aggregates | yes | none | `data/usda_world/` (scoring 27-node sum vs world) |
| FAOSTAT E0 trade shares | yes | none | `data/faostat_network/` — **E0 only**, not Food Balances (A1) |
| FAOSTAT Food Balances | **raw FBSH yes** / host reconstruction **yes** (not bit-identical; **not adopted**) | `--faostat-fb` then `--faostat-qcl-tcl` then `scripts/build_author_fb_fao.py` | `data/faostat_fb/` wheat 2006–11 item 2511. Labelled `data/food_balances/wheat_food_balance_fao.csv`. USDA stays `prepare_wheat` default. |
| AMIS / E.4 restrictions | yes (XLSX+CSV) | Browser download, then `--amis-only` | oecd.org is Cloudflare-blocked unattended (HEAD 403 this run) |
| Pink Sheet monthly/annual | yes | `--prices-only` | URL hash changes; script scrapes the WB page |
| Wheat harvest months | yes | none | Start/end months. Host uses **E.27 raised-cosine** (`sheaf.agrimate.harvest`), not the triangular/twin-pin paragraph that described the legacy host. |
| Fig. 4 author series | extracted CSVs | see Zenodo below | NetCDF zip **not** vendored |
| Author Julia 14022004 | **not in repo** | not copied | Executable spec retrieved 2026-09-16; do not vendor copyrighted code |

Default three-scenario run needs only the vendored trees (PSD extracts,
E0, AMIS CSV, calendars, Pink Sheet). You do **not** need Zenodo, and
you do **not** need FAOSTAT FB, to run the host. You **do** need
`author_fig4/*.csv` to score Fig. 4 (already committed). FBSH is a
labelled parallel WheatData (`prepare_wheat_fbsh`, not adopted), not the
default path.

## Automated refresh (no keys)

```bash
# USDA FAS PSD bulk (~10 MB zip → grain extracts)
PYTHONPATH=. python scripts/fetch_external_data.py --psd-only

# World Bank Pink Sheet annual + monthly
PYTHONPATH=. python scripts/fetch_external_data.py --prices-only

# FAOSTAT FBSH wheat 2006–11 (opt-in; not in the default fetch)
PYTHONPATH=. python scripts/fetch_external_data.py --faostat-fb

# FAOSTAT QCL+TCL wheat 2006–11 (opt-in; reconstruction inputs)
PYTHONPATH=. python scripts/fetch_external_data.py --faostat-qcl-tcl
PYTHONPATH=. python scripts/build_author_fb_fao.py
```

Default (no flags) refreshes PSD + AMIS + Pink Sheet only — **not** FB.

Script: `scripts/fetch_external_data.py`. Metadata:
`data/usda_psd/DOWNLOAD_META.json`,
`data/world_prices/DOWNLOAD_META.json`,
`data/faostat_fb/DOWNLOAD_META.json`,
`data/faostat_qcl_tcl/DOWNLOAD_META.json`. Provenance files sit next to
the CSVs.

The script does **not** mention zenodo / 14022004 / 10688435 / αI /
p_sto / xmin. `--faostat-fb` and `--faostat-qcl-tcl` do **not** change
`wheat_params` or `prepare_wheat`. Do not add a silent fit.

## Semi-automated (browser once)

OECD/AMIS export restrictions cannot be fetched from this environment
(Cloudflare 403). Vendored workbook is enough to run.

```text
1. https://www.oecd.org/en/topics/sub-issues/agro-food-trade/export-restrictions-on-staple-crops.html
2. Download the database (XLSX)
3. Replace data/amis_policies/oecd_export_restrictions_staple_crops.xlsx
4. PYTHONPATH=. python scripts/fetch_external_data.py --amis-only
```

Host loader uses sheets `AggregatedDatabase` columns
`PolicyMeasure_Name` / `CommodityClass_Name` (not `Measure`/`Commodity`).
Bans 0.95, taxes 0.50 (Tbl. E.4).

## Not automated — required for *Agrimate Fig. 4* comparison, not for the default run

### Zenodo 10688435 (Fig. 4 NetCDF)

- Record: https://doi.org/10.5281/zenodo.10688435 (HEAD 200 this run)
- Use **v1.0 / record 10688435** (150 MB `data.zip`, md5
  `2f3809c66e78b72b3c74971051f89529`), not later 1.55 GB versions.
- Extract `main_output/data/` three wheat NetCDFs.
- Rebuild CSVs (zip itself stays out of git):

```bash
PYTHONPATH=. python scripts/score_agrimate_fig4.py \
    --from-nc /path/to/main_output/data
```

Already committed: `diagnostics/gate0_agrimate/author_fig4/`. Provenance:
that folder’s `PROVENANCE.txt`. Licence CC-BY-4.0.

NetCDF attrs (this run, `netcdf_attrs.json`): AgrimateEU28 + Egypt,
α_foreign=3.5, ζ=1, N_for=6, start 2000-01-01, FAO anomalies on the
forced scenarios, git `old-demand-dynamics`. Those knobs belong on a
**named comparison object**, not in `wheat_params()`.

### Zenodo 14022004 (author Julia)

- Record: https://doi.org/10.5281/zenodo.14022004 (HEAD 200 this run)
- Retrieved 2026-09-16 as the **executable specification**. **Not copied**
  into this package (`/agrimate/` at repo root is gitignored PDF extracts
  only).
- Needed to diff `plot_wm_price_timeseries`, `two_markets`, ζ, D.30a x1.
- R3 searched this checkout: Julia is still **not** present. Host
  identity (`volume_weighted_offer_index`, `world_price.md`,
  `tests/agrimate/test_world_price.py`) locks the XI-weighted lagged
  D.7 mix. Do not treat that as a bit-diff of author `plot.jl`.
- Do not vendor it. Do not “tune” host knobs from a local checkout
  except as a labelled comparison object (R2).

### FAOSTAT Food Balances (A1) — how to get them

Author AgriculturalData expects cleaned `wheat_food_balance_fao.csv`.
A **labelled host reconstruction** of `impute_food_balance_fao("wheat")`
is now at `data/food_balances/wheat_food_balance_fao.csv` (FBSH 2006–11
+ QCL Production + TCL trade, AgriculturalData item-group factors,
`reverse_stock_variation_sign`, `remove_aggregate_areas`). It is **not**
Kuhla's unpublished local CSV (not bit-identical; window 2006–11 only;
not rebalanced). It is **not adopted** as `prepare_wheat`. Do not copy
FoodTradeNetwork `inputs_processed/` P0/R0 (2015–21 *averages*).

**Raw FAOSTAT FBSH** (old methodology through 2013) wheat 2006–11 **is**
vendored:

```bash
PYTHONPATH=. python scripts/fetch_external_data.py --faostat-fb
```

Writes `data/faostat_fb/wheat_fbsh_2006_2011.csv` (+ `_long.csv`,
`DOWNLOAD_META.json`). Bulk zip is gitignored. Domain FBSH, item 2511
Wheat and products, unit 1000 t, Stock Variation element **5074**.
Do **not** mix FBS 2010+ (new methodology) into this extract.

USDA remains `prepare_wheat` default. R6 `prepare_wheat_fbsh` is a
labelled parallel (members summed; Psi stayed USDA; **not adopted**).
S3 re-scored H/C vs the member-sum USDA host (China 1.00; moy
worsened; **not adopted**). Do not retune αI / p_sto / xmin to FBSH
numbers. Scorer: `PYTHONPATH=. python scripts/score_agrimate_s3_fbsh.py`
(historical R6: `score_agrimate_fb_wheatdata.py`).

Laptop path `/Users/mjp38/GitHub/sheaf-model/data` is a local checkout.
This cloud VM does not mount it. On the laptop, run the same
`--faostat-fb` command (or copy `data/faostat_fb/`). `inventory()`
reports `laptop_data.exists` so you can see whether that tree is
visible.

### How a user gets every Gate 0 dataset

| Already in git | Refresh command |
|---|---|
| USDA PSD grain extracts, world aggregates | `--psd-only` if you want a newer FAS dump |
| FAOSTAT E0 | none (vendored) |
| FAOSTAT FBSH wheat 2006–11 | `--faostat-fb` (opt-in; zip gitignored) |
| FAOSTAT QCL/TCL wheat 2006–11 | `--faostat-qcl-tcl` then `scripts/build_author_fb_fao.py` |
| AMIS/OECD restrictions | browser XLSX, then `--amis-only` |
| Pink Sheet | `--prices-only` |
| Harvest calendars | none (vendored) |
| Fig. 4 author CSVs | none (`author_fig4/` committed); NetCDF zip is manual Zenodo |
| Author Julia 14022004 | **not** fetched; retrieve yourself, do not vendor |

`pip install -r requirements.txt` then the commands above. No API keys
except the OECD browser step. Zenodo is only for Fig. 4 NetCDF / author
code, never for a silent fit.

## What “tuning” exists (diagnostic only)

```bash
PYTHONPATH=. python scripts/run_agrimate_validation.py --sensitivity
```

2006–08 harvest+AMIS OAT around **author** defaults. Writes
`diagnostics/gate0_agrimate/score_sensitivity.csv`. Does **not** change
`wheat_params()`. Bai αI=10 is a row in that table; P6 did not adopt it
(it *raises* the already-too-large spike).

There is no least-squares / Pink-Sheet optimiser in `sheaf/agrimate/`.
`archive/legacy-gate0/scratch/` contains old ask/scarcity sweeps; those
are frozen and are not a Gate 0 tuner.

## Run the host after data are in place

```bash
pip install -r requirements.txt
python -m pytest tests/agrimate -q
PYTHONPATH=. python scripts/run_agrimate_validation.py
```

Solver smoke (one harvest+AMIS path):

```bash
PYTHONPATH=. python scripts/run_agrimate_wheat.py
```

Fig. 4 / hindcast / methods notes **do not re-run** the host:

```bash
PYTHONPATH=. python scripts/score_agrimate_fig4.py
PYTHONPATH=. python scripts/score_agrimate_hindcast.py
PYTHONPATH=. python scripts/score_agrimate_methods.py
```

## Folders that are *not* Gate 0 wheat inputs

| Path | Why ignore for this host |
|---|---|
| `archive/legacy-gate0/` | old red-team prototypes |
| `diagnostics/redteam/` | ask/scarcity cycle |
| `diagnostics/gate0_wheat_report.md` (and maize/rice) | legacy CropParams |
| `sheaf/calibration.py` | annual SPE prototype table |
| `sheaf/legacy/`, `sheaf/dynamic_crop.py` | pre-rewrite spine |
| `data/maps/` | cartography, not quantities |
| `/agrimate/` (gitignored) | copyrighted PDF extracts |

## Provenance files

- `data/usda_psd/PROVENANCE.txt`
- `data/usda_world/PROVENANCE.txt`
- `data/faostat_network/PROVENANCE.txt`
- `data/faostat_fb/PROVENANCE.txt` (raw FBSH wheat 2006–11; USDA still default)
- `data/faostat_qcl_tcl/PROVENANCE.txt` (QCL Production + TCL trade wheat 2006–11)
- `data/food_balances/PROVENANCE.txt` (host reconstruction of impute_food_balance_fao; not adopted)
- `data/amis_policies/PROVENANCE.txt`
- `data/world_prices/PROVENANCE.txt`
- `data/crop_calendars/PROVENANCE.txt` (live host is E.27; legacy
  triangular/twin-pin language is labelled)
- `diagnostics/gate0_agrimate/author_fig4/PROVENANCE.txt`
