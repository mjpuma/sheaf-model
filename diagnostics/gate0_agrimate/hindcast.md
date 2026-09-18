# G0-H — 2006–11 wheat hindcast (P8)

**Explicit sourced shortfall versus Agrimate Fig. 4.** Independent
implementation, not a replication. Not a retune. `wheat_params()`
stay αI=3.2, p_sto=0.1, xmin=0.2. Bai α_foreign=10 is listed in the
P6 OAT and **not adopted** (it raises the already-too-large spike).
L1–L8 stay rejected. G1/G2 stay blocked.

Numbers are from `diagnostics/gate0_agrimate/` three-scenario CSVs
(spin-up 2003–05, score 2006–11) and P7 author series. The runner
was not re-run.

## G0-U items 1–3 (pass rule before judging historical fit)

1. **Source fidelity.** Met for retrieved Zenodo 14022004 code with
   labelled S3/S4/A1–A6/N5. Fig. 4 NetCDF is a different executable
   (AgrimateEU28+Egypt, FAO anomalies, α_foreign=3.5, ζ=1, N_for=6).
2. **Numerical reliability.** Feasible (failed/fallback 0, residual 0)
   but **not** first-order stationary: harvest+AMIS unconverged
   1743/5832 (N5). Counted, not papered over.
3. **Undisturbed dynamics.** Seasonal *shape* repeats (corr 0.98) but
   the annual-mean world-price ratio 2011/2006 is **1.63**. Author
   Fig. 4 baseline on the same window is 1.004. P2 drift is
   unexplained. Not a price pin.

Items 1–3 do **not** all hold. Item 5 is still reported, as an
explicit shortfall, not as a replication claim.

## Quiet-year (2006) price level

Harvest+AMIS 2006 mean is **$65.3/t** vs Pink
Sheet **$213.5/t** (ratio
0.31; about 31% of the observed quiet-year
level). Undisturbed is lower still
($43.1/t) because 2006 is a trough on
the drifting unforced path, not a calibrated intercept.

Against Agrimate Fig. 4d the same year is host D.7 index
**0.306**
(USD/p0) vs author volume-weighted index **1.183**.
The host is not on Agrimate's quiet-year scale. Do not pin p_w to the
2006 Pink mean to close this (hard stop).

## 2007/08 hike ratio

Same `_hike` helper as `score_prices.csv` (3-month rolling peak in
2006–08 over 2006 mean):

| series | 2008 hike | 2006 mean | 2007–08 peak month |
|---|---:|---:|---|
| host harvest+AMIS | ×4.54 | $65.3 | 2007-06 |
| host harvest-only | ×4.53 | $65.3 | 2007-06 |
| Pink Sheet | ×1.88 | $213.5 | 2008-03 |
| Agrimate Fig. 4d harvest+AMIS | ×1.62 | index 1.183 | 2008-05 |

Host overshoots Pink (×4.54 vs ×1.88) **and** overshoots Agrimate
(×4.54 vs ×1.62). Peak timing is also wrong: host crisis peak is
**2007-06** (harvest-calendar spike); Pink peaks
**2008-03**; author Fig. 4d peaks **2008-05**.
Bai α_foreign=10 is not a remedy: the P6 short-window OAT moves the
2008 hike from ×2.31 to ×3.58 and blows `pidx_max` to 473. That is
the wrong direction. Not adopted.

## Seasonal path, not only correlation

Full-window corr vs Pink is **negative** (harvest+AMIS −0.082).
That is a path failure, not a noisy +0.5. Year-demeaned corr is
still negative (-0.156).

Month-of-year mean profile (2006–11):

| series | peak month | trough month | max/min | moy corr vs Pink | moy corr vs author |
|---|---:|---:|---:|---:|---:|
| host undisturbed | 5 | 9 | 26.40 | -0.613 | 0.953 |
| host harvest | 6 | 9 | 16.62 | -0.633 | 0.899 |
| host harvest_amis | 6 | 9 | 17.81 | -0.639 | 0.908 |
| Pink Sheet | 9 | — | 1.07 | 1 | — |
| Agrimate Fig. 4d (harvest+AMIS) | 5 | — | 1.45 | — | 1 |

Host within-year amplitude is **~18×** on the month-of-year mean
(17.8), versus Pink **1.07×**
and Agrimate Fig. 4d **1.45×**. The host
shares Agrimate's northern-harvest *calendar* (May–June peak; moy
corr vs author 0.91) and inverts Pink
(moy corr -0.64). September 2007 is the
clearest single-month counterexample: host harvest+AMIS
**$2.8/t** vs Pink **$342/t**.
Agrimate's published wheat path does not collapse off-season like
that. Correlation alone would hide this.

Figure: `figures/fig6_hindcast_seasonal.png`.

## Production anomalies vs USDA

Harvest / harvest+AMIS production corr vs USDA world is
**0.795** (prompt ballpark +0.80). Anomaly
corr on this six-year window is the same number (0.795):
the series are short and the mean offset is nearly constant.
Level is close: host 541.5 MMT vs USDA
519.4 (ratio 1.043).
Undisturbed production is the repeating 2007–09 mean, so corr vs
USDA is undefined/zero — as designed.

Vs Agrimate Fig. 4 harvest, production corr is 0.986 at different
levels (host 542 vs author 624 MMT) because A1 is USDA PSD, not
FAOSTAT Food Balances, and the region lists differ (Brazil named
here; Egypt split there).

## Stock *level* bias vs stock *anomaly* corr

The P8 prompt's “~3× USDA world / anomaly corr ~+0.94” is the
**pre-P2** echo-bug number (exporter consumer stocks ate XI).
After B1 (T* delivery), harvest+AMIS ending stocks are
**248.1 MMT vs USDA 157.4 = 1.58×**, not 3×. Level corr
**0.699**; anomaly corr
**0.699** (again equal on this window).
Harvest-only is 1.56× with corr
0.834.

Against Agrimate Fig. 4 the host is *below* author stocks (248 vs
325 MMT harvest+AMIS), so the remaining USDA gap is not “the host
holds three worlds of grain.” Coverage (27 nodes vs world PSD) and
A1 still explain part of the level offset. Do not fit xmin or p_sto
to close it.

Consumption corr vs USDA is weak (0.171);
mean level is close (ratio
1.022).

## Harvest-only vs harvest+AMIS attribution

Production is identical by construction. AMIS wheat Δ binds 491
region-steps (Argentina, China, India, Kazakhstan, Russia, Ukraine,
Northern Africa; max 0.95). The two price paths are **not** identical.

- 2007 means are almost the same ($110.8 vs
  $111.2). June 2007 is
  $385 harvest-only vs
  $388 harvest+AMIS. The 2007 spike is
  **harvest-driven**.
- 2008 means diverge ($49.4 vs
  $85.0). May 2008 is
  $141 vs $335
  (max |Δ| $194 at
  2008-05). AMIS **adds** a 2008 spring spike
  on top of an already-too-large 2007 harvest spike.
- Ukraine 2007 exports 15.0 → 6.0 MMT with AMIS; 2007 consumption
  1.93 → 10.3 MMT. The restriction does what E.4 says on the
  exporter. It does not repair world-price *path* or *level*.

Mean |price harvest+AMIS − harvest| over 2006–11 is
$14.6/t.

## Comparison to Agrimate published wheat Fig. 4

P7 unpacked Zenodo 10688435. Headlines from `fig4.md`, restated as
a hindcast verdict:

- Quiet-year index: host ~0.31 vs author ~1.18.
- 2008 hike: host ×4.54 vs author ×1.62 vs Pink ×1.88. Agrimate is
  the closer of the two models to Pink on this metric; the host is
  not comparable to Agrimate.
- Seasonal amplitude: host ~18× vs author ~1.45× vs Pink ~1.07×.
  Host matches Agrimate's *calendar* (moy corr 0.91) and misses
  Agrimate's *amplitude*.
- Undisturbed: author last/first 1.004; host 1.63 (P2).
- Production anomalies track (corr 0.99) at USDA vs FAO levels.
- This is **not** a bit-reproduction: different region list, FAO vs
  USDA (A1), α_foreign 3.5 vs 3.2, ζ=1 vs 0, N_for 6 vs 3 months,
  git `old-demand-dynamics` vs 14022004. Labelling that mismatch
  does not make the host's ×4.54 hike a success.

## Verdict

Sourced shortfall. Gate 0 wheat is **not** at the publication bar
on historical performance (DEVELOPMENT item 5) and still fails
item 3 (undisturbed). Do not restore L1–L8. Do not adopt Bai
α_foreign=10. Do not pin 2006. Next: P9 regional USDA tables
(coverage, not a fit). P12 methods note waits on an accepted G0-H
picture; this note is that picture.

## Files

- `score_hindcast_seasonal.csv` — path metrics used above
- `score_hindcast_quantities.csv` — USDA level vs anomaly
- `figures/fig6_hindcast_seasonal.png`
- `fig4.md` — P7 author-series score (unchanged)

