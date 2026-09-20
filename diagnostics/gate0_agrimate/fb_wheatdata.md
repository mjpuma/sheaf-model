# R6 — Parallel FBSH WheatData vs USDA (one harvest+AMIS window)

**Not adopted. Leave A1. USDA remains the 2006–11 default.**
`prepare_wheat` is unchanged. `wheat_params()` stay αI=3.2, p_sto=0.1,
xmin=0.2, ζ=0, N_for=3. L1–L8 stay rejected. Bai α_foreign=10 not
adopted. Unforced price is not pinned. G1/G2 stay blocked.

Raw FAOSTAT **FBSH** wheat 2006–11 (item 2511, 1000 t) maps onto the
27 C.1 nodes. This is **not** author `wheat_food_balance_fao.csv`.
FoodTradeNetwork 2015–21 averages were not copied. FBS 2010+ was
not mixed in.

## Verification protocol

1. **Claim.** Agrimate E.1 uses FAOSTAT Food Balances.
2. **Implementation.** `prepare_wheat` still groups USDA PSD 2007–09.
   `prepare_wheat_fbsh` is a labelled parallel.
3. **Match.** Default path does not; A1 stays. Parallel uses raw FBSH,
   not the AgriculturalData impute/QCL+TCL/rebalance pipeline.
4. **Counterexample.** China H USDA 56.4 vs FBSH 112.3 (ratio 1.99) is A8 mean-of-members, not a mapping
   failure. USA H matches (61.4 vs 61.4).
5. **Correctness of not switching.** Stocks are USDA Psi (FBSH 5074 is
   ΔS). Anomalies are H_y/H_star−1 on a 6-year extract, not author
   FAO-since-2005. Intra-region FB exports are not extra-EU PSD.
   Switching the host would retune 2006–11 quantities.
6. **Change.** None to economics. USDA stays default.

## Mapping (faithful enough to run, labelled)

- Country rows only (`area_code < 5000`). Aggregates (World, EU-27
  row 5707, Europe, …) dropped. EU-27 **member sum** production
  2007–09 equals the EU-27 aggregate row (122.42 MMT).
- Dropped duplicate totals: China 351 (same 2007 production as
  mainland 41), Belgium-Luxembourg 15.
- ISO3 via `data_faostat._mappings` plus TMP→TLS. Laptop
  `/Users/mjp38/GitHub/sheaf-model/data` mounted=False.
- Members **summed** (not A8 `groupby.mean()`).

## 2007–09 baseline (MMT, after T* rebuild)

| Region | H USDA | H FBSH | ratio | C USDA | C FBSH |
|---|---:|---:|---:|---:|---:|
| USA | 61.4 | 61.4 | 1.00 | 36.0 | 35.6 |
| China | 56.4 | 112.3 | 1.99 | 57.3 | 112.6 |
| EU-27 | 137.5 | 122.4 | 0.89 | 124.3 | 84.1 |
| Eastern Africa | 0.33 | 3.29 | 9.91 | 3.6 | 7.5 |
| World 27-node | 542.2 | 658.1 | 1.21 | — | — |

Named single-row exporters (USA, Russia, Ukraine, India, Canada, …)
match ~1.00. Multi-country nodes are larger on FBSH because USDA A8
averages sparse PSD members. Next paste **R7** is that sensitivity
on the USDA host, not a reason to adopt FBSH.

## 2006–08 harvest+AMIS

| | USDA `prepare_wheat` | FBSH parallel |
|---|---:|---:|
| hike_2008 | ×2.31 | ×2.18 |
| moy max/min | 26.8× | 33.0× |
| 2006 mean USD/t | 270.7 | 274.1 |
| unconverged | 611/1944 | 778/1944 |
| failed | 0 | 0 |
| XI* annual | 125.3 | 163.4 |

`wheat_params` αI=3.2, ζ=0, N_for=3. Psi was USDA on both runs.

## Remaining cannot-set (A1 / A7)

- Author cleaned FB / QCL+TCL rebalance
- Ending stocks from FAO (Psi stayed USDA)
- FAO-since-2005 LOWESS anomalies; AgrimateEU28+Egypt
- 2015–21 FoodTradeNetwork averages (not used)

**Next paste: R7.** A8 mean-vs-sum on USDA 2007–09 means (China/EA).
R6 does not unlock G1. Do not retune αI / p_sto / xmin.

