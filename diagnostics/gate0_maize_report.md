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
- `full` corr = +0.781
- `shocks` corr = +0.373
- `demand` corr = +0.533
- `tau` corr = +0.237

## Crisis hike ratios (3-mo mean peak/base)
- **2007/08** obs×1.84  `full`×2.22  `shocks`×1.29  `demand`×1.46  `tau`×1.10
- **2010/11** obs×1.44  `full`×1.61  `shocks`×1.03  `demand`×1.12  `tau`×0.92

## Attribution (which isolated leg carries the hike)
- 2007/08: shocks×1.29  demand×1.46  tau×1.10 (full×2.22) — demand-led
- 2010/11: shocks×1.03  demand×1.12  tau×0.92 (full×1.61) — demand-led
- **tau column, unpinned baseline**: 2007/08 ×1.69 (vs ×1.10 above), 2010/11 ×0.86 (vs ×0.92) — restriction-led / demand-led
  The tau leg's base window is pinned at p0 by the calm branch, so the ratio above understates the restriction channel. The unpinned line is the like-for-like measurement; both are printed until the coauthors settle which is the headline.

## US maize industrial (inelastic FSI excess)
- Cumulative US industrial use over window: 453.5 MMT-steps (RFS residual vs 2000–04 FSI).

## Annual world ending stocks (calendar Dec vs PSD; MY-end month=8)
- 2006: Dec 489.5 MMT (STU 0.74); MY-end 88.1 MMT (STU 0.13) vs PSD 108.8 MMT (STU 0.16)
- 2007: Dec 550.0 MMT (STU 0.77); MY-end 73.2 MMT (STU 0.10) vs PSD 125.4 MMT (STU 0.18)
- 2008: Dec 596.2 MMT (STU 0.82); MY-end 139.4 MMT (STU 0.19) vs PSD 136.0 MMT (STU 0.19)
- 2009: Dec 579.9 MMT (STU 0.75); MY-end 146.1 MMT (STU 0.19) vs PSD 131.5 MMT (STU 0.17)
- 2010: Dec 584.3 MMT (STU 0.73); MY-end 145.3 MMT (STU 0.18) vs PSD 114.9 MMT (STU 0.14)
- 2011: Dec 617.9 MMT (STU 0.76); MY-end 181.0 MMT (STU 0.22) vs PSD 122.8 MMT (STU 0.15)
- Mean model/PSD: Dec ×4.63, MY-end ×1.04 (target ~1; >2 still fat warehouse)

## World MY-end excluding China (FAO/AMIS tightness; China stays a named node)
- China share of PSD world stocks: 35%
- Mean model/PSD MY-end excluding China: ×1.45 (including China ×1.04)
- China stock *levels* are estimated (state reserves, not a Gate 0 fail). This series is the traded-market remainder.
- China maize USDA MY-end is September; the world bar is August, so this snapshot under-subtracts China (model China at August is thin). Local-MY China is separately fat. Not a warehouse retune.
- 2006: ex-China 88.1 vs PSD 72.1 MMT (STU 0.17 vs 0.14; China 34% of PSD world)
- 2007: ex-China 73.2 vs PSD 89.1 MMT (STU 0.13 vs 0.16; China 29% of PSD world)
- 2008: ex-China 126.9 vs PSD 91.8 MMT (STU 0.22 vs 0.16; China 33% of PSD world)
- 2009: ex-China 126.2 vs PSD 88.9 MMT (STU 0.21 vs 0.15; China 32% of PSD world)
- 2010: ex-China 123.2 vs PSD 71.6 MMT (STU 0.20 vs 0.12; China 38% of PSD world)
- 2011: ex-China 144.6 vs PSD 67.1 MMT (STU 0.24 vs 0.11; China 45% of PSD world)

## Annual world consumption vs PSD (calendar year, official matched)
Country-sum PSD (not `load_crop_world`, which omits the EU). Mean flex + isoelastic; year-by-year food/feed is a sensitivity. Not Agrimate Fig. 4 (that figure is supply Δ and stock Δ).
- Mean model/PSD: ×0.92 (unweighted median country-year ×0.91)
- Corr(levels) = -0.66
- Δcons as % of mean PSD use (815 MMT); sign 1/5
- 2006: model 802.0 vs PSD 726.9 MMT (×1.10; Δ — / — pp)
- 2007: model 749.1 vs PSD 781.1 MMT (×0.96; Δ -6.5 / +6.7 pp)
- 2008: model 722.4 vs PSD 794.5 MMT (×0.91; Δ -3.3 / +1.6 pp)
- 2009: model 774.9 vs PSD 831.9 MMT (×0.93; Δ +6.4 / +4.6 pp)
- 2010: model 744.2 vs PSD 867.9 MMT (×0.86; Δ -3.8 / +4.4 pp)
- 2011: model 716.0 vs PSD 886.0 MMT (×0.81; Δ -3.5 / +2.2 pp)
- 2011 named-node snapshot (psd_cons>10 MMT):
  - USA: model 261.4 vs PSD 278.0 MMT (×0.94)
  - China: model 142.8 vs PSD 204.0 MMT (×0.70)
  - RestOfWorld: model 124.8 vs PSD 163.9 MMT (×0.76)
  - EU: model 54.0 vs PSD 69.7 MMT (×0.77)
  - Brazil: model 38.8 vs PSD 51.5 MMT (×0.75)
  - Mexico: model 25.4 vs PSD 29.0 MMT (×0.87)

## AMIS shipment signs (official matched vs harvest-only)
Isolated-τ assert ≠ this table. Fig. 3 is model-implied withheld grain, not FAOSTAT trade. Ratio < 1 means AMIS cut that node.
- Argentina May 2007: offers fall, shipments barely move (demand already the constraint). Isolated τ must not cut the 14-month mean world price.
- Argentina assert_May2007 2007-05→2007-05: offer ×0.30, ship ×0.92 (cut; τ̄=0.70)
- Argentina quota_May07_Jan08 2007-05→2008-01: offer ×0.34, ship ×0.87 (cut; τ̄=0.70)
- USA unrestricted_control 2007-05→2008-06: offer ×1.16, ship ×0.88 (cut; τ̄=0.00)
- Ukraine quota_2010_11 2010-10→2011-06: offer ×0.37, ship ×0.42 (cut; τ̄=0.70)
- Argentina calendar-year exports vs PSD:
  - 2007: full 11.7 vs no-AMIS 13.4 vs PSD 14.8 MMT (model/PSD ×0.79)
  - 2008: full 7.7 vs no-AMIS 8.9 vs PSD 10.3 MMT (model/PSD ×0.75)
  - 2010: full 8.4 vs no-AMIS 11.0 vs PSD 16.3 MMT (model/PSD ×0.51)
  - 2011: full 5.2 vs no-AMIS 8.6 vs PSD 17.1 MMT (model/PSD ×0.30)

## Country MY-end stocks vs PSD (local marketing year, not groupings)
- Median model/PSD stock (psd>1 MMT): ×1.63 (mean ×1.96)
- Median model/PSD consumption: ×0.91
- Δstock sign agreement: 41/80
- 2011 snapshot (psd>2 MMT):
  - China (m=9): model 145.6 vs PSD 55.7 MMT (×2.61)
  - USA (m=8): model 30.3 vs PSD 25.1 MMT (×1.21)
  - RestOfWorld (m=8): model 18.5 vs PSD 21.4 MMT (×0.87)
  - EU (m=9): model 25.9 vs PSD 6.7 MMT (×3.88)
  - Brazil (m=2): model 27.0 vs PSD 4.2 MMT (×6.41)
  - Egypt (m=8): model 1.1 vs PSD 2.2 MMT (×0.48)

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
