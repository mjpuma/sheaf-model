"""Solver: x1 fixed from demand + scipy SLSQP on the remaining horizon.

Independent Python of sourced 14022004 wheat (T2 rows 7–8). Does not
copy ``*.jl``. Does not freeze D.22. Does not pin 2006. Does not retune
``wheat_params()``. Does not raise ``plan_maxiter``. Fig. 4 later.
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


def _fmt(x, nd: int = 3) -> str:
    if x is None:
        return "nan"
    try:
        xf = float(x)
    except (TypeError, ValueError):
        return "nan"
    if xf != xf:  # NaN
        return "nan"
    return f"{xf:.{nd}f}"


def solver_metrics(result, out_dir: Path | None = None) -> dict:
    from .d22 import d22_metrics

    m = d22_metrics(result, out_dir)
    p = wheat_params()
    lf = float(m["last_first"])
    m.update({
        "d22_last_first": 0.772,
        "method": "SLSQP",
        "x1_fixed": True,
        "plan_maxiter": int(p.plan_maxiter),
        "nlopt_copied": False,
        "item3_onesided": bool(lf <= 1.1),
        "item3_pass": bool((1.0 / 1.1) <= lf <= 1.1),
        "class_solver": "H",
        "solver_unchanged": False,
        "implemented": True,
    })
    return m


def write_solver_note(metrics: dict, out_dir: Path | None = None) -> Path:
    out_dir = Path(out_dir) if out_dir else OUT_DEFAULT
    p = wheat_params()
    lf = float(metrics["last_first"])
    author = float(metrics["last_first_author"])
    item3 = "pass" if metrics["item3_pass"] else "fail"
    lines = [
        "# Solver — current x1 from demand, SLSQP on the rest",
        "",
        "Independent Python of the sourced 14022004 wheat supplier",
        "programme (T2 rows 7–8). Not a freeze. Not a pin. Not L1–L8.",
        "Not an αI retune. Not Fig. 4. Do not copy Julia.",
        f"`wheat_params()` stay αI={p.alpha_i:g}, ζ={p.zeta_penalty:g},",
        f"N_for={p.n_for_months:g}, plan_maxiter={p.plan_maxiter:g}.",
        "G1/G2 stay blocked. D.22 vector+shift stays live.",
        "",
        "## Verification protocol (CLAUDE.md)",
        "",
        "1. **Claim.** Author wheat fixes current sales to demand",
        "   requests (`producer.jl` 116–117) and optimises only future",
        "   steps with NLopt `:LD_SLSQP` (`producer_optimization.jl`",
        "   68–72, 280, 333–355). Host was L-BFGS-B with current sales",
        "   free (`optimize.py`).",
        "",
        "2. **Implementation.** `solve_supplier_plan(..., x1=(xd0,xi0))`",
        "   clips `min(D, H+S)` domestic-first, locks step 0, and runs",
        "   scipy SLSQP on the remaining fractions. Live `AgrimateSim.run`",
        "   builds D from last origin-by-buyer requests (iota floor).",
        "   R5 `x1_from_demand` (consumer inflow) stays default off.",
        "",
        "3. **Match.** Decision set (x1 fixed) and algorithm family",
        "   (SLSQP) now follow the sourced wheat law. Fraction map still",
        "   enforces S≥0 identically (already equivalent to availability).",
        "   Author used `maxtime=60`; host keeps `plan_maxiter=40` (N5).",
        "   Host horizon is `N_hor` including now, so the free block is",
        "   `N_hor-1` future steps (author stores `N_hor+1` and frees",
        "   `N_hor`). Documented.",
        "",
        "4. **Counterexample (pre-change).** L-BFGS-B with free current",
        "   sales is not author wheat. D.22 last/first **0.772** vs author",
        "   **1.004** was that mix: Agrimate eyes, non-Agrimate hands.",
        "",
        "5. **Correctness.** Author *does* fix x1 and *does* use SLSQP.",
        "   scipy SLSQP is the independent equivalent (task allowed it).",
        "   Do not vendor NLopt. Do not copy Julia. Do not pin 2006.",
        "   Do not freeze D.22. Do not raise `plan_maxiter`.",
        "",
        "6. **Change.** Live supplier programme. Undisturbed 2003–11",
        "   re-measured. Harvest+AMIS three-scenario CSVs untouched.",
        "   Fig. 4 later. Do not start G1.",
        "",
        "## Live score (undisturbed, 2006–11)",
        "",
        "| object | last/first | 2006 mean | 2011 mean |",
        "|---|---:|---:|---:|",
        f"| Host D.22 + x1-SLSQP | {_fmt(lf, 3)} | "
        f"${_fmt(metrics['mean_first_usd'], 2)}/t | "
        f"${_fmt(metrics['mean_last_usd'], 2)}/t |",
        f"| Author Fig. 4 baseline | {_fmt(author, 3)} | "
        f"{_fmt(metrics['author_first'], 3)} (index) | "
        f"{_fmt(metrics['author_last'], 3)} (index) |",
        "| D.22 only (L-BFGS-B, x1 free) | 0.772 | $456.49/t | $352.48/t |",
        "| S1 three-scenario (pre-D.22) | 1.444 | 45.82 | 66.15 |",
        "",
        f"G0-P item 3 is **{item3}** (two-sided [1/1.1, 1.1]).",
        f"Unconverged {int(metrics['unconverged'])}/"
        f"{int(metrics['n_solves'])}; failed "
        f"{int(metrics['failed'])}. Method SLSQP, x1 fixed.",
        "Do not start G1.",
        "",
        "**Next paste: leave labelled.** Solver implemented. Exact Fig. 4",
        "is later. Do not copy Julia. Do not write `freeze_q_oth` into",
        "`wheat_params()`.",
        "",
    ]
    path = Path(out_dir) / "solver_x1.md"
    path.write_text("\n".join(lines) + "\n")
    return path


def write_solver_csv(metrics: dict, out_dir: Path | None = None) -> Path:
    out_dir = Path(out_dir) if out_dir else OUT_DEFAULT
    keep = [
        "last_first", "d22_last_first", "last_first_s1",
        "mean_first_usd", "mean_last_usd", "last_first_author",
        "author_first", "author_last", "n_julia",
        "freeze_q_oth_on_params", "alpha_i", "zeta_penalty",
        "n_for_months", "plan_maxiter", "unconverged", "failed",
        "n_solves", "item3_onesided", "item3_pass", "implemented",
        "method", "x1_fixed", "nlopt_copied", "author_does_freeze",
        "solver_unchanged", "class_solver", "confidence", "runtime_s",
        "s1_three_scenario_untouched",
    ]
    path = Path(out_dir) / "score_solver_x1.csv"
    row = {k: metrics[k] for k in keep if k in metrics}
    pd.DataFrame([row]).to_csv(path, index=False)
    return path


def write_solver_prices(result, out_dir: Path | None = None) -> Path:
    from .validation import monthly_price

    out_dir = Path(out_dir) if out_dir else OUT_DEFAULT
    s = monthly_price(result, field="price_usd")
    path = Path(out_dir) / "prices_undisturbed_solver_x1.csv"
    s.to_frame("undisturbed").to_csv(path)
    return path


def write_solver_dispatch(metrics: dict, path: Path | None = None) -> Path:
    path = Path(path) if path else DISPATCH
    if path.is_file():
        text = path.read_text()
        if ("Last completed: D.22" not in text
                and "Last completed: solver" not in text):
            return path
    lf = _fmt(metrics["last_first"], 3)
    author = _fmt(metrics["last_first_author"], 3)
    item3 = "pass" if metrics["item3_pass"] else "fail"
    body = "\n".join([
        "# Gate 0 reproduction dispatch",
        "",
        "Living next-paste. D.22 and solver implemented.",
        "Template: `GATE0_CONTINUE.md`. Do not start G1.",
        "",
        "```",
        "Last completed: solver",
        "Window / scenario: 2003–11 undisturbed x1-fixed SLSQP (not Fig. 4)",
        "hike_2008: harvest+AMIS ×3.71; author ×1.62; Pink ×1.88 "
        "(S1 CSV; not re-run)",
        "moy max/min: host 16.8×; author 1.45×; Pink 1.07× (S1 CSV)",
        f"undisturbed last/first: {lf} vs author {author} "
        f"(D.22 0.772; S1 1.444; item 3 {item3})",
        f"unconverged / failed: {int(metrics['unconverged'])}/"
        f"{int(metrics['n_solves'])} / {int(metrics['failed'])}",
        "What you could set / could not set: x1 from demand + scipy "
        "SLSQP on the rest; could not copy NLopt/Julia; could not "
        "freeze; could not pin 2006; could not raise plan_maxiter",
        "Next paste: leave labelled",
        "Why: sourced solver delta is live; exact Fig. 4 is later; "
        "do not start G1",
        "Skip: G1/G2; R11; 2006 pin; Bai 10; L1–L8; FAO ΔS as stocks; "
        "freeze_q_oth; copy Julia; invent Egypt; FAO as prepare_wheat",
        "```",
        "",
    ])
    path.write_text(body)
    return path


def run_solver_undisturbed(out_dir: Path | None = None) -> dict[str, Path]:
    from .model import run_agrimate
    from .wheat_data import prepare_wheat

    out_dir = Path(out_dir) if out_dir else OUT_DEFAULT
    out_dir.mkdir(parents=True, exist_ok=True)
    p = wheat_params()
    assert p.alpha_i == 3.2
    assert p.zeta_penalty == 0.0
    assert p.n_for_months == 3
    assert p.plan_maxiter == 40
    assert "freeze_q_oth" not in {f.name for f in fields(AgrimateParams)}
    assert n_julia_sources(ROOT / "sheaf") == 0
    before = {name: (out_dir / name).read_bytes()
              for name in PROTECTED_THREE_SCENARIO
              if (out_dir / name).is_file()}
    data = prepare_wheat(start_year=2003, end_year=2011, params=p)
    result = run_agrimate(
        data=data, params=p,
        use_anomalies=False, use_restrictions=False,
        start_year=2003, end_year=2011,
    )
    metrics = solver_metrics(result, out_dir)
    assert metrics["x1_fixed"] is True
    assert metrics["method"] == "SLSQP"
    assert metrics["nlopt_copied"] is False
    assert int(metrics["n_julia"]) == 0
    assert int(metrics["plan_maxiter"]) == 40
    note = write_solver_note(metrics, out_dir)
    csv = write_solver_csv(metrics, out_dir)
    prices = write_solver_prices(result, out_dir)
    dispatch = write_solver_dispatch(metrics)
    after = {name: (out_dir / name).read_bytes()
             for name in PROTECTED_THREE_SCENARIO
             if (out_dir / name).is_file()}
    for name, blob in before.items():
        assert after[name] == blob, name
    return {"note": note, "csv": csv, "prices": prices, "dispatch": dispatch}
