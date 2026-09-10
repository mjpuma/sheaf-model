# Response to the Potsdam sitting, 30 August 2026

To: Kuhla, Kubiczek, Otto
From: the SHEAF team
Accompanies: `overleaf/gate0_discussion/main.pdf` (20 pp., revised)

Thank you for the sitting. This is not a list of things we intend to do. It
is what your questions turned up when we went and checked, what we changed
as a result, and where we would value your judgement.

The short version. Your questions sent us to compare the written equations
against the executed code, and then to red-team Gate 0 against Agrimate on
optimisation, clearing, and the rest of the formulation. Four of the note's
statements were wrong. One coding bug was also an optimisation gap: the
Armington competition you would recognise as Eq. 8c was algebraically the
identity, so cheaper origins never gained share. That is now a CES
source-share reweight — the first-order condition of expenditure
minimisation — and it is the one model change we shipped. An exporter
first-order condition that would give the offer-price law a rest point, and
remove four reduced-form knobs, restores the quiet market but costs the
crisis; we prototyped it and did not adopt it. The restriction channel is
the leading 2007/08 channel in all three crops once a contaminated
comparison is repaired. Storage is the place Gate 0 is still weaker than
Agrimate.

---

## 1. What we changed

**The one equation change.** Destination-share reweighting
\(\tilde A_{ij}\propto A_{ij}(p_0/q_i)^\gamma\), renormalised by exporter,
is the identity: a row-constant cancels. `ask_comp_elast` therefore did
nothing, against the note, the parameter comment, and Agrimate Eq. 8c.
Importer source shares are now the CES mix,
\(\tilde S_{ij}\propto S_{ij}(p_0/q_i)^\gamma\), renormalised by importer.
All twelve robustness assertions still pass. Official scores, full leg,
before → after:

| crop | corr | 2007/08 | 2010/11 | observed 07/08, 10/11 |
|---|---|---|---|---|
| wheat | +0.720 → **+0.728** | ×2.27 → ×2.28 | ×1.45 → ×1.45 | ×1.82, ×1.16 |
| maize | +0.712 → **+0.778** | ×1.97 → ×2.20 | ×1.70 → ×1.59 | ×1.84, ×1.44 |
| rice | +0.678 → **+0.678** | ×1.72 → ×1.72 | ×0.82 → ×0.82 | ×1.84, ×0.79 |

Maize moved because the twin is rebuilt under the same law. That is a
consequence of making the documented mechanism real, not a retune.

**Note corrections (no score effect).** The scarcity regulariser is 5% of
world safety stock plus a state-dependent term, not a small constant, and
biases the rice scarcity ratio by 35% on average. The unmet-demand channel
is truncated at zero and the truncation binds at 92 / 59 / 100 of 144 steps.
The trade-weighted price uses this period's asks, and falls back to the
previous world price when nothing ships — a jump of up to 12 $/t that was
missing from the printed equation. The reference identity is enforced, not
derived — see §2.

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
priced by the ask law, whose quiet level is 0.66 and 0.71 of the reference
for wheat and maize. The measured lift therefore included the release of
that pin, biased down by 27 points for maize.

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
  four robustness tests, and does not need the rival markup. It also
  takes wheat correlation from +0.73 to +0.58, maize from +0.78 to +0.34,
  and rice from +0.68 to +0.19. We did not ship it.
- **Rice trade is half residual.** 47% of rice shipments bypass the
  FAOSTAT pattern (wheat 12%, maize 4%). The network is doing less work
  for rice than the note suggests.
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
   the candidate; the cost is now measured.
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

## 6. What we would like from you

- Confirmation on the two transcription questions in §3.
- Your view on the rival markup, and on whether the exporter FOC we
  prototyped is the object you meant by an optimisation principle, or
  whether you meant something closer to the commercial-supplier programme.
- Whether §4.2 of the note describes Agrimate's storage treatment
  accurately. We have tried to state it from the published description
  rather than assume it.
