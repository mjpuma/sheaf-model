# R3-01 - Gate 0 look-ahead horizon and information content

Agrimate reference (supplement Eq. D.1, Tbl. D.1, Tbl. F.1): N_year=24, N_for=6, tau_for=4.8 steps.

Weight Agrimate puts on the REALISED future harvest by lag n:

| lag n (steps) | 0 | 2 | 4 | 6 | 8 | 10 | 12 | 14 | 16 | 18 | 20 | 22 | 24 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Agrimate w_n | 0.999 | 0.993 | 0.921 | 0.500 | 0.079 | 0.007 | 0.001 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

## wheat  (phi = 0.55)

- lean horizon h_t over T=144 steps: min 1, median 5, mean 5.79, max 14
- share of steps with h_t > 6 (Agrimate N_for): 37.5%
- share of steps with h_t > 9 (Agrimate w<0.03): 24.3%
- mean number of forward lags per step beyond n=8: 0.90
- |realised-anomaly information| inside the forward window, MMT-equivalent per step:
    SHEAF (flat phi)      mean   1.847
    Agrimate (decaying w) mean   2.833
    ratio SHEAF/Agrimate  x0.652
- lag-0 incoherence: avail_t uses H_t at weight 1.00 but the lean gap subtracts H_exp_t = phi*H_t + (1-phi)*H_seas_t; mean |(1-phi)*(H_t - H_seas_t)| = 0.808 MMT/step

## maize  (phi = 0.50)

- lean horizon h_t over T=144 steps: min 1, median 7, mean 8.00, max 19
- share of steps with h_t > 6 (Agrimate N_for): 55.6%
- share of steps with h_t > 9 (Agrimate w<0.03): 39.6%
- mean number of forward lags per step beyond n=8: 2.50
- |realised-anomaly information| inside the forward window, MMT-equivalent per step:
    SHEAF (flat phi)      mean   2.291
    Agrimate (decaying w) mean   2.529
    ratio SHEAF/Agrimate  x0.906
- lag-0 incoherence: avail_t uses H_t at weight 1.00 but the lean gap subtracts H_exp_t = phi*H_t + (1-phi)*H_seas_t; mean |(1-phi)*(H_t - H_seas_t)| = 0.871 MMT/step

## rice  (phi = 0.55)

- lean horizon h_t over T=144 steps: min 1, median 4, mean 5.06, max 11
- share of steps with h_t > 6 (Agrimate N_for): 30.6%
- share of steps with h_t > 9 (Agrimate w<0.03): 17.4%
- mean number of forward lags per step beyond n=8: 0.49
- |realised-anomaly information| inside the forward window, MMT-equivalent per step:
    SHEAF (flat phi)      mean   0.556
    Agrimate (decaying w) mean   0.788
    ratio SHEAF/Agrimate  x0.706
- lag-0 incoherence: avail_t uses H_t at weight 1.00 but the lean gap subtracts H_exp_t = phi*H_t + (1-phi)*H_seas_t; mean |(1-phi)*(H_t - H_seas_t)| = 0.180 MMT/step

