"""Tbl. E.4 export restrictions (bans 0.95, taxes 0.50)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from sheaf.calendar24 import STEPS_PER_YEAR
from sheaf.data_usda import load_amis_restrictions

from .regions import REGION_NAMES, iso3_to_region

_CUT = {
    "Export prohibition": 0.95,
    "Export ban": 0.95,
    "Export quota": 0.70,
    "Export tax": 0.50,
    "Minimum export price": 0.0,  # E.4 uses bans and taxes; others unused
    "Licensing requirement": 0.0,
}

_AMIS_ISO = {
    "Argentina": "ARG",
    "Australia": "AUS",
    "China": "CHN",
    "Egypt": "EGY",
    "India": "IND",
    "Indonesia": "IDN",
    "Kazakhstan": "KAZ",
    "Mexico": "MEX",
    "Russian Federation": "RUS",
    "Ukraine": "UKR",
    "Viet Nam": "VNM",
}


def _region_of_amis(name: str) -> str | None:
    iso = _AMIS_ISO.get(name)
    if iso is None:
        return None
    return iso3_to_region().get(iso)


def restriction_matrix(regions: list[str], start_year: int, end_year: int,
                       crop: str = "wheat") -> np.ndarray:
    """Δ[region, step] on the 24-step clock. Unweighted inside multi-country
    regions except single-country regions (export-share weights not rebuilt).
    """
    n_r = len(regions)
    n_steps = (end_year - start_year + 1) * STEPS_PER_YEAR
    delta = np.zeros((n_r, n_steps))
    idx = {r: i for i, r in enumerate(regions)}
    try:
        amis = load_amis_restrictions()
    except FileNotFoundError:
        return delta
    grain = {"wheat": "Wheat", "rice": "Rice", "maize": "Maize"}[crop]
    if "Commodity" in amis.columns:
        amis = amis[amis["Commodity"].astype(str).str.contains(grain, case=False, na=False)]
    for _, row in amis.iterrows():
        country = str(row.get("Country_Name", row.get("Country", "")))
        region = _region_of_amis(country)
        if region is None or region not in idx:
            continue
        meas = str(row.get("Measure", row.get("Policy", "")))
        cut = 0.0
        for k, v in _CUT.items():
            if k.lower() in meas.lower():
                cut = v
                break
        if cut <= 0:
            continue
        start = pd.to_datetime(row.get("Start_Date"), errors="coerce")
        end = pd.to_datetime(row.get("End_Date"), errors="coerce")
        if pd.isna(start):
            continue
        if pd.isna(end):
            end = start + pd.offsets.MonthEnd(6)
        for y in range(start_year, end_year + 1):
            for ys in range(STEPS_PER_YEAR):
                month = ys // 2 + 1
                # step midpoint ~ day 8 or 23
                day = 8 if ys % 2 == 0 else 23
                stamp = pd.Timestamp(year=y, month=month, day=day)
                if start <= stamp <= end:
                    t = (y - start_year) * STEPS_PER_YEAR + ys
                    i = idx[region]
                    delta[i, t] = max(delta[i, t], cut)
    return delta


def empty_delta(n_regions: int, n_steps: int) -> np.ndarray:
    return np.zeros((n_regions, n_steps))


# Bai/Wada/Puma exporter-at-a-time list, mapped onto AgrimateRegionsWheat.
# EU-28 in that note is EU-27 here. Used by a labelled G0-H experiment, not
# by the default three-scenario run, and not by Gate 2.
EXPORTER_PULSE_REGIONS = (
    "Russia", "Canada", "EU-27", "USA", "Ukraine",
    "Australia", "Argentina", "Kazakhstan", "Pakistan",
)


def restriction_pulse(
    regions: list[str],
    start_year: int,
    end_year: int,
    exporter: str,
    intensity: float = 1.0,
    duration_months: int = 12,
    start: str = "2008-01-01",
) -> np.ndarray:
    """Synthetic one-exporter restriction on the 24-step clock.

    Structure for a later exporter×intensity×duration grid (G0-H/P). Not a
    government best-response (G2) and not the default AMIS/E.4 schedule.
    """
    n_r = len(regions)
    n_steps = (end_year - start_year + 1) * STEPS_PER_YEAR
    delta = np.zeros((n_r, n_steps))
    if exporter not in regions:
        raise KeyError(f"exporter {exporter!r} is not in the region list")
    i = regions.index(exporter)
    t0 = pd.Timestamp(start)
    t1 = t0 + pd.DateOffset(months=int(duration_months)) - pd.Timedelta(days=1)
    cut = float(np.clip(intensity, 0.0, 1.0))
    for y in range(start_year, end_year + 1):
        for ys in range(STEPS_PER_YEAR):
            month = ys // 2 + 1
            day = 8 if ys % 2 == 0 else 23
            stamp = pd.Timestamp(year=y, month=month, day=day)
            if t0 <= stamp <= t1:
                t = (y - start_year) * STEPS_PER_YEAR + ys
                delta[i, t] = cut
    return delta


# silence unused import if REGION_NAMES only used by callers
_ = REGION_NAMES
