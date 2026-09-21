# Gate 0 departure register

Statuses: proposed | approved | implemented | validated | rejected | deferred.

## D0 — Rebuild Gate 0 as Agrimate (approved, implemented)

Rewrite approved by the 16 Sep 2026 assignment. Historical Fig. 4 match
**not** claimed.

## Legacy mechanisms removed

L1 fill-target 0.70; L2 calm-price pin; L3 trade/scarcity blend; L4 ask_rival;
L5 prescribed buffer; L6 scarcity-ratio floor as economics; L7 residual ν;
L8 AR(1) smoother. Rejected for baseline. Worse Pink-Sheet fit is not a reason
to restore them.

## Data adaptations (not economic departures)

A1 **USDA PSD not FAOSTAT Food Balances (P10 confirmed; R6 parallel).**
`data/faostat_network/` is E0 trade only. FoodTradeNetwork P0/R0 are
2015–21 averages, not 2006–11 annual FB. Zenodo 10688435 is FAO-forced
model *output*, not FB inputs. Author AgriculturalData expects cleaned
`wheat_food_balance_fao.csv`. A **labelled host reconstruction** of
`impute_food_balance_fao("wheat")` now lives at
`data/food_balances/wheat_food_balance_fao.csv` (FBSH 2006–11 + QCL +
TCL; sign-flipped 5074; not rebalanced; not bit-identical to Kuhla's
unpublished local CSV). **Not adopted** as `prepare_wheat`. R6 obtain
vendored raw FAOSTAT **FBSH** wheat 2006–11 under `data/faostat_fb/`.
R6 built a labelled `prepare_wheat_fbsh` parallel (members summed,
China ~2× USDA A8 *mean*; Psi stayed USDA; anomalies H/Hstar−1).
**Not adopted.** **S3** re-scored that parallel against the S1
member-sum USDA host (2006–08 harvest+AMIS): China H 112.7 vs FBSH
112.3 (ratio 1.00); EA 0.99; world H 0.99. moy 20.1× → 33.0×
(worsened vs this window and vs S1 host 16.8×). Items 1–3 did not
improve (item 3 still 1.444; Psi still USDA `ending_stocks`; 5074 is
ΔS, not S). **Not adopted.** USDA remains the 2006–11 `prepare_wheat`
default. Writeup: `diagnostics/gate0_agrimate/author_fb.md` (S3:
`s3_fbsh.md`; historical R6: `fb_wheatdata.md`, `faostat_fb.md`).
A2 E0 shares rescaled; A3 A_d not E.30 (F.1 Egypt 0.17 unused: Egypt is inside Northern Africa);
A4 A_c income-group proxies; A5 restriction weights inside multi-country
regions; A6 inverse-demand floor 0.05 (numerical).
A7 **Fig. 4 experiment ≠ 14022004 wheat defaults (P7).** Author
`main_output` NetCDF (10688435) is AgrimateEU28+Egypt, FAO anomalies,
α_foreign=3.5, ζ=1, N_for=6, start 2000. Host remains AgrimateRegionsWheat
+ USDA + αI=3.2. Scored in `fig4.md`; not a reason to retune.
R2 adds `fig4_experiment_params()` (αI=3.5, ζ=1, N_for=6) as a **labelled
comparison object**, not a `wheat_params()` replacement. **S4** inventoried
A7: FAO cleaned FB reconstruction is labelled and **not adopted**; a
parallel AgrimateEU28+Egypt **name list** is labelled from NetCDF
`region_list` + Egypt=EGY (`s4_parallel_eu28_egypt.csv`) and is **not**
C.1. **T3** obtained compact FAO-since-2005 annual relative anomalies
(2000–11, since-2005 mask) and the sourced AgrimateEU28 YAML + Egypt=EGY
ISO map (`t3_fig4_inputs/`). **Not adopted.** Host remains
AgrimateRegionsWheat (EU-27, Brazil named, Egypt in Northern Africa).
Still cannot-set: start 2000 as the live window, FAO as `WheatData`,
old-demand-dynamics, author Julia, bit-identical author FB, FAO as
`prepare_wheat`. Do not invent an Egypt node. Writeup:
`diagnostics/gate0_agrimate/s4_a7.md`, `t3_fig4_inputs.md`.
R10 scores that 2006–08 run against `author_fig4/`: hike ×2.22 vs ×1.62,
moy 13.3× vs 1.51×, 2006 index 1.677 vs 1.183 (knobs moved *away*),
undisturbed last/first 0.409 vs 1.006. **Not adopted.** Remaining A7
unchanged (`fig4_config_score.md`).
A8 **Multi-country PSD baseline is member-sum (P9; R7 labelled; S1 implemented).**
`prepare_wheat` 2007–09 baseline sums PSD members within each year, then
means over 2007–09 — the same construction as `psd_regional_annual()`.
The rejected construction was `groupby(region).mean()` of country-year
rows. Counterexample 2007–09 USDA (H / C / ending stocks):
China (China+Hong Kong) mean 56.4 / 53.6 / 23.3 vs sum 112.7 / 107.1 /
46.6 (0.50×); Eastern Africa (10 countries) 0.33 / 0.66 / 0.055 vs
3.31 / 6.55 / 0.55 (0.10×). Single-row nodes (USA, EU-27 `European
Union`, Ukraine, …) match either way. Stocks here are USDA
`ending_stocks`, not FAOSTAT FBSH ΔS. Anomalies stay on the *summed*
member series. R7 labelled the C/S numbers (`a8_sum.md`). **S1
implemented** the adapter — China ×2 and Eastern Africa ×10 on the
live 2003–11 host. Not a parameter fit. Do not retune αI / p_sto /
xmin. Never FAO ΔS as stocks. See `GATE0_NEXT_PROMPTS.md`.

## G0-N numerical representation (not economic departures)

N1 **Fraction parameterization.** `(fd, fi) ∈ [0,1]^{2N}` maps onto
`{XD ≥ 0, XI ≥ 0, S ≥ 0}`. Equivalent feasible set to D.11–D.21, not a
different objective. Replaces L-BFGS on unbounded sales with a `1e12`
infeasibility cliff and `xmin = 1e-6` sales bounds (those bounds made
off-season `H = 0` plans infeasible).

N2 **Rolling forthcoming year.** Planning window is `[t, t+Nyear)` with
D.1 weights from the current step. Calendar-year replan from January with
start-of-year harvest already in `S0` double-counted realised `H` and was
infeasible mid-year. Closer to D.1 than the previous host.

N3 **Jacobi IBR inside the step.** Each region best-responds to last-step
expected rivals (D.22), then all plans update. Gauss–Seidel (28 stacked
replies in one step) is not a stage Nash and raced isoelastic Cournot onto
A6.
R4 **Undisturbed last/first channel (characterisation, not adopted).**
On 2003–11 undisturbed, freezing D.22 `q_oth` at XI*_world−XI*_r
(diagnostic hook `freeze_q_oth`, default off) yields last/first **1.019**
vs author **1.004** vs live host **1.630** (pre-S1 pooled-mean). xmin_off (ζ=1) **0.548** and
calendar_replan (stride=24) **0.523** overshoot below 1. XI still spans
137–235 MMT under the freeze — last/first is the D.7 offer mix, not XI
volume. Author Agrimate still updates D.22; freeze is a diagnostic
isolation, not a copy. Not a decay knob. Not L1–L8. `wheat_params()`
unchanged. Historical writeup: `diagnostics/gate0_agrimate/xi_split.md`.
**S2 re-measure (A8 member-sum host):** last/first **1.444** vs author
**1.004** (still >1.1). **T1 obtained** GitLab + 14022004 Julia
(*inspect-only*; 0 `*.jl` copied into `sheaf/agrimate/`). Sourced D.22
**differs**: author wheat is a horizon **vector + shift** of planned
foreign sales; host *was* a **scalar EMA** of current-step realized XI.
EMA *weight* matches (`1/(0.5 N_year)=1/12`). **No freeze**
in author Julia. **D.22 implemented** (`d22.py`): live host now uses
that vector+shift of planned foreign sales. `freeze_q_oth` stays
diagnostic, default off, not a `wheat_params()` field. Not a pin.
Solver still L-BFGS-B (N5). Writeup: `diagnostics/gate0_agrimate/item3.md`
(S2 snapshot 1.444); T1: `t1_julia.md`; T2: `t2_delta.md`; living D.22:
`d22.md`.

N4 **D.7 international scale.** Argument is `(XI_r + Q_{-r}) / XI*_world`
with `XI*_world` the per-step year-average (wheat_data note; Agrimate
`X*_I` scalar). Own-region `XI*_r` as denominator made Nash-scale `q ≫ 1`.

N5 **Unconverged L-BFGS-B (P5).** Feasible fraction plans with scipy
`success=False` (maxiter 1033 + ABNORMAL 710 = 1743/5832 on harvest+AMIS
2003–11). Counted separately from failed/fallback. Default `plan_maxiter=40`
kept: more iters move the price path, but 200 vs 400 disagree by a similar
RMSE, so there is no demonstrated unique stationary point to adopt.
Writeup: `diagnostics/gate0_agrimate/solver.md`. Not a pin and not L1–L8.
**T1:** author wheat solver is NLopt `:LD_SLSQP` (`maxtime=60`, current x1
fixed to demand). Sourced solver delta; **T2** labelled file:line
(`t2_delta.md`), not adopted. `equal_constraint` default is **false** so
S_end equality is off on wheat. Do not raise `plan_maxiter`.
R9 repeats the count on `fig4_experiment_params()` harvest+AMIS 2006–08
(`solver_fig4.md`): failed still 0; unconverged still counted; labelled
maxiter=200/400 probes do **not** raise the default cap and are not adopted.

Agrimate Tbl. D.8 `x_min = 0.2` (quadratic penalty, ζ=0) and linear
`p_sto = 0.1 / Nyear` are **implemented** (G0-S, from Zenodo 14022004).
Author `ζ` is a penalty switch, not a storage-cost coefficient.

S1 **C.1 count.** Paper said 28; author wheat list is 27. Host uses 27.
S2 **D.8 vs executable.** Host wheat defaults follow author code (αI=3.2,
τ=0.1, σ=2, εc=0.1, α_nash=3). Tbl. D.8 3.5/0.2 is `wheat_table_d8_defaults()`.
S3 **β / τ_P** local price adjustment: **unwired, matching the wheat
executable.** Author `AgrimateParams` has `β=0.05` and `τ_P=0.2` yr
(`AgrimateModel.jl`). The update is
`P_loc_tgt = P_loc · (D_tot / X̂)^β` (or 1 if `X̂ < ι X_avg` or baseline
sales ≤ that cutoff), then
`P_loc ← (1/τ_P) P_loc_tgt + (1 − 1/τ_P) P_loc` with `τ_P` in steps
(`τ_P * N_year`). That combined factor is computed in `sales_step!` and
written to output. It does **not** enter the wheat path:
`two_markets=true` and `pl_opt=false` are the struct defaults and are
never assigned in the retrieved tree; the two-market optimizer is called
with `P_loc_domestic = 1`, `P_loc_foreign = 1` (passing
`price_adjustment_factor_*` is commented out); domestic/foreign targets
are hardcoded to 1, so those factors remain 1 from initialization; offer
prices on `two_markets` use `expected_price_foreign/domestic` (× those
unit factors). `pl_opt` would inject combined `P_loc` only on the
non-`two_markets` branches. Host keeps `beta_loc=0.05`, `tau_p=0.2` as
unused fields. Not a guessed local-price rule. Not a change to αI.
Classification **H** (wheat path already pins P_loc = 1). Confidence
95–100% (direct inspection of Zenodo 14022004 `producer.jl` / params).
S4 **D.30a** purchaser upper tier: **wired as the demand-request formula.**
Wheat path (`two_markets=true`, `ε_d_adjust=false`, never overridden) calls
`determine_demands` with
`D = A_d P^{-ε_d} / (1 + A_d (P^{1-ε_d} - 1)) · B` then
`q_r = a_r (p_r/P)^{-σ} D`. Host `purchaser_demand(..., A_d, eps_d)` matches
that; `A_d=1` recovers D.30-only spend of B. `B = C*/A_d` at p*=1 (author
`mean(p* D*)/A_d*`). Extra demand enters via D.31b
`A_d = clip(A_d* + P ΔD / B, 0, 1)`. A_d proxies are unchanged (A3; not a
Pink-Sheet refit). Physical inflow remains T* + domestic sales. Author
two-market `x1` is *fixed* to those requests; host supplier plan still
sets current sales (labelled, not a guessed CES-rationing rule).
Classification **H** for the formula (95–100%); remaining x1 gap is **D**.
R5 adds `x1_from_demand=False` (default recovers T*+domestic). `True`
assigns Ndel-lagged foreign D.30/D.30a requests as international arrival
(`x1_demand.md`). 2006 harvest+AMIS: max |Δp_w|=0 (XI-weighted offers);
Σ inflow 478→908 MMT. Not a min(supply, demand) ration. Not adopted.
14022004 Julia inspected under `/tmp` (T1); still **not** copied
in-tree. `wheat_params()` unchanged.

## Documentation G-fix (not an economic departure)

G-R3 **World-price methods shorthand.** Code was already the
XI-weighted mix of lagged D.7 offers × p0
(`model.py` `np.dot(xi_lag, p_lag)/vol`). methods.md said “D.7 × p0”.
R3 names `volume_weighted_offer_index`, stores `AgrimateResult.offer`,
and tests that reported `p_w` equals that mix and is not D.7 of world
XI*. Economics unchanged. Zenodo 14022004 `plot_wm_price_timeseries`
still not in the repo (`world_price.md`). Not a 2006 pin. Not a
`wheat_params()` change.

## Coding fix (not an economic departure)

B1 **International delivery (P2).** Pre-fix, lagged XI was credited to the
*exporter* as consumer inflow (`inflow = sold_d + own XI_{t−Ndel}`). That
is not D.3/E.1. Host now routes XI along row-normalised international T*.
D.30 CES / D.30a requests are computed; quantity delivered is still T*
by default. R5 labelled `x1_from_demand` (not adopted). Not a world-price pin.

## Proposed extensions (not implemented)

E1 cross-crop substitution (≠ origin CES). E2 government restriction game
(≠ supplier oligopoly). Need user approval before code.
