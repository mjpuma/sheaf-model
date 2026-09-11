# R0g — is the 0.10 floor a knob?

Sweeping the floor coefficient over a factor of eight. Wheat and
rice never enter the branch, so only maize can move.

| floor | maize corr | maize 2007/08 | maize 2010/11 | maize spread | wheat corr | rice corr |
|---|---|---|---|---|---|---|
| 0.050 | +0.788 | x2.20 | x1.62 | 0.060 | +0.720 | +0.678 |
| 0.075 | +0.781 | x2.19 | x1.62 | 0.052 | +0.720 | +0.678 |
| 0.100 | +0.781 | x2.22 | x1.61 | 0.051 | +0.720 | +0.678 |
| 0.150 | +0.780 | x2.23 | x1.61 | 0.053 | +0.720 | +0.678 |
| 0.200 | +0.774 | x2.23 | x1.62 | 0.058 | +0.720 | +0.678 |
| 0.400 | +0.772 | x2.24 | x1.62 | 0.060 | +0.720 | +0.678 |

Published maize for comparison: +0.712 / x1.97 / x1.70, spread 0.557.
Observed maize: x1.84 (2007/08), x1.44 (2010/11).

## How often does the branch fire?

- wheat: F < 0 <= F_twin at **0/144** steps
- maize: F < 0 <= F_twin at **1/144** steps
- rice: F < 0 <= F_twin at **0/144** steps

## Does the fix survive ask_rival = 0?

A2 established that ask_rival has no surviving justification but is
load-bearing for amplitude. If the fix only works at ask_rival =
0.80 it is entangled with a parameter that may not survive.

| crop | ask_rival | published | with fix |
|---|---|---|---|
| wheat | 0.00 | +0.685 | +0.685 |
| wheat | 0.80 | +0.720 | +0.720 |
| maize | 0.00 | +0.414 | +0.522 |
| maize | 0.80 | +0.712 | +0.781 |
| rice | 0.00 | +0.342 | +0.342 |
| rice | 0.80 | +0.678 | +0.678 |

## Verdict criterion

The fix is defensible if maize's correlation and fragility are flat
across the floor sweep. It is a knob, and should be rejected, if the
score tracks the coefficient. Note that a floor which is never
binding for two of three crops cannot be a fitted parameter for
them -- the relevant question is entirely about maize.

