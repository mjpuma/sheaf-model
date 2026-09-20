# Author cleaned wheat_food_balance_fao.csv — host reconstruction

**Leave A1. USDA remains the 2006–11 `prepare_wheat` default.**
This file is a labelled reconstruction of AgriculturalData
`impute_food_balance_fao("wheat")` (Zenodo 14022004), not Kuhla's
unpublished local CSV, and **not adopted** as the host. Do not
silently replace C.1. Do not invent an Egypt node. Fig. 4 knobs
stay on `fig4_experiment_params()`. `wheat_params()` stay αI=3.2,
p_sto=0.1, xmin=0.2, ζ=0, N_for=3. L1–L8 stay rejected. Bai
α_foreign=10 not adopted. FBSH 5074 is ΔS, never S.

## What was created

- `data/food_balances/wheat_food_balance_fao.csv` (1193 rows;
  FBS 1049; QCL+TCL imputed 144).
- Columns: ISO3 Code, Area, Area Code, Year, Production,
  Domestic supply quantity, Import Quantity, Export Quantity,
  Stock Variation, Source.
- Years 2006–2011. Unit 1000 t.
- 2007 Production: USA 55820.000;
  China, mainland 109298.000.
- Egypt rows in this table: 6 (ISO3 EGY if mapped;
  **not** added to the 27-node C.1 list).
- inventory()["food_balance_files"]: ['data/food_balances/wheat_food_balance_fao.csv'].
- USDA is default: True; αI=3.2.

## Verification protocol

1. **Claim.** Agrimate E.1 uses cleaned FAOSTAT Food Balances
   (`wheat_food_balance_fao.csv` from `impute_food_balance_fao`).
2. **Implementation.** `prepare_wheat` still groups USDA PSD
   2007–09 and notes "not FAOSTAT Food Balances (E.1.1)."
3. **Match.** File now exists as a **host reconstruction**, not a
   bit-identical author dump. Host quantities are still USDA (A1).
4. **Counterexample.** `prepare_wheat` notes still say USDA PSD,
   not FAOSTAT: True.
   Stock Variation here is sign-flipped FBSH 5074 (ΔS), not
   USDA `ending_stocks`.
5. **Correctness of not switching.** S3 already scored raw FBSH
   H/C vs member-sum USDA: moy worsened 20.1×→33.0×; items 1–3
   did not improve. This reconstruction does not add EU28+Egypt
   or start-2000. Switching would retune 2006–11 quantities.
6. **Change.** Write the labelled CSV. Do not change economics.

## Remaining A7 cannot-set

- AgrimateEU28 + Egypt extra node (host is AgrimateRegionsWheat).
- start 2000-01-01.
- FAO production anomalies since 2005.
- Bit-identical author local `wheat_food_balance_fao.csv`.
- Zenodo 14022004 Julia (not vendored).

Next paste: **S4** (A7 cannot-set inventory). Not G1. Do not
retune αI / p_sto / xmin. Do not adopt this file as prepare_wheat.

