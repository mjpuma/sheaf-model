"""Seasonal harvest allocation onto the 24-step calendar."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .calendar24 import STEPS_PER_YEAR, month_half_to_year_step

_CAL_DIR = Path(__file__).resolve().parents[1] / "data" / "crop_calendars"


def _months_in_window(start: int, end: int) -> list[int]:
    """Inclusive harvest months; wraps if start > end (e.g. 10..1)."""
    if start <= end:
        return list(range(start, end + 1))
    return list(range(start, 13)) + list(range(1, end + 1))


def load_wheat_harvest_calendar(
        path: Path | str | None = None) -> pd.DataFrame:
    p = Path(path) if path else (_CAL_DIR / "wheat_harvest_months.csv")
    df = pd.read_csv(p)
    required = {"country", "harvest_start_month", "harvest_end_month"}
    if not required.issubset(df.columns):
        raise ValueError(f"{p} missing columns {required - set(df.columns)}")
    return df


def harvest_month_weights(start: int, end: int) -> np.ndarray:
    """Length-12 weights (months 1–12) summing to 1 over the harvest window."""
    w = np.zeros(12)
    months = _months_in_window(int(start), int(end))
    if not months:
        w[:] = 1.0 / 12.0
        return w
    for m in months:
        w[m - 1] += 1.0
    w /= w.sum()
    return w


def step_weights_from_months(month_weights: np.ndarray) -> np.ndarray:
    """Length-24 weights: each month’s weight split equally across two halves."""
    if month_weights.shape != (12,):
        raise ValueError("month_weights must have shape (12,)")
    out = np.zeros(STEPS_PER_YEAR)
    for m in range(1, 13):
        share = float(month_weights[m - 1]) / 2.0
        out[month_half_to_year_step(m, 0)] = share
        out[month_half_to_year_step(m, 1)] = share
    s = out.sum()
    if s <= 0:
        out[:] = 1.0 / STEPS_PER_YEAR
    else:
        out /= s
    return out


def country_step_weights(calendar: pd.DataFrame | None = None) -> dict[str, np.ndarray]:
    """Map SHEAF country → length-24 harvest weight vector."""
    cal = load_wheat_harvest_calendar() if calendar is None else calendar
    out = {}
    for _, row in cal.iterrows():
        mw = harvest_month_weights(row["harvest_start_month"],
                                   row["harvest_end_month"])
        out[str(row["country"])] = step_weights_from_months(mw)
    return out


def allocate_annual_to_steps(annual_mmt: float, weights: np.ndarray) -> np.ndarray:
    """Spread one year’s production (MMT) across 24 steps."""
    w = np.asarray(weights, float)
    if w.shape != (STEPS_PER_YEAR,):
        raise ValueError(f"weights must have length {STEPS_PER_YEAR}")
    return float(annual_mmt) * w


def harvest_path(countries: list[str],
                 annual_by_country_year: pd.DataFrame,
                 start_year: int, end_year: int,
                 calendar: pd.DataFrame | None = None) -> np.ndarray:
    """Build (n_countries, n_steps) harvest matrix in MMT per step.

    `annual_by_country_year` must have columns country, year, production.
    Missing country–years → 0. Countries without a calendar row use uniform.
    """
    weights = country_step_weights(calendar)
    uniform = np.full(STEPS_PER_YEAR, 1.0 / STEPS_PER_YEAR)
    years = list(range(start_year, end_year + 1))
    n = len(countries)
    T = len(years) * STEPS_PER_YEAR
    H = np.zeros((n, T))
    lookup = {(r.country, int(r.year)): float(r.production)
              for r in annual_by_country_year.itertuples()}
    for i, cname in enumerate(countries):
        w = weights.get(cname, uniform)
        for yi, year in enumerate(years):
            ann = lookup.get((cname, year), 0.0)
            H[i, yi * STEPS_PER_YEAR:(yi + 1) * STEPS_PER_YEAR] = (
                allocate_annual_to_steps(ann, w))
    return H
