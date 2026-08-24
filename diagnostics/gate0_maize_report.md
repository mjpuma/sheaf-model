# Gate 0 report — maize

Window 2006–2011. Ask-dominated bilateral spine (`sheaf.dynamic_crop`). No cross-grain substitution.

Parameters: see `diagnostics/GATE0_PARAMETERIZATION.md`.

## Robustness asserts
- PASS twin identity (no shocks/AMIS ⇒ flat at p0)
- PASS AMIS raises price in primary ban window
- PASS AMIS cuts Argentina offers/exports in ban window
- PASS no fake spring lean-season spike

## Parameters (`CropParams`)
```
CropParams(crop='maize', elast=-0.25, stu_target=0.16, max_stu=0.25, seasonal_buffer_steps=2.0, rebuild_lambda=0.08, inv_eta=1.0, smooth=0.65, trade_w=0.65, unmet_kappa=3.0, block_kappa=5.5, ask_alpha=0.15, ask_target_fill=0.7, ask_comp_elast=1.25, ask_beta=0.18, foresight_phi=0.4, harvest_pulse_frac=0.12, residual_subst=0.15, twin_harvest='seasonal', shock_mode='shortfalls_only')
```

## Monthly price vs Pink Sheet
- `full` corr = +0.359
- `shocks` corr = +0.115
- `tau` corr = +0.670

## Crisis hike ratios (3-mo mean peak/base)
- **2007/08** obs×1.84  `full`×1.97  `shocks`×1.76  `tau`×1.05
- **2010/11** obs×1.44  `full`×1.06  `shocks`×1.16  `tau`×1.13

## Attribution (which leg carries the hike)
- 2007/08: shocks×1.76 vs tau×1.05 (full×1.97) — production/stock-led
- 2010/11: shocks×1.16 vs tau×1.13 (full×1.06) — production/stock-led

## Annual world ending stocks (model year-end vs PSD)
- 2006: model 421.5 MMT vs PSD 108.8 MMT
- 2007: model 422.2 MMT vs PSD 125.4 MMT
- 2008: model 444.2 MMT vs PSD 136.0 MMT
- 2009: model 429.7 MMT vs PSD 131.5 MMT
- 2010: model 427.3 MMT vs PSD 114.9 MMT
- 2011: model 406.3 MMT vs PSD 122.8 MMT

## Artifacts
- `diagnostics/gate0_maize_score.csv`
- `diagnostics/gate0_maize_exporters.csv`
- `diagnostics/gate0_maize_stocks.csv`
- `figures/fig_gate0_maize_diagnostics.png`
