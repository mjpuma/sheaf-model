# A1c — does the calm branch touch a scored result?

Counts steps where the branch fires (`free_twin` set, and
|free-twin| < 1e-6, u_anom < 1e-9, block_frac < 1e-9), per leg.
144 steps per run.

## wheat

- full (official)    calm fires   0/144 steps
- shocks only        calm fires   0/144 steps
- tau only           calm fires  26/144 steps
- matched (assert)   calm fires 144/144 steps, price drift 0.000%

## maize

- full (official)    calm fires   0/144 steps
- shocks only        calm fires   0/144 steps
- tau only           calm fires  32/144 steps
- matched (assert)   calm fires 144/144 steps, price drift 0.000%

## rice

- full (official)    calm fires   0/144 steps
- shocks only        calm fires   0/144 steps
- tau only           calm fires  24/144 steps
- matched (assert)   calm fires 144/144 steps, price drift 0.000%

## Reading

If the branch fires only in the matched configuration, then it
determines whether `assert_twin_identity` passes but changes no
number in `diagnostics/gate0_*_report.md`. The defect is then in the
claim -- the note calls the identity algebraic when it is enforced --
and not in any scored output. If it also fires in the scored legs,
that is a different and larger problem.

