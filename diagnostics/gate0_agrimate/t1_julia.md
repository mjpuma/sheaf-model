# T1 — Obtain-or-leave author Julia (inspect D.22 / solver)

Inspect-only. **Not copied** into `sheaf/agrimate/`. **Not a freeze.**
Not a pin. Not L1–L8. Not an αI retune. G1/G2 stay blocked.
`wheat_params()` stay αI=3.2, ζ=0,
N_for=3, p_sto=0.1, xmin=0.2.

## Obtain

| source | what | SHA / DOI | `*.jl` | copied into sheaf? |
|---|---|---|---:|---|
| GitLab paper repo | `https://gitlab.pik-potsdam.de/agrimate/agrimate` | `f2de96551857` (2023-02-05) | 41 | **no** |
| Zenodo 14022004 wheat | `/tmp/agrimate-model.zip` `agrimate-equal-sales-penalty` | `799511113ea1`; https://doi.org/10.5281/zenodo.14022004 | 32 | **no** |
| this checkout | `sheaf/agrimate/` | — | 0 | — |

Zenodo record fetch was **403** this run. The equal-sales-penalty zip
already on disk (2026-09-16 retrieval) was unpacked under `/tmp` and
inspected. GitLab clone is the public 2021–23 paper tree (no
`two_markets`). Wheat executable is **14022004** (`two_markets=true`,
α_foreign=3.2, ζ=0, τ_exp=0.5 yr, N_hor=N_year, N_for=3).

## Verification protocol (CLAUDE.md)

1. **Claim.** Host D.22 (`model.py`): `q_oth = max(XI*_world − XI*_r, 1e-9)`;
   each step `q_oth ← (1−w_exp) q_oth + w_exp · realized_oth` with
   `w_exp = 1/(τ_exp N_year)` unless `freeze_q_oth`. Supplier plan is
   scipy L-BFGS-B on the fraction map (`optimize.py`). Author wheat
   still updates D.22; freeze is a host diagnostic, not a copy.

2. **Implementation.** Host: `AgrimateSim.run` `sheaf/agrimate/model.py` (init ~263, update ~347–349); `solve_supplier_plan` `sheaf/agrimate/optimize.py` (`method="L-BFGS-B"`,
   `plan_maxiter=40`). Author wheat: `src/AgrimateModel/src/agents/producer.jl` `communication_step!` (two_markets branch);
   `src/AgrimateModel/src/agents/producer_optimization.jl` `optimize_sales_NLopt_two_markets` (`:LD_SLSQP`).

3. **Match (partial).** EMA *weight* matches: author converts
   `τ_exp = 0.5 * N_year` then uses `1/τ_exp`; host uses
   `w_exp = 1/(0.5 * 24) = 1/12`. Jacobi timing matches: all
   `sales_step!` then all `communication_step!` (host: all plans then
   one `q_oth` update). `two_markets=true`, α_foreign=3.2, ζ=0,
   N_for=3, N_hor=N_year. **No `freeze` in author Julia** (0 matches
   in 14022004 `producer.jl`).

4. **Counterexample (sourced D.22 delta).** Author wheat keeps a
   **horizon vector** `expected_others_sales_foreign` (length N_hor).
   Observation is other producers' **planned** foreign sales
   `optimal_sales_foreign[3:end]` (not current-step realized XI).
   Update is a **shift+EMA**:
   `new[1:N_hor-1] = (1/τ_exp)·obs + (1−1/τ_exp)·old[2:N_hor]`;
   `new[end] = mean(new[1:N_hor-1])`. Host tiles a **scalar**
   `q_oth[r]` across the year and blends **current-step**
   `sold_i.sum() − sold_i`. Same weight, different state and
   different observation. GitLab one-market D.22 is the older
   total-sales vector (α=5, τ_exp=0.2, N_hor=2 N_year); not the
   wheat path.

5. **Counterexample (sourced solver delta).** Author wheat:
   NLopt `:LD_SLSQP`, `xtol_abs`, `maxtime=60`, current `x1`
   **fixed** to demand requests, availability inequality, optional
   S_end equality. Host: scipy L-BFGS-B on `(fd, fi) ∈ [0,1]^{2N}`,
   current sales **free**, `S ≥ 0` identically, `plan_maxiter=40`,
   no S_end equality. Unconverged L-BFGS-B (N5) is a host-solver
   fact, not an author SLSQP status.

6. **Correctness / do not adopt freeze.** Author still *updates*
   D.22. `τ_exp == 0` is instantaneous replacement by the new plan,
   not a freeze at `XI*_world − XI*_r`. `freeze_q_oth` is absent from
   `AgrimateParams`. Adopting the host freeze would still be a new
   law. Do not copy Julia. Do not raise `plan_maxiter`. Do not pin.

7. **Change this session.** None to economics. Label the obtain and
   the sourced deltas. Next paste **T2** (write the delta; still do
   not implement unless the author wheat path does that — it does
   not freeze).

## Sourced vs host (wheat path)

| object | 14022004 wheat | host |
|---|---|---|
| D.22 state | vector length N_hor | scalar per region, tiled |
| D.22 observation | planned `optimal_sales_foreign[3:end]` | realized XI this step |
| D.22 update | shift + EMA; last slot = mean | scalar EMA |
| D.22 weight | 1/(0.5 N_year) = 1/12 | 1/(0.5 N_year) = 1/12 |
| freeze | **absent** | diagnostic `freeze_q_oth=False` |
| IBR timing | Jacobi (sales then communicate) | Jacobi |
| solver | NLopt LD_SLSQP | scipy L-BFGS-B |
| current x1 | fixed to demand | free in the plan |
| S_end | equality (both-markets) | S ≥ 0 only |
| last/first (item 3) | author Fig. 4 **1.004** | host **1.444** |

G0-P item 3 remains **fail**. Do not start G1/G2.

**Next paste: T2.** Sourced D.22 and solver deltas exist. Label only.
Do not copy Julia into `sheaf/agrimate/`. Do not write `freeze_q_oth`
into `wheat_params()`.

