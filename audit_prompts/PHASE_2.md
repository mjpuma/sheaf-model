# Phase 2 prompt (for resuming/completing Phase 2 in a fresh session)

**Status as of this checkpoint (2026-08-09): Phase 2 is IN PROGRESS. 1 of 4 subsystem
agents (Agent 7 — validation/identification) is COMPLETE; its report is at
`audit_reports/phase2_agent7_validation_identification.md`. Do NOT re-run Agent 7.
The other 3 (Agent 4 — spatial equilibrium; Agent 5 — temporal dynamics; Agent 6 —
calibration/data) were launched but did not reach completion (repeated transient
connection errors and session usage-limit errors interrupted them mid-run). Their
background agent IDs from the prior session are almost certainly NOT resumable in a
new session — launch them FRESH using the mandates below.**

**IMPORTANT PROCESS NOTE for whoever runs this:** last time, each agent's completed
report existed only in the conversation transcript until a manual checkpoint was
triggered — this caused risk when the session was interrupted. This time, as each
of Agent 4/5/6 completes, immediately write its full report to
`audit_reports/phase2_agentN_<name>.md` (matching the naming pattern of
`phase2_agent7_validation_identification.md`) BEFORE proceeding to the next step,
so a future interruption cannot lose completed work again.

---

## Original Phase 2 launch instructions (authoritative — reproduce these mandates when relaunching Agents 4, 5, 6)

Begin Phase 2 of the SHEAF scientific verification audit.
Read CLAUDE.md and all Phase 1 reports (now persisted at `audit_reports/phase1_*.md`
— use those files, or the condensed `audit_reports/phase1_register_condensed.md`,
rather than re-deriving from scratch what Phase 1 already covered).
Do not modify SHEAF model source code.
Phase 1 findings are HYPOTHESES, not premises.
Every Phase 2 agent must independently verify any Phase 1 finding it touches.
Launch the following agents in parallel (only 4, 5, 6 need launching — Agent 7 is done):

### AGENT 4 — SPATIAL EQUILIBRIUM / OPTIMIZATION

Conduct a first-principles audit of `SpatialEquilibrium.solve()` and README §2.
This subsystem was not directly audited in Phase 1.
Do not assume Phase 1's incidental solver findings are correct.
Derive the optimization problem independently.
Verify: objective function; concavity; feasibility; equality constraints; flow
constraints; tariff treatment; transport-cost treatment; demand variables; network
structure; market-clearing identities; dual interpretation; KKT conditions;
complementary slackness; domestic price interpretation; uniqueness of quantities;
uniqueness of prices; uniqueness of flows.

Determine exactly under what mathematical conditions the QP is convex/concave and
solvable. Then audit the CVXPY implementation. Explicitly inspect: CLARABEL → SCS →
OSQP fallback; exception handling; `prob.status`; `D.value`; `flow.value`; dual
values; infeasible; infeasible_inaccurate; optimal_inaccurate; unbounded states;
DCP errors.

Attempt to reproduce the Phase 1 claim (Agent 1's F3, Agent 3's S10 — see the
register) that invalid/infeasible problems can fall through to an uninformative
TypeError. Attempt to falsify that claim. Design the minimal robust solver-status
protocol appropriate for publication-quality scientific software. Do NOT implement
it.

Also investigate negative prices. Determine whether negative prices are: (1)
mathematically permitted by the stated model; (2) economically intended; (3)
reachable under plausible parameterizations; (4) reachable under the shipped
calibration; (5) consequential for storage or government behavior.

Distinguish carefully between a mathematical error and a limitation of linear
inverse demand. Investigate free disposal. Determine whether the absence of
disposal forces consumption of excess supply and whether this can cause
economically pathological prices. Construct explicit examples if possible.
Finally verify all README §2 claims against the actual QP.

For the two Phase 1 hypotheses re-investigated (F3's TypeError claim, S10's
infeasibility-TypeError claim), explicitly state: CONFIRMED / REFUTED / NARROWED /
RECLASSIFIED / UNRESOLVED.

### AGENT 5 — TEMPORAL DYNAMICS / ORCHESTRATOR

Audit `SheafModel.step()` and README §5 from first principles. Do not assume the
Phase 1 storage conclusions are correct. Construct the exact implemented
within-period timeline. For every operation identify its information set. Track:
production shock; production; beginning stocks; price expectations; private
storage; government reserves; effective availability; probe market; stress gate;
government restriction game; final spatial equilibrium; prices; consumption;
trade; stock update; lagged state update. Draw the dependency graph. Identify
every variable that depends on: t-1 information; current exogenous information;
current endogenous information; future information. Verify there is no accidental
look-ahead.

Then independently investigate the Phase 1 hypotheses (see the register for their
claimed content — treat as hypotheses, not premises):
- HYPOTHESIS S4: private storage reacts one period late to contemporaneous
  production shocks.
- HYPOTHESIS S5: the private storage rule has no stationary rest point at the
  calibration anchor.
- HYPOTHESIS S7: the strategic reserve crisis test mistakes structural import
  dependence for crisis.
- HYPOTHESIS S9: storage is within-period independent of endogenous export
  restrictions.

Do not accept these. Attempt to disprove each one.

For S4 specifically, do NOT automatically accept the Phase 1 recommendation to use
the stress-gate probe price. Compare at least three timing architectures: A.
Existing lagged-price rule. B. Probe-price sequential rule (shock → unrestricted
probe equilibrium → storage → policy game/final equilibrium). C. Simultaneous or
fixed-point storage/market solution. For each assess: economic interpretation;
continuity with TWIST/Agrimate; computational cost; possibility of
double-counting; fixed-point issues; effect on crisis timing; publication
defensibility. Recommend the simplest scientifically defensible timing
architecture.

For S7, determine what "shortfall" should mean for a structural importer. Compare:
gross domestic production gap; deviation from baseline net-import requirement;
consumption availability including normal trade; price-based scarcity; other
minimal alternatives. Do not select one until deriving the consequences.

### AGENT 6 — CALIBRATION / DATA

Audit the actual calibration and data pipelines. Files include at minimum:
`sheaf/calibration.py`, `sheaf/data_usda.py`, `sheaf/data_faostat.py`, data
provenance files, `scripts/build_network.py`, `scripts/validate_forcing.py`. Do
not judge illustrative calibration numbers as though they were claimed estimates
unless the repository claims that. Separate: prototype calibration; empirical
calibration; validation data.

Audit: units; country aggregation; Rest-of-World construction; production;
consumption; stocks; elasticities; cross-price substitution; trade matrices;
distance/transport costs; tariffs; government reserves; storage parameters;
food-security parameters; restriction parameters. For every parameter classify
it: directly observed; derived from observed data; literature calibrated;
internally calibrated; illustrative; arbitrary/default; currently unsourced.

Check whether country/grain quantities reconcile. Check whether network
construction preserves world trade accounting. Check whether dropped
countries/flows create systematic biases. Audit the LOWESS implementation
independently. Check crisis forcing construction. Identify parameters that cannot
realistically be identified from the proposed historical episodes. Do not
recommend collecting new data unless existing USDA/FAOSTAT or repository data
cannot answer the question.

---

## Cross-agent requirements (apply to all of 4/5/6)

Agents remain independent. Phase 1 findings are not facts. When a Phase 2 agent
encounters a Phase 1 finding, it must independently execute the CLAUDE.md
verification protocol. Explicitly record when a Phase 1 finding is: CONFIRMED /
REFUTED / NARROWED / RECLASSIFIED / UNRESOLVED. Do not adjudicate the entire audit
yet.

## Output format

Each agent produces an independent standalone report. For every substantive
finding include: Finding; Classification A–H; Severity; Confidence %;
Mathematical/economic evidence; Code evidence; Numerical reproduction where
possible; Attempt to falsify; Falsification result; Recommended action;
Complexity-budget assessment; Whether it changes expected published results.

At the end, once ALL FOUR Phase 2 agents (including the already-complete Agent 7)
have reports on file, produce a Phase 2 cross-agent register containing: (1)
Phase 1 findings independently confirmed; (2) Phase 1 findings refuted or
narrowed; (3) new findings; (4) disagreements; (5) claims still lacking evidence;
(6) issues requiring final adjudication.

Do not modify model source code. Do not yet produce the final publication
verdict.
