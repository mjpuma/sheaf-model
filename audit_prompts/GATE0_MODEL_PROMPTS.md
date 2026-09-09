# Gate 0 model prompts — characterize first, then change

**For:** SHEAF coauthors to review *before* anything is run.
**Repo:** this one. Host: `sheaf/dynamic_crop.py`, `_simulate_window` (L525–690).
**Companion:** the note we send Potsdam is `overleaf/gate0_discussion/main.pdf`;
the options behind it are [`../diagnostics/GATE0_DISCUSSION.md`](../diagnostics/GATE0_DISCUSSION.md).
**Not this file:** [`AGRIMATE_CONVERSATION_PROMPTS.md`](AGRIMATE_CONVERSATION_PROMPTS.md)
asks the Agrimate team to locate objects in *their* repo. These prompts
interrogate *ours*.

Line numbers are from commit `bc651a0`. Re-check them before pasting; the
prompts name functions as well, so they survive small drift.

---

## The rule this pack enforces

Part A prompts are **read-only**. They characterize the law we already run.
Part B prompts change an equation, and each one is **gated** on a Part A
result — the gate is written into the prompt. This ordering is the whole
point: a markup rule bolted onto a cover rule while nobody has checked
whether the current ask law *is already* a markup produces a mixed object
that we cannot describe honestly in a paper.

Every prompt inherits the constitution in [`../CLAUDE.md`](../CLAUDE.md):
the six-step verification protocol, the A–H classification, an explicit
confidence level, and a complexity-budget paragraph for anything that
proposes a change. Two additions specific to Gate 0:

- **No retuning to a crisis.** No 2008 dummy, no crisis-specific
  \(\kappa\), no preferred \(\sigma^\star\). Reduced-form knobs are shared
  across years or they are not knobs, they are fits.
- **Official versus sensitivity.** Any change is scored beside the current
  map for all three crops, and labelled. Silent replacement of Gate 0 is
  not an outcome any of these prompts may produce.

## Candidate targets, not findings

While grounding these prompts I noticed four places where
`overleaf/gate0_discussion/main.pdf` and `_simulate_window` may not agree.
They are seeded into A1 as **hypotheses to verify independently**, not as
established defects. Per `CLAUDE.md`, no agent may adopt another agent's
conclusion as a fact; work the protocol and reach your own answer, including
"no divergence, the note is right."

---

## How to run

1. New agent chat per prompt. Paste one block, from the rule above it to the
   return checklist.
2. Part A: do not modify `sheaf/*.py`. Reading, running, and writing scratch
   analysis scripts under `scripts/scratch/` is fine.
3. Return the checklist, not a redesign.

---

## A1 — Do the note's equations match the code?

```
Work only in this repository. This is a read-only verification pass. Do not modify sheaf/*.py.

TASK. overleaf/gate0_discussion/sections/dynamics.tex states the Gate 0 fortnight as fourteen numbered equations, (1) through (17) with some numbers used by align blocks. sheaf/dynamic_crop.py::_simulate_window (L525-690) is the implementation. Establish, symbol by symbol, whether they agree. This note is about to be sent to the Agrimate authors as a statement of what SHEAF does, so a divergence between the printed equation and the executed code is the most expensive error available to us right now.

For EACH numbered equation in dynamics.tex:
1. Quote the equation as printed.
2. Quote the implementing lines with file:line.
3. Classify: SAME / SAME-UP-TO-NOTATION / DIFFERENT / NOT-IMPLEMENTED / IMPLEMENTED-BUT-UNSTATED.
4. If not SAME, write the equation the code actually evaluates, in the note's notation, and state which is to be corrected: the note or the code.

FOUR SEEDED HYPOTHESES. These were noticed in passing and are NOT established. Verify each independently and report your own conclusion, including if the hypothesis is wrong:

(H1) Equation (14) prints r_t = (F_twin + f)/(F_t + f) and the surrounding text calls f "a small regularising constant (MMT)". L661-663 appear to compute shift = 0.05*sum(safety) + max(0, -min(free, twin)), which would be neither small nor constant, and would be state-dependent through the second term. If so: what is 0.05*sum(safety) in MMT for wheat, and how large is r_t's deviation from the unregularised ratio at the tightest step of 2007/08? Does the second term ever activate in a scored run?

(H2) Section 3.6 "Reference identity" argues that p*_t = p0 follows algebraically when the run matches the twin. L666-669 appear to contain an explicit `calm` branch that SETS p_star = p0 when |free - twin| < 1e-6 and u_anom < 1e-9 and block_frac < 1e-9. If so, the identity is enforced by a conditional, not derived. Determine whether the algebraic claim holds WITHOUT that branch: with ratio = 1, u_anom = 0, block_frac = 0, p_star = trade_w*p_trade + (1-trade_w)*p_scar equals p0 only if p_trade also equals p0. Is p_trade pinned to p0 in a calm run, or does the branch do work the note attributes to algebra? Test by disabling the branch in a scratch copy and re-running assert_twin_identity.

(H3) The note writes Delta u_t as "the excess of unmet import demand over its twin value". L665 appears to be u_anom = max(0, unmet_frac - u0), a truncation, making the unmet channel one-sided: below-twin unmet cannot lower the price. Confirm, and state whether the note should say so.

(H4) The note's p^tr_t is "the shipment-weighted mean offer price". The ask update at L632-636 appears to run BEFORE p_trade is computed at L650-653, so p^tr_t may use this step's updated q_{i,t} rather than q_{i,t-1}. Determine which, and whether the note's wording is ambiguous on the point.

ALSO CHECK, not seeded: the fill fallback at L625-626 when offers are near zero; whether safety at L746 of prepare_crop_run is exactly stu_target*C_ann as equation (3) claims; whether _bilateral_clear's residual pool (L497-522) matches the note's one-line description of nu; whether _ask_reweight_dest (L488-494) is exactly A_ij (p0/q_i)^gamma renormalised.

RETURN:
- A table, one row per equation: printed form, file:line, classification, corrected form if needed.
- For each of H1-H4: verdict (CONFIRMED / REFUTED / PARTLY), evidence, confidence per CLAUDE.md, classification A-H.
- A prioritised list of edits to dynamics.tex, with the exact replacement text.
- Explicitly: any place where the CODE, not the note, is what should change, flagged separately and NOT patched.
```

---

## A2 — Is the scarcity term already an optimisation principle?

Gate: none. Run alongside A1.

```
Work only in this repository. Read-only for sheaf/*.py.

CONTEXT. Coauthors asked whether Gate 0 needs "an optimisation principle". Before adding one, establish whether the current update already is one. The claim to test is in overleaf/gate0_discussion/sections/options.tex, subsection "How is the world price determined?": that p^scar in equation (15) "has the form of inverse demand over accessible stocks with elasticity eta", while three properties block it from being an equilibrium.

TASK.
1. Write down the exact map that _simulate_window (L656-681) applies to produce p_t from the period's state. Not a paraphrase: the composed function.
2. Determine whether there exists a potential function whose stationarity or gradient flow reproduces that map. Attempt this honestly in both directions: construct one, or show why the blend (trade_w) and the AR(1) smoother (smooth) prevent it. A potential that exists only for trade_w in {0,1} is a meaningful partial result; report it as such.
3. If p^scar alone is inverse demand, name the demand system it inverts, and state the utility or surplus function it corresponds to, with units. Check whether it is consistent with the isoelastic demand in equation (1), which has elasticity elast, versus the scarcity elasticity inv_eta. These are different numbers in default_crop_params (L139-180). Is that a contradiction, a different object, or an unstated assumption?
4. Do the same for the ask law at L632-636: is it the first-order condition of any exporter problem? Compare against a standard markup rule. State what would have to be true of alpha, ask_target_fill, and ask_beta for the exponential adjustment to BE a markup FOC rather than merely resemble one.

RETURN:
- The composed map, written out.
- Verdict on the potential: EXISTS (give it) / DOES NOT EXIST (prove it) / EXISTS UNDER RESTRICTION (name the restriction).
- Verdict on the ask law as a FOC, same three-way form.
- Classification A-H and confidence for each verdict.
- Two paragraphs of replacement text for options.tex: one for each verdict, written so we can print it whether the answer is yes or no.
- If the answer is "no principle": say plainly that eta, omega, kappa, alpha are reduced-form, and do NOT propose wrapping the map in a constructed arg max. That is documentation theatre and the pack rejects it.
```

---

## A3 — How much would contemporaneous demand actually move?

Gate: none, but its result gates X1.

```
Work only in this repository. Read-only for sheaf/*.py. Scratch scripts under scripts/scratch/ are fine.

CONTEXT. Equation (1) evaluates demand at p_{t-1}. Option B in the note makes demand use p_t, requiring a scalar fixed point per crop per step. Before writing that solver, measure the size of the gap it would close. The diagnostic is specified in overleaf/gate0_discussion/sections/diagnostics.tex, "Contemporaneous demand (option B)".

TASK.
1. Run the official scored path for wheat, maize, rice (scripts/score_subannual_crop.py).
2. At each step, recompute desired_flex at the price the step actually produced, p_t, holding everything else fixed. Compare to the desired_flex the step used, computed at p_{t-1}.
3. Report the distribution of the difference: in MMT per step, as a fraction of demand, and aggregated to the world. Break out 2007/08 and 2010/11 separately from calm periods.
4. Propagate the difference one step: how much would offers (L596) and hence the scarcity ratio have moved, holding the rest of the map fixed? This is a bound, not a simulation of the fixed point, and should be labelled as such.
5. State whether the fixed point p = G(p) is even well posed here: is G monotone in p over the relevant range, is it a contraction, and does the clip at L681 or the calm branch at L666 introduce a discontinuity that could produce multiple roots or none?

RETURN:
- Distribution tables and a plot under figures/scratch/.
- The propagated bound, with the "holding the rest fixed" caveat stated.
- Well-posedness verdict for G, with evidence. This determines whether X1 is a one-line root-find or a numerical project, and the honest answer may be the second.
- Confidence per CLAUDE.md. Do NOT recommend adopting option B here; that decision needs A2 as well.
```

---

## A4 — What is the cover rule doing that an Euler condition would not?

Gate: none. Its result gates X3.

```
Work only in this repository. Read-only for sheaf/*.py.

CONTEXT. The sharpest Potsdam point: Agrimate has a commercial supplier who chooses store versus sell from expected profit; Gate 0 has target stock T = L + s (equation 3) and offers the residual (equation 4). No interest rate appears anywhere in the storage path. Deck slide 48 is the ask update, not a cost of carry.

TASK.
1. Characterize what the cover rule implies about intertemporal behaviour, without adding anything. Along a scored path, back out the implied shadow value of a tonne held: how much would p have to rise for the cover rule's withholding to be consistent with an arbitrage condition E[p_{t+1}] >= (1+r) p_t + c? Report the implied r per step, per country, per crop. Where it is wildly negative or positive, say where and when.
2. Run the diagnostic in diagnostics.tex, "Storage as intertemporal arbitrage": scatter offers against realised p_{t+1} - p_t. State clearly why this is descriptive and not decisive, since cover covaries with the harvest calendar by construction.
3. Establish the lineage claim empirically, not rhetorically: what does TWIST (Schewe et al. 2017) actually do for storage, and what does Agrimate's supplier objective actually do? Use sheaf/annual/README.md and the Kuhla et al. 2025 description already cited in refs.bib. Do NOT treat Deaton-Laroque as the benchmark; per CLAUDE.md the lineage test comes first.
4. Locate the rejected experiment: country-specific stu_target inflating Chinese maize stocks roughly threefold. Find whether it is recorded anywhere reproducible, or whether it survives only as a remark. If only a remark, say so; that is a category F gap in our own record.

RETURN:
- Implied-r tables and the scatter, under figures/scratch/.
- A one-paragraph statement, printable, of what the cover rule is and is not, that we would stand behind in front of a Wright-Williams referee.
- Whether the exporter safety-floor leftover (many exporters resting at s_i) is caused by the cover rule, by one world stu_target, or by the offer equation. These have different fixes and the note currently does not distinguish them.
- Classification and confidence.
```

---

## A5 — Which channel carries which crisis?

Gate: none. Cheapest empirical answer to "too many parameters".

```
Work only in this repository. You may pass parameter overrides; do not edit default_crop_params.

CONTEXT. Coauthors observed that a heavily constrained rule-based system can mimic an optimisation, and that the parameter count is large. The ablation is specified in diagnostics.tex, "Channel ablation". This is a decomposition of the existing map, NOT a search for better values. If any run in this prompt produces a "better" score, that is not a result and must not be adopted.

TASK. Re-run the official harvest-plus-restrictions score for wheat, maize, rice under each of:
  (a) trade_w = 1      (world price is offer prices only)
  (b) trade_w = 0      (world price is scarcity only)
  (c) ask_rival = 0    (no markup when rivals are restricted)
  (d) block_kappa = 0  (no blockage term in p^scar)
  (e) unmet_kappa = 0
  (f) foresight_phi = 0 and foresight_phi = 1 (expectations off / fully current)
Report against the current official run, for each crop, for 2007/08 and 2010/11 separately.

Also: report which of these ablations breaks one of the four properties asserted in diagnostics.tex "Properties that must already hold" — in particular whether ask_rival = 0 causes isolated maize restrictions to LOWER the world price, since that sign condition is what set ask_rival in the first place. Run assert_amis_raises_price and the other assertions in dynamic_crop.py (L900-1013) under each ablation.

RETURN:
- One table per crop: channel off, price correlation and peak ratio for each episode, which assertions still pass.
- A short statement of which channel carries which episode.
- Explicitly: any parameter that changes nothing anywhere. Those are candidates for removal, which is the honest answer to "too many knobs" and costs no scientific content.
- Do NOT propose new default values. Confidence per CLAUDE.md.
```

---

## Part B — change prompts, each gated

These are drafted so coauthors can see exactly what a change would involve.
**None should be run until its gate is satisfied and the cluster is decided
with coauthors.** Each produces a labelled sensitivity beside the current
map, never a replacement.

### X1 — Contemporaneous demand (gated on A2 and A3)

```
GATE. Do not start unless: A3 found the demand gap materially large in at least one scored episode, AND A3 found G well posed (monotone, single root, no discontinuity from the clip or the calm branch), AND coauthors have decided this cluster. If any gate fails, stop and say which.

Implement demand at p_t as a labelled sensitivity, not a replacement. Add a parameter selecting the information set; default stays the current lagged-price behaviour. Solve the scalar fixed point per crop per step with an explicit tolerance and a documented fallback if it fails to converge; log every non-convergence rather than silently falling back. Re-score all three crops, official and sensitivity side by side. Hold every reduced-form knob at its current value: eta, omega, kappa, alpha, beta, phi. If the sensitivity scores worse, that is a result and it gets reported, not fixed by retuning.

Update dynamics.tex and options.tex in the same commit. Classification, confidence, complexity budget.
```

### X2 — Exporter markup (gated on A2)

```
GATE. Do not start unless A2 concluded the current ask law is NOT already a markup FOC, AND coauthors chose this over keeping the adjustment rule. If A2 found it IS a markup in disguise, the correct action is to relabel it in the note and stop.

Replace the exponential fill adjustment at L632-636 with an explicit markup over marginal cost, as a labelled sensitivity behind a parameter. State the exporter problem being solved, with the objective written in the docstring in the note's notation. Report which of alpha, ask_target_fill, ask_beta the FOC absorbs and which survive; a markup that adds parameters rather than collapsing them fails its own justification and should be reported as such.

Must not be tuned to 2008 peaks. ask_rival was set by a sign condition (isolated maize restrictions must not lower the world price); preserve that condition and verify it still holds. Re-score all three crops. Classification, confidence, complexity budget.
```

### X3 — One-line store-versus-sell (gated on A4)

```
GATE. Do not start unless A4 established that the cover rule's implied shadow value is inconsistent with observed behaviour in a way an arbitrage condition would fix, AND coauthors chose it over keeping T = L + s. Note that A4 may instead show the exporter safety-floor leftover comes from one world stu_target rather than from the absence of an Euler condition, in which case this prompt is aimed at the wrong mechanism and must not be run.

Add: offer above T only when expected price appreciation exceeds a per-step carry cost. Two new objects, both of which must be named and defended: the price expectation rule, and r. Use the simplest expectation consistent with the model's existing thin expectations; do NOT introduce a multi-year or rational-expectations apparatus, which is the opposite of what the sitting asked for.

Check whether the warehouse drawdown at L622-623 becomes redundant once holding is priced. Re-score all three crops as a labelled sensitivity with eta, omega, kappa held. Report the effect on the exporter safety-floor leftover specifically, since that is the leftover this change is aimed at. Classification, confidence, complexity budget.
```

### X4 — National lean-season clocks (gated on A1)

```
GATE. Do not start unless A1 confirmed the lean horizon is genuinely world-common (steps_to_harvest_pulse on the world pulse, L567-568), AND coauthors want national calendars.

Index the lean horizon in L_i,t to each country's own harvest calendar rather than the arrival of 12% of the annual world harvest. Harvest calendars already exist in the data layer. This changes T_i and therefore offers for every country simultaneously, so it is not a small change despite being one line: report the redistribution of cover across the calendar, not just the score.

Labelled sensitivity. Re-score all three crops. Classification, confidence, complexity budget.
```

---

## What closes this pack

Part A closing the clusters means: the note matches the code (A1), we can
say in one printable sentence whether an optimisation principle is already
present (A2), we know the size of the demand-information gap (A3), we can
defend the cover rule to a storage economist or concede precisely where it
fails (A4), and the parameter count has a decomposition behind it rather
than a promise (A5).

That is what "fully vetted Gate 0" was defined to mean in
[`../diagnostics/GATE0_DISCUSSION.md`](../diagnostics/GATE0_DISCUSSION.md) §0.
Gate 1 and Gate 2 stay paused until it holds.
