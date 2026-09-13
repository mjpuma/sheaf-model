# R0k — adjudicating the p_trade double-update, on current code

## 1. Size and direction of the valuation gap

The gap is (updated ask − allocating ask) weighted by shipments,
as a share of the allocating value. A positive gap through a rally
means the shipped-weighted price is systematically flattered.

| crop | mean gap, all steps | mean gap, 2007/08 rally | mean gap, 2010/11 |
|---|---|---|---|
| wheat | +0.86% | +2.24% | +1.71% |
| maize | +0.41% | +1.90% | +1.22% |
| rice | +3.24% | +3.90% | +2.07% |

## 2. Score impact of valuing shipments at the allocating ask

| crop | metric | current | fixed | Δ | observed |
|---|---|---|---|---|---|
| wheat | corr | +0.728 | +0.687 | -0.040 | — |
| wheat | 2007/08 | x2.28 | x2.09 | -0.197 | x1.82 |
| wheat | 2010/11 | x1.45 | x1.31 | -0.139 | x1.16 |
| maize | corr | +0.778 | +0.792 | +0.014 | — |
| maize | 2007/08 | x2.20 | x2.05 | -0.150 | x1.84 |
| maize | 2010/11 | x1.59 | x1.52 | -0.077 | x1.44 |
| rice | corr | +0.678 | +0.676 | -0.003 | — |
| rice | 2007/08 | x1.72 | x1.54 | -0.178 | x1.84 |
| rice | 2010/11 | x0.82 | x0.84 | +0.024 | x0.79 |

## 3. Absolute error in the hike ratios, before and after

Whether the fix moves the model toward or away from the observed
ratios, summed over both windows and all three crops.

| crop | window | |error| current | |error| fixed |
|---|---|---|---|
| wheat | 2007/08 | 0.467 | 0.270 |
| wheat | 2010/11 | 0.294 | 0.155 |
| maize | 2007/08 | 0.367 | 0.216 |
| maize | 2010/11 | 0.150 | 0.073 |
| rice | 2007/08 | 0.116 | 0.294 |
| rice | 2010/11 | 0.027 | 0.051 |
| **total** | | **1.421** | **1.060** |

## 4. Assertions under the fix

- wheat: ['PASS', 'PASS', 'PASS', 'PASS']
- maize: ['PASS', 'PASS', 'PASS', 'PASS']
- rice: ['PASS', 'PASS', 'PASS', 'PASS']

