# SHEAF Final Adjudication

**Date:** 2026-08-22  
**Role:** Lead reviewer (CLAUDE.md Final Adjudication Rule)  
**Inputs:** Phase 1 reports, Phase 2 reports (Agents 4–7), `phase1_cross_agent_summary.md`, `phase2_cross_agent_summary.md`, fresh falsification runs in this session.  
**Source status before this pass:** unmodified. Patches listed as **IMPLEMENT NOW** are authorized by this document and applied in the same session.

This is not a new specialist audit. It resolves what is accepted into the final findings set, what is reclassified, and what may change in code/docs.

---

## 1. Disagreements

No factual disagreements among agents require resolution. The only lingering tension is **F9 / S13** (producer income at unshocked `production0`): same fact, different confidence/completeness. **Resolved below** as README-consistent fixed policy weight (**D/G**), not a coding bug.

---

## 2. Three strongest criticisms — active falsification

Per CLAUDE.md, the three strongest criticisms were selected by (multi-agent confirmation × scientific severity × load-bearing for publication claims). Each was actively attacked before acceptance.

### Criticism A — Solver acceptance → opaque `TypeError` (F3 / S10 / SE5)

| Step | Outcome |
|---|---|
| Best defense | “Shipped demo always gets CLARABEL `optimal`; failure path is rare academic pedantry.” |
| Falsification attempt (2026-08-22) | Indefinite \(M\) (`subst_scale=0.63` counterexample) and global \(\sum A<0\) both raise `TypeError: '>=' not supported between NoneType and float` at `core.py:289`. Accepts on `D.value is not None` only; ignores `prob.status`. |
| Survives? | **YES.** |
| Final class | **B/C** |
| Confidence | **99%** |
| Verdict | **ACCEPTED.** |

### Criticism B — Government crisis test is autarky (S7)

| Step | Outcome |
|---|---|
| Best defense | “Reserves are meant to cover the structural import gap every year; permanent crisis is intended food-security policy.” |
| Falsification attempt | China/Egypt wheat: at \(\xi=1\), autarky \(\Sigma>0\) ⇒ crisis forever; G2 shortfall \(=0\) at baseline. Calm rebuild branch unreachable while \(R>0\). Contradicts README’s two-regime crisis/calm language and Agrimate-like refill-when-below-target lineage. Russia at \(\xi=0.6\): autarky still calm (\(\Sigma=-9\)) while G2\(=36\) correctly signals domestic scarcity pressure. S8: Egypt `gov_stock=0` + crisis ⇒ \(\Delta=+0.6\) build during shortfall. |
| Survives? | **YES** (defense fails as a reading of README’s own calm/rebuild branch). |
| Final class | **D/G** (formula matches written \(\Sigma\); economic gloss does not) with adjacent **B** (S8) |
| Confidence | **98%** |
| Verdict | **ACCEPTED.** Fix narrowed to **G2** (Agent 5): \(\Sigma = D_0 - A^{\mathrm{pre}} - \max(D_0-Q,0)\), keep price OR. |

### Criticism C — PD “guarantee” from diagonal-dominance rescale is false (F1)

| Step | Outcome |
|---|---|
| Best defense | “Shipped 17-country calibration is PD; claim is only about the prototype.” |
| Falsification attempt | Shipped: all PD (worst eigmin Argentina \(\approx 4.8\times10^{-4}\)). But docstring/`build_demand_system` claims rescale ⇒ PD. Counterexample at `subst_scale=0.63` (model units): eigmin \(\approx -0.0037\). Geometric-mean symmetrize restores PD (eigmin \(\approx +0.0285\)). Defense shows *calibration luck*, not *guarantee*. |
| Survives? | **YES** as mathematical claim about the construction. |
| Final class | **A** (guarantee false) / **G** (doc overclaim); shipped numbers currently safe |
| Confidence | **99%** |
| Verdict | **ACCEPTED.** |

**Not in the top-three falsification set but adjudicated:** S4 (confirmed; **document**, do not silently adopt B2), S5 (confirmed; authorize recentre), P6-F1/P7-F1 (confirmed; docs), game-grid F3 (accepted as **C**; defer default change), F9/S13 (no code change).

---

## 3. Final findings register (accepted)

| ID | Verdict | Class | Conf. | Action |
|---|---|---|---|---|
| F3/S10/SE5 | ACCEPTED | B/C | 99% | **IMPLEMENT** status-aware solver + named error |
| F1 | ACCEPTED | A/G | 99% | **IMPLEMENT** geometric-mean symmetrize + `b_g≤0` guard |
| S7→G2 | ACCEPTED | D/G | 98% | **IMPLEMENT** G2 quantity leg |
| S8 | ACCEPTED | B | 95% | **IMPLEMENT** `not crisis` rebuild guard |
| S5 | ACCEPTED | D/G | 98% | **IMPLEMENT** recentre `p_norm` so rest point = mean \(p_0\) |
| S4 | ACCEPTED | D/E/G | 98% | **DOCUMENT** lag; **DO NOT** implement B2 in this patch set |
| S9 | NARROWED | E/H | 95% | Document within-period independence; no architecture change |
| F14 | ACCEPTED | D/G | 98% | **DOCUMENT** ~15% glut headroom / no free disposal |
| F9/S13 | ACCEPTED as intentional | D/G | 95% | **DOCUMENT** baseline \(Q\) as policy weight; no code change |
| P6-F1 / P7-F1 | ACCEPTED | F/G | 95–100% | **DOCUMENT** runnable path vs intended USDA/FAOSTAT pipeline; Level 2 = calibration |
| P7-F2–F4 | ACCEPTED | F | 90–100% | **DEFER** pooling / held-out design (research design, not a one-liner) |
| P6 Kazakhstan | ACCEPTED | F | 95% | **DEFER** node-set expansion |
| Game grid (P1 Agent2 F3) | ACCEPTED | C | 95% | **DOCUMENT** coarse grid; **DEFER** default 5→13 (rebaseline demo first) |
| F4 NaN at \(b_g=0\) | ACCEPTED | B | 99% | **IMPLEMENT** with F1 guard |
| λ=p at D=0 | ACCEPTED | G | 95% | **DOCUMENT** interior claim |
| LOWESS / RoW / Egypt shares / QP§2 / Nash-on-grid / material balance / no look-ahead | ACCEPTED H | H | ≥95% | No change |

---

## 4. Authorized change set

### IMPLEMENT NOW (this session)

1. **Solver protocol (SE5)** — accept only `optimal` (prefer next solver on `optimal_inaccurate`); raise `SpatialEquilibriumError` with statuses; optional \(\sum A\ge 0\) precondition; no bare silent fallthrough to TypeError.
2. **Demand PD (F1+F4)** — `S = sqrt(S*S.T)` after row rescale; raise on non-positive own slopes.
3. **Government shortfall G2 (S7)** — quantity leg uses gap after normal baseline trade; pass baseline \(Q\).
4. **S8 guard** — rebuild only if `not crisis`.
5. **S5 recentre** — default expectation target so rest point = mean \(p_0\) (via `_expectation`; stress-gate `p_norm` unchanged).
6. **Docs** — README §3/§5/§7 + Caveats; VALIDATION.md Level 2 wording; note game-grid coarseness and negative-price headroom.

### AUTHORIZED BUT DEFERRED (need design/data session)

- Raise default `game_grid` or two-stage refinement (rebaseline `demo.py` figures).
- Storage timing B2 (probe-price) — only if paper claims same-year private buffering.
- Add Kazakhstan node; wire USDA PSD / AMIS; pool `fs_weight`/`p_target`.
- Forward `tol`/`revenue_weight` through `SheafModel`.
- Joint interaction suite beyond smoke test (recommended follow-up).

### REJECTED / NOT AUTHORIZED

- Free disposal / \(p\ge 0\) constraints in the QP (poor complexity budget for crisis shortfall model).
- Full fixed-point storage–market solve (architecture C).
- Joint \((\tau,\Delta)\) within period.
- Treating F9 as a bug requiring shocked \(Q\) in welfare without author redesign of the objective.

---

## 5. Complexity-budget summary (implemented set)

| Patch | Benefit | Cost | New params | Lineage | Demo impact |
|---|---|---|---|---|---|
| Solver status | Diagnosability | ~15 lines | 0 | n/a | None on successful solves |
| Geom. mean PD | Makes stated guarantee true | 1 line | 0 | n/a | Tiny cross-price change if any; shipped already PD |
| G2 shortfall | Restores crisis/calm; gov stocks usable | ~3 lines | 0 | Toward Agrimate | **Yes** — importer gov paths |
| S8 guard | Correct branch partition | 1 line | 0 | n/a | Only if stock hits 0 |
| S5 recentre | Removes structural release drift | 1 line in `_expectation` (stress-gate `p_norm` unchanged) | 0 | Neutral | Calm private stocks |
| Docs | Honest claims | prose | 0 | n/a | None |

Interaction smoke test required after patches (Black Sea demo import path).

---

## 6. Publication posture after this adjudication

SHEAF’s **architecture** (multi-commodity SPE + restriction game + storage) remains sound on the audited core. The prototype is **not** yet an executed Level-1/2 crisis validation. After IMPLEMENT NOW patches, the code’s failure modes and government-buffer logic better match the README’s own economic language; empirical claims must still wait on per-country PSD, AMIS, prices, and an identification redesign.

- **Final publication verdict:** fit for continued scientific development and honest prototype demonstration; **not** fit to claim hindcast validation or who-restricts prediction until deferred data/identification work lands.
- **IMPLEMENT NOW patches:** applied 2026-08-22 (`sheaf/core.py`, `sheaf/__init__.py`, `README.md`, `VALIDATION.md`). Smoke-tested (PD at former cliff; named infeasibility error; China/Egypt gov stocks rebuild; 3-period step OK).

---

## 7. Status

- Final adjudication: **COMPLETE**
- IMPLEMENT NOW patches: **APPLIED**
- Deferred items: remain open in `SHEAF_AUDIT_STATE.md`
