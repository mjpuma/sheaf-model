# A2c — is the map monotone in harvest?

## Channel decomposition, permanent uniform shortfall

Means over the last four years. `excess` is grain above the warehouse
cap, of which a fraction lambda_W is removed each step, so it is the
size of the drawdown channel.

### wheat
| shortfall | mean p | mean free | mean stock | mean excess | mean offers | mean shipped |
|---|---|---|---|---|---|---|
| -0% | 213.5 | 129.3 | 254.9 | 11.9 | 78.95 | 3.86 |
| -1% | 199.2 | 116.3 | 241.9 | 9.9 | 72.11 | 3.90 |
| -2% | 209.5 | 114.1 | 239.9 | 9.3 | 70.56 | 3.88 |
| -5% | 245.0 | 107.9 | 233.9 | 7.8 | 66.22 | 3.80 |
| -10% | 326.2 | 98.7 | 225.1 | 5.7 | 59.38 | 3.67 |

### maize
| shortfall | mean p | mean free | mean stock | mean excess | mean offers | mean shipped |
|---|---|---|---|---|---|---|
| -0% | 135.4 | 274.8 | 416.0 | 37.5 | 193.02 | 3.25 |
| -1% | 108.0 | 202.6 | 344.3 | 19.5 | 136.22 | 4.18 |
| -2% | 111.2 | 199.1 | 341.2 | 18.5 | 132.98 | 4.17 |
| -5% | 122.4 | 189.0 | 332.3 | 15.8 | 123.38 | 4.13 |
| -10% | 146.1 | 171.6 | 317.1 | 11.2 | 107.14 | 4.05 |

### rice
| shortfall | mean p | mean free | mean stock | mean excess | mean offers | mean shipped |
|---|---|---|---|---|---|---|
| -0% | 339.0 | 25.6 | 75.5 | 19.1 | 14.27 | 1.07 |
| -1% | 354.7 | 24.9 | 74.9 | 18.5 | 13.97 | 1.06 |
| -2% | 373.5 | 24.5 | 74.7 | 18.1 | 13.65 | 1.04 |
| -5% | 440.7 | 23.7 | 74.3 | 17.4 | 12.80 | 0.99 |
| -10% | 586.5 | 21.7 | 73.1 | 15.8 | 11.53 | 0.93 |

## Transient shortfall (one year only)

Shortfall applied to year 2 of the window only, which is closer to
how harvest anomalies actually enter. Response measured as the peak
price in the 12 steps from the start of the shock, over the
unshocked peak in the same steps.

| crop | -1% | -2% | -5% | -10% | monotone? |
|---|---|---|---|---|---|
| wheat | x0.898 | x0.954 | x0.988 | x1.016 | **NO** |
| maize | x0.755 | x0.756 | x0.758 | x0.761 | **NO** |
| rice | x1.088 | x1.108 | x1.191 | x1.336 | yes |

