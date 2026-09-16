# Note for the Agrimate team (not sent)

Zenodo 14022004 (author code) retrieved 2026-09-16. Data 10688435 not unpacked.

Closed from the executable model (not guessed):

1. **αI, τ:** author code uses α_foreign=3.2 and τ=0.1 (F.1), not Tbl. D.8 3.5 / 0.2. Host follows code; D.8 retained as `wheat_table_d8_defaults()`.
2. **ζ:** author `ζ=0` turns *on* the x_min quadratic penalty (`ζ=1` disables it). Not a storage-cost coefficient. `p_sto=0.1` per year is the storage cost.
3. **C.1 wheat:** `AgrimateRegionsWheat` is **27** names (Egypt in Northern Africa, Mexico in Central America, Pakistan and Turkey singles, no RoW). Paper text said 28.
4. **E.27:** `duration_in_s=1.2` means `s = duration/1.2`, support `|d−dmid|≤s`. Printed `|d−dmid|≤1.2` was OCR.
5. **D.1:** `w = 1/(1+exp((n−N_for)/(0.17 τ_for)))` with N_for=3 months, τ_for=0.2 yr. Near-term realised.

Still open:

6. **β=0.05 / τ_P=0.2:** local price adjustment; not wired.
7. **D.30a upper-tier purchaser** (ε_d, A_d budget share vs compound good).
8. FAOSTAT Food Balance arrays vs USDA PSD.
9. Confirm whether published Fig. 4 used the 27-region wheat list and F.1 αI=3.2.
