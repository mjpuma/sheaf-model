# R3-02 - prototype scores and assertion impact

Baselines to validate the harness against (from the brief): wheat +0.720 / x2.27 / x1.45, maize +0.712 / x1.97 / x1.70, rice +0.678 / x1.72 / x0.82.

## V0_baseline

| crop | corr | 2007/08 | 2010/11 | obs 07/08 | obs 10/11 |
|---|---|---|---|---|---|
| wheat | +0.720 | x2.27 | x1.45 | x1.82 | x1.16 |
| maize | +0.712 | x1.97 | x1.70 | x1.84 | x1.44 |
| rice | +0.678 | x1.72 | x0.82 | x1.84 | x0.79 |

| crop | twin_identity | amis_raises_price | amis_cuts_exports | no_spring_spike |
|---|---|---|---|---|
| wheat | PASS | PASS | PASS | PASS |
| maize | PASS | PASS | PASS | PASS |
| rice | PASS | PASS | PASS | PASS |


## V1_agrimate_exp

| crop | corr | 2007/08 | 2010/11 | obs 07/08 | obs 10/11 |
|---|---|---|---|---|---|
| wheat | +0.729 | x2.29 | x1.44 | x1.82 | x1.16 |
| maize | +0.787 | x2.26 | x1.64 | x1.84 | x1.44 |
| rice | +0.677 | x1.72 | x0.82 | x1.84 | x0.79 |

| crop | twin_identity | amis_raises_price | amis_cuts_exports | no_spring_spike |
|---|---|---|---|---|
| wheat | PASS | PASS | PASS | PASS |
| maize | PASS | PASS | PASS | PASS |
| rice | PASS | PASS | PASS | PASS |


## V2_lag0_only

| crop | corr | 2007/08 | 2010/11 | obs 07/08 | obs 10/11 |
|---|---|---|---|---|---|
| wheat | +0.721 | x2.27 | x1.45 | x1.82 | x1.16 |
| maize | +0.711 | x1.97 | x1.70 | x1.84 | x1.44 |
| rice | +0.678 | x1.72 | x0.82 | x1.84 | x0.79 |

| crop | twin_identity | amis_raises_price | amis_cuts_exports | no_spring_spike |
|---|---|---|---|---|
| wheat | PASS | PASS | PASS | PASS |
| maize | PASS | PASS | PASS | PASS |
| rice | PASS | PASS | PASS | PASS |


## V3_pre_update_ask

| crop | corr | 2007/08 | 2010/11 | obs 07/08 | obs 10/11 |
|---|---|---|---|---|---|
| wheat | +0.680 | x2.08 | x1.31 | x1.82 | x1.16 |
| maize | +0.733 | x1.84 | x1.64 | x1.84 | x1.44 |
| rice | +0.675 | x1.55 | x0.84 | x1.84 | x0.79 |

| crop | twin_identity | amis_raises_price | amis_cuts_exports | no_spring_spike |
|---|---|---|---|---|
| wheat | PASS | PASS | PASS | PASS |
| maize | PASS | PASS | PASS | PASS |
| rice | PASS | PASS | PASS | PASS |


## V4_cut_duration

| crop | corr | 2007/08 | 2010/11 | obs 07/08 | obs 10/11 |
|---|---|---|---|---|---|
| wheat | +0.713 | x2.14 | x1.48 | x1.82 | x1.16 |
| maize | +0.650 | x1.78 | x1.67 | x1.84 | x1.44 |
| rice | +0.693 | x1.71 | x0.82 | x1.84 | x0.79 |

| crop | twin_identity | amis_raises_price | amis_cuts_exports | no_spring_spike |
|---|---|---|---|---|
| wheat | PASS | PASS | PASS | PASS |
| maize | PASS | PASS | PASS | PASS |
| rice | PASS | PASS | PASS | PASS |


## V13_agri_exp+pre_ask

| crop | corr | 2007/08 | 2010/11 | obs 07/08 | obs 10/11 |
|---|---|---|---|---|---|
| wheat | +0.688 | x2.09 | x1.31 | x1.82 | x1.16 |
| maize | +0.794 | x2.08 | x1.55 | x1.84 | x1.44 |
| rice | +0.675 | x1.54 | x0.85 | x1.84 | x0.79 |

| crop | twin_identity | amis_raises_price | amis_cuts_exports | no_spring_spike |
|---|---|---|---|---|
| wheat | PASS | PASS | PASS | PASS |
| maize | PASS | PASS | PASS | PASS |
| rice | PASS | PASS | PASS | PASS |


## Deltas vs V0

| variant | crop | d corr | d 2007/08 | d 2010/11 |
|---|---|---|---|---|
| V1_agrimate_exp | wheat | +0.010 | +0.02 | -0.01 |
| V1_agrimate_exp | maize | +0.075 | +0.29 | -0.06 |
| V1_agrimate_exp | rice | -0.001 | -0.00 | +0.00 |
| V2_lag0_only | wheat | +0.001 | +0.00 | +0.00 |
| V2_lag0_only | maize | -0.000 | +0.00 | +0.00 |
| V2_lag0_only | rice | -0.000 | -0.00 | +0.00 |
| V3_pre_update_ask | wheat | -0.040 | -0.19 | -0.14 |
| V3_pre_update_ask | maize | +0.021 | -0.13 | -0.06 |
| V3_pre_update_ask | rice | -0.003 | -0.18 | +0.02 |
| V4_cut_duration | wheat | -0.007 | -0.13 | +0.03 |
| V4_cut_duration | maize | -0.061 | -0.20 | -0.03 |
| V4_cut_duration | rice | +0.015 | -0.01 | +0.00 |
| V13_agri_exp+pre_ask | wheat | -0.031 | -0.17 | -0.14 |
| V13_agri_exp+pre_ask | maize | +0.083 | +0.11 | -0.15 |
| V13_agri_exp+pre_ask | rice | -0.003 | -0.18 | +0.03 |

