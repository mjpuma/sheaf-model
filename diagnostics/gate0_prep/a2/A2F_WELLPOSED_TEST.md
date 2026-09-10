# A2f — a well-posed restriction sign test

Fix under test: leave every equation alone, and take the baseline leg
out of the matched regime with a harvest perturbation of 1e-6, so
that treatment and baseline are priced by the same law. The physical
change is one part per million; the change in what is being compared
is the whole point.

| crop | floor | lift as published | lift, perturbed baseline | verdict at alpha_r=0.8 |
|---|---|---|---|---|
| wheat | +0.05 | +0.675 | +0.964 | PASS |
| rice | +0.05 | +0.924 | +0.832 | PASS |
| maize | +0.00 | +0.019 | +0.312 | PASS |

The perturbation reproduces the like-for-like lift to three decimals,
so it is a drop-in repair for the test. It does not repair the
underlying property: the offer-price law still has no rest point at
the reference (A1b), and the matched run is still pinned by the
conditional. It only stops the sign test from measuring that pin.

## What alpha_r is worth on the well-posed test

| crop | alpha_r | lift, perturbed baseline | floor | verdict |
|---|---|---|---|---|
| wheat | 0.0 | +0.488 | +0.05 | PASS |
| wheat | 0.4 | +0.623 | +0.05 | PASS |
| wheat | 0.8 | +0.964 | +0.05 | PASS |
| rice | 0.0 | +0.160 | +0.05 | PASS |
| rice | 0.4 | +0.447 | +0.05 | PASS |
| rice | 0.8 | +0.832 | +0.05 | PASS |
| maize | 0.0 | +0.047 | +0.00 | PASS |
| maize | 0.4 | +0.151 | +0.00 | PASS |
| maize | 0.8 | +0.312 | +0.00 | PASS |

## Cost of dropping alpha_r on the official scores

The official leg is harvest + AMIS with mean flex demand. Reported so
the price of the simplification is visible. Per CLAUDE.md this is not
a licence to pick whichever value scores best.

| crop | alpha_r | corr | 2007/08 | 2010/11 | observed 07/08 | observed 10/11 |
|---|---|---|---|---|---|---|
| wheat | 0.0 | +0.685 | x1.53 | x1.52 | x1.82 | x1.16 |
| wheat | 0.4 | +0.739 | x1.80 | x1.49 | x1.82 | x1.16 |
| wheat | 0.8 | +0.720 | x2.27 | x1.45 | x1.82 | x1.16 |
| maize | 0.0 | +0.414 | x1.43 | x1.11 | x1.84 | x1.44 |
| maize | 0.4 | +0.553 | x1.64 | x1.25 | x1.84 | x1.44 |
| maize | 0.8 | +0.712 | x1.97 | x1.70 | x1.84 | x1.44 |
| rice | 0.0 | +0.342 | x1.01 | x0.91 | x1.84 | x0.79 |
| rice | 0.4 | +0.629 | x1.25 | x0.93 | x1.84 | x0.79 |
| rice | 0.8 | +0.678 | x1.72 | x0.82 | x1.84 | x0.79 |
