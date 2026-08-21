# AGENT 3 (Phase 1) — Storage Layer vs. TWIST/Agrimate Lineage

**Scope:** `market_responsive_storage()`, `strategic_storage()`, storage state, timing, government/private reserve interaction. Scratch code in `/tmp/sheaf_audit_agent3/`.

**Lineage sourcing.** Primary/near-primary sources were available locally (outside the repo): Kuhla, Kubiczek & Otto 2025 (Agrimate, published paper + ODD supplement — §D.3 process scheduling, Eq. D.3/D.6/D.31a), and a local reconstruction of TWIST's mechanism (not primary — flagged, confidence lowered accordingly on TWIST-dependent claims).

**What TWIST and Agrimate actually do, established first (per CLAUDE.md's ordering rule):**

*TWIST*: two stocks ($I_p$, $I_c$) that are not decisions at all — they are *schedules inside the market-clearing condition* $S(P)=D(P)$, solved simultaneously with price. No expectation, no discounting, no deadband.

*Agrimate*: commercial storage is a genuine finite-horizon discounted expected-profit maximization (Eq. 1a–2), explicitly *"similar to... competitive storage (Williams and Wright, 1991), with three major differences."* Strategic storage is a pure partial-adjustment refill (Eq. D.31a), symmetric in both directions. Per-step schedule: **Harvest → Policy update (export restrictions) → Sales (commercial storage, using the *current* harvest) → Expectation formation → ... → Procurement (strategic refill).**

Two lineage properties matter throughout: (a) both predecessors respond to the *current* period's harvest/price, not the previous period's; (b) in Agrimate, export policy is known *before* the storage/sales decision.

## 1. Explicit period timeline of `SheafModel.step` (derived line-by-line)

| # | Event | file:line | Information available |
|---|---|---|---|
| 0 | Beginning stocks; $p^{\rm prev}$ = last realised price | prior step / `core.py:174` | — |
| 1 | Production/shock realization | `:418,425` | $\xi^g_i(t)$ now known |
| 2 | Expectation formation: $p^e=p^{\rm prev}+\kappa(p^{\rm norm}-p^{\rm prev})$ | `:426–427,413–414` | Only $p^{\rm prev}$ — **not** `prod`, even though already computed |
| 3 | Private storage decision | `:428` → `:184–195` | `prod` never passed (verified by signature) |
| 4 | Government storage decision | `:429` → `:198–216` | Sees contemporaneous harvest (`prod - dm`), still lagged price |
| 5 | Availability formed | `:431` | — |
| 6–7 | Stress-gate probe, `stressed` flag | `:435–437` | First price of period $t$ |
| 8 | Export game (if stressed), warm-started | `:434,439–443` | Government's reserve decision (step 4) already locked in |
| 9 | Market clears | `:361`/`:447` | — |
| 10 | Stock update, $p^{\rm prev}\leftarrow p_t$ | `:450–453` | — |

**Coherence assessment.** Ordering matches README §5. What the timeline surfaces is that the shock is known by step 1 but used by only one storage mechanism, and government reserve decisions precede the government's own export-tax decision with no feedback either way — an inversion of Agrimate's policy-before-sales ordering.

## 2. Derived material-balance identity, verified computationally

$$Q^g_i\xi^g_i(t) - \Delta^{\rm mkt}_i(t) - \Delta^{\rm gov}_i(t) + \sum_kf^g_{ki}(t) - \sum_kf^g_{ik}(t) - D^g_i(t) = 0\quad\forall i,g,t \tag{MB}$$

Real 12-period run (17 countries × 3 grains × 12 periods = 612 cells):
```
GLOBAL: max |material-balance residual| = 4.605e-12 MMT
GLOBAL: min availability over all i,g,t = 0.0000 MMT
GLOBAL: mass created by max(0,.) clip on stocks = 0.000e+00 MMT
```

## S1 — Material balance holds exactly

- **Classification.** H. **Confidence.** 99%.
- **Attempt to falsify.** Checked three leak paths (post-constraint $D$ clip, flow re-clip, $\max(0,\cdot)$ stock guards) — all confirmed inert (residual stays at $10^{-12}$; mass created exactly 0.0).
- **Result.** Survives all three.

## S2 — Stocks provably never go negative; releases individually bounded

- **Classification.** H. **Confidence.** 97%. Proof plus reproduction; confirmed unreachable for the shipped `gov_release_frac=0.5<1` and capacity/stock ordering.

## S3 — README §3 matches the code symbol-for-symbol, but $p^{\rm ref}$'s definition (lagged price) is never stated

- **Classification.** **G.** **Severity.** Medium. **Confidence.** 95%.
- README §5's own sequencing makes the "current price" reading impossible — the README is internally consistent, merely silent.
- **Recommended action.** One sentence defining $p^{\rm ref}_{i,g}$ as the prior period's realised price.

## S4 — Private storage is structurally blind to the contemporaneous shock: the buffer arrives exactly one period late

- **Classification.** **D** primary, with **E/G** components. **Severity.** **High.** **Confidence.** 95%.
- **Mathematical evidence.** $\Delta^{\rm mkt}_t=\Phi(p_{t-1})=(\Phi\circ L)(p_t)$ — the contemporaneous rule composed with a one-period delay. Contrast: TWIST solves simultaneously in $P_t$; Agrimate's Eq. D.6 uses the *current* harvest $H^{(t)}$.
- **Code evidence.** `core.py:184` (signature has no `prod`/`shock` param), `:425–428` (`prod` computed then not passed), `:426` (`p_ref = c.p_prev[g]`).
- **Reproduction.** Real run: lagged rule vs. same function evaluated at the contemporaneous price — exact one-period shift:
  ```
   t  shock  dm_lagged  dm_if_contemporaneous
   5   0.6      0.000        -0.916
   6   0.6     -0.916        -1.646
   7   0.6     -1.646        -1.152
  ```
  **Russia — whose wheat crop just fell 40% — makes a storage adjustment of exactly 0.000 MMT in the shock period.** Price consequence (storage ON vs OFF): shock-period buffering 11.22 vs. 37.17 one period later.
- **Attempt to falsify.** Four attempts: (1) government channel compensates? — no, it's purely domestic and Russia/Ukraine hold no government reserves in the shipped calibration. (2) One period doesn't matter at annual resolution? — VALIDATION.md's own target *is* the annual price hike/stock anomaly, so a full-year displacement is not noise. (3) TWIST is also lagged? — no, both predecessors are contemporaneous (checked against primary/near-primary sources). (4) Using $p_{t-1}$ is the economically correct information set? — half right (price is genuinely unknown ex ante), but **the code's own harvest, already computed one line earlier, is ignored** — that is the precise defect, not the lagged price per se.
- **Result.** Survives, sharpened: the defect is omission of the current harvest, not use of a lagged price.
- **Recommended action.** Re-use the stress-gate probe price (`core.py:435–436`, already computed every period) as $p^{\rm ref}$ instead of `p_prev` — zero new parameters/state, ~zero extra cost (reuses an existing solve). **Highest-value change identified in this audit.**
- **Complexity-budget assessment.** High scientific benefit, ~zero cost, moves *toward* the lineage (both predecessors are contemporaneous).
- **★ NOTE per Phase 2 mandate: this recommendation must NOT be adopted without independent evaluation against alternative timing architectures — see Phase 2 Agent 5's report for that independent assessment.**

## S5 — The deadband is not centred on $p^{\rm norm}$: the rule defends $p^*=\frac{\kappa}{\kappa+r}p^{\rm norm}$, and the model is initialised exactly on the release side

- **Classification.** **D**, with a **G** component. **Severity.** Medium. **Confidence.** 97%.
- **Mathematical evidence.** $s(p^{\rm ref})=0 \iff p^{\rm ref}=p^*=\frac{\kappa}{\kappa+r}p^{\rm norm}$; downward bias $1-p^*/p^{\rm norm}=r/(\kappa+r)>0$ for any finite $\kappa,r>0$ — cannot be tuned away. Defaults give $p^*/p^{\rm norm}=0.9091$.
- **Reproduction.** `calibration.py` sets $p_0=p^{\rm norm}$ for all countries and initialises $p^{\rm prev}=p_0$ — **the model starts exactly at the release trigger, with no shock present.** Real run, $t=0$, no shock: world private wheat storage change $=-2.733$ MMT, every $\gamma>0$ country releasing.
- **Attempt to falsify.** (1) Is this correct Deaton–Laroque behaviour (release when $p=E[p]$, $r>0$)? Half right — but D–L's stationary distribution carries positive stock via price *variance*; SHEAF's expectation is deterministic, so there's no offsetting force, meaning "no stationary storage level exists" rather than "wrong sign." (2) Does calibration avoid it? No — it's the worst case, not a safe one.
- **Result.** Survives, reclassified from "sign error" to "no stationary rest point at the calibration anchor."
- **Recommended action.** Zero-parameter fix: recentre `p_norm` so $p^*=\bar p_0$ (one-line calibration change). Reject a full stochastic D–L fixed point (moves away from both TWIST and Agrimate, adds a nested fixed-point solve inside an already-nested QP/game loop).

## S6 — The symmetric deadband is a transaction-cost band, not a carrying cost; carrying cost is never charged, no spoilage

- **Classification.** **D**, with a **G** component. **Severity.** Low–medium. **Confidence.** 90%.
- A carrying-cost arbitrage gives a one-sided threshold; SHEAF's symmetric $\pm\theta$ band is the signature of a transaction cost. `mkt_cost` is used only as the band half-width, never charged in welfare; no spoilage term exists anywhere in the module (grep-confirmed).
- **Recommended action.** Documentation-only: describe as "competitive-storage-*inspired*," and $\theta$ as a transaction/inaction band. No code change.

## S7 — The government "crisis" test measures autarky, not scarcity: structural net importers are permanently "in crisis" and drain to near-zero with no shock at all

- **Classification.** **D**, with a **G** component (contradicts README's own "release in crisis / rebuild in calm" framing since these countries have no calm periods). **Severity.** **High.** **Confidence.** 97%.
- **Mathematical evidence.** $\Sigma = D_{0,i}^g - (Q^g_i\xi^g_i - \Delta^{\rm mkt})$, no imports term. For any structural importer ($D_0>Q$), $\Sigma>0$ identically — the rebuild branch (`core.py:211–215`) is structurally unreachable while `gov_stock>0`.
- **Reproduction.** Shipped calibration: China wheat/rice/maize, Egypt wheat all show `shortfall>0` and `crisis_every_period=True`. Real 12-period run: China's gov maize stock 100→0.078 MMT; wheat 100→16; Egypt wheat 4.5→0.0011 — **identical decay before, during, and after the shock.** World government stock: 349.5→137.8 MMT over 12 periods.
- **Attempt to falsify.** (1) "Reserve covers the import gap" story fails on its own terms — a reserve drawn down by the *full* gap every year forever with no replenishment mechanism from imports is not a buffer; Agrimate's purchaser rule (Eq. D.31a) explicitly does the opposite (raises demand to refill when below baseline, "and vice versa"). (2) Price-trigger branch can't override it — trigger only *adds* crisis conditions. (3) Self-corrects near zero? No — $\eta_{\rm rel}=0.5<1$ means asymptotic decay, never reaching zero, so the rebuild branch stays unreachable forever (links to S8).
- **Result.** Survives all three, strengthened by the Agrimate comparison.
- **Recommended action.** Redefine $\Sigma$ as an anomaly relative to baseline net-import position (reduces to $Q^g_i(1-\xi^g_i)+\Delta^{\rm mkt}$ — zero at baseline, positive only under an actual shortfall). One-line change, zero new parameters, uses data already in scope.
- **Complexity-budget assessment.** High scientific benefit (restores two-regime behavior, makes government-stock series usable for VALIDATION.md Level 1), zero cost on every other axis, moves toward Agrimate.
- **★ NOTE per Phase 2 mandate: the recommended anomaly definition must be independently derived and compared against alternatives, not adopted directly — see Phase 2 Agent 5's report for that independent assessment.**

## S8 — Logic fall-through: `strategic_storage` can build reserves while in shortfall when `gov_stock==0`

- **Classification.** **B** (coding bug — README's two-branch partition admits no such case). **Severity.** Low for shipped calibration (**unreachable** — proven), medium for user-supplied calibrations (the documented use case). **Confidence.** 95%.
- **Code evidence.** `core.py:205` (`if crisis and c.gov_stock[g] > 0`) — falls through to the build branch (`:211–215`) when `gov_stock==0`, guarded only by the price test, not by `not crisis`.
- **Reproduction.** Egypt's own parameters with `gov_stock` forced to 0: `shortfall=+11.00 (CRISIS)`, `p_ref<=trigger` → `dg=+0.6000` (builds while in shortfall).
- **Attempt to falsify.** Checked shipped-calibration reachability: `gov_stock` decays geometrically and never hits exactly zero (Egypt after 12 periods: $1.1\times10^{-3}$, still positive; would take ~1080 periods to underflow). **Unreachable today**, but the repository explicitly invites calibration replacement, where a stated target with zero starting stock is entirely natural.
- **Recommended action.** One-line: `if not crisis:` instead of the current price-only guard.

## S9 — Storage and the export-restriction game are exactly independent within a period; government welfare has no reserve term

- **Classification.** **E** for the modeling-philosophy judgment; the independence *fact* itself is H-grade established. **Severity.** Medium. **Confidence.** 95% (fact) / 75% (materiality judgment).
- **Reproduction.** Two otherwise-identical models, game on vs. off: `max |dm/dg diff| = 0.0` at every period; `max price diff = 29.23`; `max tau chosen = 120.0` — storage decisions are bit-identical regardless of whether the game moves prices by 29 $/t.
- **Attempt to falsify.** Checked stress-gate leakage (none — gate is strictly downstream of storage) and warm-start leakage (none — `last_tau` only affects the game's start point). Checked against Agrimate: its "Policy update" (process 2) precedes "Sales" (process 3), so Agrimate's storers *do* know current restrictions — SHEAF gives strictly less information than its own cited lineage.
- **Recommended action.** No architectural change now; disclose the decoupling in README §5. If coupling is later wanted, the natural minimal step is the same probe-price reuse already recommended in S4 (gives government reserves contemporaneous information without any joint optimization). Reject fully joint $(\tau,\Delta^{\rm gov})$ optimization — multiplies the game's already-expensive grid search for unproven benefit.
- **★ Independently re-investigated in Phase 2 by Agent 5 — see that report for status.**

## S10 — Negative effective availability is reachable; not a balance violation locally; crashes uninformatively when global

- **Classification.** **C.** **Severity.** Medium-low. **Confidence.** 95%.
- **Reproduction.** Local negative cell (single node building stock): QP solves fine, economically sensible (imports to fill store). **Global** negative availability for a grain: all three solvers return `infeasible`/`infeasible_inaccurate`, `D.value=None`, raising the identical `TypeError` at `core.py:289` that Agent 1 independently found via a different trigger (indefinite $M$). Endogenous two-period run (35% glut then 95% failure) reaches this state with real negative-availability cells across all seven wheat exporters.
- **Attempt to falsify — four attempts, two partially succeeded (reported honestly).** (1) Shipped 12-period demo run: `min availability=0.0000, n_neg_avail=0` — **latent, not active** in the shipped scenario. (2) Is negative availability itself unphysical? **No** — it just means a node imports to build stock; the QP handles it cleanly. This corrects the original hypothesis. (3) Do the two storage mechanisms jointly over-draw? **No** — the hypothesis is wrong: government storage *sees* the private decision (`core.py:429` passes `prod-dm` in), and if private build pushes availability below $D_0$, government's crisis branch (S7) partially offsets by releasing — sequencing actually helps, though no offset was available for the pure exporters tested (none hold government reserves). (4) Is the endogenous path plausible? Only partially — reaching it required a price crash deep enough to produce *negative* prices (a separate pathology, connects to Agent 1's F14), though analytic thresholds show plausible-positive-price triggers exist too (e.g. USA wheat at $p_{\rm prev}=150$, $\xi<0.108$).
- **Result.** Survives only narrowly: the crash-on-global-infeasibility is real and the error message is uninformative; the "unphysical" and "mechanisms over-draw jointly" framings are refuted and reported as such.
- **Recommended action.** Check `prob.status` rather than `D.value is not None`, raise a named error. Overlaps the market-QP subsystem (not directly audited by any of the three agents this round) — reported here as the storage-side path into it. **★ Same underlying code region independently found by Agent 1 (F3) via a different trigger. Independently re-audited in Phase 2 by Agent 4 (spatial equilibrium).**

## S11 — `strategic_storage` has no capacity bound; `mkt_capacity` defaults to `+inf`

- **Classification.** **C**, shading **D**. **Severity.** Low (shipped — arithmetically bounded by an order of magnitude) / medium (replaced calibration). **Confidence.** 90% (latent, not reproduced as an active failure).

## S12 — `mkt_cost` is a scalar, so the effective relative deadband varies 2:1 across grains (3.2%/2.0%/4.0% of $p_0$ for wheat/rice/maize)

- **Classification.** **D.** **Severity.** Low. **Confidence.** 92%. Partially blunted on falsification (a scalar $/t carrying cost is defensible; less so as a transaction band per S6's reclassification).

## S13 — Producer income uses unshocked baseline production; overlaps game-theory remit

- **Classification.** **D.** **Confidence.** 80% (explicitly lower — flagged as a question, not a settled defect, for reconciliation with the game auditor).
- Explicitly restricted to the storage-relevant claim: whenever storage is active, sales ≠ production, so producer income is mismeasured independent of any shock. Explicitly noted as possibly-intended (a policy weight rather than realised income) — could not settle this from the code or README alone.
- **★ Cross-reference: independently and more fully audited by Agent 2 as F9 — see Phase 1 cross-agent summary. Reconciliation still open as of this checkpoint.**

## S14 — Expectations use no information unavailable at decision time — no look-ahead

- **Classification.** H. **Confidence.** 98%. Verified `last_tau`/`p_norm` cannot leak future information. Explicitly noted as the flip side of S4: the same strict-lagged-information property that causes S4 is also what guarantees no look-ahead — reported as a credit, not left silent.

## S15 — Storage parameters are unsourced; VALIDATION.md's Level-1 stock-anomaly target is not currently attainable as specified

- **Classification.** **F.** **Severity.** Medium. **Confidence.** 85%.
- **Attempt to falsify.** Checked whether differencing against a no-shock counterfactual (as `demo.py` already does) rescues the target — **works for S5's drift** (differencing removes it) but **not for S7** (China's release is identical in shocked/counterfactual runs, so the differenced anomaly is identically zero — the mechanism contributes nothing detectable either way).
- **Recommended action.** Before attempting Level 1: apply the S7 fix, and source $R_0$/$\vartheta$ from `data_usda.py`'s already-computed stock-to-use ratios (data the repo has, not data it needs).

## Terminology recommendation

**Recommended:** "adaptive price-band (deadband) storage," or "competitive-storage-*inspired* behavioural storage rule."
**Not recommended:** "competitive storage," "a Wright–Williams/Deaton–Laroque arbitrage rule" (README's current wording), or "TWIST/Agrimate-style storage."

Because the expectation is deterministic, the private rule collapses algebraically to *"release when last year's price was above $p^*+$band, build when below, do nothing between"* — a price-band inventory rule, with no intertemporal trade-off, no uncertainty, no fixed point. The public mechanism's rebuild branch is genuinely continuous with Agrimate's Eq. D.31a and can honestly be called a "trigger-and-rebuild public buffer stock" — its price/shortfall release trigger is a legitimate SHEAF *extension* beyond Agrimate, and should be claimed as such rather than described as inherited.

## What to preserve vs. change

**Preserve:** the two-stock architecture (maps to Agrimate's supplier/purchaser split); the partial-adjustment rebuild rule; closed-form (non-optimizing) storage rules generally, given the QP+game is already nested and expensive; exact material balance and non-negativity (S1, S2); no-look-ahead (S14).

**Change, in priority order, each a 1–3 line edit, zero new parameters/state:** (1) S4 — contemporaneous price signal via probe reuse [highest value]. (2) S7 — anomaly-based crisis test. (3) S8 — fix the fall-through. (4) S5 — recentre the band. (5) S3/S6 — terminology and documentation fixes. (6) S10a — solver-status check.

**Explicitly rejected under the complexity-budget rule:** a full stochastic dynamic-programming storage layer (moves away from *both* TWIST and Agrimate, adds a nested fixed-point solve, no benefit tied to SHEAF's stated question); joint reserve/tax optimization (multiplies the game's grid search, not needed for the paper's claims); spoilage/welfare-charged carrying cost (cheap but not required now — defer, disclose the simplification).

**Net assessment.** The storage layer is arithmetically sound — balance, conservation, non-negativity, no look-ahead all verify cleanly, and README's equations match the code. The problems are entirely in *what the rules respond to and when*: the private rule is a period late and drifts, the public rule mistakes structural import dependence for crisis, and both act before the government sets policy. Four of the six recommended changes move SHEAF *closer* to TWIST/Agrimate, not further away.

**IMPORTANT — Phase 2 status note added at this checkpoint (2026-08-09):** the S4/S7 recommended fixes above are Phase-1-only proposals. Phase 2 explicitly tasked Agent 5 with independently comparing S4's recommendation against two alternative timing architectures, and independently deriving/comparing shortfall definitions before endorsing S7's recommendation, rather than adopting either directly. See `SHEAF_AUDIT_STATE.md` for whether that independent evaluation has completed.
