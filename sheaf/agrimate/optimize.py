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


def clip_demand_x1(
        xd: float, xi: float, S0: float, H0: float, loss: float = 0.0,
        ) -> tuple[float, float]:
    """Author current sales: min(demand, availability), domestic first.

    ``X1_dom = min(D_dom, H+S)``, ``X1_for = min(D_for, H+S−X1_dom)``.
    """
    A = max((1.0 - float(loss)) * max(float(S0), 0.0) + float(H0), 0.0)
    xd = min(max(float(xd), 0.0), A)
    xi = min(max(float(xi), 0.0), max(A - xd, 0.0))
    return xd, xi


def pack_future_fractions(z_fut: np.ndarray, fd0: float, fi0: float, n: int
                          ) -> np.ndarray:
    """Rebuild length-2n fractions with step-0 locked."""
    z_fut = np.asarray(z_fut, float).reshape(-1)
    z = np.empty(2 * n)
    z[0] = fd0
    z[1:n] = z_fut[: n - 1]
    z[n] = fi0
    z[n + 1:] = z_fut[n - 1:]
    return z


def unpack_future_fractions(z: np.ndarray, n: int) -> np.ndarray:
    z = np.asarray(z, float).reshape(-1)
    return np.concatenate([z[1:n], z[n + 1:]])


def demand_x1_from_ask(
        ask: np.ndarray, r: int, S0: float, H0: float,
        iota: float, x_avg: float, loss: float = 0.0,
        ) -> tuple[float, float]:
    """Current sales from last origin-by-buyer requests, iota floor, clip.

    ``x_avg`` is per-step mean harvest/sales (author ``X_avg``), not annual.
    """
    ask = np.asarray(ask, float)
    r = int(r)
    d_dom = float(ask[r, r])
    d_for = float(max(ask[r].sum() - d_dom, 0.0))
    floor = float(iota) * max(float(x_avg), 0.0)
    if d_dom < floor:
        d_dom = 0.0
    if d_for < floor:
        d_for = 0.0
    return clip_demand_x1(d_dom, d_for, S0, H0, loss)


def baseline_ask_matrix(xd_star: np.ndarray, xi_star: np.ndarray,
                        t_star: np.ndarray) -> np.ndarray:
    """Nash-scale origin-by-buyer demand used before the first procurement."""
    xd_star = np.asarray(xd_star, float).reshape(-1)
    xi_star = np.asarray(xi_star, float).reshape(-1)
    t_star = np.asarray(t_star, float)
    n_r = xd_star.size
    ask = np.zeros((n_r, n_r))
    for e in range(n_r):
        ask[e, e] = max(xd_star[e], 0.0)
        row = t_star[e].copy()
        row[e] = 0.0
        tot = float(row.sum())
        if tot > 1e-15:
            ask[e] += max(xi_star[e], 0.0) * (row / tot)
    return ask


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


def projected_grad_norm(z: np.ndarray, g: np.ndarray,
                        lo: float = 0.0, hi: float = 1.0) -> float:
    """Bound-constrained projected gradient (minimization, box [lo, hi])."""
    z = np.asarray(z, float)
    g = np.asarray(g, float)
    pg = g.copy()
    at_lo = z <= lo + 1e-12
    at_hi = z >= hi - 1e-12
    pg[at_lo] = np.minimum(pg[at_lo], 0.0)
    pg[at_hi] = np.maximum(pg[at_hi], 0.0)
    return float(np.linalg.norm(pg))


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
        x1: tuple[float, float] | None = None,
        ) -> dict:
    """Maximise supplier profit over (XD, XI) subject to storage ≥ 0.

    ``x0`` is concatenated *intended* sales (xd, xi), converted internally to
    fractions. Failed/non-finite optimiser output falls back to that feasible
    projection; it is not replaced by a legacy price rule.

    ``x1=(xd0, xi0)`` locks current-step sales to demand (clipped by
    availability, domestic first) and optimises only the remaining steps
    with scipy SLSQP — independent Python of the sourced wheat programme
    (x1 fixed, ``:LD_SLSQP``). ``x1 is None`` keeps the older 2N free
    L-BFGS-B path for unit tests of the fraction map.
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
    x1_fixed = x1 is not None
    method = "SLSQP" if x1_fixed else "L-BFGS-B"
    fd1 = float(z0[0])
    fi1 = float(z0[n])
    if x1_fixed:
        xd1, xi1 = clip_demand_x1(x1[0], x1[1], S0, H[0], loss)
        A0 = (1.0 - loss) * max(float(S0), 0.0) + float(H[0])
        if A0 > 1e-15:
            fd1 = xd1 / A0
            rest0 = A0 - xd1
            fi1 = xi1 / rest0 if rest0 > 1e-15 else 0.0
        else:
            fd1, fi1 = 0.0, 0.0
        z0[0] = fd1
        z0[n] = fi1

    def fun_full(z):
        return _plan_objective_grad(
            z, H, S0, xi_others, xi_star, xd_star,
            alpha_i, alpha_d, params, delta_hat,
        )

    fallback = False
    if x1_fixed and n >= 2:
        def fun_fut(zf):
            z = pack_future_fractions(zf, fd1, fi1, n)
            obj, grad = fun_full(z)
            return obj, unpack_future_fractions(grad, n)

        zf0 = unpack_future_fractions(z0, n)
        bounds_f = [(0.0, 1.0)] * (2 * (n - 1))
        res = minimize(
            fun_fut, zf0, method="SLSQP", jac=True, bounds=bounds_f,
            options={"maxiter": params.plan_maxiter, "ftol": 1e-8, "disp": False},
        )
        zf = np.asarray(res.x, float)
        if zf.size != 2 * (n - 1) or not np.all(np.isfinite(zf)):
            zf = zf0
            fallback = True
        z = pack_future_fractions(np.clip(zf, 0.0, 1.0), fd1, fi1, n)
    else:
        bounds = [(0.0, 1.0)] * (2 * n)
        res = minimize(
            fun_full, z0, method="L-BFGS-B", jac=True, bounds=bounds,
            options={"maxiter": params.plan_maxiter, "ftol": 1e-8},
        )
        z = np.asarray(res.x, float)
        if z.size != 2 * n or not np.all(np.isfinite(z)):
            z = z0
            fallback = True
        z = np.clip(z, 0.0, 1.0)
        if x1_fixed:
            z[0] = fd1
            z[n] = fi1

    xd, xi_int, xi_ship, S = fractions_to_sales(z[:n], z[n:], S0, H, loss, delta_hat)
    finite = bool(np.all(np.isfinite(xd)) and np.all(np.isfinite(xi_int))
                  and np.all(np.isfinite(S)))
    feasible = finite and bool(np.min(S) >= -1e-8)
    if not feasible:
        fallback = True
        z_fb = z0.copy()
        if x1_fixed:
            z_fb[0] = fd1
            z_fb[n] = fi1
        xd, xi_int, xi_ship, S = fractions_to_sales(
            z_fb[:n], z_fb[n:], S0, H, loss, delta_hat)
        finite = bool(np.all(np.isfinite(S)))
        feasible = finite and bool(np.min(S) >= -1e-8)

    q_i = (xi_ship + xi_others) / xi_star
    q_d = xd / xd_star
    floor = params.demand_arg_floor
    floor_binds = int(np.sum(q_i <= floor + 1e-12) + np.sum(q_d <= floor + 1e-12))
    residual = float(max(-np.min(S), 0.0)) if S.size else 0.0
    obj, grad = _plan_objective_grad(
        np.clip(z, 0.0, 1.0), H, S0, xi_others, xi_star, xd_star,
        alpha_i, alpha_d, params, delta_hat,
    )
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
        "nit": int(getattr(res, "nit", 0)),
        "status": int(getattr(res, "status", -1)),
        "message": str(getattr(res, "message", "")),
        "obj": float(obj),
        "pgnorm": projected_grad_norm(np.clip(z, 0.0, 1.0), grad),
        "floor_binds": floor_binds,
        "residual": residual,
        "method": method,
        "x1_fixed": bool(x1_fixed),
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
