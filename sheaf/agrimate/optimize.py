"""Constrained supplier plan (D.11–D.21) and Nash IBR (D.50–D.55, δ=ρ=0).

Decision variables are domestic/international *fractions* of step availability.
That is a mathematically equivalent representation of {XD ≥ 0, XI ≥ 0, S ≥ 0},
not an economic departure: every (fd, fi) ∈ [0, 1]^{2N} maps to a feasible
sales path, and every feasible sales path has a preimage (up to unused
fractions when availability is zero).
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import minimize

from .equations import inverse_demand
from .params import AgrimateParams


def apply_expected_restriction(xi: np.ndarray, delta_hat: np.ndarray) -> np.ndarray:
    return np.asarray(xi, float) * (1.0 - np.clip(delta_hat, 0.0, 1.0))


def fractions_to_sales(
        fd: np.ndarray,
        fi: np.ndarray,
        S0: float,
        H: np.ndarray,
        loss: float,
        delta_hat: np.ndarray,
        ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Map (fd, fi) ∈ [0, 1]^n to intended (xd, xi), shipped xi, and S ≥ 0.

    At step t, availability A = (1 − loss) S_{t−1} + H_t. Domestic sales take
    fd·A; intended international sales take fi of the remainder; shipped
    international sales are scaled by (1 − Δ̂) as in D.2/D.3. Storage uses
    shipped quantities, so S_t ≥ 0 identically.
    """
    n = int(H.size)
    fd = np.clip(np.asarray(fd, float), 0.0, 1.0)
    fi = np.clip(np.asarray(fi, float), 0.0, 1.0)
    delta_hat = np.clip(np.asarray(delta_hat, float), 0.0, 1.0)
    xd = np.empty(n)
    xi_int = np.empty(n)
    xi_ship = np.empty(n)
    S = np.empty(n)
    s = max(float(S0), 0.0)
    one_m_d = 1.0 - delta_hat
    for t in range(n):
        A = (1.0 - loss) * s + H[t]
        xd[t] = fd[t] * A
        rest = A - xd[t]
        xi_int[t] = fi[t] * rest
        xi_ship[t] = xi_int[t] * one_m_d[t]
        S[t] = rest - xi_ship[t]
        s = S[t]
    return xd, xi_int, xi_ship, S


def sales_to_fractions(
        xd: np.ndarray,
        xi: np.ndarray,
        S0: float,
        H: np.ndarray,
        loss: float,
        delta_hat: np.ndarray,
        ) -> tuple[np.ndarray, np.ndarray]:
    """Project intended sales onto [0, 1] fractions (domestic first, then XI)."""
    n = int(H.size)
    xd = np.asarray(xd, float)
    xi = np.asarray(xi, float)
    delta_hat = np.clip(np.asarray(delta_hat, float), 0.0, 1.0)
    fd = np.zeros(n)
    fi = np.zeros(n)
    s = max(float(S0), 0.0)
    for t in range(n):
        A = (1.0 - loss) * s + H[t]
        if A <= 1e-15:
            s = 0.0
            continue
        xd_t = min(max(xd[t], 0.0), A)
        fd[t] = xd_t / A
        rest = A - xd_t
        if rest <= 1e-15:
            s = 0.0
            continue
        xi_t = min(max(xi[t], 0.0), rest)
        fi[t] = xi_t / rest
        xi_ship = xi_t * (1.0 - delta_hat[t])
        s = rest - xi_ship
    return fd, fi


def _inv_demand_dpdq(q: np.ndarray, alpha: float, lam: float, floor: float
                     ) -> np.ndarray:
    """∂p/∂q of D.7, zero where the numerical argument floor binds."""
    q = np.asarray(q, float)
    active = (q > floor).astype(float)
    qf = np.maximum(q, floor)
    if lam == 0.0:
        return active * (-alpha) * np.power(qf, -alpha - 1.0)
    u = lam + (1.0 - lam) * qf
    return active * (-alpha) * np.power(np.maximum(u, 1e-15), -alpha - 1.0) * (1.0 - lam)


def _plan_objective_grad(
        z: np.ndarray,
        H: np.ndarray,
        S0: float,
        xi_others: np.ndarray,
        xi_star: np.ndarray,
        xd_star: np.ndarray,
        alpha_i: float,
        alpha_d: float,
        params: AgrimateParams,
        delta_hat: np.ndarray,
        ) -> tuple[float, np.ndarray]:
    n = int(H.size)
    fd = z[:n]
    fi = z[n:]
    loss = params.delta_loss
    floor = params.demand_arg_floor
    one_m_d = 1.0 - delta_hat

    A = np.empty(n)
    xd = np.empty(n)
    rest = np.empty(n)
    xi_int = np.empty(n)
    xi_ship = np.empty(n)
    S = np.empty(n)
    s = max(float(S0), 0.0)
    for t in range(n):
        A[t] = (1.0 - loss) * s + H[t]
        xd[t] = fd[t] * A[t]
        rest[t] = A[t] - xd[t]
        xi_int[t] = fi[t] * rest[t]
        xi_ship[t] = xi_int[t] * one_m_d[t]
        S[t] = rest[t] - xi_ship[t]
        s = S[t]

    q_i = (xi_ship + xi_others) / xi_star
    q_d = xd / xd_star
    p_i = np.asarray(inverse_demand(q_i, alpha_i, params.lam_demand, floor), float)
    p_d = np.asarray(inverse_demand(q_d, alpha_d, params.lam_demand, floor), float)
    rev = float(np.dot(p_i, xi_ship) + np.dot(p_d, xd))
    # Author get_unit_storage_costs with δ=ρ=0: −p_sto_step · (N, N−1, …, 1)
    psto = params.p_sto_step
    unit = -psto * (n - np.arange(n, dtype=float))
    x_tot = xd + xi_ship
    cost = float(np.dot(unit, x_tot - H))
    # xmin quadratic penalty (producer_optimization.jl); ζ=0 ⇒ fully on
    tot_possible = max(float(S0), 0.0) + float(H.sum())
    xmin_each = params.xmin_share * tot_possible / max(n * 2.0, 1.0)
    pw = 1.0 - float(params.zeta_penalty)
    under_d = xd < xmin_each
    under_i = xi_int < xmin_each
    pen = 0.0
    if pw > 0.0 and xmin_each > 0.0:
        pen = float(np.sum((xd[under_d] - xmin_each) ** 2 * p_d[under_d])
                    + np.sum((xi_int[under_i] - xmin_each) ** 2 * p_i[under_i]))
    obj = -(rev - cost) + pw * pen

    dp_i = _inv_demand_dpdq(q_i, alpha_i, params.lam_demand, floor)
    dp_d = _inv_demand_dpdq(q_d, alpha_d, params.lam_demand, floor)
    dobj_dxi_ship = -(p_i + xi_ship * dp_i / xi_star) + unit
    dobj_dxd = -(p_d + xd * dp_d / xd_star) + unit
    if pw > 0.0 and xmin_each > 0.0:
        dobj_dxd = dobj_dxd.copy()
        dobj_dxi_int_extra = np.zeros(n)
        dobj_dxd[under_d] += pw * 2.0 * (xd[under_d] - xmin_each) * p_d[under_d]
        dobj_dxi_int_extra[under_i] = (
            pw * 2.0 * (xi_int[under_i] - xmin_each) * p_i[under_i])
    else:
        dobj_dxi_int_extra = np.zeros(n)
    dobj_dS = np.zeros(n)

    dfd = np.zeros(n)
    dfi = np.zeros(n)
    adj_s = 0.0
    for t in range(n - 1, -1, -1):
        adj_S = dobj_dS[t] + adj_s
        adj_rest = adj_S
        adj_xi_ship = -adj_S + dobj_dxi_ship[t]
        adj_xd = dobj_dxd[t]
        adj_xi_int = adj_xi_ship * one_m_d[t] + dobj_dxi_int_extra[t]
        dfi[t] = adj_xi_int * rest[t]
        adj_rest = adj_rest + adj_xi_int * fi[t]
        adj_A = adj_rest
        adj_xd = adj_xd - adj_rest
        dfd[t] = adj_xd * A[t]
        adj_A = adj_A + adj_xd * fd[t]
        adj_s = adj_A * (1.0 - loss)
    return obj, np.concatenate([dfd, dfi])


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

    ``x0`` is concatenated *intended* sales (xd, xi), converted internally to
    fractions. Failed/non-finite optimiser output falls back to that feasible
    projection; it is not replaced by a legacy price rule.
    """
    n = int(H.size)
    H = np.asarray(H, float)
    xi_others = np.broadcast_to(np.asarray(xi_others, float), (n,)).copy()
    xi_star = np.maximum(np.broadcast_to(np.asarray(xi_star_step, float), (n,)), 1e-8)
    xd_star = np.maximum(np.broadcast_to(np.asarray(xd_star_step, float), (n,)), 1e-8)
    if delta_hat is None:
        delta_hat = np.zeros(n)
    delta_hat = np.clip(np.asarray(delta_hat, float), 0.0, 1.0)
    loss = params.delta_loss

    if x0 is None:
        x0 = np.concatenate([
            np.broadcast_to(np.maximum(np.asarray(xd_star_step, float), 0.0), (n,)).copy(),
            np.broadcast_to(np.maximum(np.asarray(xi_star_step, float), 0.0), (n,)).copy(),
        ])
    x0 = np.asarray(x0, float).reshape(-1)
    if x0.size != 2 * n:
        x0 = np.concatenate([
            np.broadcast_to(np.maximum(np.asarray(xd_star_step, float), 0.0), (n,)).copy(),
            np.broadcast_to(np.maximum(np.asarray(xi_star_step, float), 0.0), (n,)).copy(),
        ])
    fd0, fi0 = sales_to_fractions(x0[:n], x0[n:], S0, H, loss, delta_hat)
    z0 = np.concatenate([fd0, fi0])

    def fun(z):
        return _plan_objective_grad(
            z, H, S0, xi_others, xi_star, xd_star,
            alpha_i, alpha_d, params, delta_hat,
        )

    bounds = [(0.0, 1.0)] * (2 * n)
    res = minimize(
        fun, z0, method="L-BFGS-B", jac=True, bounds=bounds,
        options={"maxiter": params.plan_maxiter, "ftol": 1e-8},
    )
    fallback = False
    z = np.asarray(res.x, float)
    if z.size != 2 * n or not np.all(np.isfinite(z)):
        z = z0
        fallback = True
    z = np.clip(z, 0.0, 1.0)
    xd, xi_int, xi_ship, S = fractions_to_sales(z[:n], z[n:], S0, H, loss, delta_hat)
    finite = bool(np.all(np.isfinite(xd)) and np.all(np.isfinite(xi_int))
                  and np.all(np.isfinite(S)))
    feasible = finite and bool(np.min(S) >= -1e-8)
    if not feasible:
        fallback = True
        xd, xi_int, xi_ship, S = fractions_to_sales(fd0, fi0, S0, H, loss, delta_hat)
        finite = bool(np.all(np.isfinite(S)))
        feasible = finite and bool(np.min(S) >= -1e-8)

    q_i = (xi_ship + xi_others) / xi_star
    q_d = xd / xd_star
    floor = params.demand_arg_floor
    floor_binds = int(np.sum(q_i <= floor + 1e-12) + np.sum(q_d <= floor + 1e-12))
    residual = float(max(-np.min(S), 0.0)) if S.size else 0.0
    return {
        "xd": xd,
        "xi": xi_int,
        "xi_ship": xi_ship,
        "S": S,
        "fd": np.clip(z[:n], 0.0, 1.0),
        "fi": np.clip(z[n:], 0.0, 1.0),
        "success": bool(feasible),
        "fallback": fallback,
        "converged": bool(getattr(res, "success", False)) and not fallback,
        "nfev": int(getattr(res, "nfev", 0)),
        "floor_binds": floor_binds,
        "residual": residual,
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
