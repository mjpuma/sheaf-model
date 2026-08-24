# Gate 0 report — maize

Window 2006–2011. Ask-dominated bilateral spine (`sheaf.dynamic_crop`). No cross-grain substitution.

Parameters: see `diagnostics/GATE0_PARAMETERIZATION.md`.

## Robustness asserts
- PASS twin identity (no harvest/demand/AMIS ⇒ flat at p0)
- PASS AMIS raises price in primary ban window (maize: must not cut world price)
- PASS AMIS cuts Argentina offers/exports in ban window
- PASS no fake spring lean-season spike (climatology path)

## Parameters (`CropParams`)
```
CropParams(crop='maize', elast=-0.25, stu_target=0.16, max_stu=0.18, seasonal_buffer_steps=0.0, pipeline_max_steps=12, rebuild_lambda=0.08, warehouse_lambda=0.08, inv_eta=0.85, smooth=0.65, trade_w=0.8, unmet_kappa=2.5, block_kappa=4.0, ask_alpha=0.15, ask_target_fill=0.7, ask_comp_elast=1.25, ask_beta=0.18, ask_rival=0.8, foresight_phi=0.5, harvest_pulse_frac=0.12, residual_subst=0.15, twin_harvest='seasonal', shock_mode='full', industrial_nodes=('USA',), ind_base_years=(2000, 2004))
```

## Monthly price vs Pink Sheet
- `full` corr = +0.712
- `shocks` corr = +0.271
- `demand` corr = +0.533
- `tau` corr = +0.237

## Crisis hike ratios (3-mo mean peak/base)
- **2007/08** obs×1.84  `full`×1.97  `shocks`×1.11  `demand`×1.46  `tau`×1.10
- **2010/11** obs×1.44  `full`×1.70  `shocks`×1.01  `demand`×1.12  `tau`×0.92

## Attribution (which isolated leg carries the hike)
- 2007/08: shocks×1.11  demand×1.46  tau×1.10 (full×1.97) — demand-led
- 2010/11: shocks×1.01  demand×1.12  tau×0.92 (full×1.70) — demand-led

## US maize industrial (inelastic FSI excess)
- Cumulative US industrial use over window: 453.5 MMT-steps (RFS residual vs 2000–04 FSI).

## Annual world ending stocks (calendar Dec vs PSD; MY-end month=8)
- 2006: Dec 497.0 MMT (STU 0.75); MY-end 88.1 MMT (STU 0.13) vs PSD 108.8 MMT (STU 0.16)
- 2007: Dec 566.1 MMT (STU 0.79); MY-end 100.4 MMT (STU 0.14) vs PSD 125.4 MMT (STU 0.18)
- 2008: Dec 594.2 MMT (STU 0.81); MY-end 141.1 MMT (STU 0.19) vs PSD 136.0 MMT (STU 0.19)
- 2009: Dec 575.5 MMT (STU 0.75); MY-end 140.5 MMT (STU 0.18) vs PSD 131.5 MMT (STU 0.17)
- 2010: Dec 586.5 MMT (STU 0.73); MY-end 146.0 MMT (STU 0.18) vs PSD 114.9 MMT (STU 0.14)
- 2011: Dec 620.1 MMT (STU 0.76); MY-end 184.0 MMT (STU 0.23) vs PSD 122.8 MMT (STU 0.15)
- Mean model/PSD: Dec ×4.66, MY-end ×1.08 (target ~1; >2 still fat warehouse)

## Artifacts
- `diagnostics/gate0_maize_score.csv`
- `diagnostics/gate0_maize_exporters.csv`
- `diagnostics/gate0_maize_stocks.csv`
- `figures/fig_gate0_maize_diagnostics.png`
