# SHEAF Audit State

This file is a **persistent handoff document** — a checkpoint, not an audit report
and not a replacement for `CLAUDE.md`. It exists so a future Claude Code session,
with no conversational memory of this one, can resume the scientific audit
correctly from files alone.

## Audit status

- **Current phase:** Final adjudication — **COMPLETE** (2026-08-22). Authorized IMPLEMENT NOW patches applied. Deferred items remain.
- **Architecture pivot (2026-08-23):** Gate 0 locked to **Agrimate-aligned 24 steps/year**
  out-of-equilibrium dynamics. Annual SPE demoted. See `ARCHITECTURE.md` (includes
  why 24 not 26) and rewritten Gate 0 in `VALIDATION.md`.
- **Phases completed:**
  - Phase 0 — repository mapping / preparation of `CLAUDE.md`. Complete.
  - Phase 1 — specialist audits + cross-agent section. Complete; adjudicated.
  - Phase 2 — Agents 4–7 + `phase2_cross_agent_summary.md`. Complete; adjudicated.
  - Final adjudication — `audit_reports/FINAL_ADJUDICATION.md`. Complete; patches applied.
- **Phases not yet started / next engineering:** Sub-annual calendar + dynamic core
  (ARCHITECTURE.md implementation order). No Level-2 until monthly Gate 0 Hard is green.
- **Phase 2 detail:** All four agents + cross-register complete (see prior checkpoint).
- **Checkpoint date:** 2026-08-23 (architecture lock). Prior: 2026-08-22 adjudication.
- **Orchestration:** Cursor parent + Task subagents for Phase 2; parent lead-reviewer for adjudication.
- **Source code modification status:** **AUTHORIZED PATCHES APPLIED 2026-08-22** per `FINAL_ADJUDICATION.md` §4 IMPLEMENT NOW:
  - `sheaf/core.py` — PD geometric-mean; solver status protocol; G2 shortfall; S8 guard; S5 expectation recentre
  - `sheaf/__init__.py` — export `SpatialEquilibriumError`
  - `README.md`, `VALIDATION.md` — honesty / formula sync
  - Audit artifacts remain under `audit_reports/`, `audit_prompts/`, `SHEAF_AUDIT_STATE.md`
  - 2026-08-23 docs: `ARCHITECTURE.md`, Gate 0 rewrite (code clock not yet migrated)

## Governing documents

- **`CLAUDE.md`** (repo root) — the audit constitution. Defines the governing
  principle, the A–H classification system, confidence-level bands, the six-step
  verification protocol, the complexity-budget rule, the TWIST→Agrimate→SHEAF
  lineage framing, and the read-only ground rule. Always read this first.
- **Phase 1 reports** (full text, persisted this checkpoint):
  - `audit_reports/phase1_agent1_math_foundations.md`
  - `audit_reports/phase1_agent2_game_theory.md`
  - `audit_reports/phase1_agent3_storage_lineage.md`
  - `audit_reports/phase1_cross_agent_summary.md`
- **Condensed Phase 1 register** (used to brief Phase 2 agents without re-pasting
  full reports): `audit_reports/phase1_register_condensed.md`. Mirrors a working
  copy that was at `/tmp/sheaf_audit_phase1_register.md` — that `/tmp` copy is
  **not** guaranteed durable (see Risks); the copy inside the repo is the durable
  one and should be treated as authoritative going forward.
- **Phase 2 reports:**
  - `audit_reports/phase2_agent4_spatial_equilibrium.md` — COMPLETE.
  - `audit_reports/phase2_agent5_temporal_dynamics.md` — COMPLETE.
  - `audit_reports/phase2_agent6_calibration_data.md` — COMPLETE.
  - `audit_reports/phase2_agent7_validation_identification.md` — COMPLETE.
  - `audit_reports/phase2_cross_agent_summary.md` — COMPLETE (2026-08-22).
- **Next-phase / resume prompt:** `audit_prompts/PHASE_2.md` — contains the
  original Phase 2 mandate for all four agents plus a status note on what still
  needs launching.
- **Temporary test/counterexample scratch code** (created by each specialist
  agent outside the repo; read-only; helpful for reproducing a finding but **not
  guaranteed durable** — see Risks):
  - `/tmp/sheaf_audit_agent1/` — Phase 1, math foundations
  - `/private/tmp/sheaf_audit_agent2/` — Phase 1, game theory
  - `/tmp/sheaf_audit_agent3/` — Phase 1, storage/lineage
  - `/tmp/sheaf_audit_agent4/` — Phase 2, spatial equilibrium (2026-08-22 complete)
  - `/tmp/sheaf_audit_agent5/` — Phase 2, temporal dynamics (2026-08-22 complete)
  - `/tmp/sheaf_audit_agent6/` — Phase 2, calibration/data (2026-08-22 complete;
    prior 2026-08-09 contents may be stale)
  - `/tmp/sheaf_audit_agent7/` — Phase 2, validation/identification (complete;
    referenced as `e01`–`e07` in its report)

## Completed work

| Agent | Remit | Report | Status |
|---|---|---|---|
| Agent 1 (Phase 1) | Mathematical foundations — demand system, PD/symmetry/diagonal dominance, integrability, consumer surplus, σ=0 limit | `audit_reports/phase1_agent1_math_foundations.md` | **COMPLETE** |
| Agent 2 (Phase 1) | Game theory — `ExportRestrictionGame`, Nash-equilibrium concept, joint vs. coordinate best response, ε-exploitability, grid discretization | `audit_reports/phase1_agent2_game_theory.md` | **COMPLETE** |
| Agent 3 (Phase 1) | Storage layer vs. TWIST/Agrimate lineage — `market_responsive_storage`, `strategic_storage`, material balance, period timeline, terminology | `audit_reports/phase1_agent3_storage_lineage.md` | **COMPLETE** |
| Agent 4 (Phase 2) | Spatial equilibrium / optimization — `SpatialEquilibrium.solve`, QP derivation, solver fallback/status-checking, negative prices, free disposal, README §2 | `audit_reports/phase2_agent4_spatial_equilibrium.md` | **COMPLETE** (2026-08-22) |
| Agent 5 (Phase 2) | Temporal dynamics / orchestrator — `SheafModel.step` dependency graph, independent re-verification of S4/S5/S7/S9, 3-architecture timing comparison, shortfall-definition comparison | `audit_reports/phase2_agent5_temporal_dynamics.md` | **COMPLETE** (2026-08-22) |
| Agent 6 (Phase 2) | Calibration and data pipelines — `calibration.py` DATA table, LOWESS correctness, FAOSTAT ISO3/aggregation, crisis forcing, parameter-sourcing classification table | `audit_reports/phase2_agent6_calibration_data.md` | **COMPLETE** (2026-08-22 Cursor relaunch) |
| Agent 7 (Phase 2) | Validation and identification — VALIDATION.md Level 1/2 circularity, parameter identification, feasible validation design, metrics, minimum-evidence assessment | `audit_reports/phase2_agent7_validation_identification.md` | **COMPLETE** (after 4 transient connection-error retries during write-up) |

Findings are **not reinterpreted here** — see the report files for full evidence,
falsification attempts, and reasoning.

## Provisional findings register

**Status values used below:** PROVISIONAL (single agent, not yet independently
cross-checked) · CONFIRMED BY MULTIPLE AGENTS (two+ agents independently reached
the same conclusion) · REFUTED · NARROWED · UNRESOLVED. Nothing below is an
established fact — the linked report is the source of evidence; this table is an
index, not a verdict.

| ID | Description | Class | Confidence | Status | Report(s) |
|---|---|---|---|---|---|
| P1-F1 | PD guarantee in `build_demand_system` is false (rescale before symmetrize); one-line geometric-mean fix proposed | A | 99% | PROVISIONAL | phase1_agent1 |
| P1-F3 / P3-S10 | Indefinite/infeasible QP → swallowed exception → opaque `TypeError` at `core.py:289` | C/B | 98%/95% | **CONFIRMED BY MULTIPLE AGENTS** (Phase 1 hit via 2 triggers; Phase 2 Agent 4 independently **CONFIRMED** both + unified SE5 root cause) | phase1_agent1, phase1_agent3, phase2_agent4 |
| P2-F3 | Default 5-point tax grid distorts extensive & intensive margin of the export-restriction game | C | 95–100% | PROVISIONAL | phase1_agent2 |
| P3-S4 | Private storage reacts one period late to the contemporaneous shock (no `prod`/`shock` argument) | D/E/G | 95% | **CONFIRMED BY MULTIPLE AGENTS** (Agent 5 independent confirm; recommend document A or B2) | phase1_agent3, phase2_agent5 |
| P3-S5 | Private storage rule has no stationary rest point at the calibration anchor; model initialised on the release side | D/G | 97% | **CONFIRMED BY MULTIPLE AGENTS** (Agent 5) | phase1_agent3, phase2_agent5 |
| P3-S7 | Government "crisis" test is an autarky check, not a scarcity/anomaly check; structural importers drain shock-independently | D/G | 97% | **CONFIRMED BY MULTIPLE AGENTS**; fix **NARROWED** by Agent 5 to G2 shortfall | phase1_agent3, phase2_agent5 |
| P3-S9 | Storage decisions are computed strictly independent of the export-restriction game within a period | E/H | 95%/75% | **NARROWED** by Agent 5 (within-period CONFIRMED; full-run bit-identity REFUTED) | phase1_agent3, phase2_agent5 |
| P3-S8 | `strategic_storage` build/crisis fall-through logic bug (unreachable in shipped calibration, reachable for other calibrations) | B | 95% | PROVISIONAL | phase1_agent3 |
| P2-F9 / P3-S13 | Producer income in `_welfare` uses unshocked baseline production, not realised/post-storage output | D/G | 95–100% (P2) / 80% (P3) | **CONFIRMED BY MULTIPLE AGENTS** on the underlying fact; reconciliation of confidence/interpretation **still open**, not assigned to any single Phase 2 agent | phase1_agent2, phase1_agent3 |
| P7-F1 | VALIDATION.md Level 2 is circular as written (parameters fit to the same cascade later scored as "prediction") | F/G | 95–100% | PROVISIONAL (Phase 2, single agent, but internally demonstrated numerically, not merely asserted) | phase2_agent7 |
| P7-F2 | `fs_weight`/`p_target` demonstrably non-identified on the fitted margin (10/63 tested combinations bit-identical or near-identical output) | F | 95–100% | PROVISIONAL | phase2_agent7 |
| P7-F3 | A second crisis episode (synthetic analogue) eliminates at most ~40% of the non-identified parameter set | F | 90–95% (explicit data caveat: synthetic, not real 2010/11 forcing) | PROVISIONAL | phase2_agent7 |
| P7-F4 | 28 free policy parameters vs. ≤28 binary observations; pooling to ~4 structural parameters recommended | F | 90–95% | PROVISIONAL | phase2_agent7 |
| P7-F5 | Neither VALIDATION.md Level 1 nor Level 2 is executable with the repository's current vendored data (world-aggregate USDA only; wheat-only 2-year-window FAOSTAT; no AMIS timeline; no price series) | F/G | 95–100% | PROVISIONAL | phase2_agent7 |
| P7-F6 | `subst_scale=0.6` and `RHO` are unsourced; the headline substitution-spillover result is monotonic in `subst_scale` | F/G | 95–100% | PROVISIONAL | phase2_agent7 |
| P6-F1 | Runnable path uses only illustrative `calibration.py`; USDA/FAOSTAT adapters are diagnostic-only; README §7 present-tense “come from USDA/FAOSTAT” overclaims | G/F | 95–100% | **CONFIRMED BY MULTIPLE AGENTS** (Agent 6 + Agent 7 overlap) | phase2_agent6, phase2_agent7 |
| P6-F2 | RoW residual accounting closes (`GLOBAL − named`); wheat GLOBAL≈780 MMT is ~23% above USDA 2019–21 — OK as prototype, not crisis baseline | H/F | 95–100% | PROVISIONAL | phase2_agent6 |
| P6-F3 / S15 | `stock_to_use` never wires into storage targets; private stocks = `0.15·Q` | F | 95–100% | **CONFIRMED BY MULTIPLE AGENTS** (Phase 1 S15 independently confirmed by Agent 6) | phase1_agent3, phase2_agent6 |
| P6-F4 | Hand-rolled LOWESS matches statsmodels `it=0` to ~1e-13; crisis wheat anomalies ~−4% as documented | H | 95–100% | PROVISIONAL | phase2_agent6 |
| P6-F5 | FAOSTAT network sums preserved; Egypt Russia shares 37.3→45.7→52.4% confirmed; Kazakhstan pooled into RoW (~40% of RoW wheat exports 2006–07) — Level-2 who-restricts cannot score KAZ | F/H | 95–100% | PROVISIONAL (KAZ gap); Egypt check **CONFIRMED BY MULTIPLE AGENTS** | phase2_agent6, phase2_agent7 |
| P6-F6 | Transport is haversine not E0; tariffs all 0; rice/maize E0 not vendored; ε/ρ/freight/γ/mkt_cost illustrative — not identifiable from world-aggregate crises alone | F/D/G | 90–95% | PROVISIONAL | phase2_agent6 |
| P4-SE5 | Accept-if-`D.value`; bare `except`; ignore `prob.status`; latent `optimal_inaccurate` risk — designed (not implemented) status-aware protocol | C/B | 95–100% | PROVISIONAL (unified root of F3/S10) | phase2_agent4 |
| P4-F14 | Negative-price headroom ~15% wheat/rice, ~23% maize; no free disposal; storage can build under \(p<0\) | D/G | 95–100% | **CONFIRMED BY MULTIPLE AGENTS** (Agent 4 remeasured Phase 1 F14) | phase1_agent1, phase2_agent4 |

## Strong positive findings (H-class — tested and found sound; do not reopen without new evidence)

- **Storage material balance is exact.** Country×grain×period conservation holds
  to solver precision (~1e-12) over a full 612-cell real run; no grain created or
  destroyed. (`phase1_agent3`, S1/S2, 97–99%)
- **No look-ahead in storage.** Expectations use strictly t-1 information; `p_norm`
  and `last_tau` verified not to leak future information. (`phase1_agent3`, S14, 98%)
- **`ExportRestrictionGame` returns an exact Nash equilibrium of its own
  discretized grid.** ε_i = 0 exactly across 204 tested runs, including real
  in-run stressed states. (`phase1_agent2`, F1, 95–100%)
- **Coordinate-vs-joint best-response gap is exactly zero for every tested
  calibration** (multi-grain exporters' welfare surface is ~99.88% additively
  separable across their own grains in this model). (`phase1_agent2`, F2, 95–100%
  tested)
- **No cycling; unique fixed point** across 11 initializations × 8 player
  orderings, including an adversarial all-τ_max corner start. (`phase1_agent2`,
  F6/F7, 95–100% tested)
- **`_welfare` matches README §4 term-by-term** with correct signs. (`phase1_agent2`,
  F12, 95–100%)
- **Demand-system math (once PD holds) is otherwise exactly correct**: symmetry of
  M is bitwise exact; the integrability condition and gradient (∇W=p) are correct;
  the consumer-surplus formula and its one-grain limit are exact identities; the
  intercept calibration D(p0)=D0 holds exactly; own-price elasticities are
  recovered exactly; dimensional consistency (MMT, $/t) holds throughout; strict
  concavity in D and uniqueness of (D,p) are confirmed via independent dual
  extraction; the σ=0 decomposition (README §6's Proposition) holds to
  numerical precision. (`phase1_agent1`, F5–F13, 95–99%)
- **The Egypt Russia-import-dependence figure in VALIDATION.md reproduces exactly**
  against the real vendored FAOSTAT data (37.3%→45.7%→52.4% across the three
  windows) — a genuine, checkable data validation. (`phase2_agent7`, Finding 5
  positive check, 95–100%)

## Unresolved questions

- **Final adjudication has not run.** Strongest criticisms and proposed fixes are
  indexed in `audit_reports/phase2_cross_agent_summary.md` §6 — none authorized.
- **F1 (PD after symmetrize)** remains Phase-1-only; no Phase 2 re-audit.
- **Game-grid F3** and related Agent 2 findings remain Phase-1-only.
- **Producer-income F9/S13** reconciliation (intent vs fixed policy weight) open.
- **Joint interaction of proposed fixes** still untested.
- **Real 2010/11 per-country PSD + AMIS** still absent (Agents 6 & 7).
- Phase 2 specialist coverage is complete (Agents 4–7 + cross-agent register).

## Proposed changes — NOT APPROVED — DO NOT IMPLEMENT UNTIL FINAL ADJUDICATION

Every item below is a Phase 1 or Phase 2 agent's *recommendation*, not an
authorized change. None have been reviewed by a lead-adjudicator role, and per
CLAUDE.md's Final Adjudication Rule, the three strongest criticisms must survive
an active falsification attempt before being accepted into any final findings
set — none of that adjudication has happened yet.

1. Replace arithmetic-mean symmetrization with geometric mean in
   `build_demand_system` (`core.py:115`) — motivated by P1-F1 (Phase-1-only).
2. Guard against `b_g=0` causing NaN propagation (`core.py:112–114`) —
   motivated by Agent 1's F4.
3. Status-aware solver acceptance + named error (`core.py:281–289`) — F3/S10;
   Agent 4 designed (not implemented) the protocol (SE5).
4. Two-stage local grid refinement (or raise default `game_grid` 5→13) —
   Phase 1 Agent 2 F3 (not Phase-2-reconfirmed).
5. S4 timing: document lagged-price rule **or** adopt B2 probe-price reuse —
   Agent 5 compared A/B/C; do not silently patch.
6. Recentre `p_norm` so the storage rule's rest point equals `mean(p0)` — S5.
7. Redefine `strategic_storage` shortfall as G2 (Agent 5 narrowing of S7).
8. Fix `strategic_storage` crisis/build fall-through (`if not crisis:`) — S8.
9. Forward `tol`/`revenue_weight` through `SheafModel.__init__` — Agent 2 F11.
10. Pool `fs_weight`/`p_target` into ~4 structural parameters — P7-F4.
11. Reframe VALIDATION.md Level 2 from "prediction" to "calibration"; align
    README §7 with actual runnable path — P7-F1 / P6-F1.
12. Cite or sensitivity-band `subst_scale`/`RHO` — P7-F6.
13. Add Kazakhstan as a named node before Level-2 who-restricts scoring — P6-F5.

## Next phase

Deferred work authorized in spirit but **not** implemented (see
`FINAL_ADJUDICATION.md` §4): game-grid refinement + demo rebaseline; optional B2
storage timing; Kazakhstan node; USDA PSD / AMIS wire-up; pool `fs_weight`/
`p_target`; joint interaction test suite beyond smoke test.

## Resume instructions

Read `CLAUDE.md`, then this file, then `audit_reports/FINAL_ADJUDICATION.md`.
Do not re-run completed Phase 1/2 audits. Further code changes need a new
explicit authorization beyond the closed IMPLEMENT NOW set.

## Next prompt

Pick a deferred track, e.g. “wire per-country USDA + add Kazakhstan” or
“rebaseline demo with game_grid=13”, or ask for a git commit of the adjudication
patches.