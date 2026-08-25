# Gate 0 report — wheat

Window 2006–2011. Ask-dominated bilateral spine (`sheaf.dynamic_crop`). No cross-grain substitution.

Parameters: see `diagnostics/GATE0_PARAMETERIZATION.md`.

## Robustness asserts
- PASS twin identity (no harvest/demand/AMIS ⇒ flat at p0)
- PASS AMIS raises price in primary ban window (maize: must not cut world price)
- PASS AMIS cuts Russia offers in check window and shipments
- PASS no fake spring lean-season spike (climatology path)

## Parameters (`CropParams`)
```
CropParams(crop='wheat', elast=-0.15, stu_target=0.2, max_stu=0.28, seasonal_buffer_steps=0.0, pipeline_max_steps=12, rebuild_lambda=0.08, warehouse_lambda=0.08, inv_eta=1.0, smooth=0.65, trade_w=0.7, unmet_kappa=2.5, block_kappa=4.0, ask_alpha=0.15, ask_target_fill=0.7, ask_comp_elast=1.25, ask_beta=0.18, ask_rival=0.8, foresight_phi=0.55, harvest_pulse_frac=0.12, residual_subst=0.15, twin_harvest='seasonal', shock_mode='full', industrial_nodes=(), ind_base_years=(2000, 2004))
```

## Monthly price vs Pink Sheet
- `full` corr = +0.720
- `shocks` corr = +0.400
- `demand` corr = +0.015
- `tau` corr = +0.550

## Crisis hike ratios (3-mo mean peak/base)
- **2007/08** obs×1.82  `full`×2.27  `shocks`×1.20  `demand`×0.98  `tau`×1.70
- **2010/11** obs×1.16  `full`×1.45  `shocks`×1.85  `demand`×1.35  `tau`×1.36

## Attribution (which isolated leg carries the hike)
- 2007/08: shocks×1.20  demand×0.98  tau×1.70 (full×2.27) — restriction-led
- 2010/11: shocks×1.85  demand×1.35  tau×1.36 (full×1.45) — production-led

## Annual world ending stocks (calendar Dec vs PSD; MY-end month=5)
- 2006: Dec 241.3 MMT (STU 0.49); MY-end 126.5 MMT (STU 0.26) vs PSD 134.8 MMT (STU 0.27)
- 2007: Dec 278.9 MMT (STU 0.56); MY-end 140.2 MMT (STU 0.28) vs PSD 129.2 MMT (STU 0.26)
- 2008: Dec 341.9 MMT (STU 0.67); MY-end 169.5 MMT (STU 0.33) vs PSD 170.3 MMT (STU 0.33)
- 2009: Dec 351.4 MMT (STU 0.67); MY-end 213.4 MMT (STU 0.41) vs PSD 203.8 MMT (STU 0.39)
- 2010: Dec 322.1 MMT (STU 0.61); MY-end 206.6 MMT (STU 0.39) vs PSD 199.6 MMT (STU 0.38)
- 2011: Dec 351.1 MMT (STU 0.62); MY-end 206.5 MMT (STU 0.37) vs PSD 200.1 MMT (STU 0.35)
- Mean model/PSD: Dec ×1.84, MY-end ×1.02 (target ~1; >2 still fat warehouse)

## World MY-end excluding China (FAO/AMIS tightness; China stays a named node)
- China share of PSD world stocks: 28%
- Mean model/PSD MY-end excluding China: ×1.09 (including China ×1.02)
- China stock *levels* are estimated (state reserves, not a Gate 0 fail). This series is the traded-market remainder.
- 2006: ex-China 96.9 vs PSD 96.2 MMT (STU 0.25 vs 0.25; China 29% of PSD world)
- 2007: ex-China 106.4 vs PSD 89.9 MMT (STU 0.27 vs 0.23; China 30% of PSD world)
- 2008: ex-China 127.4 vs PSD 123.9 MMT (STU 0.32 vs 0.31; China 27% of PSD world)
- 2009: ex-China 162.8 vs PSD 149.6 MMT (STU 0.39 vs 0.36; China 27% of PSD world)
- 2010: ex-China 158.0 vs PSD 140.8 MMT (STU 0.38 vs 0.34; China 29% of PSD world)
- 2011: ex-China 156.7 vs PSD 144.3 MMT (STU 0.36 vs 0.33; China 28% of PSD world)

## Annual world consumption vs PSD (calendar year, official matched)
Country-sum PSD (not `load_crop_world`, which omits the EU). Mean flex + isoelastic; year-by-year food/feed is a sensitivity. Not Agrimate Fig. 4 (that figure is supply Δ and stock Δ).
- Mean model/PSD: ×0.92 (unweighted median country-year ×0.92)
- Corr(levels) = -0.17
- Δcons as % of mean PSD use (644 MMT); sign 3/5
- 2006: model 619.6 vs PSD 619.1 MMT (×1.00; Δ — / — pp)
- 2007: model 574.8 vs PSD 614.4 MMT (×0.94; Δ -7.0 / -0.7 pp)
- 2008: model 568.8 vs PSD 636.8 MMT (×0.89; Δ -0.9 / +3.5 pp)
- 2009: model 609.6 vs PSD 650.9 MMT (×0.94; Δ +6.3 / +2.2 pp)
- 2010: model 622.2 vs PSD 653.4 MMT (×0.95; Δ +2.0 / +0.4 pp)
- 2011: model 570.7 vs PSD 690.8 MMT (×0.83; Δ -8.0 / +5.8 pp)
- 2011 named-node snapshot (psd_cons>10 MMT):
  - RestOfWorld: model 158.3 vs PSD 192.2 MMT (×0.82)
  - EU: model 110.2 vs PSD 126.7 MMT (×0.87)
  - China: model 97.3 vs PSD 123.5 MMT (×0.79)
  - India: model 68.4 vs PSD 81.4 MMT (×0.84)
  - Russia: model 34.0 vs PSD 38.0 MMT (×0.89)
  - USA: model 27.6 vs PSD 32.0 MMT (×0.86)

## AMIS shipment signs (official matched vs harvest-only)
Isolated-τ assert ≠ this table. Fig. 3 is model-implied withheld grain, not FAOSTAT trade. Ratio < 1 means AMIS cut that node.
- Russia 2010: offers fall hard; shipments fall less (Armington fill). Calendar-year model still well above PSD.
- Russia assert_AugDec2010 2010-08→2010-12: offer ×0.11, ship ×0.79 (cut; τ̄=0.95)
- Ukraine quota_2010_11 2010-10→2011-06: offer ×1.23, ship ×1.43 (up; τ̄=0.70)
- Russia calendar-year exports vs PSD:
  - 2007: full 9.0 vs no-AMIS 10.3 vs PSD 12.2 MMT (model/PSD ×0.73)
  - 2008: full 11.6 vs no-AMIS 11.2 vs PSD 18.4 MMT (model/PSD ×0.63)
  - 2010: full 9.5 vs no-AMIS 10.2 vs PSD 4.0 MMT (model/PSD ×2.39)
  - 2011: full 4.1 vs no-AMIS 5.9 vs PSD 21.6 MMT (model/PSD ×0.19)

## Country MY-end stocks vs PSD (local marketing year, not groupings)
- Median model/PSD stock (psd>1 MMT): ×0.46 (mean ×0.73)
- Median model/PSD consumption: ×0.92
- Δstock sign agreement: 35/83
- 2011 snapshot (psd>2 MMT):
  - China (m=6): model 89.3 vs PSD 55.8 MMT (×1.60)
  - RestOfWorld (m=5): model 6.4 vs PSD 39.5 MMT (×0.16)
  - USA (m=5): model 5.1 vs PSD 20.2 MMT (×0.25)
  - India (m=3): model 35.4 vs PSD 19.9 MMT (×1.77)
  - EU (m=6): model 19.7 vs PSD 15.6 MMT (×1.27)
  - Russia (m=6): model 9.6 vs PSD 10.9 MMT (×0.89)
  - Egypt (m=5): model 3.6 vs PSD 7.1 MMT (×0.51)
  - Australia (m=9): model 1.4 vs PSD 7.1 MMT (×0.20)
  - Kazakhstan (m=6): model 1.2 vs PSD 6.2 MMT (×0.20)
  - Canada (m=7): model 1.0 vs PSD 5.9 MMT (×0.17)
  - Ukraine (m=6): model 2.8 vs PSD 5.4 MMT (×0.53)

## Artifacts
- `diagnostics/gate0_wheat_score.csv`
- `diagnostics/gate0_wheat_exporters.csv`
- `diagnostics/gate0_wheat_shipments.csv`
- `diagnostics/gate0_wheat_exports_psd.csv`
- `figures/fig_gate0_wheat_shipments.png`
- `diagnostics/gate0_wheat_stocks.csv`
- `diagnostics/gate0_wheat_country_balance.csv`
- `figures/fig_gate0_wheat_diagnostics.png`
- `figures/fig_gate0_wheat_country_stocks.png`
- `figures/fig_gate0_wheat_world_exchina.png`
- `diagnostics/gate0_wheat_consumption.csv`
- `figures/fig_gate0_wheat_world_consumption.png`
