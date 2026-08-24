# Gate 0 report — maize

Window 2006–2011. Ask-dominated bilateral spine (`sheaf.dynamic_crop`). No cross-grain substitution.

Parameters: see `diagnostics/GATE0_PARAMETERIZATION.md`.

## Robustness asserts
- PASS twin identity (no harvest/demand/AMIS ⇒ flat at p0)
- SKIP isolated-tau world-price lift for maize (quotas on slack climatology; offer-cut assert binds)
- PASS AMIS cuts Argentina offers/exports in ban window
- PASS no fake spring lean-season spike

## Parameters (`CropParams`)
```
CropParams(crop='maize', elast=-0.25, stu_target=0.18, max_stu=0.25, seasonal_buffer_steps=3.5, rebuild_lambda=0.08, inv_eta=0.85, smooth=0.65, trade_w=0.8, unmet_kappa=2.5, block_kappa=4.0, ask_alpha=0.15, ask_target_fill=0.7, ask_comp_elast=1.25, ask_beta=0.18, foresight_phi=0.5, harvest_pulse_frac=0.12, residual_subst=0.15, twin_harvest='seasonal', shock_mode='full', industrial_nodes=('USA',), ind_base_years=(2000, 2004))
```

## Monthly price vs Pink Sheet
- `full` corr = +0.582
- `shocks` corr = -0.344
- `demand` corr = +0.464
- `tau` corr = -0.445

## Crisis hike ratios (3-mo mean peak/base)
- **2007/08** obs×1.84  `full`×1.80  `shocks`×1.26  `demand`×1.21  `tau`×0.78
- **2010/11** obs×1.44  `full`×1.17  `shocks`×0.90  `demand`×0.87  `tau`×1.04

## Attribution (which isolated leg carries the hike)
- 2007/08: shocks×1.26  demand×1.21  tau×0.78 (full×1.80) — production-led
- 2010/11: shocks×0.90  demand×0.87  tau×1.04 (full×1.17) — restriction-led

## US maize industrial (inelastic FSI excess)
- Cumulative US industrial use over window: 453.5 MMT-steps (RFS residual vs 2000–04 FSI).

## Annual world ending stocks (model year-end vs PSD)
- 2006: model 514.9 MMT vs PSD 108.8 MMT
- 2007: model 547.4 MMT vs PSD 125.4 MMT
- 2008: model 585.7 MMT vs PSD 136.0 MMT
- 2009: model 591.2 MMT vs PSD 131.5 MMT
- 2010: model 592.8 MMT vs PSD 114.9 MMT
- 2011: model 635.3 MMT vs PSD 122.8 MMT

## Artifacts
- `diagnostics/gate0_maize_score.csv`
- `diagnostics/gate0_maize_exporters.csv`
- `diagnostics/gate0_maize_stocks.csv`
- `figures/fig_gate0_maize_diagnostics.png`
