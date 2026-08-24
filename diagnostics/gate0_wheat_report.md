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
CropParams(crop='wheat', elast=-0.15, stu_target=0.2, max_stu=0.25, seasonal_buffer_steps=2.0, rebuild_lambda=0.08, inv_eta=1.0, smooth=0.65, trade_w=0.7, unmet_kappa=2.5, block_kappa=4.0, ask_alpha=0.15, ask_target_fill=0.7, ask_comp_elast=1.25, ask_beta=0.18, foresight_phi=0.55, harvest_pulse_frac=0.12, residual_subst=0.15, twin_harvest='seasonal', shock_mode='full', industrial_nodes=(), ind_base_years=(2000, 2004))
```

## Monthly price vs Pink Sheet
- `full` corr = +0.735
- `shocks` corr = +0.137
- `demand` corr = -0.038
- `tau` corr = +0.508

## Crisis hike ratios (3-mo mean peak/base)
- **2007/08** obs×1.82  `full`×1.36  `shocks`×1.16  `demand`×0.91  `tau`×1.12
- **2010/11** obs×1.16  `full`×1.22  `shocks`×1.09  `demand`×1.44  `tau`×1.09

## Attribution (which isolated leg carries the hike)
- 2007/08: shocks×1.16  demand×0.91  tau×1.12 (full×1.36) — production-led
- 2010/11: shocks×1.09  demand×1.44  tau×1.09 (full×1.22) — demand/ethanol-led

## Annual world ending stocks (model year-end vs PSD)
- 2006: model 228.8 MMT vs PSD 134.8 MMT
- 2007: model 248.7 MMT vs PSD 129.2 MMT
- 2008: model 278.1 MMT vs PSD 170.3 MMT
- 2009: model 282.3 MMT vs PSD 203.8 MMT
- 2010: model 263.2 MMT vs PSD 199.6 MMT
- 2011: model 271.4 MMT vs PSD 200.1 MMT

## Artifacts
- `diagnostics/gate0_wheat_score.csv`
- `diagnostics/gate0_wheat_exporters.csv`
- `diagnostics/gate0_wheat_stocks.csv`
- `figures/fig_gate0_wheat_diagnostics.png`
