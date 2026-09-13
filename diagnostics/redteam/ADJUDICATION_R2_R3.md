# Adjudication of the R2 and R3 findings

Per CLAUDE.md's final adjudication rule: disagreements are resolved by
re-running the verification protocol, not by deferring to the agent that
reported them. Both findings below were re-derived independently before
any change was made.

## R3's `p_trade` double-update — CONFIRMED, fix applied

**Classification B (coding bug), confidence 95%.** Fallback if the
coauthors state the old behaviour was intended: G, in which case README §8
and the `ask_path` bookkeeping are what change instead.

*The claim.* `_simulate_window` allocates shipments using the inherited ask
and then values those same shipments at the ask updated later in the same
step.

*Independently verified by reading.* Within step `t`:

| line | what happens |
|---|---|
| L643 | `ask_path[:, t] = ask` — records the pre-update value as **step t's** ask |
| L645–648 | `A_eff`/`S_eff` built from `ask`, so the **allocation** uses the pre-update value |
| L678–681 | `ask` is updated in place, becoming q_{t+1} |
| L697 | `p_trade = dot(ask, shipped)/Σshipped` — the **valuation** uses the post-update value |

So the model's own output array, and its allocation, both treat the
pre-update ask as step *t*'s offer price. Only the valuation disagrees:
three against one. Agrimate Eq. D.4 is explicit that the transaction price
is the offer price the demand request responded to.

*The bias is signed and rally-directional,* which is what makes it matter
rather than being a rounding concern. Measured as the shipment-weighted
gap between the two asks:

| crop | all steps | through 2007/08 | through 2010/11 |
|---|---|---|---|
| wheat | +0.86% | **+2.24%** | +1.71% |
| maize | +0.41% | **+1.90%** | +1.22% |
| rice | +3.24% | **+3.90%** | +2.07% |

Positive in every crop and every window, and larger in the rallies. The
shipped-weighted price was systematically flattered exactly when the model
is being scored on amplitude, on a term carrying ω = 0.70–0.80 of p\*.

*Fix.* One array index: value at `ask_path[:, t]`. Applied at
`sheaf/dynamic_crop.py` L695–704.

*Cost, stated plainly.* Official scores before → after:

| crop | corr | 2007/08 (obs) | 2010/11 (obs) |
|---|---|---|---|
| wheat | +0.720 → **+0.687** | ×2.27 → **×2.09** (×1.82) | ×1.45 → **×1.31** (×1.16) |
| maize | +0.781 → **+0.792** | ×2.22 → **×2.05** (×1.84) | ×1.61 → **×1.52** (×1.44) |
| rice | +0.678 → **+0.676** | ×1.72 → **×1.54** (×1.84) | ×0.82 → **×0.84** (×0.79) |

Wheat loses 0.033 correlation. Total absolute error across all six hike
ratios falls from **1.421 to 1.060**, a 25% reduction, with five of six
windows improving; rice's 2007/08 gets worse because rice was already
undershooting and the fix removes amplitude. All twelve robustness
assertions pass.

Per CLAUDE.md those score movements are the **visible cost of a
correctness fix, not its justification**. The justification is that the
model was pricing step *t*'s trade at step *t+1*'s offers.

*Independent corroboration.* R3 measured the correlation delta for wheat as
−0.040 against a different baseline; I measured −0.040 on current code.
Same delta from two harnesses.

## R2's `_ask_reweight_dest` identity map — FALSIFIED

R2 reported this as its first recommendation, **category B at 99%**,
stating that `_ask_reweight_dest` is a bit-for-bit identity map and
therefore that "`ask_comp_elast` has no effect at all" and SHEAF's only
price-based source-substitution mechanism is dead code.

**The first half is true and the conclusion does not follow.
Reclassified to H, confidence 95–100%.**

*What is true.* `_ask_reweight_dest` (L508–521) does multiply row *i* by a
row-constant and renormalise, so the tilt cancels exactly. R2's
`max|A_eff − A| = 3.3e-16` is correct.

*Why the conclusion fails.* This is already known and documented in the
function's own docstring — "Algebraically the identity… Kept so existing
callers do not break; **the live Armington channel is
`_ask_reweight_src`**" — and the live sibling is called on the very next
line, L646, with the same `ask_comp_elast`. `_ask_reweight_src` (L524–539)
reweights **columns**, which does not cancel, and its docstring says
directly that it is "the channel `ask_comp_elast` was documented as
providing and that destination reweighting cannot, because a row-scalar
cancels."

*Decisive test.* Varying `ask_comp_elast` over {0, 1.25, 8} changes the
run:

| crop | mean price at γ=0 | γ=1.25 | γ=8 | Σ\|trade\| at γ=0 → γ=8 |
|---|---|---|---|---|
| wheat | 342.06 | 341.22 | 341.66 | 523.4 → 529.2 |
| maize | 205.10 | 202.72 | **189.61** | 402.8 → 418.4 |
| rice | 640.83 | 640.78 | 640.98 | 125.0 → 122.0 |

Maize's mean price moves 7.5%. The parameter is live.

*What R2 appears to have done* is verify the identity property of the
destination function correctly and then generalise to the run without
checking the adjacent call. Its own note that Σp was "identical to 12
decimals across γ" is consistent with having tested the matrix rather than
the trajectory.

*The one residual point, which is minor and real.* The call at L645 is a
computed no-op executed every step. It costs nothing measurable but it is
a trap — it caught a careful reviewer — so removing the call and passing
`A` directly would be a behaviour-preserving cleanup. Left alone for now
because it is provably inert and the audit is not the place to churn code.
**G (documentation/housekeeping), confidence 95%.**

## R2's demand-elasticity finding — not adjudicated here

R2's substantive result is separate from the falsified one and stands on
its own measurement: 86–99% of SHEAF's market demand sits in the price-free
`rebuild` branch, giving a measured effective elasticity of −0.05 to −0.11
against Agrimate's ≈−0.35, and a prototype in Agrimate's CES form raises it
4.5–7.2× while moving scores by <0.02. That is a **D**-class gap with a
plausible fix, and R2 itself falsified the stronger framing by showing the
budget curvature contributes only 7–13% of the gain.

It is **not** applied here, for a reason the scores cannot settle: it
changes what the demand side of the model *is*, and unlike the two fixes
above it is not repairing an internal inconsistency. It belongs in front of
the coauthors as a specification choice. Recorded as an open decision.
