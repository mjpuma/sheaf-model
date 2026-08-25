# Long-term paper stack (collaborator feedback, 2026-08-24)

Feedback from Kilian / Christian (and related) on uses of SHEAF. This is the
**destination**. Gate 0 / crisis P1 is **accepted** (white paper
`overleaf/gate0_whitepaper/`). Next mile is **P3 substitution**. Do not skip
to the game (P4–P5) or an endogenous network (P2).

## Papers

| ID | Question | Now / next / later |
|---|---|---|
| **P1** | Reproduce observed **price, consumption, and trade** over crisis years (then decades) | **Crisis Gate 0 done.** Agrimate bar 2006–11 + Ukraine-war 2021–23 prices. Consumption and AMIS shipment *signs* scored; leftover *levels* are disclosed, not retuned. Decades after crises remain a later P1 expansion. |
| **P3** | Empirically validate **wheat–maize–rice substitution** vs 2007/08 spillovers | **Gate 1 scored** (`diagnostics/GATE1_PLAN.md`). σ band, not a 2008 fit. Maize 2010 leftover disclosed. Locked Gate 0 `CropParams`. |
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
P1  Gate 0 crisis hindcast  ✓  (2006–11 + Ukraine-war prices; leftovers disclosed)
        ↓
P3  Substitution on this spine   ← **Gate 1 scored** (band, not a fit)
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
P1 also reports: world consumption vs PSD, MY-end stocks vs PSD (world and
world excluding China; rice also excluding India), exporter
shipment signs under AMIS (key restrictors, with vs without AMIS; optional
PSD export signs). Not FAOSTAT bilateral crisis volumes or 28-region trade
maps. Agrimate Fig. 3 is model-implied withheld grain, not observed trade.

## Explicitly not Gate 0

- P2 endogenous network
- P3 substitution fitting
- P4/P5 cooperative / tipping game
- Fitting Agrimate’s private price series
