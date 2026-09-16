"""Raised-cosine harvest profiles (supplement Eq. E.27–E.28).

Support matches Zenodo 14022004 ``raised_cosine_harvest_distribution``
(duration_in_s=1.2), not the OCR reading |d−dmid|≤1.2 days.
"""
from __future__ import annotations

import numpy as np

from sheaf.calendar24 import STEPS_PER_YEAR


def _month_to_doy(month: int, end: bool = False) -> float:
    mdays = np.array([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31], float)
    if end:
        return float(mdays[:month].sum())
    return float(mdays[: month - 1].sum()) + 1.0


def raised_cosine_daily(start_month: int, end_month: int, n_days: int = 365,
                        duration_in_s: float = 1.2) -> np.ndarray:
    """Eq. (E.27) as in author ``harvest_distributions.py``.

    ``s = duration / duration_in_s``; support |d − dmid| ≤ s; fold a 3-year
    window back onto the calendar year.
    """
    d_beg = _month_to_doy(start_month, end=False)
    d_end = _month_to_doy(end_month, end=True)
    start_day = d_beg
    end_day = d_end
    if end_day < start_day:
        end_day += n_days
    duration = end_day - start_day + 1.0
    s = duration / max(duration_in_s, 1e-12)
    days = np.arange(1, 3 * n_days + 1, dtype=float)
    start_shift = start_day + n_days
    end_shift = end_day + n_days
    mid = 0.5 * (start_shift + end_shift)
    dist = np.abs(days - mid)
    h3 = np.zeros(3 * n_days)
    inside = dist <= s
    h3[inside] = 1.0 + np.cos((days[inside] - mid) / s * np.pi)
    h = h3[:n_days] + h3[n_days:2 * n_days] + h3[2 * n_days:3 * n_days]
    tot = h.sum()
    if tot <= 0:
        h[:] = 1.0 / n_days
    else:
        h /= tot
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
