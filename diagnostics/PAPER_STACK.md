# Research questions (not a paper queue)

Kilian / Christian (and related) listed **uses** of SHEAF — hindcast,
substitution, policy, tipping, endogenous network. Those are questions
the model might answer. They are **not** five papers that must be
written in order, and they are not a license to skip the market.

What actually exists as writeups:

| Note | Question it answers | Status |
|---|---|---|
| Gate 0 (`overleaf/gate0_whitepaper/`) | Can the 24-step market, substitution off and AMIS prescribed, hindcast crisis prices? | **Accepted.** |
| Gate 1 (`overleaf/gate1_whitepaper/`) | Does turning substitution on spill in the right direction without breaking Gate 0? | **Draft written.** Claim frozen. Do not pick σ*. |
| Gate 2 beta (`diagnostics/GATE2_PLAN.md`) | Can one exporter, on that same spine, cut inside the year when a harvest fails and stay open in climatology? | **Mechanism check.** Illustrative types. Not a 2008 score. Clock: `diagnostics/GAME_CLOCK.md`. |

Everything else below is a **question**, not a manuscript name. Any of
them might end up as a section, an appendix, a later note, or never.

## Open questions (downgraded)

| Question | What it is | What it is not |
|---|---|---|
| **Who restricts, and when?** | Positive game on the 24-step spine (Headey 2011): types slow, actions `τ_t`. Train on one window, score another — if we ever estimate. | Not an annual Nash in `core.py`. Not “write paper P4.” The beta is a one-player mechanism check only. |
| **Just enough / club of the willing?** | A *normative* variant of the same layer: restrict for domestic food security while limiting importer harm; what if only some join. | Not a separate model. Same host, different objective. Later, if ever. |
| **Cooperation vs protectionism / tipping?** | Comparative statics on types (food-security vs cooperation weights). | Not a third paper by default. Still sub-annual actions. |
| **Does the network emerge?** | Trade shares from costs and prices instead of FAOSTAT E0. | Optional. Gate 0 **prescribes** Armington on E0; say so. Not required for the hindcast or the game. |
| **Decades, not just crises?** | Extend the Gate 0 hindcast beyond 2006–11 / 2021–23. | An expansion of the same note, not a new product line. |
| **Calibration** | Which knobs are structural, literature, or estimated (and on what hold-out). Kilian: extra behavior needs a plan, not a grid search on crises. | Alongside the notes we already have. Not its own paper unless it has to be. |

**Do not re-run Gate 0 or Gate 1** to host the game. Headey does not
change CropParams or σ.

## Calibration (honest, still)

| Layer | What | How constrained | Not allowed |
|---|---|---|---|
| Gate 0 market | `CropParams`: ε literature; STU literature; η, ω, κ, ask gains **reduced-form sign-constrained** | Shared across years; **not** fit per crisis. Official hindcast = Agrimate split (harvest ± AMIS, mean flex). USA maize industrial = structural RFS residual. | Crisis dummies; 2008-only κ |
| Substitution | Cross-price / `subst_scale` | Literature own-price; band `{0, 0.3, 0.6}`, not a 2008 fit | Fitting all three crises jointly then claiming validation |
| Game types | Food-security weights, ratio trigger, `tau_on`, cooperation | Labeled illustrative for a mechanism check; if estimated, train on one window and score the other | Estimating the game on the same episode used as the result |

## What is next

Not “start P4” or “start P5.” Those labels were the confusion.

**Next model step:** more than one government on the Headey clock. The
one-player beta cannot produce a cascade (Ukraine’s cut spilling onto
Russia; Thai exports absorbing diverted demand; a stock *announcement*
substituting for a ban). Still synthetic, still not a 2008/10 score,
still on `sheaf/dynamic_crop.py`. Importer procurement is the same
layer, not a new product.

**Next writing step, if any:** zip and upload the two notes that exist
(Gate 0, Gate 1). Do not invent a third title for the beta until the
cascade exists.

## Gate 0 official split (scoring)

Agrimate Figs. 3–4 / G.1–G.2:

1. baseline (climatology harvest, no AMIS)
2. production anomalies only
3. harvest + AMIS (`use_demand=False` except USA maize industrial)

Year-by-year world food/feed PSD is a **sensitivity**, not the headline
series. Gate 0 also reports: world consumption vs PSD, MY-end stocks vs
PSD (world and world excluding China; rice also excluding India),
exporter shipment signs under AMIS. Not FAOSTAT bilateral crisis
volumes or 28-region trade maps. Agrimate Fig. 3 is model-implied
withheld grain, not observed trade.

## Explicitly not Gate 0

- Endogenous network (FAOSTAT E0 is prescribed)
- Fitting substitution on joint W/R/M crises
- Endogenous restriction *actions* (those belong on this spine later;
  they are not a reason to re-run Gate 0)
- Fitting Agrimate’s private price series
