# Validation

## Gate 0, Julia host

The published Agrimate code, given the authors’ own calibration,
reproduces their published wheat run. Numbers and figure:
[`diagnostics/gate0_julia/J10_authorbaseline.md`](diagnostics/gate0_julia/J10_authorbaseline.md),
[`figures/gate0_j10_vs_author.png`](figures/gate0_j10_vs_author.png).

| metric | our run | author |
|---|---|---|
| 2007/08 price ratio | 1.359 | 1.361 |
| 2010/11 price ratio | 1.213 | 1.219 |
| peak (May 2008) | 2.216 | 2.223 |
| monthly correlation | 1.000 | — |
| end-of-year stocks, 2000–2012 | within 0.5 % | — |

World price is the monthly export-weighted mean of cross-border
transaction prices, matching Agrimate’s `plot_wm_price_timeseries`.

## What this does and does not show

**Shows:** the vendored source tree plus the inverted author baseline
reproduces the published NetCDF. That is code-path verification (class
**H**, 95–100 %).

**Does not show:** that the same code, fed USDA / FAOSTAT / AMIS
reconstructions, reproduces the published magnitudes. It does not (J4,
J8, J9): stocks ~+23 %, 2007/08 ratio 1.25 vs 1.361. That is an
empirical limitation (class **F**) because the authors published outputs
but not input tables. A failed match stays a failed match.

## How to re-score

```bash
python drivers/score.py path/to/local.nc
python plots/j10_vs_author.py
```

Author file (harvest + restrictions):
`agrimate-2025/data-v3/data/hindcasting_analysis/raw_data/agrimate_baseline=2007-2009_export_restrictions=2007-2011_extra_regions=(Egypt=EGY)_production_anomalies=FAOsince-2005_regions=AgrimateEU28_start=2000-01-01.nc`

## Later gates

Gate 1 (substitution) and Gate 2 (endogenous restrictions) have no
validation protocol in this tree until G0-P is accepted.
