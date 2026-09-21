"""T2: label sourced D.22 / supplier-programme delta from T1 Julia.

Does not implement the vector+shift, a freeze, a pin, or a solver switch.
Does not copy ``*.jl`` into ``sheaf/agrimate/``. Does not retune
``wheat_params()``. Does not start G1.
"""
from __future__ import annotations

from dataclasses import fields
from pathlib import Path

import pandas as pd

from .fig4_config import PROTECTED_THREE_SCENARIO
from .params import AgrimateParams, wheat_params
from .t1_julia import t1_metrics
from .validation import OUT_DEFAULT
from .xi_split import n_julia_sources

ROOT = Path(__file__).resolve().parents[2]
DISPATCH = ROOT / "diagnostics" / "GATE0_REPRO_DISPATCH.md"

# Author wheat (Zenodo 14022004 equal-sales-penalty). Cited, not copied.
AUTHOR_D22 = "src/AgrimateModel/src/agents/producer.jl"
AUTHOR_SOLVER = "src/AgrimateModel/src/agents/producer_optimization.jl"
AUTHOR_PARAMS = "src/AgrimateModel/src/AgrimateModel.jl"
AUTHOR_STEP = "src/AgrimateModel/src/model.jl"


def t2_metrics() -> dict:
    t1 = t1_metrics()
    p = wheat_params()
    param_names = {f.name for f in fields(AgrimateParams)}
    implemented = False  # T2 is label-only.
    author_does_freeze = False
    next_paste = "T3"  # FAO-since-2005 + EU28 still cannot-set.
    return {
        "t1_obtained": bool(t1["obtained"]),
        "d22_differs": bool(t1["d22_differs"]),
        "solver_differs": bool(t1["solver_differs"]),
        "implemented": implemented,
        "author_does_freeze": author_does_freeze,
        "freeze_q_oth_on_params": "freeze_q_oth" in param_names,
        "n_jl_sheaf": n_julia_sources(ROOT / "sheaf"),
        "ema_weight_match": bool(t1["ema_weight_match"]),
        "author_d22_file": AUTHOR_D22,
        "author_d22_lines": "452-464",
        "host_d22_file": "sheaf/agrimate/model.py",
        "host_d22_lines": "262-264,287,347-349",
        "author_solver_file": AUTHOR_SOLVER,
        "author_solver_lines": "68-72,280,333-355",
        "host_solver_file": "sheaf/agrimate/optimize.py",
        "host_solver_lines": "207-258",
        "author_x1_lines": f"{AUTHOR_D22}:116-117 + {AUTHOR_SOLVER}:68-72",
        "equal_constraint_default": False,
        "class_d22": "D",
        "class_solver": "C",
        "class_freeze": "H",
        "confidence": "95-100",
        "next_paste": next_paste,
        "alpha_i": float(p.alpha_i),
        "zeta_penalty": float(p.zeta_penalty),
        "n_for_months": int(p.n_for_months),
        "last_first_host": 1.444,
        "last_first_author": 1.004,
    }


def write_t2_note(metrics: dict, out_dir: Path | None = None) -> Path:
    out_dir = Path(out_dir) if out_dir else OUT_DEFAULT
    p = wheat_params()
    lines = [
        "# T2 — Sourced D.22 / solver delta (label only)",
        "",
        "T1 obtained 14022004 wheat Julia. This note writes the delta",
        "(equation, file, line). **Not implemented.** Not a freeze. Not a",
        "pin. Not L1–L8. Not an αI retune. Do not copy Julia.",
        f"`wheat_params()` stay αI={p.alpha_i:g}, ζ={p.zeta_penalty:g},",
        f"N_for={p.n_for_months:g}. G1/G2 stay blocked.",
        "",
        "Author citations are the 14022004 `agrimate-equal-sales-penalty`",
        "tree inspected under `/tmp` (T1; zip `79951111`). GitLab 2023",
        "paper repo is the older one-market path and is **not** the wheat",
        "executable.",
        "",
        "## Verification protocol (CLAUDE.md)",
        "",
        "1. **Claim.** Host D.22 is the rivals' expected international",
        "   sales used in D.7 (`model.py` comment at 262). Author wheat",
        "   still *updates* expectations (`communication_step!`). R4 freeze",
        "   is a host diagnostic, not Agrimate. Supplier plan is D.11–D.21",
        "   on the fraction map (`optimize.py`).",
        "",
        "2. **Implementation (host).**",
        "   - Init: `q_oth = max(XI*_world − XI*_r, 1e-9)` "
        "(`model.py` 263).",
        "   - Weight: `w_exp = 1/(τ_exp N_year)` (`model.py` 264);",
        "     `τ_exp=0.5` (`params.py` 28) ⇒ `w_exp=1/12`.",
        "   - Horizon: `others = full(N_year, q_oth[r])` (`model.py` 287).",
        "   - Observation: `realized_oth = max(Σ sold_i − sold_i, 0)` "
        "(`model.py` 347).",
        "   - Update: `q_oth ← (1−w_exp) q_oth + w_exp realized_oth` "
        "unless `freeze_q_oth` (`model.py` 348–349).",
        "   - Solver: `minimize(..., method=\"L-BFGS-B\", jac=True, "
        "bounds=[(0,1)]^{2N}, maxiter=plan_maxiter)` "
        "(`optimize.py` 256–258). Current `xd, xi` are decision variables",
        "     (`fractions_to_sales`, `optimize.py` 22–55, 207–219).",
        "",
        "3. **Implementation (author wheat, `two_markets=true`).**",
        "   - State: `expected_others_sales_foreign` length `N_hor`",
        f"     (`{AUTHOR_D22}` 130, 160–161, 452–464).",
        "   - Observation: `Σ_{s≠r} optimal_sales_foreign[3:end]`",
        f"     (`{AUTHOR_D22}` 454–455) — *planned future foreign sales*,",
        "     not current-step realized XI.",
        "   - Update (τ_exp ≠ 0), with τ_exp already in **steps**",
        f"     (`{AUTHOR_PARAMS}` 110: `τ_exp = τ_exp_years * N_year`):",
        "",
        "     $$Q^{\\mathrm{new}}_{1:N_{\\mathrm{hor}}-1} = "
        "\\tfrac{1}{\\tau_{\\exp}} Q^{\\mathrm{obs}} + "
        "\\left(1-\\tfrac{1}{\\tau_{\\exp}}\\right) "
        "Q^{\\mathrm{old}}_{2:N_{\\mathrm{hor}}}$$",
        "",
        "     $$Q^{\\mathrm{new}}_{N_{\\mathrm{hor}}} = "
        "\\mathrm{mean}(Q^{\\mathrm{new}}_{1:N_{\\mathrm{hor}}-1})$$",
        "",
        f"     (`{AUTHOR_D22}` 461–464).",
        "   - Jacobi timing: all `sales_step!` then all",
        f"     `communication_step!` (`{AUTHOR_STEP}` 60–75).",
        "   - Current x1 **fixed** to demand:",
        f"     `X1_dom = min(D_dom, H+S)`, `X1_for = min(D_for, H+S−X1_dom)`",
        f"     (`{AUTHOR_D22}` 116–117); optimizer comments `# x1 is fixed`,",
        f"     `N = N_hor`, `n = 2:N_hor+1` (`{AUTHOR_SOLVER}` 68–72).",
        "   - Algorithm: `optimizer_algorithm = :LD_SLSQP`, `maxtime=60`,",
        f"     `xtol_abs=tol` (`{AUTHOR_SOLVER}` 280, 353–355). Both-markets",
        f"     branch `Opt(..., 2N)` (`{AUTHOR_SOLVER}` 333–347).",
        "   - `equal_constraint::Bool = false` (`AgrimateModel.jl` 51) so",
        "     S_end equality is **off** on the wheat default (T1 said",
        "     “optional”; T2 pins the default).",
        "",
        "4. **Match.** EMA *weight* matches: both `1/(0.5 N_year)=1/12`.",
        "   Jacobi timing matches. `two_markets=true`, α_foreign=3.2, ζ=0,",
        "   N_hor=N_year, N_for=3. **No `freeze` in author Julia.**",
        "",
        "5. **Counterexample (D.22).** Same `w_exp`, different *state* and",
        "   *observation*. Author ages a horizon vector of planned foreign",
        "   sales. Host blends a scalar of *this-step realized* XI and tiles",
        "   it. `τ_exp==0` on the author path is instantaneous replacement",
        f"   by the new plan (`{AUTHOR_D22}` 457–459), not a freeze at",
        "   `XI*_world − XI*_r`. Host `freeze_q_oth` is absent from",
        "   `AgrimateParams`.",
        "",
        "6. **Correctness / do not implement this session.** Author wheat",
        "   *does* the vector+shift and *does not* freeze. T2 is **label",
        "   only** (`GATE0_CONTINUE.md`: “label sourced delta only”).",
        "   Copying the Julia update into `model.py` would be a new host",
        "   law in this prompt, not a freeze, and is out of scope. Do not",
        "   switch to NLopt. Do not raise `plan_maxiter`. Do not pin 2006.",
        "   Do not restore L1–L8. Host x1=demand remains the labelled R5",
        "   hook (`x1_from_demand=False`).",
        "",
        "7. **Change.** None to economics. Write this delta. Next paste",
        "   **T3** (FAO-since-2005 + AgrimateEU28 still cannot-set).",
        "",
        "## Sourced deltas (file:line)",
        "",
        "| # | object | author wheat | host | class | adopt? |",
        "|---|---|---|---|---|---|",
        "| 1 | D.22 state | vector `N_hor` "
        f"(`{AUTHOR_D22}` 452–464) | scalar tiled "
        "(`model.py` 263, 287) | **D** | **no** |",
        "| 2 | D.22 observation | planned "
        "`optimal_sales_foreign[3:end]` (454–455) | realized "
        "`Σ XI − XI_r` (`model.py` 347) | **D** | **no** |",
        "| 3 | D.22 update | shift+EMA; last=mean (461–464) | scalar EMA "
        "(`model.py` 348–349) | **D** | **no** |",
        "| 4 | D.22 weight | `1/τ_exp` after `τ_exp *= N_year` "
        f"(`{AUTHOR_PARAMS}` 110) | `1/(τ_exp N_year)` "
        "(`model.py` 264) | **H** | already match |",
        "| 5 | freeze | **absent** | diagnostic `freeze_q_oth=False` "
        "(`model.py` 177, 187, 348) | **H** | **no** (author does not) |",
        "| 6 | IBR timing | sales then communicate "
        f"(`{AUTHOR_STEP}` 60–75) | plan then `q_oth` update "
        "(`model.py` 285–349) | **H** | already Jacobi |",
        "| 7 | solver | NLopt `:LD_SLSQP` "
        f"(`{AUTHOR_SOLVER}` 280, 333–355) | scipy L-BFGS-B "
        "(`optimize.py` 256–258) | **C** | **no** (N5 cap stays 40) |",
        "| 8 | current x1 | fixed to demand "
        f"(`{AUTHOR_D22}` 116–117; `{AUTHOR_SOLVER}` 68–72) | free in "
        "the fraction plan (`optimize.py` 22–55, 207–219) | **D** | "
        "already labelled R5; default off |",
        "| 9 | S_end equality | `equal_constraint=false` (params 51) | "
        "`S ≥ 0` identically | **H** | wheat default has no S_end |",
        "",
        "Confidence **95–100%** on rows 1–9 (direct inspection of the same",
        "14022004 files T1 obtained). Item 3 last/first remains **1.444** vs",
        "author **1.004**. Do not start G1/G2.",
        "",
        "**Next paste: T3.** Delta labelled, not adopted. FAO-since-2005 +",
        "AgrimateEU28+Egypt arrays still cannot-set. Do not copy Julia.",
        "Do not write `freeze_q_oth` into `wheat_params()`.",
        "",
    ]
    path = Path(out_dir) / "t2_delta.md"
    path.write_text("\n".join(lines) + "\n")
    return path


def write_t2_csv(metrics: dict, out_dir: Path | None = None) -> Path:
    out_dir = Path(out_dir) if out_dir else OUT_DEFAULT
    keep = [
        "t1_obtained", "d22_differs", "solver_differs", "implemented",
        "author_does_freeze", "freeze_q_oth_on_params", "n_jl_sheaf",
        "ema_weight_match", "author_d22_file", "author_d22_lines",
        "host_d22_file", "host_d22_lines",
        "author_solver_file", "author_solver_lines",
        "host_solver_file", "host_solver_lines",
        "equal_constraint_default", "class_d22", "class_solver",
        "class_freeze", "confidence", "next_paste",
        "alpha_i", "zeta_penalty", "n_for_months",
        "last_first_host", "last_first_author",
    ]
    path = Path(out_dir) / "score_t2_delta.csv"
    pd.DataFrame([{k: metrics[k] for k in keep}]).to_csv(path, index=False)
    return path


def write_t2_dispatch(metrics: dict, path: Path | None = None) -> Path:
    """Living T2 writer. Does not clobber a later T-session dispatch."""
    path = Path(path) if path else DISPATCH
    if path.is_file():
        text = path.read_text()
        if "Last completed: T1" not in text and "Last completed: T2" not in text:
            return path
    body = "\n".join([
        "# Gate 0 reproduction dispatch",
        "",
        "Living next-paste. R-science and S-queue exhausted. Template:",
        "`GATE0_CONTINUE.md` (T1–). Do not walk R8…R12 as science. Do not start G1.",
        "",
        "```",
        "Last completed: T2",
        "Window / scenario: sourced D.22 vector+shift and NLopt vs host "
        "(label only)",
        "hike_2008: harvest+AMIS ×3.71; author ×1.62; Pink ×1.88 "
        "(unchanged; not R11)",
        "moy max/min: host 16.8×; author 1.45×; Pink 1.07×",
        "undisturbed last/first: 1.444 vs author 1.004",
        "unconverged / failed: 2304/5832 / 0",
        "What you could set / could not set: wrote file:line D.22 and "
        "solver delta; could not implement vector+shift this session; "
        "could not freeze (author does not); could not copy Julia",
        "Next paste: T3",
        "Why: T2 labelled, not adopted; next is FAO/EU28 obtain-or-leave; "
        "do not start G1",
        "Skip: G1/G2; R11; 2006 pin; Bai 10; L1–L8; FAO ΔS as stocks; "
        "freeze_q_oth; copy Julia into sheaf/agrimate/",
        "```",
        "",
    ])
    path.write_text(body)
    return path


def run_t2_delta(out_dir: Path | None = None) -> dict[str, Path]:
    out_dir = Path(out_dir) if out_dir else OUT_DEFAULT
    metrics = t2_metrics()
    assert metrics["t1_obtained"] is True
    assert metrics["d22_differs"] is True
    assert metrics["implemented"] is False
    assert metrics["author_does_freeze"] is False
    assert int(metrics["n_jl_sheaf"]) == 0
    assert wheat_params().alpha_i == 3.2
    assert wheat_params().zeta_penalty == 0.0
    assert wheat_params().n_for_months == 3
    note = write_t2_note(metrics, out_dir)
    csv = write_t2_csv(metrics, out_dir)
    dispatch = write_t2_dispatch(metrics)
    for name in PROTECTED_THREE_SCENARIO:
        assert (OUT_DEFAULT / name).is_file(), name
    return {"note": note, "csv": csv, "dispatch": dispatch}
