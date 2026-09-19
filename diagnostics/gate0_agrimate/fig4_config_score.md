# Fig. 4 knobs vs author series (R10)

Scores the **R2 comparison run** (2006–08, USDA 27-node WheatData,
`fig4_experiment_params()`) against `author_fig4/`. Does **not**
re-run the 2003–11 three-scenario host. **Not a retune.**
`wheat_params()` stay αI=3.2, ζ=0,
N_for=3. Bai α_foreign=10 is not adopted.
L1–L8 stay rejected. Unforced price is not pinned. G1/G2 stay blocked.

Window is **2006–2008 with no 2003 spin-up**. P7/P8 2006–11 numbers
(harvest+AMIS 2006 index 0.306, hike ×4.54, moy 17.8×, undisturbed
last/first 1.63) are a different path. Do not mix them.

## What was scored (settable knobs)

alpha_i=3.5, alpha_nash=3.0, zeta_penalty=1.0, n_for_months=6.

## Remaining A7 (cannot set)

- FAOSTAT Food Balances (A1)
- AgrimateEU28 + Egypt extra (host is AgrimateRegionsWheat: EU-27, Brazil named, Egypt in Northern Africa)
- start 2000-01-01
- FAO production anomalies since 2005
- git old-demand-dynamics
- Zenodo 14022004 author Julia

Optional region/data path: `None` (Egypt node=False, EU-28=False; FAO FB files=none).

## 2006–08 vs author_fig4

Host index = 2006 mean USD / p0 (p0 = 2006 Pink mean, unit scale).
Author index is `wm_price_index` on the same months. Not a 2006 pin.

| label | scenario | 2006 index | 2006 author | hike | hike author | moy | moy author | last/first | last/first author |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| default | harvest_amis | 1.267 | 1.183 | ×2.31 | ×1.62 | 26.8× | 1.51× | 0.696 | 1.197 |
| default | undisturbed | 0.955 | 1.113 | ×2.29 | ×1.12 | 29.5× | 1.31× | 0.618 | 1.006 |
| fig4_knobs | harvest_amis | 1.677 | 1.183 | ×2.22 | ×1.62 | 13.3× | 1.51× | 0.789 | 1.197 |
| fig4_knobs | undisturbed | 1.144 | 1.113 | ×2.14 | ×1.12 | 27.2× | 1.31× | 0.409 | 1.006 |

Harvest+AMIS (knobs we could set vs author vs same-window default):
- 2008 hike ×2.22 vs author ×1.62 (default ×2.31).
- Quiet-year index 1.677 vs author 1.183 (default 1.267). Knobs moved **away** from
  the author quiet year.
- moy max/min 13.3× vs author 1.51× (default 26.8×). Toward author; still ~9× too large.
- Undisturbed last/first 0.409 vs author 1.006 (default 0.618). Worse, not repeating.

Pink Sheet 2006 mean is $213.5/t (side column).
Knobs 2006 USD $358.1/t (1.68× Pink) vs default $270.7/t. Pink corr is **not** an
adoption criterion. Knobs that move Pink are not adopted.

**match=False.** hike_still_above_author=True; moy_still_above_author=True; quiet_year_not_closer=True; adopted=False.

Do not put αI=3.5 / ζ=1 / N_for=6 into `wheat_params()`.
Do not restore L1–L8. Do not start G1.

**Next paste: R9.** N5 on this comparison object (unconverged
553/1944 harvest+AMIS).
Remaining A7 (FAO/EU28/start-2000/FAO anomalies/old-demand-dynamics)
still blocks a full Fig. 4 executable. R4 still pending for item 3.
