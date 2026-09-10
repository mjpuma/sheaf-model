# R0e — the negative-accessible-stock regime

## 1. Confirming the mechanism

| crop | steps with F<0 | worst F | F_twin there | ratio there | price step before/after | 0.05*sum(safety) |
|---|---|---|---|---|---|---|
| wheat | 0/144 | 22.6 | 25.1 | 1.09 | 202.0 -> 198.9 $/t | 6.44 MMT |
| maize | 1/144 | -15.2 | 207.1 | 35.10 | 95.5 -> 393.9 $/t | 6.52 MMT |
| rice | 33/144 | -36.8 | -36.8 | 1.01 | 342.0 -> 341.9 $/t | 3.92 MMT |

The ratio in the negative regime is of order F_twin / (0.05*sum(
safety)), which is a property of the regulariser rather than of
scarcity. Confirmed if the ratio above is close to that quotient.

## 2. A bounded alternative

Denominator floored at 10% of physical world stock, which cannot go
negative, instead of shifted by an unbounded state-dependent term.
One new constant, no new free parameter beyond the 0.10 floor, and
the unbounded branch disappears. This is a PROBE, not a proposal.

| crop | metric | published | bounded ratio | Δ |
|---|---|---|---|---|
| wheat | corr | +0.720 | +0.720 | +0.000 |
| wheat | 2007/08 | x2.27 | x2.27 | +0.000 |
| wheat | 2010/11 | x1.45 | x1.45 | +0.000 |
| maize | corr | +0.712 | +0.781 | +0.070 |
| maize | 2007/08 | x1.97 | x2.22 | +0.245 |
| maize | 2010/11 | x1.70 | x1.61 | -0.084 |
| rice | corr | +0.678 | +0.728 | +0.051 |
| rice | 2007/08 | x1.72 | x2.40 | +0.678 |
| rice | 2010/11 | x0.82 | x1.11 | +0.293 |

## 3. Does the bounded ratio remove the fragility?

Same ~1% recalibration probe as R0c/R0d, on the bounded version.

| crop | version | end 2011 | end 2012 | end 2013 | spread |
|---|---|---|---|---|---|
| wheat | published | +0.720 | +0.719 | +0.714 | **0.006** |
| wheat | bounded | +0.720 | +0.719 | +0.714 | **0.006** |
| maize | published | +0.712 | +0.276 | +0.832 | **0.557** |
| maize | bounded | +0.781 | +0.818 | +0.840 | **0.059** |
| rice | published | +0.678 | +0.678 | +0.678 | **0.000** |
| rice | bounded | +0.728 | +0.728 | +0.728 | **0.001** |

## Reading

The probe earns consideration only if it both (a) removes the
unbounded branch and the 4x transient, and (b) collapses the maize
spread, without wrecking the scores. If it collapses the spread but
costs a lot of correlation, that is a real trade and belongs in front
of the coauthors, not in a silent commit.

