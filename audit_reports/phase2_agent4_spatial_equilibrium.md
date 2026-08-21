# Phase 2 Agent 4 — Spatial Equilibrium / Optimization Audit

**Subsystem:** `SpatialEquilibrium.solve()` and README §2  
**Workspace:** `/Users/mjp38/GitHub/sheaf-model`  
**Mode:** Read-only on `sheaf/*.py`, `demo.py`, `scripts/*.py`  
**Scratch:** `/tmp/sheaf_audit_agent4/`  
**Report:** `audit_reports/phase2_agent4_spatial_equilibrium.md`  
**cvxpy:** 1.7.5; installed solvers `CLARABEL`, `OSQP`, `SCS` (also `SCIPY`)

Phase 1 findings touching this subsystem (Agent 1 F3; Agent 3 S10; Agent 1 F14) were treated as **hypotheses**, re-derived and re-executed under CLAUDE.md’s six-step protocol. This report does not adjudicate the whole audit.

---

## 0. Independent derivation of the market QP

### 0.1 Stated problem (README §2)

Given availabilities \(A^g_i\) and policies \((\tau, m)\),

\[
\max_{D\ge 0,\ f\ge 0}\ \sum_{i=1}^{n} W_i(D_i)\;-\;\sum_{g=1}^{G}\sum_{i,j} K^g_{ij}\, f^g_{ij}
\]

subject to

\[
A^g_i + \sum_k f^g_{ki} - \sum_k f^g_{ik} - D^g_i = 0 \quad\forall i,g,
\qquad f^g_{ii}=0,
\]

with delivered marginal cost

\[
K^g_{ij} = c_{ij}\,\phi_g\,\psi_{ij} \;+\; \tau^g_i \;+\; m^g_j
\]

and benefit potential (README §1 / `DemandSystem`)

\[
W_i(D_i) = (M_i^{-1}a_i)^\top D_i - \tfrac12 D_i^\top M_i^{-1} D_i,
\qquad \nabla W_i = p_i(D_i) = M_i^{-1}(a_i - D_i).
\]

### 0.2 Convexity / concavity / solvability (exact conditions)

Rewrite as a minimization of \(-\sum_i W_i + \sum K\cdot f\).

| Object | Condition for the claimed property |
|---|---|
| \(W_i\) concave | \(M_i^{-1}\succeq 0\) (positive semidefinite) |
| \(W_i\) **strictly** concave | \(M_i^{-1}\succ 0\) \(\Leftrightarrow\) \(M_i\succ 0\) (since \(M_i\) symmetric) |
| Objective concave (maximize) / cost convex (minimize) | every country’s \(M_i^{-1}\succeq 0\), and \(K\) enters linearly |
| Feasible set | polyhedron: linear equalities + \(D\ge 0\), \(f\ge 0\), \(\mathrm{diag}(f)=0\) |
| **Necessary** feasibility (per grain \(g\)) | \(\sum_i A^g_i \ge 0\) (sum balance \(\Rightarrow \sum_i D^g_i = \sum_i A^g_i\)) |
| **Sufficient** feasibility (this codebase) | \(\sum_i A^g_i \ge 0\) for each \(g\), because \(c_{ij}<\infty\) for all \(i\neq j\) (complete network); local \(A_i<0\) is fine |
| Bounded optimal value | feasible set nonempty and (with finite \(A\)) compact in \(D\) along the affine hull of the balances; with \(M_i^{-1}\succeq 0\) the concave QP attains a maximum |
| Unique \((D,p)\) | strict concavity of \(\sum_i W_i\) (all \(M_i\succ 0\)) \(\Rightarrow\) unique \(D^*\); \(p_i=M_i^{-1}(a_i-D_i^*)\) unique |
| Unique flows \(f\) | **not** guaranteed: when route costs tie (or path costs equal direct costs), the flow polytope for fixed net exports can have positive dimension |
| Unique duals / shadow prices | under strict complementarity / LICQ-type conditions at an interior \(D>0\) optimum, \(\lambda=p\); at \(D_i^g=0\) the demand nonnegativity multiplier can make \(\lambda_i^g \ge p_i^g(\text{choke})\) |

**DCP / cvxpy solvability:** `cp.quad_form(D, Minv)` is accepted as concave in a `Maximize` problem iff cvxpy’s DCP rules see `Minv` as PSD. If any `Minv` has a negative eigenvalue, cvxpy raises `DCPError` **before** any numeric solver runs.

**Not unbounded in the intended regime:** with PSD `Minv` and finite \(A\), the problem cannot be unbounded above. An indefinite `Minv` is rejected by DCP rather than solved as an unbounded/nonconcave program.

### 0.3 Code mapping (`sheaf/core.py` 232–296)

| README element | Implementation |
|---|---|
| \(W_i\) | `ca @ D[i,:] - 0.5 * cp.quad_form(D[i,:], sysd.Minv)` with `ca = Minv @ a` (lines 262–265) |
| \(K^g_{ij}\) | `Cg = C * freight_mult[g]` then optional `* route_multiplier`; `K = Cg + export_tax[:,g][:,None] + tariff[:,g][None,:]` (269–273) |
| Balance | `availability[:,g] + imports - exports - D[:,g] == 0` (277) |
| No self-trade | `cp.diag(fg[g]) == 0` (278) |
| \(D\ge 0,\ f\ge 0\) | `cp.Variable(..., nonneg=True)` (259–260) |
| Prices | **not** taken from duals; `systems[i].price(Dv[i,:])` i.e. \(M^{-1}(a-D)\) (292) |

Symbol-for-symbol match of the **primal QP** with README §2 was verified numerically (max \(|K_{\mathrm{code}}-K_{\mathrm{README}}|=0\); balance residuals \(\sim 10^{-15}\)).

---

## Findings

### SE1 — Primal QP matches README §2 (objective, \(K\), balances, no self-trade)

- **Finding.** The implemented concave QP is the Samuelson–Takayama–Judge net-social-payoff program stated in README §2. Tariff is on the **destination** (\(m_j\)), export tax on the **origin** (\(\tau_i\)), freight is \(c_{ij}\phi_g\psi_{ij}\). Market clearing holds at solver precision. Prices returned equal inverse demand \(p=M^{-1}(a-D)\).
- **Classification.** **H** (Not an issue).
- **Severity.** — (positive confirmation).
- **Confidence.** **99%**.
- **Mathematical evidence.** Direct term-by-term comparison of README (107–136) with `SpatialEquilibrium.solve` (255–296).
- **Code evidence.** `sheaf/core.py:255–296`.
- **Numerical reproduction.** `/tmp/sheaf_audit_agent4/audit_spatial.py` TEST 1: two-node, two-grain instance with nonzero \(\tau\), \(m\), \(\psi\); all identities hold to machine precision.
- **Attempt to falsify.** Sought mismatches in tariff broadcasting (row vs column) and freight application order — none found.
- **Falsification result.** Failed to falsify; claim stands.
- **Recommended action.** None.
- **Complexity-budget assessment.** N/A.
- **Changes published results?** No.

---

### SE2 — Concavity / uniqueness claims in README §2 hold under PD \(M\)

- **Finding.** Strict concavity of \(\sum_i W_i\) when every \(M_i\succ 0\) yields a unique consumption vector and hence unique inverse-demand prices. Flows are **not** unique when delivered costs tie; different solvers return different optimal flow matrices with the same \((D,p)\) and net exports. This matches README’s explicit caveat (“flows may be non-unique when routes tie”).
- **Classification.** **H**.
- **Severity.** —.
- **Confidence.** **98%** (theory + reproduction); flow non-uniqueness **99%**.
- **Mathematical evidence.** Hessian of \(W_i\) is \(-M_i^{-1}\); strict concavity \(\Leftrightarrow M_i^{-1}\succ 0\). Flow degeneracy when \(K_{02}=K_{01}+K_{12}\) (standard transportation polytope).
- **Code evidence.** Objective at `core.py:265`; no secondary flow-selection rule.
- **Numerical reproduction.**
  - Re-solve spread on a PD instance: \(\max|\Delta D|=\max|\Delta p|=0\).
  - Tied-path 3-node instance: CLARABEL / SCS / OSQP flows differ by up to \(\sim 1.13\) MMT while remaining optimal.
- **Attempt to falsify.** Tried to find PD instances with multiple \(D\) — none.
- **Falsification result.** Uniqueness of \((D,p)\) stands; non-uniqueness of \(f\) confirmed as README states.
- **Recommended action.** Optional: document that reported bilateral flows are a solver-dependent selection from the optimal face (caveat already partially present).
- **Complexity-budget.** Prose only.
- **Changes published results?** No for aggregates/prices; bilateral flow tables could differ by solver version.

---

### SE3 — Dual interpretation \(\lambda=p\) and Enke–Samuelson KKT (interior)

- **Finding.** For **interior** demand (\(D_i^g>0\)), the balance-constraint dual from cvxpy under `Maximize` satisfies \(-\mathrm{dual}=\lambda_{\mathrm{README}}=p\) to numerical noise (\(\max|-\mathrm{dual}-p|=0\) on the 17-country baseline with a Russia wheat tax). Classical Enke–Samuelson inequalities and complementary slackness hold on reported prices for active/inactive routes (0 inequality violations and 0 CS violations at \(1\)–\(2\,\$/\mathrm{t}\) tolerance on the tested instances).
- **Classification.** **H**, with a boundary caveat recorded as SE4.
- **Severity.** —.
- **Confidence.** **97%**.
- **Mathematical evidence.** Stationarity in \(D\): \(\nabla W_i - \lambda_i + \mu_i = 0\). When \(D_i>0\), \(\mu_i=0\Rightarrow\lambda_i=p_i\). Stationarity in \(f_{ij}\): \(-\,K_{ij} + \lambda_j - \lambda_i \le 0\) with equality if \(f_{ij}>0\).
- **Code evidence.** Duals are **not** used in `MarketResult`; prices always from `DemandSystem.price` (`core.py:292`). Dual check is an external verification of the QP.
- **Numerical reproduction.** TEST 2 and TEST 10 in `audit_spatial.py`; ES checks on tiny and shipped instances.
- **Attempt to falsify.** Looked for ES violations on shipped baseline with \(\tau_{\mathrm{Russia,wheat}}=50\) — none.
- **Falsification result.** Interior claim stands.
- **Recommended action.** None required for code. Optional README note that \(\lambda=p\) is the interior KKT identification (see SE4).
- **Complexity-budget.** Prose.
- **Changes published results?** No.

---

### SE4 — At \(D=0\), shadow price \(\lambda\) can exceed inverse-demand choke price

- **Finding.** When \(D_i^g=0\), complementary slackness on \(D\ge 0\) allows \(\mu>0\), so \(\lambda_i = p_i(0)+\mu \ge p_i^{\mathrm{choke}}\). Constructed 1-node \(A=0\) and 2-node scarce/high-\(K\) examples show \(\lambda \neq p_{\mathrm{inv}}\) while the QP remains optimal. The code still reports \(p_{\mathrm{inv}}=M^{-1}(a-D)\) (choke at \(D=0\)). README’s blanket “\(\lambda^g_i = p^g_i\)” is therefore slightly overstated at the demand boundary. In practice, with affordable trade, nodes rarely sit at \(D=0\); shipped baseline \(\min D_{\mathrm{wheat}}\gg 0\).
- **Classification.** **G** (documentation imprecision), not a coding bug.
- **Severity.** Low.
- **Confidence.** **90%**.
- **Mathematical evidence.** KKT with inequality dual \(\mu\) as above; reproduced \(\lambda-\,p_{\mathrm{inv}}\approx 411\) on a scarce 2-node example with \(K=1000\), \(D_1=0\).
- **Code evidence.** `core.py:292` always uses inverse demand.
- **Attempt to falsify.** Sought shipped-scale ES violations in reported prices after zeroing some countries’ wheat availability — 0 violations; nodes imported rather than sitting at \(D=0\).
- **Falsification result.** Practical impact on shipped calibration not demonstrated; mathematical caveat stands.
- **Recommended action.** One-sentence README clarification: \(\lambda=p\) when \(D>0\); at \(D=0\), \(\lambda\ge p^{\mathrm{choke}}\).
- **Complexity-budget.** Zero code cost.
- **Changes published results?** No.

---

### SE5 — Solver fallback accepts `D.value is not None` and ignores `prob.status` (F3 / S10 root cause)

- **Finding.** The loop at `core.py:281–287` tries `CLARABEL → SCS → OSQP`, swallows **all** exceptions (`except Exception: continue`), and accepts a solution iff `D.value is not None`, **without** reading `prob.status`. Consequences:
  1. **Indefinite \(M\) / non-DCP:** every solver attempt raises `DCPError`; after the loop, `D.value is None` and `np.clip(D.value, 0, None)` raises  
     `TypeError: '>=' not supported between instances of 'NoneType' and 'float'` at `core.py:289`.
  2. **Globally infeasible QP** (\(\sum_i A^g_i < 0\)): all three solvers return `status='infeasible'`, `D.value is None` → **same** `TypeError` at the same line.
  3. **`optimal_inaccurate`:** if a solver returns a numeric `D.value` with inaccurate status, it is **accepted**. Forced SCS with `max_iters=5` on the 17-country problem: `status=optimal_inaccurate`, would be accepted, with \(\max|\Delta D|\sim 30\), \(\max|\Delta p|\sim 2\cdot 10^5\), balance residual \(\sim 10^2\) MMT versus CLARABEL’s optimal solution.
- **Classification.** **C** (numerical / robustness), with a **B** component (acceptance logic does not match the docstring’s implication of a solved concave QP).
- **Severity.** Medium (latent in the shipped demo because CLARABEL typically returns `optimal`; loud failure on invalid inputs; silent corruption risk if CLARABEL fails and SCS returns inaccurate).
- **Confidence.** **99%**.
- **Mathematical / economic evidence.** Infeasibility when \(\sum A<0\); non-concavity when \(M^{-1}\not\succeq 0\).
- **Code evidence.** `sheaf/core.py:281–289`.
- **Numerical reproduction.** `audit_spatial.py` TESTS 4, 5, 9, 12; `audit_followups.py` inaccurate-quality probe.
- **Attempt to falsify.**
  - Checked whether any solver returns a non-`None` value on clear global infeasibility — **no** (CLARABEL/SCS/OSQP all `infeasible`, `D_none=True`).
  - Checked whether cvxpy silently accepts clearly indefinite `Minv` — **no** (`DCPError`); near-PSD edge with a zero eigenvalue produced absurd prices (`1e13`) when accepted — separate fragility, not a refutation of the TypeError path.
  - Confirmed local \(A_i<0\) with \(\sum A\ge 0\) **does** solve cleanly (imports cover the deficit) — narrows “negative availability ⇒ crash” but does **not** refute the global-infeasibility crash.
- **Falsification result.** TypeError fallthrough **survives**. Acceptance-without-status is real; inaccurate-acceptance is real though not hit when CLARABEL succeeds first.
- **Recommended action (design only — not implemented).** Minimal publication-quality protocol:
  1. After each `prob.solve(...)`, record `status`.
  2. **Accept** only if `status in {optimal, optimal_inaccurate}` **and** `D.value is not None` (optionally reject `optimal_inaccurate` or re-try next solver first).
  3. Prefer: try next solver on `optimal_inaccurate` / `user_limit` before accepting.
  4. If the loop ends without an accepted solve: raise a dedicated error, e.g. `SpatialEquilibriumError(status=..., last_statuses=[...], hint=...)`, distinguishing `infeasible` (check \(\sum A\)), `DCPError`/non-PSD `Minv`, and solver failures.
  5. Do **not** bare-`except` forever; catch `cp.DCPError` and solver errors separately, or re-raise after logging.
  6. Optional cheap precondition: if `availability.sum(axis=0).min() < 0`, raise before building the QP.
- **Complexity-budget.** A few lines; zero new parameters; improves diagnosability; negligible runtime. Strongly justified.
- **Changes published results?** No change to successful CLARABEL-optimal runs (including the shipped demo). Changes failure mode from opaque `TypeError` to an informative error; would reject inaccurate SCS solutions that are currently acceptable if CLARABEL were skipped/failed.

---

### SE6 — Phase 1 F3 (indefinite \(M\) → opaque TypeError): **CONFIRMED**

- **Finding.** Independently reproduced: non-PSD / indefinite `Minv` ⇒ `is_dcp=False` ⇒ `DCPError` on every solver attempt ⇒ swallowed ⇒ `TypeError` at `core.py:289`.
- **Classification.** Same as SE5 (**C**/B).
- **Severity.** Medium.
- **Confidence.** **99%**.
- **Status vs Phase 1.** **CONFIRMED** (same crash site and mechanism; Agent 1’s incidental finding was correct).
- **Recommended action.** Covered by SE5 protocol; optionally also guard in `build_demand_system` (outside this report’s implementation remit; overlaps Agent 1 F1).
- **Changes published results?** Not for the PD shipped 3-grain calibration.

---

### SE7 — Phase 1 S10 (global infeasibility → same TypeError): **CONFIRMED** (already-narrowed scope retained)

- **Finding.** Independently reproduced: \(\sum_i A_i < 0\) for a grain ⇒ all solvers `infeasible` ⇒ same `TypeError` at `core.py:289`. Local negative availability with nonnegative world sum is **feasible and economically sensible** (import to cover a storage build) — consistent with Agent 3’s own narrowing.
- **Classification.** **C** (same acceptance bug); the storage-side path into global infeasibility is a scenario issue, not a balance bug in the QP.
- **Severity.** Medium-low for the shipped demo (not hit); medium for stress tests / alternate calibrations with aggressive storage builds after gluts.
- **Confidence.** **99%** for the crash; **95%** that local-negative-A is intentional/OK.
- **Status vs Phase 1.** **CONFIRMED** on the crash mechanism; Agent 3’s narrowing (local OK / global bad) **retained** after independent checks (`sum A=0` yields \(D=0\), finite choke prices; local \(A=-2,A'=15\) solves).
- **Recommended action.** SE5 protocol + optional \(\sum A\ge 0\) precondition.
- **Changes published results?** No for the 12-period Black Sea demo (no global infeasibility observed in Phase 1; not re-litigated here beyond QP probes).

---

### SE8 — Negative prices: permitted by the math; not economically intended; reachable; consequential

Answers to the mandate’s five questions:

| # | Question | Answer |
|---|---|---|
| (1) Mathematically permitted by the stated model? | **Yes.** No \(p\ge 0\) constraint; \(p=M^{-1}(a-D)\) is unrestricted. Equality clearing forces \(\sum D=\sum A\). |
| (2) Economically intended? | **No.** README never discusses negative prices; grain prices as a \$/t index are implicitly nonnegative in economic narrative. |
| (3) Reachable under plausible parameterizations? | **Yes.** Any world glut with \(\sum_i A^g_i > \sum_i a_i^g\) (demand at \(p=0\)) forces some \(D>a\) somewhere and drives prices negative under linear inverse demand. |
| (4) Reachable under the shipped calibration? | **Yes, under glut shocks; not under the shipped Black Sea shortfall demo.** Theoretical headroom at baseline \(A=Q\): wheat \(\approx 15.4\%\), rice \(\approx 14.6\%\), maize \(\approx 22.6\%\) above world availability before the \(p=0\) hyperplane. Uniform production scale \(\approx 1.15\) already produces negatives; wheat-only scale \(\approx 1.22\). A demo-like shortfall run: \(\min p\approx 163>0\). A **+20%** global glut run: \(\min p\approx -131\), 100 negative price cells. |
| (5) Consequential for storage / government? | **Yes.** `market_responsive_storage` with \(p_{\mathrm{ref}}=-50\) produced a **build** (\(\Delta\approx +15.8\) MMT on USA wheat params). `strategic_storage` with negative \(p_{\mathrm{ref}}\) fails the price-crisis test and can take the **build** branch when \(p\le\) trigger — i.e. accumulating public stocks into a glut with negative prices. |

- **Classification.** **D** (limitation of linear inverse demand + no free disposal) / **G** (undocumented domain restriction). **Not** an A-class algebra error in the QP.
- **Severity.** Low–medium for crisis-focused shortfall papers; high if anyone runs boom/glut scenarios or claims global domain validity.
- **Confidence.** **98%**.
- **Relation to Phase 1 F14.** Headroom numbers match Agent 1’s ~15% claim for wheat/rice; **CONFIRMED** as an independent measurement (maize headroom larger, ~23%).
- **Attempt to falsify.** Checked whether PD / substitution prevents negatives — no; multi-grain shipped systems still go negative under glut. Checked whether \(D\ge 0\) alone prevents \(D>a\) — no, because balances force consumption of excess supply.
- **Falsification result.** Negative prices are a real domain limitation, not a solver bug.
- **Recommended action.** Document the ~15% (grain-dependent) headroom in README Caveats. **Do not** add free disposal solely to “fix” this for a food-security crisis model (see SE9). Optional soft guard: warn if \(\min p<0\).
- **Complexity-budget.** Documentation: free. Free disposal: adds \(nG\) variables every QP, multiplied by the export-game grid — poor cost/benefit for SHEAF’s stated question.
- **Changes published results?** No for the Black Sea shortfall demo; yes for any glut experiment already run without noticing negatives.

---

### SE9 — Absence of free disposal forces consumption of excess supply

- **Finding.** The equality \(A+\mathrm{imports}-\mathrm{exports}-D=0\) with \(D\ge 0\) and **no** disposal slack means excess supply must be consumed. Explicit tiny example: forced \(D\) sum equals \(A\) sum with deeply negative prices. The same instance **with** a hypothetical disposal slack \(s\ge 0\) (not in SHEAF) optimally disposes the excess and pins prices at \(\approx 0\).
- **Classification.** **D** / **E** (modeling choice relative to SPE models that allow disposal or \(p\ge 0\) with inequality clearing). Not a coding bug relative to README (README states equalities).
- **Severity.** Low for scarcity applications; the pathology is the glut dual of SE8.
- **Confidence.** **99%**.
- **Recommended action.** Disclose; do not add disposal without a science case (complexity budget fails for the crisis narrative).
- **Changes published results?** No.

---

### SE10 — `np.clip` on solver output is inert on successful PD solves; not a correctness fix for failure

- **Finding.** After a successful solve, `np.clip(..., 0, None)` on \(D\) and \(f\) (`core.py:289–291`) does not change the shipped baseline (raw minima already \(\ge 0\); balance unchanged). It does **not** protect against `D.value is None` (clip is what raises the TypeError).
- **Classification.** **H** for successful solves; part of SE5’s failure path.
- **Confidence.** **95%**.
- **Recommended action.** None beyond SE5.
- **Changes published results?** No.

---

### SE11 — Commodities couple only through demand cross-terms (README claim)

- **Finding.** With substitution on, a Russia wheat availability shock moves rice and maize prices (mean \(|\Delta p|\) of order 19 and 9 \$/t alongside wheat ~62). Network constraints are per-grain; cross-grain coupling in the QP enters only via off-diagonal blocks of each \(W_i\) / `Minv`. This matches README §2’s coupling claim.
- **Classification.** **H**.
- **Confidence.** **96%**.
- **Recommended action.** None.
- **Changes published results?** No.

---

### SE12 — Export-tax insulation wedge works as documented

- **Finding.** With \(\tau_{\mathrm{Russia,wheat}}=50\), Egypt–Russia wheat price wedge \(\approx 73.7\) \$/t (tax + transport), Russia domestic price depressed relative to importers — consistent with README’s insulation narrative.
- **Classification.** **H**.
- **Confidence.** **95%**.
- **Recommended action.** None.
- **Changes published results?** No.

---

## README §2 claim checklist

| Claim | Verdict |
|---|---|
| Joint multi-commodity concave QP (Samuelson–TJ) | **Holds** (SE1) |
| Objective \(\sum W_i - \sum K f\) | **Holds** |
| \(K = c\phi\psi + \tau_i + m_j\) | **Holds** |
| Balance equalities + no self-trade | **Holds** |
| Coupling only via cross terms of \(W_i\) | **Holds** (SE11) |
| \(\lambda = p\) at optimum | **Holds interior**; **narrowed** at \(D=0\) (SE3–SE4) |
| Enke–Samuelson inequalities + CS | **Holds** for reported prices on tested interior solutions |
| Export tax widens domestic/world wedge | **Holds** (SE12) |
| Unique \((D,p)\); flows may be non-unique | **Holds** (SE2) |
| Solver always returns a meaningful optimum | **Fails** on non-DCP / infeasible / inaccurate paths (SE5–SE7) |

---

## Minimal robust solver-status protocol (design only)

Not implemented (per mandate). Intended behavior for publication-quality use:

```text
statuses = []
for solver in (CLARABEL, SCS, OSQP):
    try:
        prob.solve(solver=solver, verbose=False)
    except cp.DCPError as e:
        raise SpatialEquilibriumError("non-DCP objective (check Minv PSD)", cause=e)
    except Exception as e:
        statuses.append((solver, "exception", str(e)))
        continue
    statuses.append((solver, prob.status, None))
    if prob.status == "optimal" and D.value is not None:
        break
    if prob.status == "optimal_inaccurate" and D.value is not None:
        # prefer trying next solver; accept only if last resort
        continue
    # infeasible / unbounded / solver_error: try next
else:
    raise SpatialEquilibriumError(
        f"no acceptable solve; statuses={statuses}; "
        f"world_A={availability.sum(0)}"
    )
# then assemble MarketResult (clip optional)
```

Optional precondition: `if np.any(availability.sum(0) < -1e-9): raise ...`.

---

## Complexity-budget summary for recommended changes

| Change | Benefit | Cost | Recommend? |
|---|---|---|---|
| Status-aware acceptance + named error (SE5) | Diagnosability; avoid silent inaccurate solves | ~10 lines | **Yes** |
| \(\sum A\ge 0\) precondition | Clearer infeasibility | 1–2 lines | **Yes** |
| README: \(\lambda=p\) interior; negative-price headroom; no free disposal | Honest domain | Prose | **Yes** |
| Free disposal / \(p\ge 0\) constraints | Removes glut pathology | Extra vars every QP × game grid; changes economics | **No** (for now) |
| Force unique flows (secondary criterion) | Reproducible bilaterals | Extra rule/complexity | **No** unless flow tables are a paper deliverable |

---

## Phase 1 hypotheses touched

- **Agent 1 F3** (indefinite \(M\) → DCPError swallowed → opaque TypeError): **CONFIRMED**
- **Agent 3 S10** (global infeasibility → same TypeError; local negative \(A\) OK): **CONFIRMED**
- **Agent 1 F14** (~15% glut headroom → negative prices; undocumented): **CONFIRMED** (wheat/rice ~15%; maize ~23%; demo shortfall safe; +20% glut unsafe)

No Phase 1 spatial-equilibrium hypotheses were refuted. F3/S10 are the same acceptance defect with two triggers; SE5 is the unified root-cause finding.

---

## Scratch artifacts

- `/tmp/sheaf_audit_agent4/audit_spatial.py` — main verification suite  
- `/tmp/sheaf_audit_agent4/audit_followups.py` — duals at \(D=0\), flow ties, demo/glut prices, inaccurate quality, gov storage  
- `/tmp/sheaf_audit_agent4/audit_es_boundary.py` — Enke–Samuelson at corners  
- `/tmp/sheaf_audit_agent4/audit_out.txt`, `followup_out.txt`, `es_out.txt` — logs  
- `/tmp/sheaf_audit_agent4/venv/` — isolated deps (not part of the repo)

Nothing under `sheaf/`, `demo.py`, or `scripts/` was modified.

---

AGENT 4 COMPLETE

- F3 (TypeError via indefinite/non-DCP \(M\)): **CONFIRMED**
- S10 (TypeError via global infeasibility): **CONFIRMED**
- F14 (negative-price headroom / linear demand limitation): **CONFIRMED**
