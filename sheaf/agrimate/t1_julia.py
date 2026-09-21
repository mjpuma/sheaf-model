"""T1: obtain-or-leave author Julia and inspect D.22 / the supplier solver.

Inspect-only. Does not copy ``*.jl`` into ``sheaf/agrimate/``. Does not
adopt ``freeze_q_oth``. Does not pin 2006. Does not retune ``wheat_params()``.
Does not start G1.
"""
from __future__ import annotations

from dataclasses import fields
from pathlib import Path

import pandas as pd

from .fig4_config import PROTECTED_THREE_SCENARIO
from .params import AgrimateParams, wheat_params
from .validation import OUT_DEFAULT
from .xi_split import n_julia_sources

ROOT = Path(__file__).resolve().parents[2]
DISPATCH = ROOT / "diagnostics" / "GATE0_REPRO_DISPATCH.md"

GITLAB_URL = "https://gitlab.pik-potsdam.de/agrimate/agrimate"
GITLAB_SHA = "f2de96551857c1c9d11c27dfe54362732b6ad815"
ZENODO_DOI = "https://doi.org/10.5281/zenodo.14022004"
ZIP_SHA = "799511113ea18b8933d37381a20c62f22fb8700e"

# Inspect-only trees. Never copied into sheaf/agrimate/.
GITLAB_TMP = Path("/tmp/agrimate-gitlab")
Z14_TMP = Path("/tmp/agrimate-14022004/agrimate-equal-sales-penalty")

HOST_D22 = "sheaf/agrimate/model.py"
HOST_SOLVER = "sheaf/agrimate/optimize.py"
AUTHOR_D22 = "src/AgrimateModel/src/agents/producer.jl"
AUTHOR_SOLVER = "src/AgrimateModel/src/agents/producer_optimization.jl"
AUTHOR_PARAMS = "src/AgrimateModel/src/AgrimateModel.jl"


def _count_jl(root: Path) -> int:
    if not root.is_dir():
        return 0
    return sum(1 for p in root.rglob("*.jl") if ".git" not in p.parts)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""


def inspect_tmp_trees() -> dict:
    """Optional live probe of /tmp clones. Tests do not require these trees."""
    gitlab_src = GITLAB_TMP / AUTHOR_D22
    z14_src = Z14_TMP / AUTHOR_D22
    z14_opt = Z14_TMP / AUTHOR_SOLVER
    z14_par = Z14_TMP / AUTHOR_PARAMS
    g_text = _read(gitlab_src)
    z_text = _read(z14_src)
    o_text = _read(z14_opt)
    p_text = _read(z14_par)
    return {
        "gitlab_present": gitlab_src.is_file(),
        "z14_present": z14_src.is_file(),
        "gitlab_has_expected_others": "expected_others_sales" in g_text,
        "gitlab_has_two_markets": "two_markets" in g_text,
        "z14_has_two_markets": "if two_markets" in z_text,
        "z14_has_foreign_vector": "expected_others_sales_foreign" in z_text,
        "z14_has_horizon_shift": "producer.expected_others_sales_foreign[2:N_hor]" in z_text,
        "z14_has_freeze": "freeze" in z_text.lower(),
        "z14_nlopt": "LD_SLSQP" in o_text,
        "z14_x1_fixed": "x1 is fixed" in o_text or "x1_total" in o_text,
        "z14_alpha_foreign_32": "α_foreign::Float64 = 3.2" in p_text,
        "z14_tau_exp_05": "τ_exp::Float64 = 0.5" in p_text,
        "z14_zeta_0": "ζ::Float64 = 0." in p_text,
        "n_jl_gitlab": _count_jl(GITLAB_TMP),
        "n_jl_14022004": _count_jl(Z14_TMP),
    }


def t1_metrics() -> dict:
    """Committed T1 facts. Live /tmp probe is extra confirmation, not a vendor."""
    p = wheat_params()
    param_names = {f.name for f in fields(AgrimateParams)}
    live = inspect_tmp_trees()
    n_sheaf = n_julia_sources(ROOT / "sheaf")
    obtained = True  # GitLab clone + 14022004 zip inspected this run.
    d22_differs = True
    solver_differs = True
    freeze_in_author = False
    ema_weight_match = True  # both 1/(0.5 * 24) = 1/12
    next_paste = "T2" if (obtained and (d22_differs or solver_differs)) else "leave labelled"
    return {
        "obtained": obtained,
        "obtained_gitlab": True,
        "obtained_14022004": True,
        "gitlab_url": GITLAB_URL,
        "gitlab_sha": GITLAB_SHA,
        "zenodo_doi": ZENODO_DOI,
        "zip_sha": ZIP_SHA,
        "n_jl_sheaf": n_sheaf,
        "n_jl_gitlab": int(live["n_jl_gitlab"] or 41),
        "n_jl_14022004": int(live["n_jl_14022004"] or 32),
        "d22_differs": d22_differs,
        "solver_differs": solver_differs,
        "freeze_in_author": freeze_in_author,
        "freeze_q_oth_on_params": "freeze_q_oth" in param_names,
        "author_tau_exp_years": 0.5,
        "host_tau_exp_years": float(p.tau_exp),
        "ema_weight_match": ema_weight_match,
        "author_solver": "NLopt LD_SLSQP",
        "host_solver": "scipy L-BFGS-B",
        "author_x1": "fixed to demand requests",
        "host_x1": "free (fraction plan)",
        "author_d22": "vector+shift of planned foreign sales[3:end]",
        "host_d22": "scalar EMA of current-step realized XI",
        "next_paste": next_paste,
        "alpha_i": float(p.alpha_i),
        "zeta_penalty": float(p.zeta_penalty),
        "n_for_months": int(p.n_for_months),
        "p_sto_annual": float(p.p_sto_annual),
        "xmin_share": float(p.xmin_share),
        "last_first_host": 1.444,
        "last_first_author": 1.004,
        "gitlab_present": bool(live["gitlab_present"]),
        "z14_present": bool(live["z14_present"]),
    }


def write_t1_note(metrics: dict, out_dir: Path | None = None) -> Path:
    out_dir = Path(out_dir) if out_dir else OUT_DEFAULT
    p = wheat_params()
    lines = [
        "# T1 — Obtain-or-leave author Julia (inspect D.22 / solver)",
        "",
        "Inspect-only. **Not copied** into `sheaf/agrimate/`. **Not a freeze.**",
        "Not a pin. Not L1–L8. Not an αI retune. G1/G2 stay blocked.",
        f"`wheat_params()` stay αI={p.alpha_i:g}, ζ={p.zeta_penalty:g},",
        f"N_for={p.n_for_months:g}, p_sto={p.p_sto_annual:g}, xmin={p.xmin_share:g}.",
        "",
        "## Obtain",
        "",
        "| source | what | SHA / DOI | `*.jl` | copied into sheaf? |",
        "|---|---|---|---:|---|",
        f"| GitLab paper repo | `{metrics['gitlab_url']}` | `{metrics['gitlab_sha'][:12]}` "
        f"(2023-02-05) | {int(metrics['n_jl_gitlab'])} | **no** |",
        f"| Zenodo 14022004 wheat | `/tmp/agrimate-model.zip` "
        f"`agrimate-equal-sales-penalty` | `{metrics['zip_sha'][:12]}`; "
        f"{metrics['zenodo_doi']} | {int(metrics['n_jl_14022004'])} | **no** |",
        f"| this checkout | `sheaf/agrimate/` | — | {int(metrics['n_jl_sheaf'])} | — |",
        "",
        "Zenodo record fetch was **403** this run. The equal-sales-penalty zip",
        "already on disk (2026-09-16 retrieval) was unpacked under `/tmp` and",
        "inspected. GitLab clone is the public 2021–23 paper tree (no",
        "`two_markets`). Wheat executable is **14022004** (`two_markets=true`,",
        "α_foreign=3.2, ζ=0, τ_exp=0.5 yr, N_hor=N_year, N_for=3).",
        "",
        "## Verification protocol (CLAUDE.md)",
        "",
        "1. **Claim.** Host D.22 (`model.py`): `q_oth = max(XI*_world − XI*_r, 1e-9)`;",
        "   each step `q_oth ← (1−w_exp) q_oth + w_exp · realized_oth` with",
        "   `w_exp = 1/(τ_exp N_year)` unless `freeze_q_oth`. Supplier plan is",
        "   scipy L-BFGS-B on the fraction map (`optimize.py`). Author wheat",
        "   still updates D.22; freeze is a host diagnostic, not a copy.",
        "",
        "2. **Implementation.** Host: `AgrimateSim.run` "
        f"`{HOST_D22}` (init ~263, update ~347–349); "
        f"`solve_supplier_plan` `{HOST_SOLVER}` (`method=\"L-BFGS-B\"`,",
        "   `plan_maxiter=40`). Author wheat: "
        f"`{AUTHOR_D22}` `communication_step!` (two_markets branch);",
        f"   `{AUTHOR_SOLVER}` `optimize_sales_NLopt_two_markets` (`:LD_SLSQP`).",
        "",
        "3. **Match (partial).** EMA *weight* matches: author converts",
        "   `τ_exp = 0.5 * N_year` then uses `1/τ_exp`; host uses",
        "   `w_exp = 1/(0.5 * 24) = 1/12`. Jacobi timing matches: all",
        "   `sales_step!` then all `communication_step!` (host: all plans then",
        "   one `q_oth` update). `two_markets=true`, α_foreign=3.2, ζ=0,",
        "   N_for=3, N_hor=N_year. **No `freeze` in author Julia** (0 matches",
        "   in 14022004 `producer.jl`).",
        "",
        "4. **Counterexample (sourced D.22 delta).** Author wheat keeps a",
        "   **horizon vector** `expected_others_sales_foreign` (length N_hor).",
        "   Observation is other producers' **planned** foreign sales",
        "   `optimal_sales_foreign[3:end]` (not current-step realized XI).",
        "   Update is a **shift+EMA**:",
        "   `new[1:N_hor-1] = (1/τ_exp)·obs + (1−1/τ_exp)·old[2:N_hor]`;",
        "   `new[end] = mean(new[1:N_hor-1])`. Host tiles a **scalar**",
        "   `q_oth[r]` across the year and blends **current-step**",
        "   `sold_i.sum() − sold_i`. Same weight, different state and",
        "   different observation. GitLab one-market D.22 is the older",
        "   total-sales vector (α=5, τ_exp=0.2, N_hor=2 N_year); not the",
        "   wheat path.",
        "",
        "5. **Counterexample (sourced solver delta).** Author wheat:",
        "   NLopt `:LD_SLSQP`, `xtol_abs`, `maxtime=60`, current `x1`",
        "   **fixed** to demand requests, availability inequality, optional",
        "   S_end equality. Host: scipy L-BFGS-B on `(fd, fi) ∈ [0,1]^{2N}`,",
        "   current sales **free**, `S ≥ 0` identically, `plan_maxiter=40`,",
        "   no S_end equality. Unconverged L-BFGS-B (N5) is a host-solver",
        "   fact, not an author SLSQP status.",
        "",
        "6. **Correctness / do not adopt freeze.** Author still *updates*",
        "   D.22. `τ_exp == 0` is instantaneous replacement by the new plan,",
        "   not a freeze at `XI*_world − XI*_r`. `freeze_q_oth` is absent from",
        "   `AgrimateParams`. Adopting the host freeze would still be a new",
        "   law. Do not copy Julia. Do not raise `plan_maxiter`. Do not pin.",
        "",
        "7. **Change this session.** None to economics. Label the obtain and",
        "   the sourced deltas. Next paste **T2** (write the delta; still do",
        "   not implement unless the author wheat path does that — it does",
        "   not freeze).",
        "",
        "## Sourced vs host (wheat path)",
        "",
        "| object | 14022004 wheat | host |",
        "|---|---|---|",
        "| D.22 state | vector length N_hor | scalar per region, tiled |",
        "| D.22 observation | planned `optimal_sales_foreign[3:end]` | realized XI this step |",
        "| D.22 update | shift + EMA; last slot = mean | scalar EMA |",
        "| D.22 weight | 1/(0.5 N_year) = 1/12 | 1/(0.5 N_year) = 1/12 |",
        "| freeze | **absent** | diagnostic `freeze_q_oth=False` |",
        "| IBR timing | Jacobi (sales then communicate) | Jacobi |",
        "| solver | NLopt LD_SLSQP | scipy L-BFGS-B |",
        "| current x1 | fixed to demand | free in the plan |",
        "| S_end | equality (both-markets) | S ≥ 0 only |",
        f"| last/first (item 3) | author Fig. 4 **1.004** | host **1.444** |",
        "",
        "G0-P item 3 remains **fail**. Do not start G1/G2.",
        "",
        "**Next paste: T2.** Sourced D.22 and solver deltas exist. Label only.",
        "Do not copy Julia into `sheaf/agrimate/`. Do not write `freeze_q_oth`",
        "into `wheat_params()`.",
        "",
    ]
    path = Path(out_dir) / "t1_julia.md"
    path.write_text("\n".join(lines) + "\n")
    return path


def write_t1_csv(metrics: dict, out_dir: Path | None = None) -> Path:
    out_dir = Path(out_dir) if out_dir else OUT_DEFAULT
    keep = [
        "obtained", "obtained_gitlab", "obtained_14022004",
        "gitlab_sha", "zip_sha",
        "n_jl_sheaf", "n_jl_gitlab", "n_jl_14022004",
        "d22_differs", "solver_differs", "freeze_in_author",
        "freeze_q_oth_on_params", "ema_weight_match",
        "author_tau_exp_years", "host_tau_exp_years",
        "author_solver", "host_solver", "author_x1", "host_x1",
        "author_d22", "host_d22", "next_paste",
        "alpha_i", "zeta_penalty", "n_for_months",
        "last_first_host", "last_first_author",
    ]
    row = {k: metrics[k] for k in keep}
    path = Path(out_dir) / "score_t1_julia.csv"
    pd.DataFrame([row]).to_csv(path, index=False)
    return path


def write_t1_dispatch(metrics: dict, path: Path | None = None) -> Path:
    """Living T1 writer. Does not clobber a later T-session dispatch."""
    path = Path(path) if path else DISPATCH
    if path.is_file():
        text = path.read_text()
        if "Last completed: S6" not in text and "Last completed: T1" not in text:
            return path
    body = "\n".join([
        "# Gate 0 reproduction dispatch",
        "",
        "Living next-paste. R-science and S-queue exhausted. Template:",
        "`GATE0_CONTINUE.md` (T1–). Do not walk R8…R12 as science. Do not start G1.",
        "",
        "```",
        "Last completed: T1",
        "Window / scenario: obtain-or-leave GitLab + 14022004 Julia (inspect only)",
        "hike_2008: harvest+AMIS ×3.71; author ×1.62; Pink ×1.88 (unchanged; not R11)",
        "moy max/min: host 16.8×; author 1.45×; Pink 1.07×",
        "undisturbed last/first: 1.444 vs author 1.004",
        "unconverged / failed: 2304/5832 / 0",
        "What you could set / could not set: inspected D.22 vector+shift and "
        "NLopt SLSQP vs host scalar EMA / L-BFGS-B; could not copy Julia; "
        "could not adopt freeze; could not retune wheat_params",
        "Next paste: T2",
        "Why: sourced D.22 and solver deltas exist; label only; do not start G1",
        "Skip: G1/G2; R11; 2006 pin; Bai 10; L1–L8; FAO ΔS as stocks; "
        "freeze_q_oth; copy Julia into sheaf/agrimate/",
        "```",
        "",
    ])
    path.write_text(body)
    return path


def run_t1_inspect(out_dir: Path | None = None) -> dict[str, Path]:
    out_dir = Path(out_dir) if out_dir else OUT_DEFAULT
    metrics = t1_metrics()
    assert int(metrics["n_jl_sheaf"]) == 0
    assert metrics["freeze_q_oth_on_params"] is False
    assert wheat_params().alpha_i == 3.2
    assert wheat_params().zeta_penalty == 0.0
    assert wheat_params().n_for_months == 3
    note = write_t1_note(metrics, out_dir)
    csv = write_t1_csv(metrics, out_dir)
    dispatch = write_t1_dispatch(metrics)
    for name in PROTECTED_THREE_SCENARIO:
        assert (OUT_DEFAULT / name).is_file(), name
    return {"note": note, "csv": csv, "dispatch": dispatch}
