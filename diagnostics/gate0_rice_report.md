# Gate 0 report — rice

Window 2006–2011. Ask-dominated bilateral spine (`sheaf.dynamic_crop`). No cross-grain substitution.

Parameters: see `diagnostics/GATE0_PARAMETERIZATION.md`.

## Robustness asserts
- PASS twin identity (no harvest/demand/AMIS ⇒ flat at p0)
- PASS AMIS raises price in primary ban window (maize: must not cut world price)
- PASS AMIS cuts Vietnam offers in check window (shipments not asserted for maize/rice)
- PASS no fake spring lean-season spike (climatology path)

## Parameters (`CropParams`)
```
CropParams(crop='rice', elast=-0.2, stu_target=0.18, max_stu=0.22, seasonal_buffer_steps=0.0, pipeline_max_steps=0, rebuild_lambda=0.08, warehouse_lambda=0.08, inv_eta=0.95, smooth=0.65, trade_w=0.72, unmet_kappa=2.5, block_kappa=4.5, ask_alpha=0.15, ask_target_fill=0.7, ask_comp_elast=1.25, ask_beta=0.18, ask_rival=0.8, foresight_phi=0.55, harvest_pulse_frac=0.12, residual_subst=0.15, twin_harvest='seasonal', shock_mode='full', industrial_nodes=(), ind_base_years=(2000, 2004))
```

## Monthly price vs Pink Sheet
- `full` corr = +0.678
- `shocks` corr = -0.115
- `demand` corr = +0.309
- `tau` corr = +0.662

## Crisis hike ratios (3-mo mean peak/base)
- **2007/08** obs×1.84  `full`×1.72  `shocks`×0.93  `demand`×1.21  `tau`×1.75
- **2010/11** obs×0.79  `full`×0.82  `shocks`×1.06  `demand`×1.60  `tau`×0.81

## Attribution (which isolated leg carries the hike)
- 2007/08: shocks×0.93  demand×1.21  tau×1.75 (full×1.72) — restriction-led
- 2010/11: shocks×1.06  demand×1.60  tau×0.81 (full×0.82) — demand-led

## Annual world ending stocks (calendar Dec vs PSD; MY-end month=8)
- 2006: Dec 125.7 MMT (STU 0.30); MY-end 74.9 MMT (STU 0.18) vs PSD 76.4 MMT (STU 0.18)
- 2007: Dec 143.6 MMT (STU 0.34); MY-end 85.7 MMT (STU 0.20) vs PSD 82.3 MMT (STU 0.19)
- 2008: Dec 165.0 MMT (STU 0.38); MY-end 106.7 MMT (STU 0.25) vs PSD 95.0 MMT (STU 0.22)
- 2009: Dec 159.6 MMT (STU 0.37); MY-end 108.6 MMT (STU 0.25) vs PSD 97.5 MMT (STU 0.23)
- 2010: Dec 160.1 MMT (STU 0.36); MY-end 107.8 MMT (STU 0.24) vs PSD 102.8 MMT (STU 0.23)
- 2011: Dec 165.3 MMT (STU 0.37); MY-end 110.4 MMT (STU 0.24) vs PSD 112.7 MMT (STU 0.25)
- Mean model/PSD: Dec ×1.63, MY-end ×1.05 (target ~1; >2 still fat warehouse)

## World MY-end excluding China (FAO/AMIS tightness; China stays a named node)
- China share of PSD world stocks: 44%
- Mean model/PSD MY-end excluding China: ×1.14 (including China ×1.05)
- Mean model/PSD MY-end excluding China+India: ×1.17
- China stock *levels* are estimated (state reserves, not a Gate 0 fail). This series is the traded-market remainder.
- 2006: ex-China 40.8 vs PSD 40.4 MMT (STU 0.14 vs 0.14; China 47% of PSD world); ex-CN+IN 27.5 vs 29.0 MMT
- 2007: ex-China 49.2 vs PSD 44.3 MMT (STU 0.17 vs 0.15; China 46% of PSD world); ex-CN+IN 32.3 vs 31.3 MMT
- 2008: ex-China 67.1 vs PSD 55.5 MMT (STU 0.22 vs 0.18; China 42% of PSD world); ex-CN+IN 43.3 vs 36.5 MMT
- 2009: ex-China 68.4 vs PSD 55.5 MMT (STU 0.23 vs 0.19; China 43% of PSD world); ex-CN+IN 46.1 vs 35.0 MMT
- 2010: ex-China 67.8 vs PSD 58.3 MMT (STU 0.22 vs 0.19; China 43% of PSD world); ex-CN+IN 45.9 vs 34.8 MMT
- 2011: ex-China 70.8 vs PSD 62.7 MMT (STU 0.23 vs 0.20; China 44% of PSD world); ex-CN+IN 46.1 vs 37.6 MMT

## Annual world consumption vs PSD (calendar year, official matched)
Country-sum PSD (not `load_crop_world`, which omits the EU). Mean flex + isoelastic; year-by-year food/feed is a sensitivity. Not Agrimate Fig. 4 (that figure is supply Δ and stock Δ).
- Mean model/PSD: ×0.86 (unweighted median country-year ×0.83)
- Corr(levels) = -0.74
- Δcons as % of mean PSD use (436 MMT); sign 1/5
- 2006: model 398.3 vs PSD 418.3 MMT (×0.95; Δ — / — pp)
- 2007: model 380.2 vs PSD 426.6 MMT (×0.89; Δ -4.2 / +1.9 pp)
- 2008: model 363.6 vs PSD 435.8 MMT (×0.83; Δ -3.8 / +2.1 pp)
- 2009: model 370.6 vs PSD 435.2 MMT (×0.85; Δ +1.6 / -0.1 pp)
- 2010: model 368.8 vs PSD 443.9 MMT (×0.83; Δ -0.4 / +2.0 pp)
- 2011: model 370.4 vs PSD 455.2 MMT (×0.81; Δ +0.4 / +2.6 pp)
- 2011 named-node snapshot (psd_cons>10 MMT):
  - China: model 113.7 vs PSD 137.9 MMT (×0.82)
  - RestOfWorld: model 103.7 vs PSD 129.1 MMT (×0.80)
  - India: model 76.8 vs PSD 93.3 MMT (×0.82)
  - Indonesia: model 30.8 vs PSD 38.2 MMT (×0.81)
  - Vietnam: model 16.4 vs PSD 19.7 MMT (×0.84)
  - Thailand: model 8.5 vs PSD 10.4 MMT (×0.82)

## AMIS shipment signs (official matched vs harvest-only)
Isolated-τ assert ≠ this table. Fig. 3 is model-implied withheld grain, not FAOSTAT trade. Ratio < 1 means AMIS cut that node.
- Assert window is Vietnam Sep–Nov 2008 **tax**, not the 2007/08 ban. Clean ban+harvest overlap is Oct–Dec 2007. India lingering can leak.
- Vietnam assert_tax_SepNov2008 2008-09→2008-11: offer ×0.57, ship ×0.77 (cut; τ̄=0.50)
- Vietnam ban_harvest_overlap 2007-10→2007-12: offer ×0.06, ship ×0.26 (cut; τ̄=0.95)
- India ban_harvest_overlap 2007-10→2007-12: offer ×0.09, ship ×0.77 (cut; τ̄=0.95)
- Thailand unrestricted_control 2007-10→2007-12: offer ×1.14, ship ×1.09 (up; τ̄=0.00)
- India lingering_prohibition 2008-10→2011-09: offer ×0.31, ship ×1.93 (up; τ̄=0.95)
- Vietnam calendar-year exports vs PSD:
  - 2007: full 0.5 vs no-AMIS 1.6 vs PSD 4.6 MMT (model/PSD ×0.11)
  - 2008: full 1.0 vs no-AMIS 1.3 vs PSD 6.0 MMT (model/PSD ×0.16)
  - 2010: full 1.0 vs no-AMIS 1.6 vs PSD 7.0 MMT (model/PSD ×0.15)
  - 2011: full 0.2 vs no-AMIS 1.0 vs PSD 7.7 MMT (model/PSD ×0.03)

## Country MY-end stocks vs PSD (local marketing year, not groupings)
- Median model/PSD stock (psd>1 MMT): ×1.06 (mean ×1.44)
- Median model/PSD consumption: ×0.83
- Δstock sign agreement: 36/64
- 2011 snapshot (psd>2 MMT):
  - China (m=12): model 47.9 vs PSD 50.0 MMT (×0.96)
  - India (m=9): model 30.4 vs PSD 25.1 MMT (×1.21)
  - RestOfWorld (m=8): model 21.2 vs PSD 13.1 MMT (×1.62)
  - Thailand (m=12): model 9.8 vs PSD 9.3 MMT (×1.05)
  - Indonesia (m=12): model 5.2 vs PSD 7.4 MMT (×0.71)

## Artifacts
- `diagnostics/gate0_rice_score.csv`
- `diagnostics/gate0_rice_exporters.csv`
- `diagnostics/gate0_rice_shipments.csv`
- `diagnostics/gate0_rice_exports_psd.csv`
- `figures/fig_gate0_rice_shipments.png`
- `diagnostics/gate0_rice_stocks.csv`
- `diagnostics/gate0_rice_country_balance.csv`
- `figures/fig_gate0_rice_diagnostics.png`
- `figures/fig_gate0_rice_country_stocks.png`
- `figures/fig_gate0_rice_world_exchina.png`
- `diagnostics/gate0_rice_consumption.csv`
- `figures/fig_gate0_rice_world_consumption.png`
