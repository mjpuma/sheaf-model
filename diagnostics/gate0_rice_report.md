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
CropParams(crop='rice', elast=-0.2, stu_target=0.18, max_stu=0.22, seasonal_buffer_steps=0.0, pipeline_max_steps=0, rebuild_lambda=0.08, warehouse_lambda=0.08, inv_eta=0.95, smooth=0.65, trade_w=0.72, unmet_kappa=2.5, block_kappa=4.5, ask_alpha=0.15, ask_target_fill=0.7, ask_comp_elast=1.25, ask_beta=0.18, ask_rival=0.8, foresight_phi=0.55, harvest_pulse_frac=0.12, residual_subst=0.15, twin_harvest='seasonal', shock_mode='full', industrial_nodes=(), ind_base_years=(2000, 2004), ask_fill_ref='fixed', spec_kappa=0.0, carry_rate_annual=0.05, pin_calm=True)
```

## Monthly price vs Pink Sheet
- `full` corr = +0.676
- `shocks` corr = -0.132
- `demand` corr = +0.317
- `tau` corr = +0.644

## Crisis hike ratios (3-mo mean peak/base)
- **2007/08** obs×1.84  `full`×1.54  `shocks`×0.92  `demand`×1.19  `tau`×1.55
- **2010/11** obs×0.79  `full`×0.84  `shocks`×1.05  `demand`×1.58  `tau`×0.82

## Attribution (which isolated leg carries the hike)
- 2007/08: shocks×0.92  demand×1.19  tau×1.55 (full×1.54) — restriction-led
- 2010/11: shocks×1.05  demand×1.58  tau×0.82 (full×0.84) — demand-led
- **tau column, unpinned baseline**: 2007/08 ×1.51 (vs ×1.55 above), 2010/11 ×0.82 (vs ×0.82) — restriction-led / demand-led
  The tau leg's base window is pinned at p0 by the calm branch, so the ratio above understates the restriction channel. The unpinned line is the like-for-like measurement; both are printed until the coauthors settle which is the headline.

## Annual world ending stocks (calendar Dec vs PSD; MY-end month=8)
- 2006: Dec 126.0 MMT (STU 0.30); MY-end 74.7 MMT (STU 0.18) vs PSD 76.4 MMT (STU 0.18)
- 2007: Dec 141.2 MMT (STU 0.33); MY-end 84.1 MMT (STU 0.20) vs PSD 82.3 MMT (STU 0.19)
- 2008: Dec 163.0 MMT (STU 0.38); MY-end 103.5 MMT (STU 0.24) vs PSD 95.0 MMT (STU 0.22)
- 2009: Dec 157.8 MMT (STU 0.36); MY-end 106.0 MMT (STU 0.25) vs PSD 97.5 MMT (STU 0.23)
- 2010: Dec 158.6 MMT (STU 0.36); MY-end 105.4 MMT (STU 0.24) vs PSD 102.8 MMT (STU 0.23)
- 2011: Dec 163.7 MMT (STU 0.36); MY-end 108.0 MMT (STU 0.24) vs PSD 112.7 MMT (STU 0.25)
- Mean model/PSD: Dec ×1.62, MY-end ×1.03 (target ~1; >2 still fat warehouse)

## World MY-end excluding China (FAO/AMIS tightness; China stays a named node)
- China share of PSD world stocks: 44%
- Mean model/PSD MY-end excluding China: ×1.11 (including China ×1.03)
- Mean model/PSD MY-end excluding China+India: ×1.14
- China stock *levels* are estimated (state reserves, not a Gate 0 fail). This series is the traded-market remainder.
- 2006: ex-China 40.6 vs PSD 40.4 MMT (STU 0.14 vs 0.14; China 47% of PSD world); ex-CN+IN 27.4 vs 29.0 MMT
- 2007: ex-China 48.0 vs PSD 44.3 MMT (STU 0.16 vs 0.15; China 46% of PSD world); ex-CN+IN 31.7 vs 31.3 MMT
- 2008: ex-China 64.0 vs PSD 55.5 MMT (STU 0.21 vs 0.18; China 42% of PSD world); ex-CN+IN 41.0 vs 36.5 MMT
- 2009: ex-China 66.4 vs PSD 55.5 MMT (STU 0.22 vs 0.19; China 43% of PSD world); ex-CN+IN 44.5 vs 35.0 MMT
- 2010: ex-China 66.1 vs PSD 58.3 MMT (STU 0.22 vs 0.19; China 43% of PSD world); ex-CN+IN 44.7 vs 34.8 MMT
- 2011: ex-China 69.1 vs PSD 62.7 MMT (STU 0.22 vs 0.20; China 44% of PSD world); ex-CN+IN 44.8 vs 37.6 MMT

## Annual world consumption vs PSD (calendar year, official matched)
Country-sum PSD (not `load_crop_world`, which omits the EU). Mean flex + isoelastic; year-by-year food/feed is a sensitivity. Not Agrimate Fig. 4 (that figure is supply Δ and stock Δ).
- Mean model/PSD: ×0.87 (unweighted median country-year ×0.84)
- Corr(levels) = -0.75
- Δcons as % of mean PSD use (436 MMT); sign 1/5
- 2006: model 397.9 vs PSD 418.3 MMT (×0.95; Δ — / — pp)
- 2007: model 384.1 vs PSD 426.6 MMT (×0.90; Δ -3.2 / +1.9 pp)
- 2008: model 365.8 vs PSD 435.8 MMT (×0.84; Δ -4.2 / +2.1 pp)
- 2009: model 372.7 vs PSD 435.2 MMT (×0.86; Δ +1.6 / -0.1 pp)
- 2010: model 370.4 vs PSD 443.9 MMT (×0.83; Δ -0.5 / +2.0 pp)
- 2011: model 372.4 vs PSD 455.2 MMT (×0.82; Δ +0.5 / +2.6 pp)
- 2011 named-node snapshot (psd_cons>10 MMT):
  - China: model 114.4 vs PSD 137.9 MMT (×0.83)
  - RestOfWorld: model 104.3 vs PSD 129.1 MMT (×0.81)
  - India: model 77.2 vs PSD 93.3 MMT (×0.83)
  - Indonesia: model 30.9 vs PSD 38.2 MMT (×0.81)
  - Vietnam: model 16.4 vs PSD 19.7 MMT (×0.84)
  - Thailand: model 8.6 vs PSD 10.4 MMT (×0.83)

## AMIS shipment signs (official matched vs harvest-only)
Isolated-τ assert ≠ this table. Fig. 3 is model-implied withheld grain, not FAOSTAT trade. Ratio < 1 means AMIS cut that node.
- Assert window is Vietnam Sep–Nov 2008 **tax**, not the 2007/08 ban. Clean ban+harvest overlap is Oct–Dec 2007. India lingering can leak.
- Vietnam assert_tax_SepNov2008 2008-09→2008-11: offer ×0.56, ship ×0.78 (cut; τ̄=0.50)
- Vietnam ban_harvest_overlap 2007-10→2007-12: offer ×0.06, ship ×0.25 (cut; τ̄=0.95)
- India ban_harvest_overlap 2007-10→2007-12: offer ×0.08, ship ×0.73 (cut; τ̄=0.95)
- Thailand unrestricted_control 2007-10→2007-12: offer ×1.10, ship ×1.07 (up; τ̄=0.00)
- India lingering_prohibition 2008-10→2011-09: offer ×0.29, ship ×1.92 (up; τ̄=0.95)
- Vietnam calendar-year exports vs PSD:
  - 2007: full 0.5 vs no-AMIS 1.7 vs PSD 4.6 MMT (model/PSD ×0.11)
  - 2008: full 1.0 vs no-AMIS 1.4 vs PSD 6.0 MMT (model/PSD ×0.17)
  - 2010: full 1.1 vs no-AMIS 1.7 vs PSD 7.0 MMT (model/PSD ×0.15)
  - 2011: full 0.3 vs no-AMIS 1.1 vs PSD 7.7 MMT (model/PSD ×0.03)

## Country MY-end stocks vs PSD (local marketing year, not groupings)
- Median model/PSD stock (psd>1 MMT): ×1.06 (mean ×1.42)
- Median model/PSD consumption: ×0.84
- Δstock sign agreement: 37/64
- 2011 snapshot (psd>2 MMT):
  - China (m=12): model 47.4 vs PSD 50.0 MMT (×0.95)
  - India (m=9): model 30.0 vs PSD 25.1 MMT (×1.19)
  - RestOfWorld (m=8): model 20.3 vs PSD 13.1 MMT (×1.55)
  - Thailand (m=12): model 9.7 vs PSD 9.3 MMT (×1.04)
  - Indonesia (m=12): model 5.1 vs PSD 7.4 MMT (×0.69)

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
