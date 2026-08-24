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


def load_harvest_calendar(
        crop: str = "wheat",
        path: Path | str | None = None) -> pd.DataFrame:
    """Load `{crop}_harvest_months.csv` (or an explicit path)."""
    crop = crop.lower().strip()
    p = Path(path) if path else (_CAL_DIR / f"{crop}_harvest_months.csv")
    if not p.exists():
        raise FileNotFoundError(
            f"No harvest calendar for {crop!r} at {p}. "
            f"Expected columns country, harvest_start_month, harvest_end_month.")
    df = pd.read_csv(p)
    required = {"country", "harvest_start_month", "harvest_end_month"}
    if not required.issubset(df.columns):
        raise ValueError(f"{p} missing columns {required - set(df.columns)}")
    return df


def load_wheat_harvest_calendar(
        path: Path | str | None = None) -> pd.DataFrame:
    """Backward-compatible alias for wheat."""
    return load_harvest_calendar("wheat", path=path)


def harvest_month_weights(start: int, end: int,
                          peak_month: int | None = None) -> np.ndarray:
    """Length-12 weights summing to 1; triangular peak inside the window.

    If peak_month is None, peak at the middle of the window. This matches
    Agrimate-style concentration of harvest mass mid-season rather than a
    flat uniform slab.
    """
    w = np.zeros(12)
    months = _months_in_window(int(start), int(end))
    if not months:
        w[:] = 1.0 / 12.0
        return w
    if peak_month is None or peak_month not in months:
        peak_month = months[len(months) // 2]
    # Triangular weights by circular distance along the window sequence
    peak_idx = months.index(int(peak_month))
    for i, m in enumerate(months):
        dist = abs(i - peak_idx)
        w[m - 1] += max(len(months) - dist, 1)
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
        peak = int(row["peak_month"]) if "peak_month" in cal.columns and pd.notna(
            row.get("peak_month")) else None
        mw = harvest_month_weights(row["harvest_start_month"],
                                   row["harvest_end_month"],
                                   peak_month=peak)
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


def rolling_ahead(arr: np.ndarray, horizon: int) -> np.ndarray:
    """For each t, sum arr[t+1 : t+1+horizon] with zero beyond the end.

    arr shape (n, T) → (n, T). Used for foresight of remaining harvest/demand.
    """
    n, T = arr.shape
    out = np.zeros((n, T))
    csum = np.concatenate([np.zeros((n, 1)), np.cumsum(arr, axis=1)], axis=1)
    for t in range(T):
        t1 = min(t + 1 + horizon, T)
        # sum of arr[t+1:t1] = csum[t1] - csum[t+1]
        out[:, t] = csum[:, t1] - csum[:, t + 1]
    return out


def rolling_ahead_variable(arr: np.ndarray, horizons: np.ndarray) -> np.ndarray:
    """Like rolling_ahead but horizon[t] may differ per time index.

    arr (n, T), horizons (T,) of non-negative ints → (n, T).
    """
    n, T = arr.shape
    out = np.zeros((n, T))
    csum = np.concatenate([np.zeros((n, 1)), np.cumsum(arr, axis=1)], axis=1)
    for t in range(T):
        h = int(max(0, horizons[t]))
        t1 = min(t + 1 + h, T)
        out[:, t] = csum[:, t1] - csum[:, t + 1]
    return out


def steps_to_harvest_pulse(H: np.ndarray, frac: float = 0.12,
                           max_horizon: int = STEPS_PER_YEAR) -> np.ndarray:
    """Steps ahead until cumulative future harvest ≥ frac of mean annual H.

    H is (n, T). Uses the **world** harvest path (sum over countries) so all
    agents share the same lean-season clock (NH summer pulse). Returns (T,).
    If the pulse never arrives within max_horizon, returns max_horizon.
    """
    world = H.sum(axis=0)
    T = world.shape[0]
    # Mean annual harvest over complete years in the window
    n_years = max(T // STEPS_PER_YEAR, 1)
    ann = float(world[: n_years * STEPS_PER_YEAR].sum()) / n_years
    thresh = max(frac * ann, 1e-6)
    csum = np.concatenate([[0.0], np.cumsum(world)])
    out = np.full(T, max_horizon, dtype=int)
    for t in range(T):
        # search smallest h≥1 with sum world[t+1:t+1+h] ≥ thresh
        for h in range(1, max_horizon + 1):
            t1 = min(t + 1 + h, T)
            if csum[t1] - csum[t + 1] >= thresh:
                out[t] = h
                break
            if t1 >= T:
                out[t] = max(t1 - t - 1, 1)
                break
    return out
