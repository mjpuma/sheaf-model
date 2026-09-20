# Gate 0 reproduction dispatch

Living next-paste. Rewrite after every R-session from **that run’s
numbers**. Do not walk R3…R12 in order. Template:
`GATE0_REPRO_PROMPTS.md` (Adaptive rule).

```
Last completed: R6 obtain
Window / scenario: FAOSTAT FBSH wheat 2006–11 extract (not a WheatData switch)
hike_2008 (default → knobs → author): ×2.31 → ×2.22 → ×1.62
moy max/min: 26.8× → 13.3× → 1.51×
undisturbed last/first: default 1.630 → qoth_freeze 1.019 → author 1.004
unconverged / failed: host not re-run
What you could set / could not set: FBSH bulk 200; JSON API 521; author cleaned FB absent; laptop /Users/mjp38/.../data not mounted
Next paste: R6
Why: raw FBSH vendored (2 csv); author wheat_food_balance_fao.csv absent; laptop data mounted=False; USDA still prepare_wheat default; no parallel WheatData this paste
Skip: R11; G1/G2; do not retune αI; do not copy 2015–21 averages; do not switch prepare_wheat
```
