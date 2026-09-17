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

A1 USDA PSD not FAOSTAT Food Balances; A2 E0 shares rescaled; A3 A_d not E.30 (F.1 Egypt 0.17 unused: Egypt is inside Northern Africa);
A4 A_c income-group proxies; A5 restriction weights inside multi-country
regions; A6 inverse-demand floor 0.05 (numerical).

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

N4 **D.7 international scale.** Argument is `(XI_r + Q_{-r}) / XI*_world`
with `XI*_world` the per-step year-average (wheat_data note; Agrimate
`X*_I` scalar). Own-region `XI*_r` as denominator made Nash-scale `q ≫ 1`.

Agrimate Tbl. D.8 `x_min = 0.2` (quadratic penalty, ζ=0) and linear
`p_sto = 0.1 / Nyear` are **implemented** (G0-S, from Zenodo 14022004).
Author `ζ` is a penalty switch, not a storage-cost coefficient.

S1 **C.1 count.** Paper said 28; author wheat list is 27. Host uses 27.
S2 **D.8 vs executable.** Host wheat defaults follow author code (αI=3.2,
τ=0.1, σ=2, εc=0.1, α_nash=3). Tbl. D.8 3.5/0.2 is `wheat_table_d8_defaults()`.
S3 **β / τ_P** local price adjustment: present in author params, not wired.
S4 **D.30a** purchaser upper tier (commodity vs compound good): not wired.

## Coding fix (not an economic departure)

B1 **International delivery (P2).** Pre-fix, lagged XI was credited to the
*exporter* as consumer inflow (`inflow = sold_d + own XI_{t−Ndel}`). That
is not D.3/E.1. Host now routes XI along row-normalised international T*.
D.30 CES still does not ration quantities (P4). Not a world-price pin.

## Proposed extensions (not implemented)

E1 cross-crop substitution (≠ origin CES). E2 government restriction game
(≠ supplier oligopoly). Need user approval before code.
