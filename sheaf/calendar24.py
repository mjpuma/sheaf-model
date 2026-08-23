"""SHEAF 24-step calendar (Agrimate-aligned).

STEPS_PER_YEAR = 24  →  Δt ≈ 15.22 days  →  exactly 2 steps per calendar month.

See ARCHITECTURE.md for why 24 (not 26 fortnights).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

STEPS_PER_YEAR = 24
DAYS_PER_STEP = 365.25 / STEPS_PER_YEAR  # ≈ 15.21875


@dataclass(frozen=True)
class StepStamp:
    """Absolute model step indexed from a start date."""
    step: int                 # 0-based global step index
    year: int                 # calendar year of this step's midpoint
    month: int                # 1–12
    half: int                 # 0 = first half of month, 1 = second
    year_step: int            # 0–23 within calendar year
    date: date                # midpoint date of the step


def year_step_to_month_half(year_step: int) -> tuple[int, int]:
    """Map year_step in [0, 23] → (month 1–12, half 0|1)."""
    if not 0 <= year_step < STEPS_PER_YEAR:
        raise ValueError(f"year_step must be in 0..{STEPS_PER_YEAR-1}, got {year_step}")
    month = year_step // 2 + 1
    half = year_step % 2
    return month, half


def month_half_to_year_step(month: int, half: int = 0) -> int:
    if not 1 <= month <= 12:
        raise ValueError(f"month must be 1..12, got {month}")
    if half not in (0, 1):
        raise ValueError(f"half must be 0 or 1, got {half}")
    return (month - 1) * 2 + half


def step_midpoint_date(year: int, year_step: int) -> date:
    """Midpoint of a calendar-year step (equal 365.25/24 day bins from Jan 1)."""
    month, half = year_step_to_month_half(year_step)
    # Place midpoints at ~day 7.5 and ~day 22.5 of each month (month-tiled).
    day = 8 if half == 0 else 23
    # Clamp day for short months
    for d in (day, 22, 21, 20, 15, 8):
        try:
            return date(year, month, d)
        except ValueError:
            continue
    return date(year, month, 1)


def iter_steps(start_year: int, end_year: int):
    """Yield StepStamp for every step with calendar year in [start_year, end_year]."""
    k = 0
    for year in range(start_year, end_year + 1):
        for ys in range(STEPS_PER_YEAR):
            month, half = year_step_to_month_half(ys)
            yield StepStamp(
                step=k, year=year, month=month, half=half,
                year_step=ys, date=step_midpoint_date(year, ys),
            )
            k += 1


def n_steps(start_year: int, end_year: int) -> int:
    return (end_year - start_year + 1) * STEPS_PER_YEAR


def steps_in_month(year: int, month: int, start_year: int) -> list[int]:
    """Global step indices for the two half-months in (year, month)."""
    base = (year - start_year) * STEPS_PER_YEAR
    ys0 = month_half_to_year_step(month, 0)
    return [base + ys0, base + ys0 + 1]


def agricultural_year(year: int, month: int, start_month: int = 7) -> int:
    """Crop year label: July–June → ag_year is the July calendar year.

    Example: 2010-07 → 2010; 2011-03 → 2010 (2010/11 crop year).
    """
    return year if month >= start_month else year - 1


def monthly_mean_from_steps(values, start_year: int, end_year: int):
    """Aggregate a length-(n_steps) series to a (year, month) → mean dict/list.

    `values` is indexed by global step from start_year Jan half-0.
    Returns list of dicts: year, month, value.
    """
    import numpy as np
    v = np.asarray(values, float)
    out = []
    expected = n_steps(start_year, end_year)
    if len(v) != expected:
        raise ValueError(f"expected {expected} steps, got {len(v)}")
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            idxs = steps_in_month(year, month, start_year)
            out.append(dict(year=year, month=month,
                            value=float(np.mean(v[idxs]))))
    return out
