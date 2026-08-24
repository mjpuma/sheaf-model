# Gate 0 report — rice

Window 2006–2011. Ask-dominated bilateral spine (`sheaf.dynamic_crop`). No cross-grain substitution.

Parameters: see `diagnostics/GATE0_PARAMETERIZATION.md`.

## Robustness asserts
- PASS twin identity (no shocks/AMIS ⇒ flat at p0)
- PASS AMIS raises price in primary ban window
- PASS AMIS cuts Vietnam offers/exports in ban window
- PASS no fake spring lean-season spike

## Parameters (`CropParams`)
```
CropParams(crop='rice', elast=-0.2, stu_target=0.2, max_stu=0.28, seasonal_buffer_steps=3.0, rebuild_lambda=0.08, inv_eta=0.95, smooth=0.65, trade_w=0.72, unmet_kappa=2.5, block_kappa=4.5, ask_alpha=0.15, ask_target_fill=0.7, ask_comp_elast=1.25, ask_beta=0.18, foresight_phi=0.55, harvest_pulse_frac=0.12, residual_subst=0.15, twin_harvest='seasonal', shock_mode='full')
```

## Monthly price vs Pink Sheet
- `full` corr = +0.798
- `shocks` corr = -0.076
- `tau` corr = +0.820

## Crisis hike ratios (3-mo mean peak/base)
- **2007/08** obs×1.84  `full`×2.21  `shocks`×1.40  `tau`×1.57
- **2010/11** obs×0.79  `full`×0.85  `shocks`×1.05  `tau`×0.87

## Attribution (which leg carries the hike)
- 2007/08: shocks×1.40 vs tau×1.57 (full×2.21) — restriction-led
- 2010/11: shocks×1.05 vs tau×0.87 (full×0.85) — production/stock-led

## Annual world ending stocks (model year-end vs PSD)
- 2006: model 268.3 MMT vs PSD 76.4 MMT
- 2007: model 291.1 MMT vs PSD 82.3 MMT
- 2008: model 339.7 MMT vs PSD 95.0 MMT
- 2009: model 356.6 MMT vs PSD 97.5 MMT
- 2010: model 359.2 MMT vs PSD 102.8 MMT
- 2011: model 360.0 MMT vs PSD 112.7 MMT

## Artifacts
- `diagnostics/gate0_rice_score.csv`
- `diagnostics/gate0_rice_exporters.csv`
- `diagnostics/gate0_rice_stocks.csv`
- `figures/fig_gate0_rice_diagnostics.png`
