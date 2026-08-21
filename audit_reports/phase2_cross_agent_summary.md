# Phase 2 Cross-Agent Register (produced after all four Phase 2 reports on file — not yet adjudicated)

Source agents:
- Agent 4 — spatial equilibrium / optimization (`phase2_agent4_spatial_equilibrium.md`)
- Agent 5 — temporal dynamics / orchestrator (`phase2_agent5_temporal_dynamics.md`)
- Agent 6 — calibration / data (`phase2_agent6_calibration_data.md`)
- Agent 7 — validation / identification (`phase2_agent7_validation_identification.md`)

Phase 1 reports remain hypotheses until this register (and final adjudication) says otherwise.
**No model source was modified.** This register indexes evidence; it is not final adjudication.

---

## 1. Phase 1 findings independently confirmed in Phase 2

| ID | Claim (short) | Phase 2 confirmation | Reports |
|---|---|---|---|
| **F3 / S10** | Solver accepts on `D.value is not None`, swallows exceptions → opaque `TypeError` at `core.py:289` (indefinite M *and* global infeasibility) | Agent 4 **CONFIRMED** both triggers; unified root cause as SE5; also notes latent `optimal_inaccurate` acceptance risk | phase2_agent4 ← phase1_agent1, phase1_agent3 |
| **F14** | ~15% glut headroom before negative prices; no free disposal; undocumented | Agent 4 **CONFIRMED** (wheat/rice ~15%, maize ~23%); demo shortfall safe; +20% glut unsafe; storage can *build* under \(p<0\) | phase2_agent4 ← phase1_agent1 |
| **S4** | Private storage reacts one period late to contemporaneous shocks | Agent 5 **CONFIRMED**; compared A/B/C; recommend document A or adopt B2 (probe-price) if same-year response required; reject full fixed-point C for now | phase2_agent5 ← phase1_agent3 |
| **S5** | No stationary rest point at calibration anchor; init on release side | Agent 5 **CONFIRMED**; recommend recentre so \(p^*=\bar p_0\) | phase2_agent5 ← phase1_agent3 |
| **S7** | Government crisis test = autarky; structural importers drain shock-independently | Agent 5 **CONFIRMED**; recommended fix **NARROWED** to G2 (anomaly vs baseline net-import need — coincides with Phase 1 slogan on importers, extends to exporters) | phase2_agent5 ← phase1_agent3 |
| **S8** | Crisis/build fall-through when `gov_stock==0` | Agent 5 **CONFIRMED** as latent | phase2_agent5 ← phase1_agent3 |
| **S3** | \(p^{\mathrm{ref}}=p_{t-1}\) undocumented | Agent 5 **CONFIRMED** | phase2_agent5 ← phase1_agent3 |
| **S14** | No look-ahead in storage expectations | Agent 5 **CONFIRMED** | phase2_agent5 ← phase1_agent3 |
| **S15** | Storage params illustrative; `stock_to_use` unwired | Agent 6 **CONFIRMED**; private stocks = `0.15·Q` | phase2_agent6 ← phase1_agent3 |
| **S9** (partial) | Storage independent of endogenous τ within period | Agent 5 **NARROWED**: within-period independence **CONFIRMED**; full-run bit-identity across game on/off **REFUTED** (cross-period price→storage path) | phase2_agent5 ← phase1_agent3 |

---

## 2. Phase 1 findings refuted or narrowed

| ID | Outcome | Detail |
|---|---|---|
| **S9** | **NARROWED** | Fact of within-period τ⊥Δ stands; Phase 1’s stronger “bit-identical over a full run whether or not the game is played” does not hold once lagged prices transmit prior τ into later storage. |
| **S7 fix slogan** | **NARROWED** | Agent 5 endorses G2 shortfall (deviation from baseline net-import requirement), not an importer-only redefinition and not gross production-gap alone. |
| **S10 scope** | **Retained narrowing** | Agent 4 confirms: local \(A_i<0\) with world \(\sum A\ge 0\) is feasible; only global scarcity triggers the TypeError path. |

No Phase 1 finding that Phase 2 was tasked to re-check was fully **REFUTED**.

**Not re-audited as primary Phase 2 targets** (still Phase-1-only evidence): F1 (PD/symmetrize), F2–F4 demand edge cases beyond F3/F14, game findings F1–F13 except where storage/orchestrator touched them, producer-income F9/S13.

---

## 3. New Phase 2 findings (not in Phase 1 register)

### Market / QP (Agent 4)
- **SE5 / status protocol:** Accept-if-value, bare `except`, ignore `prob.status` — root cause of F3/S10; designed (not implemented) minimal status-aware named-error protocol; also flags `optimal_inaccurate` acceptance if SCS ever wins first.
- **λ=p at D=0:** README blanket claim slightly overstated; dual ≥ choke when demand binds at zero (**G**, low practical severity on shipped baseline).
- **No free disposal:** Forces consumption of excess supply → pathological negative prices under glut (**D/E**, disclosed-as-limitation recommended; do not add disposal yet).
- **QP ↔ README §2 otherwise sound:** objective, tariffs/freight, Enke–Samuelson on interior tests, unique \((D,p)\) under PD, non-unique flows when costs tie (**H**).

### Temporal (Agent 5)
- Timeline/info-set audit: no accidental look-ahead; delayed *use* of current harvest in private storage is S4, not peeking.
- Architecture comparison: A (status quo) vs B2 (probe-price sequential) vs C (fixed point) — prefer B2 only if same-year private buffer is a publication claim; else document A.
- S7 drains erase Level-1 government stock-anomaly signal under differencing (shocked ≡ unshocked gov path for China/Egypt under Black Sea forcing).

### Calibration / data (Agent 6)
- **P6-F1:** Runnable model uses only illustrative `calibration.py`; USDA/FAOSTAT adapters are diagnostic-only — README §7 present-tense overclaim (**G/F**); overlaps Agent 7.
- RoW residual accounting closes; wheat GLOBAL≈780 MMT ~23% above USDA 2019–21 (prototype OK, not crisis baseline).
- LOWESS matches statsmodels `it=0` to ~1e-13 (**H**).
- FAOSTAT sums preserved; Egypt Russia shares 37.3→45.7→52.4% (**H**, multi-agent with Agent 7).
- **Kazakhstan pooled into RoW** (~40% of RoW wheat exports 2006–07) — Level-2 who-restricts cannot score KAZ (**F**, High).
- Transport haversine not E0; tariffs 0; rice/maize E0 not vendored; ε/ρ/freight/γ/mkt_cost illustrative.

### Validation / identification (Agent 7 — already on file)
- Level 2 circular as written; `fs_weight`/`p_target` non-identified; pooling to ~4 structural params; Level 1/2 not executable with vendored data; `subst_scale`/`RHO` unsourced — see P7-F1…F6 in `SHEAF_AUDIT_STATE.md`.

---

## 4. Disagreements among Phase 2 agents

- **None on overlapping factual claims.** Agent 6 independently confirms Agent 7’s README §7 / missing-input / Egypt-network / world-forcing structural points without contradicting magnitudes.
- Agent 4 and Agent 5 do not share a contested numeric claim; Agent 5’s storage build-under-negative-price note is consistent with Agent 4’s F14/glut analysis.
- **Open reconciliation still from Phase 1 (not Phase 2 disagreement):** F9/S13 producer income at `production0` — confidence/completeness difference only; still flagged for final adjudication.

---

## 5. Claims still lacking evidence / incomplete coverage

- **F1 (PD after symmetrize)** — Phase 1 only; no Phase 2 re-audit.
- **Game grid F3 / welfare surface / tau_max pinning** — Phase 1 only; not re-run in Phase 2.
- **Joint interaction of proposed one-line fixes** (PD geometric mean + solver status + storage timing + G2 shortfall + game grid) — still untested.
- **Author intent on F9/S13** — unsettled.
- **Real 2010/11 per-country forcing + AMIS timeline** — still absent from repo (Agents 6 & 7); Agent 7’s second-episode ID results used synthetic analogue.
- **Whether Agent 7 non-identification interacts with Agent 5 S7 / Agent 6 S15** beyond the Level-1 “gov differential is zero” note — partially noted, not fully cross-experimented.

---

## 6. Issues requiring final adjudication

Per CLAUDE.md Final Adjudication Rule: take the strongest criticisms, actively attempt to falsify each, then authorize (or reject) changes. Candidates for that pass (complexity-budget already argued by specialists):

1. **Solver status protocol (F3/S10/SE5)** — named error; stop accepting on value alone; optionally reject `optimal_inaccurate`; optional \(\sum A\ge 0\) precondition. High confidence, low cost, publication hygiene.
2. **Demand PD / symmetrize (F1)** — still Phase-1-only; adjudicator should either re-verify or commission a short replication before patching.
3. **Government shortfall → G2 (S7)** + latent S8 guard — high publish impact on stock dynamics; Agent 5 narrowed the fix.
4. **Private storage timing (S4)** — choose document-A vs implement-B2; do not silently adopt probe-price without deciding the paper’s same-year claim.
5. **S5 recentre** — one-line; calm-path drift.
6. **Validation honesty (P7-F1, P6-F1)** — reframe Level 2 as calibration; align README §7 with Caveats; do not claim USDA/FAOSTAT-driven runnable path.
7. **Identification / node set (P7-F2–F4, P6 Kazakhstan)** — pool policy params; add KAZ before who-restricts scoring; acquire per-country PSD + AMIS (already on VALIDATION.md remaining list — not new data types).
8. **Game grid (Phase 1 F3)** — still awaiting adjudication; not Phase-2-reconfirmed.
9. **F9/S13 producer income** — intent vs README revision vs code change.
10. **Fix-interaction test** — required before shipping a multi-patch PR.

**Do not implement any of the above until final adjudication explicitly authorizes patches.**

---

## 7. Strong positive Phase 2 results (do not reopen without new evidence)

- Market QP matches README §2 on the shipped/interior regime (Agent 4).
- LOWESS correct; RoW accounting closes; Egypt network diagnostic exact (Agents 6, 7).
- No look-ahead in orchestrator (Agent 5).
- Material-balance / game Nash-on-grid positives from Phase 1 stand unchallenged by Phase 2.

---

## Status

- Phase 2 specialist audits: **COMPLETE** (4/4 reports on file).
- This cross-agent register: **COMPLETE** (2026-08-22).
- Final adjudication: **NOT STARTED** — requires explicit authorization.
- Model source: **UNCHANGED**.
