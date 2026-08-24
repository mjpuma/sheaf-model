# Gate 0 report — maize

Window 2006–2011. Ask-dominated bilateral spine (`sheaf.dynamic_crop`). No cross-grain substitution.

Parameters: see `diagnostics/GATE0_PARAMETERIZATION.md`.

## Robustness asserts
- PASS twin identity (no harvest/demand/AMIS ⇒ flat at p0)
- SKIP isolated-tau world-price lift for maize (other exporters fill; offer-cut assert binds)
- PASS AMIS cuts Argentina offers/exports in ban window
- PASS no fake spring lean-season spike (climatology path)

## Parameters (`CropParams`)
```
CropParams(crop='maize', elast=-0.25, stu_target=0.16, max_stu=0.18, seasonal_buffer_steps=0.0, pipeline_max_steps=12, rebuild_lambda=0.08, inv_eta=0.85, smooth=0.65, trade_w=0.8, unmet_kappa=2.5, block_kappa=4.0, ask_alpha=0.15, ask_target_fill=0.7, ask_comp_elast=1.25, ask_beta=0.18, foresight_phi=0.5, harvest_pulse_frac=0.12, residual_subst=0.15, twin_harvest='seasonal', shock_mode='full', industrial_nodes=('USA',), ind_base_years=(2000, 2004))
```

## Monthly price vs Pink Sheet
- `full` corr = +0.451
- `shocks` corr = -0.220
- `demand` corr = +0.377
- `tau` corr = -0.187

## Crisis hike ratios (3-mo mean peak/base)
- **2007/08** obs×1.84  `full`×1.75  `shocks`×1.05  `demand`×1.41  `tau`×0.84
- **2010/11** obs×1.44  `full`×1.81  `shocks`×0.91  `demand`×2.37  `tau`×0.92

## Attribution (which isolated leg carries the hike)
- 2007/08: shocks×1.05  demand×1.41  tau×0.84 (full×1.75) — demand-led
- 2010/11: shocks×0.91  demand×2.37  tau×0.92 (full×1.81) — demand-led

## US maize industrial (inelastic FSI excess)
- Cumulative US industrial use over window: 453.5 MMT-steps (RFS residual vs 2000–04 FSI).

## Annual world ending stocks (calendar Dec vs PSD; MY-end month=8)
- 2006: Dec 431.4 MMT (STU 0.65); MY-end 51.4 MMT (STU 0.08) vs PSD 108.8 MMT (STU 0.16)
- 2007: Dec 441.1 MMT (STU 0.62); MY-end 55.0 MMT (STU 0.08) vs PSD 125.4 MMT (STU 0.18)
- 2008: Dec 460.5 MMT (STU 0.63); MY-end 59.3 MMT (STU 0.08) vs PSD 136.0 MMT (STU 0.19)
- 2009: Dec 461.6 MMT (STU 0.60); MY-end 63.4 MMT (STU 0.08) vs PSD 131.5 MMT (STU 0.17)
- 2010: Dec 467.4 MMT (STU 0.58); MY-end 75.1 MMT (STU 0.09) vs PSD 114.9 MMT (STU 0.14)
- 2011: Dec 463.4 MMT (STU 0.57); MY-end 75.6 MMT (STU 0.09) vs PSD 122.8 MMT (STU 0.15)
- Mean model/PSD: Dec ×3.70, MY-end ×0.52 (target ~1; >2 still fat warehouse)

## Artifacts
- `diagnostics/gate0_maize_score.csv`
- `diagnostics/gate0_maize_exporters.csv`
- `diagnostics/gate0_maize_stocks.csv`
- `figures/fig_gate0_maize_diagnostics.png`
