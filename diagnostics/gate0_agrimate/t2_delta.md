# T2 — Sourced D.22 / solver delta (label only)

T1 obtained 14022004 wheat Julia. This note writes the delta
(equation, file, line). **Not implemented.** Not a freeze. Not a
pin. Not L1–L8. Not an αI retune. Do not copy Julia.
`wheat_params()` stay αI=3.2, ζ=0,
N_for=3. G1/G2 stay blocked.

Author citations are the 14022004 `agrimate-equal-sales-penalty`
tree inspected under `/tmp` (T1; zip `79951111`). GitLab 2023
paper repo is the older one-market path and is **not** the wheat
executable.

## Verification protocol (CLAUDE.md)

1. **Claim.** Host D.22 is the rivals' expected international
   sales used in D.7 (`model.py` comment at 262). Author wheat
   still *updates* expectations (`communication_step!`). R4 freeze
   is a host diagnostic, not Agrimate. Supplier plan is D.11–D.21
   on the fraction map (`optimize.py`).

2. **Implementation (host).**
   - Init: `q_oth = max(XI*_world − XI*_r, 1e-9)` (`model.py` 263).
   - Weight: `w_exp = 1/(τ_exp N_year)` (`model.py` 264);
     `τ_exp=0.5` (`params.py` 28) ⇒ `w_exp=1/12`.
   - Horizon: `others = full(N_year, q_oth[r])` (`model.py` 287).
   - Observation: `realized_oth = max(Σ sold_i − sold_i, 0)` (`model.py` 347).
   - Update: `q_oth ← (1−w_exp) q_oth + w_exp realized_oth` unless `freeze_q_oth` (`model.py` 348–349).
   - Solver: `minimize(..., method="L-BFGS-B", jac=True, bounds=[(0,1)]^{2N}, maxiter=plan_maxiter)` (`optimize.py` 256–258). Current `xd, xi` are decision variables
     (`fractions_to_sales`, `optimize.py` 22–55, 207–219).

3. **Implementation (author wheat, `two_markets=true`).**
   - State: `expected_others_sales_foreign` length `N_hor`
     (`src/AgrimateModel/src/agents/producer.jl` 130, 160–161, 452–464).
   - Observation: `Σ_{s≠r} optimal_sales_foreign[3:end]`
     (`src/AgrimateModel/src/agents/producer.jl` 454–455) — *planned future foreign sales*,
     not current-step realized XI.
   - Update (τ_exp ≠ 0), with τ_exp already in **steps**
     (`src/AgrimateModel/src/AgrimateModel.jl` 110: `τ_exp = τ_exp_years * N_year`):

     $$Q^{\mathrm{new}}_{1:N_{\mathrm{hor}}-1} = \tfrac{1}{\tau_{\exp}} Q^{\mathrm{obs}} + \left(1-\tfrac{1}{\tau_{\exp}}\right) Q^{\mathrm{old}}_{2:N_{\mathrm{hor}}}$$

     $$Q^{\mathrm{new}}_{N_{\mathrm{hor}}} = \mathrm{mean}(Q^{\mathrm{new}}_{1:N_{\mathrm{hor}}-1})$$

     (`src/AgrimateModel/src/agents/producer.jl` 461–464).
   - Jacobi timing: all `sales_step!` then all
     `communication_step!` (`src/AgrimateModel/src/model.jl` 60–75).
   - Current x1 **fixed** to demand:
     `X1_dom = min(D_dom, H+S)`, `X1_for = min(D_for, H+S−X1_dom)`
     (`src/AgrimateModel/src/agents/producer.jl` 116–117); optimizer comments `# x1 is fixed`,
     `N = N_hor`, `n = 2:N_hor+1` (`src/AgrimateModel/src/agents/producer_optimization.jl` 68–72).
   - Algorithm: `optimizer_algorithm = :LD_SLSQP`, `maxtime=60`,
     `xtol_abs=tol` (`src/AgrimateModel/src/agents/producer_optimization.jl` 280, 353–355). Both-markets
     branch `Opt(..., 2N)` (`src/AgrimateModel/src/agents/producer_optimization.jl` 333–347).
   - `equal_constraint::Bool = false` (`AgrimateModel.jl` 51) so
     S_end equality is **off** on the wheat default (T1 said
     “optional”; T2 pins the default).

4. **Match.** EMA *weight* matches: both `1/(0.5 N_year)=1/12`.
   Jacobi timing matches. `two_markets=true`, α_foreign=3.2, ζ=0,
   N_hor=N_year, N_for=3. **No `freeze` in author Julia.**

5. **Counterexample (D.22).** Same `w_exp`, different *state* and
   *observation*. Author ages a horizon vector of planned foreign
   sales. Host blends a scalar of *this-step realized* XI and tiles
   it. `τ_exp==0` on the author path is instantaneous replacement
   by the new plan (`src/AgrimateModel/src/agents/producer.jl` 457–459), not a freeze at
   `XI*_world − XI*_r`. Host `freeze_q_oth` is absent from
   `AgrimateParams`.

6. **Correctness / do not implement this session.** Author wheat
   *does* the vector+shift and *does not* freeze. T2 is **label
   only** (`GATE0_CONTINUE.md`: “label sourced delta only”).
   Copying the Julia update into `model.py` would be a new host
   law in this prompt, not a freeze, and is out of scope. Do not
   switch to NLopt. Do not raise `plan_maxiter`. Do not pin 2006.
   Do not restore L1–L8. Host x1=demand remains the labelled R5
   hook (`x1_from_demand=False`).

7. **Change.** None to economics. Write this delta. Next paste
   **T3** (FAO-since-2005 + AgrimateEU28 still cannot-set).

## Sourced deltas (file:line)

| # | object | author wheat | host | class | adopt? |
|---|---|---|---|---|---|
| 1 | D.22 state | vector `N_hor` (`src/AgrimateModel/src/agents/producer.jl` 452–464) | scalar tiled (`model.py` 263, 287) | **D** | **no** |
| 2 | D.22 observation | planned `optimal_sales_foreign[3:end]` (454–455) | realized `Σ XI − XI_r` (`model.py` 347) | **D** | **no** |
| 3 | D.22 update | shift+EMA; last=mean (461–464) | scalar EMA (`model.py` 348–349) | **D** | **no** |
| 4 | D.22 weight | `1/τ_exp` after `τ_exp *= N_year` (`src/AgrimateModel/src/AgrimateModel.jl` 110) | `1/(τ_exp N_year)` (`model.py` 264) | **H** | already match |
| 5 | freeze | **absent** | diagnostic `freeze_q_oth=False` (`model.py` 177, 187, 348) | **H** | **no** (author does not) |
| 6 | IBR timing | sales then communicate (`src/AgrimateModel/src/model.jl` 60–75) | plan then `q_oth` update (`model.py` 285–349) | **H** | already Jacobi |
| 7 | solver | NLopt `:LD_SLSQP` (`src/AgrimateModel/src/agents/producer_optimization.jl` 280, 333–355) | scipy L-BFGS-B (`optimize.py` 256–258) | **C** | **no** (N5 cap stays 40) |
| 8 | current x1 | fixed to demand (`src/AgrimateModel/src/agents/producer.jl` 116–117; `src/AgrimateModel/src/agents/producer_optimization.jl` 68–72) | free in the fraction plan (`optimize.py` 22–55, 207–219) | **D** | already labelled R5; default off |
| 9 | S_end equality | `equal_constraint=false` (params 51) | `S ≥ 0` identically | **H** | wheat default has no S_end |

Confidence **95–100%** on rows 1–9 (direct inspection of the same
14022004 files T1 obtained). Item 3 last/first remains **1.444** vs
author **1.004**. Do not start G1/G2.

**Next paste: T3.** Delta labelled, not adopted. FAO-since-2005 +
AgrimateEU28+Egypt arrays still cannot-set. Do not copy Julia.
Do not write `freeze_q_oth` into `wheat_params()`.

