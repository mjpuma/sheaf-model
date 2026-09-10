# Gate 0 report — maize

Window 2006–2011. Ask-dominated bilateral spine (`sheaf.dynamic_crop`). No cross-grain substitution.

Parameters: see `diagnostics/GATE0_PARAMETERIZATION.md`.

## Robustness asserts
- PASS twin identity (no harvest/demand/AMIS ⇒ flat at p0)
- PASS AMIS raises price in primary ban window (maize: must not cut world price)
- PASS AMIS cuts Argentina offers in check window (shipments not asserted for maize/rice)
- PASS no fake spring lean-season spike (climatology path)

## Parameters (`CropParams`)
```
CropParams(crop='maize', elast=-0.25, stu_target=0.16, max_stu=0.18, seasonal_buffer_steps=0.0, pipeline_max_steps=12, rebuild_lambda=0.08, warehouse_lambda=0.08, inv_eta=0.85, smooth=0.65, trade_w=0.8, unmet_kappa=2.5, block_kappa=4.0, ask_alpha=0.15, ask_target_fill=0.7, ask_comp_elast=1.25, ask_beta=0.18, ask_rival=0.8, foresight_phi=0.5, harvest_pulse_frac=0.12, residual_subst=0.15, twin_harvest='seasonal', shock_mode='full', industrial_nodes=('USA',), ind_base_years=(2000, 2004))
```

## Monthly price vs Pink Sheet
- `full` corr = +0.778
- `shocks` corr = +0.383
- `demand` corr = +0.540
- `tau` corr = +0.223

## Crisis hike ratios (3-mo mean peak/base)
- **2007/08** obs×1.84  `full`×2.20  `shocks`×1.30  `demand`×1.49  `tau`×1.09
- **2010/11** obs×1.44  `full`×1.59  `shocks`×1.08  `demand`×1.18  `tau`×0.93

## Attribution (which isolated leg carries the hike)
- 2007/08: shocks×1.30  demand×1.49  tau×1.09 (full×2.20) — demand-led
- 2010/11: shocks×1.08  demand×1.18  tau×0.93 (full×1.59) — demand-led
- **tau column, unpinned baseline**: 2007/08 ×1.69 (vs ×1.09 above), 2010/11 ×0.88 (vs ×0.93) — restriction-led / demand-led
  The tau leg's base window is pinned at p0 by the calm branch, so the ratio above understates the restriction channel. The unpinned line is the like-for-like measurement; both are printed until the coauthors settle which is the headline.

## US maize industrial (inelastic FSI excess)
- Cumulative US industrial use over window: 453.5 MMT-steps (RFS residual vs 2000–04 FSI).

## Annual world ending stocks (calendar Dec vs PSD; MY-end month=8)
- 2006: Dec 488.9 MMT (STU 0.74); MY-end 87.4 MMT (STU 0.13) vs PSD 108.8 MMT (STU 0.16)
- 2007: Dec 549.9 MMT (STU 0.77); MY-end 73.1 MMT (STU 0.10) vs PSD 125.4 MMT (STU 0.18)
- 2008: Dec 594.3 MMT (STU 0.81); MY-end 137.9 MMT (STU 0.19) vs PSD 136.0 MMT (STU 0.19)
- 2009: Dec 578.1 MMT (STU 0.75); MY-end 143.8 MMT (STU 0.19) vs PSD 131.5 MMT (STU 0.17)
- 2010: Dec 581.2 MMT (STU 0.72); MY-end 143.3 MMT (STU 0.18) vs PSD 114.9 MMT (STU 0.14)
- 2011: Dec 614.6 MMT (STU 0.75); MY-end 177.3 MMT (STU 0.22) vs PSD 122.8 MMT (STU 0.15)
- Mean model/PSD: Dec ×4.62, MY-end ×1.03 (target ~1; >2 still fat warehouse)

## World MY-end excluding China (FAO/AMIS tightness; China stays a named node)
- China share of PSD world stocks: 35%
- Mean model/PSD MY-end excluding China: ×1.44 (including China ×1.03)
- China stock *levels* are estimated (state reserves, not a Gate 0 fail). This series is the traded-market remainder.
- China maize USDA MY-end is September; the world bar is August, so this snapshot under-subtracts China (model China at August is thin). Local-MY China is separately fat. Not a warehouse retune.
- 2006: ex-China 87.4 vs PSD 72.1 MMT (STU 0.17 vs 0.14; China 34% of PSD world)
- 2007: ex-China 73.1 vs PSD 89.1 MMT (STU 0.13 vs 0.16; China 29% of PSD world)
- 2008: ex-China 126.0 vs PSD 91.8 MMT (STU 0.22 vs 0.16; China 33% of PSD world)
- 2009: ex-China 124.6 vs PSD 88.9 MMT (STU 0.21 vs 0.15; China 32% of PSD world)
- 2010: ex-China 122.4 vs PSD 71.6 MMT (STU 0.20 vs 0.12; China 38% of PSD world)
- 2011: ex-China 142.8 vs PSD 67.1 MMT (STU 0.23 vs 0.11; China 45% of PSD world)

## Annual world consumption vs PSD (calendar year, official matched)
Country-sum PSD (not `load_crop_world`, which omits the EU). Mean flex + isoelastic; year-by-year food/feed is a sensitivity. Not Agrimate Fig. 4 (that figure is supply Δ and stock Δ).
- Mean model/PSD: ×0.92 (unweighted median country-year ×0.91)
- Corr(levels) = -0.64
- Δcons as % of mean PSD use (815 MMT); sign 1/5
- 2006: model 802.9 vs PSD 726.9 MMT (×1.10; Δ — / — pp)
- 2007: model 748.8 vs PSD 781.1 MMT (×0.96; Δ -6.6 / +6.7 pp)
- 2008: model 724.5 vs PSD 794.5 MMT (×0.91; Δ -3.0 / +1.6 pp)
- 2009: model 776.0 vs PSD 831.9 MMT (×0.93; Δ +6.3 / +4.6 pp)
- 2010: model 747.2 vs PSD 867.9 MMT (×0.86; Δ -3.5 / +4.4 pp)
- 2011: model 719.1 vs PSD 886.0 MMT (×0.81; Δ -3.5 / +2.2 pp)
- 2011 named-node snapshot (psd_cons>10 MMT):
  - USA: model 262.2 vs PSD 278.0 MMT (×0.94)
  - China: model 143.5 vs PSD 204.0 MMT (×0.70)
  - RestOfWorld: model 125.5 vs PSD 163.9 MMT (×0.77)
  - EU: model 54.2 vs PSD 69.7 MMT (×0.78)
  - Brazil: model 39.0 vs PSD 51.5 MMT (×0.76)
  - Mexico: model 25.5 vs PSD 29.0 MMT (×0.88)

## AMIS shipment signs (official matched vs harvest-only)
Isolated-τ assert ≠ this table. Fig. 3 is model-implied withheld grain, not FAOSTAT trade. Ratio < 1 means AMIS cut that node.
- Argentina May 2007: offers fall, shipments barely move (demand already the constraint). Isolated τ must not cut the 14-month mean world price.
- Argentina assert_May2007 2007-05→2007-05: offer ×0.30, ship ×0.92 (cut; τ̄=0.70)
- Argentina quota_May07_Jan08 2007-05→2008-01: offer ×0.35, ship ×0.85 (cut; τ̄=0.70)
- USA unrestricted_control 2007-05→2008-06: offer ×1.16, ship ×0.88 (cut; τ̄=0.00)
- Ukraine quota_2010_11 2010-10→2011-06: offer ×0.38, ship ×0.44 (cut; τ̄=0.70)
- Argentina calendar-year exports vs PSD:
  - 2007: full 11.9 vs no-AMIS 13.8 vs PSD 14.8 MMT (model/PSD ×0.80)
  - 2008: full 6.5 vs no-AMIS 8.4 vs PSD 10.3 MMT (model/PSD ×0.63)
  - 2010: full 9.0 vs no-AMIS 12.0 vs PSD 16.3 MMT (model/PSD ×0.55)
  - 2011: full 5.5 vs no-AMIS 8.9 vs PSD 17.1 MMT (model/PSD ×0.32)

## Country MY-end stocks vs PSD (local marketing year, not groupings)
- Median model/PSD stock (psd>1 MMT): ×1.63 (mean ×1.94)
- Median model/PSD consumption: ×0.91
- Δstock sign agreement: 41/80
- 2011 snapshot (psd>2 MMT):
  - China (m=9): model 143.6 vs PSD 55.7 MMT (×2.58)
  - USA (m=8): model 30.6 vs PSD 25.1 MMT (×1.22)
  - RestOfWorld (m=8): model 18.3 vs PSD 21.4 MMT (×0.86)
  - EU (m=9): model 25.6 vs PSD 6.7 MMT (×3.83)
  - Brazil (m=2): model 26.1 vs PSD 4.2 MMT (×6.19)
  - Egypt (m=8): model 1.0 vs PSD 2.2 MMT (×0.46)

## Artifacts
- `diagnostics/gate0_maize_score.csv`
- `diagnostics/gate0_maize_exporters.csv`
- `diagnostics/gate0_maize_shipments.csv`
- `diagnostics/gate0_maize_exports_psd.csv`
- `figures/fig_gate0_maize_shipments.png`
- `diagnostics/gate0_maize_stocks.csv`
- `diagnostics/gate0_maize_country_balance.csv`
- `figures/fig_gate0_maize_diagnostics.png`
- `figures/fig_gate0_maize_country_stocks.png`
- `figures/fig_gate0_maize_world_exchina.png`
- `diagnostics/gate0_maize_consumption.csv`
- `figures/fig_gate0_maize_world_consumption.png`
