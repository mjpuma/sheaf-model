# S3 — FBSH H/C vs S1 member-sum USDA (one harvest+AMIS window)

**Not adopted. Leave A1. USDA remains the 2006–11 `prepare_wheat`
default.** `wheat_params()` stay αI=3.2, p_sto=0.1, xmin=0.2,
ζ=0, N_for=3. L1–L8 stay rejected.
Bai α_foreign=10 not adopted. Unforced price is not pinned. G1/G2
stay blocked. Historical R6 note (`fb_wheatdata.md`) is frozen.

Raw FAOSTAT **FBSH** wheat 2006–11 (item 2511, 1000 t) vs USDA
member-sum (S1). This is **not** author `wheat_food_balance_fao.csv`.
FoodTradeNetwork 2015–21 averages were not copied. FBS 2010+ was
not mixed in. FBSH Stock Variation (element **5074**) is not S.

## Verification protocol (CLAUDE.md)

1. **Claim.** Agrimate E.1 uses FAOSTAT Food Balances. S3 may switch
`prepare_wheat` to the FBSH parallel only if DEVELOPMENT items 1–3
improve **and** moy does not worsen versus the S1 USDA host.

2. **Implementation.** `prepare_wheat` is USDA PSD member-sum then
mean (`ending_stocks` is S). `prepare_wheat_fbsh` is a labelled
parallel: FBSH H/C/X, Psi copied from USDA, 5074 unused as a stock
level.

3. **Match.** Default path is still USDA (A1). After S1, China and
Eastern Africa H sit next to FBSH (not 0.50× / 0.10×). Author
cleaned FB is still absent.

4. **Counterexample.** China H USDA 112.7 vs FBSH 112.3 (ratio 1.00). USA 61.4 vs 61.4. 2006–08 harvest+AMIS moy USDA 20.1× vs
FBSH 33.0×; hike ×2.28
vs ×2.18 (S1 2003–11 host ×3.71;
author ×1.62). Item 3 last/first is still
1.444 on the USDA host.

5. **Correctness of not switching.** item 3 undisturbed last/first still 1.444 on the USDA host (author 1.004); FBSH not scored undisturbed; author wheat_food_balance_fao.csv still absent (A7/A1 cannot-set); Psi still USDA ending_stocks (FBSH 5074 is ΔS, not S); moy worsened 20.1× → 33.0× on this 2006–08 window (S1 host 2003–11 moy 16.8×). Switching would retune 2006–11 quantities
without a sourced cleaned FB or an item-3 gain.

6. **Change.** None to economics. USDA stays default. Do not retune
αI / p_sto / xmin. Do not treat 5074 as stocks.

## 2007–09 baseline (MMT, after T* rebuild)

| Region | H USDA | H FBSH | ratio | C USDA | C FBSH |
|---|---:|---:|---:|---:|---:|
| USA | 61.4 | 61.4 | 1.00 | 36.7 | 35.6 |
| China | 112.7 | 112.3 | 1.00 | 113.2 | 112.6 |
| EU-27 | 137.5 | 122.4 | 0.89 | 125.7 | 84.1 |
| Eastern Africa | 3.31 | 3.29 | 0.99 | 6.8 | 7.5 |
| World 27-node | 662.0 | 658.1 | 0.99 | — | — |

China H is comparable after S1 (R6 was 56.4 vs 112.3). Remaining
H/C gaps are EU-27 consumption (USDA ~126 vs FBSH ~84) and other
multi-country C. World 27-node H now matches (~0.99). Psi identical
(USDA) on both objects.
Laptop `/Users/mjp38/GitHub/sheaf-model/data` mounted=False. Author cleaned FB files: none.

## 2006–08 harvest+AMIS (this window, not the 2003–11 host)

| | USDA member-sum | FBSH parallel | S1 2003–11 host | author |
|---|---:|---:|---:|---:|
| hike_2008 | ×2.28 | ×2.18 | ×3.71 | ×1.62 |
| moy max/min | 20.1× | 33.0× | 16.8× | 1.45× |
| 2006 mean USD/t | 257.5 | 274.1 | — | — |
| unconverged | 823/1944 | 778/1944 | 2304 | — |
| failed | 0 | 0 | 0 | — |
| XI* annual | 132.3 | 163.4 | — | — |

`wheat_params` αI=3.2, ζ=0, N_for=3. Psi was USDA on both runs.
The 2006–08 last/first columns are **not** item 3 (item 3 is
undisturbed 2006–11 = 1.444).

## Remaining cannot-set (A1 / A7)

- Author cleaned FB / QCL+TCL rebalance
- Ending stocks from FAO (Psi stayed USDA; 5074 is ΔS)
- FAO-since-2005 LOWESS anomalies; AgrimateEU28+Egypt
- 2015–21 FoodTradeNetwork averages (not used)

**Adoption:** not adopted. item 3 undisturbed last/first still 1.444 on the USDA host (author 1.004); FBSH not scored undisturbed; author wheat_food_balance_fao.csv still absent (A7/A1 cannot-set); Psi still USDA ending_stocks (FBSH 5074 is ΔS, not S); moy worsened 20.1× → 33.0× on this 2006–08 window (S1 host 2003–11 moy 16.8×).

**Next paste: S4.** A7 cannot-set inventory (EU28+Egypt / start-2000
/ cleaned FB). Do not start G1. Do not retune αI / p_sto / xmin.

