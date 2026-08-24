# Gate 0 report — rice

Window 2006–2011. Ask-dominated bilateral spine (`sheaf.dynamic_crop`). No cross-grain substitution.

## Robustness asserts
- PASS twin identity (no shocks/AMIS ⇒ flat at p0)
- PASS AMIS raises price in primary ban window
- PASS AMIS cuts India offers/exports in ban window
- PASS no fake spring lean-season spike

## Monthly price vs Pink Sheet
- `full` corr = +0.623
- `shocks` corr = -0.044
- `tau` corr = +0.781

## Crisis hike ratios (3-mo mean peak/base)
- **2007/08** obs×1.84  `full`×2.11  `shocks`×1.49  `tau`×1.41
- **2010/11** obs×0.79  `full`×0.75  `shocks`×1.03  `tau`×0.79

## Attribution (which leg carries the hike)
- 2007/08: shocks×1.49 vs tau×1.41 (full×2.11) — production/stock-led
- 2010/11: shocks×1.03 vs tau×0.79 (full×0.75) — production/stock-led

## Annual world ending stocks (model year-end vs PSD)
- 2006: model 260.6 MMT vs PSD 76.4 MMT
- 2007: model 285.8 MMT vs PSD 82.3 MMT
- 2008: model 343.6 MMT vs PSD 95.0 MMT
- 2009: model 368.5 MMT vs PSD 97.5 MMT
- 2010: model 380.8 MMT vs PSD 102.8 MMT
- 2011: model 396.8 MMT vs PSD 112.7 MMT

## Artifacts
- `diagnostics/gate0_rice_score.csv`
- `diagnostics/gate0_rice_exporters.csv`
- `diagnostics/gate0_rice_stocks.csv`
- `figures/fig_gate0_rice_diagnostics.png`
