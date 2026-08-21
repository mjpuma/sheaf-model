# Phase 2 Agent 5 — Temporal Dynamics / Orchestrator

**Mandate:** Audit `SheafModel.step()` and README §5 from first principles; construct the implemented within-period timeline and information sets; independently verify Phase 1 hypotheses S4, S5, S7, S9 (treat as hypotheses, not premises); compare storage timing architectures A/B/C for S4; derive shortfall alternatives for S7.

**Scope:** `sheaf/core.py` (`SheafModel.step`/`run`, `market_responsive_storage`, `strategic_storage`, stress gate, `ExportRestrictionGame` invocation); README §3 and §5; continuity with TWIST/Agrimate before Deaton–Laroque.

**Method:** Six-step CLAUDE.md protocol per claim. Scratch reproductions under `/tmp/sheaf_audit_agent5/` (`verify_temporal.py`, `verify_followup.py`). Model source untouched.

**Status legend for Phase 1 hypotheses:** CONFIRMED / REFUTED / NARROWED / RECLASSIFIED / UNRESOLVED.

---

## 1. Exact implemented within-period timeline

Derived line-by-line from `SheafModel.step` (`core.py:416–457`). This matches README §5’s five-stage sketch; the table makes information sets explicit.

| # | Operation | Code | Information set used |
|---|---|---|---|
| 0 | Beginning stocks \(R^{\mathrm{mkt}}_{t}, R^{\mathrm{gov}}_{t}\); \(p^{\mathrm{prev}}_{t}\); `last_tau` | prior step / `__post_init__` | Strictly \(t-1\) (or calibration init) |
| 1 | Production shock \(\xi_t\); realised production \(Q\circ\xi_t\) | `:418,425` | Current **exogenous** |
| 2 | Price expectation \(p^e = p^{\mathrm{prev}}+\kappa(p^{\mathrm{norm}}-p^{\mathrm{prev}})\) | `:413–414,426–427` | Only \(p^{\mathrm{prev}}\) (\(t-1\)); **not** \(\xi_t\) or \(Q\xi_t\) even though already computed |
| 3 | Private storage \(\Delta^{\mathrm{mkt}}\) | `:428` → `:184–195` | \(p^{\mathrm{prev}}\), \(p^e\), stocks/capacity/γ/θ; **no** production/shock argument (signature) |
| 4 | Government storage \(\Delta^{\mathrm{gov}}\) | `:429` → `:198–216` | \(p^{\mathrm{prev}}\), \(D_0\), **contemporaneous** \(Q\xi-\Delta^{\mathrm{mkt}}\) |
| 5 | Effective availability \(A = Q\xi - \Delta^{\mathrm{mkt}} - \Delta^{\mathrm{gov}}\) | `:431` | Endogenous given (1)–(4) |
| 6 | Stress-gate probe: market at \(\tau=0\) | `:435–436` | \(A_t\), tariffs; unrestricted taxes |
| 7 | Stress flag: \(\exists g:\ \max_i p^{\mathrm{probe}}_{i,g} > \mu\, p^{\mathrm{norm}}_g\) | `:437` | Probe prices vs fixed \(p^{\mathrm{norm}}\) |
| 8 | Export-restriction game **or** reuse probe | `:439–448` | If stressed: \(A_t\), `production0` (baseline \(Q\)), `last_tau` warm-start; else \(\tau=0\), `res=probe` |
| 9 | Final \((p_t, D_t, f_t)\) | game `:361` or probe `:447` | Current endogenous market map |
| 10 | Stock update \(R \leftarrow \max(0, R+\Delta)\); \(p^{\mathrm{prev}}\leftarrow p_t\); optionally refresh `last_tau` | `:450–453,444/448` | End-of-period bookkeeping for \(t+1\) |

README §5 ordering (expectations → storage → stress gate → clear → update) **matches the code**. What the README does not state is that \(p^{\mathrm{ref}}\) in §3 is implemented as \(p^{\mathrm{prev}}\) (same scalar for expectations and both storage rules).

---

## 2. Dependency graph and information classification

```
                    ξ_t (exogenous, current)
                         |
                         v
   p_{t-1} -----> p^e_t -----> Δ^{mkt}_t ----+
   (lagged)                      |           |
                                 v           v
                      Δ^{gov}_t(Qξ_t - Δ^{mkt}) --> A_t --> probe (τ=0)
                                                           |
                                           +---------------+---------------+
                                           |                               |
                                     stressed?                        calm
                                           |                               |
                                           v                               v
                                    game(τ | A_t, last_τ_{t-1})      res = probe
                                           |                               |
                                           +---------------+---------------+
                                                           |
                                                           v
                                              (p_t, D_t, f_t)
                                                           |
                                                           v
                                         R_{t+1}, p^{prev}_{t+1}, last_τ_t
```

### Variable classification

| Variable | Depends on \(t-1\) | Current exogenous | Current endogenous | Future |
|---|---|---|---|---|
| \(p^e_t\) | \(p_{t-1}\), \(p^{\mathrm{norm}}\) | — | — | **No** |
| \(\Delta^{\mathrm{mkt}}_t\) | \(p_{t-1}\), stocks | — | — | **No** |
| \(\Delta^{\mathrm{gov}}_t\) | \(p_{t-1}\), stocks | \(\xi_t\) (via \(Q\xi\)) | \(\Delta^{\mathrm{mkt}}_t\) | **No** |
| \(A_t\) | via Δ | \(\xi_t\) | Δ | **No** |
| Probe / stress | via \(A\) | via \(A\) | market map | **No** |
| \(\tau_t\) | `last_tau` warm-start only | via \(A\) | game + market | **No** |
| \(p_t, D_t, f_t\) | — | via \(A\) | market / game | **No** |
| \(R_{t+1}, p^{\mathrm{prev}}_{t+1}\) | \(R_t\) | — | \(\Delta_t, p_t\) | **No** |

### Look-ahead verdict

**No accidental look-ahead.** Future shocks do not affect period-\(t\) state before they are applied (verified: identical burn-in through \(t=4\); divergent \(\xi_5\) changes \(p_5\) but leaves \(\Delta^{\mathrm{mkt}}_5\) unchanged). `last_tau` is a \(t-1\) warm start, not foresight. `p_norm` is a fixed calibration object.

**Related fact (not a look-ahead bug):** private storage ignores *current* exogenous harvest information that is already in hand at line `:425` — that is delayed *use of available information*, not peeking at the future (see S4).

---

## 3. Hypothesis S4 — Private storage reacts one period late to contemporaneous production shocks

### Verification protocol

1. **Claim (README §3):** \(\Delta^{\mathrm{mkt}}\) responds to signal \(s = p^e/(1+r) - p^{\mathrm{ref}}\); stocks build/release when discounted expected price diverges from “current” reference price. README §5 sequences storage *before* \(p_t\) is realised, so \(p^{\mathrm{ref}}=p_{t-1}\) is the only reading consistent with the stated timeline — but that implication is never written down.
2. **Implementation:** `market_responsive_storage(c, g, p_ref, p_expected, r)` — no `prod`/`shock` parameter (`core.py:184–195`). Caller sets `p_ref = c.p_prev[g]` (`:426–428`) after computing `prod = Q*ξ` and **not** passing `prod` in.
3. **Match:** Code matches a lagged-price rule. It does **not** match a contemporaneous harvest/price response of the sort TWIST (simultaneous in market clearing) and Agrimate (sales use current harvest; ODD process order Harvest → … → Sales) implement.
4. **Counterexample / reproduction (Black Sea demo shock at \(t=5\):**

| \(t\) | Russia ξ | \(\Delta^{\mathrm{mkt}}\) (actual) | \(\Delta^{\mathrm{mkt}}\) if rule used \(p_t\) as \(p^{\mathrm{ref}}\) |
|---|---|---|---|
| 5 | 0.6 | **0.000** | −1.406 |
| 6 | 0.6 | **−1.406** | −1.626 |
| 7 | 0.6 | −1.626 | −0.669 |

Russia’s wheat crop falls 40% in period 5; private storage adjustment that period is exactly **0**. The first nonzero response equals the counterfactual period-5 response evaluated at the *realised* shock-period price — i.e. a pure one-period shift. Structural proof: with identical \(p^{\mathrm{prev}}\), \(\Delta^{\mathrm{mkt}}\) is invariant to any \(\xi\) (function signature + caller).

5. **Attempt to prove the implementation correct / falsify the hypothesis:**
   - *“Lagged price is the right information set because \(p_t\) is unknown when storage is set.”* Partially true for a sequential timing convention — but it does **not** justify ignoring \(Q\xi_t\), which *is* known. Falsification of “no problem” succeeds on that narrower point.
   - *“Government storage compensates in-period.”* Russia/Ukraine hold no government wheat reserves in the shipped calibration; gov path cannot substitute. Partial falsification fails for the demo’s shocked exporters.
   - *“Annual resolution makes a one-period lag immaterial.”* VALIDATION.md’s Level-1 targets include within-crisis stock/price anomalies; a full-period displacement is first-order for those claims. Does not falsify materiality.
   - *“TWIST/Agrimate are also lagged.”* Lineage evaluation first (CLAUDE.md): both predecessors are contemporaneous in the harvest/price of the active period. Lag is a **departure from stated lineage**, not continuity.

6. **Falsification result:** Hypothesis **survives**. Sharpened statement: the defect is omission of contemporaneous harvest (and any contemporaneous price signal), not the mere use of a predetermined price in a sequential model.

### Finding S4

- **Finding:** Private storage is a pure function of \(p_{t-1}\) (and static parameters). Contemporaneous production shocks affect private storage only from \(t+1\) onward, after \(p_t\) is written into `p_prev`.
- **Classification:** **D** (economic simplification / timing choice) primary; **E** (lineage departure vs TWIST/Agrimate contemporaneous response); **G** (README never defines \(p^{\mathrm{ref}}:=p^{\mathrm{prev}}\)).
- **Severity:** **High** if the paper claims same-year private stock buffering of harvest shocks; **Medium** if stocks are explicitly adaptive/lagged.
- **Confidence:** **98%**.
- **Recommended action:** See §7 (timing architectures). Do **not** silently “reuse the stress-gate probe” without reordering — the current probe is computed *after* storage.
- **Changes expected published results:** Yes, for any scenario where private γ>0 and shocks bind within the reporting window (demo: shock-period exporter wheat price and Russia stock path).

### S4 status: **CONFIRMED** (with documentation/lineage qualifiers D/E/G)

---

## 4. Timing architectures for S4 (mandatory comparison)

Compared on the burned-in Black Sea state at first shock period \(t=5\) (Russia wheat). Play-game enabled where applicable.

| Architecture | Russia \(\Delta^{\mathrm{mkt}}\) wheat | Mean wheat \(p\) (final) | Extra QP cost / period |
|---|---|---|---|
| **A.** Existing lagged-price rule | **0.00** | ~299 | baseline |
| **B.** Shock → unrestricted probe on \(A=Q\xi\) → storage → game/final | **−3.40** | ~269 | +1 provisional QP |
| **B2.** Storage with \(p_{t-1}\) → stress probe → **revise** storage with probe prices → game/final | **−2.85** | ~275 | +0–1 QP if calm re-clear; reuses probe |
| **C.** Simultaneous / damped fixed point \((p,\Delta)\) then game | **−1.92** | ~284 | ~10–20 QP (observed ~16 iters to \(10^{-3}\)) |

### Assessment

**A — Existing lagged-price rule**
- *Economic interpretation:* Predetermined / adaptive inventory: storers commit before seeing this year’s spot equilibrium. Coherent sequential model; not “wrong” as arithmetic.
- *TWIST/Agrimate continuity:* **Poor** — both respond to current harvest/price.
- *Compute:* Cheapest.
- *Double-counting:* None.
- *Fixed-point issues:* None.
- *Crisis timing:* Buffer arrives one period late (confirmed).
- *Publication defensibility:* Defensible **only if** README/VALIDATION explicitly call it lagged adaptive storage and do not claim same-year private buffering of harvest shocks.

**B — Probe-on-production then storage**
- *Interpretation:* Storers observe the spot price that would prevail if inventories did not adjust, then adjust once.
- *Lineage:* Closer (contemporaneous).
- *Compute:* +1 QP/period.
- *Double-counting:* Avoided if provisional \(A=Q\xi\) excludes storage (as tested).
- *Bias:* **Systematically over-releases** in crises (no-storage probe price is too high → too negative \(\Delta^{\mathrm{mkt}}\); −3.40 vs FP −1.92).
- *Crisis timing:* Same-year response.
- *Defensibility:* Acceptable with explicit sequential-bias disclosure; weaker than C.

**C — Fixed-point storage/market**
- *Interpretation:* Within-period rational consistency: \(\Delta = \Phi(p)\) and \(p = P^{\mathrm{mkt}}(Q\xi-\Delta)\).
- *Lineage:* Closest in spirit to TWIST’s simultaneous stock–price clearing; heavier than Agrimate’s behavioural rules.
- *Compute:* Expensive inside an already nested QP+game loop.
- *Fixed-point:* Converged with damping in the tested state; not proved unique/global for all calibrations.
- *Defensibility:* Strongest theoretically; weak on complexity-budget unless the paper’s identification really needs it.

**B2 — One revision using the stress-gate probe (Phase 1 idea, made precise)**
- *Interpretation:* Gauss–Seidel truncation of C: one lagged pass, one pass at the unrestricted post-lagged-storage price.
- *Lineage:* Material improvement over A; still sequential.
- *Compute:* Minimal — **reuses the probe already computed every period**; when stressed the game/final already re-solves; when calm may need one re-clear if revised \(A\) differs.
- *Double-counting:* Avoided if the first pass’s \(\Delta\) is **replaced**, not added again.
- *Bias:* Between B and C (−2.85 vs −1.92/−3.40).
- *This is what “reuse the stress-gate probe price” must mean* — not reading a post-storage probe back into the *already applied* \(\Delta\) without recomputing \(A\).

### Recommendation (simplest scientifically defensible)

1. **If the manuscript will describe storage as lagged/adaptive and will difference vs a no-shock path for validation:** keep **A**, but add an explicit README sentence: \(p^{\mathrm{ref}}_{i,g}(t) := p_{i,g}(t-1)\). Lowest complexity; honest.
2. **If the manuscript claims (or VALIDATION.md requires) same-year private stock response to harvest shocks:** adopt **B2** (one probe-price revision). It is the minimal change that (a) uses information already computed, (b) moves toward TWIST/Agrimate contemporaneity, (c) avoids B’s overshoot, (d) avoids C’s iteration tax.
3. **Reject full C for now** under the complexity-budget rule (nested iters × game grid).
4. **Reject naive B** as default (over-release bias) unless disclosed and stress-tested.

**Do not accept Phase 1’s wording that the probe can be reused with “~zero extra cost” without stating the required reorder/revision of \(A\).**

---

## 5. Hypothesis S5 — Private storage has no stationary rest point at the calibration anchor

### Verification protocol

1. **Claim:** With \(p^e = p + \kappa(p^{\mathrm{norm}}-p)\) and signal \(s = p^e/(1+r) - p\), zero-signal rest point is
   \[
   p^* = \frac{\kappa}{\kappa+r}\, p^{\mathrm{norm}}.
   \]
   At defaults \(\kappa=0.5\), \(r=0.05\): \(p^*/p^{\mathrm{norm}} = 0.9091\).
2. **Implementation:** `_expectation` + `market_responsive_storage` (`:413–414,184–195`). `SheafModel` sets `p_norm` to mean of country `p0` (`:392–393`); calibration uses common `P0` for all countries; `p_prev` initialises to `p0` (`:173–174`).
3. **Match:** Algebra and code agree; `signal(p^*)=0` verified numerically to \(10^{-15}\).
4. **Reproduction:** At \(t=0\), every γ>0 country-grain has \(p_{\mathrm{ref}}=p^{\mathrm{norm}}\), signal \(= -r/(1+r)\,p^{\mathrm{norm}}\) (wheat −11.90, outside θ=8). World private wheat \(\Delta\) at period 0: **−2.733 MMT** with **no shock**. A 40-period calm run still shows late wheat private-stock drift (~−4.3 MMT over the last 10 periods) with mean wheat price ~243.7 still below \(p^{\mathrm{norm}}=250\) but **above** \(p^*=227.3\), with signal still slightly outside the deadband — consistent with “no calm rest at the calibration anchor,” and with the stronger observation that deterministic expectations do not support a stable interior stock the way stochastic competitive storage would.
5. **Attempt to falsify:**
   - *“This is correct Deaton–Laroque behaviour (release when \(p \approx E[p]\) with \(r>0\).”* Half-right on the inequality direction, but D–L positive stocks rely on price *risk*. SHEAF’s expectation is deterministic, so there is no offsetting speculative demand. Evaluating lineage first: neither TWIST nor Agrimate uses this exact discounted mean-reverting deadband rest-point construction; invoking D–L as the defence overstates what SHEAF claims to implement.
   - *“Calibration avoids the issue.”* Opposite: initialising at \(p^{\mathrm{norm}}\) places the system on the release side of \(p^*\).
6. **Falsification result:** Hypothesis **survives**. Optional narrowing: the *closed-loop* market+storage system may wander for other reasons too; the sharp, code-level claim “\(p^{\mathrm{norm}}\) is not a zero-signal point of the storage rule” is unambiguous.

### Finding S5

- **Finding:** Zero-signal price of the private rule is \(p^*=\kappa/(\kappa+r)\,p^{\mathrm{norm}} \neq p^{\mathrm{norm}}\) for \(r>0\). Shipped init sets \(p_{\mathrm{prev}}=p_0=p^{\mathrm{norm}}\), so period 0 is structurally a release period for all active private storers.
- **Classification:** **D** / **G**.
- **Severity:** **Medium** (endogenous drift contaminates levels; first-differenced or shocked-minus-baseline contrasts partially purge it).
- **Confidence:** **98%**.
- **Recommended action:** Zero-parameter recentre: choose the expectation anchor so \(p^*=\overline{p_0}\) (equivalently scale the stored `p_norm` by \((\kappa+r)/\kappa\) if the formula is kept). Document that the rule is a deterministic price-band inventory rule, not a full competitive-storage equilibrium.
- **Complexity-budget:** Excellent (one-line, no new state). Reject embedding a stochastic D–L fixed point (moves away from TWIST/Agrimate behavioural simplicity; nested cost).
- **Changes published results:** Levels of private stocks and calm-period prices; **differenced** demo-style contrasts less so.

### S5 status: **CONFIRMED**

---

## 6. Hypothesis S7 — Strategic reserve crisis test mistakes structural import dependence for crisis

### Verification protocol

1. **Claim (README §3):** Shortfall \(\Sigma = D_0 - A^{\mathrm{(pre-gov)}}\); crisis if \(p^{\mathrm{ref}}>p^{\mathrm{trig}}\) **or** \(\Sigma>0\); release in crisis, rebuild in calm.
2. **Implementation:** `shortfall = cons_baseline - availability_wo_gov` with `availability_wo_gov = prod - dm` (`:203–204,429`). No imports term.
3. **Match to README:** Symbol-for-symbol match to the written \(\Sigma\). The economic gloss “crisis / calm” does **not** match open-economy scarcity.
4. **Reproduction (baseline \(\xi=1\), \(\Delta^{\mathrm{mkt}}=0\)):**

| Country | Grain | \(D_0\) | \(Q\) | \(\Sigma\) | Structural importer? | Crisis at baseline? |
|---|---|---|---|---|---|---|
| China | wheat | 145 | 138 | +7 | yes | **yes** |
| China | rice | 212 | 210 | +2 | yes | **yes** |
| China | maize | 295 | 275 | +20 | yes | **yes** |
| Egypt | wheat | 20 | 9 | +11 | yes | **yes** |
| India | wheat/rice | … | … | negative | no | no (price permitting) |

China/Egypt government stocks over 12 calm periods: maize 100→0.078, wheat 100→16, Egypt wheat 4.5→0.0011 — **rebuild_periods = 0**. Black Sea shock (Russia/Ukraine only): China/Egypt gov paths **bit-identical** to no-shock (max |diff| = 0). Under autarky \(\Sigma\), release is often \(\min(\eta_{\mathrm{rel}} R,\Sigma)\) with large structural \(\Sigma\), so even a *domestic* production shock often fails to change the release once the stock fraction binds (verified at init and after drain).

5. **Attempt to falsify:**
   - *“Reserves are meant to cover the structural import gap every year.”* Then rebuild must be financed somehow; the calm branch is unreachable while \(R>0\), so the stock is a one-way geometric drain (\(R\leftarrow(1-\eta_{\mathrm{rel}})R\) once stock-limited), not a buffer. Contradicts README’s two-regime language.
   - *“Price trigger can restore calm.”* Price trigger only *adds* crisis conditions (`or`); it cannot cancel \(\Sigma>0\).
   - *“Agrimate does the same.”* Lineage-first: Agrimate’s strategic purchaser rule refills toward a baseline when below target (and the reverse) — opposite of permanent autarky crisis.

### What “shortfall” should mean for a structural importer

Compare alternatives at baseline and under a China maize harvest loss (mandate: derive consequences before selecting).

Define \(A^{\mathrm{pre}}=Q\xi-\Delta^{\mathrm{mkt}}\).

| Definition | Formula | Baseline importer | Baseline exporter | China maize \(\xi=0.9\) |
|---|---|---|---|---|
| **G0. Gross domestic production gap (current)** | \(D_0 - A^{\mathrm{pre}}\) | \(\Sigma=D_0-Q>0\) always | calm if \(Q\ge D_0\) | 47.5 |
| **G1. Anomaly vs baseline net-import need** | \(Q(1-\xi)+\Delta^{\mathrm{mkt}}\) | **0** | **0** | 27.5 |
| **G2. Gap after normal baseline trade** | \(D_0 - A^{\mathrm{pre}} - \max(D_0-Q,0)\) | **0** (equals G1) | \(D_0-A^{\mathrm{pre}}\) | 27.5 (=G1) |
| **G3. Price-only scarcity** | \(1\{p^{\mathrm{ref}}>p^{\mathrm{trig}}\}\) | 0 at \(p_0\) | 0 | 0 unless price leg fires |
| **G4. Hybrid (recommended quantity leg)** | crisis if price trigger **or** G2>0 | calm | harvest-below-domestic-needs | crisis |

**Consequences:**
- **G0:** Permanent crisis for all \(D_0>Q\); rebuild unreachable; gov stocks useless for shocked-minus-baseline validation (identical paths) — **rejects**.
- **G1:** Clean “harvest anomaly” instrument; ignores whether domestic disappearance matters relative to normal imports; for pure exporters equals harvest loss even when \(Q\xi\gg D_0\) (may over-trigger food-security release while exportable surplus remains).
- **G2:** For importers **identical to G1**. For exporters, crisis only when pre-gov availability falls below domestic baseline consumption — a food-security reading. At \(\xi=1,\Delta^{\mathrm{mkt}}=0\), exporters with surplus have \(\Sigma<0\).
- **G3 alone:** Drops quantity response entirely; gov reserves ignore known harvest failures until prices move (and with lagged \(p^{\mathrm{ref}}\), that is another period late). Too thin as sole trigger.
- **G4:** Keep README’s OR structure; replace quantity leg with G2.

Under G1/G2 at China maize baseline: crisis=False, rebuild \(+1.8\) MMT toward target (target \(0.4\times295=118\), stock 100) — restores two-regime behaviour.

### Finding S7

- **Finding:** Implemented \(\Sigma\) is an autarky accounting identity. Structural net importers are in perpetual “crisis,” so government reserves follow a shock-invariant geometric drain in the shipped calibration; the calm rebuild branch is unreachable while stocks remain positive.
- **Classification:** **D** / **G** (formula matches README math; README’s crisis/calm language does not match open-economy intent).
- **Severity:** **High**.
- **Confidence:** **98%**.
- **Recommended action:** Replace quantity leg with **G2** (gap after normal baseline trade), keep price trigger as OR. Equivalent to Phase 1’s anomaly formula **for importers**; better motivated for exporters. One-line change, zero new parameters. Optionally document S8 (build fall-through when `gov_stock==0` during crisis) as an adjacent bug — reproduced here: Egypt wheat with stock forced to 0 yields \(\Delta^{\mathrm{gov}}=+0.6\) while \(\Sigma=+11\).
- **Complexity-budget:** Excellent; moves toward Agrimate’s refill-when-below-baseline philosophy without importing Agrimate’s full purchaser optimisation.
- **Changes published results:** Yes — China/Egypt gov stock paths and any Level-1 stock-anomaly attribution that hoped to use government reserves.

### S7 status: **CONFIRMED** (recommended fix **NARROWED** from Phase 1’s importer-only anomaly slogan to G2, which coincides with that anomaly on importers and extends sensibly to exporters)

---

## 7. Hypothesis S9 — Storage is within-period independent of endogenous export restrictions

### Verification protocol

1. **Claim:** Storage is decided before the stress gate/game, so \(\Delta^{\mathrm{mkt}},\Delta^{\mathrm{gov}}\) do not depend on \(\tau_t\).
2. **Implementation:** Storage block `:423–431` precedes probe/game `:434–448`.
3. **Within-period test (same burned-in state, same shock, game on vs off):**  
   \(\max|\Delta^{\mathrm{mkt}}_{\mathrm{game}}-\Delta^{\mathrm{mkt}}_{\mathrm{off}}|=0\),  
   \(\max|\Delta^{\mathrm{gov}}_{\mathrm{game}}-\Delta^{\mathrm{gov}}_{\mathrm{off}}|=0\),  
   while \(\max|p_{\mathrm{game}}-p_{\mathrm{off}}|\approx 27.6\) and \(\max\tau=30\).  
   Precomputed storage from the step’s first block matches the post-step stock change to numerical noise (~1e-15).
4. **Cross-period test (full 12-period runs, game on vs off):**  
   \(\max|\Delta^{\mathrm{mkt}}|\text{ diff} \approx 1.54\) MMT, price diff ≈ 29.4 — because \(\tau_t\) changes \(p_t\) which becomes \(p^{\mathrm{prev}}_{t+1}\) and feeds next period’s storage. Phase 1’s claim that full parallel runs are bit-identical on storage is **false** as stated.
5. **Attempt to falsify within-period independence:** Stress-gate cannot leak backward; `last_tau` affects only the game’s start, not \(\Delta\). Falsification **fails** for within-period. Cross-period coupling via prices **succeeds** as a narrowing.
6. **Lineage:** Agrimate updates export policy *before* commercial sales — SHEAF gives storers less within-period policy information. That is a modeling-philosophy choice (E), not a coding bug relative to README §5 (which places storage before the game).

### Finding S9

- **Finding:** Within a period, storage is exactly independent of the export-restriction game (architectural fact, README-consistent). Across periods, the game affects storage indirectly via lagged prices. Phase 1’s “bit-identical full-run storage” reproduction overstated the cross-period case.
- **Classification:** Within-period fact **H**; modeling judgment vs Agrimate **E**; Phase 1 write-up accuracy **G** (overstatement).
- **Severity:** **Medium** for interpretation / lineage; not a silent arithmetic error.
- **Confidence:** **99%** (within-period fact), **95%** (cross-period narrowing).
- **Recommended action:** No architectural change required for correctness vs README §5. Disclose decoupling in §5. If future work wants Agrimate-like policy-before-sales, that is a larger redesign (rejects joint \((\tau,\Delta)\) optimisation under complexity budget for now). B2 timing (S4) gives storers contemporaneous *price* information without coupling to \(\tau\) within the period.
- **Changes published results:** None from disclosure alone; coupling redesign would.

### S9 status: **NARROWED** (within-period independence **CONFIRMED**; cross-period bit-identity **REFUTED**; lineage judgment remains **E**)

---

## 8. Additional findings from the orchestrator audit

### Finding T1 — README §5 sequencing matches `SheafModel.step`

- **Classification:** **H**. **Severity:** n/a. **Confidence:** **99%**.
- **Evidence:** Table in §1 vs README §5 stages (i)–(v).
- **Falsification attempt:** Look for hidden passes after `p_t` that revise \(\Delta\) — none.
- **Action:** None.

### Finding T2 — \(p^{\mathrm{ref}}\) undefined in README §3 (equals \(p^{\mathrm{prev}}\) in code)

- **Classification:** **G**. **Severity:** Medium. **Confidence:** **97%**.
- **Evidence:** §3 uses \(p^{\mathrm{ref}}\); §5 updates \(p^{\mathrm{prev}}\leftarrow p_t\); code uses `p_prev` for both expectation and storage reference (`:426–429`).
- **Action:** One defining sentence in README §3/§5.
- **Related:** Phase 1 S3 — **CONFIRMED** independently.

### Finding T3 — Stress-gate indexation is per-grain `any`, not a single global max

- **Classification:** **G** (minor). **Confidence:** **90%**.
- **Evidence:** README writes \(\max_{i,g} p_{i,g} > \mu p^{\mathrm{norm}}_g\) (ambiguous RHS index); code `:437` is \(\exists g:\ \max_i p_{i,g} > \mu p^{\mathrm{norm}}_g\).
- **Action:** Align notation; behaviour is sensible.

### Finding T4 — Government storage *code* sees current shocks; autarky \(\Sigma\) often makes releases shock-invariant

- **Classification:** **H** on the code path; consequence of S7. **Confidence:** **95%**.
- **Evidence:** `strategic_storage(..., prod - dm)`; Black Sea (no China ξ) gov paths identical; even China ξ shocks often leave \(\Delta^{\mathrm{gov}}\) unchanged when \(\min(\eta R,\Sigma)\) is stock-fraction limited.
- **Action:** Fold into S7 fix narrative; do not claim “gov ignores shocks” as a separate bug.

### Finding T5 — Adjacent S8 fall-through reproduced (not primary mandate)

- **Classification:** **B** when reachable. **Severity:** Low in shipped calibration (stock never hits exact 0 under \(\eta_{\mathrm{rel}}=0.5\)); medium for replaced calibrations.
- **Confidence:** **95%**.
- **Evidence:** Egypt wheat, `gov_stock=0`, \(\Sigma=11\) → \(\Delta^{\mathrm{gov}}=+0.6\) (builds during shortfall).
- **Action:** Guard rebuild with `not crisis` (one line). Status vs Phase 1: **CONFIRMED** as latent.

---

## 9. Hypothesis status summary (Phase 1 → Agent 5)

| ID | Phase 1 claim (short) | Agent 5 status | Notes |
|---|---|---|---|
| **S4** | Private storage one period late to shocks | **CONFIRMED** | Recommend B2 if same-year response required; else document A |
| **S5** | No rest point at calibration anchor | **CONFIRMED** | Recentre anchor so \(p^*=\bar p_0\) |
| **S7** | Crisis test = autarky for importers | **CONFIRMED**; fix **NARROWED** to G2 | G2≡Phase1 anomaly on importers |
| **S9** | Storage independent of τ | **NARROWED** | Within-period yes; full-run bit-identity no |
| S3 (related) | \(p^{\mathrm{ref}}\) undocumented | **CONFIRMED** | T2 |
| S8 (adjacent) | Build while crisis at stock=0 | **CONFIRMED** (latent) | T5 |
| S14 (related) | No look-ahead | **CONFIRMED** | §2 |

---

## 10. Complexity-budget rollup (recommended changes only)

| Change | Benefit | Cost | New params/state | Lineage | Publish impact |
|---|---|---|---|---|---|
| Document \(p^{\mathrm{ref}}=p_{t-1}\) | Clarity | Doc only | 0 | Honest about A | Claims hygiene |
| S5 recentre anchor | Stops structural release drift | One line | 0 | Neutral | Calm stock levels |
| S7 → G2 shortfall | Restores crisis/calm; usable gov stocks | One line | 0 | Toward Agrimate | **High** |
| S8 `not crisis` guard | Correct branch partition | One line | 0 | n/a | Only if stock hits 0 |
| S4 → B2 if needed | Same-year private buffer | Reuse probe; optional calm re-clear | 0 | Toward TWIST/Agrimate | Shock-year prices/stocks |
| Full C fixed point | Consistency | Many QPs/period | 0 | TWIST-like | Reject for now |
| Joint \((\tau,\Delta)\) | Agrimate policy-before-sales | Multiplies game cost | 0 | Agrimate | Reject for now |

---

## 11. Does this change expected published results?

- **Demo Black Sea figures (levels):** Yes if S4→B2 or S5 recentre applied; government importer stocks already inert under S7 for that shock.
- **Shocked-minus-baseline contrasts:** S5 drift largely cancels; **S7 drain does not produce a differential government signal** (identical shocked/unshocked gov paths for China/Egypt under Black Sea forcing) — government reserves currently cannot contribute to Level-1 stock-anomaly targets until G2 (or similar) is adopted.
- **Restriction timing/identity:** Indirect only (via prices→next-period storage); within-period τ⊥Δ (S9).

---

## 12. Reproducibility

```bash
/tmp/sheaf_audit_agent5/venv/bin/python /tmp/sheaf_audit_agent5/verify_temporal.py
/tmp/sheaf_audit_agent5/venv/bin/python /tmp/sheaf_audit_agent5/verify_followup.py
# outputs: /tmp/sheaf_audit_agent5/s4_lag_table.csv, s5_*.csv, s7_*.csv, agent5_results.json
```

No modifications under `sheaf/`, `demo.py`, or `scripts/`.

---

AGENT 5 COMPLETE
