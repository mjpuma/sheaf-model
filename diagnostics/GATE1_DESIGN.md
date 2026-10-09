# Gate 1 design: cross-crop substitution in Agrimate

Michael J. Puma, Columbia University. Draft for comment, 8 October 2026.
Source: `SHEAF_Gate1_design_note.docx`. This file is the Gate 1 spec on
`agrimate_julia/`. Do not implement from the deleted Python-host
`GATE1_PLAN.md`.

**Status.** Wheat Gate 0 is accepted (G0-P). Rice and maize `t_max=0`
smoke is met (2026-10-08). Coauthor questions are in §8; the note asks
for those views **before any of this is coded**.

## 1. What this does

Gate 1 links the wheat, rice and maize markets so that a shock to one
grain can move the other two. Do this **inside the published Agrimate
code**, with the smallest change to its economics, so that substitution
off recovers the single-crop runs exactly.

Each crop’s baseline consumption share and purchase budget share are
multiplied by a factor that rises when the other two grains are expensive
relative to an undisturbed run. With the substitution scale set to zero,
the factor is exactly one.

## 2. Demand in Agrimate today

Each region \(s\) has a purchaser (the strategic storage holder) and a
consumer. With the settings of the accepted wheat run (`two_markets =
true`, `ε_d_adjust = false`), the purchaser follows the single-market
formulas in `agents/consumer.jl`. Line numbers refer to
`agrimate_julia/src/AgrimateModel/src/` on SHEAF `main` at `647cab0`
(later commits do not change those lines).

Price index across suppliers \(r\), with demand shares \(a_{rs}\) and the
Armington elasticity \(\sigma\) (`determine_crop_price_index`, line 324):

\[
P_s = \Bigl( \sum_r a_{rs}\, p_r^{1-\sigma} \Bigr)^{1/(1-\sigma)}
\]

Purchase budget share: the seasonal baseline share plus a storage
correction, clamped to \([0, 1]\) (`determine_crop_budget_share`, lines
312–322):

\[
A_{d,s}(t) = A^*_{d,s}(n) + P_s(t)\, \Delta D_s(t) / B_s
\]

Purchases (`determine_demands`, line 355), other-goods price normalized
to 1:

\[
D_s = B_s A_{d,s}\, P_s^{-\varepsilon_d}
\big/ \bigl[ 1 + A_{d,s} \bigl( P_s^{1-\varepsilon_d} - 1 \bigr) \bigr]
\]

Consumption is set separately, from the consumer price \(p_c\) and the
consumer’s own share \(A^*_c\), and capped by what is available
(`determine_consumption`, lines 144–158):

\[
C_s = \min\Bigl\{
H_s A^*_c\, p_c^{-\varepsilon_c}
\big/ \bigl[ 1 + A^*_c \bigl( p_c^{1-\varepsilon_c} - 1 \bigr) \bigr],\;
S_s + \text{delivery}
\Bigr\}
\]

\(\Delta D_s\) restocks toward the seasonal storage target over \(\tau\)
steps (`determine_extra_demand`, line 345). \(B_s\) and \(H_s\) are the
purchaser and household budgets, \(n\) is the calendar step (24 per
year), and \(\varepsilon_d = 1/\alpha\) (`AgrimateModel.jl`, line 40;
default \(\alpha = 3\)).

Consumption and purchasing have **separate shares**. Raising the purchase
share alone does not change what people eat.

## 3. Proposed change

For crop \(g\) in region \(s\), a substitution factor from the other two
crops’ price indices:

\[
M^g_s(t) = \prod_{h \neq g}
\Bigl( P^h_s(t) \big/ \bar P^h_s(t) \Bigr)^{\eta_{gh}},
\qquad
\eta_{gh} = \xi\, \rho_{gh}\, \varepsilon_d^g
\]

\(\bar P^h_s(t)\) is the same purchaser’s index for crop \(h\) in an
**undisturbed run** of the same period, at the same step \(t\). Apply
the factor to both shares:

\[
A_{d,s}(t) = A^*_{d,s}(n)\, M^g_s(t) + P_s(t)\, \Delta D_s(t) / B_s
\]

and in consumption, \(A^*_c \rightarrow A^*_c\, M^g_s(t-1)\).

Consumption uses the factor from the **previous** step because, in
Agrimate’s step order, consumption runs before the purchasers compute
this step’s price indices. Scaling both shares by the same factor keeps
purchases in line with the higher consumption, so storage stays near its
target instead of absorbing the shift.

\(\xi\) is the substitution scale, tested at \(0\), \(0.3\) and \(0.6\).
Use \(\xi\) because \(\sigma\) is already Agrimate’s Armington
elasticity, \(s\) is the region index, and \(\kappa\) is a step size in
initialization. \(\rho\) is the substitutability structure from the
August Gate 1 plan, kept fixed:

| \(\rho\) | wheat | rice | maize |
|---|---:|---:|---:|
| wheat | 0 | 0.30 | 0.40 |
| rice | 0.30 | 0 | 0.20 |
| maize | 0.40 | 0.20 | 0 |

Near baseline prices, purchases respond to the share almost one for one,
so the implied cross-price elasticity of crop \(g\) with respect to crop
\(h\) is about \(\xi\, \rho_{gh}\, \varepsilon_d^g\). With the default
\(\alpha = 3\) and \(\xi = 0.6\), wheat to maize comes to about
\(0.6 \times 0.4 \times 0.33 \approx 0.08\). The calibrated \(\alpha\) in
the accepted runs may differ by crop; read the numbers from there.

## 4. What this does and does not do

At \(\xi = 0\) every exponent is zero and the factor is one, so each crop
reproduces its single-crop run. Because the reference is the undisturbed
run itself, the factor is also one in an undisturbed coupled run at any
\(\xi\). A wheat shock raises the wheat index above its reference, which
raises rice and maize consumption and purchases, so their prices rise.
That is the right sign for substitutes.

The change is **not** derived from a utility function. Each crop model
keeps its own household and purchaser budgets for the same region, so
higher rice spending is not offset elsewhere, and the cross responses
are not Slutsky-symmetric. State that plainly and report total grain
spending per region at \(\xi > 0\). The clamp on \(A_d\) still applies;
log how often it binds.

## 5. Code changes

The economics change is two lines. The rest lets three crop models step
together. Each edit gets an entry in `agrimate_julia/UPSTREAM.md`. Paths
are under `agrimate_julia/src/`.

| # | File | Lines | Change |
|---|---|---|---|
| 1 | `AgrimateModel/src/AgrimateModel.jl` | near 40; 100–101 | Add `ξ::Float64 = 0.0` to the parameters and pass it into the global parameters. |
| 2 | `AgrimateModel/src/agents.jl` | 77–114, 115–124 | Add `substitution_factor` and `substitution_factor_prev` (`Float64`), both set to `1.0` in the constructor. |
| 3 | `AgrimateModel/src/agents/consumer.jl` | 319 | `A_d = A_d_star * consumer.substitution_factor + p * ΔD / B` |
| 4 | `AgrimateModel/src/agents/consumer.jl` | 34 | Pass `A_c_star * consumer.substitution_factor_prev` instead of `A_c_star`. |
| 5 | `AgrimateModel/src/agents/consumer.jl` | 60–131 | Split before line 85. Lines 64–84 become `price_index_step!` (offer prices, demand shares, price indices); lines 85–130 stay in `procurement_step!`. Same statements, same order. |
| 6 | `AgrimateModel/src/model.jl` | 55–82 | In the purchaser loop (77–82) call `price_index_step!` then `procurement_step!`, so single-crop runs are unchanged. Add `step_coupled!`: for every crop run the supplier, policy and communication loops (60–75) and the purchaser delivery, consumption, accounting and `price_index_step!`; then set every purchaser’s factor; then run `procurement_step!` for all purchasers of all crops; then copy each factor into `substitution_factor_prev`. |
| 7 | new `AgrimateModel/src/coupling.jl` | new | Holds \(\rho\), the crop order and the reference index paths, and computes \(M\) for crop \(g\), region \(s\), step \(t\). A crop with no purchaser in region \(s\) contributes 1. |
| 8 | `simulation.jl` | 17, 55, 58, 140 | Move the per-crop setup (from line 55 through the `initialize_model` call) into `initialize_crop(params, crop)`. Add `simulate_coupled(params; crops, ξ)`: initialize the three crops, check that `start`, `N_year` and `t_max` match, load the reference paths, and step with `step_coupled!`. |
| 9 | `AgrimateModel/src/run.jl` | 55–60 | A coupled version that steps the three runs together. |
| 10 | `AgrimateModel/src/model/initialization.jl` | 300, 317, 372, 380 | No change. For reference: baseline price, purchaser baseline price, budget, baseline budget share. |
| 11 | `drivers/run.py`, `drivers/score.py` |  | `--coupled --xi` flags. Save each purchaser’s price index from the undisturbed single-crop runs as the reference. Score coupled output against the accepted single-crop output. |
| 12 | `AgrimateModel/test/` | new test | \(M = 1\) at \(\xi = 0\); \(M > 1\) for rice and maize when the wheat index is above its reference. |

## 6. How a coupled step runs

One process holds three Agrimate models and steps them together. Phases
1, 2 and 4 are existing code, split only so the factor can be set between
them. All three crops must share `start`, `N_year` and `t_max`; each
keeps its own harvest, trade network and restriction inputs. The
reference paths need one undisturbed run per crop before the coupled
runs, so the full Gate 1 set is three undisturbed runs plus coupled runs
at \(\xi = 0\), \(0.3\) and \(0.6\). Each coupled run costs about the sum
of the three single-crop runs, because the serial supplier optimizations
dominate and are unchanged.

## 7. Weak points

**Calibration basis.** Wheat Gate 0 is accepted on the authors’ own
calibration (J10). The rice and maize author inputs are not in the
Zenodo release, so their baselines would come from public data, which
for wheat overstated stocks by 23% and gave a 2007/08 price ratio of
1.25 against 1.36. Coupling crops calibrated on different bases would
blur the spillover result. Prefer asking for the rice and maize inputs
to running all three on public data.

**Region sets.** After Agrimate’s production and flow cutoffs, the
regions may not match across crops. The factor only uses crops that have
a purchaser with the same region id, which is safe but means some
regions get partial substitution. (Rice: Canada and Rest of Oceania are
not producers after the 0/0 harvest guard; they remain importers.)

**Reference choice.** An earlier draft used the stored baseline price
path (`consumer.baseline_price`) as the reference. That is one world
path set at initialization, not each purchaser’s realized index, and
undisturbed runs drift. Using the recorded undisturbed run removes both
problems at the cost of one extra run per crop.

**Identification.** Maize prices in 2007/08 also rose with biofuel
demand, which the Agrimate inputs do not carry. Choosing \(\xi\) on the
wheat-to-maize spillover could load that missing driver onto
substitution. Report the three values of \(\xi\) and do not pick one
unless a reviewer requires it.

**Budgets.** Three separate budgets for one region is a simplification.
It should be small at these elasticities; report it rather than assume
it.

**Exactness.** The split of `procurement_step!` keeps the statements in
order, but the coupled loop changes when each purchaser’s work happens.
Identity at \(\xi = 0\) should be exact; test it against a 0.5% bar on
monthly prices rather than assume it.

Do not invent production to hide empty regions.

## 8. Tests and questions

The test plan is the one from August. \(\xi \in \{0, 0.3, 0.6\}\) is a
sensitivity band fixed **before** any coupled run, not an estimate, and
\(\rho\) and \(\alpha\) are not retuned to improve the fit.

Hard bars:

1. At \(\xi = 0\) each crop matches its single-crop run (0.5% monthly
   price bar).
2. A wheat rise in 2007/08 does not lower rice or maize prices.
3. Wheat keeps its Gate 0 story (2007/08 restriction-led, 2010/11
   production-led).
4. The rice export bans still carry most of the 2008 rice spike.

Rice and maize single-crop smoke on this host is **met**. Do not start
Gate 2 until Gate 1 is accepted.

**Questions for Christian and Kilian (before coding):**

1. Is scaling both the consumption share and the purchase share the
   right place to put substitution, or would you attach it elsewhere in
   the purchaser’s or consumer’s problem?
2. Can you share the rice and maize inputs behind the published runs, so
   all three crops sit on the same calibration basis?
3. Do the region sets after cutoffs line up across the three crops?
4. Should the cross response scale with \(\varepsilon_d\), as proposed,
   or stay independent of each crop’s own price sensitivity?
5. Does anything in the storage rule assume a single crop, so that
   moving shares between crops could interact badly with restocking?
