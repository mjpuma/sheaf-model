# R0f — surgical fix for the asymmetric negative-F case

Fires only where F < 0 <= F_twin. Everywhere else the shipped
formula is untouched, so wheat (F never negative) and rice (F and
F_twin negative together) should be bit-identical.

## 1. Is it actually surgical?

| crop | max |Δ price| over 144 steps | steps changed |
|---|---|---|
| wheat | 0.000000 $/t | 0/144 |
| maize | 266.573209 $/t | 122/144 |
| rice | 0.000000 $/t | 0/144 |

## 2. The maize transient

- maize largest one-step move in year 1: **298.4 $/t** published, **31.9 $/t** with the fix
- maize year-1 price range: 91.6-393.9 published, 91.6-134.4 with the fix

## 3. Scores

| crop | metric | published | surgical fix | Δ | observed |
|---|---|---|---|---|---|
| wheat | corr | +0.720 | +0.720 | +0.000 | — |
| wheat | 2007/08 | x2.27 | x2.27 | +0.000 | x1.82 |
| wheat | 2010/11 | x1.45 | x1.45 | +0.000 | x1.16 |
| maize | corr | +0.712 | +0.781 | +0.070 | — |
| maize | 2007/08 | x1.97 | x2.22 | +0.245 | x1.84 |
| maize | 2010/11 | x1.70 | x1.61 | -0.084 | x1.44 |
| rice | corr | +0.678 | +0.678 | +0.000 | — |
| rice | 2007/08 | x1.72 | x1.72 | +0.000 | x1.84 |
| rice | 2010/11 | x0.82 | x0.82 | +0.000 | x0.79 |

## 4. Fragility

| crop | version | end 2011 | end 2012 | end 2013 | spread |
|---|---|---|---|---|---|
| wheat | published | +0.720 | +0.719 | +0.714 | **0.006** |
| wheat | surgical | +0.720 | +0.719 | +0.714 | **0.006** |
| maize | published | +0.712 | +0.276 | +0.832 | **0.557** |
| maize | surgical | +0.781 | +0.818 | +0.832 | **0.051** |
| rice | published | +0.678 | +0.678 | +0.678 | **0.000** |
| rice | surgical | +0.678 | +0.678 | +0.678 | **0.000** |

## 5. Assertions under the fix

- wheat: ['PASS', 'PASS', 'PASS', 'PASS']
- maize: ['PASS', 'PASS', 'PASS', 'PASS']
- rice: ['PASS', 'PASS', 'PASS', 'PASS']

