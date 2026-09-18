# Agrimate Gate 0 — three-scenario validation

Command: `python scripts/run_agrimate_validation.py --start-year 2003 --end-year 2011 --sensitivity`

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
- data notes: Baseline quantities: USDA PSD 2007–09 mean, not FAOSTAT Food Balances (E.1.1).; Trade pattern: FAOSTAT E0 2006–07, rescaled to USDA exports.; C.1 wheat nodes: Zenodo 14022004 AgrimateRegionsWheat (27 names).; A_d is not E.30. F.1 Egypt 0.17 unused (Egypt is in Northern Africa).; Starred XI*, XD*, C* used in inverse demand are per-step averages.; AMIS wheat Δ: 491 region-steps, max=0.95, regions=['Argentina', 'China', 'India', 'Kazakhstan', 'Russia', 'Ukraine', 'Northern Africa'].
- AMIS wheat Δ region-steps: 491; max=0.95; regions=['Argentina', 'China', 'India', 'Kazakhstan', 'Russia', 'Ukraine', 'Northern Africa']

## Solver (each scenario)

| scenario | failed | fallback | unconverged | floor | residual | runtime_s | pidx min/max |
|---|---:|---:|---:|---:|---:|---:|---|
| undisturbed | 0 | 0 | 1583 | 0 | 0.000e+00 | 14.5 | 0.0145 / 3.1681 |
| harvest | 0 | 0 | 1628 | 0 | 0.000e+00 | 19.5 | 0.0105 / 3.1681 |
| harvest_amis | 0 | 0 | 1743 | 0 | 0.000e+00 | 19.9 | 0.0113 / 3.1681 |

## Prices vs Pink Sheet (2006–11)

Indexed comparison in `figures/fig2_prices.png`. A worse Pink-Sheet
fit than the legacy host is not a reason to restore L1–L8.

| scenario | corr | RMSE $/t | 2007/08 hike model | hike obs | 2006 mean model | 2006 obs |
|---|---:|---:|---:|---:|---:|---:|
| undisturbed | -0.065 | 213.3 | ×4.78 | ×1.88 | 43.1 | 213.5 |
| harvest | -0.160 | 205.7 | ×4.53 | ×1.88 | 65.3 | 213.5 |
| harvest_amis | -0.082 | 197.6 | ×4.54 | ×1.88 | 65.3 | 213.5 |

## Supply and stocks vs USDA world (2006–11)

Model sums 27 AgrimateRegionsWheat nodes; USDA is the world aggregate.
Level bias from missing coverage is expected; **anomaly correlation**
is the performance number. FAOSTAT Food Balances remain labelled A1
(Bai found FAO anomalies closer to prices in 2020–24; we stay on USDA
because FAOSTAT FB is not in this repository).

| scenario | field | corr | RMSE | mean model | mean USDA |
|---|---|---:|---:|---:|---:|
| undisturbed | production | 0.000 | 38.68 | 542.25 | 519.40 |
| undisturbed | consumption | -0.466 | 48.00 | 538.80 | 520.12 |
| undisturbed | ending_stocks | 0.737 | 48.06 | 200.88 | 157.43 |
| undisturbed | stock_to_use | 0.584 | 0.09 | 0.38 | 0.30 |
| harvest | production | 0.795 | 29.55 | 541.54 | 519.40 |
| harvest | consumption | 0.204 | 39.31 | 531.38 | 520.12 |
| harvest | ending_stocks | 0.834 | 90.26 | 245.64 | 157.43 |
| harvest | stock_to_use | 0.520 | 0.17 | 0.46 | 0.30 |
| harvest_amis | production | 0.795 | 29.55 | 541.54 | 519.40 |
| harvest_amis | consumption | 0.171 | 40.73 | 531.64 | 520.12 |
| harvest_amis | ending_stocks | 0.699 | 94.68 | 248.09 | 157.43 |
| harvest_amis | stock_to_use | 0.374 | 0.18 | 0.47 | 0.30 |

## G0-U undisturbed dynamics (after 2003–05 spin-up)

Repeating seasonal harvest, no AMIS. Not a world-price pin.

- post-spin-up price mean: 0.3191
- within-window CV: 1.174
- annual-mean min/max: 0.2020 / 0.3894
- last/first annual-mean ratio (drift): 1.630
- year-to-year seasonal-shape RMSE: 0.1604
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
- `figures/fig4_author_vs_host_prices.png` (P7; author Fig. 4d vs host D.7)
- `figures/fig6_hindcast_seasonal.png` (P8; month-of-year path)
- `fig4.md` — author series score. Independent implementation, not a replication.
- `hindcast.md` — G0-H 2006–11 score. Explicit sourced shortfall, not a retune.
- `regional.md` — P9 named-node vs `psd_regional_annual()`. Coverage labelled (A8); no xmin/p_sto fit.

## What this does not do

- Does not retune αI, p_sto, or x_min from Pink Sheet or from Bai's table.
- Does not split-calibrate 2008 vs 2022 (Bai's finding that one set cannot
  fit both crises is recorded as an open G0-H question).
- Does not implement G1 substitution or G2 government best-response.
- Fig. 4 author series are scored in `fig4.md` (P7). Not a replication.
  Host `AgrimateParams` were not retuned to the Fig. 4 NetCDF knobs.

## OAT sensitivity (diagnostic, author defaults unchanged)

Each named parameter is varied individually. α_foreign=10 is Bai's
fit, shown as an alternative, not adopted.

Window is harvest+AMIS **2006–08 simulation** (not the 2003–11 hindcast).
Author defaults stay αI=3.2, p_sto=0.1, xmin=0.2, εc=0.1, σ=2.
Bai αI=10 is listed, not adopted. A knob *moves* the 2008 hike if
|Δ×| ≥ 0.10 versus that axis's author value; otherwise it does not.
Unconverged scipy stays labelled (N5), not a retune.

- `alpha_i` default 3.2 → 2008 hike ×2.31.
  - moves: `alpha_i`=5 → ×2.95 (Δ=+0.63)
  - moves: `alpha_i`=10 → ×3.58 (Δ=+1.26)
- `p_sto_annual` default 0.1 → 2008 hike ×2.31.
  - moves: `p_sto_annual`=0.05 → ×1.96 (Δ=-0.35)
  - does not: `p_sto_annual`=0.15 → ×2.27 (Δ=-0.04)
- `xmin_share` default 0.2 → 2008 hike ×2.31.
  - moves: `xmin_share`=0.1 → ×2.21 (Δ=-0.10)
- `eps_c` default 0.1 → 2008 hike ×2.31.
  - does not: `eps_c`=0.2 → ×2.31 (Δ=+0.00)
- `sigma_ces` default 2 → 2008 hike ×2.31.
  - does not: `sigma_ces`=2.5 → ×2.31 (Δ=+0.00)

**Moves 2008 hike:** `alpha_i`=5 → ×2.95 (Δ=+0.63); `alpha_i`=10 → ×3.58 (Δ=+1.26); `p_sto_annual`=0.05 → ×1.96 (Δ=-0.35); `xmin_share`=0.1 → ×2.21 (Δ=-0.10).
**Does not:** `p_sto_annual`=0.15 → ×2.27 (Δ=-0.04); `eps_c`=0.2 → ×2.31 (Δ=+0.00); `sigma_ces`=2.5 → ×2.31 (Δ=+0.00).
No parameter was adopted as a new default.
εc and σ silent on world price is expected while D.30/D.35 do not
set T*+domestic inflows (S4).

| param | value | scenario | corr | hike_2008 | pidx_max | failed | unconverged |
|---|---:|---|---:|---:|---:|---:|---:|
| alpha_i | 3.2 | harvest_amis | -0.077 | ×2.31 | 3.769 | 0 | 611 |
| alpha_i | 5.0 | harvest_amis | -0.087 | ×2.95 | 10.046 | 0 | 603 |
| alpha_i | 10.0 | harvest_amis | -0.065 | ×3.58 | 473.490 | 0 | 721 |
| p_sto_annual | 0.05 | harvest_amis | -0.191 | ×1.96 | 3.913 | 0 | 705 |
| p_sto_annual | 0.1 | harvest_amis | -0.077 | ×2.31 | 3.769 | 0 | 611 |
| p_sto_annual | 0.15 | harvest_amis | -0.241 | ×2.27 | 3.818 | 0 | 637 |
| xmin_share | 0.1 | harvest_amis | -0.300 | ×2.21 | 3.943 | 0 | 455 |
| xmin_share | 0.2 | harvest_amis | -0.077 | ×2.31 | 3.769 | 0 | 611 |
| eps_c | 0.1 | harvest_amis | -0.077 | ×2.31 | 3.769 | 0 | 611 |
| eps_c | 0.2 | harvest_amis | -0.077 | ×2.31 | 3.769 | 0 | 611 |
| sigma_ces | 2.0 | harvest_amis | -0.077 | ×2.31 | 3.769 | 0 | 611 |
| sigma_ces | 2.5 | harvest_amis | -0.077 | ×2.31 | 3.769 | 0 | 611 |

