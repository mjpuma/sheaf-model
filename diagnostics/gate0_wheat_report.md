# Gate 0 report — wheat

Window 2006–2011. Ask-dominated bilateral spine (`sheaf.dynamic_crop`). No cross-grain substitution.

Parameters: see `diagnostics/GATE0_PARAMETERIZATION.md`.

## Robustness asserts
- PASS twin identity (no shocks/AMIS ⇒ flat at p0)
- PASS AMIS raises price in primary ban window
- PASS AMIS cuts Russia offers/exports in ban window
- PASS no fake spring lean-season spike

## Parameters (`CropParams`)
```
CropParams(crop='wheat', elast=-0.15, stu_target=0.2, max_stu=0.25, seasonal_buffer_steps=2.0, rebuild_lambda=0.08, inv_eta=1.0, smooth=0.65, trade_w=0.7, unmet_kappa=2.5, block_kappa=4.0, ask_alpha=0.15, ask_target_fill=0.7, ask_comp_elast=1.25, ask_beta=0.18, foresight_phi=0.55, harvest_pulse_frac=0.12, residual_subst=0.15, twin_harvest='seasonal', shock_mode='full')
```

## Monthly price vs Pink Sheet
- `full` corr = +0.680
- `shocks` corr = +0.319
- `tau` corr = +0.452

## Crisis hike ratios (3-mo mean peak/base)
- **2007/08** obs×1.82  `full`×1.38  `shocks`×1.14  `tau`×1.09
- **2010/11** obs×1.16  `full`×1.08  `shocks`×1.21  `tau`×1.12

## Attribution (which leg carries the hike)
- 2007/08: shocks×1.14 vs tau×1.09 (full×1.38) — production/stock-led
- 2010/11: shocks×1.21 vs tau×1.12 (full×1.08) — production/stock-led

## Annual world ending stocks (model year-end vs PSD)
- 2006: model 234.5 MMT vs PSD 134.8 MMT
- 2007: model 256.9 MMT vs PSD 129.2 MMT
- 2008: model 281.0 MMT vs PSD 170.3 MMT
- 2009: model 283.2 MMT vs PSD 203.8 MMT
- 2010: model 261.8 MMT vs PSD 199.6 MMT
- 2011: model 268.8 MMT vs PSD 200.1 MMT

## Artifacts
- `diagnostics/gate0_wheat_score.csv`
- `diagnostics/gate0_wheat_exporters.csv`
- `diagnostics/gate0_wheat_stocks.csv`
- `figures/fig_gate0_wheat_diagnostics.png`
