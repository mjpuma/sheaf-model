# Gate 2 beta

Exporter Russia wheat. Synthetic 2007 harvest ×0.5. AMIS off. Illustrative `gov_stu`=0.48, `fs_stock_weight`=12. Government buffer s_gov = 18.13 MMT.

- Calm τ* = **0**
- Shock τ* = **0.6**

- [PASS] calm τ* = 0
- [PASS] shock τ* > 0
- [PASS] shock τ* cuts shipments vs τ=0

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
Figure: `figures/fig_gate2_beta_welfare.png`.
