# S2 — Item 3 re-measure on the A8 member-sum host

Not a pin. Not a freeze. Not a decay knob. Not L1–L8. Not an αI
retune. `wheat_params()` stay αI=3.2, ζ=0,
N_for=3, p_sto=0.1, xmin=0.2.
Fig. 4 knobs stay on the comparison object. G1/G2 stay blocked.

## Verification protocol (CLAUDE.md)

1. **Claim.** DEVELOPMENT item 3 / Agrimate undisturbed: after
spin-up, repeating seasonal behaviour. Author Fig. 4 baseline
last/first of the annual-mean world-price index 2011/2006 =
**1.004**.

2. **Implementation.** D.22 `q_oth` EMA in `sheaf/agrimate/model.py`
(`AgrimateSim.__init__` `freeze_q_oth=False`; init
`q_oth = max(XI*_world − XI*_r, 1e-9)`; each step
`q_oth = (1−w_exp)·q_oth + w_exp·realized_oth` unless freeze).
`freeze_q_oth` is an `AgrimateSim` / `run_agrimate` kwarg, **not**
an `AgrimateParams` field and **not** in `wheat_params()`.

3. **Match.** Live host still updates `q_oth` (D.22). N2 rolling
year (`replan_stride=1`) and N3 Jacobi IBR unchanged. Author D.22
still updates `q_oth` (R4 / `GATE0_DEPARTURES.md`).

4. **Counterexample.** On the S1 member-sum host, undisturbed
`prices_three_scenarios.csv` 2006–11 last/first = **1.444**
(USD annual mean $45.82 → $66.15). Author **1.004**
(index 1.113 → 1.117). Pre-S1 pooled-mean host was
**1.630**. Member-sum moved the
ratio; it did not recover Agrimate. Threshold 1.1 still failed.

5. **Correctness argument (do not adopt freeze).** R4
`qoth_freeze` last/first **1.019**
on the *pre-S1* host was a diagnostic isolation. Author still
updates `q_oth` and still has last/first ≈ 1. There is **no**
sourced D.22 variant in retrieved 14022004 wheat: this tree has
**0** `*.jl` files.
`scripts/fetch_external_data.py` does not mention 14022004.
`freeze_q_oth` is not an `AgrimateParams` field (absent, as
required). Without a sourced freeze (or other D.22 variant) from
author wheat code, adopting it would be a new economic law, not a
copy. Label and stop.

6. **Change.** None to economics. This note labels item 3 on the
member-sum host. `freeze_q_oth` stays default False. Do not pin
the unforced world price to the 2006 mean. Do not restore L1–L8.

## Live score (USD, 2006–11, from prices_three_scenarios.csv)

| object | last/first | 2006 mean | 2011 mean |
|---|---:|---:|---:|
| Host undisturbed | 1.444 | 45.82 | 66.15 |
| Author Fig. 4 baseline | 1.004 | 1.113 (index) | 1.117 (index) |
| Pre-S1 host (R4 default) | 1.630 | — | — |
| R4 qoth_freeze (pre-S1, not adopted) | 1.019 | — | — |

G0-P item 3 remains **fail**. Historical R4 probes stay in
`xi_split.md` (including that note's **Next paste: R5**).
**Next paste: S3.** A1 after A8 (USDA `ending_stocks` only;
never FAO ΔS as stocks). Do not start G1/G2.
