"""Raised-cosine harvest profiles (supplement Eq. E.27–E.28)."""
from __future__ import annotations

import numpy as np

from sheaf.calendar24 import STEPS_PER_YEAR


def _month_to_doy(month: int, end: bool = False) -> float:
    mdays = np.array([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31], float)
    if end:
        return float(mdays[:month].sum())
    return float(mdays[: month - 1].sum()) + 1.0


def raised_cosine_daily(start_month: int, end_month: int, n_days: int = 365
                        ) -> np.ndarray:
    """Eq. (E.27). Wraps if start_month > end_month.

    Printed condition |d−dmid| ≤ 1.2 is dimensionally days and cannot be
    right for a months-long harvest. Support used: |d−dmid| ≤ 0.6 Δd.
    """
    if start_month <= end_month:
        d_beg = _month_to_doy(start_month, end=False)
        d_end = _month_to_doy(end_month, end=True)
        span = d_end - d_beg + 1.0
        mid = 0.5 * (d_beg + d_end)
        d = np.arange(1, n_days + 1, dtype=float)
        dist = np.abs(d - mid)
    else:
        d_beg = _month_to_doy(start_month, end=False)
        d_end = _month_to_doy(end_month, end=True)
        span = (n_days - d_beg + 1) + d_end
        mid = (d_beg + span / 2.0 - 1.0) % n_days + 1.0
        d = np.arange(1, n_days + 1, dtype=float)
        dist = np.minimum(np.abs(d - mid), n_days - np.abs(d - mid))
    h = np.zeros(n_days)
    half = 0.6 * max(span, 1.0)
    inside = dist <= half
    h[inside] = (1.0 + np.cos(1.2 * dist[inside] / max(span, 1.0) * np.pi)) / max(
        0.6 * span, 1e-9)
    s = h.sum()
    if s <= 0:
        h[:] = 1.0 / n_days
    else:
        h /= s
    return h


def step_profile_from_months(start_month: int, end_month: int,
                             n_year: int = STEPS_PER_YEAR) -> np.ndarray:
    """Integrate the daily profile over 24 equal-length bins (E.28)."""
    daily = raised_cosine_daily(start_month, end_month)
    edges = np.linspace(0, 365, n_year + 1)
    out = np.empty(n_year)
    d = np.arange(1, 366)
    for i in range(n_year):
        mask = (d - 0.5 >= edges[i]) & (d - 0.5 < edges[i + 1])
        out[i] = daily[mask].sum() if np.any(mask) else 0.0
    s = out.sum()
    return out / s if s > 0 else np.full(n_year, 1.0 / n_year)
