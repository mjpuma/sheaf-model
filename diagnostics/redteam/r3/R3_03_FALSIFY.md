# R3-03 - falsification battery

## 1. V1 across Agrimate's own N_for / tau_for sensitivity range

Agrimate Tbl. F.1 explores N_for in {3, 6, 9} and tau_for in {0.1, 0.2, 0.4} x N_year and reports no change in model dynamics. If SHEAF's scores swing across that range, V1 is a knob.

| N_for | tau_for | crop | corr | 2007/08 | 2010/11 |
|---|---|---|---|---|---|
| 3 | 4.8 | wheat | +0.720 | x2.27 | x1.44 |
| 3 | 4.8 | maize | +0.785 | x2.28 | x1.64 |
| 3 | 4.8 | rice | +0.677 | x1.72 | x0.82 |
| 6 | 4.8 | wheat | +0.729 | x2.29 | x1.44 |
| 6 | 4.8 | maize | +0.787 | x2.26 | x1.64 |
| 6 | 4.8 | rice | +0.677 | x1.72 | x0.82 |
| 9 | 4.8 | wheat | +0.722 | x2.27 | x1.43 |
| 9 | 4.8 | maize | +0.513 | x2.04 | x1.83 |
| 9 | 4.8 | rice | +0.677 | x1.72 | x0.82 |
| 6 | 2.4 | wheat | +0.730 | x2.29 | x1.44 |
| 6 | 2.4 | maize | +0.787 | x2.26 | x1.63 |
| 6 | 2.4 | rice | +0.677 | x1.72 | x0.82 |
| 6 | 9.6 | wheat | +0.729 | x2.29 | x1.44 |
| 6 | 9.6 | maize | +0.795 | x2.23 | x1.64 |
| 6 | 9.6 | rice | +0.677 | x1.72 | x0.82 |

Spread across the whole Agrimate range:

| crop | corr min | corr max | corr spread | 07/08 spread | 10/11 spread |
|---|---|---|---|---|---|
| wheat | +0.720 | +0.730 | 0.009 | 0.02 | 0.01 |
| maize | +0.513 | +0.795 | 0.281 | 0.25 | 0.20 |
| rice | +0.677 | +0.677 | 0.000 | 0.01 | 0.00 |

## 2. Is `foresight_phi` inert under V1 (no double-counting)?

| crop | phi | corr | 2007/08 | 2010/11 |
|---|---|---|---|---|
| wheat | 0.00 | +0.729 | x2.29 | x1.44 |
| wheat | 0.55 | +0.729 | x2.29 | x1.44 |
| wheat | 1.00 | +0.729 | x2.29 | x1.44 |
| maize | 0.00 | +0.787 | x2.26 | x1.64 |
| maize | 0.55 | +0.787 | x2.26 | x1.64 |
| maize | 1.00 | +0.787 | x2.26 | x1.64 |
| rice | 0.00 | +0.677 | x1.72 | x0.82 |
| rice | 0.55 | +0.677 | x1.72 | x0.82 |
| rice | 1.00 | +0.677 | x1.72 | x0.82 |

phi exactly inert under V1: **True** (so V1 replaces the parameter rather than stacking on it).

For contrast, phi in the SHIPPED model:

| crop | phi | corr | 2007/08 | 2010/11 |
|---|---|---|---|---|
| wheat | 0.00 | +0.724 | x2.28 | x1.46 |
| wheat | 0.55 | +0.720 | x2.27 | x1.45 |
| wheat | 1.00 | +0.721 | x2.27 | x1.43 |
| maize | 0.00 | +0.781 | x2.28 | x1.63 |
| maize | 0.55 | +0.713 | x1.97 | x1.74 |
| maize | 1.00 | +0.765 | x2.22 | x1.60 |
| rice | 0.00 | +0.678 | x1.73 | x0.82 |
| rice | 0.55 | +0.678 | x1.72 | x0.82 |
| rice | 1.00 | +0.677 | x1.72 | x0.82 |

## 3. Size of the within-step ask double-update

`_simulate_window` allocates shipments with the inherited ask (`A_eff` at L616 uses `ask_path[:, t]`), then updates `ask` at L646-651, then values the SAME shipments at the updated ask (L667). README section 8 writes p^tr with q_{i,t} while step 5 of Method of solution produces q_{i,t+1}.

| crop | mean |p^tr(post) - p^tr(pre)| $/t | mean rel gap | max rel gap | mean max_i |dask| $/t |
|---|---|---|---|---|
| wheat | 13.08 | 3.6941% | 12.6788% | 27.00 |
| maize | 5.49 | 3.2581% | 75.3548% | 12.03 |
| rice | 30.48 | 4.5560% | 27.5925% | 72.18 |

## 4. How long are the AMIS restriction phases SHEAF sees?

Duration knowledge can only matter where duration varies and is informative. Phase = maximal run of a constant nonzero cut.

| crop | n phases | median len (steps) | mean | max | share of cut-steps in phases >= 6 steps |
|---|---|---|---|---|---|
| wheat | 17 | 18 | 34.5 | 112 | 99.7% |
    - Russia wheat cut steps: 38, levels [0.5, 0.95], first step 44 (2007), last 131 (2011)
| maize | 10 | 22 | 38.6 | 94 | 99.5% |
| rice | 13 | 26 | 47.1 | 112 | 98.7% |

