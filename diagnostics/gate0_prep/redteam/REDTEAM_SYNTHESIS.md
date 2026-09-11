# Gate 0 vs Agrimate — red-team synthesis

Three independent adversarial passes (optimisation, clearing, census)
plus the earlier A1–A5 sweep. This file is the adjudication, not a
vote. Measurements live under `optimisation/`, `clearing/`, `census/`.
Per-axis write-ups: `optimisation/REDTEAM_OPTIMISATION.md`,
`clearing/REDTEAM_CLEARING.md`, `census/REDTEAM_CENSUS.md`.
Scripts under `scripts/scratch/redteam_*.py`.

**Goal the principal investigator set:** SHEAF Gate 0 as strong or
stronger than Agrimate on economic realism and optimisation, then
update the Potsdam letter. **What we actually shipped:** one coding
bug that was also an optimisation gap (dead Armington competition).
**What we did not ship:** an exporter FOC in place of the ask law,
two-sided unmet demand, tatonnement, or Agrimate's commercial
store-versus-sell agent. Each was prototyped and scored.

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
| Parameter count | Fewer free reduced-form knobs (inferred) | 18 scored knobs, 3 exact collinear pairs (`ask_alpha`~\(`ask_target_fill\), `block_kappa`~\(`ask_rival\), `max_stu`~\(`warehouse_lambda`)). `ask_comp_elast` was **exactly** inert; it is not, after the CES fix. Hard bounds do **not** reproduce official scores (maize corr \(+0.71\to+0.22\) with all three hard bounds) | Their "hard bounds would give similar behaviour" is **false** (H, 95–100%). Collinearity of `ask_rival` with `block_kappa` is the live identification issue (F) |

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
