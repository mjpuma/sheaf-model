"""Core Agrimate equations (supplement §D)."""
from __future__ import annotations

import numpy as np

from .params import AgrimateParams


def clip01(x: np.ndarray | float) -> np.ndarray | float:
    return np.clip(x, 0.0, 1.0)


def harvest_weights(n_year: int, n_for: int | None = None,
                   tau_for_steps: float | None = None) -> np.ndarray:
    """Eq. D.1 weights from Zenodo ``expected_harvests.jl``.

    ``w = 1 / (1 + exp((n − N_for) / (0.17 τ_for)))`` on 1-based steps.
    Near-term w ≈ 1 (realised harvest); far-term w ≈ 0 (baseline).
    """
    if n_for is None:
        n_for = 3 * (n_year // 12)
    if tau_for_steps is None:
        tau_for_steps = 0.2 * n_year
    n = np.arange(1, n_year + 1, dtype=float)
    den = 0.17 * max(float(tau_for_steps), 1e-12)
    return 1.0 / (1.0 + np.exp((n - n_for) / den))


def expected_harvest(H_star_step: np.ndarray, H_realised: np.ndarray,
                     n_year: int, n_for: int | None = None,
                     tau_for_steps: float | None = None) -> np.ndarray:
    """Eq. D.1. Second term is realised H (OCR D.1b is circular)."""
    w = harvest_weights(n_year, n_for=n_for, tau_for_steps=tau_for_steps)
    return (1.0 - w) * H_star_step + w * H_realised


def expected_restriction(delta_now: float, n_year: int) -> np.ndarray:
    """Eq. D.2: current phase known; future announcements not foreseen."""
    out = np.zeros(n_year)
    out[0] = float(np.clip(delta_now, 0.0, 1.0))
    return out


def inverse_demand(q_over_star: np.ndarray | float, alpha: float, lam: float,
                   floor: float = 0.05) -> np.ndarray | float:
    """Eq. D.7 isoelastic inverse demand. Argument floored (numerical)."""
    x = np.maximum(np.asarray(q_over_star, float), floor)
    if lam == 0.0:
        return x ** (-alpha)
    return (lam + (1.0 - lam) * x) ** (-alpha)


def inverse_of_inverse_demand(p: np.ndarray, alpha: float, lam: float
                              ) -> np.ndarray:
    p = np.maximum(np.asarray(p, float), 1e-12)
    if lam == 0.0:
        return p ** (-1.0 / max(alpha, 1e-12))
    return np.maximum((p ** (-1.0 / max(alpha, 1e-12)) - lam) / max(1.0 - lam, 1e-12), 0.0)


def alpha_domestic_d10(alpha_i: float, xi_r: float, xi_world: float) -> float:
    """Eq. D.10: αD,r = αI · XI,r*/XI* when both markets exist."""
    if xi_world <= 0:
        return 1.0
    return float(alpha_i * xi_r / xi_world)


def fulfill_sales(planned_d: float, planned_i: float, available: float,
                  delta: float) -> tuple[float, float]:
    """Eq. D.3: domestic first; international scaled by (1−Δ)."""
    planned_d = max(float(planned_d), 0.0)
    planned_i = max(float(planned_i), 0.0)
    avail = max(float(available), 0.0)
    d = min(planned_d, avail)
    rest = avail - d
    i = min(planned_i, rest) * (1.0 - float(np.clip(delta, 0.0, 1.0)))
    return d, i


def update_producer_storage(S: float, harvest: float, sold_d: float, sold_i: float,
                            delta_loss: float) -> float:
    """Eq. D.6 storage identity, clipped at 0."""
    return max((1.0 - delta_loss) * S + harvest - sold_d - sold_i, 0.0)


def purchaser_commodity_quantity(price_index: float, A_d: float, eps_d: float,
                                 budget: float) -> float:
    """D.30a: commodity quantity vs a compound good.

    Author ``determine_demands`` global factor (wheat path, ``ε_d_adjust=false``)::

        D = A_d P^{-ε_d} / (1 + A_d (P^{1-ε_d} - 1)) · B

    Same algebraic form as D.35. ``budget`` is total purchaser B
    (author ``mean(p* D*) / A_d*``). At P=1, D = A_d B.
    """
    p = max(float(price_index), 1e-12)
    A = float(np.clip(A_d, 0.0, 1.0))
    e = float(eps_d)
    B = max(float(budget), 0.0)
    den = 1.0 + A * (p ** (1.0 - e) - 1.0)
    return float(max(A * (p ** (-e)) / max(den, 1e-12) * B, 0.0))


def crop_budget_share(A_d_star: float, price_index: float, extra_demand: float,
                      budget: float) -> float:
    """Author ``determine_crop_budget_share`` (D.31b). Clipped to [0, 1]."""
    B = max(float(budget), 1e-12)
    A = float(A_d_star) + float(price_index) * float(extra_demand) / B
    return float(np.clip(A, 0.0, 1.0))


def purchaser_demand(prices: np.ndarray, budget: float, sigma: float,
                     shares: np.ndarray, A_d: float | None = None,
                     eps_d: float | None = None) -> np.ndarray:
    """CES D.30, nested under D.30a when ``A_d`` is set.

    Upper tier off (``A_d is None``): spend ``budget`` on origins (D.30 only).
    Upper tier on: ``budget`` is total B; commodity quantity from D.30a, then
    ``q_r = a_r (p_r / P)^{-σ} D``. ``A_d = 1`` recovers the off case.
    """
    p = np.maximum(np.asarray(prices, float), 1e-12)
    s = np.maximum(np.asarray(shares, float), 0.0)
    if s.sum() <= 0:
        return np.zeros_like(p)
    s = s / s.sum()
    if A_d is None:
        q_prop = s * p ** (-sigma)
        spend_prop = q_prop * p
        tot = spend_prop.sum()
        if tot <= 0:
            return np.zeros_like(p)
        return q_prop * (budget / tot)
    if eps_d is None:
        raise ValueError("eps_d is required when A_d is set (D.30a)")
    P = ces_price_index(p, s, sigma)
    D = purchaser_commodity_quantity(P, A_d, eps_d, budget)
    return s * (p / max(P, 1e-12)) ** (-sigma) * D


def ces_price_index(prices: np.ndarray, shares: np.ndarray, sigma: float) -> float:
    p = np.maximum(np.asarray(prices, float), 1e-12)
    s = np.maximum(np.asarray(shares, float), 0.0)
    if s.sum() <= 0:
        return 1.0
    s = s / s.sum()
    if abs(sigma - 1.0) < 1e-9:
        return float(np.exp(np.sum(s * np.log(p))))
    r = 1.0 - sigma
    return float((np.sum(s * p ** r)) ** (1.0 / r))


def consumption_ces(p_c: float, A_c: float, eps_c: float, C_star: float) -> float:
    """Eq. D.35 food consumption share of CES expenditure."""
    pc = max(float(p_c), 1e-8)
    A = float(np.clip(A_c, 1e-8, 1.0 - 1e-8))
    e = float(eps_c)
    num = pc ** (-e)
    den = 1.0 + A * (pc ** (1.0 - e) - 1.0)
    w = num / max(den, 1e-12)
    return float(max(w, 0.0) * C_star)


def consumer_price_mix(p_import: float, inflow: float, p_prev: float,
                       stock: float) -> float:
    """Volume mix of incoming purchase price and stored grain."""
    inflow = max(inflow, 0.0)
    stock = max(stock, 0.0)
    den = inflow + stock
    if den <= 1e-12:
        return float(p_prev)
    return float((p_import * inflow + p_prev * stock) / den)


def extra_storage_demand(S: float, S_star: float, tau_steps: float) -> float:
    """Purchaser rebuild toward Ψ-target on timescale τ."""
    if tau_steps <= 0:
        return 0.0
    return (S_star - S) / tau_steps


def foreign_request_quantity(q: np.ndarray, self_index: int) -> float:
    """International part of a D.30/D.30a request vector (drop own origin).

    Author two-market ``x1`` is the request, not a min(supply, demand)
    ration. Domestic origin stays on the supplier ``sold_d`` path.
    """
    q = np.asarray(q, float).reshape(-1)
    i = int(self_index)
    if q.size == 0:
        return 0.0
    if i < 0 or i >= q.size:
        return float(np.maximum(q, 0.0).sum())
    return float(max(q.sum() - q[i], 0.0))


def preference_update(pref: np.ndarray, fill: np.ndarray, rho: float) -> np.ndarray:
    p = np.asarray(pref, float)
    f = np.asarray(fill, float)
    out = (1.0 - rho) * p + rho * f
    s = out.sum()
    return out / s if s > 0 else p
