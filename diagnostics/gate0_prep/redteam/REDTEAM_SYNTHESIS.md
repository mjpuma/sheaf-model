# Gate 0 vs Agrimate — red-team synthesis

Three independent adversarial passes (optimisation, clearing, census)
plus the earlier A1–A5 sweep. This file is the adjudication, not a
vote. Measurements live under `optimisation/`, `clearing/`, `census/`.
Per-axis write-ups: `optimisation/REDTEAM_OPTIMISATION.md`,
`clearing/REDTEAM_CLEARING.md`, `census/REDTEAM_CENSUS.md`.
Scripts under `scripts/scratch/redteam_*.py`.

**Goal the principal investigator set:** SHEAF Gate 0 as strong or
stronger than Agrimate on economic realism and optimisation, then
update the Potsdam letter. **What we actually shipped:** three
changes, each repairing an internal inconsistency rather than
recalibrating — the dead Armington competition (this pass), plus two
from a parallel pass that read the Agrimate paper and ODD supplement
directly, namely a bounded scarcity ratio in the asymmetric
negative-accessible-stock regime and valuing shipments at the offer
price that allocated them (Agrimate Eq. D.4). Those two are written up
in `diagnostics/redteam/r0/R0_REPORT.md` and adjudicated in
`diagnostics/redteam/ADJUDICATION_R2_R3.md`. **What we did not ship:**
an exporter FOC in place of the ask law, two-sided unmet demand,
tatonnement, price-responsive restock demand, or Agrimate's commercial
store-versus-sell agent. Each was prototyped and scored.

**Current official scores after all three** (supersedes the table in
"What was shipped" below, which reports change 1 only):

| crop | corr | 2007/08 | 2010/11 | observed |
|---|---|---|---|---|
| wheat | **+0.687** | ×2.09 | ×1.31 | ×1.82, ×1.16 |
| maize | **+0.792** | ×2.05 | ×1.52 | ×1.84, ×1.44 |
| rice | **+0.676** | ×1.54 | ×0.84 | ×1.84, ×0.79 |

Total absolute error over all six hike windows falls 1.421 → 1.060.
Wheat loses 0.033 correlation and rice's 2007/08 undershoot deepens;
those are the costs of the correctness fixes, not their justification.
All twelve assertions pass.

## Scorecard (Gate 0 vs Agrimate)

Verdicts use CLAUDE.md classes. "Stronger" here means stronger as an
economic model of the 2007/08 crisis market, not a higher correlation.

| Mechanism | Agrimate (established from Kuhla et al. 2025 as cited in-repo; inferred flagged) | SHEAF Gate 0 | Verdict |
|---|---|---|---|
| Importer sourcing | CES / Armington over origins, price-responsive (Agrimate Eq. 8c, as described in `diagnostics/redteam/r2/`) | **Was** destination-share reweight, algebraically the identity. **Now** CES source-share reweight, the FOC of expenditure minimisation | Was Agrimate stronger (B, 95–100%). Now **parity** on this channel (H) |
| Storage / store-vs-sell | Commercial supplier maximises finite-horizon expected profit (established as their design; exact horizon/discount from the paper not re-derived here) | Cover target \(T=L+s\); leftover offered. No \(r\), no \(E[p]\) | **Agrimate stronger** (D/E, 80–95%). Implied newsvendor penalty ratios are \(10^{5}\)–\(10^{6}\) — the safety stock is not a competitive-storage optimum (`cover_newsvendor.csv`) |
| Exporter pricing | Inferred: oligopolist / offer adaptation with a rest point | Adaptive fill law + rival markup. **No rest point at \(p_0\)** without an explicit pin | **Agrimate stronger** on the rest point (G on our claim; the pin is B-adjacent). An FOC \(q_i=\mu\,p^{\mathrm{scar}}_i\) restores the rest point and passes all four asserts, but maize corr falls \(+0.71\to+0.34\) (`foc_scores.csv`). Not shipped |
| Demand | CES with a budget (inferred from r2's Agrimate comparison) | Isoelastic food/feed on the lagged world price; industrial inelastic | Different-by-design (D). Gap to contemporaneous \(p_t\) is 0.3–0.9% of world use |
| Market clearing | Agent programmes; quantities and prices from the same problem (inferred) | Short-side bilateral + residual pool; price from a separate blend. Mass balance closes to \(10^{-14}\) MMT. World ship = world recv | Different-by-design (E). Not Walrasian: \(\mathrm{sign}(\Delta p)\) agrees with excess demand at 40–53% of steps (`clr_signs.csv`) |
| Residual / unlisted trade | Network is the market (inferred) | Residual pool share: wheat 12%, maize 4%, **rice 47%** | **Agrimate stronger** for rice (F, 95–100%). Nearly half of rice trade bypasses the FAOSTAT pattern |
| Glut / surplus | Price falls when stock is abundant (their sitting question) | Surplus **does** lower the price through the scarcity ratio, roughly symmetrically at 1–2% shocks (`clr_glut_permanent.csv`). The unmet channel is one-sided and is a different object | **H** — their glut question is already answered. Two-sided unmet is not the glut channel and mixed the scores |
| Restrictions | Exogenous | Gate 0: exogenous AMIS. Gate 2: endogenous (claimed contribution) | SHEAF stronger **as a research programme** (E). Gate 0 is a usable host: exporter revenue at own \(q_i\) vs world \(p\) differs by 5–15% (`clr_gate2_revenue.csv`), so a government incentive is representable, but the two-price seam is real |
| Expectations | Adaptive, stay close unless new info (their instruction) | Blend \(\phi H+(1-\phi)H^{\mathrm{seas}}\) over the lean window. Mean lead 5–8 steps, not 10 years. Agrimate-equivalent \(\phi\) is 0.75/0.48/0.80 vs our 0.55/0.50/0.55 | Close enough (D). Adaptive EWMA moves scores by at most 0.41 on their probe metric; not a defect |
| Scarcity ratio, extreme regime | Isoelastic inverse demand on a flow, bounded by construction (Suppl. D.7.4.1) | **Was** unbounded when accessible stock went negative while the reference stayed positive: ratio 35.1, price ×4.13 in one step, and maize's correlation not reproducible (spread 0.557 under a 1% recalibration). **Now** floored on physical stock in that case only | Was Agrimate stronger (**C, 95–100%**). Now **parity** (H). Wheat and rice bit-identical; maize spread 0.557 → 0.051 |
| Transaction pricing | Transaction price is the offer the request responded to (Eq. D.4, explicit) | **Was** shipments allocated at the pre-update ask and valued at the post-update ask, a rally-directional bias of +2.2/+1.9/+3.9% through 2007/08. **Now** valued at the allocating ask | Was Agrimate stronger (**B, 95%**). Now **parity** (H) |
| Price-response steepness | \(\alpha=3\) world, \(\alpha_I=3.5\) international, on flows | Measured price flexibility \(d\log p/d\log H\) = 5.49 / 2.96 / 4.88 | **Parity or better (H, 80–95%).** Our prior that SHEAF was 3–4× too flat was **false** — the exponents apply to different state variables |
| Continuity of the price map | Continuous in the state | **Step discontinuity at zero anomaly:** mean price −9.5% (wheat), −22.6% (maize) for an infinitesimal shortfall, smooth and monotone beyond | **Agrimate stronger (A, 95–100%).** Sharpest form of the rest-point problem; the FOC would fix it by construction |
| Effective demand elasticity | Purchaser CES, ≈ −0.35 | 86–99% of market demand in a price-free restock branch; measured −0.05 / −0.11 / −0.09 | **Agrimate stronger (D, 95%).** CES form raises ours to −0.38/−0.48/−0.40 for <0.02 corr. Not shipped — specification question, not a bug |
| Discounting and decay in storage | \(\rho=0\) **and** \(\delta=0\) at default (Tbl. D.8); only \(p_{\rm sto}=0.1/N_{\rm year}\) bites | No \(r\), no decay | **Closer to parity than assumed (D).** Any FOC repair needs no interest rate to stay in the lineage |
| Optimiser stabiliser | \(x_{\min}=0.2\): ≥20% of expected sales spread evenly (Tbl. D.8) | n/a — no optimiser | **Precedent, not a gap.** If a SHEAF FOC needs a stabiliser, that is parity, citable |
| Reference state | Nash equilibrium, annually periodic storage and sales (Suppl. D.7.4.1) | Climatological twin, no equilibrium imposed. Measured: start-of-year stock converges geometrically, stable to a few tenths of a %/yr by 2010 | **Agrimate stronger (E, 90%).** Ours is periodic in practice but not by construction |
| Attribution design | §5.4 uses the same three scenarios and reports restrictions as the leading 2007/08 and 2010/11 driver for wheat | Same design, three crops | **Priority question, not a defect (F).** Gate 0 agrees with a published Agrimate result; what is new is the cross-commodity span |
| Parameter count | **Counted, not inferred: ≈21 numerical parameters** (Tbl. D.8 fifteen agent + Tbl. D.1 two timescales + two harvest-expectation + Tbl. D.10 two), two of them per-region vectors over 28 regions | 20 numerical `CropParams` fields (24 less 4 structural); 18 scored knobs, 3 exact collinear pairs (`ask_alpha`~\(`ask_target_fill\), `block_kappa`~\(`ask_rival\), `max_stu`~\(`warehouse_lambda`)). `ask_comp_elast` was **exactly** inert; it is not, after the CES fix. Hard bounds do **not** reproduce official scores (maize corr \(+0.71\to+0.22\) with all three hard bounds) | Their "hard bounds would give similar behaviour" is **false** (H, 95–100%). Collinearity of `ask_rival` with `block_kappa` is the live identification issue (F) |

## The FOC idea, resolved

Hypothesis: replace the ask law with
\(q_{i,t}=\mu\,p_0\bigl((F^{\mathrm{twin}}_{i,t}+f_i)/(F_{i,t}+f_i)\bigr)^\eta\),
dropping `ask_alpha`, `ask_target_fill`, `ask_beta`, `ask_rival`.

| Test | Result |
|---|---|
| Quiet-market rest point without the pin | **Pass.** Drift \(0.00\%\) for all three crops (`foc_calm_rest_point.csv`) |
| Four robustness asserts | **Pass** at \(\mu=1\) (`foc_robustness.csv`) |
| Maize sign condition without `ask_rival` | **Pass** (lift \(+0.07\)) |
| Official scores | **Fail.** Wheat \(+0.720\to+0.576\), maize \(+0.712\to+0.339\), rice \(+0.678\to+0.194\) |

So the idea does what the sitting asked — it is an optimisation principle
and it removes four reduced-form knobs — and it cannot be the default
without giving up the crisis amplitudes the model exists to produce.
Category **D**, not B: the ask law is a disclosed reduced form, not a
miscoded FOC. Complexity-budget verdict: do not adopt.

## What was shipped

**CES source-share reweight** (`_ask_reweight_src`). Destination
reweighting is the identity (max \(|A_{\mathrm{eff}}-A|=10^{-16}\)).
Source reweighting is the CES FOC and moves shares (max \(|S_{\mathrm{eff}}-S|=0.29\)
on a probe). All twelve asserts still pass.

Official scores, before → after (full leg):

| crop | corr | 2007/08 | 2010/11 |
|---|---|---|---|
| wheat | +0.720 → **+0.728** | ×2.27 → ×2.28 | ×1.45 → ×1.45 |
| maize | +0.712 → **+0.778** | ×1.97 → ×2.20 | ×1.70 → ×1.59 |
| rice | +0.678 → **+0.678** | ×1.72 → ×1.72 | ×0.82 → ×0.82 |

Maize moved because the twin is rebuilt under the same law, so the
scarcity ratio sees the new allocation. That is a consequence of
making the documented mechanism real, not a retune. `ask_rival`
remains load-bearing after the fix (maize corr \(+0.778\to+0.520\) at
zero).

## What a referee would reject us for

**Added by the parallel pass, and arguably ahead of storage in
severity: we were reporting a score that was not reproducible.** Maize's
published correlation of +0.712 moved to +0.276 or +0.832 under a ~1%
change in the in-sample climatology, and nothing in how we reported it
would have exposed that. The cause is now fixed and the spread is 0.051,
but the lesson generalises past this one number: a headline fit should be
published with its spread under perturbation, or it is not evidence. Wheat
(0.006) and rice (0.000) show the diagnostic discriminates rather than
condemning everything.

**Second, the price map is discontinuous at its own reference** — a step
of −9.5% (wheat) and −22.6% (maize) for an infinitesimal shortfall. This
is the rest-point problem stated as a property of the map rather than of a
convention, and it is materially harder to defend in print.

The cover rule is not an intertemporal decision. Agrimate's commercial
agent chooses store versus sell from expected profit; we offer the
residual above a lean-season target. The implied carry that would
rationalise observed withholding is a coin-flip of signs, and the
implied newsvendor penalty is astronomical. That is the one place
where "SHEAF is as strong as Agrimate" is currently false, and the
FOC that would close it costs the crisis. Until that is either
derived or explicitly scoped as a disclosed simplification, a
storage referee has a clean shot.

## One thing SHEAF does that is genuinely better

The restriction is a first-class object on the same clock as the
market, with a signed robustness condition and an endogenous-policy
gate in front of it. Agrimate takes restrictions as given. That is
the paper's thesis. Gate 0 is a strong enough host for it on the
quantity side (offers fall when \(\tau\) is on; mass balance closes)
and a usable host on the incentive side (own-\(q\) revenue is not
identical to world-\(p\) revenue). It is not yet as strong as
Agrimate on the decision that produces the surplus those
restrictions act on.
