# Response to the Potsdam sitting, 30 August 2026

To: Kuhla, Kubiczek, Otto
From: the SHEAF team
Accompanies: `overleaf/gate0_discussion/main.pdf` (20 pp., revised)

Thank you for the sitting. This is not a list of things we intend to do. It
is what your questions turned up when we went and checked, what we changed
as a result, and where we would value your judgement.

The short version. Your questions sent us to compare the written equations
against the executed code, and then to red-team Gate 0 against Agrimate on
optimisation, clearing, and the rest of the formulation, this time reading
your paper and its ODD supplement line by line rather than working from our
own summary of them. Four of the note's statements were wrong. **Three model
changes are shipped, all three of them repairs of internal inconsistencies
rather than recalibrations**, and together they move the headline scores
enough that every number in our August material is superseded.

The first is the one you would recognise as Eq. 8c: our Armington
competition was algebraically the identity, so cheaper origins never gained
share. It is now a CES source-share reweight, the first-order condition of
expenditure minimisation. The second is that our scarcity ratio had an
unbounded branch: when a country's lean-season requirement exceeded its
physical stock, the ratio was set by a regularising constant rather than by
scarcity, and it put a factor-of-four price spike into the maize path. The
third is that we were valuing each period's shipments at the offer prices
that *replaced* the ones which had allocated them — a bias of about two to
four per cent, always in the direction of a rally, on a term carrying
seventy to eighty per cent of the world price. Your Eq. D.4 is explicit on
this point and we were not following it.

An exporter first-order condition that would give the offer-price law a
rest point, and remove four reduced-form knobs, restores the quiet market
but costs the crisis; we prototyped it and did not adopt it. The
restriction channel is the leading 2007/08 channel in all three crops once
a contaminated comparison is repaired. Storage remains the place Gate 0 is
weaker than Agrimate — though reading your supplement closely narrowed that
gap more than we expected, for reasons in §4.

---

## 1. What we changed

**Change 1, importer sourcing.** Destination-share reweighting
\(\tilde A_{ij}\propto A_{ij}(p_0/q_i)^\gamma\), renormalised by exporter,
is the identity: a row-constant cancels. `ask_comp_elast` therefore did
nothing, against the note, the parameter comment, and Agrimate Eq. 8c.
Importer source shares are now the CES mix,
\(\tilde S_{ij}\propto S_{ij}(p_0/q_i)^\gamma\), renormalised by importer,
where \(S_{ij}\) is the baseline share of importer \(j\)'s purchases coming
from exporter \(i\), \(q_i\) is exporter \(i\)'s offer price, \(p_0\) is the
reference price, and \(\gamma\) is the substitution elasticity.

**Change 2, a bounded scarcity ratio.** The world price responds to a
scarcity ratio \(r_t=(\mathcal F^{\rm twin}_t+f_t)/(\mathcal F_t+f_t)\),
where \(\mathcal F_t\) is accessible stock — physical stock less the
lean-season requirement and less any surplus locked behind an export
restriction — \(\mathcal F^{\rm twin}_t\) is the same quantity on the
reference run, and \(f_t\) is a regulariser. Accessible stock can go
negative, because a forward-looking requirement can exceed the grain
actually held. When it did, while the reference stayed positive, the
regulariser collapsed the denominator to a constant and the ratio became
that constant divided into the reference — 35.1 for maize in the first
December of the run, which took the price from 95.5 to 393.9 \$/t in one
fortnight against a reference of 134.4. This fired at exactly one step in
144 for maize and never for wheat or rice, but one step is enough: it
propagated through stocks and offer prices for the remaining 122. Its
consequence was that maize's headline correlation was not reproducible —
perturbing the in-sample climatology by about one per cent moved it across
+0.28, +0.71 and +0.83. The ratio is now floored on physical stock, which
cannot be negative, in that one asymmetric case. Wheat and rice are
bit-identical. Maize's spread under the same perturbation falls from 0.557
to 0.051.

**Change 3, valuing trade at the price that allocated it.** Within a
fortnight we allocate shipments using the offer prices standing at the
start of the step, then update those offer prices, and were then valuing
the same shipments at the updated figures. Three of the four places that
refer to "this step's offer price" — the recorded output, the destination
mix, the source mix — used the pre-update value; only the valuation did
not. Your Eq. D.4 states the transaction price is the offer the demand
request responded to, and we now do the same. The bias this removes was
systematic and rally-directional: the shipment-weighted gap ran +2.2%
(wheat), +1.9% (maize) and +3.9% (rice) through 2007/08, so the trade price
was flattered precisely in the windows on which we report amplitude.

All twelve robustness assertions pass after all three. Official scores,
full leg, August material → now:

| crop | corr | 2007/08 | 2010/11 | observed 07/08, 10/11 |
|---|---|---|---|---|
| wheat | +0.720 → **+0.687** | ×2.27 → **×2.09** | ×1.45 → **×1.31** | ×1.82, ×1.16 |
| maize | +0.712 → **+0.792** | ×1.97 → **×2.05** | ×1.70 → **×1.52** | ×1.84, ×1.44 |
| rice | +0.678 → **+0.676** | ×1.72 → **×1.54** | ×0.82 → **×0.84** | ×1.84, ×0.79 |

We should be plain about the trade. Summed over all six crisis windows, the
absolute error in the hike ratios falls from 1.421 to 1.060, and five of
the six move toward the observed value. But wheat's correlation falls by
0.033 and rice's 2007/08 ratio, which was already short of the observed
×1.84, falls further to ×1.54. **None of these three changes was selected
on a score.** Two were selected because a quantity was unbounded or
inconsistent, and the third because a documented mechanism was inert. We
report the score movements as the cost, and in rice's case it is a cost.

Maize moved under change 1 as well, because the reference run is rebuilt
under the same law, so the scarcity ratio sees the new allocation. That is
a consequence of making a documented mechanism real, not a retune.

**And one consequence we should report against ourselves.** Both defects
existed character-for-character in the Gate 1 coupled host as well, so we
fixed them there too. Gate 1's central invariant survives — at zero
substitution the coupled model still reproduces the independent Gate 0
prices exactly — but one of its hard bars, requiring that switching on
cross-commodity substitution raise rice's 2007/08 hike, now fails at the
largest substitution setting, returning ×0.984 where it needs to exceed 1.
It had been passing at ×1.039, and it still passes at the intermediate
setting. Reverting either fix alone does not restore it.

The mechanism is legible rather than mysterious: maize's spurious
factor-of-four spike was a spurious source of spillover into rice, and
removing the pathology removed the spillover it was generating. Our reading
is that a bar which was passing by four per cent, and whose verdict is set
by a numerical artefact in a different commodity, was not measuring what it
was built to measure — and that rice is undershooting its observed ×1.84
hike at every substitution setting anyway, so the sign of its
substitution-response is a second-order property of an already-short
amplitude. But we are not going to revert a correctness fix to keep a bar
green, nor quietly restate the bar, without telling you first.
`diagnostics/redteam/r0/R0L_GATE1_CONSEQUENCE.md` has the attribution table
and three options.

**Note corrections (no score effect).** The scarcity regulariser is 5% of
world safety stock plus a state-dependent term, not a small constant, and
biases the rice scarcity ratio by 35% on average. The unmet-demand channel
is truncated at zero and the truncation binds at 92 / 59 / 100 of 144 steps.
The trade-weighted price falls back to the previous world price when nothing
ships — a jump of up to 12 $/t that was missing from the printed equation.
The reference identity is enforced, not derived — see §2. The note's
statement that the trade-weighted price uses "this period's asks" was itself
imprecise, and is what led us to change 3 above.

**Measurement fixes (no equation change).** Unknown keyword overrides now
raise. The four assertions accept overrides. The restriction sign test
perturbs its baseline harvest by one part per million so both legs share a
price law — see §2.

---

## 2. The one we would like you to look at first

Your question was whether the price map is a differential equation and how
the price is actually formed. Working through it, we found that the
reference identity — no shock, therefore price at the reference — is
delivered by an explicit conditional in the code rather than by the price
law. With that conditional disabled, a run with climatological harvest, mean
demand and no restrictions drifts 25%, 34% and 19% for wheat, maize and
rice, against a 2% tolerance.

The cause is that realised fill in a quiet market averages 0.54, 0.32 and
0.62 against a target of 0.70, so the offer-price law pushes offers down
every period with nothing happening. The law has no rest point at the
reference. Re-targeting the fill parameter to the realised quiet-market mean
does not repair it (drift falls only to about 19%) and degrades the maize
correlation from +0.71 to +0.65, so that is not the fix.

This matters beyond bookkeeping because of what the conditional was
silently doing to a comparison. The restriction sign test compares a
restriction-only run against a no-restriction baseline; the baseline is
matched, so it is pinned at exactly the reference, while the treatment is
priced by the ask law, whose quiet trade-weighted offer price is 0.81 and
0.71 of the reference for wheat and maize (`gate0_prep/a1/A1B_CALM_FIXED_POINT.md`).
The measured lift therefore included the release of that pin, biased down
by 27 points for maize (unpinned τ-leg base 98.2 vs pinned 135.4 $/t;
`gate0_prep/a2/A2D_TAU_ATTRIBUTION.md`).

The repair needs no equation change: perturb the baseline harvest by one
part per million so it leaves the matched regime and both legs share a price
law. Two consequences.

**The justification we gave for the rival markup does not survive.** The
code recorded `ask_rival = 0.80` as the smallest shared value at which
isolated maize restrictions do not cut the world price. On the corrected
test the condition holds at zero for all three crops (maize +4.7%, wheat
+48.8%, rice +16.0%). The sign condition does not pin the parameter.

We should not overstate this in the other direction. Bisecting the crossing
under both versions of the test: as written, maize crosses at 0.755, which
is why 0.80 was chosen; corrected, maize clears at zero but by only +4.7%,
so the condition is nearly binding rather than comfortably slack. And the
parameter is not spurious — setting it to zero moves the maize correlation
from +0.778 to +0.520 after the CES repair (it was +0.712 → +0.414 before)
and the rice 2007/08 ratio from ×1.72 to ×1.01 against an observed ×1.84.

So the finding is narrower and more awkward than "a knob we can drop": a
parameter that materially sets crisis amplitude has no independent basis for
its value. That is the identification problem we are least comfortable with. We would rather hear
your view than pick a story. Options as we see them: find an external basis
(the export-restriction price-transmission literature is the obvious place),
relabel it explicitly as a shared reduced-form amplitude parameter and
disclose that no sign condition pins it, or rebuild the offer-price law so
the markup emerges from an exporter problem.

**The attribution table changes.** The same pin sat in the base window of
the restriction-only leg's hike ratio.

| crop | 2007/08 τ ratio, as published | like-for-like | observed |
|---|---|---|---|
| wheat | ×1.71 | ×2.00 | ×1.82 |
| maize | ×1.09 | ×1.69 | ×1.84 |
| rice | ×1.75 | ×1.70 | ×1.84 |

Maize 2007/08 moves from demand-led to restriction-led. Both numbers are
now printed in the per-crop reports; we have not yet decided which is the
headline, and would like that to be a joint decision.

---

## 3. Your twelve questions

Every one has a named home in the revised note. Where we have since
measured something, the measurement is in the third column.

| Your question | In the note | What we measured |
|---|---|---|
| How is price formed? Is it a differential equation? | §3.5 eqs (12)–(17); §4.3 | Discrete sequential map. Price flexibility table in `gate0_prep/a2/` |
| Export prices each step? World vs export price? | §3.4 eq (11); §4.4 | Two prices, both now defined; §2 above on their interaction |
| Do we need an optimisation principle? | §4.3 | Scarcity term = \(U'(F)\) for CRRA over accessible stock. CES sourcing is now a real FOC. The ask law is not; an exporter FOC was prototyped (see §4) |
| What is the baseline? | §4.1, Fig. 2 | Four objects, all named |
| Commercial hold / competitive storage / one agent | §4.2, Fig. 3 | Cover rule, not store-versus-sell. Implied newsvendor penalties are \(10^{5}\)–\(10^{6}\). This is the remaining gap |
| How much is sold to each market? | §3.2 eqs (6)–(8); §4.4 | FAOSTAT pattern plus residual pool. Residual share: wheat 12%, maize 4%, **rice 47%** |
| Linear demand? Industrial use? | §3.1 eq (1); §4.5 | Isoelastic, not linear |
| Expectations: not ten-year foresight | §3.1 eq (2); §4.7 | Foresight is near-inert for wheat (0.02 on all metrics), active for maize (0.30) |
| Slide 48 / storage cost; why not dump everything? | §4.2 | Slide 48 is the ask update, not a cost of carry. **Please confirm which you meant** |
| Glut should lower p; annually? | §4.6 | Surplus already lowers the price through the scarcity ratio, roughly symmetrically at 1–2% shocks. The unmet channel is a different, one-sided object |
| Too many parameters | §4.8, Table 2; §5 | Hard bounds do **not** reproduce the official scores (maize corr +0.71 → +0.22). Three collinear pairs; `ask_comp_elast` was the one dead knob and is now live |
| "FRO and economics" | — | We read "FAO and economists". **Please confirm** |

---

## 4. New results

All runs are reproducible from `scripts/scratch/`; artifacts in
`diagnostics/gate0_prep/`.

### Would contemporaneous demand change anything?

You asked whether demand should respond to the price the period produces
rather than the previous one. We sized it. The gap is 0.08 to 0.24 MMT per
step, which is 0.3% to 0.9% of world desired use, largest in 2007/08 for
maize.

We also checked whether the implied fixed point is well posed, since that
determines whether this is a one-line change or a numerical project. The
answer is in between. Over all 432 crop-steps the map has exactly one root
at every step, the slope at the root never exceeds 0.117 in absolute value,
and plain Picard iteration converges in at most thirteen iterations even
from deliberately bad starting points. So the inner solve is genuinely
cheap.

What stops it being one line is that the map is not globally contractive —
its Lipschitz constant over the admissible price interval reaches 39.7,
always far from the root — and it has two real jump discontinuities. One is
the conditional discussed in §2, which steps the map by up to 37 $/t. The
other we had not catalogued at all: when world shipments fall below a
threshold, the shipment-weighted offer price falls back to the previous
world price, and the mean it replaces does not approach that value, so the
map jumps by up to 12 $/t. A jump straddling a root means no root exists
there, so an implementation needs a bracketed solve with an explicit
residual check rather than a bare iteration. Neither jump came near a root
on the scored path, but both live where accessible stock is small or
negative — which is the regime the model exists to study.

Our inclination is still to record the measurement and not change the map,
for a 0.3% to 0.9% correction. But the second discontinuity is a genuine
gap in how we had written the price down, and it is now in the note.

### Which channel carries which crisis?

Nine one-at-a-time ablations across three crops and two legs, with all four
assertions re-run in each of the thirty cells.

- The restriction channel carries 2007/08 in all three crops, and it is
  carried by the two blockage-conditional terms rather than by the quantity
  cut alone. This was reached independently of the attribution correction in
  §2, and agrees with it.
- 2010/11 is an ask-dynamics episode rather than a restriction episode for
  wheat and maize.
- No parameter is inert everywhere, so the honest answer to "too many
  parameters" is not that some are dead. But three exact conditional
  inertness results hold: the scarcity parameters vanish when the price is
  all offer prices, the two restriction parameters are exactly inert on any
  restriction-free path, and foresight is exactly inert whenever harvest
  equals its climatology. The last means the calm twin that anchors our
  robustness test is a function of far fewer parameters than the treatment
  path.
- Of 120 assertion evaluations, three fail, all of them the maize sign test,
  under the ablations that remove the rival markup, the blockage term, or the
  scarcity price entirely. The quantity-side assertions are robust to every
  price-channel ablation.

---

### Gate 0 against Agrimate

We red-teamed the formulation on three axes — optimisation, clearing, and
the rest of the census — with the instruction that Gate 0 should be as
strong as Agrimate or stronger, and that a cheaper design is not
automatically an error. Full tables in
`diagnostics/gate0_prep/redteam/REDTEAM_SYNTHESIS.md`. The short version:

- **Now at parity:** importer sourcing. That was the dead Armington
  channel; it is now the CES first-order condition you already use.
- **At parity on the steepness of the price response, which surprised us.**
  Your world price is isoelastic inverse demand on a *flow* with inverse
  elasticity \(\alpha=3\) (Suppl. §D.7.4.1), and \(\alpha_I=3.5\) on the
  international market (Tbl. D.8). Ours is isoelastic in a ratio of
  *stocks* with exponent 0.85–0.95, and we had assumed the comparison was
  unflattering by a factor of three or four. It is not: the two exponents
  apply to different state variables, and the comparable quantity is the
  reduced-form price flexibility \(d\log p/d\log H\). Measured on uniform
  harvest shortfalls, ours is **5.49 (wheat), 2.96 (maize), 4.88 (rice)**,
  against the 6.7 / 4.0 / 5.0 implied by our own demand elasticities and
  your 3.0–3.5. We had this one wrong in our own disfavour and are
  recording it as such.
- **But our price map is discontinuous at its own reference.** The same
  experiment found that an arbitrarily small harvest shortfall moves the
  mean price *down* by 9.5% for wheat and 22.6% for maize, after which the
  response is smooth and correctly signed. That step is the gap between the
  reference we pin and the rest point the offer-price law actually has, and
  it is the sharpest statement we can make of the problem in §2: not merely
  that an identity is enforced rather than derived, but that the model as a
  map jumps by up to a quarter in response to an infinitesimal shock. It is
  the strongest argument for the exporter first-order condition, which
  would be continuous in the state by construction.
- **On the number of free parameters, we think the criticism does not
  survive the comparison.** Counting from your Tbl. D.8, Tbl. D.1, the
  harvest-expectation submodel and Tbl. D.10, Agrimate carries roughly 21
  numerical parameters, two of them per-region vectors over 28 regions.
  Gate 0 carries 20. We do not raise this to score a point — the honest
  difference is **provenance, not quantity**. Yours are elasticities,
  timescales and costs with external referents. Two of ours, the rival
  markup and the target fill that sets the offer law's rest point, have no
  such referent, and those two are exactly what the exporter first-order
  condition would retire.
- **Two things in your supplement narrowed the storage gap more than we
  expected, and one widened it.** Your interest rate \(\rho\) and spoilage
  rate \(\delta\) are both **zero** at default (Tbl. D.8), so the
  finite-horizon programme carries, as shipped, neither discounting nor
  decay — the only intertemporal force is the unit storage cost
  \(p_{\rm sto}=0.1/N_{\rm year}\). That matters for us in two ways: the
  distance from our cover rule to your supplier is smaller than the phrase
  "competitive storage" suggests, and any first-order condition we adopt
  does not need an interest rate to stay inside the lineage. Second,
  \(x_{\min}=0.2\) constrains your optimiser to spread at least a fifth of
  expected sales evenly, which is a stabiliser of the same kind we would
  need to stop an exporter emptying its silo in one fortnight; if we adopt
  one we will cite yours rather than apologise for ours. What widened the
  gap is that your reference state is a Nash equilibrium with annually
  periodic storage and sales (Suppl. §D.7.4.1), where ours is a
  climatological run with no equilibrium condition imposed. We checked
  whether ours is at least periodic in practice and it is — start-of-year
  world stock converges geometrically, and by 2010 it is stable to a few
  tenths of a per cent a year — but that is a property we observed, not one
  we imposed.
- **Already answered, without a change:** a surplus lowers the price.
  Controlled ±1% and ±2% harvest shocks move the price roughly
  symmetrically through the scarcity ratio. The one-sided unmet term is a
  different object.
- **Your "hard bounds would give similar behaviour" is false.** Replacing
  the partial-adjustment and smoothing knobs with 0/1 bounds moves maize
  correlation from +0.71 to +0.22. The knobs are doing work.
- **Still weaker:** the store-versus-sell decision. The cover rule is a
  target-stock heuristic. Backing out the newsvendor penalty that would
  rationalise the safety stock produces ratios of \(10^{5}\) to \(10^{6}\).
  We prototyped the obvious close — set each exporter's offer price to a
  markup over the marginal value of own accessible stock, which is exactly
  \(U'(F_i)\) for the CRRA felicity the scarcity term already implies.
  That law has a rest point at the reference without the pin, passes all
  four robustness tests, and does not need the rival markup. The prototype
  was scored on the pre-CES ask law, not against the current official
  maize +0.778 path. Like-for-like on that path: wheat +0.720 → +0.576,
  maize +0.712 → +0.339, rice +0.678 → +0.194. With CES kept, foc+ces
  maize is +0.468 (wheat +0.543, rice +0.187). Either comparison costs
  the crisis; we did not ship it.
- **Rice trade is half residual.** 47% of rice shipments bypass the
  FAOSTAT pattern (wheat 12%, maize 4%). The network is doing less work
  for rice than the note suggests.
- **A question about priority that we would rather raise ourselves.** Your
  §5.4 asks the same question Gate 0's headline asks, with the same
  three-scenario design: an unperturbed baseline, production anomalies, and
  production anomalies plus export restrictions. You report that in 2007
  production failures contributed +13.7 \$/t (+13.2%) against restrictions'
  +16.7 \$/t (+16.2%); that in 2008 restrictions raised the price to a
  similar extent as the production failures, +23.3 \$/t (+22.5%) combined;
  and that the 2010/11 hike was "mainly driven by the export restrictions",
  at +5.6% and +12.3%. Our attribution result — restrictions as the leading
  2007/08 channel — is therefore in agreement with a result you have
  already published, on a design you have already used, for wheat. We think
  what remains genuinely new is that it holds across wheat, maize **and**
  rice, with rice's 2010/11 correctly coming out as a decline rather than a
  rise, and that the restriction channel sits on an endogenous-policy gate.
  But we would rather hear from you now than from a referee later whether
  you read Gate 0's attribution as a cross-commodity extension of your §5.4
  or as a restatement of it. It changes how we frame the paper.
- **The paper's thesis is intact.** Restrictions are a first-class object
  on the market's own clock. That is the thing SHEAF does that Agrimate
  does not. Gate 0 is a strong enough host on the quantity side and a
  usable host on the incentive side: exporter revenue at own offer price
  differs from revenue at the world price by 5–15%, so a government's
  objective is representable. It is not yet as strong as Agrimate on the
  decision that produces the surplus those restrictions act on.

## 5. What we propose next

1. **Settle the rival markup.** External basis, explicit reduced-form
   relabel, or derive it from the exporter problem in the bullet above.
   We would take your view on which.
2. **Decide the offer-price law.** Keep the conditional and document it, or
   rebuild so a quiet market is a genuine rest point. The FOC prototype is
   the candidate; the cost is now measured. We think the discontinuity
   measurement in §4 raises the stakes on this decision: a step of 9.5% to
   22.6% at the origin is harder to defend in print than an enforced
   identity, because it is a statement about the model as a map rather than
   about one of its conventions.
3. **Settle the attribution headline** — pinned or like-for-like.
4. **Storage.** The remaining gap versus Agrimate. We will not clone the
   commercial-supplier agent and call it SHEAF. If there is a one-line
   store-versus-sell condition you would accept as in the lineage, we
   would rather hear it than invent one.
5. **Rice residual pool.** Diagnose before redesigning. 47% is large
   enough that the FAOSTAT pattern may be the wrong object for rice, not
   merely a thin one.
6. **Contemporaneous demand.** Well posed and cheap, but small. Record,
   do not change.
7. **Report the reproducibility of every headline score, not just its
   value.** The maize episode in §1 is the lesson we take most seriously
   from this round. The number was not wrong by a little; it was drawn from
   a range spanning +0.28 to +0.83, and nothing in how we were reporting it
   would have revealed that. We propose to publish, alongside each score, its
   spread under a small perturbation of the in-sample climatology, and to
   treat a wide spread as a finding about the model rather than as noise to
   be averaged away. Wheat's spread is 0.006 and rice's is 0.000, so the
   diagnostic is discriminating rather than uniformly pessimistic.
8. **Price-responsive restock demand.** Roughly 86–99% of our market demand
   currently sits in a restock branch with no price term in it, which puts
   the effective elasticity of demand facing the world market at −0.05 to
   −0.11 against your purchaser's ≈−0.35. Expressing that branch in your
   CES form raises ours to −0.38 / −0.48 / −0.40 and moves every score by
   less than 0.02 in correlation. We have not shipped it, because unlike the
   three changes above it alters what the demand side *is* rather than
   repairing an inconsistency, and we would rather put the specification
   question to you first.

## 6. What we would like from you

- Confirmation on the two transcription questions in §3.
- Your view on the rival markup, and on whether the exporter FOC we
  prototyped is the object you meant by an optimisation principle, or
  whether you meant something closer to the commercial-supplier programme.
- Whether §4.2 of the note describes Agrimate's storage treatment
  accurately. We have tried to state it from the published description
  rather than assume it.
- Your reading of the priority question in §4: is Gate 0's attribution a
  cross-commodity extension of your §5.4, or a restatement of it?
- Whether you would accept, as inside the lineage, a stabiliser on an
  exporter first-order condition of the kind your \(x_{\min}\) provides. We
  ask because the honest objection to our prototype is that such a device
  is another reduced-form knob under a better name, and the answer depends
  on whether you regard yours that way.
