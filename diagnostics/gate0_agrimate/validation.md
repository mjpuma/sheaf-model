# Agrimate Gate 0 — three-scenario validation

Command: `python scripts/run_agrimate_validation.py --start-year 2003 --end-year 2011`

Independent Agrimate copy (Kuhla et al. 2025 §D; Zenodo 14022004 as
executable spec, not copied). Workflow structure matches the Bai/Wada/Puma
Agrimate-copy note (three scenarios; prices **and** supply/stocks;
Ukraine / Eastern Africa mechanism panels; OAT diagnostic). Defaults
remain author `AgrimateParams` (αI=3.2, not Bai's fitted α_foreign=10).
Window is Agrimate wheat 2006–11, not that note's 2017–2025 paper.

## SHEAF differentiators (later, blocked until G0-P)

- **G1** Cross-crop substitution (wheat/rice/maize on the demand side). Disabled G1 recovers this single-crop G0 run.
- **G2** Endogenous export-restriction game among governments. Disabled G2 recovers E.4 AMIS on this host. Not the 36-run exporter-at-a-time grid, which is a prescribed-Δ experiment.

This run is G0: single crop, AMIS prescribed. Do not retune L1–L8.

- regions: 27
- spin-up: 2003–2005; score: 2006–2011
- data notes: Baseline quantities: USDA PSD 2007–09 member-sum then mean, not FAOSTAT Food Balances (E.1.1).; A8 (S1): multi-country nodes sum PSD members within year (same as psd_regional_annual()), then mean 2007–09.; Stocks are USDA ending_stocks, never FAOSTAT FBSH Stock Variation (element 5074 / ΔS).; Trade pattern: FAOSTAT E0 2006–07, rescaled to USDA exports.; C.1 wheat nodes: Zenodo 14022004 AgrimateRegionsWheat (27 names).; A_d is not E.30. F.1 Egypt 0.17 unused (Egypt is in Northern Africa).; Starred XI*, XD*, C* used in inverse demand are per-step averages.; Anomalies use the already-summed member series (groupby region+year production.sum).; AMIS wheat Δ: 491 region-steps, max=0.95, regions=['Argentina', 'China', 'India', 'Kazakhstan', 'Russia', 'Ukraine', 'Northern Africa'].
- AMIS wheat Δ region-steps: 491; max=0.95; regions=['Argentina', 'China', 'India', 'Kazakhstan', 'Russia', 'Ukraine', 'Northern Africa']

## Solver (each scenario)

| scenario | failed | fallback | unconverged | floor | residual | runtime_s | pidx min/max |
|---|---:|---:|---:|---:|---:|---:|---|
| undisturbed | 0 | 0 | 1990 | 0 | 0.000e+00 | 17.7 | 0.0148 / 3.3712 |
| harvest | 0 | 0 | 2161 | 0 | 0.000e+00 | 22.1 | 0.0302 / 3.3712 |
| harvest_amis | 0 | 0 | 2304 | 0 | 0.000e+00 | 22.9 | 0.0302 / 3.3712 |

## Prices vs Pink Sheet (2006–11)

Indexed comparison in `figures/fig2_prices.png`. A worse Pink-Sheet
fit than the legacy host is not a reason to restore L1–L8.

| scenario | corr | RMSE $/t | 2007/08 hike model | hike obs | 2006 mean model | 2006 obs |
|---|---:|---:|---:|---:|---:|---:|
| undisturbed | -0.116 | 212.6 | ×4.87 | ×1.88 | 45.8 | 213.5 |
| harvest | -0.024 | 189.0 | ×3.85 | ×1.88 | 81.5 | 213.5 |
| harvest_amis | 0.014 | 185.5 | ×3.71 | ×1.88 | 81.5 | 213.5 |

## Supply and stocks vs USDA world (2006–11)

Model sums 27 AgrimateRegionsWheat nodes; USDA is the world aggregate.
Level bias from missing coverage is expected; **anomaly correlation**
is the performance number. FAOSTAT Food Balances remain labelled A1
(Bai found FAO anomalies closer to prices in 2020–24; we stay on USDA
because FAOSTAT FB is not in this repository).

| scenario | field | corr | RMSE | mean model | mean USDA |
|---|---|---:|---:|---:|---:|
| undisturbed | production | 0.000 | 146.01 | 662.04 | 519.40 |
| undisturbed | consumption | 0.077 | 157.56 | 672.82 | 520.12 |
| undisturbed | ending_stocks | 0.238 | 64.37 | 214.02 | 157.43 |
| undisturbed | stock_to_use | 0.341 | 0.05 | 0.32 | 0.30 |
| harvest | production | 0.803 | 143.23 | 661.38 | 519.40 |
| harvest | consumption | -0.269 | 141.00 | 657.00 | 520.12 |
| harvest | ending_stocks | 0.912 | 82.80 | 239.22 | 157.43 |
| harvest | stock_to_use | 0.818 | 0.07 | 0.36 | 0.30 |
| harvest_amis | production | 0.803 | 143.23 | 661.38 | 519.40 |
| harvest_amis | consumption | -0.390 | 137.93 | 649.20 | 520.12 |
| harvest_amis | ending_stocks | 0.831 | 104.64 | 259.41 | 157.43 |
| harvest_amis | stock_to_use | 0.608 | 0.12 | 0.40 | 0.30 |

## G0-U undisturbed dynamics (after 2003–05 spin-up)

Repeating seasonal harvest, no AMIS. Not a world-price pin.

- post-spin-up price mean: 0.3498
- within-window CV: 1.209
- annual-mean min/max: 0.2146 / 0.4501
- last/first annual-mean ratio (drift): 1.444
- year-to-year seasonal-shape RMSE: 0.1998
- min S_p / S_c: 0.0000 / 0.0000

## Mechanism panels

- Fig. 4 `Ukraine` supplier: harvest, producer stocks, exports, consumption.
- Fig. 5 `Eastern Africa` purchaser: consumer price, inflow, consumption, stocks.
These compare harvest-only vs harvest+AMIS on the 2006–11 AMIS diary,
not a synthetic 36-run exporter grid (that grid is G0-H/P; see
`restriction_pulse` in `restrictions.py`).

## Figures

- `figures/fig1_coverage_trade.png`
- `figures/fig2_prices.png`
- `figures/fig3_supply_stocks.png`
- `figures/fig4_ukraine_supplier.png`
- `figures/fig5_eastern_africa_purchaser.png`

## What this does not do

- Does not retune αI, p_sto, or x_min from Pink Sheet or from Bai's table.
- Does not split-calibrate 2008 vs 2022 (Bai's finding that one set cannot
  fit both crises is recorded as an open G0-H question).
- Does not implement G1 substitution or G2 government best-response.
- Does not unpack Zenodo 10688435 (Agrimate Fig. 4 author series still G0-H).

