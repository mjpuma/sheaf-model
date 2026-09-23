"""R9: P5 unconverged count on the R2 Fig. 4 comparison object.

Short window 2006–08 harvest+AMIS. Labelled ``plan_maxiter`` probes do
**not** change ``wheat_params()`` or ``fig4_experiment_params()``
defaults. Does not restore L1–L8. Does not overwrite 2003–11
``solver.md`` / three-scenario CSVs.
"""
from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import numpy as np

from . import model as agr_model
from .fig4_config import PROTECTED_THREE_SCENARIO, apply_alpha_i
from .model import run_agrimate
from .params import AgrimateParams, fig4_experiment_params, wheat_params
from .validation import OUT_DEFAULT
from .wheat_data import prepare_wheat

START_YEAR = 2006
END_YEAR = 2008
ROOT = Path(__file__).resolve().parents[2]
DISPATCH = ROOT / "diagnostics" / "GATE0_REPRO_DISPATCH.md"


def _bucket(message: str) -> str:
    u = str(message).upper()
    if "ITERATION" in u and "LIMIT" in u:
        return "maxiter"
    if "ABNORMAL" in u:
        return "abnormal"
    return "other"


def _summarize(res) -> dict:
    p = np.asarray(res.price_index, float)
    return {
        "failed": int(res.failed_solves),
        "fallback": int(res.fallback_solves),
        "unconverged": int(res.unconverged_solves),
        "n_solves": int(len(res.regions) * res.price_index.size),
        "residual": float(res.plan_residual),
        "runtime_s": float(res.runtime_s),
        "pidx_min": float(np.min(p)),
        "pidx_max": float(np.max(p)),
        "pidx_mean": float(np.mean(p)),
    }


def _price_delta(a, b) -> dict:
    pa = np.asarray(a.price_index, float)
    pb = np.asarray(b.price_index, float)
    d = pa - pb
    xi_a = np.asarray(a.xi_ship, float)
    xi_b = np.asarray(b.xi_ship, float)
    return {
        "max_abs_pidx": float(np.max(np.abs(d))),
        "rmse_pidx": float(np.sqrt(np.mean(d ** 2))),
        "corr_pidx": float(np.corrcoef(pa, pb)[0, 1]) if pa.size > 1 else 1.0,
        "max_abs_xi": float(np.max(np.abs(xi_a - xi_b))),
    }


def capture_unconverged(data, params: AgrimateParams):
    """Run harvest+AMIS; record scipy status on feasible unconverged plans."""
    snaps = []
    orig = agr_model.solve_supplier_plan

    def wrapped(H, S0, others, xi_star, xd_star, alpha_i, alpha_d, p,
                delta_hat=None, x0=None, x1=None, xd_others=None):
        sol = orig(H, S0, others, xi_star, xd_star, alpha_i, alpha_d, p,
                   delta_hat=delta_hat, x0=x0, x1=x1, xd_others=xd_others)
        if sol["success"] and (not sol["fallback"]) and (not sol["converged"]):
            snaps.append({
                "nit": int(sol["nit"]),
                "status": int(sol["status"]),
                "message": str(sol["message"]),
                "pgnorm": float(sol["pgnorm"]),
            })
        return sol

    agr_model.solve_supplier_plan = wrapped
    try:
        res = run_agrimate(
            data, use_restrictions=True, use_anomalies=True,
            start_year=data.start_year, end_year=data.end_year, params=params,
        )
    finally:
        agr_model.solve_supplier_plan = orig
    return res, snaps


def _snap_stats(snaps: list[dict]) -> dict:
    messages: dict[str, int] = {}
    statuses: dict[str, int] = {}
    buckets = {"maxiter": 0, "abnormal": 0, "other": 0}
    nits = []
    pgnorms = []
    for s in snaps:
        messages[s["message"]] = messages.get(s["message"], 0) + 1
        statuses[str(s["status"])] = statuses.get(str(s["status"]), 0) + 1
        buckets[_bucket(s["message"])] += 1
        nits.append(s["nit"])
        pgnorms.append(s["pgnorm"])
    return {
        "n_snaps": len(snaps),
        "messages": messages,
        "status": statuses,
        "buckets": buckets,
        "nit_median": float(np.median(nits)) if nits else None,
        "nit_max": int(np.max(nits)) if nits else None,
        "pgnorm_median": float(np.median(pgnorms)) if pgnorms else None,
        "pgnorm_p90": float(np.quantile(pgnorms, 0.9)) if pgnorms else None,
    }


def _pack(res, snaps: list[dict], params: AgrimateParams) -> dict:
    out = _summarize(res)
    out.update(_snap_stats(snaps))
    out["plan_maxiter"] = int(params.plan_maxiter)
    out["alpha_i"] = float(params.alpha_i)
    out["zeta_penalty"] = float(params.zeta_penalty)
    out["n_for_months"] = int(params.n_for_months)
    return out


def run_fig4_solver_probe(
    start_year: int = START_YEAR,
    end_year: int = END_YEAR,
) -> tuple[dict, dict]:
    """Default vs Fig. 4 knobs at 40; labelled 200/400 probes on knobs only."""
    default = wheat_params()
    knobs = fig4_experiment_params()
    if default.plan_maxiter != 40 or knobs.plan_maxiter != 40:
        raise RuntimeError("R9 must not find a raised default plan_maxiter")
    data = prepare_wheat(start_year=start_year, end_year=end_year, params=default)
    data_default = apply_alpha_i(data, default.alpha_i)
    data_knobs = apply_alpha_i(data, knobs.alpha_i)

    results = {}
    packed = {}
    for name, params, wheat in (
        ("default_40", default, data_default),
        ("knobs_40", knobs, data_knobs),
        ("knobs_200", replace(knobs, plan_maxiter=200), data_knobs),
        ("knobs_400", replace(knobs, plan_maxiter=400), data_knobs),
    ):
        res, snaps = capture_unconverged(wheat, params)
        results[name] = res
        packed[name] = _pack(res, snaps, params)

    report = {
        "window": [start_year, end_year],
        "scenario": "harvest_amis",
        "n_regions": len(data.regions),
        "default_plan_maxiter": int(wheat_params().plan_maxiter),
        "fig4_plan_maxiter": int(fig4_experiment_params().plan_maxiter),
        "wheat_params_alpha_i": float(wheat_params().alpha_i),
        "runs": packed,
        "knobs_40_vs_200": _price_delta(results["knobs_40"], results["knobs_200"]),
        "knobs_40_vs_400": _price_delta(results["knobs_40"], results["knobs_400"]),
        "knobs_200_vs_400": _price_delta(results["knobs_200"], results["knobs_400"]),
        "decision": "leave plan_maxiter=40",
        "adopted_fig4_knobs": False,
    }
    return report, results


def _fmt(x, nd: int = 3) -> str:
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "nan"
    return f"{float(x):.{nd}f}"


def write_solver_fig4_note(report: dict, out_dir: Path) -> Path:
    d40 = report["runs"]["default_40"]
    k40 = report["runs"]["knobs_40"]
    k200 = report["runs"]["knobs_200"]
    k400 = report["runs"]["knobs_400"]
    vs200 = report["knobs_40_vs_200"]
    vs400 = report["knobs_40_vs_400"]
    vs24 = report["knobs_200_vs_400"]
    y0, y1 = report["window"]
    lines = [
        "# R9 — Unconverged plans on the Fig. 4 comparison object",
        "",
        "Repeat of P5 (`solver.md`) on `fig4_experiment_params()`",
        f"harvest+AMIS **{y0}–{y1}** (short window; USDA 27-node).",
        "**Not a retune.** `wheat_params()` stay αI=3.2, ζ=0, N_for=3,",
        "`plan_maxiter=40`. Fig. 4 knobs are not adopted. L1–L8 stay",
        "rejected. Unforced price is not pinned. G1/G2 stay blocked.",
        "",
        "Failed = infeasible (`success=False`). Fallback = non-finite",
        "or infeasible `res.x`, replaced by the start. Unconverged =",
        "feasible accepted plan with scipy L-BFGS-B `success=False`.",
        "Counted separately. Not dropped.",
        "",
        "## Failed vs unconverged vs maxiter",
        "",
        "| label | maxiter | failed | fallback | unconverged | maxiter-hit | ABNORMAL | n_solves |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for key, lab in (
        ("default_40", "default (ζ=0)"),
        ("knobs_40", "fig4 knobs (ζ=1)"),
        ("knobs_200", "fig4 knobs probe"),
        ("knobs_400", "fig4 knobs probe"),
    ):
        r = report["runs"][key]
        b = r["buckets"]
        lines.append(
            f"| {lab} | {int(r['plan_maxiter'])} | {int(r['failed'])} | "
            f"{int(r['fallback'])} | {int(r['unconverged'])}/"
            f"{int(r['n_solves'])} | {int(b['maxiter'])} | "
            f"{int(b['abnormal'])} | {int(r['n_solves'])} |"
        )
    lines += [
        "",
        f"Default 40: unconverged {int(d40['unconverged'])}/{int(d40['n_solves'])}, "
        f"failed={int(d40['failed'])}, fallback={int(d40['fallback'])}, "
        f"residual={_fmt(d40['residual'], 0)}; buckets maxiter="
        f"{int(d40['buckets']['maxiter'])}, ABNORMAL="
        f"{int(d40['buckets']['abnormal'])}.",
        f"Knobs 40: unconverged {int(k40['unconverged'])}/{int(k40['n_solves'])}, "
        f"failed={int(k40['failed'])}, fallback={int(k40['fallback'])}; "
        f"maxiter-hit {int(k40['buckets']['maxiter'])}, ABNORMAL "
        f"{int(k40['buckets']['abnormal'])}. "
        f"Median nit={_fmt(k40['nit_median'], 0)}; pgnorm median "
        f"{_fmt(k40['pgnorm_median'], 1)}.",
        "",
        "P5 on 2003–11 wheat defaults was 1743/5832 (maxiter 1033 +",
        "ABNORMAL 710). This short-window Fig. 4 object is a different",
        "path (ζ=1 turns the xmin quadratic **off**). ABNORMAL here is",
        "evidence about that kink, not a reason to raise the default cap.",
        "",
        "## Does a tighter cap unique the knobs path?",
        "",
        "| maxiter | unconverged | pidx mean | vs 40 RMSE p | vs 40 max \\|Δp\\| | vs 40 max \\|ΔXI\\| |",
        "|---:|---:|---:|---:|---:|---:|",
        f"| 40 | {int(k40['unconverged'])} | {_fmt(k40['pidx_mean'], 3)} | 0 | 0 | 0 |",
        f"| 200 | {int(k200['unconverged'])} | {_fmt(k200['pidx_mean'], 3)} | "
        f"{_fmt(vs200['rmse_pidx'], 3)} | {_fmt(vs200['max_abs_pidx'], 3)} | "
        f"{_fmt(vs200['max_abs_xi'], 1)} |",
        f"| 400 | {int(k400['unconverged'])} | {_fmt(k400['pidx_mean'], 3)} | "
        f"{_fmt(vs400['rmse_pidx'], 3)} | {_fmt(vs400['max_abs_pidx'], 3)} | "
        f"{_fmt(vs400['max_abs_xi'], 1)} |",
        "",
        f"200 vs 400: RMSE p={_fmt(vs24['rmse_pidx'], 3)}, "
        f"max \\|Δp\\|={_fmt(vs24['max_abs_pidx'], 3)}, "
        f"corr={_fmt(vs24['corr_pidx'], 3)}.",
        "",
        "**Leave `plan_maxiter=40`.** Raising it on the comparison object",
        "moves p_w without a unique stationary point to adopt. Do not",
        "change `wheat_params().plan_maxiter`. Do not paper over with",
        "L1–L8. Do not adopt Fig. 4 knobs.",
        "",
        "Classification **C** (N5 on this object). Not a 2006 pin.",
        "",
        "**Next paste: R4.** Item 3 / XI split is still open. R9 does not",
        "unlock G1.",
        "",
    ]
    path = out_dir / "solver_fig4.md"
    path.write_text("\n".join(lines))
    return path


def write_r9_dispatch(report: dict, path: Path | None = None) -> Path:
    path = Path(path) if path else DISPATCH
    k40 = report["runs"]["knobs_40"]
    d40 = report["runs"]["default_40"]
    b = k40["buckets"]
    body = "\n".join([
        "# Gate 0 reproduction dispatch",
        "",
        "Living next-paste. Rewrite after every R-session from **that run’s",
        "numbers**. Do not walk R3…R12 in order. Template:",
        "`GATE0_REPRO_PROMPTS.md` (Adaptive rule).",
        "",
        "```",
        "Last completed: R9",
        "Window / scenario: 2006–08 harvest+AMIS fig4_knobs N5 (P5 repeat)",
        "hike_2008 (default → knobs → author): ×2.31 → ×2.22 → ×1.62",
        "moy max/min: 26.8× → 13.3× → 1.51×",
        "undisturbed last/first: 0.618 → 0.409 → 1.006",
        f"unconverged / failed: knobs {int(k40['unconverged'])}/"
        f"{int(k40['n_solves'])} failed={int(k40['failed'])} "
        f"(maxiter {int(b['maxiter'])}, ABNORMAL {int(b['abnormal'])}); "
        f"default {int(d40['unconverged'])}/{int(d40['n_solves'])}",
        "What you could set / could not set: N5 on αI=3.5/ζ=1/N_for=6; remaining A7",
        "Next paste: R4",
        "Why: plan_maxiter stays 40; knobs unconverged still counted; item 3 next",
        "Skip: R11; G1/G2; do not raise maxiter; do not adopt knobs",
        "```",
    ])
    path.write_text(body + "\n")
    return path


def run_fig4_solver_score(out_dir: Path | None = None) -> dict[str, Path]:
    out_dir = Path(out_dir) if out_dir else OUT_DEFAULT
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in PROTECTED_THREE_SCENARIO:
        assert (out_dir / name).is_file(), name
    before = {name: (out_dir / name).read_bytes() for name in PROTECTED_THREE_SCENARIO}
    report, _results = run_fig4_solver_probe()
    js = out_dir / "solver_fig4.json"
    js.write_text(json.dumps(report, indent=2) + "\n")
    note = write_solver_fig4_note(report, out_dir)
    dispatch = write_r9_dispatch(report)
    after = {name: (out_dir / name).read_bytes() for name in PROTECTED_THREE_SCENARIO}
    assert before == after, "R9 must not overwrite 2003–11 three-scenario CSVs"
    assert wheat_params().plan_maxiter == 40
    assert fig4_experiment_params().plan_maxiter == 40
    return {"note": note, "json": js, "dispatch": dispatch}
