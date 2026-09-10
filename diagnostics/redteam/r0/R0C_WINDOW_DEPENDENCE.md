# R0c — decomposing SHEAF's window dependence

## Channel A — the reference objects are in-sample means

How much the calibrated objects move when end_year goes 2011 to 2012,
with start_year fixed. These are the same physical years in both runs.

| crop | Δ p0 | Δ sum(C_ann) | Δ sum(safety) | Δ H_seas over common steps | Δ stock0 |
|---|---|---|---|---|---|
| wheat | +0.000 $/t | +6.2 MMT | +1.23 MMT | max |Δ| 0.4959 MMT | max |Δ| 1.723 MMT |
| maize | +0.000 $/t | +10.0 MMT | +1.60 MMT | max |Δ| 2.5649 MMT | max |Δ| 5.215 MMT |
| rice | +0.000 $/t | +3.8 MMT | +0.69 MMT | max |Δ| 0.1902 MMT | max |Δ| 0.616 MMT |

If these are nonzero, R0b's extended-window test was confounded and
its maize swing cannot be attributed to the horizon. More important,
it means the scored path is a function of the window chosen.

## Channel B — truncation alone, everything else held fixed

Lean-window inputs padded with a repeat of the final year, so the
horizon is never clipped. Identical calibration, identical forcing,
identical scored months.

| crop | metric | published | horizon padded | Δ |
|---|---|---|---|---|
| wheat | corr | +0.720 | +0.728 | +0.008 |
| wheat | 2007/08 | x2.27 | x2.27 | -0.000 |
| wheat | 2010/11 | x1.45 | x1.45 | -0.001 |
| maize | corr | +0.712 | +0.716 | +0.004 |
| maize | 2007/08 | x1.97 | x1.98 | +0.012 |
| maize | 2010/11 | x1.70 | x1.70 | +0.003 |
| rice | corr | +0.678 | +0.678 | +0.000 |
| rice | 2007/08 | x1.72 | x1.72 | +0.000 |
| rice | 2010/11 | x0.82 | x0.82 | -0.000 |

## Reading

Channel B is the narrow, fixable artifact: pad the lean window and
the last year stops seeing a short horizon. Channel A is the larger
question, and it is not a bug -- using in-sample means for the
climatology is a deliberate and disclosed choice. But it does mean
the headline scores are conditional on the 2006-2011 window, and if
Channel A moves a score by more than Channel B, the honest
robustness statement is about the window, not the horizon.

