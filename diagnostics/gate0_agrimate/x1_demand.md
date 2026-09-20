# R5 — S4 x1=demand labelled experiment

Default **off**. Not adopted. **Not a pin.** Not a CES-rationing
rule (no min(supply, demand)). `wheat_params()` stay
αI=3.2, ζ=0, N_for=3,
xmin=0.2. L1–L8 stay rejected. G1/G2 stay blocked.

14022004 Julia is still **not in-tree**. S4 (2026-09-16 retrieval)
records that author two-market `x1` is *fixed* to D.30/D.30a
requests. This flag copies that assignment: Ndel-lagged foreign
requests replace `dest.T @ XI_lag` as international arrival;
domestic inflow stays `sold_d`. Destination-weight allocation of
XI was **not** copied (that would guess a ration).

Window: harvest+AMIS **2006** only
(24 steps). Default-off recovers today's
path (`test_x1_from_demand_default_off_recovers_path`).

## Off vs on

| metric | T*+domestic (off) | x1=demand (on) |
|---|---:|---:|
| Σ inflow MMT | 478.29 | 907.66 |
| Eastern Africa inflow | 4.628 | 7.386 |
| USA inflow | 29.91 | 95.47 |
| max \|Δ inflow\| | — | 100.516 |
| max \|Δ C\| | — | 0.950 |
| max \|Δ S_c\| | — | 121.250 |
| max \|Δ p_w\| | — | 0.000e+00 |
| unconverged | 213/648 | 213/648 |
| failed | 0 | 0 |

p_w is **silent** (XI-weighted lagged D.7 mix; B1/R3). Who eats / S_c move. εc/σ can now affect inflow; they still do not enter the supplier plan. Not a reason to retune αI.

**Next paste: R6.** A1 FAOSTAT FB obtain-or-leave. R5 does not
unlock G1. Item 3 still fails on the live host (x1 default off).
