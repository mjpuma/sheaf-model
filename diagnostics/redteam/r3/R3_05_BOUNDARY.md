# R3-05 - the calendar-boundary price artefact

| crop | variant | max 1-step |dp/p| | at | max p | min p | mean |dp/p| at Dec->Jan boundaries |
|---|---|---|---|---|---|---|
| wheat | V0 | 12.3% | 2007-03 | 536 | 185 | 2.59% |
| wheat | V1 | 12.6% | 2007-03 | 538 | 186 | 2.55% |
| maize | V0 | 33.4% | 2006-11 | 325 | 92 | 1.65% |
| maize | V1 | 12.8% | 2006-12 | 328 | 92 | 2.00% |
| rice | V0 | 10.9% | 2007-10 | 902 | 307 | 8.77% |
| rice | V1 | 11.0% | 2007-10 | 902 | 307 | 8.83% |

Note: the boundary column averages the Dec-2nd-half -> Jan-1st-half step, which is where `_apply_harvest_scalars` switches the annual anomaly multiplier.

