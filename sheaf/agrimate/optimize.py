"""Constrained supplier plan (D.11–D.21) and Nash IBR (D.50–D.55, δ=ρ=0)."""
from __future__ import annotations

import numpy as np
from scipy.optimize import minimize

from .equations import inverse_demand
from .params import AgrimateParams


def apply_expected_restriction(xi: np.ndarray, delta_hat: np.ndarray) -> np.ndarray:
    return np.asarray(xi, float) * (1.0 - np.clip(delta_hat, 0.0, 1.0))


def _storage_path(S0: float, H: np.ndarray, xd: np.ndarray, xi: np.ndarray,
                  loss: float) -> np.ndarray:
    n = len(H)
    S = np.empty(n)
    s = S0
    for t in range(n):
        s = (1.0 - loss) * s + H[t] - xd[t] - xi[t]
        S[t] = s
    return S


def solve_supplier_plan(
        H: np.ndarray,
        S0: float,
        xi_others: np.ndarray,
        xi_star_step: np.ndarray,
        xd_star_step: np.ndarray,
        alpha_i: float,
        alpha_d: float,
        params: AgrimateParams,
        delta_hat: np.ndarray | None = None,
        x0: np.ndarray | None = None,
        ) -> dict:
    """Maximise supplier profit over (XD, XI) subject to storage ≥ 0.

    Returns planned sales, storage path, success flag. Failed solves are
    reported; the last feasible projection is returned rather than a legacy rule.
    """
    n = int(H.size)
    H = np.asarray(H, float)
    xi_star_step = np.broadcast_to(np.asarray(xi_star_step, float), (n,))
    xd_star_step = np.broadcast_to(np.asarray(xd_star_step, float), (n,))
    if delta_hat is None:
        delta_hat = np.zeros(n)
    delta_hat = np.clip(np.asarray(delta_hat, float), 0.0, 1.0)

    def unpack(z):
        xd = np.maximum(z[:n], 0.0)
        xi = np.maximum(z[n:], 0.0) * (1.0 - delta_hat)
        return xd, xi

    def objective(z):
        xd, xi = unpack(z)
        S = _storage_path(S0, H, xd, xi, params.delta_loss)
        if np.any(S < -1e-8):
            return 1e12
        q_i = (xi + xi_others) / np.maximum(xi_star_step, 1e-8)
        q_d = xd / np.maximum(xd_star_step, 1e-8)
        p_i = inverse_demand(q_i, alpha_i, params.lam_demand, params.demand_arg_floor)
        p_d = inverse_demand(q_d, alpha_d, params.lam_demand, params.demand_arg_floor)
        rev = float(np.dot(p_i, xi) + np.dot(p_d, xd))
        # storage cost ζ0 (S/S*)^2 ; S* ~ mean harvest
        s_star = max(float(H.mean()), 1e-8)
        cost = params.zeta0 * float(np.mean((np.maximum(S, 0.0) / s_star) ** 2))
        return -(rev - cost)

    tot = float(H.sum() + max(S0, 0.0))
    if x0 is None:
        x0 = np.concatenate([np.maximum(xd_star_step, 0.0), np.maximum(xi_star_step, 0.0)])
        if x0.sum() <= 0:
            x0 = np.full(2 * n, tot / max(2 * n, 1))
    bounds = [(params.xmin, None)] * (2 * n)
    res = minimize(objective, x0, method="L-BFGS-B", bounds=bounds,
                   options={"maxiter": params.plan_maxiter, "ftol": 1e-8})
    xd, xi = unpack(res.x)
    S = _storage_path(S0, H, xd, xi, params.delta_loss)
    feasible = bool(np.all(np.isfinite(S)) and np.min(S) >= -1e-6)
    # If infeasible, project: scale sales so storage stays non-negative.
    fallback = False
    if not feasible:
        fallback = True
        scale = 0.5
        xd, xi = unpack(res.x) if np.all(np.isfinite(res.x)) else (x0[:n], x0[n:])
        for _ in range(8):
            S = _storage_path(S0, H, xd, xi, params.delta_loss)
            if np.min(S) >= -1e-8:
                feasible = True
                break
            xd *= scale
            xi *= scale
    success = bool(np.all(np.isfinite(xd)) and feasible)
    return {
        "xd": xd,
        "xi": xi,
        "S": S,
        "success": success,
        "fallback": fallback,
        "nfev": int(getattr(res, "nfev", 0)),
    }


def nash_ibr(H_star: np.ndarray,
             alpha_d: np.ndarray,
             xi_star_step: np.ndarray,
             xd_star_step: np.ndarray,
             params: AgrimateParams,
             ) -> dict:
    """δ=ρ=0 Nash init (D.17–D.18): annual sales equal harvest.

    IBR with storage cost is a refinement; the closed form is the quantity
    identity used to initialise the dynamic run.
    """
    n_r, n_y = H_star.shape
    xi_star_step = np.broadcast_to(np.asarray(xi_star_step, float), (n_r,))
    xd_star_step = np.broadcast_to(np.asarray(xd_star_step, float), (n_r,))
    tot = np.maximum(xi_star_step + xd_star_step, 1e-12)
    share_i = xi_star_step / tot
    xd = H_star * (1.0 - share_i)[:, None]
    xi = H_star * share_i[:, None]
    sales = xd + xi
    rel = np.abs(sales.sum(axis=1) - H_star.sum(axis=1)) / np.maximum(H_star.sum(axis=1), 1e-12)
    return {
        "xd": xd,
        "xi": xi,
        "sales": sales,
        "iterations": 0,
        "err": float(np.max(rel)),
        "success": bool(np.max(rel) < 1e-12),
    }
