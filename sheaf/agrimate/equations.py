"""Core Agrimate equations (supplement §D)."""
from __future__ import annotations

import numpy as np

from .params import AgrimateParams


def clip01(x: np.ndarray | float) -> np.ndarray | float:
    return np.clip(x, 0.0, 1.0)


def harvest_weights(n_year: int, steepness: float = 8.0) -> np.ndarray:
    """Eq. D.1a logistic weights over the forthcoming year."""
    n = np.arange(n_year, dtype=float)
    mid = 0.5 * (n_year - 1)
    w = 1.0 / (1.0 + np.exp(-steepness * (n - mid) / max(n_year, 1)))
    w = (w - w.min()) / max(float(w.max() - w.min()), 1e-12)
    return w


def expected_harvest(H_star_step: np.ndarray, H_realised: np.ndarray,
                     n_year: int) -> np.ndarray:
    """Eq. D.1. Second term uses realised H (not Ĥ; OCR D.1b is circular)."""
    w = harvest_weights(n_year)
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


def purchaser_demand(prices: np.ndarray, budget: float, sigma: float,
                     shares: np.ndarray) -> np.ndarray:
    """CES demand D.30. ``shares`` are baseline value shares (sum 1)."""
    p = np.maximum(np.asarray(prices, float), 1e-12)
    s = np.maximum(np.asarray(shares, float), 0.0)
    if s.sum() <= 0:
        return np.zeros_like(p)
    s = s / s.sum()
    # q_i ∝ s_i * p_i^{-σ}; spend s-weighted
    q_prop = s * p ** (-sigma)
    spend_prop = q_prop * p
    tot = spend_prop.sum()
    if tot <= 0:
        return np.zeros_like(p)
    return q_prop * (budget / tot)


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


def preference_update(pref: np.ndarray, fill: np.ndarray, rho: float) -> np.ndarray:
    p = np.asarray(pref, float)
    f = np.asarray(fill, float)
    out = (1.0 - rho) * p + rho * f
    s = out.sum()
    return out / s if s > 0 else p
