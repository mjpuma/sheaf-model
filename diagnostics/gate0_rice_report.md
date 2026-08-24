# Gate 0 report — rice

Window 2006–2011. Ask-dominated bilateral spine (`sheaf.dynamic_crop`). No cross-grain substitution.

Parameters: see `diagnostics/GATE0_PARAMETERIZATION.md`.

## Robustness asserts
- PASS twin identity (no harvest/demand/AMIS ⇒ flat at p0)
- PASS AMIS raises price in primary ban window (maize: must not cut world price)
- PASS AMIS cuts Vietnam offers/exports in ban window
- PASS no fake spring lean-season spike (climatology path)

## Parameters (`CropParams`)
```
CropParams(crop='rice', elast=-0.2, stu_target=0.18, max_stu=0.22, seasonal_buffer_steps=0.0, pipeline_max_steps=0, rebuild_lambda=0.08, warehouse_lambda=0.08, inv_eta=0.95, smooth=0.65, trade_w=0.72, unmet_kappa=2.5, block_kappa=4.5, ask_alpha=0.15, ask_target_fill=0.7, ask_comp_elast=1.25, ask_beta=0.18, ask_rival=0.8, foresight_phi=0.55, harvest_pulse_frac=0.12, residual_subst=0.15, twin_harvest='seasonal', shock_mode='full', industrial_nodes=(), ind_base_years=(2000, 2004))
```

## Monthly price vs Pink Sheet
- `full` corr = +0.678
- `shocks` corr = -0.115
- `demand` corr = +0.309
- `tau` corr = +0.662

## Crisis hike ratios (3-mo mean peak/base)
- **2007/08** obs×1.84  `full`×1.72  `shocks`×0.93  `demand`×1.21  `tau`×1.75
- **2010/11** obs×0.79  `full`×0.82  `shocks`×1.06  `demand`×1.60  `tau`×0.81

## Attribution (which isolated leg carries the hike)
- 2007/08: shocks×0.93  demand×1.21  tau×1.75 (full×1.72) — restriction-led
- 2010/11: shocks×1.06  demand×1.60  tau×0.81 (full×0.82) — demand-led

## Annual world ending stocks (calendar Dec vs PSD; MY-end month=12)
- 2006: Dec 125.7 MMT (STU 0.30); MY-end 125.7 MMT (STU 0.30) vs PSD 76.4 MMT (STU 0.18)
- 2007: Dec 143.6 MMT (STU 0.34); MY-end 143.6 MMT (STU 0.34) vs PSD 82.3 MMT (STU 0.19)
- 2008: Dec 165.0 MMT (STU 0.38); MY-end 165.0 MMT (STU 0.38) vs PSD 95.0 MMT (STU 0.22)
- 2009: Dec 159.6 MMT (STU 0.37); MY-end 159.6 MMT (STU 0.37) vs PSD 97.5 MMT (STU 0.23)
- 2010: Dec 160.1 MMT (STU 0.36); MY-end 160.1 MMT (STU 0.36) vs PSD 102.8 MMT (STU 0.23)
- 2011: Dec 165.3 MMT (STU 0.37); MY-end 165.3 MMT (STU 0.37) vs PSD 112.7 MMT (STU 0.25)
- Mean model/PSD: Dec ×1.63, MY-end ×1.63 (target ~1; >2 still fat warehouse)

## Artifacts
- `diagnostics/gate0_rice_score.csv`
- `diagnostics/gate0_rice_exporters.csv`
- `diagnostics/gate0_rice_stocks.csv`
- `figures/fig_gate0_rice_diagnostics.png`
