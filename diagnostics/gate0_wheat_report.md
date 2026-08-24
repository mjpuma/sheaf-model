# Gate 0 report — wheat

Window 2006–2011. Ask-dominated bilateral spine (`sheaf.dynamic_crop`). No cross-grain substitution.

Parameters: see `diagnostics/GATE0_PARAMETERIZATION.md`.

## Robustness asserts
- PASS twin identity (no harvest/demand/AMIS ⇒ flat at p0)
- PASS AMIS raises price in primary ban window
- PASS AMIS cuts Russia offers/exports in ban window
- PASS no fake spring lean-season spike (climatology path)

## Parameters (`CropParams`)
```
CropParams(crop='wheat', elast=-0.15, stu_target=0.2, max_stu=0.28, seasonal_buffer_steps=0.0, pipeline_max_steps=12, rebuild_lambda=0.08, inv_eta=1.0, smooth=0.65, trade_w=0.7, unmet_kappa=2.5, block_kappa=4.0, ask_alpha=0.15, ask_target_fill=0.7, ask_comp_elast=1.25, ask_beta=0.18, foresight_phi=0.55, harvest_pulse_frac=0.12, residual_subst=0.15, twin_harvest='seasonal', shock_mode='full', industrial_nodes=(), ind_base_years=(2000, 2004))
```

## Monthly price vs Pink Sheet
- `full` corr = +0.485
- `shocks` corr = -0.023
- `demand` corr = +0.177
- `tau` corr = +0.415

## Crisis hike ratios (3-mo mean peak/base)
- **2007/08** obs×1.82  `full`×1.44  `shocks`×1.16  `demand`×1.17  `tau`×1.24
- **2010/11** obs×1.16  `full`×1.04  `shocks`×0.92  `demand`×1.84  `tau`×0.87

## Attribution (which isolated leg carries the hike)
- 2007/08: shocks×1.16  demand×1.17  tau×1.24 (full×1.44) — restriction-led
- 2010/11: shocks×0.92  demand×1.84  tau×0.87 (full×1.04) — demand-led

## Annual world ending stocks (calendar Dec vs PSD; MY-end month=5)
- 2006: Dec 193.3 MMT (STU 0.39); MY-end 87.9 MMT (STU 0.18) vs PSD 134.8 MMT (STU 0.27)
- 2007: Dec 223.6 MMT (STU 0.45); MY-end 114.1 MMT (STU 0.23) vs PSD 129.2 MMT (STU 0.26)
- 2008: Dec 228.0 MMT (STU 0.45); MY-end 128.0 MMT (STU 0.25) vs PSD 170.3 MMT (STU 0.33)
- 2009: Dec 232.1 MMT (STU 0.44); MY-end 137.6 MMT (STU 0.26) vs PSD 203.8 MMT (STU 0.39)
- 2010: Dec 236.4 MMT (STU 0.44); MY-end 128.2 MMT (STU 0.24) vs PSD 199.6 MMT (STU 0.38)
- 2011: Dec 212.5 MMT (STU 0.38); MY-end 139.1 MMT (STU 0.25) vs PSD 200.1 MMT (STU 0.35)
- Mean model/PSD: Dec ×1.31, MY-end ×0.72 (target ~1; >2 still fat warehouse)

## Artifacts
- `diagnostics/gate0_wheat_score.csv`
- `diagnostics/gate0_wheat_exporters.csv`
- `diagnostics/gate0_wheat_stocks.csv`
- `figures/fig_gate0_wheat_diagnostics.png`
