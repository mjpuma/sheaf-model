# Gate 2 beta

Players Russia, Kazakhstan. Synthetic 2007 Russia harvest ×0.5; Kazakhstan harvest unchanged. AMIS off. Illustrative types: `gov_stu`=0.48, `fs_stock_weight`=12, `tau_on`=0.6, `stock_ratio_trigger`=0.85. s_gov (Russia) = 18.13 MMT.

Gate 0 and Gate 1 were **not** re-run. Clock: `diagnostics/GAME_CLOCK.md`.

### Headey path (headline)

- Russia calm on: **0** / 24; shock on: **12** / 24 (first step 12, min S/S_calm = 0.45)
- Kazakhstan calm on: **0** / 24; shock on: **6** / 24 (first step 13, min S/S_calm = 0.76) — no own harvest cut
- Russia shipments 3.27 → 3.25 MMT
- Kazakhstan shipments 6.66 → 6.28 MMT

Cascade is **harvest diversion** (Kazakhstan’s open-path S/S_calm already below r after Russia’s harvest fails), not sequential ban-on-ban IBR. Ukraine is on the market but does not play.

### Nested year-open-loop BR (diagnostic)

- Calm τ* = **0**
- Shock τ* = **0.6**

- [PASS] nested year: calm τ* = 0
- [PASS] nested year: shock τ* > 0
- [PASS] nested year: shock τ* cuts shipments vs τ=0
- [PASS] Headey: calm all players τ_t = 0
- [PASS] Headey: shock Russia some τ_t > 0
- [PASS] Headey: shock Kazakhstan some τ_t > 0 (no own harvest cut)
- [PASS] Headey: Kazakhstan lags or ties Russia
- [PASS] Headey: Russia cuts shipments vs open

Not scored against 2008/10 AMIS. See `diagnostics/GATE2_PLAN.md`.

| scenario | tau | W | revenue | penalty | mean_stock | min_stock | mean_price | sum_exports |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| calm | 0.0 | 2539.4 | 2539.4 | 0.0 | 22.13 | 4.69 | 213.5 | 11.89 |
| calm | 0.3 | 2343.3 | 2343.3 | 0.0 | 22.17 | 4.75 | 202.3 | 11.74 |
| calm | 0.6 | 2425.3 | 2425.3 | 0.0 | 22.83 | 5.36 | 229.4 | 10.72 |
| calm | 0.9 | 2281.5 | 2281.5 | 0.0 | 24.32 | 6.85 | 264.0 | 8.53 |
| shock | 0.0 | 411.5 | 589.2 | 177.7 | 14.28 | 4.48 | 208.4 | 3.27 |
| shock | 0.3 | 467.4 | 620.7 | 153.2 | 14.55 | 4.72 | 224.5 | 3.20 |
| shock | 0.6 | 531.6 | 650.5 | 118.9 | 14.98 | 5.17 | 243.6 | 3.04 |
| shock | 0.9 | 425.5 | 468.5 | 43.0 | 16.23 | 6.44 | 268.8 | 1.88 |

Table: `diagnostics/gate2_beta_score.csv`.
Figures: `figures/fig_gate2_beta_welfare.png`, `figures/fig_gate2_headey_tau.png`.
