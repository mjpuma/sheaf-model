# S5 — re-score Fig. 4 / hindcast on the member-sum host

Allowed because S1 changed the **data adapter**, not
`wheat_params()`. This is **not R11**. The 2003–11 three-scenario
NLP runner was not re-run. Bai αI=10 not adopted. L1–L8 stay
rejected. 2006 not pinned. G1/G2 stay blocked.

## Live scores (S1 CSVs vs author_fig4 / Pink Sheet)

| metric | host | author Fig. 4 | Pink Sheet |
|---|---:|---:|---:|
| 2006–08 hike (harvest+AMIS) | ×3.71 | ×1.62 | ×1.88 |
| 2006 quiet-year mean | $81.5/t (index 0.381) | index 1.183 | $213.5/t |
| moy max/min | 16.8× | 1.45× | 1.07× |
| undisturbed last/first | 1.444 | 1.004 | — |
| unconverged / failed | 2304/5832 / 0 | — | — |

`wheat_params()` αI=3.2, ζ=0, N_for=3.
Fig. 4 knobs stay on `fig4_experiment_params()`.

## Items 1–3 (pass rule)

1. Source fidelity: still met for retrieved 14022004 with labelled
   S3/S4/A1–A6/N5. Unchanged.
2. Numerical reliability: still feasible, **not** first-order
   stationary (unconverged 2304/5832). Still fails.
3. Undisturbed: last/first 1.444 vs author 1.004 (still >1.1). Still fails.

Items 1–3 evidence did **not** newly pass. Item 5 is still a
sourced shortfall (hike and moy still several times Agrimate).
G0-P stays **not accepted**. S6 is not next. Do not start G1.

## What this session did not do

- Did not re-run `scripts/run_agrimate_validation.py` (R11).
- Did not retune αI / p_sto / xmin / λ.
- Did not restore L1–L8 or pin 2006.
- Did not adopt Bai α_foreign=10.
- Did not adopt FBSH. Did not invent Egypt.
- Did not start G1/G2.

**Next paste: stay not-accepted.** Do not start G1.

