# R0d — the spin-up transient and the fragility of the maize score

## The transient itself

Largest single-step price move in the first model year, and where the
first year's prices sit relative to the reference.

| crop | p0 | max |Δp| in year 1 | at step | as ratio | year-1 price range |
|---|---|---|---|---|---|
| wheat | 211.4 | 19.1 $/t | 19->20 | x1.09 | 185.0-256.5 $/t |
| maize | 134.4 | 298.4 $/t | 21->22 | x4.13 | 91.6-393.9 $/t |
| rice | 342.4 | 10.8 $/t | 19->20 | x0.97 | 307.1-369.6 $/t |

## Correlation with and without the spin-up year

`end_year` is varied only to perturb the in-sample climatology by
about 1%, exactly as in R0c; the scored months are held fixed. The
question is whether dropping the first model year stabilises the
score.

| crop | scored months | end 2011 | end 2012 | end 2013 | spread |
|---|---|---|---|---|---|
| wheat | 2006-2011 (published) | +0.720 | +0.719 | +0.714 | **0.006** |
| wheat | 2007-2011 (drop spin-up) | +0.689 | +0.687 | +0.684 | **0.005** |
| maize | 2006-2011 (published) | +0.712 | +0.276 | +0.832 | **0.557** |
| maize | 2007-2011 (drop spin-up) | +0.652 | +0.079 | +0.814 | **0.734** |
| rice | 2006-2011 (published) | +0.678 | +0.678 | +0.678 | **0.000** |
| rice | 2007-2011 (drop spin-up) | +0.542 | +0.542 | +0.543 | **0.001** |

## Reading

A score whose spread across a 1% recalibration is comparable to the
score itself is not measuring what it claims to measure. If dropping
the spin-up year collapses the spread, the fix is to score on
2007-2011 -- which is what the twin-identity test already does -- and
the published maize correlation should be restated. If the spread
survives, the fragility is in the maize path itself and is a larger
problem than a scoring convention.

