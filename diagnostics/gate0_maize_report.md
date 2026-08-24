# Gate 0 report — maize

Window 2006–2011. Ask-dominated bilateral spine (`sheaf.dynamic_crop`). No cross-grain substitution.

## Robustness asserts
- PASS twin identity (no shocks/AMIS ⇒ flat at p0)
- PASS AMIS raises price in primary ban window
- PASS AMIS cuts Argentina offers/exports in ban window
- PASS no fake spring lean-season spike

## Monthly price vs Pink Sheet
- `full` corr = -0.092
- `shocks` corr = -0.177
- `tau` corr = +0.706

## Crisis hike ratios (3-mo mean peak/base)
- **2007/08** obs×1.84  `full`×1.42  `shocks`×1.24  `tau`×1.11
- **2010/11** obs×1.44  `full`×1.22  `shocks`×1.22  `tau`×1.72

## Attribution (which leg carries the hike)
- 2007/08: shocks×1.24 vs tau×1.11 (full×1.42) — production/stock-led
- 2010/11: shocks×1.22 vs tau×1.72 (full×1.22) — restriction-led

## Annual world ending stocks (model year-end vs PSD)
- 2006: model 471.8 MMT vs PSD 108.8 MMT
- 2007: model 602.8 MMT vs PSD 125.4 MMT
- 2008: model 622.0 MMT vs PSD 136.0 MMT
- 2009: model 580.6 MMT vs PSD 131.5 MMT
- 2010: model 566.6 MMT vs PSD 114.9 MMT
- 2011: model 584.7 MMT vs PSD 122.8 MMT

## Artifacts
- `diagnostics/gate0_maize_score.csv`
- `diagnostics/gate0_maize_exporters.csv`
- `diagnostics/gate0_maize_stocks.csv`
- `figures/fig_gate0_maize_diagnostics.png`
