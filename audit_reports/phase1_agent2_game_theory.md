# AGENT 2 (Phase 1) — Strategic Layer: `ExportRestrictionGame` and its invocation in `SheafModel.step`

**Scope:** `sheaf/core.py:302–362`, `:416–457`. All experiments ran from `/private/tmp/sheaf_audit_agent2/` against the unmodified repository, using the real `build_countries()`, `SpatialEquilibrium`, and `ExportRestrictionGame` — roughly 40,000 executed market QPs across all experiments.

## What the algorithm actually is

Tracing `core.py:335–362`: exact discretized-**coordinate** best response (Gauss–Seidel, in-place). Strategy set per exporter/grain is `np.linspace(0, tau_max, grid)` — default $\{0,30,60,90,120\}$. Nested loop `for i in exporters: for g in export_grain_idx[i]:` optimizes one scalar $\tau^g_i$ at a time, holding the country's *other* restricted grain fixed — **not** a joint optimization over the country's $\tau_i$ vector. Convergence test (`np.max(np.abs(tau-last)) < tol`) is evaluated at the *start* of each sweep, so it requires a full sweep with **zero** moves — an exact fixed point, not an approximate one.

## F1 — The algorithm computes an exact Nash equilibrium of the discretized game, not an approximation to it

- **Classification.** **H.** **Confidence.** 95–100%.
- **Mathematical evidence.** $\varepsilon_i = \max_{\tau_i'\in\mathcal{T}_i}\mathcal{W}_i(\tau_i',\tau_{-i}) - \mathcal{W}_i(\tau_i,\tau_{-i})$, evaluated over the algorithm's **own** grid, using the model's own `_welfare` and `SpatialEquilibrium.solve` — no re-derivation introduced.
- **Reproduction.** Real in-run stressed states (demo's Black Sea shock, wrapped at runtime, no repo edit), all 11 exporters, all three game calls ($t=5,6,7$):
  ```
  USA        tau=[0.0, 0.0]   eps_coord=0  eps_joint=0
  Russia     tau=[30.0]       eps_coord=0  eps_joint=0
  Ukraine    tau=[30.0, 0.0]  eps_coord=0  eps_joint=0
  Argentina  tau=[30.0, 0.0]  eps_coord=0  eps_joint=0
  ... (all 11, all zero)
  ```
- **Attempt to falsify.** (a) Budget truncation: re-ran at `max_iters=12`, checked what `max_iters=3` would have returned — 85 runs, `nonconv=0 cycles=0 exploitable=0`. (b) Coarser grids ($\{2,3,5\}$) × stronger substitution: 96 runs, `exploitable-on-own-grid: 0`. (c) Simultaneous two-grain multi-country stress: 20 scenarios, all clean.
- **Result.** Survives all three.
- **Recommended action.** None.

## F2 — Coordinate vs. joint best response: gap real in principle, measured at exactly zero in SHEAF

- **Classification.** **H** for tested calibrations (60–80% as a forward-looking claim about untested/real calibrations).
- **Mathematical evidence.** Coordinate optimality implies joint optimality iff the discrete cross-difference $\Delta(a,b)=\mathcal{W}_i(a,b)-\mathcal{W}_i(a,0)-\mathcal{W}_i(0,b)+\mathcal{W}_i(0,0)\equiv0$. No a-priori reason for this to hold — $\tau^w_i$ moves $p^w_i$, which moves $D^m_i$ through $M_i$'s off-diagonal.
- **Code evidence.** `core.py:344–348` — trial perturbs a single `[i,g]` entry only. Multi-grain exporters: USA, Ukraine, Argentina (wheat+maize).
- **Reproduction.** Joint enumeration on own grid, 96 runs (grid∈{2,3,5} × subst_scale∈{0.6,0.9} × 16 shock combos): **0/96 exploitable**. On a 5×-finer grid (625 joint combos/exporter): `eps_joint == eps_coord` to the last digit in all 22 exporter-instances. Direct measurement of Ukraine's full $13\times13$ welfare surface: $\max|\Delta| = 138.6$ vs. total range $111{,}550.6$ — **0.12%** of range.
- **Attempt to falsify (i.e., attempt to establish the criticism).** Deliberately tried binary grids, $\sigma=0.9$, simultaneous dual-grain shortfalls — could not construct a counterexample within SHEAF's parameter space.
- **Result.** Criticism did **not** survive; recorded as H per CLAUDE.md.
- **Recommended action.** No code change (joint search would cost $\text{grid}^{|G_i|}$ QPs for measured benefit of zero — fails complexity budget decisively). One-line README note that the sweep is coordinate-wise and joint optimality was numerically verified, to be re-checked under a real calibration.

## F3 — The default tax grid (5 points, 30 $/t spacing) materially distorts both margins of the model's headline output

- **Classification.** **C.** **Severity.** **Medium–high.** **Confidence.** 95–100%.
- **Mathematical evidence.** README defines the strategy space as a continuum; the code searches a 5-point subset. Discretization error in the *policy* variable is first-order even though the welfare loss is second-order (≤1% of $\mathcal{W}_i$, per F1).
- **Code evidence.** `core.py:315` (`grid=5`), `:340`, `:380`, `:474` (`n_restrict = (tau>1.0).sum()`).
- **Reproduction.** Russia's own-$\tau$ welfare profile at $t=7$ (49 QPs): true optimum at $\tau=15$ ($W=65475.02$); grid=5 returns $\tau=30$ ($W=64950.02$) — **twice** the optimum, 525 lost (0.81%). Grid ladder on the shipped run's own per-period states:
  ```
  t=5  grid5 n=3 {Russia 30, Ukraine 30, Argentina 30} | grid25 n=3 {..., Argentina 20}
  t=6  grid5 n=0 {}                                    | grid25 n=2 {Russia 5, Ukraine 5}
  t=7  grid5 n=2 {Russia 30, Ukraine 30}                | grid25 n=3 {..., Argentina 5}
  ```
  **The demo's own "restrictions switch off at $t=6$, mid-shock, then back on at $t=7$" is a pure discretization artifact** — the converged equilibrium restricts continuously across $t=5,6,7$. Grid ladder across shock size (`max_iters=20`, never the limiting factor): at $s=0.75$, grid=5 reports **zero** restricting countries where grid=13/25 report two; at $s=0.72$, grid=5 reports 30/30/30 where the converged answer is 15/15/5.
- **Attempt to falsify.** (a) Ruled out solver noise (repeat solves bit-identical; welfare gains 0.3–1.0%, far above any noise floor). (b) Not a contrived scenario — appears in the demo's own shipped run at its own defaults. (c) Not a fixed-point-search artifact — all ladder entries converged in ≤3 sweeps independent of grid. (d) Not defensible as "a ban is coarse anyway" — README explicitly frames $\tau$ as continuous, scored via a continuous-instrument extensive margin (`tau>1.0`).
- **Result.** Survives — **the one substantive defect found in this subsystem.**
- **Recommended action.** Two-stage local refinement inside the existing coordinate loop (~5 lines, no new user parameter): coarse scan, then rescan a finer `linspace` around the coarse optimum. Measured: recovers the converged answer at ~2× runtime (vs. ~20× for a brute grid=49). Minimum viable alternative: raise default `game_grid` from 5 to 13 (one-character change, ~2.6× runtime). **Report a grid-sensitivity check alongside any Level-2 validation result** — a "who restricts" score at grid=5 is not yet a statement about the model.
- **Complexity-budget assessment.** Scientific benefit high — repairs the headline output and is a precondition for VALIDATION.md's Level-2 test being meaningful. Cost ~2× on the game loop only (~+25% on `demo.py` total). Zero new economic parameters/state. Passes on every axis.

## F4 — `tol=3.0` is inoperative: strictly smaller than grid spacing, so convergence is exactly "no coordinate moved"

- **Classification.** **G.** **Severity.** Low. **Confidence.** 95–100%.
- **Mathematical evidence.** All $\tau$ values lie on $\mathcal{G}=\{k\Delta\}$ with $\Delta\in\{30,20\}$; `tol=3<\Delta` selects exactly $\{0\}$.
- **Code evidence.** `core.py:315` (`tol=3.0`), `:387–388` (`SheafModel` never passes `tol` through).
- **Reproduction.** 85 traced runs: sweep-count `{1:2, 2:41, 3:41}`; every terminating sweep had `max|tau-last|==0.0` exactly, never a nonzero-but-small value.
- **Attempt to falsify.** Could become live and *harmful* if `game_grid>41` (spacing<3) — currently `SheafModel` doesn't expose `tol`, so a user refining the grid per F3 could silently activate this.
- **Result.** Survives as documentation/latent-robustness issue, worth flagging precisely because it interacts with the F3 fix.
- **Recommended action.** Document as an exact fixed-point test; optionally make `tol` scale with grid spacing if F3's fix is adopted.

## F5 — `max_iters=3` adequate in everything tested but has no margin and no non-convergence signal

- **Classification.** **C**, bordering H for the shipped configuration. **Severity.** Low (prototype) / medium (larger country/grain sets). **Confidence.** 95–100% tested / 80–95% margin claim.
- **Reproduction.** 85 runs (adversarial initialization at all-120, grid∈{5,7}, 21 shock combos): sweep distribution `{1:2, 2:41, 3:41}`; **48% saturated the full budget**; `nonconv=0, cycles=0`.
- **Attempt to falsify.** Actively hunted for a 4th-sweep case across corner initialization, dual-binding grains, $\sigma=0.9$ — none found.
- **Result.** Concern (silent truncation risk) survives as a robustness note; allegation that it currently truncates does not.
- **Recommended action.** Raise default to 5 (free — early break means no extra cost when convergence is faster) and/or return a `converged` flag.

## F6 — Grid equilibrium is unique in tested states: independent of initialization and player ordering

- **Classification.** **H** (tested states); 60–80% as a general property. **Confidence.** 95–100% tested.
- **Reproduction.** 11 initializations × real $t=5,7$ states → single fixed point each; 8 random exporter orderings → same. Includes the strongest available test: initializing at the opposite corner (all-120, full ban) — still collapses to the same low-restriction profile in 3 sweeps.
- **Result.** No multiplicity found; recorded as H per CLAUDE.md rather than left as unresolved doubt, with the honest caveat that this is calibration-specific and the warm start (`core.py:443`) would create hysteresis if multiplicity ever arose.

## F7 — No cycling observed in 85 traced runs with explicit cycle detection

- **Classification.** **H** (tested space); 60–80% general. **Confidence.** 95–100% tested.
- Tested grid=2 (most cycle-prone) and dual-grain simultaneous shortfalls specifically. Zero cycles.

## F8 — Stress gate verified non-binding in the shipped calibration, but the safety margin is calibration-contingent and undocumented

- **Classification.** **H** for correctness / **G** for documentation. **Severity.** Low (as shipped) / medium (calibration hazard). **Confidence.** 95–100% / 80–95%.
- **Mathematical evidence.** Gate: $\max_ip_{i,g}>\mu p^{\rm norm}_g$, $\mu=1.12$. Restriction incentive: $p_{i,g}>\bar p_{i,g}$. These coincide only if $\min_i\bar p_{i,g}\ge\mu p^{\rm norm}_g$ — **violated** in the prototype ($\mu p^{\rm norm}_{\rm wheat}=280$; Russia's $\bar p=265$, Argentina's $=268$).
- **Reproduction.** Forced the game in all 12 periods (bypassing the gate): calm periods return $\tau=0$ **exactly**, confirming README's claim empirically rather than assuming it. Boundary scan at both grid resolutions through the sub-gate window ($p/p^{\rm norm}=1.06$–$1.11$, where $\bar p<$gate threshold): fine-grid equilibrium still exactly zero throughout.
- **Attempt to falsify.** Specifically targeted the sub-gate window where a country with low $\bar p$ should in principle want to restrict while the gate is shut — checked at both coarse and fine grid (to rule out the grid itself masking a small optimal $\tau$). No case found.
- **Result.** Correctness claim survives; documentation gap remains (the safety depends on a relation between $\bar p$ and $\mu p^{\rm norm}$ that isn't stated and should be re-checked on recalibration).
- **Recommended action.** One README sentence stating the condition under which the gate is safe.

## F9 — Producer income evaluated at unshocked baseline production $Q$, not realised $Q\xi$

- **Classification.** **D** (matches README's own notation table symbol-for-symbol — not B), with a **G** component. **Severity.** Low–medium. **Confidence.** 95–100%.
- **Code evidence.** `core.py:440` (`self.production0` passed to the game), `:407` (unshocked, set once at construction), `:329` (`producer = p @ production[i,:]`).
- **Reproduction.** Re-ran with $Q$ vs. $Q\xi$ on real stressed states: **no change** at shipped grid=5; at grid=25, Russia moves one 5 $/t step (30→35 or 15→20) in two of four tested cases.
- **Attempt to falsify.** Confirmed this is *not* a README mismatch (README's own notation defines $Q$ as baseline) — reclassified from a suspected bug to a disclosed convention. Effect is smaller than F3's discretization error and biases *against* restriction (conservative direction).
- **Result.** Survives as low-severity, correctly not classified as a bug.
- **Recommended action.** Document only; do not change code ahead of the F3 fix, against which this effect should be re-measured.
- **★ Cross-reference: this is the same code path independently flagged by Agent 3 (storage) as S13 — see Phase 1 cross-agent summary. Reconciliation still open as of this checkpoint.**

## F10 — Equilibrium saturates at the strategy bound $\bar\tau=120$ in 9/20 multi-grain scenarios

- **Classification.** **D**, with an **F** component. **Severity.** Medium. **Confidence.** 95–100%.
- **Reproduction.** At 15–25% simultaneous wheat+maize shortfall, essentially every exporter pins at $\tau=120$ — result becomes a statement about $\bar\tau$, not economics. The demo's own scenarios never saturate (max $\tau=30$).
- **Attempt to falsify.** Confirmed not a grid artifact (corner is the endpoint at every resolution tested); confirmed genuinely shock-driven, not a numerical guard (welfare is decreasing in $\tau$ well before 120 in unsaturated states).
- **Recommended action.** Report $\bar\tau$ alongside any scenario and flag saturation when it occurs. Do not raise $\bar\tau$ without an empirical anchor.

## F11 — `tol` and `revenue_weight` unreachable through `SheafModel`

- **Classification.** **G.** **Severity.** Low. **Confidence.** 95–100%.
- README's own "Minimal use in code" snippet and terms-of-trade extension (`revenue_weight`) are advertised but not wired through the only orchestrator — `gov_rev` is identically 0 in every result the repo has ever produced, including `sheaf_results.csv` and all four demo figures.
- **Recommended action.** Forward both as `SheafModel.__init__` kwargs (one line) or amend README to say the game must be constructed directly.

## F12 — Welfare function matches README §4 symbol-for-symbol

- **Classification.** **H.** **Confidence.** 95–100%.
- Term-by-term comparison of `_welfare` (`core.py:324–333`) against README's $\mathcal{W}_i=CS_i+\Pi_i-\Phi_i+\zeta\Psi_i$ — all terms, signs, and the $(x)_+$ clip match exactly. One noted specification detail (not a discrepancy): $X^g_i$ is net exports per README's own definition, so a future $\zeta>0$ user taxes net rather than gross exports "correctly" per spec — flagged for whoever first activates the term.

## F13 — README misattributes the approximation to welfare non-concavity; the operative limitation is grid coarseness

- **Classification.** **G.** **Severity.** Low–medium. **Confidence.** 80–95%.
- **Mathematical evidence.** The penalty $\Phi_i$ is convex, so $-\Phi_i$ is concave — not itself a source of non-concavity, contrary to README's parenthetical.
- **Reproduction.** Russia's own-$\tau$ profile, 49 points: second-difference range $[-65.98,+0.249]$ — essentially concave/single-peaked. Ukraine's $13\times13$ two-grain surface: monotone, single-peaked, no ridge.
- **Attempt to falsify.** Actively tried to *vindicate* README by finding non-concavity (2D surfaces, dual binding penalties, $\sigma=0.9$) — none found.
- **Result.** README's *conclusion* ("approximate/discretised") is directionally right; its *stated cause* is not supported.
- **Recommended action.** Replace the causal clause: the sweep converges to an exact discretized-Nash equilibrium (verified); the approximation is the discretization of $[0,\bar\tau]$ itself — pairs naturally with the F3 fix.

## Summary

| # | Finding | Class | Severity | Confidence |
|---|---|---|---|---|
| F1 | Exact Nash equilibrium of the discretized game ($\varepsilon_i=0$, 204 runs) | H | — | 95–100% |
| F2 | Coordinate vs. joint gap measured at exactly 0 (0.12% separability residual) | H | Low | 95–100% (tested) |
| F3 | **Default 5-point grid flips the extensive margin** (headline finding) | **C** | **Med–high** | 95–100% |
| F4 | `tol=3.0` inoperative (< grid spacing) | G | Low | 95–100% |
| F5 | `max_iters=3` sufficient but 48% saturated; no convergence signal | C | Low | 95–100%/80–95% |
| F6 | Unique fixed point across 11 inits × 8 orderings | H | — | 95–100% (tested) |
| F7 | No cycling in 85 traced runs | H | — | 95–100% (tested) |
| F8 | Stress gate non-binding but calibration-contingent | H/G | Low | 95–100%/80–95% |
| F9 | Producer income uses unshocked $Q$ (README-consistent) | D/G | Low–med | 95–100% |
| F10 | Saturates at $\bar\tau=120$ in 9/20 multi-grain scenarios | D/F | Medium | 95–100% |
| F11 | `tol`/`revenue_weight` unreachable via `SheafModel` | G | Low | 95–100% |
| F12 | Welfare function matches README exactly | H | — | 95–100% |
| F13 | README's non-concavity cause unsupported; real limit is discretization | G | Low–med | 80–95% |

**Single most important result:** the equilibrium *solver* is sound — better than README claims for it. The one substantive defect is the strategy-space discretization (F3): at the shipped `game_grid=5`, the demo's own run reports zero restricting countries mid-shock where the converged equilibrium restricts throughout.
