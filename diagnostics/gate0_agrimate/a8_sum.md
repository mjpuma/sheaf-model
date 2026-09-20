# R7 — A8 mean-vs-sum sensitivity (2007–09 USDA only)

**Host unchanged. Not adopted.** `prepare_wheat` still uses
`groupby(region).mean()` on USDA PSD country-year rows.
`wheat_params()` stay αI=3.2, p_sto=0.1, xmin=0.2, ζ=0, N_for=3.
No xmin/p_sto fit. L1–L8 stay rejected. Bai α_foreign=10 not
adopted. G1/G2 stay blocked. 2003–11 three-scenario CSVs are
not rewritten.

**Stocks are USDA PSD `ending_stocks`.** FAOSTAT FBSH Stock
Variation (element 5074) is ΔS, a food-balance residual, not a
stock level. R6 copied USDA Psi onto the FBSH parallel for that
reason. This table does not use FAO ΔS.

## Verification protocol

1. **Claim.** A8: multi-country PSD baseline uses mean, not sum;
   China 0.50× and Eastern Africa 0.10× on harvest.
2. **Implementation.** `prepare_wheat` (`wheat_data.py`) 
   `groupby("region").mean()`; `psd_regional_annual()` sums.
3. **Match.** They match. This note reports C and S on the same
   construction, still USDA.
4. **Counterexample.** China 2007–09 H mean 56.4 vs sum 112.7 (ratio 0.50); EA 0.33 vs 3.31 (ratio 0.10). USA is 1.00.
5. **Correctness of not rewriting.** Summing would rescale China
   H/C/S ×2 and Eastern Africa ×10 and rewrite the 2003–11 host.
   That is a data-adapter change, not a parameter fit. Host C
   after T* is already not the PSD mean (inflows).
6. **Change.** None to economics. Mean stays the default.

## 2007–09 USDA PSD (MMT)

Mean = pooled country-year rows (what `prepare_wheat` uses for
H and for S_ann). Sum = members summed within each year, then
averaged over 2007–09 (what `psd_regional_annual()` uses).

| region | members | H mean | H sum | C mean | C sum | S mean | S sum | mean/sum |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| USA | 1 (United States) | 61.4 | 61.4 | 31.3 | 31.3 | 17.6 | 17.6 | 1.00 |
| EU-27 | 1 (European Union) | 137.5 | 137.5 | 123.3 | 123.3 | 16.5 | 16.5 | 1.00 |
| China | 2 (China|Hong Kong) | 56.4 | 112.7 | 53.6 | 107.1 | 23.3 | 46.6 | 0.50 |
| Eastern Africa | 10 countries | 0.33 | 3.31 | 0.66 | 6.55 | 0.055 | 0.55 | 0.10 |

If members are **summed**, China H/C/S become 112.7 / 107.1 / 46.6 (now 56.4 / 53.6 / 23.3). Eastern Africa becomes 3.31 / 6.55 / 0.55 (now 0.33 / 0.66 / 0.055). Hong Kong wheat production and stocks
are ~0, so China mean is ½ of China mainland. Eastern Africa is
the mean of 10 mapped PSD rows
(Eritrea|Ethiopia|Kenya|Madagascar|Mauritius|Mozambique|Somalia|Tanzania|Zambia|Zimbabwe).

## Host after T* (unchanged)

`prepare_wheat` H follows the **mean** for these nodes. S_ann is
the mean of USDA ending stocks; host S = Ψ C* = S_ann. C* is
rebuilt from T* inflows, so host C is not the PSD mean.

| region | host H | PSD H mean | host C (T*) | PSD C mean | host S | PSD S mean |
|---|---:|---:|---:|---:|---:|---:|
| China | 56.4 | 56.4 | 57.3 | 53.6 | 23.3 | 23.3 |
| Eastern Africa | 0.33 | 0.33 | 3.61 | 0.66 | 0.055 | 0.055 |
| USA | 61.4 | 61.4 | 36.0 | 31.3 | 17.6 | 17.6 |

Eastern Africa host C is already 3.61 vs PSD mean 0.66 because
T* inflows fill the node. Summing members would still ×10 H and
S. That is why this stays a labelled sensitivity, not a silent
host rewrite.

`wheat_params` αI=3.2, p_sto=0.1, xmin=0.2.

**Next paste: R8.** Honest Fig. 4 score tests. R7 does not unlock
G1. Do not rewrite the 2003–11 host. Do not retune αI.

