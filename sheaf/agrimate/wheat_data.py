"""Wheat baseline arrays: USDA PSD quantities + FAOSTAT E0 shares.

Data adaptation (not an economic departure): FAOSTAT Food Balances E.1 are
not in this repository. A_d is not E.30 (merchandise exports absent).

A8 (S1): the 2007–09 baseline is member-sum within year, then mean over
those years — the same construction as ``psd_regional_annual()``. Stocks
are USDA ``ending_stocks`` only. Never FAOSTAT FBSH Stock Variation
(element 5074) as a stock level.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from sheaf.calendar24 import STEPS_PER_YEAR
from sheaf.data_faostat import load_trade_matrix
from sheaf.data_usda import detrend_anomalies, load_psd_country, load_price_series_monthly
from sheaf.seasonal import load_harvest_calendar

from .harvest import step_profile_from_months
from .params import AgrimateParams
from .regions import D9_ALPHA, D9_NU, REGION_NAMES, iso3_to_region
from .restrictions import restriction_matrix

_CONV = None

# USDA PSD quantity columns. ending_stocks is S; never FAO ΔS (element 5074).
PSD_QTY_COLS = ("production", "consumption", "exports", "imports", "ending_stocks")
BASELINE_YEARS = (2007, 2009)


def _iso2_to_iso3() -> dict[str, str]:
    global _CONV
    if _CONV is None:
        from pathlib import Path
        p = Path(__file__).resolve().parents[2] / "data" / "faostat_network" / "country_conversion_table.csv"
        t = pd.read_csv(p, encoding="utf-8-sig")
        out = {}
        if "USDA PSD" in t.columns and "ISO3 alpha" in t.columns:
            for _, r in t.iterrows():
                a, b = str(r["USDA PSD"]).strip(), str(r["ISO3 alpha"]).strip()
                if a and a != "NULL" and b and b != "nan":
                    out[a] = b
        _CONV = out
    return _CONV


def _psd_to_region(country_code: str, country_psd: str) -> str:
    iso3 = _iso2_to_iso3().get(str(country_code).strip())
    m = iso3_to_region()
    if iso3 and iso3 in m:
        return m[iso3]
    # fallback by name
    named = {
        "United States": "USA", "Russia": "Russia", "European Union": "EU-27",
        "Ukraine": "Ukraine", "Kazakhstan": "Kazakhstan", "Canada": "Canada",
        "Australia": "Australia", "Argentina": "Argentina", "Brazil": "Brazil",
        "India": "India", "China": "China", "Pakistan": "Pakistan",
        "Turkey": "Turkey",
    }
    return named.get(country_psd)


@dataclass
class WheatData:
    regions: list[str]
    H_star: np.ndarray          # (n_r, n_year) annual harvest path, MMT / year split
    H_annual: np.ndarray        # (n_r,) annual harvest MMT
    C_star: np.ndarray          # (n_r,) per-step consumption average
    XI_star: np.ndarray         # (n_r,) per-step mean international *
    XD_star: np.ndarray         # (n_r,) per-step mean domestic *
    XI_star_path: np.ndarray    # (n_r, n_year) seasonal *
    XD_star_path: np.ndarray    # (n_r, n_year) seasonal *
    XI_world: float             # per-step world international *
    T_star: np.ndarray          # (n_r, n_r) annual bilateral, exporter, importer
    Psi: np.ndarray
    A_c: np.ndarray
    A_d: np.ndarray
    alpha_d: np.ndarray
    nu: np.ndarray
    profile: np.ndarray         # (n_r, n_year)
    anomaly: np.ndarray         # (n_r, n_years) relative, indexed from start_year
    delta: np.ndarray           # (n_r, n_steps)
    p0: float
    start_year: int
    end_year: int
    notes: list[str]


def _income_ac(region: str) -> float:
    # F.1 Egypt A_c=0.34 unused: Egypt is inside Northern Africa in C.1.
    high = {"USA", "Canada", "Australia", "EU-27", "Rest of Europe", "Rest of Oceania"}
    um = {"Russia", "Kazakhstan", "Brazil", "Argentina", "China", "Rest of Eastern Asia",
          "Turkey"}
    if region in high:
        return 0.15
    if region in um:
        return 0.25
    return 0.40


def psd_member_sum_then_mean(
    psd: pd.DataFrame,
    year0: int = BASELINE_YEARS[0],
    year1: int = BASELINE_YEARS[1],
) -> pd.DataFrame:
    """Sum PSD members within each year, then mean over ``[year0, year1]``.

    Same construction as ``psd_regional_annual()`` followed by a year-mean.
    ``psd`` must already carry a ``region`` column. Stocks are USDA
    ``ending_stocks`` only.
    """
    cols = list(PSD_QTY_COLS)
    window = psd[(psd["year"] >= year0) & (psd["year"] <= year1)]
    return (
        window.groupby(["region", "year"])[cols].sum()
        .groupby("region")
        .mean()
    )


def prepare_wheat(start_year: int = 2003, end_year: int = 2011,
                  params: AgrimateParams | None = None) -> WheatData:
    params = params or AgrimateParams()
    regions = list(REGION_NAMES)
    n_r = len(regions)
    n_y = params.n_year
    notes = [
        "Baseline quantities: USDA PSD 2007–09 member-sum then mean, not FAOSTAT Food Balances (E.1.1).",
        "A8 (S1): multi-country nodes sum PSD members within year (same as psd_regional_annual()), then mean 2007–09.",
        "Stocks are USDA ending_stocks, never FAOSTAT FBSH Stock Variation (element 5074 / ΔS).",
        "Trade pattern: FAOSTAT E0 2006–07, rescaled to USDA exports.",
        "C.1 wheat nodes: Zenodo 14022004 AgrimateRegionsWheat (27 names).",
        "A_d is not E.30. F.1 Egypt 0.17 unused (Egypt is in Northern Africa).",
        "Starred XI*, XD*, C* used in inverse demand are per-step averages.",
        "Anomalies use the already-summed member series (groupby region+year production.sum).",
    ]
    psd = load_psd_country("wheat")
    mapped = psd.copy()
    mapped["region"] = [
        _psd_to_region(c, n) for c, n in zip(mapped["country_code"], mapped["country_psd"])
    ]
    mapped = mapped.dropna(subset=["region"])
    g = psd_member_sum_then_mean(mapped)
    H_ann = np.array([float(g["production"].get(r, 0.0)) for r in regions])
    C_ann = np.array([float(g["consumption"].get(r, 0.0)) for r in regions])
    X_ann = np.array([float(g["exports"].get(r, 0.0)) for r in regions])
    M_ann = np.array([float(g["imports"].get(r, 0.0)) for r in regions])
    S_ann = np.array([float(g["ending_stocks"].get(r, 0.0)) for r in regions])

    E0 = load_trade_matrix("wheat", window=(2006, 2007))
    m = iso3_to_region()
    T = np.zeros((n_r, n_r))
    ridx = {r: i for i, r in enumerate(regions)}
    for iso_e, row in E0.iterrows():
        er = m.get(str(iso_e), "Rest of World")
        if er not in ridx:
            continue
        for iso_i, val in row.items():
            ir = m.get(str(iso_i), "Rest of World")
            if ir not in ridx:
                continue
            T[ridx[er], ridx[ir]] += float(val)
    # drop domestic for international pattern; rescale exports to USDA
    T_int = T.copy()
    np.fill_diagonal(T_int, 0.0)
    row_sum = T_int.sum(axis=1)
    usda_x = np.maximum(X_ann, 0.0)
    for i in range(n_r):
        if row_sum[i] > 0 and usda_x[i] > 0:
            T_int[i] *= usda_x[i] / row_sum[i]
        else:
            T_int[i] = 0.0
    # 1% prune of world international (E.1.6-style)
    world_x = T_int.sum()
    if world_x > 0:
        T_int[T_int < 0.01 * world_x / max(n_r * n_r, 1)] = 0.0
    # domestic flow E.23: remaining production after exports
    domestic = np.maximum(H_ann - T_int.sum(axis=1), 0.0)
    T_star = T_int.copy()
    np.fill_diagonal(T_star, domestic)
    # rebuild consumption from inflows
    C_from_flow = T_star.sum(axis=0)
    use_C = np.where(C_from_flow > 0, C_from_flow, C_ann)
    H_from_flow = T_star.sum(axis=1)
    use_H = np.where(H_from_flow > 0, H_from_flow, H_ann)

    cal = load_harvest_calendar("wheat")
    cal_map = {str(r.country): (int(r.harvest_start_month), int(r.harvest_end_month))
               for r in cal.itertuples()}
    sh = {"Argentina", "Australia", "Brazil", "Rest of Oceania", "Southern Africa",
          "Rest of South America"}
    profile = np.zeros((n_r, n_y))
    for i, r in enumerate(regions):
        if r in cal_map:
            a, b = cal_map[r]
        elif r == "USA":
            a, b = 6, 9
        elif r == "EU-27":
            a, b = 7, 8
        elif r in sh:
            a, b = 11, 1
        else:
            a, b = 6, 8
        profile[i] = step_profile_from_months(a, b, n_y)
    H_star = use_H[:, None] * profile  # MMT per step, sums to annual

    XI_ann = T_int.sum(axis=1)
    XD_ann = np.maximum(use_H - XI_ann, 0.0)
    # per-step starred (inverse demand lives on a step)
    C_star = use_C / n_y
    XI_star = XI_ann / n_y
    XD_star = XD_ann / n_y
    XI_star_path = XI_ann[:, None] * profile
    XD_star_path = XD_ann[:, None] * profile
    XI_world = float(XI_star.sum())

    Psi = np.array([
        float(S_ann[i] / use_C[i]) if use_C[i] > 0 else 0.18 for i in range(n_r)
    ])
    A_c = np.array([_income_ac(r) for r in regions])
    A_d = np.array([
        float(np.clip(0.05 + 0.4 * (M_ann[i] / max(use_C[i], 1e-8)), 0.02, 0.9))
        for i, r in enumerate(regions)
    ])
    alpha_d = np.array([
        D9_ALPHA[r] if r in D9_ALPHA else (
            params.alpha_i * XI_star[i] / XI_world if XI_world > 0 else 1.0)
        for i, r in enumerate(regions)
    ])
    nu = np.array([D9_NU.get(r, 1.0) for r in regions])

    years = list(range(start_year, end_year + 1))
    anomaly = np.zeros((n_r, len(years)))
    # Already-summed member series (A8). Do not re-mean country-year rows here.
    prod = mapped.groupby(["region", "year"])["production"].sum().unstack("year")
    for i, r in enumerate(regions):
        if r not in prod.index:
            continue
        s = prod.loc[r].dropna()
        if len(s) < 8:
            continue
        an = detrend_anomalies(s, window_years=10)["anomaly"]
        for j, y in enumerate(years):
            if y in an.index and y >= 2005:
                anomaly[i, j] = float(an.loc[y])

    delta = restriction_matrix(regions, start_year, end_year, crop="wheat")
    n_bind = int((delta > 0).sum())
    bound = [r for i, r in enumerate(regions) if float(delta[i].max()) > 0]
    notes.append(
        f"AMIS wheat Δ: {n_bind} region-steps, max={float(delta.max()):.2f}, "
        f"regions={bound or 'none'}."
    )
    pink = load_price_series_monthly()
    p0 = float(pink[(pink["year"] == 2006)]["wheat"].mean())
    return WheatData(
        regions=regions, H_star=H_star, H_annual=use_H, C_star=C_star,
        XI_star=XI_star, XD_star=XD_star,
        XI_star_path=XI_star_path, XD_star_path=XD_star_path,
        XI_world=XI_world, T_star=T_star,
        Psi=Psi, A_c=A_c, A_d=A_d, alpha_d=alpha_d, nu=nu, profile=profile,
        anomaly=anomaly, delta=delta, p0=p0, start_year=start_year,
        end_year=end_year, notes=notes,
    )


def international_destination_shares(T_star: np.ndarray) -> np.ndarray:
    """Row-normalised international T* (exporter → importer).

    Domestic diagonal is dropped. An exporter with no international partners
    keeps a unit weight on itself so XI is not deleted. This is E.1 pattern
    routing, not D.30 CES reallocation.
    """
    T = np.asarray(T_star, float).copy()
    np.fill_diagonal(T, 0.0)
    row = T.sum(axis=1, keepdims=True)
    dest = np.divide(T, np.maximum(row, 1e-12))
    empty = row.ravel() <= 1e-12
    dest[empty, :] = 0.0
    for r in np.where(empty)[0]:
        dest[r, r] = 1.0
    return dest


def psd_regional_annual(regions: list[str] | None = None) -> pd.DataFrame:
    """USDA PSD wheat, aggregated to Agrimate wheat nodes (MMT / marketing year).

    Coverage is incomplete: multi-country regions only include PSD members that
    map through the conversion table. Use world-aggregate USDA for global scores.
    """
    regions = list(regions or REGION_NAMES)
    psd = load_psd_country("wheat")
    psd = psd.copy()
    psd["region"] = [_psd_to_region(c, n) for c, n in zip(psd["country_code"], psd["country_psd"])]
    psd = psd.dropna(subset=["region"])
    psd = psd[psd["region"].isin(regions)]
    g = psd.groupby(["region", "year"])[list(PSD_QTY_COLS)].sum().reset_index()
    return g
