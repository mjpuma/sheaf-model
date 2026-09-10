# A3 — size of the contemporaneous-demand gap, and is G well posed?

Read-only measurement. `sheaf/*.py` and `scripts/*.py` untouched; everything here comes from `scripts/scratch/a3_demand_gap.py`.

**This measurement does not recommend adopting option B / X1.** It sizes a gap and tests well-posedness. The adoption decision needs A2 as well (per `audit_prompts/GATE0_MODEL_PROMPTS.md`).

Official scored path for all three crops: `run_crop_dynamics(crop, start_year=2006, end_year=2011, use_amis=True, use_shocks=True, use_demand=False)` — 144 steps, 2006-01a … 2011-12b.

## 0. Replica verification (prerequisite)

`simulate_prep(prepare_crop_run(...))` vs `run_crop_dynamics(...)`, and the scratch transcription of L577-681 (`step_G` with `p_demand = p_in`) vs the recorded path:

| crop | max_abs_dprice | max_abs_doffers | max_abs_dfree | max_abs_dstock | simprep_vs_run_max_dprice |
|---|---|---|---|---|---|
| wheat | 0.000e+00 | 0.000e+00 | 0.000e+00 | 0.000e+00 | 0.000e+00 |
| maize | 0.000e+00 | 0.000e+00 | 0.000e+00 | 0.000e+00 | 0.000e+00 |
| rice | 0.000e+00 | 0.000e+00 | 0.000e+00 | 0.000e+00 | 0.000e+00 |

All four columns are exactly 0.0, so the scratch copy of the step body is the shipped step body and `prep.C_flex` is the array the official run consumed.

## 1. Size of the gap (Task 1)

Gap at step *t* = `C_flex[:,t]*(p_t/p0)**elast - C_flex[:,t]*(p_{t-1}/p0)**elast`, everything else held at the official path. World totals, MMT per step (a step is 365.25/24 ≈ 15.2 days):

| crop | episode | n | mean | median | p05 | p95 | min | max | mean_abs | max_abs |
|---|---|---|---|---|---|---|---|---|---|---|
| maize | 2007/08 | 44 | -0.1145 | 0.06733 | -0.3775 | 0.7709 | -10.03 | 1.352 | 0.4774 | 10.03 |
| maize | 2010/11 | 42 | -0.08632 | -0.1199 | -0.3212 | 0.3142 | -0.442 | 0.3956 | 0.1583 | 0.442 |
| maize | calm | 58 | 0.09376 | 0.06204 | -0.06457 | 0.3285 | -0.1633 | 0.3416 | 0.1209 | 0.3416 |
| rice | 2007/08 | 44 | -0.04467 | -0.03294 | -0.2891 | 0.221 | -0.3718 | 0.2472 | 0.1179 | 0.3718 |
| rice | 2010/11 | 42 | 0.02198 | -0.06535 | -0.1142 | 0.2813 | -0.1837 | 0.2862 | 0.1211 | 0.2862 |
| rice | calm | 58 | -0.03126 | -0.06211 | -0.2447 | 0.284 | -0.285 | 0.2874 | 0.1023 | 0.2874 |
| wheat | 2007/08 | 44 | -0.06924 | -0.04991 | -0.2903 | 0.06288 | -0.4463 | 0.1171 | 0.09453 | 0.4463 |
| wheat | 2010/11 | 42 | -0.03685 | -0.0707 | -0.1888 | 0.1559 | -0.3904 | 0.1659 | 0.1215 | 0.3904 |
| wheat | calm | 58 | 0.03739 | 0.05065 | -0.1228 | 0.1649 | -0.2219 | 0.1836 | 0.09311 | 0.2219 |

Same, as a percent of world *desired* use in that step (flex + industrial, evaluated at `p_{t-1}`):

| crop | episode | n | mean | median | p05 | p95 | min | max | mean_abs | max_abs |
|---|---|---|---|---|---|---|---|---|---|---|
| maize | 2007/08 | 44 | -0.2454 | 0.2087 | -1.196 | 2.719 | -28.73 | 5.438 | 1.487 | 28.73 |
| maize | 2010/11 | 42 | -0.2765 | -0.3705 | -1.02 | 0.963 | -1.393 | 1.336 | 0.5089 | 1.393 |
| maize | calm | 58 | 0.299 | 0.1993 | -0.2133 | 1.079 | -0.5579 | 1.108 | 0.3878 | 1.108 |
| rice | 2007/08 | 44 | -0.261 | -0.1973 | -1.72 | 1.395 | -2.048 | 1.526 | 0.6942 | 2.048 |
| rice | 2010/11 | 42 | 0.1405 | -0.4191 | -0.7264 | 1.786 | -1.126 | 1.816 | 0.7768 | 1.816 |
| rice | calm | 58 | -0.1892 | -0.3918 | -1.499 | 1.763 | -1.716 | 1.835 | 0.6458 | 1.835 |
| wheat | 2007/08 | 44 | -0.2685 | -0.2023 | -1.096 | 0.2502 | -1.727 | 0.4747 | 0.3655 | 1.727 |
| wheat | 2010/11 | 42 | -0.1472 | -0.2777 | -0.7199 | 0.6117 | -1.496 | 0.6603 | 0.4737 | 1.496 |
| wheat | calm | 58 | 0.15 | 0.2098 | -0.5012 | 0.6877 | -0.9181 | 0.7697 | 0.3802 | 0.9181 |

Episode summary (absolute value, so signs do not cancel):

| crop | episode | mean_price | mean_abs_gap_mmt | max_abs_gap_mmt | mean_abs_gap_pct | max_abs_gap_pct | mean_world_desired |
|---|---|---|---|---|---|---|---|
| maize | 2007/08 | 172.6 | 0.4774 | 10.03 | 1.487 | 28.73 | 31.65 |
| maize | 2010/11 | 236.1 | 0.1583 | 0.442 | 0.5089 | 1.393 | 31.24 |
| maize | calm | 214.1 | 0.1209 | 0.3416 | 0.3878 | 1.108 | 31.06 |
| rice | 2007/08 | 467.4 | 0.1179 | 0.3718 | 0.6942 | 2.048 | 17.2 |
| rice | 2010/11 | 760.2 | 0.1211 | 0.2862 | 0.7768 | 1.816 | 15.46 |
| rice | calm | 685.9 | 0.1023 | 0.2874 | 0.6458 | 1.835 | 15.97 |
| wheat | 2007/08 | 305.9 | 0.09453 | 0.4463 | 0.3655 | 1.727 | 25.67 |
| wheat | 2010/11 | 297.6 | 0.1215 | 0.3904 | 0.4737 | 1.496 | 25.68 |
| wheat | calm | 401.7 | 0.09311 | 0.2219 | 0.3802 | 0.9181 | 24.6 |

Same, **dropping the first model year (steps 0-23)**. `assert_twin_identity` (L907) already discards `price[:24]` as transient, and the single largest gap in the whole dataset (maize step 22, 2006-12a) sits inside it, so the episode numbers should be read from this table rather than the one above:

| crop | episode | n | mean_abs_gap_mmt | max_abs_gap_mmt | mean_abs_gap_pct | max_abs_gap_pct |
|---|---|---|---|---|---|---|
| maize | 2007/08 | 30 | 0.24 | 1.091 | 0.8077 | 4.014 |
| maize | 2010/11 | 42 | 0.1583 | 0.442 | 0.5089 | 1.393 |
| maize | calm | 48 | 0.1049 | 0.3416 | 0.3437 | 1.108 |
| rice | 2007/08 | 30 | 0.148 | 0.3718 | 0.8813 | 2.048 |
| rice | 2010/11 | 42 | 0.1211 | 0.2862 | 0.7768 | 1.816 |
| rice | calm | 48 | 0.1171 | 0.2874 | 0.7439 | 1.835 |
| wheat | 2007/08 | 30 | 0.08277 | 0.4463 | 0.3285 | 1.727 |
| wheat | 2010/11 | 42 | 0.1215 | 0.3904 | 0.4737 | 1.496 |
| wheat | calm | 48 | 0.09745 | 0.2219 | 0.4037 | 0.9181 |

Fifteen largest world gaps, any crop:

| crop | step | tag | episode | p_prev | p_t | price_ratio | world_gap_mmt | world_gap_pct | offers_gap_pct | ratio_gap_pct | p_gap_one_step |
|---|---|---|---|---|---|---|---|---|---|---|---|
| maize | 22 | 2006-12a | 2007/08 | 95.5 | 393.9 | 4.125 | -10.03 | -28.73 | 12.92 | -4.182 | -14.94 |
| maize | 23 | 2006-12b | 2007/08 | 393.9 | 315.2 | 0.8001 | 1.352 | 5.438 | -1.06 | 1.372 | 0.4023 |
| maize | 24 | 2007-01a | 2007/08 | 315.2 | 265.6 | 0.8426 | 1.091 | 4.014 | -0.9548 | 1.138 | 0.2204 |
| maize | 25 | 2007-01b | 2007/08 | 265.6 | 235.3 | 0.886 | 0.7993 | 2.828 | -0.7697 | 0.8169 | 0.1512 |
| maize | 26 | 2007-02a | 2007/08 | 235.3 | 215.1 | 0.914 | 0.6101 | 2.099 | -0.6808 | 0.5796 | 0.09371 |
| maize | 27 | 2007-02b | 2007/08 | 215.1 | 200.4 | 0.9318 | 0.4886 | 1.647 | -0.5354 | 0.4262 | 0.0635 |
| wheat | 30 | 2007-04a | 2007/08 | 274.5 | 308.3 | 1.123 | -0.4463 | -1.727 | 0.3546 | -0.6219 | -0.5124 |
| maize | 101 | 2010-03b | 2010/11 | 216.7 | 231.3 | 1.067 | -0.442 | -1.393 | 0.4179 | -0.27 | -0.5311 |
| maize | 15 | 2006-08b | 2007/08 | 99.27 | 104.7 | 1.055 | -0.4416 | -1.278 | 0.1575 | -0.3368 | -0.06142 |
| maize | 110 | 2010-08a | 2010/11 | 299 | 281 | 0.9397 | 0.3956 | 1.336 | -0.4516 | 0.2448 | 0.05846 |
| wheat | 110 | 2010-08a | 2010/11 | 258.3 | 285.6 | 1.106 | -0.3904 | -1.496 | 0.1379 | -0.09179 | -0.02297 |
| maize | 37 | 2007-07b | 2007/08 | 177.2 | 186.9 | 1.055 | -0.3817 | -1.23 | 0.1266 | -0.2883 | -0.07316 |
| maize | 28 | 2007-03a | 2007/08 | 200.4 | 190.1 | 0.9484 | 0.372 | 1.233 | -0.3671 | 0.2883 | 0.04246 |
| rice | 24 | 2007-01a | 2007/08 | 312.6 | 346 | 1.107 | -0.3718 | -2.014 | 0 | -6.83 | -4.113 |
| maize | 111 | 2010-08b | 2010/11 | 281 | 265.7 | 0.9456 | 0.3611 | 1.204 | -0.1332 | 0.2541 | 0.004478 |

Twenty largest country-step gaps:

| crop | step | tag | episode | country | C_flex_step | gap_mmt | gap_pct_of_demand | offers_gap_mmt |
|---|---|---|---|---|---|---|---|---|
| maize | 22 | 2006-12a | 2007/08 | USA | 7.919 | -2.578 | -25.98 | 2.578 |
| maize | 22 | 2006-12a | 2007/08 | China | 7.188 | -2.34 | -29.83 | 0 |
| maize | 22 | 2006-12a | 2007/08 | RestOfWorld | 6.282 | -2.045 | -29.83 | 0 |
| maize | 22 | 2006-12a | 2007/08 | EU | 2.716 | -0.8842 | -29.83 | 0 |
| maize | 22 | 2006-12a | 2007/08 | Brazil | 1.951 | -0.6353 | -29.83 | 0.6353 |
| maize | 22 | 2006-12a | 2007/08 | Mexico | 1.276 | -0.4155 | -29.83 | 0 |
| maize | 23 | 2006-12b | 2007/08 | USA | 7.919 | 0.3477 | 4.733 | -0.3477 |
| maize | 23 | 2006-12b | 2007/08 | China | 7.188 | 0.3156 | 5.734 | -0.3156 |
| maize | 24 | 2007-01a | 2007/08 | USA | 7.919 | 0.2805 | 3.243 | -0.2805 |
| maize | 23 | 2006-12b | 2007/08 | RestOfWorld | 6.282 | 0.2758 | 5.734 | 0 |
| maize | 24 | 2007-01a | 2007/08 | China | 7.188 | 0.2545 | 4.374 | -0.2545 |
| maize | 24 | 2007-01a | 2007/08 | RestOfWorld | 6.282 | 0.2225 | 4.374 | 0 |
| maize | 22 | 2006-12a | 2007/08 | India | 0.6632 | -0.2159 | -29.83 | 0 |
| maize | 25 | 2007-01b | 2007/08 | USA | 7.919 | 0.2055 | 2.302 | -0.2055 |
| maize | 25 | 2007-01b | 2007/08 | China | 7.188 | 0.1865 | 3.071 | -0.1865 |
| maize | 22 | 2006-12a | 2007/08 | Canada | 0.5015 | -0.1633 | -29.83 | 0 |
| maize | 25 | 2007-01b | 2007/08 | RestOfWorld | 6.282 | 0.163 | 3.071 | 0 |
| maize | 26 | 2007-02a | 2007/08 | USA | 7.919 | 0.1569 | 1.717 | -0.1569 |
| maize | 22 | 2006-12a | 2007/08 | Egypt | 0.475 | -0.1546 | -29.83 | 0 |
| maize | 26 | 2007-02a | 2007/08 | China | 7.188 | 0.1424 | 2.274 | -0.1424 |

Six largest-gap countries per crop (mean over all 144 steps):

| crop | country | mean_abs_gap_mmt | max_abs_gap_mmt | mean_abs_gap_pct |
|---|---|---|---|---|
| maize | USA | 0.0619 | 2.578 | 0.6231 |
| maize | China | 0.05618 | 2.34 | 0.8262 |
| maize | RestOfWorld | 0.0491 | 2.045 | 0.8262 |
| maize | EU | 0.02123 | 0.8842 | 0.8262 |
| maize | Brazil | 0.01525 | 0.6353 | 0.8262 |
| maize | Mexico | 0.009977 | 0.4155 | 0.8262 |
| rice | China | 0.03424 | 0.1131 | 0.6988 |
| rice | RestOfWorld | 0.03124 | 0.1032 | 0.6988 |
| rice | India | 0.02312 | 0.07639 | 0.6988 |
| rice | Indonesia | 0.009622 | 0.03179 | 0.6988 |
| rice | Vietnam | 0.004965 | 0.0164 | 0.6988 |
| rice | Thailand | 0.002573 | 0.008499 | 0.6988 |
| wheat | RestOfWorld | 0.02816 | 0.1235 | 0.403 |
| wheat | EU | 0.01961 | 0.08598 | 0.403 |
| wheat | China | 0.01731 | 0.07586 | 0.403 |
| wheat | India | 0.01217 | 0.05336 | 0.403 |
| wheat | Russia | 0.006045 | 0.0265 | 0.403 |
| wheat | USA | 0.004908 | 0.02152 | 0.403 |

## 2. One-step propagation (Task 2)

**Caveat, stated as required: this is a one-step bound, not a simulation of the fixed point.** Each row re-evaluates the step body once with demand priced at the realised `p_t`, holding the incoming stock, incoming ask vector, incoming price, harvest, cuts and the calm twin at their official values. It does not iterate to `p = G(p)` and it does not let the state drift.

| crop | episode | n | mean | median | p05 | p95 | min | max | mean_abs | max_abs |
|---|---|---|---|---|---|---|---|---|---|---|
| maize | 2007/08 | 44 | 0.1853 | -0.0312 | -0.7563 | 0.1307 | -1.06 | 12.92 | 0.474 | 12.92 |
| maize | 2010/11 | 42 | 0.0782 | 0.06911 | -0.131 | 0.2808 | -0.4516 | 0.4179 | 0.1277 | 0.4516 |
| maize | calm | 58 | -0.04567 | -0.02706 | -0.1503 | 0.04378 | -0.2611 | 0.1275 | 0.06374 | 0.2611 |
| rice | 2007/08 | 44 | 0.2392 | 0 | -0.2303 | 0.5758 | -0.7028 | 8.865 | 0.3583 | 8.865 |
| rice | 2010/11 | 42 | 0.1039 | 0.09649 | -0.09221 | 0.19 | -0.1063 | 1.894 | 0.1427 | 1.894 |
| rice | calm | 58 | 0.1264 | 0.1134 | -0.08394 | 0.4673 | -0.09935 | 0.6586 | 0.1559 | 0.6586 |
| wheat | 2007/08 | 44 | 0.09427 | 0.03224 | -0.05613 | 0.3664 | -0.391 | 1.478 | 0.1279 | 1.478 |
| wheat | 2010/11 | 42 | 0.03019 | 0.03955 | -0.08219 | 0.1701 | -0.1671 | 0.2275 | 0.08554 | 0.2275 |
| wheat | calm | 58 | -0.00151 | -0.02305 | -0.1216 | 0.1904 | -0.174 | 0.5395 | 0.06944 | 0.5395 |

Scarcity ratio `r_t = (twin+shift)/(free+shift)` (L661-663):

| crop | episode | n | mean | median | p05 | p95 | min | max | mean_abs | max_abs |
|---|---|---|---|---|---|---|---|---|---|---|
| maize | 2007/08 | 44 | 0.004065 | 0.0271 | -0.2709 | 0.7813 | -4.182 | 1.372 | 0.2803 | 4.182 |
| maize | 2010/11 | 42 | -0.04938 | -0.05985 | -0.1862 | 0.09388 | -0.27 | 0.2541 | 0.08819 | 0.27 |
| maize | calm | 58 | 0.03742 | 0.01939 | -0.03369 | 0.1469 | -0.09052 | 0.183 | 0.05138 | 0.183 |
| rice | 2007/08 | 44 | -0.6 | -0.04057 | -4.158 | 0.8811 | -6.83 | 1.035 | 0.8215 | 6.83 |
| rice | 2010/11 | 42 | 0.08581 | -0.03977 | -0.2806 | 0.7331 | -0.4627 | 0.7807 | 0.2414 | 0.7807 |
| rice | calm | 58 | -0.1379 | -0.05925 | -0.8201 | 0.6384 | -1.237 | 0.7084 | 0.2742 | 1.237 |
| wheat | 2007/08 | 44 | -0.12 | -0.0407 | -0.6828 | 0.06275 | -0.8396 | 0.1841 | 0.1449 | 0.8396 |
| wheat | 2010/11 | 42 | -0.01788 | -0.04412 | -0.1123 | 0.09393 | -0.1576 | 0.09948 | 0.06837 | 0.1576 |
| wheat | calm | 58 | 0.01977 | 0.02808 | -0.1412 | 0.1488 | -0.2855 | 0.2106 | 0.07358 | 0.2855 |

Resulting one-step move in the price the step writes (`p_out` under contemporaneous demand minus official `p_t`), $/t:

| crop | episode | n | mean | median | p05 | p95 | min | max | mean_abs | max_abs |
|---|---|---|---|---|---|---|---|---|---|---|
| maize | 2007/08 | 44 | -0.3204 | 0.004498 | -0.06039 | 0.1426 | -14.94 | 0.4023 | 0.3772 | 14.94 |
| maize | 2010/11 | 42 | -0.06502 | -0.01203 | -0.3205 | 0.05607 | -0.599 | 0.2387 | 0.0843 | 0.599 |
| maize | calm | 58 | 0.0009321 | 0.001635 | -0.02433 | 0.01687 | -0.1215 | 0.05157 | 0.01117 | 0.1215 |
| rice | 2007/08 | 44 | -0.3323 | -0.02757 | -2.325 | 0.1628 | -4.113 | 0.2404 | 0.3896 | 4.113 |
| rice | 2010/11 | 42 | -0.008482 | -0.00793 | -0.07683 | 0.06128 | -0.09927 | 0.06717 | 0.04438 | 0.09927 |
| rice | calm | 58 | -0.05185 | -0.04201 | -0.2801 | 0.04916 | -0.4499 | 0.06518 | 0.07146 | 0.4499 |
| wheat | 2007/08 | 44 | -0.09204 | -0.02851 | -0.4928 | 0.03142 | -0.819 | 0.1104 | 0.1042 | 0.819 |
| wheat | 2010/11 | 42 | -0.01232 | -0.01024 | -0.04627 | 0.01376 | -0.06257 | 0.02349 | 0.01986 | 0.06257 |
| wheat | calm | 58 | 0.0009511 | 0.006954 | -0.06554 | 0.03838 | -0.1699 | 0.06552 | 0.02431 | 0.1699 |

## 3. Well-posedness of G (Task 3)

`G(x)` = the price the step writes when demand is evaluated at trial price `x`, incoming state held at the official path. Option B is `p_t = G(p_t)`.

### 3a. Local behaviour on ±35% around the official price

| crop | episode | n | L_max_worst | L_max_mean | all_monotone_decreasing | n_not_monotone | worst_root_sign_changes | max_abs_fp_residual | max_abs_fp_minus_official | n_any_calm | n_twin_in_range |
|---|---|---|---|---|---|---|---|---|---|---|---|
| maize | 2007/08 | 12 | 0.03883 | 0.0146 | True | 0 | 1 | 0 | 14.61 | 0 | 0 |
| maize | 2010/11 | 11 | 0.1187 | 0.02963 | False | 3 | 1 | 5.684e-14 | 0.5663 | 0 | 0 |
| maize | calm | 16 | 0.04097 | 0.01053 | False | 4 | 1 | 5.684e-14 | 0.1197 | 0 | 0 |
| rice | 2007/08 | 12 | 0.1954 | 0.04676 | False | 1 | 1 | 1.137e-13 | 3.683 | 0 | 5 |
| rice | 2010/11 | 11 | 0.004179 | 0.003043 | True | 0 | 1 | 1.137e-13 | 0.06047 | 0 | 0 |
| rice | calm | 16 | 0.1305 | 0.02051 | True | 0 | 1 | 1.137e-13 | 0.3765 | 0 | 4 |
| wheat | 2007/08 | 13 | 0.05212 | 0.01767 | False | 1 | 1 | 5.684e-14 | 0.5662 | 0 | 1 |
| wheat | 2010/11 | 11 | 0.00666 | 0.003475 | False | 1 | 1 | 5.684e-14 | 0.04163 | 0 | 0 |
| wheat | calm | 16 | 0.03555 | 0.006491 | False | 3 | 1 | 5.684e-14 | 0.05878 | 0 | 1 |

### 3b. Global scan on the full admissible interval [60, 1200]

| crop | step | tag | episode | p_official | resid_at_60 | resid_at_1200 | root_sign_changes | L_max_global | monotone_decreasing | G_min | G_max | any_calm | any_clipped |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| wheat | 30 | 2007-04a | 2007/08 | 308.3 | 256.4 | -897.4 | 1 | 0.1024 | True | 302.6 | 316.4 | False | False |
| wheat | 53 | 2008-03b | 2007/08 | 429.5 | 373.7 | -771.9 | 1 | 0.04305 | True | 428.1 | 433.7 | False | False |
| wheat | 78 | 2009-04a | calm | 290.3 | 231.1 | -910.1 | 1 | 0.01088 | True | 289.9 | 291.1 | False | False |
| wheat | 123 | 2011-02b | 2010/11 | 447.5 | 386.1 | -752.8 | 1 | 0.02176 | False | 445.2 | 447.5 | False | False |
| maize | 22 | 2006-12a | 2007/08 | 393.9 | 340.1 | -829.5 | 1 | 0.2269 | True | 370.5 | 400.1 | False | False |
| maize | 78 | 2009-04a | calm | 183.9 | 124.8 | -1017 | 1 | 0.01567 | False | 183.1 | 184.8 | False | False |
| maize | 123 | 2011-02b | 2010/11 | 315.5 | 253 | -884.6 | 1 | 0.131 | False | 311.5 | 315.7 | False | False |
| rice | 24 | 2007-01a | 2007/08 | 346 | 362.7 | -885.6 | 1 | 0.8567 | True | 314.4 | 422.7 | False | False |
| rice | 47 | 2007-12b | 2007/08 | 698 | 648.4 | -503 | 1 | 0.1618 | True | 697 | 708.4 | False | False |
| rice | 78 | 2009-04a | calm | 653.4 | 596 | -546.9 | 1 | 0.02938 | True | 653.1 | 656 | False | False |
| rice | 113 | 2010-09b | 2010/11 | 896.9 | 842.7 | -303.6 | 1 | 0.04511 | True | 896.4 | 902.7 | False | False |

### 3c. The calm boundary (L666-669)

Bisection on `free(x) - twin` over the whole interval, to land on the calm boundary and measure the jump in `G` across it. `theoretical_jump` is `(1-smooth)*trade_w*|p_trade - p0|`, the size of the discontinuity implied by dropping the trade term.

| crop | step | tag | episode | twin | free_at_60 | free_at_1200 | block_frac | crossing_exists | p_cross | G_below | G_above | calm_below | calm_above | p_trade_at_cross | jump_in_G | theoretical_jump | bracket_width |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| wheat | 30 | 2007-04a | 2007/08 | 52.18 | 30.87 | 37.65 | 0.001355 | False | — | — | — | nan | nan | — | — | — | — |
| wheat | 53 | 2008-03b | 2007/08 | 49.47 | 53.38 | 62.21 | 0.1362 | False | — | — | — | nan | nan | — | — | — | — |
| wheat | 78 | 2009-04a | calm | 58.67 | 97.49 | 106.8 | 0.07836 | False | — | — | — | nan | nan | — | — | — | — |
| wheat | 123 | 2011-02b | 2010/11 | 53.94 | 87.33 | 95.85 | 0.2354 | False | — | — | — | nan | nan | — | — | — | — |
| maize | 22 | 2006-12a | 2007/08 | 207.1 | -19.14 | -0.1453 | 0 | False | — | — | — | nan | nan | — | — | — | — |
| maize | 78 | 2009-04a | calm | 226.2 | 170.9 | 190.2 | 0.0901 | False | — | — | — | nan | nan | — | — | — | — |
| maize | 123 | 2011-02b | 2010/11 | 207.4 | 138.9 | 158 | 0.09376 | False | — | — | — | nan | nan | — | — | — | — |
| rice | 24 | 2007-01a | 2007/08 | -32.05 | -38.82 | -29.04 | 0.1408 | True | 390 | 337.2 | 337.2 | False | False | 312.6 | 3.979e-13 | 6.659 | 5.684e-14 |
| rice | 47 | 2007-12b | 2007/08 | -20.57 | -11.89 | -3.027 | 0.3725 | False | — | — | — | nan | nan | — | — | — | — |
| rice | 78 | 2009-04a | calm | -15.45 | 9.828 | 21.28 | 0.3008 | False | — | — | — | nan | nan | — | — | — | — |
| rice | 113 | 2010-09b | 2010/11 | 117.8 | 103.6 | 109.4 | 0.3572 | False | — | — | — | nan | nan | — | — | — | — |

### 3d. Every step, every crop: root count, Lipschitz, Picard

`G` evaluated on a 401-point grid spanning the whole clip interval [60, 1200] at all 3 x 144 steps; the root then bisected to machine precision; then plain Picard (`x <- G(x)`) started from `p_{t-1}`, tolerance 1e-8 $/t, cap 200 iterations.

| crop | episode | n | n_roots_min | n_roots_max | L_max_worst | L_max_median | slope_at_root_worst | n_not_monotone | max_abs_fp_residual | picard_iters_max | picard_iters_median | max_abs_picard_vs_bisect | n_free_negative | min_resid_at_60 | max_resid_at_1200 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| maize | 2007/08 | 44 | 1 | 1 | 2.362 | 0.02121 | 0.04888 | 1 | 2.842e-14 | 8 | 5 | 2.286e-10 | 1 | 31.65 | -829.5 |
| maize | 2010/11 | 42 | 1 | 1 | 0.7884 | 0.03058 | 0.05788 | 18 | 0 | 9 | 5 | 2.24e-10 | 0 | 110.9 | -884.6 |
| maize | calm | 58 | 1 | 1 | 0.6056 | 0.01574 | 0.02379 | 21 | 5.684e-14 | 6 | 5 | 1.764e-10 | 0 | 45.96 | -872.4 |
| rice | 2007/08 | 44 | 1 | 1 | 19.86 | 0.2321 | 0.1174 | 6 | 0 | 12 | 6 | 5.162e-10 | 18 | 266.8 | -503 |
| rice | 2010/11 | 42 | 1 | 1 | 0.1009 | 0.04481 | 0.004658 | 3 | 1.137e-13 | 6 | 5 | 1.171e-11 | 7 | 473.5 | -303.6 |
| rice | calm | 58 | 1 | 1 | 0.6571 | 0.05984 | 0.07695 | 3 | 5.684e-14 | 9 | 5 | 3.532e-10 | 8 | 322.1 | -298.2 |
| wheat | 2007/08 | 44 | 1 | 1 | 0.2081 | 0.05705 | 0.04795 | 5 | 5.684e-14 | 8 | 5 | 4.549e-10 | 0 | 126.6 | -771.6 |
| wheat | 2010/11 | 42 | 1 | 1 | 0.06656 | 0.01301 | 0.00636 | 12 | 2.842e-14 | 6 | 5 | 2.191e-11 | 0 | 152.7 | -752.8 |
| wheat | calm | 58 | 1 | 1 | 0.1211 | 0.0152 | 0.01968 | 9 | 0 | 6 | 5 | 1.896e-10 | 0 | 135.6 | -664.3 |

Root count is exactly 1 at all 432 crop-steps: min=1, max=1. `resid_at_60 > 0 > resid_at_1200` at every step (min resid at 60 = 31.6, max resid at 1200 = -298), so `G` maps [60,1200] strictly into itself and the clip cannot remove the root.

**Per-step fixed point vs the official price** — this is the sharpest one-step number available, and it is still a one-step bound: it solves `p = G(p)` at step *t* with the incoming stock, ask vector and `p_{t-1}` pinned to the official path, so it does not let the state drift as a real option-B run would.

| crop | episode | n | mean_abs_dp | max_abs_dp | mean_abs_pct | max_abs_pct |
|---|---|---|---|---|---|---|
| maize | 2007/08 | 30 | 0.0339 | 0.2193 | 0.0163 | 0.08259 |
| maize | 2010/11 | 42 | 0.08222 | 0.5663 | 0.03301 | 0.2613 |
| maize | calm | 48 | 0.01077 | 0.1197 | 0.004098 | 0.03697 |
| rice | 2007/08 | 30 | 0.4863 | 3.683 | 0.1193 | 1.064 |
| rice | 2010/11 | 42 | 0.04429 | 0.09881 | 0.006009 | 0.01316 |
| rice | calm | 48 | 0.05011 | 0.1528 | 0.00681 | 0.0223 |
| wheat | 2007/08 | 30 | 0.07422 | 0.5053 | 0.02354 | 0.1639 |
| wheat | 2010/11 | 42 | 0.01981 | 0.06218 | 0.00668 | 0.0268 |
| wheat | calm | 48 | 0.02039 | 0.1689 | 0.004724 | 0.03698 |

Including the first model year, the worst single step is:

| crop | step | tag | episode | in_first_model_year | p_prev | p_official | fp | fp_minus_official | fp_pct_of_official | L_max_global | picard_iters | free_official |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| maize | 22 | 2006-12a | 2007/08 | True | 95.5 | 393.9 | 379.3 | -14.61 | -3.707 | 0.2269 | 8 | -15.18 |
| rice | 24 | 2007-01a | 2007/08 | False | 312.6 | 346 | 342.4 | -3.683 | -1.064 | 0.8567 | 12 | -32.72 |
| rice | 25 | 2007-01b | 2007/08 | False | 346 | 375.2 | 372.3 | -2.898 | -0.7724 | 0.8757 | 11 | -33.79 |
| rice | 26 | 2007-02a | 2007/08 | False | 375.2 | 398.4 | 396.1 | -2.271 | -0.57 | 0.9111 | 11 | -33.34 |
| rice | 27 | 2007-02b | 2007/08 | False | 398.4 | 412.4 | 411.2 | -1.179 | -0.286 | 0.9326 | 10 | -32.24 |
| wheat | 21 | 2006-11b | 2007/08 | True | 238.2 | 256.5 | 255.8 | -0.7816 | -0.3047 | 0.1693 | 8 | 32.37 |
| rice | 44 | 2007-11a | 2007/08 | False | 539.9 | 598.8 | 598.1 | -0.6502 | -0.1086 | 0.2388 | 6 | 31.25 |
| maize | 100 | 2010-03a | 2010/11 | False | 206.6 | 216.7 | 216.1 | -0.5663 | -0.2613 | 0.1129 | 9 | 141.4 |

### 3e. Grid-refinement continuity test

If `G` had a jump inside the window, the finite-difference `L_max` would grow roughly linearly with grid density and `maxjump` would stay pinned at the jump height. Six worst-slope steps per crop plus the probe steps, window = official price +/- 15%:

| crop | step | tag | episode | p_official | lo | hi | L_max_n401 | maxjump_n401 | L_max_n3201 | maxjump_n3201 | L_max_n25601 | maxjump_n25601 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| wheat | 19 | 2006-10b | 2007/08 | 219.1 | 186.2 | 252 | 0.03934 | 0.006465 | 0.03936 | 0.0008086 | 0.03937 | 0.0001011 |
| wheat | 20 | 2006-11a | 2007/08 | 238.2 | 202.5 | 274 | 0.04689 | 0.008378 | 0.04692 | 0.001048 | 0.04693 | 0.000131 |
| wheat | 21 | 2006-11b | 2007/08 | 256.5 | 218.1 | 295 | 0.05131 | 0.009872 | 0.05135 | 0.001235 | 0.05135 | 0.0001544 |
| wheat | 22 | 2006-12a | 2007/08 | 252.2 | 214.4 | 290 | 0.03206 | 0.006064 | 0.03207 | 0.0007583 | 0.03208 | 9.48e-05 |
| wheat | 24 | 2007-01a | 2007/08 | 258.6 | 219.8 | 297.4 | 0.03465 | 0.006721 | 0.03467 | 0.0008406 | 0.03467 | 0.0001051 |
| wheat | 29 | 2007-03b | 2007/08 | 274.5 | 233.3 | 315.7 | 0.03876 | 0.007981 | 0.03878 | 0.0009981 | 0.03879 | 0.0001248 |
| wheat | 30 | 2007-04a | 2007/08 | 308.3 | 262.1 | 354.6 | 0.01718 | 0.003974 | 0.01719 | 0.0004969 | 0.01719 | 6.212e-05 |
| wheat | 53 | 2008-03b | 2007/08 | 429.5 | 365.1 | 494 | 0.004623 | 0.001489 | 0.004625 | 0.0001862 | 0.004625 | 2.328e-05 |
| wheat | 78 | 2009-04a | calm | 290.3 | 246.8 | 333.9 | 0.001467 | 0.0003194 | 0.001467 | 3.994e-05 | 0.001468 | 4.993e-06 |
| wheat | 123 | 2011-02b | 2010/11 | 447.5 | 380.3 | 514.6 | 0.0007694 | 0.0002582 | 0.0007697 | 3.229e-05 | 0.0007697 | 4.036e-06 |
| maize | 22 | 2006-12a | 2007/08 | 393.9 | 334.9 | 453 | 0.02736 | 0.008083 | 0.02737 | 0.001011 | 0.02737 | 0.0001264 |
| maize | 42 | 2007-10a | 2007/08 | 178.2 | 151.5 | 205 | 0.001003 | 0.0001341 | 0.001004 | 1.677e-05 | 0.001004 | 2.097e-06 |
| maize | 78 | 2009-04a | calm | 183.9 | 156.3 | 211.5 | 0.004291 | 0.0005919 | 0.004293 | 7.403e-05 | 0.004294 | 9.254e-06 |
| maize | 107 | 2010-06b | 2010/11 | 290.3 | 246.7 | 333.8 | 0.06723 | 0.01464 | 0.06741 | 0.001834 | 0.06742 | 0.0002294 |
| maize | 108 | 2010-07a | 2010/11 | 297 | 252.4 | 341.5 | 0.02967 | 0.006609 | 0.02979 | 0.0008295 | 0.0298 | 0.0001037 |
| maize | 109 | 2010-07b | 2010/11 | 299 | 254.2 | 343.9 | 0.01661 | 0.003725 | 0.01663 | 0.0004663 | 0.01664 | 5.83e-05 |
| maize | 123 | 2011-02b | 2010/11 | 315.5 | 268.1 | 362.8 | 0.009966 | 0.002358 | 0.009969 | 0.0002948 | 0.009969 | 3.685e-05 |
| maize | 131 | 2011-06b | calm | 324.1 | 275.4 | 372.7 | 0.009362 | 0.002275 | 0.009371 | 0.0002847 | 0.009372 | 3.559e-05 |
| maize | 137 | 2011-09b | calm | 266.7 | 226.7 | 306.8 | 0.0005848 | 0.000117 | 0.0005851 | 1.463e-05 | 0.0005851 | 1.829e-06 |
| rice | 21 | 2006-11b | 2007/08 | 307.4 | 261.3 | 353.5 | 0.04744 | 0.01094 | 0.04747 | 0.001368 | 0.04748 | 0.000171 |
| rice | 24 | 2007-01a | 2007/08 | 346 | 294.1 | 397.9 | 0.1397 | 0.03625 | 0.1397 | 0.004533 | 0.1397 | 0.0005667 |
| rice | 25 | 2007-01b | 2007/08 | 375.2 | 318.9 | 431.4 | 0.1266 | 0.03562 | 0.1266 | 0.004454 | 0.1266 | 0.0005568 |
| rice | 26 | 2007-02a | 2007/08 | 398.4 | 338.6 | 458.2 | 0.1257 | 0.03755 | 0.1257 | 0.004696 | 0.1257 | 0.0005871 |
| rice | 27 | 2007-02b | 2007/08 | 412.4 | 350.5 | 474.2 | 0.1238 | 0.03829 | 0.1239 | 0.004788 | 0.1239 | 0.0005986 |
| rice | 28 | 2007-03a | 2007/08 | 420.2 | 357.2 | 483.3 | 0.1124 | 0.03542 | 0.1125 | 0.004432 | 0.1125 | 0.000554 |
| rice | 47 | 2007-12b | 2007/08 | 698 | 593.3 | 802.7 | 0.003585 | 0.001877 | 0.003587 | 0.0002347 | 0.003587 | 2.934e-05 |
| rice | 51 | 2008-02b | 2007/08 | 573.6 | 487.6 | 659.6 | 0.001082 | 0.0004653 | 0.001083 | 5.822e-05 | 0.001083 | 7.278e-06 |
| rice | 78 | 2009-04a | calm | 653.4 | 555.4 | 751.4 | 0.001201 | 0.0005885 | 0.001202 | 7.36e-05 | 0.001202 | 9.201e-06 |
| rice | 113 | 2010-09b | 2010/11 | 896.9 | 762.4 | 1031 | 0.002312 | 0.001555 | 0.002313 | 0.0001945 | 0.002314 | 2.432e-05 |

### 3f. Is the `calm` branch reachable at all?

The branch needs three conditions simultaneously (`|free-twin| < 1e-6`, `u_anom < 1e-9`, `block_frac < 1e-9`). `block_frac` does not depend on the trial price except through the demand *weights*; it is zero only if no restricted exporter is a preferred source for any positive demand. Scan over all 3 x 144 steps:

| crop | episode | n | n_free_crosses_twin | n_block_frac_zero | n_u_anom_zero | n_calm_reachable | max_hypothetical_jump |
|---|---|---|---|---|---|---|---|
| maize | 2007/08 | 44 | 0 | 22 | 8 | 0 | 18.66 |
| maize | 2010/11 | 42 | 0 | 0 | 20 | 0 | 45.99 |
| maize | calm | 58 | 7 | 14 | 30 | 2 | 59.31 |
| rice | 2007/08 | 44 | 30 | 14 | 18 | 0 | 153.8 |
| rice | 2010/11 | 42 | 2 | 0 | 41 | 0 | 153.8 |
| rice | calm | 58 | 12 | 10 | 46 | 3 | 153.8 |
| wheat | 2007/08 | 44 | 7 | 16 | 5 | 0 | 71.38 |
| wheat | 2010/11 | 42 | 6 | 0 | 35 | 0 | 83.37 |
| wheat | calm | 58 | 16 | 10 | 44 | 2 | 93.98 |

Steps where the calm branch is reachable by any trial price: **7 of 432**. Where it is not reachable, the L666-669 conditional is dead code for the fixed point and cannot create a jump. `hypothetical_jump` = `(1-smooth)*trade_w*|p_trade - p0|` is what the jump in `G` WOULD be if the branch did fire; its max over all steps is 153.8 $/t, so the hazard is real in magnitude and only unreachability is protecting the solve.

## Artifacts

- `diagnostics/gate0_prep/a3/demand_gap.csv` (7776 rows: crop × step × country)
- `diagnostics/gate0_prep/a3/demand_gap_world.csv` (432 rows: crop × step, incl. Task-2 columns)
- `diagnostics/gate0_prep/a3/g_lipschitz.csv`
- `diagnostics/gate0_prep/a3/g_wide_scan.csv`
- `diagnostics/gate0_prep/a3/g_calm_boundary.csv`
- `diagnostics/gate0_prep/a3/g_all_steps.csv` (432 rows)
- `diagnostics/gate0_prep/a3/g_grid_refinement.csv`
- `diagnostics/gate0_prep/a3/g_calm_reachability.csv` (432 rows)
- `diagnostics/gate0_prep/a3/replica_verification.csv`
- `figures/scratch/a3/g_curve_wheat.png`
- `figures/scratch/a3/g_curve_wide_wheat.png`
- `figures/scratch/a3/g_curve_maize.png`
- `figures/scratch/a3/g_curve_wide_maize.png`
- `figures/scratch/a3/g_curve_rice.png`
- `figures/scratch/a3/g_curve_wide_rice.png`
- `figures/scratch/a3/demand_gap_paths.png`

