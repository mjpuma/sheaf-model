# R2 — Gate 0 demand side vs Agrimate's consumer and purchaser problems

Red-team task R2. Branch `cursor/sheaf-first-principles-deck-a923`.
Read-only with respect to `sheaf/*.py` and `scripts/*.py`: every prototype is
produced by recompiling `sheaf/dynamic_crop.py` in memory with a textual
substitution (the technique in `scripts/scratch/a1_equation_audit.py`).

Primary source: `agrimate/Kuhla_2025_Agrimate.txt` §3.2.2–3.2.3 and
`agrimate/Kuhla_2025_AgrimateSupplement.txt` §D.7.2.3, §D.7.3, Tables D.8/D.9.
Host under audit: `sheaf/dynamic_crop.py`, `_simulate_window` (L540–705).

## 0. Harness validation

`scripts/scratch/r2_01_baseline_and_noop.py` reproduces the published Gate 0
scores exactly, using `_corr` and `_hike` imported from
`scripts/score_subannual_crop.py` on the official `full` leg
(`use_amis=True, use_shocks=True, use_demand=False`):

| crop | corr | 2007/08 | 2010/11 | brief's published values |
|---|---|---|---|---|
| wheat | +0.720 | ×2.27 | ×1.45 | +0.720 / ×2.27 / ×1.45 |
| maize | +0.712 | ×1.97 | ×1.70 | +0.712 / ×1.97 / ×1.70 |
| rice  | +0.678 | ×1.72 | ×0.82 | +0.678 / ×1.72 / ×0.82 |

Observed hikes for reference: 2007/08 ×1.82 / ×1.84 / ×1.84; 2010/11
×1.16 / ×1.44 / ×0.79. **No parameter in this report was chosen to improve a
crisis score**; where scores moved, they are reported as an outcome, not a
justification (§5).

## 1. What Agrimate actually specifies

Established from the primary source, not assumed.

**Consumer (Eq. 6a–6c; Suppl. D.34c/d, D.35).** CES over the commodity and a
compound good, maximised under a budget constraint *and* a quantity
constraint `0 ≤ C̃ ≤ I_s + S_c,s^(t-1)`, giving

```
C_s = min( A*_c p_c^(-ε_c) / (1 + A*_c (p_c^(1-ε_c) - 1)) · B*_c,s ,  I_s + S_c )
```

with `B*_c,s = p*_c,s C*_s / A*_c,s` **fixed** and equal to baseline
consumption cost divided by the baseline budget share. Prices are unitless
indices of order one, so at baseline `p = 1` and the bracket returns `C*_s`.

Differentiating, with `s(p)` the *current* budget share,

```
d ln C / d ln p = (1-ε_c)(1 - s(p)) - 1 = -[ ε_c + s(p)(1-ε_c) ]
```

so Agrimate's consumer is isoelastic at `-(ε_c + A*_c(1-ε_c))` near baseline
and tends to unit-elastic as the budget share rises — expenditure is bounded
by `B*_c,s`. This reproduces the paper's own stated limits (`A*_c ≪ 1` ⇒
`C ∼ p^-ε_c`; `A*_c = 1` ⇒ `C ∼ p^-1`) and its low-income-country argument.
Default `ε_c = 0.1` (Suppl. Table D.8), so at `A*_c = 0.1` the baseline
elasticity is **−0.19**.

**Purchaser (Eq. 8a–8d; Suppl. D.30a/b, D.31a/b/c, D.59, D.61).** Two-tier
nested CES. Upper tier splits a budget `B*_d,s` between the commodity and a
compound good with elasticity `ε_d` (default `1/α = 1/3`); lower tier
allocates the commodity across suppliers by relative offer price with
elasticity `σ` (default 2) around baseline source shares `a*_{r,s}`:

```
D_{r←s} = a_{r,s} (p_off,r / p_→s)^(-σ) · [A_d p_→s^(-ε_d) / (1 + A_d(p_→s^(1-ε_d) - 1))] · B*_d,s
```

`A*_d,s` is the baseline ratio of commodity import value to total export
value; `B*_d,s = p*_wld D*_←s / A*_d,s` (D.59) — again derived from baseline
price × baseline quantity, not from an external income series. Restocking
(D.31a) is a symmetric partial adjustment `ΔD = (S* - Ŝ + δS*)/τ`, and
critically it is **converted into price terms** before it becomes demand:
`A_d = O_[0,1](A*_d + p_→s ΔD / B_d)` (D.31b/c). Agrimate's restock demand is
therefore budget-mediated and price-responsive.

## 2. Parity table

| # | Element | Agrimate | SHEAF Gate 0 | Verdict | Class / conf. |
|---|---|---|---|---|---|
| a1 | Consumption demand form | CES under budget constraint, Eq. (6c)/(D.35); elasticity −(ε_c + s(p)(1−ε_c)), → −1 | isoelastic `C_flex·(p/p0)^elast`, `dynamic_crop.py:595`; no budget | **weaker, but only mildly** | D, 90% |
| a2 | Consumer price faced | region-specific consumer-site price `p_c,s` = storage-average price (D.26) | single world price `p` for all nodes | **weaker** | D/E, 90% |
| a3 | Heterogeneity of demand response | per-region `A*_c,s` ⇒ per-region elasticity | one `elast` per crop, identical across 18 nodes | **weaker** | D, 95% |
| **a4** | **Price responsiveness of *market* demand** | whole purchaser demand carries ε_d ≈ 1/3 (D.30a), restock included (D.31b) | 86–99% of market demand is `rebuild`, which has **no price term**; measured aggregate η = −0.05 / −0.11 / −0.09 | **materially weaker** | **D, 95%** |
| b1 | Supplier allocation form | CES lower tier, `(p_off,r/p_→s)^(-σ)`, σ = 2 | fixed source shares `S` = Leontief (σ = 0) corner | weaker | D, 95% |
| **b2** | **Offer-price reweighting** | active | `_ask_reweight_dest` (`dynamic_crop.py:503-509`) is the **identity map**; verified bit-for-bit | **absent — coding bug** | **B, 99%** |
| b3 | Is the allocation an optimum? | yes, Eq. (8a/8b) | allocation yes (σ=0 CES); **clearing no** | see (c) | — |
| c | Bilateral clearing | offer prices + CES allocation clear the market | `min(offers·A, S·demand)` short side + 15% residual pool (`_bilateral_clear`, L512-537) | **rationing rule, not clearing** | D, 95% |
| d | Consumption capped by holdings | `0 ≤ C ≤ I_s + S_c^(t-1)` (D.34d) | `min(desired, max(0, avail − shipped + received))`, L622-623; binds on 7.9 / 0.3 / 20.1 % of country-steps | **equivalent** | **H, 95%** |
| e | Inelastic industrial block | none | US maize FSI excess vs 2000–04 (`_demand_blocks`, L410-451) | **stronger** (with a caveat) | E, 85% |

### (a) Budget constraint — verdict: **weaker, but the effect is smaller than the prior expected, and it is not where the real gap is**

*Measured* (`r2_02_parity_measure.py`, `r2_a_budget_peak.csv`,
`r2_a_budget_country.csv`). At the simulated 2007/08 peak on the official
scored path, comparing SHEAF's `(p/p0)^elast` against Agrimate's Eq. (D.35)
branch at `ε_c = 0.1`:

| crop | p_peak/p0 | SHEAF q/q* | Agrimate A*=0.05 | A*=0.10 | A*=0.20 | A*=0.40 |
|---|---|---|---|---|---|---|
| wheat | 2.51 | 0.871 | 0.857 (−1.4pp) | 0.808 (−6.3pp) | 0.725 (−14.6pp) | 0.601 (−27.0pp) |
| maize | 2.91 | 0.766 | 0.832 (**+6.6pp**) | 0.774 (+0.8pp) | 0.679 (−8.6pp) | 0.546 (−22.0pp) |
| rice  | 2.66 | 0.822 | 0.847 (+2.5pp) | 0.794 (−2.8pp) | 0.707 (−11.5pp) | 0.579 (−24.3pp) |

Two findings, both against the prior:

1. **At Agrimate's own default calibration (`ε_c = 0.1`, `A*_c ≈ 0.1`) SHEAF's
   constant elasticity is nearly identical to Agrimate's consumer demand.**
   The implied Agrimate baseline elasticity is −0.19, bracketed by SHEAF's
   −0.15 / −0.20 / −0.25. At the peak the gap is +6.3 pp (wheat), −0.8 pp
   (maize, SHEAF destroys *more* demand), +2.8 pp (rice). The budget wall is
   a convexity that bites at price ratios well above the ×2.5–2.9 reached in
   this window.
2. **A homogeneous `A*` is a reparameterisation, not new heterogeneity.**
   `r2_a_budget_country.csv` shows the per-country percentage gap is
   *identical* for every node (wheat 10.37% at `A*=0.20`), because Gate 0 has
   one world price and a common `A*` cancels. The distributional claim — poor
   import-dependent countries cut purchases more — requires per-country
   `A*_c,s`, which is **not in the repository** and is the true calibration
   burden. Without it, "adding a budget constraint" buys nothing over
   retuning `elast`.

The real gap is a4, found while doing this measurement
(`r2_03_decomp.py`, `r2_04_effective_elasticity.py`):

```
food_need = max(0, desired - avail)                          <- carries elast
rebuild   = rebuild_lambda * max(0, target - after_food_stock)  <- NO price term
demand    = food_need + rebuild            (dynamic_crop.py:606-610)
```

| crop | rebuild share of demand, full window | 2007/08 crisis | measured η of market demand | vs `params.elast` |
|---|---|---|---|---|
| wheat | 86.2% | 90.3% | **−0.052** | −0.15 (35% of it) |
| maize | 96.5% | 99.5% | **−0.106** | −0.25 (43%) |
| rice  | 84.5% | 88.3% | **−0.085** | −0.20 (43%) |

η is an exact finite difference: the demand block is recomputed at `1.01·p`
holding `avail`, `target`, `C_flex`, `C_ind` fixed; the reconstruction
reproduces the recorded `demand` array to 0.0. Agrimate's purchaser carries
ε_d ≈ 1/3 on *all* of its demand including restocking. **SHEAF's world market
faces demand 3–7× less price-elastic than Agrimate's.** That, not the missing
budget constraint, is the material demand-side gap.

### (b) Armington vs CES purchaser — verdict: **weaker, and one intended mechanism is dead code**

*Is SHEAF's allocation the solution to a stated optimisation?* Partly.
`D_{i→j} = S_ij · demand_j` with `S` fixed and price-free is exactly the
`σ → 0` (Leontief) corner of Agrimate's Eq. (8c) lower tier: it is the
cost-minimising solution of `min Σ p_i D_i s.t. min_i(D_i/a_i) ≥ D̄`. So a
utility/constraint pair does exist, and it is Agrimate's own aggregator at
zero substitution — SHEAF omits the elasticity, not the framework. The
*clearing* step (`min(O, D)` plus the residual pool) is **not** the solution to
any optimisation; see (c).

*The reweighting is a no-op.* `_ask_reweight_dest` (L503–509) multiplies row
`i` of the exporter→destination matrix `A` by `rel_i = (p0/ask_i)^γ`, a scalar
constant within the row, then renormalises the row. On any row-stochastic `A`
this is algebraically the identity. Verified two ways
(`r2_ask_reweight_noop.csv`, `r2_ask_comp_elast_sweep.csv`):

- `max|A_eff − A|` over 203 ask draws including γ ∈ {0, 1.25, 8}: **3.3e-16**
  for all three crops (16–17 of 18 rows sum to 1; the rest are zero rows).
- End to end, `Σ_t p_t` is **bit-identical** across γ ∈ {0, 1.25, 8} for all
  three crops (wheat 49256.660194, maize 29929.314368, rice 92279.150479),
  as are corr and both hike ratios.

`ask_comp_elast = 1.25` is documented in `CropParams` (L112) as the analogue
of Agrimate's σ, and `data_faostat.bilateral_shares` docstring names the
`by="source"` matrix "the baseline demand shares a*_rs" — i.e. the code
already identifies `S` with Agrimate's `a*_{r,s}`. Agrimate reweights `a*_{r,s}`
by the *suppliers'* offer prices, down the importer's source mix. SHEAF applies
the reweight to the wrong matrix and the wrong axis, where it cancels.
**Classification B (coding bug), confidence 99%** — reproduced, not inferred.

### (c) Short-side clearing — verdict: **a rationing rule, not a market-clearing condition**

`_bilateral_clear` takes `ship = min(offers_i·A_ij, S_ij·demand_j)`
element-wise. There is no price that equates the two sides; the element-wise
minimum *defines* the quantity and discards the difference. Measured
(`r2_c_rationing.csv`), on the official scored path:

| crop | steps where Σoffers ≥ Σdemand | of those, steps with unmet demand | mean unmet frac when supply covers demand | cumulative unshipped offers | cumulative unmet demand |
|---|---|---|---|---|---|
| wheat | 132 / 144 | **132** | 32.2% | 10 366 MMT | 378 MMT |
| maize | 144 / 144 | **120** | 12.1% | 17 468 MMT | 81 MMT |
| rice  | 73 / 144 | **73** | 46.5% | 1 643 MMT | 565 MMT |

Wheat has 27× more grain on offer than there is unmet demand, at essentially
every step, and the demand still goes unmet. The unsatisfied demand does not
carry over and is not reallocated beyond `residual_subst = 0.15` of the
residual: it is destroyed, and it re-enters the model **as a price signal**
through `unmet_frac` (L661–663) and `unmet_kappa`.

Is that consistent? Partly, and this is the strongest defence of the current
design. The price uses `u_anom = max(0, unmet_frac − unmet_twin)`, so the
systematic rationing level is differenced against a twin that suffers the same
friction. Measured (`r2_F6_unmet_anomaly.csv`): only **7.3% (wheat), 33.0%
(maize), 0.2% (rice)** of the mean unmet level survives differencing. But the
peak anomaly reaches 0.40 (wheat and maize), which at `κ = 2.5` is a **+100%
price uplift** at exactly the crisis peak. So the twin absorbs the level and
leaves the crisis amplitude to be carried by an anomaly in a rationing
statistic rather than in physical scarcity. Classification D, confidence 90%.

### (d) Consumption capped by holdings — verdict: **equivalent. Tested, not assumed.**

`consumption = min(desired, max(0, avail − shipped + received))` where
`avail = stock + H[:,t]` (L622-623, L593) is the operational counterpart of
Agrimate's `0 ≤ C ≤ I_s^(t) + S_c,s^(t-1)` (D.34d). Instrumenting the loop
(`r2_d_storage_cap.csv`) shows the cap **actually binds**:

| crop | country-steps where cap binds | desired not consumed | as % of desired | worst node |
|---|---|---|---|---|
| wheat | 7.87% | 68.8 MMT | 1.89% | Thailand (26.4%) |
| maize | 0.31% | 8.7 MMT | 0.19% | Egypt (1.4%) |
| rice  | 20.10% | 80.6 MMT | 3.46% | Canada (56.9%) |

The one bookkeeping difference: SHEAF lets same-step harvest and same-step
imports be consumed, Agrimate uses previous-step storage plus current
arrivals. On a 24-step clock this is a sub-fortnight timing convention, not a
substantive divergence. **Classification H, confidence 95%.**

### (e) Inelastic industrial block — verdict: **a strength, with a documentation caveat**

The US maize FSI excess over the 2000–04 mean is a real, dated, legally
mandated rigidity (RFS/RFS2, EISA 2007) affecting ~40 MMT/yr of US maize by
2008 — the single largest identified demand-side driver of the 2007/08 maize
price in the literature SHEAF is competing with. Agrimate is single-commodity
and does not carry it; SHEAF does, and it is derived from PSD data
(`load_psd_use_split`) rather than assumed. It is also *disclosed and
generalised*: `industrial_nodes` and `ind_base_years` are `CropParams` fields,
and `_demand_blocks` applies the same rule to any node listed. That is a
parameterised structural feature, not a hard-coded exception; the only node
currently listed is USA because it is the only one with a mandate of that
scale in-window.

The caveat is that an inelastic block mechanically lowers the aggregate demand
elasticity, and maize's rebuild share is already 99.5% in the crisis window —
so the block sits on top of an already near-inelastic market rather than
being the thing that makes it inelastic. **Classification E (design
difference, favourable to SHEAF), confidence 85%.** Not a defect.

## 3. Prototype

`scripts/scratch/r2_05_prototypes.py`. Three patches, all in memory.

- **P1 — consumer budget constraint** (Agrimate 6c/D.35) on `desired_flex`.
  `ε_c` is chosen per crop so the *baseline* elasticity equals the existing
  `params.elast`: `ε_c = (|elast| − A_c)/(1 − A_c)` at `A_c = 0.10`. Only the
  curvature is new, so it cannot double-count at `p = p0`.
- **P2 — purchaser budget constraint** (Agrimate 8c/D.30a with D.31b/c) as a
  normalised CES budget factor `g_d(p̂) = p̂^(−ε_d)/(1 + A_d(p̂^(1−ε_d) − 1))`
  multiplying the price-free `rebuild` branch. `ε_d = 1/3`, `A_d = 0.05`
  (Agrimate defaults). `g_d(1) = 1` exactly, so the twin identity is preserved
  by construction. **No budget series is ever constructed** — the
  normalisation removes `B*_d,s`, exactly as Agrimate's own D.59 makes the
  budget a function of baseline price × baseline quantity.
- **P3 — source-share offer-price reweight** (Agrimate 8c lower tier). Adds
  `_ask_reweight_src(S, ask, p0, γ)`, normalising down columns, and passes
  `S_eff` to `_bilateral_clear`. Pure bug fix: no new parameter (`γ` reuses
  the existing `ask_comp_elast`), no new data, no new state.

### Results

`r2_prototype_scores.csv`, `r2_prototype_asserts.csv`. **All four robustness
assertions pass for every variant on every crop** (twin identity, AMIS raises
price, AMIS cuts exports, no spring spike) — 24/24 assertion runs.

| variant | crop | corr (Δ) | 2007/08 (Δ) | 2010/11 (Δ) | η market demand |
|---|---|---|---|---|---|
| baseline | wheat | +0.720 | ×2.27 | ×1.45 | −0.052 |
| | maize | +0.712 | ×1.97 | ×1.70 | −0.106 |
| | rice | +0.678 | ×1.72 | ×0.82 | −0.085 |
| P1 consumer budget | wheat | +0.716 (−0.004) | ×2.20 (−0.07) | ×1.46 (+0.01) | −0.066 |
| | maize | +0.709 (−0.003) | ×1.94 (−0.03) | ×1.66 (−0.04) | −0.127 |
| | rice | +0.691 (+0.013) | ×1.71 (−0.01) | ×0.86 (+0.04) | −0.108 |
| **P2 purchaser budget** | wheat | +0.708 (−0.012) | ×2.21 (−0.05) | ×1.48 (+0.03) | **−0.376** |
| | maize | +0.729 (+0.017) | ×1.96 (−0.01) | ×1.66 (−0.04) | **−0.477** |
| | rice | +0.691 (+0.013) | ×1.72 (−0.00) | ×0.86 (+0.04) | **−0.402** |
| P3 source reweight | wheat | +0.728 (+0.008) | ×2.28 (+0.01) | ×1.45 (−0.00) | −0.052 |
| | maize | +0.712 (+0.000) | ×1.97 (+0.00) | ×1.66 (−0.03) | −0.107 |
| | rice | +0.678 (+0.000) | ×1.72 (+0.00) | ×0.82 (+0.00) | −0.085 |
| P2 + P3 | wheat | +0.716 | ×2.23 | ×1.49 | −0.377 |
| | maize | +0.723 | ×1.95 | ×1.62 | −0.466 |
| | rice | +0.691 | ×1.72 | ×0.86 | −0.402 |

**P2 raises the model's effective demand elasticity by a factor of 4.5–7.2, to
Agrimate's own −0.35 to −0.48 range, while moving every crisis score by less
than 0.02 in correlation and 0.05 in hike ratio.** That is the headline: a
large, checkable realism gain that is very nearly score-neutral. Score
movement is mixed in sign (wheat corr down, maize and rice up; the 2007/08
over-shoot narrows slightly toward the observed ×1.82/×1.84, the 2010/11
wheat over-shoot widens slightly) and is *not* offered as evidence for the
change.

Sensitivity (`r2_P2_A_D_sweep.csv`, `r2_P2_eps_d_sweep.csv`): across
`A_d ∈ [0, 0.4]` corr moves ≤ 0.04 and η spans −0.34 to −0.70; across
`ε_d ∈ [0.1, 0.6]` corr moves ≤ 0.03 and η spans −0.20 to −0.69. The result is
robust to `A_d` and governed by `ε_d`, which is the parameter with a
literature value.

## 4. Falsification

`scripts/scratch/r2_06_falsify.py`. Arguing the other side.

**F1. "You measured a budget constraint effect; you actually measured an
elasticity." — This objection succeeds, and it changes the recommendation.**
Setting `A_d = 0` collapses `g_d` to a plain isoelastic `p̂^(−ε_d)` with no
budget constraint at all. `r2_F1_budget_vs_elasticity.csv`:

| crop | η baseline | η at A_d = 0 (no budget) | η at A_d = 0.05 (full) | share of gain from elasticity | from the budget wall |
|---|---|---|---|---|---|
| wheat | −0.052 | −0.338 | −0.376 | **88.4%** | 11.6% |
| maize | −0.106 | −0.450 | −0.477 | **92.7%** | 7.3% |
| rice  | −0.085 | −0.362 | −0.402 | **87.5%** | 12.5% |

87–93% of the gain comes from making the restock branch respond to price
*at all*; only 7–13% comes from the budget curvature. **The prior in the brief
— that a budget constraint on import demand is the highest-value candidate —
is right about *where* (the purchaser, not the consumer) and wrong about
*what*: the constraint is second-order in a window where prices reach only
×2.5–2.9.** I report the change as "price-responsive restock demand,
parameterised in Agrimate's CES budget form", not as "SHEAF now has a budget
constraint".

**F2. "Where does the budget come from for 2006–2011?" — It does not need to
come from anywhere, and that is why this objection fails against P2 but
succeeds against P1.** Agrimate's D.59 and D.34c define both budgets as
baseline price × baseline quantity divided by a baseline budget share, so the
budget is self-calibrating; and in the normalised form `g(1) = 1` the budget
level cancels entirely. P2 therefore introduces **two scalars with published
defaults** (`ε_d = 1/α = 1/3`, `A_d = 0.05`, Suppl. Table D.8) and **zero new
data**. P1 is the opposite case: its whole economic content is per-country
`A*_c,s`, which is not in the repository, would need FAO/World Bank food
budget shares for 18 heterogeneous nodes including a RestOfWorld aggregate,
and — with Gate 0's single world price — would still deliver heterogeneous
elasticities against a homogeneous price. **P1's calibration burden is real
and its measured payoff is 0.014 in η. It should not be adopted.**

**F3. Double-counting.** P2 multiplies `rebuild`, which contains no price term
(`dynamic_crop.py:608-609`), so there is nothing to double-count. The
*indirect* channel — `desired` ↑ ⇒ `after_food_stock` ↓ ⇒ `rebuild` ↑ — is
already inside the measured baseline η of −0.05 to −0.11 and is the reason η
is 35–43% of `params.elast` rather than 0%. P1 was constructed to be
elast-matched at baseline precisely to avoid double-counting, and the measured
Δη of +0.014 to +0.023 confirms it adds only curvature.

**F4. Twin identity and seasonality.** `g_d(1) = 1` exactly, so the calm leg is
unchanged; `assert_twin_identity` and `assert_no_spring_spike` pass on all
three crops for all six variants (24/24 assertion runs across the whole
matrix). Not argued — run.

**F5. Physical plausibility.** `r2_F5_physical_plausibility.csv`: P2 changes
cumulative consumption by −0.18% / +0.06% / −0.19%, mean world stocks by
−0.91% / −0.78% / +0.12%, and mean price by +0.07% / −0.33% / +0.93%. Trade
volume falls 3.0% / 1.6% / 9.3%, which is the intended effect (less notional
price-blind restock demand) and is largest for rice, the crop with the
thinnest trade and the highest rationing rate. Nothing breaks.

**F6. "The rationing finding (c) is overstated because the twin differences it
out."** Substantially correct in level — 92.7% (wheat) / 67.0% (maize) /
99.8% (rice) of the unmet fraction is absorbed by the twin. The finding
survives only in the weaker form stated in §2(c): the residual anomaly reaches
0.40 at the crisis peak for wheat and maize, so at `κ = 2.5` a doubling of the
price target at the peak is being sourced from a rationing statistic. I report
it at D/90% rather than as a defect.

**F7. "P3 is cosmetic — it barely moves the scores."** True on scores (+0.008
wheat corr, −0.03 maize 2010/11, rice unchanged). But that is the point: a
parameter documented as the Armington competition elasticity, whose sensitivity
sweep would report "no effect", is a live trap for exactly the kind of
sensitivity study `prepare_crop_run`'s `TypeError` on unknown overrides
(L738-743) was written to prevent. The defect is that `ask_comp_elast` is
currently unfalsifiable, not that fixing it changes 2008.

## 5. Complexity budget

Assessed against all nine axes in `CLAUDE.md`.

| axis | P3 (source reweight) | P2 (price-responsive restock) | P1 (consumer budget) |
|---|---|---|---|
| scientific benefit | restores a documented mechanism that is currently dead; makes `ask_comp_elast` falsifiable | η −0.05→−0.38: closes a 3–7× gap vs Agrimate on the single most consequential demand property | Δη +0.014; duplicates `elast` unless `A*_c,s` is heterogeneous |
| computational cost | one extra `(n,n)` multiply + column normalise per step | one scalar `pow` per step | one scalar `pow` per step |
| calibration burden | **none** (reuses `ask_comp_elast`) | **none new in-repo**: 2 scalars with Agrimate published defaults | **high**: per-country food budget shares for 18 nodes, 2006–11 |
| interpretability | improves (the parameter now does what its name says) | good: one Agrimate equation, cited | good in principle |
| new parameters | 0 | 2 (`eps_d`, `A_d`), both with source values | 1 per node |
| new state variables | 0 | 0 | 0 |
| runtime | +38 s over the full 6-variant × 3-crop matrix ⇒ negligible per run | negligible | negligible |
| continuity with lineage | **closer** to Agrimate Eq. (8c) | **closer** to Agrimate Eq. (8c)/(D.31b) | closer to Eq. (6c) in form, but Gate 0 lacks the regional price `p_c,s` that gives it content |
| publication benefit | none directly; removes a reviewer trap | high: "SHEAF's world market demand elasticity is −0.05" is a question a referee comparing SHEAF to Agrimate will ask, and there is currently no answer | low at homogeneous `A*` |

P3 passes on every axis and costs nothing. P2 passes: the benefit is large and
measured, the cost is two literature scalars and no state. P1 fails the
calibration-burden axis against a measured payoff of 0.014 in η and should be
recorded as a *deferred* option contingent on per-country budget shares and a
regional consumer price.

## 6. Recommendation

1. **Fix `_ask_reweight_dest` / add the source-side reweight.** Classification
   **B (coding bug)**, confidence **99%** (reproduced bit-for-bit). This is a
   defect on the code's own terms: `CropParams.ask_comp_elast` is documented as
   the Armington competition elasticity and has no effect. Fix independent of
   any other decision.
2. **Make the `rebuild` branch price-responsive in Agrimate's CES budget
   form.** Classification **D (economic simplification)**, confidence **95%**
   that the gap is real and material (measured η, exact finite difference,
   reproduced), **85%** that the proposed patch is the right size of fix.
   Present it as adding the purchaser's price elasticity `ε_d`, with the
   budget curvature `A_d` as the second-order refinement it measurably is.
3. **Do not adopt a consumer budget constraint at a homogeneous `A*_c`.**
   Classification **D**, confidence **90%**: measured payoff 0.014 in η,
   analytically a reparameterisation of `elast` under one world price.
4. Record (d) as **H, 95%** and (e) as **E, 85%** — investigated, sound.

## 7. Artifacts

Scripts (`scripts/scratch/`): `r2_lib.py`, `r2_01_baseline_and_noop.py`,
`r2_02_parity_measure.py`, `r2_03_decomp.py`,
`r2_04_effective_elasticity.py`, `r2_05_prototypes.py`, `r2_06_falsify.py`.

CSVs (`diagnostics/redteam/r2/`): `r2_ask_reweight_noop.csv`,
`r2_ask_comp_elast_sweep.csv`, `r2_a_budget_peak.csv`,
`r2_a_budget_country.csv`, `r2_c_rationing.csv`, `r2_d_storage_cap.csv`,
`r2_demand_decomposition.csv`, `r2_effective_elasticity.csv`,
`r2_prototype_scores.csv`, `r2_prototype_asserts.csv`, `r2_P2_A_D_sweep.csv`,
`r2_P2_eps_d_sweep.csv`, `r2_F1_budget_vs_elasticity.csv`,
`r2_F5_physical_plausibility.csv`, `r2_F6_unmet_anomaly.csv`.

Figure: `figures/scratch/r2/r2_prototype_and_rationing.png`.

### What was run vs what was reasoned

**Run** (executable evidence): baseline reproduction; the `_ask_reweight_dest`
identity check and γ sweep; the storage-cap binding test; the rationing
counts; the budget-constraint counterfactual at the peak and per country; the
demand decomposition; the exact finite-difference elasticity; all six variants
× three crops × (3 scores + 4 assertions); the `A_d` and `ε_d` sweeps; F1, F5,
F6.

**Reasoned** (not executed): the derivation of Agrimate's effective elasticity
`−[ε_c + s(p)(1−ε_c)]` from Eq. (6c) — checked against the paper's own stated
limits but not against a running Agrimate; the identification of SHEAF's fixed
source shares with the `σ → 0` corner of Agrimate's CES; the claim in (e) that
the RFS is the largest in-window maize demand rigidity; the judgement that
SHEAF's same-step-harvest consumption timing is not a substantive divergence
from D.34d.
