# Long-term paper stack (collaborator feedback, 2026-08-24)

Feedback from Kilian / Christian (and related) on uses of SHEAF. This is the
**destination**. Gate 0 is still the next mile. Do not skip ahead.

## Papers

| ID | Question | Now / next / later |
|---|---|---|
| **P1** | Reproduce observed **price, consumption, and trade** over crisis years (then decades) | **Now (Gate 0).** Agrimate bar: 2006–11, 24 steps/yr, per crop. Expand scoring beyond Pink Sheet to PSD consumption and coarse trade signs. Decades after crises hindcast. |
| **P3** | Empirically validate **wheat–maize–rice substitution** vs 2007/08 spillovers | **Next.** Agrimate cannot do this (single commodity). Blocked until P1 is green per crop. |
| **Cal** | Constrain behavioral + strategic parameters | **Alongside P1–P3.** See below. Kilian’s point stands: extra behavior needs a plan, not a grid search on crises. |
| **P4** | Policy: exporters restrict *just enough* for domestic food security, minimizing importer harm; **club of the willing** if not all join | **After P1 is honest.** Same game layer, **normative / constrained-welfare** objective — not “who restricted in 2010.” Illustrative parameters OK if labeled. |
| **P5** | Game theory: cooperation vs protectionism; **social tipping** | **After P4 setup.** Vary cooperation / food-security weights. Current IBR is non-cooperative only. |
| **P2** | Does a realistic network **emerge** from costs and prices without prescribing FAOSTAT E0? | **Later, optional.** Gate 0 **prescribes** Armington on FAOSTAT E0. Say so in P1. P2 is a different paper. |

Compliment (theory-aligned, spillovers, restriction game, fast iteration) describes
the **stack**, not a license to skip P1.

## Calibration plan (honest)

| Layer | What | How constrained | Not allowed |
|---|---|---|---|
| Gate 0 / P1 | `CropParams`: ε literature; STU literature; η, ω, κ, ask gains **reduced-form sign-constrained** | Shared across years; **not** fit per crisis. Official hindcast = Agrimate split (harvest ± AMIS, mean flex). USA maize industrial = structural RFS residual. | Crisis dummies; 2008-only κ |
| P3 | Cross-price / `subst_scale` | Literature own-price; substitution strength from 2007/08 **held-out** grain or from independent estimates | Fitting all three crises jointly then claiming validation |
| Level 2 / P4–P5 | Food-security weights, price triggers, cooperation | **Train** on one crisis window, **score** the other (or pooled structural). P4 may use labeled illustrative knobs for a mechanism paper | Estimating the game on the same episode used as the result |

Reduced-form `CropParams` and illustrative `sheaf/calibration.py` are **not**
an estimated model. A P4 policy paper can still run if P1 is credible and the
appendix lists what was not estimated.

## Sequence (do not skip)

```
P1  Gate 0 per crop  →  Agrimate-matched hindcast (price + consumption + trade signs)
        ↓
P3  Substitution on this spine
        ↓
Cal Written: structural / literature / estimated; train/hold-out for the game
        ↓
P4  Cooperative τ vs Nash; club of the willing (illustrative OK)
P5  Tipping: cooperation vs food-security weights
        ↓
P2  Endogenous network (optional; not required for P1/P3/P4)
```

## Gate 0 official split (P1 scoring)

Agrimate Figs. 3–4 / G.1–G.2:

1. baseline (climatology harvest, no AMIS)
2. production anomalies only
3. harvest + AMIS (`use_demand=False` except USA maize industrial)

Year-by-year world food/feed PSD is a **sensitivity**, not the headline series.
P1 also reports: world consumption vs PSD, MY-end stocks vs PSD, exporter
shipment signs under AMIS.

## Explicitly not Gate 0

- P2 endogenous network
- P3 substitution fitting
- P4/P5 cooperative / tipping game
- Fitting Agrimate’s private price series
