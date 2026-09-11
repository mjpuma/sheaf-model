# R0i — raw price response to a uniform harvest shortfall

Matched configuration (no AMIS, no shocks, no demand anomaly, no
industrial), so this is the model's own transfer function. Prices in
2010 $/t. A well-behaved market has mean price rising monotonically
with the shortfall.

## after the R0f fix

| crop | −0% | −0.5% | −1% | −2% | −3% | −5% | −7.5% | −10% | −15% |
|---|---|---|---|---|---|---|---|---|---|
| wheat | 213.5 | 193.2 | 197.8 | 207.6 | 218.3 | 242.4 | 280.7 | 333.9 | 458.9 |
| maize | 135.4 | 104.8 | 106.2 | 109.1 | 112.2 | 118.9 | 128.4 | 139.5 | 167.1 |
| rice | 339.0 | 344.8 | 353.5 | 371.7 | 391.6 | 432.3 | 494.6 | 565.3 | 743.3 |

| crop | monotone in the shortfall? | reference p0 |
|---|---|---|
| wheat | **NO** | 213.5 $/t |
| maize | **NO** | 135.4 $/t |
| rice | yes | 339.0 $/t |

## before the R0f fix

| crop | −0% | −0.5% | −1% | −2% | −3% | −5% | −7.5% | −10% | −15% |
|---|---|---|---|---|---|---|---|---|---|
| wheat | 213.5 | 193.2 | 197.8 | 207.6 | 218.3 | 242.4 | 280.7 | 333.9 | 481.3 |
| maize | 135.4 | 104.8 | 106.2 | 109.1 | 112.2 | 118.9 | 128.4 | 139.5 | 167.1 |
| rice | 339.0 | 344.8 | 353.5 | 371.7 | 391.6 | 437.4 | 503.1 | 580.1 | 772.9 |

| crop | monotone in the shortfall? | reference p0 |
|---|---|---|
| wheat | **NO** | 213.5 $/t |
| maize | **NO** | 135.4 $/t |
| rice | yes | 339.0 $/t |

## Reading

A non-monotone or inverted response is a formulation problem, not a
calibration one: it means a scarcer world can be a cheaper world in
this model over some range. Comparing the two panels attributes it
either to the R0f fix or to something older. A1's rest-point finding
predicts the inversion is older than the fix, because the downward
drift in the offer-price law is present in both versions.

For orientation: Agrimate's world-market inverse elasticity is 3.0
(Suppl. D.7.4.1) and its international-market alpha_I is 3.5 (Tbl.
D.8), both on flows, so a 1% shortfall there moves the price by
roughly 3%.

