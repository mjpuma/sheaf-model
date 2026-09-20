# S1 — A8 member-sum host adapter (2007–09 USDA)

**Implemented.** `prepare_wheat` uses member-sum within year, then
mean over 2007–09 (same construction as `psd_regional_annual()`).
The pooled country-year `groupby.mean()` is the rejected A8
construction (R7 labelled). `wheat_params()` stay αI=3.2,
p_sto=0.1, xmin=0.2, ζ=0, N_for=3. No xmin/p_sto fit. L1–L8 stay
rejected. Bai α_foreign=10 not adopted. G1/G2 stay blocked.
FAOSTAT FBSH is not adopted.

**Stocks are USDA PSD `ending_stocks`.** FAOSTAT FBSH Stock
Variation (element 5074) is ΔS, a food-balance residual, not a
stock level. R6 copied USDA Psi onto the FBSH parallel for that
reason. This table does not use FAO ΔS.

## Verification protocol

1. **Claim.** A8 S1: 2007–09 baseline is member-sum, not mean;
   China and Eastern Africa host H match PSD sum.
2. **Implementation.** `prepare_wheat` (`wheat_data.py`)
   `psd_member_sum_then_mean()`; `psd_regional_annual()` sums.
3. **Match.** Host H equals the year-sum then 2007–09 mean.
4. **Counterexample (old mean).** China 2007–09 H mean 56.4 vs sum 112.7 (ratio 0.50); EA 0.33 vs 3.31 (ratio 0.10). USA is 1.00.
5. **Correctness of switching.** Summing rescales China H/C/S ×2
   and Eastern Africa ×10. That is the approved data adapter,
   not a parameter fit. Anomalies stay on the summed member
   series. Host C after T* is still rebuilt from inflows.
6. **Change.** Baseline construction only. `wheat_params()`
   unchanged. Do not pin. Do not restore L1–L8.

## 2007–09 USDA PSD (MMT)

Mean = pooled country-year rows (the rejected A8 construction).
Sum = members summed within each year, then averaged over 2007–09
(what `prepare_wheat` and `psd_regional_annual()` now share).

| region | members | H mean | H sum | C mean | C sum | S mean | S sum | mean/sum |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| USA | 1 (United States) | 61.4 | 61.4 | 31.3 | 31.3 | 17.6 | 17.6 | 1.00 |
| EU-27 | 1 (European Union) | 137.5 | 137.5 | 123.3 | 123.3 | 16.5 | 16.5 | 1.00 |
| China | 2 (China|Hong Kong) | 56.4 | 112.7 | 53.6 | 107.1 | 23.3 | 46.6 | 0.50 |
| Eastern Africa | 10 countries | 0.33 | 3.31 | 0.66 | 6.55 | 0.055 | 0.55 | 0.10 |

S1 **sums** members. China H/C/S are now 112.7 / 107.1 / 46.6 (were 56.4 / 53.6 / 23.3). Eastern Africa is now 3.31 / 6.55 / 0.55 (were 0.33 / 0.66 / 0.055). Hong Kong wheat production and stocks
are ~0, so China mean was ½ of China mainland. Eastern Africa was
the mean of 10 mapped PSD rows
(Eritrea|Ethiopia|Kenya|Madagascar|Mauritius|Mozambique|Somalia|Tanzania|Zambia|Zimbabwe).

## Host after T* (S1 member-sum)

`prepare_wheat` H follows the **sum** for these nodes. S_ann is
the member-sum of USDA ending stocks; host S = Ψ C* after T*
rebuilds C. C* is rebuilt from T* inflows, so host C is not the
PSD consumption column.

| region | host H | PSD H sum | host C (T*) | PSD C sum | host S | PSD S sum |
|---|---:|---:|---:|---:|---:|---:|
| China | 112.7 | 112.7 | 113.2 | 107.1 | 46.6 | 46.6 |
| Eastern Africa | 3.31 | 3.31 | 6.83 | 6.55 | 0.55 | 0.55 |
| USA | 61.4 | 61.4 | 36.7 | 31.3 | 17.6 | 17.6 |

Eastern Africa host C was already near the member-sum because
T* inflows filled the node. S1 still ×10 H and S. USA is 1.00
(single PSD row). Anomalies stay on the summed member series.

`wheat_params` αI=3.2, p_sto=0.1, xmin=0.2.

**Next paste: S2.** Re-measure item-3 last/first on this host.
Do not pin. Do not retune αI. Do not start G1.

