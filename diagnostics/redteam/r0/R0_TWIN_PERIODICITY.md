# R0 — is the SHEAF twin annually periodic?

Agrimate's baseline enforces a periodicity condition: a year's
beginning storage equals its ending storage. SHEAF's twin is a
forward climatological simulation with no such condition. Below,
what the twin actually does.

## wheat

| model year | world stock at year start (MMT) | year-end (MMT) | drift over year | mean accessible stock F_twin |
|---|---|---|---|---|
| 2006 | 226.1 | 262.9 | +36.8 | 101.9 |
| 2007 | 240.5 | 268.6 | +28.2 | 110.7 |
| 2008 | 246.2 | 271.3 | +25.1 | 114.3 |
| 2009 | 248.8 | 272.7 | +23.9 | 116.1 |
| 2010 | 250.2 | 273.3 | +23.1 | 117.0 |
| 2011 | 250.8 | 267.6 | +16.8 | 169.9 |

- world stock, first step 226.1 MMT, last step 267.6 MMT: net drift **+18.4%** over 6 model years
- annual-mean accessible stock F_twin by year: 101.9, 110.7, 114.3, 116.1, 117.0, 169.9
- spread across years: 66.8% (a periodic baseline would be 0%)
- correlation of the within-year F_twin shape, year 2 vs final year: +0.681 (1.0 would mean the seasonal cycle repeats exactly)

## maize

| model year | world stock at year start (MMT) | year-end (MMT) | drift over year | mean accessible stock F_twin |
|---|---|---|---|---|
| 2006 | 499.4 | 563.8 | +64.3 | 222.3 |
| 2007 | 526.6 | 581.2 | +54.6 | 245.6 |
| 2008 | 543.2 | 589.9 | +46.7 | 258.0 |
| 2009 | 551.4 | 593.9 | +42.6 | 263.9 |
| 2010 | 555.2 | 595.8 | +40.6 | 266.6 |
| 2011 | 556.9 | 594.4 | +37.5 | 310.7 |

- world stock, first step 499.4 MMT, last step 594.4 MMT: net drift **+19.0%** over 6 model years
- annual-mean accessible stock F_twin by year: 222.3, 245.6, 258.0, 263.9, 266.6, 310.7
- spread across years: 39.7% (a periodic baseline would be 0%)
- correlation of the within-year F_twin shape, year 2 vs final year: +0.750 (1.0 would mean the seasonal cycle repeats exactly)

## rice

| model year | world stock at year start (MMT) | year-end (MMT) | drift over year | mean accessible stock F_twin |
|---|---|---|---|---|
| 2006 | 104.3 | 126.2 | +22.0 | 20.6 |
| 2007 | 107.8 | 125.9 | +18.1 | 20.9 |
| 2008 | 107.5 | 125.9 | +18.4 | 20.8 |
| 2009 | 107.5 | 125.9 | +18.4 | 20.9 |
| 2010 | 107.5 | 125.9 | +18.4 | 20.9 |
| 2011 | 107.5 | 124.4 | +16.9 | 39.7 |

- world stock, first step 104.3 MMT, last step 124.4 MMT: net drift **+19.3%** over 6 model years
- annual-mean accessible stock F_twin by year: 20.6, 20.9, 20.8, 20.9, 20.9, 39.7
- spread across years: 92.9% (a periodic baseline would be 0%)
- correlation of the within-year F_twin shape, year 2 vs final year: +0.723 (1.0 would mean the seasonal cycle repeats exactly)

## Reading

A drifting twin is not automatically a defect: SHEAF's reference is
documented as a trajectory rather than a constant, and a two-year
spin-up is a deliberate choice. The question is whether the drift is
small enough that r_t reads as scarcity rather than as baseline
transient. If the annual-mean accessible stock moves by more across
the twin's own years than a crisis moves it, then the denominator is
doing work the numerator was supposed to do, and the honest fix is
either Agrimate's periodicity condition or a longer spin-up.

