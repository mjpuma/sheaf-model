# Fig. 4-config comparison (R2)

Labelled comparison. **Not a retune.** `wheat_params()` stay
αI=3.2, ζ=0, N_for=3. Fig. 4 knobs live on
`fig4_experiment_params()` (αI=3.5, ζ=1, N_for=6).
L1–L8 stay rejected. Bai α_foreign=10 is not adopted.
Unforced price is not pinned. G1/G2 stay blocked.
USDA 27-node WheatData is unchanged (A1).

Window **2006–2008** harvest+AMIS and undisturbed.
Does **not** overwrite 2003–11 three-scenario CSVs.

## What this object can set

alpha_i=3.5, alpha_nash=3.0, zeta_penalty=1.0, n_for_months=6.

## What this object cannot set

- FAOSTAT Food Balances (A1)
- AgrimateEU28 + Egypt extra (host is AgrimateRegionsWheat: EU-27, Brazil named, Egypt in Northern Africa)
- start 2000-01-01
- FAO production anomalies since 2005
- git old-demand-dynamics
- Zenodo 14022004 author Julia

Optional region/data path: `None` (host Egypt node=False, EU-28=False; FAO FB files=none).

## 2006–08 scores

| label | scenario | hike_2008 | moy max/min | last/first | unconverged | failed | 2006 mean USD |
|---|---|---:|---:|---:|---:|---:|---:|
| default | harvest_amis | ×2.31 | 26.8× | 0.696 | 611/1944 | 0 | 270.7 |
| default | undisturbed | ×2.29 | 29.5× | 0.618 | 583/1944 | 0 | 204.0 |
| fig4_knobs | harvest_amis | ×2.22 | 13.3× | 0.789 | 553/1944 | 0 | 358.1 |
| fig4_knobs | undisturbed | ×2.14 | 27.2× | 0.409 | 432/1944 | 0 | 244.3 |

Author harvest+AMIS on this window: hike ×1.62, moy 1.51×. Author undisturbed last/first 2006–2008 = 1.006.

Default vs Fig. 4 knobs (harvest+AMIS): hike ×2.31 → ×2.22 (author ×1.62); moy 26.8× → 13.3× (author 1.51×). toward_hike=False; moy_drop_ge2=True; barely_moved=False.

Undisturbed last/first on this short window: default 0.618 → knobs 0.409 (author 1.006). This is **not** the 2006–11 1.630 figure; do not pin.

Unconverged harvest+AMIS: default 611/1944 (failed=0); knobs 553/1944 (failed=0).

**Next paste: R10.** moy 26.8×→13.3× (drop ≥2); hike barely moved (×2.31→×2.22); score vs author series before treating it as a win.

Do not adopt `fig4_experiment_params()` as `wheat_params()`.
Do not start G1.
