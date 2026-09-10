# R0 — the negative-accessible-stock regime (own-thread red-team finding)

This finding did not come from the five commissioned red-team seams. It
came out of a periodicity check prompted by Agrimate's baseline
construction, and it turned out to be the most consequential thing found
in the Gate 0 comparison, so it is written up on its own.

Everything below was executed. Scripts: `scripts/scratch/r0_twin_periodicity.py`,
`r0b_lean_truncation.py`, `r0c_window_dependence.py`, `r0d_spinup_fragility.py`,
`r0e_negative_free.py`, `r0f_surgical_fix.py`, `r0g_floor_sensitivity.py`.
CSVs alongside this file.

## How it was found

Agrimate's baseline is an inter-annual Nash-baseline state solved quasi
analytically (Suppl. §D.7.4) under an explicit **periodicity condition**:
"the yearly supply has to match the yearly consumption in this idealized
baseline setting; the periodicity condition prohibits a year's beginning
storage level to differ from the ending one" (Suppl. ~L2507–2509). SHEAF's
reference is a different object — a climatological twin simulated forward
from a two-year spin-up — with no periodicity condition imposed.

Asking whether SHEAF's twin is periodic anyway turned up something else.
The twin does converge: start-of-year world stock for maize moves
499 → 527 → 543 → 551 → 555 → 557 MMT, changes of +27, +17, +8, +4, +2, so
it is approaching an annual cycle geometrically and is within a few tenths
of a percent per year by 2010. Rice is periodic to three digits from year
two. **That question came back clean.** But every crop's *final* year
showed a jump in accessible stock, which led to the horizon check below,
which led to the real finding.

## What was ruled out first

**The lean-cover horizon truncates at the end of the run.**
`rolling_ahead_variable` computes the forward window as
`t1 = min(t + 1 + h, T)` (`sheaf/seasonal.py` L158), and
`MAX_LEAN_STEPS = STEPS_PER_YEAR = 24` (`dynamic_crop.py` L64), so the last
24 steps see a short horizon. The 2010/11 peak month, 2011-02, is step ~122
of 144, inside that zone.

Measured by padding the lean-window inputs with a repeated final year,
holding calibration and forcing fixed: the largest movement on any metric
for any crop is **0.012** (maize 2007/08), and wheat/rice correlations move
by +0.008/+0.000. **Not material. Classification H, confidence 95–100%
(directly reproduced).** Recorded because the truncation is real and
someone will find it again; it just does not matter at this window length.

## The finding

**Maize's Gate 0 price path contains an unbounded branch, and it makes the
maize score fragile.**

*Mechanism, confirmed.* When accessible stock `F = Σstock − lean_need −
locked` goes negative while the twin's stays positive, the regulariser
`shift = 0.05·Σsafety + max(0, −min(F, F_twin))` collapses the denominator
to `0.05·Σsafety`, so the ratio becomes approximately
`F_twin / (0.05·Σsafety)` — a number set by an arbitrary constant, not by
scarcity. For maize at 2006-12a: `F = −15.2` MMT, `F_twin = +207.1` MMT,
`0.05·Σsafety = 6.52` MMT, ratio **35.10**, and the price goes
**95.5 → 393.9 $/t in one step, ×4.13**, against a reference price of
134.4 $/t.

*Frequency.* The asymmetric case `F < 0 ≤ F_twin` fires at **1/144** steps
for maize and **0/144** for wheat and rice. Rice's `F` is negative at
33/144 steps but its twin is negative in the same steps, so the shift
cancels and the ratio is 1.01 — rice's negative-`F` regime is benign.

*Consequence.* Perturbing the in-sample climatology by about 1% (by
extending `end_year`, which moves `C_ann` by 1.4%, `H_seas` by ≤2.6 MMT/step
and `stock0` by ≤5.2 MMT) swings maize's 2006–2011 monthly price
correlation across **+0.276, +0.712, +0.832** — a spread of **0.557**, and
the published +0.712 is one draw from it. Wheat's spread is 0.006 and
rice's is 0.000 under the identical perturbation. Dropping the spin-up year
from the scoring window does *not* help (spread 0.734), so this is not a
scoring convention: it is the path.

**Classification C (numerical issue), confidence 95–100%** for the
mechanism and the fragility, both directly reproduced.

## The fix

Fire only on the asymmetric case, and floor the denominator on physical
world stock, which cannot be negative:

```
if free < 0.0 <= twin:
    ratio = (twin + floor0) / (0.10 * stock.sum() + floor0)
else:
    shift = floor0 + max(0.0, -min(free, twin))   # unchanged
    ratio = (twin + shift) / (free + shift)
```

Applied at `sheaf/dynamic_crop.py` L676–685.

| | wheat | maize | rice |
|---|---|---|---|
| steps changed | **0/144** | 122/144 | **0/144** |
| correlation | +0.720 → +0.720 | +0.712 → **+0.781** | +0.678 → +0.678 |
| 2007/08 (obs ×1.84 maize) | ×2.27 → ×2.27 | ×1.97 → **×2.22** | ×1.72 → ×1.72 |
| 2010/11 (obs ×1.44 maize) | ×1.45 → ×1.45 | ×1.70 → **×1.61** | ×0.82 → ×0.82 |
| fragility spread | 0.006 → 0.006 | 0.557 → **0.051** | 0.000 → 0.000 |
| largest year-1 one-step move | — | 298.4 → **31.9** $/t | — |

Wheat and rice are **bit-identical** — they never enter the branch. Maize
changes at 122/144 steps because the single triggered step propagates
through stock, asks and price smoothing. All four robustness assertions
pass for all three crops.

**The cost is real and is not hidden:** maize's 2007/08 overshoot gets
worse, from ×1.97 against an observed ×1.84 (+7%) to ×2.22 (+21%). Its
2010/11 overshoot improves, from ×1.70 against ×1.44 (+18%) to ×1.61
(+12%). So this is not a free improvement; it trades a worse 2007/08 level
for a bounded, robust and mechanically defensible path.

## Falsification attempts

1. **"You replaced an arbitrary 0.05 with an arbitrary 0.10."** Swept the
   floor coefficient over 0.05 → 0.40, a factor of eight. Maize
   correlation moves +0.788 → +0.772, a range of **0.016**; 2007/08 stays
   within ×2.19–×2.24; 2010/11 within ×1.61–×1.62; fragility spread within
   0.051–0.060. The result is flat, so the fix works by removing the
   unbounded branch, not by the coefficient's value. **Survives.**
2. **"You tuned to 2008."** The fix was selected on the mechanism (an
   unbounded branch) and on robustness (the spread), before any score was
   looked at, and it makes the 2007/08 ratio *worse*. A tuning exercise
   would not have accepted that. **Survives.**
3. **"It is entangled with `ask_rival`, which A2 showed has no surviving
   justification."** Re-ran at `ask_rival = 0`: maize +0.414 → +0.522, so
   the fix still helps when the disputed parameter is switched off.
   **Survives.**
4. **"A 1/144 branch cannot matter."** It can, because the state is
   persistent: one step at ×4.13 propagates through stock and asks for the
   remaining 122 steps. Directly measured. **Does not survive; the
   objection is wrong.**

## What this changes for the Potsdam response

Maize's published headline correlation changes from **+0.712 to +0.781**
and its 2007/08 ratio from **×1.97 to ×2.22**. Wheat and rice are
unaffected to the last digit. Any figure, table or slide carrying the old
maize numbers needs regenerating, and the coauthors should be told that the
old maize number was drawn from a range spanning +0.28 to +0.83 rather than
being a stable property of the model.
