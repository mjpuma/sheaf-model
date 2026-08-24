# Gate 0 report — wheat

Window 2006–2011. Ask-dominated bilateral spine (`sheaf.dynamic_crop`). No cross-grain substitution.

## Robustness asserts
- PASS twin identity (no shocks/AMIS ⇒ flat at p0)
- PASS AMIS raises price in primary ban window
- PASS AMIS cuts Russia offers/exports in ban window
- PASS no fake spring lean-season spike

## Monthly price vs Pink Sheet
- `full` corr = +0.490
- `shocks` corr = +0.361
- `tau` corr = +0.365

## Crisis hike ratios (3-mo mean peak/base)
- **2007/08** obs×1.82  `full`×2.30  `shocks`×1.88  `tau`×1.01
- **2010/11** obs×1.16  `full`×0.83  `shocks`×0.90  `tau`×1.42

## Attribution (which leg carries the hike)
- 2007/08: shocks×1.88 vs tau×1.01 (full×2.30) — production/stock-led
- 2010/11: shocks×0.90 vs tau×1.42 (full×0.83) — restriction-led

## Annual world ending stocks (model year-end vs PSD)
- 2006: model 241.8 MMT vs PSD 134.8 MMT
- 2007: model 291.2 MMT vs PSD 129.2 MMT
- 2008: model 386.2 MMT vs PSD 170.3 MMT
- 2009: model 427.3 MMT vs PSD 203.8 MMT
- 2010: model 407.5 MMT vs PSD 199.6 MMT
- 2011: model 393.4 MMT vs PSD 200.1 MMT

## Artifacts
- `diagnostics/gate0_wheat_score.csv`
- `diagnostics/gate0_wheat_exporters.csv`
- `diagnostics/gate0_wheat_stocks.csv`
- `figures/fig_gate0_wheat_diagnostics.png`
