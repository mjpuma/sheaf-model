# Gate 1 substitution red-team (2026-08-26)

**Question:** does isoelastic coupling on the locked Gate 0 spine actually
substitute, or only move prices through a side channel?

**Method:** independent probes (η algebra, step-level identity, calm twin,
frozen-wheat quantity signs, 2008 offer/use split). No σ* selection. No
game. CropParams / ρ not retuned.

Script: `scripts/redteam_gate1_substitution.py`.
Tests: `tests/test_gate1_substitution.py`.

## Findings

| ID | Claim | Result | Class | Conf. |
|---|---|---|---|---|
| RT1 | `cross_price_eta(0.6)` matches η_gg=ε_g, η_gh=σ ρ_gh \|ε_g\| with GRAINS order | Exact match. Maize←wheat 0.060 > wheat←maize 0.036. σ=0 off-diag 0. | **H** | 95–100% |
| RT2 | `fac=exp(η log(p/p0))` is the isoelastic product | Wheat ×1.5, others at p0: fac = (0.941, 1.015, 1.025). Own-price at σ=0 equals `(p/p0)**ε`. | **H** | 95–100% |
| RT3 | Coupled σ=0 recovers Gate 0 **state**, not just monthly prices | Official 2006–11: price/stock/consumption/offers/ask/free/exports max rel ~1e-16 all three grains. Ukraine 2021–23 same. Countries aligned. | **H** | 95–100% |
| RT4 | Old identity assert (monthly price, 0.5%) could miss loop drift | True as a guardrail gap. Implementation itself matched at 1e-16. Tightened to step-level 1e-9 on price, stocks, use, offers. | **G** then patched | 95–100% |
| RT5 | Calm σ=0.6 (no AMIS, no shocks, no industrial) stays at p0 | Exact. fac=1 at p=p0 for any σ, so the twin identity survives substitution. | **H** | 95–100% |
| RT6 | Wheat dear ⇒ rice/maize flex up; ethanol unchanged | Freeze wheat at 1.5 p0. σ=0: rice/maize use ×1.000, industrial identical. σ=0.6: rice use ×1.004, maize ×1.005 vs σ=0 freeze; industrial identical. Jacobi lag: t=0 still at p0. | **H** | 95–100% |
| RT7 | 2007/08 official split: substitution is demand-side, not a fake scarcity dummy | Rice 2008: use +2.9%, offers −10.7%, free 37→32 MMT, price +2.1%. Maize: use +3.9%, offers −17.7%, price +13.9%. Signs match substitutes. | **H** | 80–95% |
| RT8 | Price spillovers are large vs tiny cross elasticities | η_rice,wheat=0.036. A 50% wheat hike wants ~+1.5% rice flex before rice's own price rises. Gate 0 tightness (offers residual + free vs twin) amplifies that into a several-percent price move. Same map P1 uses for own-price. Not a coding error; do not retune κ/ω to “make substitution smaller.” | **D** | 80–95% |
| RT9 | Lean cover / warehouse use unsubstituted C_ann | Hungry-season target does not include extra substituted use over the horizon. Current-step `desired` does. Offers = avail−desired−target, so extra food still cuts exports. Understates the *future* buffer. Simplification, not an inverted sign. | **D** | 80–95% |
| RT10 | Row elasticities do not sum to 0 (not homogeneous of degree 0) | Wheat row sum −0.087 at σ=0.6. Uniform inflation still cuts demand. Constant-elasticity overlay, dual host vs annual Slutsky. Disclosed. | **D** | 95–100% |
| RT11 | numpy 2 / pandas CoW: `fill_diagonal` and Vietnam rice row were read-only | `load_trade_shares` / `_repair_vietnam_rice_e0` crashed before any coupled step. Copy-on-write, not a substitution formula bug. | **B** patched | 95–100% |
| RT12 | Duplicate `_simulate_coupled` vs `_simulate_window` | Currently bit-identical at σ=0. DRY extract would be a refactor, not a defect. The tightened identity test is the guardrail. | **H** (maintenance risk only) | 80–95% |

## What was not a bug

- Jacobi lag (demand uses last step's world prices): same clock as Gate 0 own-price.
- All countries see one world p: same as Gate 0.
- Unsubstituted `free_twin`: calm diet is baseline (fac=1 at p0). Extra substitute demand *should* look tight vs that twin.
- 2010 maize hike-ratio leftover and 2022 rice drift: classified in E5/E6; this pass did not find an inverted demand sign.

## Fixes in this pass

1. Writable copies in `load_trade_shares` and `_repair_vietnam_rice_e0`.
2. `assert_subst0_matches_gate0` checks step-level price, stock, consumption, offers at 1e-9.
3. `tests/test_gate1_substitution.py` locks RT1, RT2, RT3, RT5, RT6.

Do not pick σ*, densify the band, retune CropParams/ρ, unpause `dynamic_grains.py`, or start the export game from these findings.
