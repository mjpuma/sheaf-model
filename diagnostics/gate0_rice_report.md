# Gate 0 report — rice

Window 2006–2011. Ask-dominated bilateral spine (`sheaf.dynamic_crop`). No cross-grain substitution.

Parameters: see `diagnostics/GATE0_PARAMETERIZATION.md`.

## Robustness asserts
- PASS twin identity (no harvest/demand/AMIS ⇒ flat at p0)
- PASS AMIS raises price in primary ban window
- PASS AMIS cuts Vietnam offers/exports in ban window
- PASS no fake spring lean-season spike

## Parameters (`CropParams`)
```
CropParams(crop='rice', elast=-0.2, stu_target=0.2, max_stu=0.28, seasonal_buffer_steps=3.0, rebuild_lambda=0.08, inv_eta=0.95, smooth=0.65, trade_w=0.72, unmet_kappa=2.5, block_kappa=4.5, ask_alpha=0.15, ask_target_fill=0.7, ask_comp_elast=1.25, ask_beta=0.18, foresight_phi=0.55, harvest_pulse_frac=0.12, residual_subst=0.15, twin_harvest='seasonal', shock_mode='full', industrial_nodes=(), ind_base_years=(2000, 2004))
```

## Monthly price vs Pink Sheet
- `full` corr = +0.809
- `shocks` corr = -0.334
- `demand` corr = +0.294
- `tau` corr = +0.779

## Crisis hike ratios (3-mo mean peak/base)
- **2007/08** obs×1.84  `full`×2.05  `shocks`×1.24  `demand`×1.30  `tau`×1.56
- **2010/11** obs×0.79  `full`×0.85  `shocks`×0.99  `demand`×1.34  `tau`×0.79

## Attribution (which isolated leg carries the hike)
- 2007/08: shocks×1.24  demand×1.30  tau×1.56 (full×2.05) — restriction-led
- 2010/11: shocks×0.99  demand×1.34  tau×0.79 (full×0.85) — demand/ethanol-led

## Annual world ending stocks (model year-end vs PSD)
- 2006: model 263.9 MMT vs PSD 76.4 MMT
- 2007: model 278.5 MMT vs PSD 82.3 MMT
- 2008: model 324.5 MMT vs PSD 95.0 MMT
- 2009: model 351.6 MMT vs PSD 97.5 MMT
- 2010: model 357.9 MMT vs PSD 102.8 MMT
- 2011: model 359.8 MMT vs PSD 112.7 MMT

## Artifacts
- `diagnostics/gate0_rice_score.csv`
- `diagnostics/gate0_rice_exporters.csv`
- `diagnostics/gate0_rice_stocks.csv`
- `figures/fig_gate0_rice_diagnostics.png`
