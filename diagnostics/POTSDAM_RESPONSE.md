# Response to the Potsdam sitting, 30 August 2026

To: Kuhla, Kubiczek, Otto
From: the SHEAF team
Accompanies: `overleaf/gate0_discussion/main.pdf` (19 pp., revised)

Thank you for the sitting. This is not a list of things we intend to do. It
is what your questions turned up when we went and checked, what we changed
as a result, and where we would value your judgement.

The short version: your questions about the price map sent us to compare the
written equations against the executed code line by line. Four of the note's
statements were wrong, one of them materially. Correcting the measurement
that the material one had contaminated changes a headline result in your
favour — the restriction channel is now the leading 2007/08 channel in all
three crops, where maize had previously read as demand-led. No model
equation was changed and no score moved.

---

## 1. What we changed

Four corrections to the note, three fixes to code. Every official score is
unchanged to three digits: wheat +0.720 / ×2.27 / ×1.45, maize +0.712 /
×1.97 / ×1.70, rice +0.678 / ×1.72 / ×0.82 (monthly price correlation
against the deflated Pink Sheet, then the 2007/08 and 2010/11 hike ratios).

**Note corrections.** The scarcity regulariser was described as a small
constant; it is 5% of world safety stock plus a state-dependent term, which
biases the scarcity ratio by 35% on average for rice. The unmet-demand
channel was written without its truncation at zero, which binds at 92, 59
and 100 of 144 steps. The trade-weighted price was ambiguous about which
period's offer prices it uses; it uses the current ones, so offer prices are
updated twice in one causal chain. And the reference identity was described
as algebraic when it is enforced — see §2.

**Code fixes.** Unknown keyword overrides were silently dropped, so a
mistyped sensitivity study returned the baseline and reported no effect;
they now raise. The four robustness assertions could not be run under
parameter overrides, so no sensitivity study could exercise them; they now
can. And the restriction sign test was not comparing like with like, which
is §2.

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

It is also not a spurious knob: setting it to zero moves the maize
correlation from +0.712 to +0.414 and the rice 2007/08 ratio from ×1.72 to
×1.01 against an observed ×1.84. So we have a parameter that materially sets
crisis amplitude and now has no independent basis, which is the
identification problem we are least comfortable with. We would rather hear
your view than pick a story. Options as we see them: find an external basis
(the export-restriction price-transmission literature is the obvious place),
relabel it explicitly as a shared reduced-form amplitude parameter and
disclose that no sign condition pins it, or rebuild the offer-price law so
the markup emerges from an exporter problem.

**The attribution table changes.** The same pin sat in the base window of
the restriction-only leg's hike ratio.

| crop | 2007/08 τ ratio, as published | like-for-like | observed |
|---|---|---|---|
| wheat | ×1.70 | ×1.99 | ×1.82 |
| maize | ×1.10 | ×1.69 | ×1.84 |
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
| Do we need an optimisation principle? | §4.3 | The scarcity term *is* isoelastic inverse demand over accessible stock, elasticity −1/η. The blend with the mean offer price is not the stationarity condition of any single objective |
| What is the baseline? | §4.1, Fig. 2 | Four objects, all named |
| Commercial hold / competitive storage / one agent | §4.2, Fig. 3 | A4 in progress; reported separately |
| How much is sold to each market? | §3.2 eqs (6)–(8); §4.4 | FAOSTAT supplies the pattern only |
| Linear demand? Industrial use? | §3.1 eq (1); §4.5 | Isoelastic, not linear |
| Expectations: not ten-year foresight | §3.1 eq (2); §4.7 | Foresight is near-inert for wheat (0.02 on all metrics), active for maize (0.30) |
| Slide 48 / storage cost; why not dump everything? | §4.2 | Slide 48 is the ask update, not a cost of carry. **Please confirm which you meant** |
| Glut should lower p; annually? | §4.6 | The channel is one-sided by construction; now stated |
| Too many parameters | §4.8, Table 2; §5 | Ablation below |
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
determines whether this is a one-line change or a numerical project. Over
all 432 crop-steps, the map has exactly one root at every step, its
Lipschitz constant has a median of 0.02 to 0.03, and plain Picard iteration
converges in five to nine iterations. So it is a one-line root-find. Whether
it is worth doing for a 0.3% to 0.9% correction is a separate question and
we lean against, but the obstacle we expected is not there.

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

## 5. What we propose next

1. **Settle the rival markup.** External basis, explicit reduced-form
   relabel, or derive it. We would take your view on which.
2. **Decide the offer-price law.** Keep the conditional and document it, or
   rebuild the law so a quiet market is a genuine rest point. The second is
   the principled option and connects to your optimisation question; it is
   also a real change with consequences across all three crops, so we would
   not do it on the strength of one diagnostic.
3. **Settle the attribution headline** — pinned or like-for-like.
4. **Storage.** A4 is running: the cover rule's implied intertemporal
   behaviour, and which of three candidate causes produces the exporter
   stock floor. We will send it separately. This is the cluster where your
   commercial-supplier agent is the sharpest contrast, and we would rather
   bring you a measurement than a proposal.
5. **Contemporaneous demand.** Well posed and cheap, but small. Our
   inclination is to record the measurement and not change the map.

## 6. What we would like from you

- Confirmation on the two transcription questions in §3.
- Your view on the rival markup, which is the one place where we have a
  parameter doing real work without a defensible reason for its value.
- Whether the commercial-storage contrast in §4.2 of the note describes
  Agrimate accurately. We have tried to state your treatment from the
  published description rather than assume it.
