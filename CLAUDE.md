# CLAUDE.md

This file is the constitution for a multi-agent scientific verification
process on the SHEAF model. It orients Claude Code (including parallel
sub-agents) working in this repository. Its purpose right now is
preparation: mapping the repository and establishing the rules of evidence
the audit must follow. **It is not an invitation to start auditing, fixing,
or refactoring** — see Ground Rules. No audit work begins from this document.

## Governing principle

The purpose of this audit is to establish the truth status of every
important mathematical, economic, computational, and empirical claim SHEAF
makes about itself.

- Do not optimize for criticism.
- Do not optimize for praise.
- Optimize for correctness.
- Every criticism must be supported by mathematical reasoning, implementation
  evidence, executable tests, numerical counterexamples, or empirical
  evidence.
- Every positive conclusion ("this claim holds," "this code is correct")
  must be supported with the same rigor as a negative one.
- If an agent cannot establish that something is incorrect, it must
  explicitly say so, rather than implying doubt without resolving it.

Nothing in this document — including the "points warranting verification"
listed below — should be read as an established defect. Each is a question,
not a finding. Repository mapping surfaced places where a mathematical claim
and its implementation should be checked against each other; it did not
establish that any of them diverge.

## What SHEAF is

SHEAF (Substitution, Heterogeneous agents, Equilibrium, And Fragility) is a
country-level, multi-commodity, game-theoretic network model of global grain
trade. It couples three layers each period: a spatial price equilibrium
(concave QP, Takayama–Judge/Samuelson), a strategic export-restriction game
among governments (iterated best response), and a storage layer (competitive
+ government buffer stocks). Cross-commodity substitution (wheat/rice/maize
linked on the demand side) is the model's stated distinguishing feature:
zeroing it collapses SHEAF into G independent single-commodity models (the
TWIST/Agrimate-style limit — see README §6).

The full mathematical formulation is written out in
[README.md](README.md) ("Mathematical formulation" section, §1–§7) and is
claimed to match the implementation in `sheaf/core.py` symbol-for-symbol.
**Whether that correspondence (README equations ↔ code) holds is a primary
verification target** — to be established affirmatively or not, not assumed
in either direction.

[VALIDATION.md](VALIDATION.md) documents an intended two-level empirical
validation plan (Level 1: reproduce Agrimate's 2007/08 and 2010/11 hindcast
targets; Level 2: endogenous prediction of *who* restricts). At the time this
file was prepared, the scripts present in the repository (`scripts/*.py`)
build and plot diagnostic inputs but do not appear to execute a hindcast or
score model output against history. Confirm independently whether this is
still the case before relying on it — do not treat it as established without
re-checking, since the repository may have changed.

### Modeling lineage: TWIST → Agrimate → SHEAF

SHEAF is explicitly positioned as a successor in a specific lineage: TWIST
(Schewe et al. 2017, single-commodity, no endogenous restrictions) →
Agrimate (Kuhla et al. 2025, single-commodity, dynamic agent-based, exogenous
restrictions) → SHEAF (multi-commodity, endogenous restriction game). This
lineage is the correct reference frame for evaluation.

- Do not judge SHEAF against a theoretically more elaborate model merely
  because that model exists in the literature. A design choice that is
  simpler than the state of the art is not, by itself, an error.
- For the storage layer in particular: evaluate continuity with TWIST's and
  Agrimate's storage treatment *first*. Only invoke Deaton–Laroque or other
  canonical competitive-storage frameworks as a comparison after establishing
  what SHEAF's own lineage does and claims to do — a departure from
  Deaton–Laroque is not automatically a defect if it is a departure from
  something SHEAF never claimed to implement.

## Repository map

Everything the model does lives in one package, `sheaf/`, with no
subpackages. There is no separation into "market/", "game/", "storage/"
directories — all four conceptual layers are classes/functions inside a
single 487-line module.

| Path | Role | Notes |
|---|---|---|
| `sheaf/core.py` | **Model core** — demand system, spatial equilibrium (QP), storage rules, export-restriction game, `SheafModel` orchestrator | The audit's center of gravity. See "Core module internals" below for a section-by-section map. |
| `sheaf/calibration.py` | Prototype dataset: 17 named countries + a Rest-of-World residual node, hand-entered production/consumption/elasticities | Explicitly labeled "illustrative" in its own docstring, not presented as a production calibration. `build_countries()` is the entry point. |
| `sheaf/data_usda.py` | USDA PSD adapter: loads world-aggregate crop series, LOWESS detrending (hand-rolled, not `statsmodels`), stock-to-use ratios, crisis-forcing multipliers | Feeds production-shock forcing for hindcasts. |
| `sheaf/data_faostat.py` | FAOSTAT bilateral trade adapter: loads E0 matrices, resolves ISO3 via a country-conversion table + hardcoded aliases, aggregates to SHEAF's node set | Network *structure* only — its module docstring explains why production/reserves are deliberately sourced elsewhere (FAOSTAT stocks are a food-balance residual). |
| `sheaf/__init__.py` | Public API re-exports | Thin; not a modeling target. |
| `demo.py` | Black Sea wheat-shock scenario (Russia −40%, Ukraine −50%) run under substitution on/off, generates `sheaf_results.csv` and 4 figures | The one existing end-to-end run of the model; useful as a smoke test. Whether it constitutes validation is a question for the audit, not a premise. |
| `scripts/validate_forcing.py` | Builds/plots USDA-derived production anomalies and stock-to-use ratios around the 2007/08 and 2010/11 crises | Diagnostic — verify independently whether it runs SHEAF or scores anything against history. |
| `scripts/build_network.py` | Builds/plots the FAOSTAT baseline wheat network and Egypt's import-source shift across crisis windows | Diagnostic — same verification applies. |
| `data/usda_world/`, `data/faostat_network/` | Vendored input CSVs + `PROVENANCE.txt` files | Check provenance files before treating any number pulled from these as ground truth. |
| `README.md` | Full mathematical writeup, references, caveats section | A specification to check the code against — its self-description is a claim to verify, not evidence of the code's behavior. |
| `VALIDATION.md` | Validation methodology (Level 1/2) and data-alignment rationale | Describes an intended validation process; whether it has been carried out is a separate, checkable question. |
| `grist_results.csv`, `assets/`, `figures/` | Prior run outputs / presentation material | Not model code. |

There is no `tests/` directory and no automated test suite in this
repository. Whether that absence constitutes a deficiency, and of what
severity, is for the audit to classify (see Classification System) rather
than for this document to pre-judge.

## Core module internals (`sheaf/core.py`, line references as of this preparation pass)

Each item below is phrased as a verification question with a pointer to
where the relevant mathematical claim and implementation live. None presume
an outcome.

1. **Demand system** (lines 49–119): `DemandSystem` dataclass +
   `build_demand_system()`. Verify whether the demand-matrix construction
   preserves the claimed positive-definiteness guarantee after all
   transformations — specifically, the per-row diagonal-dominance rescale is
   applied before the final symmetrization step (`S = 0.5*(S+S.T)`); confirm
   whether PD is preserved through that ordering, and under what parameter
   ranges (of `subst_scale`, `rho`) this has been checked or should be.
2. **Country / agent state** (lines 125–178): `Country` dataclass bundling
   producer, consumer, exporter, and both storage roles per node. Verify
   default values and units are applied consistently with README notation.
3. **Storage rules** (lines 184–217): `market_responsive_storage()`
   (positioned by the README as Wright-Williams/Deaton-Laroque-*flavored*,
   not a direct implementation — see Modeling Lineage above) and
   `strategic_storage()` (government buffer release/rebuild). Verify sign
   conventions and clipping bounds against README §3, and evaluate against
   TWIST/Agrimate's storage treatment before invoking the canonical
   competitive-storage literature as the comparison baseline.
4. **Market layer** (lines 222–296): `MarketResult`, `SpatialEquilibrium`.
   The QP is solved with a three-solver fallback
   (`CLARABEL → SCS → OSQP`). Determine whether the solver fallback and
   acceptance logic (proceeding once `D.value is not None`, without
   inspecting `prob.status`) provides sufficient guarantee that accepted
   solutions are optimal and feasible, or whether this is a place where
   additional verification is warranted — and if so, under what conditions
   (which solver, which problem instances) it matters in practice.
5. **Strategic layer** (lines 302–362): `ExportRestrictionGame`. Determine
   precisely which equilibrium concept the implemented government solver
   (grid-search iterated best response; default `grid=5`, `max_iters=3`,
   `tol=3.0` $/t) computes, and whether it satisfies the model's own stated
   Nash conditions (README §4) under the non-concave welfare surface the
   README itself flags. The README already describes this as an
   "approximate/discretised equilibrium rather than a proven unique one" —
   verify whether the implementation matches that self-description, and
   whether the approximation's quality has been characterized anywhere.
6. **Orchestrator** (lines 368–487): `SheafModel`. Verify the per-period
   sequencing (expectations → storage → stress gate → market/game clear →
   reserve update) against README §5, including the stress gate's role in
   deciding whether the game is played that period.

## Classification system

Every audit finding must be assigned exactly one of the following
categories. Agents must not confuse simplifications or alternative modeling
philosophies with errors — categories D and E exist precisely to hold
findings that are real and worth documenting but are not defects.

- **A. Mathematical error** — a formula, proof, or derivation is incorrect
  on its own terms.
- **B. Coding bug** — the implementation does not do what the code's own
  surrounding documentation/math says it should do.
- **C. Numerical issue** — correct formulation, but numerically fragile,
  unstable, or solver-dependent in a way that affects results.
- **D. Economic simplification** — a deliberate simplification relative to
  a richer economic theory, disclosed or not, that is a modeling choice
  rather than an error.
- **E. Modeling philosophy** — a difference in framework or scope relative
  to another model or literature (e.g., TWIST, Agrimate, Deaton–Laroque)
  that reflects a different design intent, not a mistake.
- **F. Empirical limitation** — a gap in validation, calibration, or data
  coverage relative to what the model or documentation claims to have
  established empirically.
- **G. Documentation issue** — the code is correct but the README/
  docstrings/VALIDATION.md misdescribe, overstate, or under-specify it.
- **H. Not an issue** — investigated and found to be correct/sound/adequate
  as implemented; recorded explicitly rather than left unstated.

## Burden of proof and confidence levels

Every major finding — including category H findings — must receive an
explicit confidence level:

- **95–100%** — mathematically demonstrated or directly reproduced
  (proof, or a runnable reproduction).
- **80–95%** — strong implementation evidence (code inspection plus
  targeted execution, but not a full proof or exhaustive test).
- **60–80%** — likely but not fully established (reasoning-based, limited
  or no direct execution).
- **40–60%** — reviewer concern (a plausible issue raised, but not yet
  substantiated by evidence).
- **below 40%** — speculation.

No redesign, rewrite, or architectural change should be recommended
primarily on the basis of speculative (below-40%) or reviewer-concern
(40–60%) findings. Findings below 60% confidence should be reported as open
questions for further investigation, not as conclusions.

## Verification protocol

For every suspected problem, agents must work through these steps in order
and record the outcome of each:

1. **Locate the mathematical claim** — cite the specific README equation,
   section, or docstring statement.
2. **Locate the implementation** — cite the specific file:line(s).
3. **Determine whether they match** — direct comparison, symbol by symbol
   where feasible.
4. **Attempt to construct a counterexample** — a concrete input, parameter
   set, or numerical case where claim and implementation diverge.
5. **Attempt to prove the current implementation correct** — actively argue
   the other side before concluding it is wrong; this step is not optional
   and must be documented even when step 4 succeeds.
6. **Only then recommend a change, if warranted** — and only with a
   classification (see above), a confidence level, and a complexity-budget
   assessment (see below) attached.

Skipping to step 6 without steps 1–5 is not an acceptable audit output.

## Complexity-budget rule

Every proposed change — including changes an agent is confident are
warranted — must be evaluated against:

- scientific benefit
- computational cost
- calibration burden
- interpretability
- additional parameters introduced
- additional state variables introduced
- runtime cost
- continuity with TWIST/Agrimate (does this move SHEAF further from or
  closer to its stated lineage?)
- likely publication benefit

Do not recommend additional complexity unless the scientific benefit
justifies it against this full list, not against a single axis (e.g.,
"more theoretically correct" is not sufficient justification on its own).

## Ground rules for this preparation and the eventual audit phase

- **Read-only.** Do not modify `sheaf/*.py`, `demo.py`, or `scripts/*.py` —
  neither during this preparation pass nor during the audit phase that
  follows it. Findings are reported, not silently patched.
- **This document does not start the audit.** Preparation ends here; the
  audit begins only when separately instructed.
- Units throughout the codebase: quantities in million tonnes (MMT), prices
  as a $/tonne index. Flag any place units appear inconsistent, using the
  classification and confidence-level system above rather than asserting an
  error outright.

## Suggested partition for a multi-agent audit

Natural seams for parallel agents, each independently verifiable against
README §1–§7. **Agents must not inherit another agent's conclusions as
facts.** A hypothesis raised by one agent (including anything phrased as a
"verification question" in this document) may be passed to another agent as
something to check, but each agent must independently work the Verification
Protocol on it — locate claim, locate implementation, attempt a
counterexample, attempt a correctness proof — before adopting or rejecting
it. Cross-agent agreement is evidence to be weighed, not a shortcut around
independent verification.

1. **Demand system & positive-definiteness** — `build_demand_system`
   correctness, whether diagonal dominance survives symmetrization,
   consumer-surplus potential formula vs. README §1.
2. **Market QP / spatial equilibrium** — `SpatialEquilibrium.solve`, solver
   fallback and status-checking, KKT/complementary-slackness claims in
   README §2 vs. what the QP actually encodes.
3. **Storage layer** — `market_responsive_storage` / `strategic_storage` vs.
   README §3 and vs. TWIST/Agrimate's storage treatment, sign/unit checks,
   edge cases (zero capacity, negative stock).
4. **Strategic game** — `ExportRestrictionGame`, which equilibrium concept
   is actually computed, grid/tolerance defaults, welfare function vs.
   README §4.
5. **Orchestrator & temporal dynamics** — `SheafModel.step`/`run`, stress
   gate logic, expectation formation vs. README §5.
6. **Calibration data** — `calibration.py` DATA table plausibility, RoW
   residual-node construction, elasticity/substitutability sourcing —
   evaluated as illustrative-prototype data, not a claimed production
   calibration, unless the repository states otherwise.
7. **Data pipelines** — `data_usda.py` (hand-rolled LOWESS correctness) and
   `data_faostat.py` (ISO3 resolution, drop behavior, unit-agnostic E0
   magnitudes).
8. **Validation methodology** — the actual (not assumed) gap between
   VALIDATION.md's stated plan and what `scripts/*.py` execute; whether
   README's zero-substitution limiting-case proposition (§6) is verifiable
   from the code as stated.

## Final adjudication rule

After independent agent findings are collected, a lead reviewer role must:

- Identify disagreements among agents and resolve them by evidence (re-running
  the Verification Protocol where agents reached different conclusions on the
  same claim), not by majority vote or seniority of the agent.
- Take the three strongest criticisms surfaced across all agents and, for
  each, actively attempt to falsify it — construct the best case that the
  implementation is correct or the concern does not apply — before accepting
  it into the final findings set. A criticism that survives a genuine
  falsification attempt may be reported at its evidenced confidence level; a
  criticism that does not survive must be reclassified (commonly to H, D, or
  E) rather than dropped silently.

## Reproducing the one existing run

```bash
pip install -r requirements.txt
python demo.py
```

This is the only current end-to-end execution path and a reasonable smoke
test before/after any change, though it exercises only one scenario
(Black Sea wheat shock). Whether it constitutes validation evidence, and at
what confidence level, is itself a question for the audit (see Classification
System, category F).
