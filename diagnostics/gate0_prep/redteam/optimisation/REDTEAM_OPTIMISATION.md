# Red team / optimisation — Gate 0 vs Agrimate

Adversarial pass on whether Gate 0's price and storage objects are
optimisation principles, or disclosed reduced forms. Read-only on
`sheaf/*.py`. Measurements live in this directory; scripts under
`scripts/scratch/redteam_opt_*.py`. Adjudication is
`../REDTEAM_SYNTHESIS.md`; this file is the specialist record.

CES origin-share reweight is already shipped (`929cec4`, `9f69a36`).
The exporter FOC was prototyped and **not** shipped. This report does
not reopen either decision.

Official scores cited below are the **pre-CES** ask-law path unless a
row is labelled `ces` or `foc+ces`. After the CES ship, official maize
corr is +0.778; like-for-like FOC-with-CES-kept is +0.468
(`foc_scores.csv`, `POTSDAM_RESPONSE.md` §4, `../VERIFICATION.md` §C).

## What was asked

Potsdam: do we need an optimisation principle? Agrimate's commercial
supplier maximises finite-horizon expected profit; Gate 0 has a cover
target and an adaptive ask law. The pass tests, in order: (1) whether
the documented Armington reweight was already an FOC; (2) whether any
shipped object *is* an FOC; (3) whether replacing the ask law with an
exporter FOC restores a quiet-market rest point without costing the
crisis.

## Probe map

| Script | CSV | Question |
|---|---|---|
| `redteam_opt_01_reweight_noop.py` | `reweight_noop.csv` | Destination reweight \(\tilde A\) is the identity |
| `redteam_opt_02_objectives.py` | `pscar_utility.csv`, `cover_newsvendor.csv` | Is \(p^{\mathrm{scar}}\) a \(U'(F)\)? Is \(T\) a newsvendor? |
| `redteam_opt_03_exporter_foc.py` | `foc_scores.csv`, `foc_robustness.csv`, `foc_calm_rest_point.csv`, `foc_ask_rival.csv` | Replace the ask law with \(q_i = \mu\,p^{\mathrm{scar}}_i\) |
| `redteam_opt_04_foc_diagnosis.py` | `foc_dispersion.csv`, `foc_psi_family.csv` | Why the FOC costs amplitude |
| `redteam_opt_05_eta_and_clip.py` | `foc_eta_sweep.csv`, `ask_clip_sensitivity.csv`, `eta_empirical.csv` | \(\eta\) and ask clips as substitutes for the FOC |
| `redteam_opt_06_regulariser.py` | `foc_regulariser_sweep.csv` | Scarcity regulariser under the FOC |
| `redteam_opt_07_scarcity_signal.py` | `scarcity_signal.csv` | Which stock object should enter scarcity |
| `redteam_opt_08_flow_scarcity.py` | (see `scarcity_signal.csv` / summary) | Flow vs stock scarcity |
| `redteam_opt_09_omega_sweep.py` | `omega_sweep.csv`, `summary_best_configs.csv` | \(\omega\) retunes exist; not adopted |

`foc_eta_sweep.csv` is present. Flow-scarcity does not have a
separately named CSV beyond `scarcity_signal.csv`; if a claim needs a
flow-only table, it is missing.

## 1. Destination reweight was dead — and that *was* the optimisation gap

`reweight_noop.csv`. For every crop, \(\max|\tilde A - A|\) is
\(2.2\)–\(3.3\times 10^{-16}\). Full scored runs are bit-identical
across \(\gamma \in \{0, 0.25, 1.25, 5, 50\}\) up to \(10^{-13}\). Own
price derivative of own shipments is \(10^{-16}\). Census `cen04` and
R2 had the same identity.

Category **B** on the pre-fix claim that cheaper origins gained
destination share; **H** on the algebra. Confidence **95–100%**. The
CES *source*-share reweight that replaced it is the FOC of expenditure
minimisation (`../VERIFICATION.md` §A). That is the one optimisation
gap that was also a coding bug, and the one that shipped.

## 2. What already is an FOC, and what is not

**Scarcity term.** `pscar_utility.csv`: \(p^{\mathrm{scar}} = p_0 r^\eta\)
with \(r = (F^{\mathrm{twin}}+f)/(F+f)\) equals \(U'(F)\) for CRRA over
accessible stock to \(\max|U'-p^{\mathrm{scar}}| = 0\) on all three
crops. The \(\kappa_u/\kappa_b\) multipliers are a wedge on top of that
\(U'\) (mean wedge 1.4–2.1; rice regulariser share of the scarcity
ratio is 3.67 — the letter's "35% rice bias" is the same object,
stated as a percent of the ratio rather than this share column).
Category **H**. Confidence **95–100%**.

**Cover rule.** `cover_newsvendor.csv`. If \(s_i = z_i \sigma_{L,i}\)
were a newsvendor safety stock, the implied stockout:carry penalty is
astronomical. Forecast-error \(z\) is 10–30 on wheat/maize USA-scale
nodes and hundreds to thousands on rice; interannual \(z\) is still
3–8. Synthesis's \(10^{5}\)–\(10^{6}\) is the rice forecast-error
ratios; wheat/maize USA interannual ratios are \(10^{3}\)–\(10^{6}\).
Either way this is not a competitive-storage optimum. Category **D/E**,
confidence **80–95%**. A4's implied-\(r\) coin-flip
(`../../a4/implied_carry.csv`) is the same conclusion from the other
side of the Euler.

**Ask law.** Not an exporter FOC. Probe 1 already had
\(\partial X_i / \partial q_i = 0\) under destination reweighting.

## 3. Exporter FOC — prototyped, scored, rejected

Candidate, dropping `ask_alpha`, `ask_target_fill`, `ask_beta`,
`ask_rival`:

\[
q_{i,t} = \mu\, p_0 \left(\frac{F^{\mathrm{twin}}_{i,t}+f_i}{F_{i,t}+f_i}\right)^\eta.
\]

`foc_calm_rest_point.csv`. Quiet market with the pin off:

| crop | ask, pin off | foc, pin off | passes 2% |
|---|---|---|---|
| wheat | 25.6% drift | 0.00% | FOC yes; ask no |
| maize | 34.2% | 0.00% | FOC yes; ask no |
| rice  | 19.5% | 0.00% | FOC yes; ask no |

That is the sitting's rest-point question, answered. `foc_robustness.csv`:
all four asserts pass at \(\mu=1\) for ask, ces, foc, and foc+ces.
`foc_ask_rival.csv`: under the FOC, `ask_rival` is inert (maize
foc+ces corr +0.468 at both 0 and 0.80), which is the point of removing
it.

Official scores, `foc_scores.csv` \(\mu=1\):

| crop | ask (pre-CES) | foc | foc+ces |
|---|---|---|---|
| wheat | +0.720 | +0.576 | +0.543 |
| maize | +0.712 | **+0.339** | **+0.468** |
| rice  | +0.678 | +0.194 | +0.187 |

Hike ratios collapse with the correlation: maize 2007/08 ×1.97 → ×1.27
(foc) / ×1.29 (foc+ces). \(\mu \in \{1.1, 1.25\}\) does not recover the
crisis. `foc_regulariser_sweep.csv` under foc+ces: maize corr stays
0.45–0.47 as the regulariser coefficient falls; rice corr falls further
and the restriction sign test fails at 0.01 and below.

Letter numbers (`POTSDAM_RESPONSE.md` §4; `../VERIFICATION.md` §C.1):
pre-CES maize **+0.712 → +0.339**; CES-kept **+0.468**. Do not mix the
post-CES official +0.778 with the pre-CES FOC endpoint. Qualitative
rejection is the same on either path.

`foc_dispersion.csv`: the FOC pins asks near \(p^{\mathrm{scar}}\)
(maize sd of \(q/p_0\) 0.11 ask → 0.30 foc, but mean \(q\) falls 1.40 →
0.92). The shipped ask law is an amplitude machine with a rival markup;
the FOC is a rest point. They are different objects.

**Classification.** **D**, not B: the ask law is a disclosed reduced
form, not a miscoded FOC. Decision **H** (prototyped, not shipped).
Confidence **95–100%** on the scores; **80–95%** that no nearby
\(\mu/\eta\) recovers 2007/08 without putting the markup back.
Complexity-budget: do not adopt. Four knobs removed, crisis given up.

## 4. Retunes that were not shipped

`summary_best_configs.csv`. Higher-corr \(\omega\) configs exist (wheat
+0.80, maize +0.82, rice +0.75) against shipped +0.72 / +0.71 / +0.68.
Synthesis correctly did not retune: those rows are in-sample score
shopping on the crisis window. `ask_clip_sensitivity.csv`: the 2.8\(p_0\)
ceiling is load-bearing for rice (corr +0.42 at 1.6\(p_0\), +0.68 at
shipped 2.8, +0.72 at 4.0) and for wheat in the other direction.
`eta_empirical.csv`: regression \(\eta\) on annual world STU vs price
is noisy and often below the shipped `inv_eta`; not a basis to move
`inv_eta`.

Category **H** that the retunes exist and were not adopted.
Confidence **95–100%**.

## What is thin

- No separate flow-scarcity CSV with a name of its own. Claims about
  flow vs stock scarcity rest on `scarcity_signal.csv` plus the
  synthesis sentence; if a referee wants the flow-only table, it is
  not here.
- FOC scores are on a monkeypatched `_simulate_window`, not a branch of
  `sheaf/dynamic_crop.py`. The CES *ask* column in `foc_scores.csv`
  (maize +0.712) does not rebuild the twin; live CES does, which is why
  official maize is +0.778. Named in `../VERIFICATION.md`. Not a
  disagreement once that is named.
- Cover newsvendor ratios depend on the \(\sigma_L\) proxy
  (forecast-error vs interannual). Both reject a competitive-storage
  reading; the \(10^{5}\)–\(10^{6}\) sentence is rice-true and
  wheat/maize-overstated if read as USA-scale interannual.

## Classification summary

| Claim | Class | Confidence |
|---|---|---|
| Dest reweight is the identity | H (algebra); B (pre-fix docs) | 95–100% |
| \(p^{\mathrm{scar}} = U'(F)\) for CRRA over accessible stock | H | 95–100% |
| Cover is not a newsvendor / Euler | D/E | 80–95% |
| Exporter FOC restores the rest point and costs the crisis | H (decision); D (ask law) | 95–100% |
| Pre-CES maize +0.712 → +0.339; CES-kept +0.468 | H | 95–100% |
| \(\omega\) retunes exist; not adopted | H | 95–100% |

Nothing here recommends a model change. The CES ship and the FOC reject
are already closed.
