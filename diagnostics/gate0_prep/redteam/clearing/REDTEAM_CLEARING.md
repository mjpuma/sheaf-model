# Red team / clearing — Gate 0 vs Agrimate

Adversarial pass on whether the Gate 0 market clears, in what sense, and
whether a glut lowers the price. Read-only on `sheaf/*.py`. Measurements
live in this directory; scripts under `scripts/scratch/redteam_clr_*.py`.
Adjudication is `../REDTEAM_SYNTHESIS.md`.

CES origin-share reweight is already shipped. Residual-pool shares and
the glut experiments below were measured **pre-CES** and were not
re-run after `929cec4` (`../VERIFICATION.md` §C.4). The rice 47% figure
is a FAOSTAT-pattern fact plus the residual-pool identity; it is not
expected to move with CES, but it is not re-measured.

## Probe map

| Script | CSV | Question |
|---|---|---|
| `redteam_clr_01_clearing.py` | `clr_massbalance.csv`, `clr_residual_pool.csv`, `clr_unexploited.csv`, `clr_walras.csv`, `clr_signs.csv` | Mass balance, residual pool, unmatched offers, Walras, sign of \(\Delta p\) |
| `redteam_clr_02_glut.py` | `clr_glut_permanent.csv`, `clr_glut_transient.csv`, `clr_glut_channels.csv` | Surplus vs shortfall, pinned-baseline removed |
| `redteam_clr_03_proto.py` | `clr_proto_scores.csv` | Prototype scores for clearing upgrades |
| `redteam_clr_04_twoprice.py` | `clr_price_variance.csv`, `clr_gate2_revenue.csv`, `clr_supply_demand.csv` | Two prices; government incentive |
| `redteam_clr_05_upgrades.py` | `clr_upgrade_scores.csv`, `clr_u1_mechanism.csv` | U1 source reweight, U2 two-sided unmet, U3 tatonnement |
| `redteam_clr_06_final.py` | `clr_omega.csv`, `clr_noarb.csv`, `clr_gamma_inert.csv` | \(\omega\), no-arbitrage, \(\gamma\) inertness (pre-CES) |
| `redteam_clr_07_qpcost.py` | `clr_qp_cost.csv`, `clr_solver_cost.csv` | Spatial QP as an alternative clearer |
| `redteam_clr_08_askfloor.py` | `clr_askfloor_scores.csv`, `clr_askfloor_asym.csv` | Ask floor vs glut asymmetry |
| (decomp) | `clr_asym_decomp.csv` | Drawdown vs unmet as the asymmetry channel |

## 1. Mass balance closes

`clr_massbalance.csv`. Accounting identity
\(\mathrm{avail} - \mathrm{ship} + \mathrm{recv} - \mathrm{cons} - S' - \mathrm{drawdown}\)
and world ship = world recv:

| crop | max \|mass residual\| MMT | world ship − recv | drawdown / harvest |
|---|---|---|---|
| wheat | \(1.4\times 10^{-14}\) | \(1.8\times 10^{-15}\) | 6.1% |
| maize | \(2.8\times 10^{-14}\) | \(1.8\times 10^{-15}\) | 6.6% |
| rice  | \(1.2\times 10^{-14}\) | \(8.9\times 10^{-16}\) | 14.0% |

Category **H**. Confidence **95–100%**. This is not Walrasian clearing
(§3); it is an accounting identity of the short-side map.

## 2. Residual pool — rice is half residual

`clr_residual_pool.csv`, official matched leg, all 144 steps:

| crop | world trade MMT | network | residual | residual share | 2007/08 | 2010/11 |
|---|---|---|---|---|---|---|
| wheat | 523.4 | 459.5 | 63.9 | **12.2%** | 14.8% | 8.0% |
| maize | 399.6 | 385.3 | 14.3 | **3.6%** | 3.6% | 4.2% |
| rice  | 125.0 | 65.7 | 59.3 | **47.4%** | 47.5% | 40.6% |

Letter and synthesis round rice to 47%, wheat 12%, maize 4%. Reproduced.
Rice trade-over-world-demand is 0.18 against wheat 0.58 and maize 0.83:
the FAOSTAT pattern is doing less work for rice, and the residual pool
is carrying almost half of what ships. Category **F** (empirical
coverage of the rice network), not B. Confidence **95–100%** on the
pre-CES CSV; the post-CES figure is not in this directory.

`clr_unexploited.csv`: both sides left unmatched in 74–97% of steps
(wheat 140/144). Mean offer left is large relative to trade; that is
the cover/offer residual sitting unshipped, not a bug in the min(OA,
SD) step. Category **D/E** (short-side bilateral plus pool, by design).

## 3. Not Walrasian, and \(\mathrm{sign}(\Delta p)\) is not excess demand

`clr_signs.csv`:

| crop | frac \(\Delta p\) agrees with excess demand | corr(\(\Delta p\), ED) | frac \(\Delta p\) agrees with stock gap |
|---|---|---|---|
| wheat | 0.47 | +0.36 | 0.60 |
| maize | 0.53 | −0.02 | 0.51 |
| rice  | 0.40 | +0.41 | 0.47 |

Synthesis's 40–53% is this table. `clr_walras.csv`: an interior
flow-clearing price in the ask bounds exists in 16 / 18 / 4 of 144
steps. Storage demand's price elasticity in that probe is coded 0 — the
cover does not buy when \(p\) falls. Category **E** (different clearing
concept from Agrimate's agent programmes). Confidence **95–100%** on
the signs CSV; **80–95%** that a Walrasian re-clear would be a different
model (U3 below).

## 4. Glut already lowers the price

Sitting question: surplus should lower \(p\). Controlled harvest shocks
on the unpinned calm twin (`clr_glut_permanent.csv`; baseline harvest
scaled by \(1-10^{-6}\) so both legs share a price law). Permanent
±1% and ±2%, one-sided unmet (the shipped channel):

| crop | \(s\) | shortfall \(\Delta\log p\) | surplus \(\Delta\log p\) | asym ratio | surplus lowers \(p\) |
|---|---|---|---|---|---|
| wheat | 1% | +5.01% | **−4.60%** | 1.04 | True |
| wheat | 2% | +10.4% | **−8.90%** | 1.06 | True |
| maize | 1% | +2.86% | **−2.74%** | 1.02 | True |
| maize | 2% | +5.85% | **−5.44%** | 1.02 | True |
| rice  | 1% | +5.29% | **−4.91%** | 1.02 | True |
| rice  | 2% | +10.8% | **−9.42%** | 1.04 | True |

Every row in the file, including ±5/10/20% and the two-sided-unmet
mode, has `surplus_lowers_price = True`. Asymmetry grows at large
shocks (wheat 10% onesided ratio 1.31) because the unmet channel is
truncated at zero; that is a different object from the glut. Two-sided
unmet does not repair the 1–2% band (already symmetric) and mixed the
upgrade scores (§5).

`clr_asym_decomp.csv` at 10%: turning drawdown off *increases* wheat
asymmetry (1.31 → 1.43). The glut channel is the scarcity ratio, not
the warehouse drain and not unmet.

Category **H** — their glut question is already answered without a
change. Confidence **95–100%**.

## 5. Upgrades prototyped, not adopted

`clr_upgrade_scores.csv`. U1 (source-share reweight, \(\gamma=1.25\)) is
the object that shipped as CES; pre-CES monkeypatch maize corr +0.711
(twin not rebuilt; live CES is +0.778). U2 (two-sided unmet) wheat corr
+0.720 → +0.739 but 2010/11 hike ×1.45 → ×1.77 (overshoot). U3
tatonnement on traded quantity wrecks wheat corr (+0.72 → +0.38).
Imbalance tatonnement at small \(k\) is near-inert to mildly harmful
on maize.

`clr_u1_mechanism.csv`: Russia→Egypt wheat share during the ban falls
more under U1 than under shipped dest-reweight (−0.19 → −0.21 at
\(\gamma=1.25\)). That is the "cheaper / less-blocked origins gain
share" channel working on the source matrix.

`clr_askfloor_scores.csv`: widening the 0.45\(p_0\) ask floor does not
move official scores (`frac_at_floor = 0` on the shipped path). The
glut question is not an ask-floor question.

`clr_gate2_revenue.csv`: exporter revenue at own \(q_i\) vs at world
\(p\) differs by on the order of 5–15% at the world aggregate
(wheat −5.6%, maize +14%, rice −15%). A government incentive on own
export price is representable; the two-price seam is real. Category
**E** that Gate 0 is a usable host for Gate 2, not that the seam is a
bug.

QP-cost CSVs (`clr_qp_cost.csv`, `clr_solver_cost.csv`) are present;
they compare a spatial-QP clearer as an alternative, not as a shipped
path. Thin as a recommendation: the synthesis correctly did not adopt
it.

## Classification summary

| Claim | Class | Confidence |
|---|---|---|
| Mass balance to \(10^{-14}\) MMT; world ship = world recv | H | 95–100% |
| Residual share wheat 12%, maize 4%, rice 47% | F (rice network); H (the numbers) | 95–100% pre-CES |
| Not Walrasian; \(\mathrm{sign}(\Delta p)\) agrees with ED 40–53% | E | 95–100% |
| Surplus lowers \(p\) at 1–2%, roughly symmetrically | H | 95–100% |
| Two-sided unmet / tatonnement prototyped, not adopted | D/E | 80–95% |
| Own-\(q\) vs world-\(p\) revenue 5–15% | H | 80–95% |

No change to `sheaf/*.py`. The glut question does not justify two-sided
unmet. Rice 47% is a diagnose-before-redesign item, already in the
letter.
