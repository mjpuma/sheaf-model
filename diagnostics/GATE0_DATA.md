# Gate 0 data cookbook

How to obtain, refresh, and *not* tune the wheat host inputs. Live code:
`sheaf/agrimate/`. Do not use `archive/legacy-gate0/` or
`diagnostics/redteam/` as a calibrator.

There is **no** fit loop. Author `AgrimateParams` stay the defaults
(`wheat_params()`: αI=3.2, p_sto=0.1, xmin=0.2, ζ=0, N_for=3). Bai
α_foreign=10 is an OAT alternative, not a download target. Pink Sheet is
for **scoring**, not calibration.

## One-screen map

| Need | Vendored? | Command | Notes |
|---|---|---|---|
| USDA PSD country P/C/S | zip + grain extracts | `PYTHONPATH=. python scripts/fetch_external_data.py --psd-only` | No API key. Full `psd_alldata.csv` is gitignored; rebuild from zip. |
| USDA world aggregates | yes | none | `data/usda_world/` (scoring 27-node sum vs world) |
| FAOSTAT E0 trade shares | yes | none | `data/faostat_network/` — **E0 only**, not Food Balances (A1) |
| FAOSTAT Food Balances | **no** | **none** | P10 left A1. Do not invent a vintage. |
| AMIS / E.4 restrictions | yes (XLSX+CSV) | Browser download, then `--amis-only` | oecd.org is Cloudflare-blocked unattended |
| Pink Sheet monthly/annual | yes | `--prices-only` | URL hash changes; script scrapes the WB page |
| Wheat harvest months | yes | none | Start/end months. Host uses **E.27 raised-cosine** (`sheaf.agrimate.harvest`), not the triangular/twin-pin paragraph in that PROVENANCE (legacy). |
| Fig. 4 author series | extracted CSVs | see Zenodo below | NetCDF zip **not** vendored |
| Author Julia 14022004 | **not in repo** | not copied | Executable spec retrieved 2026-09-16; do not vendor copyrighted code |

Default three-scenario run needs only the vendored trees (PSD extracts,
E0, AMIS CSV, calendars, Pink Sheet). You do **not** need Zenodo to run
the host. You **do** need `author_fig4/*.csv` to score Fig. 4 (already
committed).

## Automated refresh (no keys)

```bash
# USDA FAS PSD bulk (~10 MB zip → grain extracts)
PYTHONPATH=. python scripts/fetch_external_data.py --psd-only

# World Bank Pink Sheet annual + monthly
PYTHONPATH=. python scripts/fetch_external_data.py --prices-only
```

Script: `scripts/fetch_external_data.py`. Metadata:
`data/usda_psd/DOWNLOAD_META.json`,
`data/world_prices/DOWNLOAD_META.json`. Provenance files sit next to
the CSVs.

Units: PSD bulk is 1000 MT; host converts ×1e-3 → MMT.

## Semi-automated (browser once)

OECD/AMIS export restrictions cannot be fetched from this environment
(Cloudflare). Vendored workbook is enough to run.

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

- Record: https://doi.org/10.5281/zenodo.10688435
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

### Zenodo 14022004 (author Julia)

- Record: https://doi.org/10.5281/zenodo.14022004
- Retrieved 2026-09-16 as the **executable specification**. **Not copied**
  into this package (`/agrimate/` at repo root is gitignored PDF extracts
  only).
- Needed to diff `plot_wm_price_timeseries`, `two_markets`, ζ, D.30a x1.
- Do not vendor it. Do not “tune” host knobs from a local checkout
  except as a labelled comparison object (R2).

### FAOSTAT Food Balances (A1)

Author AgriculturalData expects cleaned `wheat_food_balance_fao.csv`.
That file is **not** in `data/faostat_network/` (E0 trade only).
FoodTradeNetwork `inputs_processed/` P0/R0 are 2015–21 *averages*, not
2006–11 annual FB. P10 left A1. USDA remains the default.

If you add FB later: ship PROVENANCE.txt, build a **parallel** WheatData,
keep USDA as `prepare_wheat` default until G0-P says otherwise.

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
- `data/amis_policies/PROVENANCE.txt`
- `data/world_prices/PROVENANCE.txt`
- `data/crop_calendars/PROVENANCE.txt` (legacy triangular language; live
  host is E.27 — see Step 8 of `GATE0_REDTEAM.md`)
- `diagnostics/gate0_agrimate/author_fig4/PROVENANCE.txt`
