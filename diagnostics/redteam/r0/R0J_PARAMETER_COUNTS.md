# R0j — parameter counts: SHEAF against its own lineage

Own-thread red-team item. The Potsdam sitting raised the number of free
parameters in Gate 0 as a criticism. The right comparison for that
criticism, under the lineage rule, is Agrimate — not an abstract standard
of parsimony. This note counts both, from primary sources.

## Agrimate

Counted from the ODD supplement, `agrimate/Kuhla_2025_AgrimateSupplement.txt`.

**Table D.8, agent parameters (15):** `α_I` inverse price elasticity of
demand, international market (3.5); `α_D,r` the same for the domestic
market (per region, see Eq. D.10 and Tbl. D.9); `α` inverse price
elasticity of the single world market for the Nash baseline (3); `λ`
linearity of the inverse demand function (0); `p_sto` unit storage cost per
step (0.1/N_year US$/t); `τ_exp` timescale of sales-expectation update
(0.5·N_year); `σ` price elasticity of supplier substitution (2); `τ`
timescale of balancing storage (0.2·N_year); `ρ` interest rate per step
(**0**); `δ` storage deterioration rate per step (**0**); `ν_r` share of
domestic imports in other suppliers' total sales (per region, Tbl. D.9);
`x_min` minimum sales per step as a share of total expected sales (0.2);
`ε_d` price elasticity of demand (1/α); `ε_c` price elasticity of
consumption (0.1); `ι` relative cutoff for price adjustments (0.001).

**Table D.1, timescales (2 behavioural):** `N_year` = 24, `N_hor` = N_year.
`N_total` is run length, not a behavioural parameter.

**Harvest-expectation submodel (2):** `N_for`, the horizon of accurate
harvest forecast, and `τ_for`, the width of the smooth transition to
baseline harvests beyond it (Suppl. ~L2615–2620).

**Table D.10, initialisation (2):** `κ` convergence damping (0.25), `ε`
convergence precision (1e−6).

**Total ≈ 21 numerical parameters**, two of which (`α_D,r`, `ν_r`) are
per-region vectors over 28 regions rather than scalars.

## SHEAF Gate 0

`CropParams` has 24 fields excluding `crop`. Four are structural
configuration rather than numerical knobs — `twin_harvest`, `shock_mode`,
`industrial_nodes`, `ind_base_years` — leaving **20 numerical parameters**:
`elast`, `stu_target`, `max_stu`, `seasonal_buffer_steps`,
`pipeline_max_steps`, `rebuild_lambda`, `warehouse_lambda`, `inv_eta`,
`smooth`, `trade_w`, `unmet_kappa`, `block_kappa`, `ask_alpha`,
`ask_target_fill`, `ask_comp_elast`, `ask_beta`, `ask_rival`,
`foresight_phi`, `harvest_pulse_frac`, `residual_subst`.

## Verdict

**Roughly 20 for SHEAF against roughly 21 for Agrimate, and Agrimate's
count excludes its per-region vectors.** SHEAF Gate 0 is not more heavily
parameterised than the model it succeeds. **Classification H, confidence
80–95%** — the counting is exact, but any count of this kind depends on
where one draws the line between a parameter and a configuration choice,
which is why the itemised lists are given above rather than only the
totals.

That is a complete answer to the count, and not an answer to the real
criticism underneath it. The substantive difference is **provenance, not
quantity**. Agrimate's parameters are mostly elasticities, timescales and
costs with external referents; two of SHEAF's most load-bearing ones are
not. `ask_rival` (0.80) was shown by A2 to have no surviving independent
justification, and `ask_target_fill` (0.70) sets the rest point of the
offer-price law by fiat, against a realised fill of 0.54/0.32/0.62 — which
is the origin of the transfer-function discontinuity in R0i.

So the honest position to put to Potsdam is: the count is in line with the
lineage, and two named parameters need better foundations. Both of those
are retired by an exporter-FOC formulation, which is the subject of the R1
seam.

## A related asymmetry worth conceding

Agrimate's `ρ = 0` and `δ = 0` at default. Its "finite-horizon discounted
expected-profit maximisation" therefore has, in its shipped configuration,
neither discounting nor spoilage: the only intertemporal force is the unit
storage cost `p_sto = 0.1/N_year`. This narrows the gap to SHEAF's
non-optimising cover rule considerably, and it means **any exporter-FOC
repair to SHEAF does not need to introduce an interest rate** to match the
lineage. It also means Agrimate's own optimisation is thinner than the
phrase "competitive storage model" implies, which is worth knowing before
conceding too much ground in the response.

Agrimate does, however, have two things SHEAF Gate 0 does not, and both
should be conceded plainly:

1. **A Nash baseline.** Agrimate's reference state is constructed so that
   each supplier maximises annual profit assuming others do the same, with
   storage and sales annually periodic (Suppl. §D.7.4.1). SHEAF's twin is a
   climatological simulation with no equilibrium condition imposed. R0
   checked and found SHEAF's twin does converge to an annual cycle, so it
   is periodic in practice, but it is not an equilibrium object.
2. **`x_min` as an admitted device.** Agrimate constrains minimum sales per
   step to 20% of expected sales, evenly spread, to stop the optimiser
   dumping stock in one step. This matters for the R1 seam: if a SHEAF FOC
   needs a similar stabiliser, that is parity with the lineage rather than
   a new sin, and the response can say so with a citation.
