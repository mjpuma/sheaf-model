"""P5: compare default unconverged plans to a tighter L-BFGS-B solve.

Does not retune economics. Does not drop unconverged from the host count.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from sheaf.agrimate import model as agr_model
from sheaf.agrimate.model import run_agrimate
from sheaf.agrimate.optimize import (
    fractions_to_sales,
    solve_supplier_plan,
)
from sheaf.agrimate.params import AgrimateParams
from sheaf.agrimate.wheat_data import prepare_wheat

OUT = Path("diagnostics/gate0_agrimate")
N_SAMPLE = 80
RNG = np.random.default_rng(5)


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
        "pidx_last": float(p[-1]),
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
        "mean_abs_pidx": float(np.mean(np.abs(d))),
        "corr_pidx": float(np.corrcoef(pa, pb)[0, 1]) if pa.size > 1 else 1.0,
        "max_abs_xi": float(np.max(np.abs(xi_a - xi_b))),
        "rmse_xi": float(np.sqrt(np.mean((xi_a - xi_b) ** 2))),
    }


def _capture_unconverged(data, params: AgrimateParams):
    snaps = []
    orig = agr_model.solve_supplier_plan

    def wrapped(H, S0, others, xi_star, xd_star, alpha_i, alpha_d, p,
                delta_hat=None, x0=None):
        sol = orig(H, S0, others, xi_star, xd_star, alpha_i, alpha_d, p,
                   delta_hat=delta_hat, x0=x0)
        if sol["success"] and (not sol["fallback"]) and (not sol["converged"]):
            snaps.append({
                "H": np.asarray(H, float).copy(),
                "S0": float(S0),
                "others": np.asarray(others, float).copy(),
                "xi_star": np.asarray(xi_star, float).copy(),
                "xd_star": np.asarray(xd_star, float).copy(),
                "alpha_i": float(alpha_i),
                "alpha_d": float(alpha_d),
                "delta_hat": None if delta_hat is None else np.asarray(delta_hat, float).copy(),
                "x0": None if x0 is None else np.asarray(x0, float).copy(),
                "xi0": float(sol["xi_ship"][0]),
                "xd0": float(sol["xd"][0]),
                "obj": float(sol["obj"]),
                "pgnorm": float(sol["pgnorm"]),
                "nit": int(sol["nit"]),
                "status": int(sol["status"]),
                "message": sol["message"],
                "nfev": int(sol["nfev"]),
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


def _mid_x0(snap, params: AgrimateParams) -> np.ndarray:
    n = snap["H"].size
    dhat = np.zeros(n) if snap["delta_hat"] is None else snap["delta_hat"]
    xd, xi, _, _ = fractions_to_sales(
        np.full(n, 0.5), np.full(n, 0.5), snap["S0"], snap["H"],
        params.delta_loss, dhat,
    )
    return np.concatenate([xd, xi])


def _star_x0(snap) -> np.ndarray:
    n = snap["H"].size
    xd = np.broadcast_to(np.asarray(snap["xd_star"], float), (n,)).copy()
    xi = np.broadcast_to(np.asarray(snap["xi_star"], float), (n,)).copy()
    return np.concatenate([xd, xi])


def _resolve(snap, params: AgrimateParams, x0: np.ndarray | None):
    return solve_supplier_plan(
        snap["H"], snap["S0"], snap["others"], snap["xi_star"], snap["xd_star"],
        snap["alpha_i"], snap["alpha_d"], params,
        delta_hat=snap["delta_hat"], x0=x0,
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    data = prepare_wheat(2003, 2011)
    p_def = AgrimateParams()
    p_tight = AgrimateParams(plan_maxiter=400)

    res_def, snaps = _capture_unconverged(data, p_def)
    res_tight = run_agrimate(
        data, use_restrictions=True, use_anomalies=True,
        start_year=2003, end_year=2011, params=p_tight,
    )

    messages: dict[str, int] = {}
    statuses: dict[str, int] = {}
    nits = []
    pgnorms = []
    for s in snaps:
        messages[s["message"]] = messages.get(s["message"], 0) + 1
        statuses[str(s["status"])] = statuses.get(str(s["status"]), 0) + 1
        nits.append(s["nit"])
        pgnorms.append(s["pgnorm"])

    n_take = min(N_SAMPLE, len(snaps))
    idx = RNG.choice(len(snaps), size=n_take, replace=False) if n_take else np.array([], int)
    sample = [snaps[int(i)] for i in idx]

    rows = []
    for snap in sample:
        same = _resolve(snap, p_tight, snap["x0"])
        mid = _resolve(snap, p_tight, _mid_x0(snap, p_def))
        star = _resolve(snap, p_tight, _star_x0(snap))
        rows.append({
            "xi0_def": snap["xi0"],
            "obj_def": snap["obj"],
            "pgnorm_def": snap["pgnorm"],
            "nit_def": snap["nit"],
            "status_def": snap["status"],
            "xi0_tight": float(same["xi_ship"][0]),
            "obj_tight": float(same["obj"]),
            "pgnorm_tight": float(same["pgnorm"]),
            "nit_tight": int(same["nit"]),
            "converged_tight": bool(same["converged"]),
            "dxi0_tight": abs(float(same["xi_ship"][0]) - snap["xi0"]),
            "dobj_tight": float(same["obj"]) - snap["obj"],
            "xi0_mid": float(mid["xi_ship"][0]),
            "dxi0_mid": abs(float(mid["xi_ship"][0]) - snap["xi0"]),
            "xi0_star": float(star["xi_ship"][0]),
            "dxi0_star": abs(float(star["xi_ship"][0]) - snap["xi0"]),
        })

    dxi_tight = np.array([r["dxi0_tight"] for r in rows], float) if rows else np.zeros(0)
    dobj = np.array([r["dobj_tight"] for r in rows], float) if rows else np.zeros(0)
    dxi_mid = np.array([r["dxi0_mid"] for r in rows], float) if rows else np.zeros(0)
    dxi_star = np.array([r["dxi0_star"] for r in rows], float) if rows else np.zeros(0)
    pgn_t = np.array([r["pgnorm_tight"] for r in rows], float) if rows else np.zeros(0)
    n_conv = int(sum(1 for r in rows if r["converged_tight"]))

    report = {
        "default": _summarize(res_def),
        "tight_maxiter_400": _summarize(res_tight),
        "path_default_vs_tight": _price_delta(res_def, res_tight),
        "unconverged_messages": messages,
        "unconverged_status": statuses,
        "unconverged_nit_median": float(np.median(nits)) if nits else None,
        "unconverged_nit_max": int(np.max(nits)) if nits else None,
        "unconverged_pgnorm_median": float(np.median(pgnorms)) if pgnorms else None,
        "unconverged_pgnorm_p90": float(np.quantile(pgnorms, 0.9)) if pgnorms else None,
        "sample_n": n_take,
        "sample_tight_converged": n_conv,
        "sample_max_abs_dxi0_same_start": float(np.max(dxi_tight)) if dxi_tight.size else None,
        "sample_median_abs_dxi0_same_start": float(np.median(dxi_tight)) if dxi_tight.size else None,
        "sample_max_dobj_same_start": float(np.max(dobj)) if dobj.size else None,
        "sample_min_dobj_same_start": float(np.min(dobj)) if dobj.size else None,
        "sample_median_pgnorm_tight": float(np.median(pgn_t)) if pgn_t.size else None,
        "sample_max_abs_dxi0_mid_start": float(np.max(dxi_mid)) if dxi_mid.size else None,
        "sample_max_abs_dxi0_star_start": float(np.max(dxi_star)) if dxi_star.size else None,
        "default_plan_maxiter": p_def.plan_maxiter,
    }
    path = OUT / "solver_probe.json"
    path.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
