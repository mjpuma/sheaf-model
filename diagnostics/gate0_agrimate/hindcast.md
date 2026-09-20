# G0-H — 2006–11 wheat hindcast (P8 / S5)

**Explicit sourced shortfall versus Agrimate Fig. 4.** Independent
implementation, not a replication. Not a retune. `wheat_params()`
stay αI=3.2, p_sto=0.1, xmin=0.2. Bai α_foreign=10 is listed in the
P6 OAT and **not adopted** (it raises the already-too-large spike).
L1–L8 stay rejected. G1/G2 stay blocked. This is **not R11**: S5
re-scores the S1 member-sum CSVs; the NLP runner was not re-run.

Numbers are from `diagnostics/gate0_agrimate/` three-scenario CSVs
(spin-up 2003–05, score 2006–11, A8 member-sum) and P7 author series.

## G0-U items 1–3 (pass rule before judging historical fit)

1. **Source fidelity.** Met for retrieved Zenodo 14022004 code with
   labelled S3/S4/A1–A6/N5. Fig. 4 NetCDF is a different executable
   (AgrimateEU28+Egypt, FAO anomalies, α_foreign=3.5, ζ=1, N_for=6).
2. **Numerical reliability.** Feasible (failed/fallback 0, residual 0)
   but **not** first-order stationary: harvest+AMIS unconverged
   2304/5832 (N5).
   Counted, not papered over.
3. **Undisturbed dynamics.** Seasonal *shape* repeats (corr 0.98) but
   the annual-mean world-price ratio 2011/2006 is **1.444**.
   Author Fig. 4 baseline on the same window is 1.004.
   P2 drift is unexplained. Not a price pin.

Items 1–3 do **not** all hold. Item 5 is still reported, as an
explicit shortfall, not as a replication claim.

## Quiet-year (2006) price level

Harvest+AMIS 2006 mean is **$81.5/t** vs Pink
Sheet **$213.5/t** (ratio
0.38; about 38% of the observed quiet-year
level). Undisturbed is lower still
($45.8/t) because 2006 is a trough on
the drifting unforced path, not a calibrated intercept.

Against Agrimate Fig. 4d the same year is host D.7 index
**0.381**
(USD/p0) vs author volume-weighted index **1.183**.
The host is not on Agrimate's quiet-year scale. Do not pin p_w to the
2006 Pink mean to close this (hard stop).

## 2007/08 hike ratio

Same `_hike` helper as `score_prices.csv` (3-month rolling peak in
2006–08 over 2006 mean):

| series | 2008 hike | 2006 mean | 2007–08 peak month |
|---|---:|---:|---|
| host harvest+AMIS | ×3.71 | $81.5 | 2008-06 |
| host harvest-only | ×3.85 | $81.5 | 2008-06 |
| Pink Sheet | ×1.88 | $213.5 | 2008-03 |
| Agrimate Fig. 4d harvest+AMIS | ×1.62 | index 1.183 | 2008-05 |

Host overshoots Pink (×3.71 vs ×1.88) **and** overshoots Agrimate
(×3.71 vs ×1.62).
Peak timing is also wrong: host crisis peak is
**2008-06** (harvest-calendar spike); Pink peaks
**2008-03**; author Fig. 4d peaks **2008-05**.
Bai α_foreign=10 is not a remedy: the P6 short-window OAT moves the
2008 hike from ×2.31 to ×3.58 and blows `pidx_max` to 473. That is
the wrong direction. Not adopted.

## Seasonal path, not only correlation

Full-window corr vs Pink is **near zero** (harvest+AMIS 0.014).
That is a path failure, not a noisy +0.5. Year-demeaned corr is
negative (-0.065).

Month-of-year mean profile (2006–11):

| series | peak month | trough month | max/min | moy corr vs Pink | moy corr vs author |
|---|---:|---:|---:|---:|---:|
| host undisturbed | 6 | 9 | 26.92 | -0.614 | 0.944 |
| host harvest | 6 | 10 | 13.82 | -0.640 | 0.900 |
| host harvest_amis | 6 | 9 | 16.80 | -0.655 | 0.897 |
| Pink Sheet | 9 | — | 1.07 | 1 | — |
| Agrimate Fig. 4d (harvest+AMIS) | 5 | — | 1.45 | — | 1 |

Host within-year amplitude is **16.8×** on the month-of-year mean
versus Pink **1.07×**
and Agrimate Fig. 4d **1.45×**. The host
shares Agrimate's northern-harvest *calendar* (May–June peak; moy
corr vs author 0.90) and inverts Pink
(moy corr -0.65). September 2007 is the
clearest single-month counterexample: host harvest+AMIS
**$14.3/t** vs Pink **$342/t**.
Agrimate's published wheat path does not collapse off-season like
that. Correlation alone would hide this.

Figure: `figures/fig6_hindcast_seasonal.png`.

## Production anomalies vs USDA

Harvest / harvest+AMIS production corr vs USDA world is
**0.803** (prompt ballpark +0.80). Anomaly
corr on this six-year window is the same number (0.803):
the series are short and the mean offset is nearly constant.
Level: host 661.4 MMT vs USDA
519.4 (ratio 1.273).
Undisturbed production is the repeating 2007–09 mean, so corr vs
USDA is undefined/zero — as designed. A8 member-sum (S1) raised the
27-node production sum versus the rejected pooled-mean host.

Vs Agrimate Fig. 4 harvest+AMIS, production corr is 0.999 at different
levels (host 661 vs author 624 MMT) because A1 is USDA PSD, not
FAOSTAT Food Balances, and the region lists differ (Brazil named
here; Egypt split there).

## Stock *level* bias vs stock *anomaly* corr

The P8 prompt's “~3× USDA world / anomaly corr ~+0.94” is the
**pre-P2** echo-bug number (exporter consumer stocks ate XI).
After B1 (T* delivery), harvest+AMIS ending stocks are
**259.4 MMT vs USDA 157.4 = 1.65×**, not 3×. Level corr
**0.831**; anomaly corr
**0.831** (again equal on this window).
Harvest-only is 1.52× with corr
0.912.

Against Agrimate Fig. 4 the host is 259 vs author 325 MMT harvest+AMIS, so the remaining USDA gap is not “the host holds three worlds of grain.” Coverage (27 nodes vs world PSD) and
A1 still explain part of the level offset. Do not fit xmin or p_sto
to close it.

Consumption corr vs USDA is weak (-0.390);
mean level is close (ratio
1.248).

## Harvest-only vs harvest+AMIS attribution

Production is identical by construction. AMIS wheat Δ binds 491
region-steps (Argentina, China, India, Kazakhstan, Russia, Ukraine,
Northern Africa; max 0.95). The two price paths are **not** identical.

- 2007 means are almost the same ($101.9 vs
  $101.9). June 2007 is
  $308 harvest-only vs
  $312 harvest+AMIS. The 2007 spike is
  **harvest-driven**.
- 2008 means: $126.9 vs
  $119.6. May 2008 is
  $316 vs $342
  (max |Δ| $136 at
  2011-07). On the member-sum host the largest
  harvest vs harvest+AMIS price gap is not a 2008 spring spike.
- Ukraine 2007 exports 6.7 → 14.5 MMT with AMIS; 2007 consumption 10.09 → 2.83 MMT (sign flipped vs the pre-S1 pooled-mean host). AMIS still moves the exporter. It does not repair world-price *path* or *level*.

Mean |price harvest+AMIS − harvest| over 2006–11 is
$17.0/t.

## Comparison to Agrimate published wheat Fig. 4

P7 unpacked Zenodo 10688435. Headlines from `fig4.md`, restated as
a hindcast verdict (S5 re-score on the S1 member-sum CSVs):

- Quiet-year index: host 0.38 vs author 1.18.
- 2008 hike: host ×3.71 vs author ×1.62 vs Pink ×1.88. Agrimate is
  the closer of the two models to Pink on this metric; the host is
  not comparable to Agrimate.
- Seasonal amplitude: host 16.8× vs author 1.45× vs Pink 1.07×.
  Host matches Agrimate's *calendar* (moy corr 0.90) and misses
  Agrimate's *amplitude*.
- Undisturbed: author last/first 1.004; host 1.444 (S2).
- Production anomalies track at USDA vs FAO levels.
- This is **not** a bit-reproduction: different region list, FAO vs
  USDA (A1), α_foreign 3.5 vs 3.2, ζ=1 vs 0, N_for 6 vs 3 months,
  git `old-demand-dynamics` vs 14022004. Labelling that mismatch
  does not make the host's ×3.71 hike a success.

## Verdict

Sourced shortfall. Gate 0 wheat is **not** at the publication bar
on historical performance (DEVELOPMENT item 5) and still fails
item 3 (undisturbed). Items 1–3 evidence did **not** newly pass
(unconverged still N5; last/first still >1.1). Do not restore L1–L8.
Do not adopt Bai α_foreign=10. Do not pin 2006. Do not start G1.
Regional USDA (P9): `regional.md` (coverage labelled; no xmin/p_sto
fit). P11 prescribed-Δ: `pulse.md` (8-run 2008 clean; not 36; not G2).
P12 methods note: `methods.md` (written; **not accepted** as the
SHEAF market section). S6 is not next: items 1–3 still fail.

## Files

- `score_hindcast_seasonal.csv` — path metrics used above
- `score_hindcast_quantities.csv` — USDA level vs anomaly
- `figures/fig6_hindcast_seasonal.png`
- `fig4.md` — P7/S5 author-series score
- `regional.md` — P9 named-node USDA (coverage, not a fit)

