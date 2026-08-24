# Gate 0 report — wheat

Window 2006–2011. Ask-dominated bilateral spine (`sheaf.dynamic_crop`). No cross-grain substitution.

Parameters: see `diagnostics/GATE0_PARAMETERIZATION.md`.

## Robustness asserts
- PASS twin identity (no harvest/demand/AMIS ⇒ flat at p0)
- PASS AMIS raises price in primary ban window (maize: must not cut world price)
- PASS AMIS cuts Russia offers/exports in ban window
- PASS no fake spring lean-season spike (climatology path)

## Parameters (`CropParams`)
```
CropParams(crop='wheat', elast=-0.15, stu_target=0.2, max_stu=0.28, seasonal_buffer_steps=0.0, pipeline_max_steps=12, rebuild_lambda=0.08, warehouse_lambda=0.08, inv_eta=1.0, smooth=0.65, trade_w=0.7, unmet_kappa=2.5, block_kappa=4.0, ask_alpha=0.15, ask_target_fill=0.7, ask_comp_elast=1.25, ask_beta=0.18, ask_rival=0.8, foresight_phi=0.55, harvest_pulse_frac=0.12, residual_subst=0.15, twin_harvest='seasonal', shock_mode='full', industrial_nodes=(), ind_base_years=(2000, 2004))
```

## Monthly price vs Pink Sheet
- `full` corr = +0.720
- `shocks` corr = +0.400
- `demand` corr = +0.015
- `tau` corr = +0.550

## Crisis hike ratios (3-mo mean peak/base)
- **2007/08** obs×1.82  `full`×2.27  `shocks`×1.20  `demand`×0.98  `tau`×1.70
- **2010/11** obs×1.16  `full`×1.45  `shocks`×1.85  `demand`×1.35  `tau`×1.36

## Attribution (which isolated leg carries the hike)
- 2007/08: shocks×1.20  demand×0.98  tau×1.70 (full×2.27) — restriction-led
- 2010/11: shocks×1.85  demand×1.35  tau×1.36 (full×1.45) — production-led

## Annual world ending stocks (calendar Dec vs PSD; MY-end month=5)
- 2006: Dec 241.3 MMT (STU 0.49); MY-end 126.5 MMT (STU 0.26) vs PSD 134.8 MMT (STU 0.27)
- 2007: Dec 278.9 MMT (STU 0.56); MY-end 140.2 MMT (STU 0.28) vs PSD 129.2 MMT (STU 0.26)
- 2008: Dec 341.9 MMT (STU 0.67); MY-end 169.5 MMT (STU 0.33) vs PSD 170.3 MMT (STU 0.33)
- 2009: Dec 351.4 MMT (STU 0.67); MY-end 213.4 MMT (STU 0.41) vs PSD 203.8 MMT (STU 0.39)
- 2010: Dec 322.1 MMT (STU 0.61); MY-end 206.6 MMT (STU 0.39) vs PSD 199.6 MMT (STU 0.38)
- 2011: Dec 351.1 MMT (STU 0.62); MY-end 206.5 MMT (STU 0.37) vs PSD 200.1 MMT (STU 0.35)
- Mean model/PSD: Dec ×1.84, MY-end ×1.02 (target ~1; >2 still fat warehouse)

## Artifacts
- `diagnostics/gate0_wheat_score.csv`
- `diagnostics/gate0_wheat_exporters.csv`
- `diagnostics/gate0_wheat_stocks.csv`
- `figures/fig_gate0_wheat_diagnostics.png`
