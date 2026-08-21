# AGENT 1 (Phase 1) — Mathematical Foundations of the Demand System and Spatial Equilibrium

**Scope:** `build_demand_system()`, positive definiteness of $M$, symmetry, diagonal dominance, rescale/symmetrize ordering, integrability, the consumer-benefit potential $W_i$, the Slutsky claim, concavity of the market QP, existence/uniqueness, cross-price construction, dimensional consistency, and the $\sigma=0$ limit (README §6).

**Method:** all numerical work ran in `/tmp/sheaf_audit_agent1/` against the *unmodified* repository via `sys.path.insert`. No file inside the repo was created, edited, or deleted.

## Preliminary: an exact closed form for what `build_demand_system` computes

Let $b_g = -\varepsilon_g D_{0,g}/p_{0,g}$, $u_g=\sqrt{b_g}$, and $A = \sigma\rho$ (symmetric, non-negative, zero diagonal). Then `core.py:105–109` builds $S_{gh}=A_{gh}u_gu_h$, whose row sums are $\sum_h S_{gh} = u_g (Au)_g$. The rescale at `core.py:111–114` multiplies row $g$ by

$$c_g = \min\Big(1,\ \frac{0.95\,b_g}{\sum_h S_{gh}}\Big) = \min\Big(1,\ \frac{0.95\,u_g}{(Au)_g}\Big)\in(0,1].$$

The rows do not interact, so loop order is irrelevant. Line 115 then averages, giving $S''_{gh}=\tfrac12(c_g+c_h)A_{gh}u_gu_h$ and $M = \operatorname{diag}(b) - S''$. Congruence by $\operatorname{diag}(u)^{-1}$ gives

$$N = \operatorname{diag}(u)^{-1} M \operatorname{diag}(u)^{-1} = I - \hat S,\qquad \hat S_{gh}=\tfrac12(c_g+c_h)A_{gh},$$

so **$M \succ 0 \iff \lambda_{\max}(\hat S) < 1$.** $\sigma$ and $\rho$ enter only through $A=\sigma\rho$.

**Verification** (4000 random draws, $G\in[2,6]$): max deviation between this closed form and the real `build_demand_system`'s $M$ was 2.8e-16.

## F1 — The claimed positive-definiteness guarantee is false: rescaling rows before symmetrizing destroys diagonal dominance, and $M$ can be indefinite

- **Finding.** `core.py:96–99` and README:105 assert per-row rescaling "guarantees $M$ positive-definite." Because the rescale (line 114) is applied *before* symmetrization (line 115), the delivered $M$ is generally not diagonally dominant, and for a wide, reachable region of the documented parameter domain it is **not positive definite**. Nothing caps $\rho$ or $\sigma$.
- **Classification.** **A** (mathematical error). Not B — the code faithfully implements the flawed prose.
- **Severity.** **High.** PD is load-bearing for existence of $W_i$, strict concavity of the QP, uniqueness of the equilibrium, and validity of $CS_i$. Shipped 3-grain config is safe with a 3.3× margin; default `subst_scale=0.6` is already past the failure threshold for $G\ge4$ — the exact extension README invites.
- **Confidence.** **99%** — proven and reproduced against the unmodified function.
- **Mathematical evidence.** The rescale guarantees $\rho(DA)\le0.95$ (Perron–Frobenius). Averaging to symmetrize gives $\hat S=\tfrac12(DA+AD)$, and $\rho(\hat S)$ is **not** bounded by $\rho(DA)$. For a hard-capped row $g$ ($c_g\ll1$) whose neighbour $h$ was untouched ($c_h=1$), $\hat S_{gh}\approx\tfrac12A_{gh}$ — the cap is under-applied by $(c_g+1)/(2c_g)\gg1$.
- **Code evidence.** `sheaf/core.py:110–114` (rescale), `:115` (`S = 0.5*(S+S.T)`, applied *after*), `:116–117` (`M`, `Minv = np.linalg.inv(M)` — no PD check anywhere); `core.py:97–99`, README:105 (the false guarantee).
- **Reproduction/counterexample.**

  **Counterexample 1 ($G=3$):** `D0=[100,25,25]`, `p0=[100,100,100]`, `own_elast=[-1,-1,-1]`, $\rho=0.9$ off-diag, `subst_scale=1.5`:
  ```
  M = [[ 1.      -0.31667 -0.31667]
       [-0.31667  0.25    -0.07917]
       [-0.31667 -0.07917  0.25   ]]
  eig(M) = [-0.02486, 0.32917, 1.19569]   NOT POSITIVE DEFINITE
  DemandSystem.surplus(D0) = -103037.38   <- negative "consumer surplus"
  ```

  **Counterexample 2 (model's own units):** `p0=[250,400,200]`, `own_elast=[-0.25,-0.20,-0.30]`, `D0=[1000.0,519.0,666.7]`, $\rho=0.999$ off-diag, `subst_scale=0.63`:
  ```
  eig(M) = [-0.00368, 0.63383, 1.62937]    NOT POSITIVE DEFINITE
  ```

  **Counterexample 3 ($G=5$ at the default `subst_scale=0.6`):**
  ```
  eig(M) = [-0.0031, 0.1391, 1.2044, 1.2448, 1.2909]    NOT POSITIVE DEFINITE
  ```

  **Threshold map** — smallest `subst_scale` producing a non-PD $M$:

  | $G$ | $\rho\le0.999$ | $\rho\le0.60$ | $\rho\le0.40$ (shipped max) |
  |---|---|---|---|
  | 2 | 1.314 | — | — |
  | 3 | **0.620** | 1.032 | 1.548 |
  | 4 | **0.403** | 0.667 | 1.002 |
  | 5 | **0.317** | **0.506** | 0.754 |
  | 6 | **0.271** | **0.429** | 0.647 |

  Bold = at or below the default 0.6. Sharp $G=3$ boundary, worst-case $\lambda_{\min}$:
  ```
  subst_scale=0.58 -> +0.03753 PD
  subst_scale=0.60 -> +0.02155 PD    <- shipped default, 3% below the cliff
  subst_scale=0.61 -> +0.01131 PD
  subst_scale=0.62 -> -0.00050 NOT PD
  ```
  Over 400,000 random draws ($G\in[2,8]$), worst $\lambda_{\max}(\hat S)$ reached **13.69**.

- **Attempt to falsify.** (1) Proved three sufficient cases: **P1** (no row rescaled) ⟹ $M\succ0$ (confirmed, worst $\lambda_{\max}=0.9371$); **P2** (unconditional): $\sigma\,\lambda_{\max}(\rho)<1 \Rightarrow M\succ0$ for every $b$; **P3** (uniform rescale) ⟹ $M\succ0$. Failure requires heterogeneous $c$ across rows — the normal case for unequal own-slopes. (2) The shipped model is safe: $\lambda_{\max}(\text{RHO})=0.6075$, true threshold $\sigma_{\rm crit}\approx1.97$ vs. default 0.6 — a 3.3× margin; all 17 countries give $\lambda_{\min}(M)\ge1.45\times10^{-4}$. This is an accident of small `RHO` entries, not of the rescale, and evaporates at $G\ge4$. (3) Docstring claims a universal guarantee over both parameters — confirmed, no bound exists in code. (4) Closed form validated to 2.8e-16. (5) No downstream PD check found by grep.
- **Result of falsification.** **Survives.** Guarantee holds exactly under P1/P2/P3; shipped config safe with margin; failure region reachable at default $\sigma$ for $G\ge4$ and within 3% of default for $G=3$.
- **Recommended action.** One-line fix with complete proof: replace `S = 0.5 * (S + S.T)` with `S = np.sqrt(S * S.T)` (geometric mean). Then $\hat S = D^{1/2}AD^{1/2}$ is *similar* to $DA$, so $\rho(\hat S)=\rho(DA)\le0.95$ **unconditionally**, for every $\sigma,\rho,G,b>0$. Empirically confirmed: worst $\lambda_{\max}(\hat S)$ = exactly **0.9500** across 400,000 draws, vs. 13.69 as coded. Weakly more conservative (geometric mean ≤ arithmetic mean) — never adds substitution the current code lacks. Simply reordering (symmetrize-then-rescale) is **not** a fix — leaves $M$ asymmetric (confirmed, up to 2.2e-3 on shipped calibration).
- **Complexity-budget assessment.** Scientific benefit high (proves a currently-false theorem, covers the advertised extension path). Computational cost nil. Calibration burden none. Interpretability neutral-to-better. Added parameters/state: zero. Runtime unmeasurable. Lineage: neutral (both predecessors are single-commodity, so $M$ is scalar there). Publication benefit material.

## F2 — Delivered $M$ is not diagonally dominant in the repository's own shipped calibration (8 of 17 countries)

- **Classification.** **G**. **Severity.** Low–medium. **Confidence.** 99%.
- **Reproduction.** `build_countries()`: 8/51 rows across 8/17 countries fail strict dominance (Argentina, Australia, Canada, EU, Mexico, Russia, USA, Ukraine); rescale branch fires in 10/17 countries; yet all 17 have $\lambda_{\min}(M)\ge1.4539\times10^{-4}>0$ — PD by margin, not by the stated mechanism.
- **Attempt to falsify.** Checked the dominance test isn't a sign-convention artifact — it isn't ($M_{gg}=b_g$ exact, all off-diagonals $\le0$).
- **Result.** Survives.
- **Recommended action.** Subsumed by F1's fix (geometric mean makes the stated mechanism true).
- **Complexity budget.** N/A — prose only.

## F3 — A non-PD $M$ produces an opaque `TypeError`, because the DCP error is swallowed by a bare `except Exception`

- **Classification.** **C**, with a **B** component. **Severity.** Medium. **Confidence.** 98%.
- **Mathematical evidence.** $-\tfrac12D^\top M^{-1}D$ is concave iff $M\succeq0$; cvxpy's DCP analysis raises `DCPError` otherwise.
- **Code evidence.** `core.py:265` (`cp.quad_form`), `:281–287` (`except Exception: continue`), `:289` (`np.clip(D.value,...)` on `None`).
- **Reproduction.**
  ```
  GOOD (PD): solve() returned, prices = [[90,90,90],[110,110,110]]
  BAD (indefinite): solve() RAISED TypeError: '>=' not supported between NoneType and float
  direct cvxpy probe: is_concave=False, is_dcp=False, DCPError(...)
  ```
- **Attempt to falsify.** Tested whether cvxpy might silently accept a slightly-indefinite matrix (worse than crashing) — it rejects down to $\lambda_{\min}=-10^{-9}$, only accepting at $\le-10^{-12}$ (floating-point noise). So the "silent wrong answer" window is negligible; crash characterization stands. Also confirmed an *infeasible* instance (negative global availability) hits the identical `TypeError` at the same line.
- **Result.** Survives, severity downgraded from suspected silent corruption to loud-but-opaque failure.
- **Recommended action.** (1) In `build_demand_system`, raise/warn if $\lambda_{\min}(M)\le0$. (2) In `SpatialEquilibrium.solve`, raise a named error if the loop exits with `D.value is None`. Do not restructure the fallback logic itself — outside this subsystem's remit.
- **Complexity budget.** Negligible cost, zero new parameters/state, improved diagnosability.
- **★ Cross-referenced by Agent 3's S10 (storage report) — same crash site, different trigger (global infeasibility vs. indefinite M). Independently re-audited in Phase 2 by Agent 4 (spatial equilibrium) — see Phase 2 report / SHEAF_AUDIT_STATE.md for status.**

## F4 — $b_g=0$ silently returns a NaN-poisoned `DemandSystem`

- **Classification.** **B**. **Severity.** Medium (latent — not hit by shipped calibration; reachable via README's advertised real-data replacement path). **Confidence.** 99%.
- **Code evidence.** `core.py:112–114` — `if off >= 0.95 * b[g]:` fires as `0>=0` when $b_g=0$, causing `0/0`.
- **Reproduction.**
  ```
  D0=[120, 0, 85] -> M = [[0.12, nan, -0.0297],[nan, nan, nan],[-0.0297, nan, 0.1275]]
  downstream QP: ValueError("Quadratic form matrices must be symmetric/Hermitian.")
  ```
  Occurs even at `subst_scale=0.0`.
- **Attempt to falsify.** README/docstring state no positivity precondition; README explicitly allows $D_i\ge0$. Confirmed all 17 shipped `cons` tuples are strictly positive (not hit today).
- **Result.** Survives.
- **Recommended action.** `if off > 0 and off >= 0.95*b[g]:` plus an explicit precondition check naming the offending grain. Two lines.
- **Complexity budget.** Zero cost; clearly justified as a prerequisite for the real-data path README advertises.

## F5–F13 — Positive (H) findings, and two further documentation issues

| # | Finding | Class | Conf. |
|---|---|---|---|
| F5 | Symmetry of $M$ — exact (bitwise), including under adversarial asymmetric `rho` input (silently averaged, not rejected) | H | 99% |
| F6 | Integrability; $\nabla W_i = M^{-1}(a-D) = p$ — confirmed via central-difference gradient check (max diff 2.75e-05) | H | 99% |
| F7 | $CS_i = W_i - p_i^\top D_i = \tfrac12D^\top M^{-1}D$, and its one-grain triangle limit — exact identity, confirmed | H | 99% |
| F8 | "Slutsky" label is loose (true Slutsky matrices are singular/NSD; $M$ here is a quasilinear demand slope matrix, PD) — the *integrability* framing is correct, the *Slutsky* gloss overstates without the quasilinearity caveat | G/D | 90% |
| F9 | Intercept calibration $a=D_0+Mp_0 \Rightarrow D(p_0)=D_0$ exactly; $a>0$ in all 17 shipped countries (min 0.3035) — but this is a thin margin, and a negative $a_g$ (unreachable today) would render "choke consumption" meaningless | H | 99% |
| F10 | Own-price elasticities recovered exactly (max error 0.0); cross-price signs correct; but delivered cross-price magnitude is $\tfrac12(c_g+c_h)\sigma\rho\sqrt{b_gb_h}$, silently attenuated vs. README's stated $\sigma\rho\sqrt{b_gb_h}$ (down to 40% in some countries) | H/G | 97% |
| F11 | Dimensional consistency (MMT, $/t) — full symbolic unit trace, all terms commensurate | H | 95% |
| F12 | Strict concavity in $D$ (not jointly in $(D,f)$ — $f$ is linear, so flows may be non-unique on ties, exactly as README states); uniqueness of $(D,p)$; $\lambda^g_i=p^g_i$ confirmed via independent dual extraction (max diff 6.97e-05) | H | 97% |
| F13 | $\sigma=0$ limit: $M=\operatorname{diag}(b)$ exactly, QP and welfare separate per grain (confirmed to $10^{-5}$ relative residual); **but** the stress gate (`core.py:437`) is a single joint trigger across all grains, so a wheat crisis can switch the game on for rice/maize too — a real coupling surviving $\sigma=0$, though it had zero observed consequence in the tested scenario (calm best responses are $\tau=0$ regardless) | H/G | 96% |

## F14 — Linear demand has only ~15% global supply headroom before prices go negative

- **Classification.** **D**, with a **G** component. **Severity.** Low–medium. **Confidence.** 97%.
- **Mathematical evidence.** Headroom $=\sum_ia_{i,g}/\sum_iD_{0,i,g}$: 1.154 (wheat), 1.146 (rice), 1.226 (maize). No disposal variable, no $p\ge0$ constraint.
- **Reproduction.**
  ```
  x1.0: min price = [227.5, 384.2, 177.6]  negative: False
  x1.1: min price = [ 72.8, 123.9,  80.5]  negative: False
  x1.2: min price = [-79.2,-136.1, -16.6]  negative: True
  ```
- **Attempt to falsify.** Not reached by the demo (only negative shocks applied); storage builds push further away from the ceiling. Judged an acceptable domain restriction for a crisis-focused model, with the documentation gap as the real issue. Rejected free-disposal as a fix (adds variables to every QP solve, multiplied through the game's grid search; wrong economics for a food-security model).
- **Recommended action.** Document the ~15% ceiling in README's Caveats. Do not add free disposal.
- **Complexity budget.** Prose fix: zero cost. Free disposal: fails the budget on cost, interpretability, and runtime (multiplied by the game's repeated QP solves) — not recommended.
- **★ Cross-referenced by Agent 3's S10 falsification path (negative prices encountered as a side effect while stress-testing storage overdraw) — independently re-audited in Phase 2 by Agent 4.**

## Summary

| # | Finding | Class | Severity | Conf. |
|---|---|---|---|---|
| F1 | PD guarantee false — rescale-before-symmetrize; indefinite for $G\ge4$ at default $\sigma$, $\sigma_{\rm crit}=0.620$ at $G=3$ | **A** | High | 99% |
| F2 | Delivered $M$ not diagonally dominant in 8/17 shipped countries | **G** | Low–med | 99% |
| F3 | Indefinite $M$ → `DCPError` swallowed → opaque `TypeError` | **C**/B | Medium | 98% |
| F4 | $b_g=0$ silently returns NaN | **B** | Medium | 99% |
| F5 | Symmetry — exact | H | — | 99% |
| F6 | Integrability / gradient — correct | H | — | 99% |
| F7 | Consumer surplus formula — correct | H | — | 99% |
| F8 | "Slutsky" label loose | G/D | Low | 90% |
| F9 | Intercept calibration — correct, thin positive margin | H | — | 99% |
| F10 | Own-price exact; cross-price attenuation undocumented | H/G | Low | 97% |
| F11 | Dimensional consistency — correct | H | — | 95% |
| F12 | Concavity/uniqueness/multiplier=price — correct | H | — | 97% |
| F13 | $\sigma=0$ decomposition holds; stress gate a joint scheduler | H/G | — | 96% |
| F14 | ~15% headroom before negative prices; undocumented | D/G | Low–med | 97% |

**Single most important result:** the ordering flagged in CLAUDE.md (rescale before symmetrize) is a genuine A-class mathematical error, proven and counterexampled against the live code, with a one-line, zero-cost, fully-proved fix (`np.sqrt(S*S.T)` in place of `0.5*(S+S.T)`).
