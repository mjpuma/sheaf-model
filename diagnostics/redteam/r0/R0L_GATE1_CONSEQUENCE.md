# R0l — the Gate 1 rice spillover-sign bar, after the Gate 0 fixes

Both shipped fixes exist in two places: `dynamic_crop._simulate_window`
(Gate 0) and `dynamic_coupled._simulate_coupled` (Gate 1), which carries its
own copy of the same two blocks. Leaving Gate 1 on the defective versions
was not an option — the negative-accessible-stock branch and the
post-update valuation were character-for-character the same code — so both
were applied there too.

## What still holds

**Gate 1's σ = 0 identity passes.** The coupled model at zero substitution
reproduces the independent Gate 0 prices exactly: wheat +0.687 / ×2.09 /
×1.31, rice +0.676 / ×1.54 / ×0.84, maize +0.792 / ×2.05 / ×1.52. That is
the invariant Gate 1 exists to establish and it is intact.

Wheat attribution signs pass at every σ. Rice AMIS share of the 2008 hike
passes at every σ (101% / 94% / 109%).

## What broke

**The spillover-sign hard bar now fails for rice at σ = 0.6**, returning
×0.984 where it must exceed 1. It previously returned ×1.039. Rice at
σ = 0.3 still passes (×1.029), and wheat and maize pass at both settings.

## Attribution

Each fix reverted in isolation inside `dynamic_coupled`, scored with
`score_gate1`'s own helpers:

| variant | rice σ=0.3 | rice σ=0.6 | verdict |
|---|---|---|---|
| both fixes (shipped) | ×1.029 | ×0.984 | **FAIL** |
| revert `p_trade` only, scarcity fix live | ×1.019 | ×0.985 | **FAIL** |
| revert scarcity only, `p_trade` fix live | ×1.032 | ×0.996 | **FAIL** |
| revert both (pre-fix) | ×1.018 | ×1.040 | pass |

**Neither fix alone is responsible; either one alone is sufficient to
break it.** The scarcity fix is the larger contributor — reverting
`p_trade` still leaves ×0.985, whereas reverting the scarcity fix reaches
×0.996.

## Reading, and what we are not doing about it

The mechanism is legible. The scarcity fix removes maize's factor-of-four
one-step price spike. In the coupled model maize's price feeds rice through
substitution, so a spurious spike in maize was a spurious source of
cross-commodity spillover into rice. Removing the pathology removed the
spillover it was generating.

The bar was passing by 4% and now fails by 1.6%. A test that sits within a
few per cent of its own threshold, and whose verdict is set by a numerical
artefact in a *different* commodity, is not measuring what it was built to
measure. **Classification F (empirical limitation) on the bar itself,
confidence 80–95%.**

We are not reverting a correctness fix to keep a bar green, and we are not
quietly re-tuning the bar. Both would be worse than the disclosure. The
options, for the coauthors:

1. Accept that rice's spillover at σ = 0.6 is genuinely ambiguous in sign
   and restate the bar as holding at σ = 0.3, where it passes.
2. Re-derive the bar on a quantity less sensitive to a single step in
   another commodity — a mean over the window rather than a
   three-month-peak ratio would be the obvious candidate.
3. Establish independently whether rice's 2007/08 spillover *should* be
   positive at large substitution. The observed rice hike (×1.84) is well
   above the model's (×1.54) at every σ, so the model is undershooting
   rice throughout, and the sign of its σ-response is a second-order
   property of an already-short amplitude.

Option 3 is the one that would settle it rather than accommodate it.
