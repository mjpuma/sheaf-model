"""Minimal Agrimate-aligned wheat dynamics (Gate 0 prototype).

24 steps/year. Out-of-equilibrium stock–trade adjustment with exogenous AMIS
export quantity cuts. Single commodity (wheat).

Improvements vs first cut:
  * 2-year spin-up on mean seasonal harvest (Agrimate uses 4y; we start lighter)
  * commercial stock *targets* (release above target, rebuild below)
  * year-specific PSD consumption
  * inverse-demand world price on liquid (above-target) supply
  * p0 anchored to observed 2006 Pink Sheet mean when available
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .calendar24 import STEPS_PER_YEAR, n_steps
from .data_usda import load_amis_restrictions, load_psd_country
from .seasonal import harvest_path, load_wheat_harvest_calendar

_AMIS_CUT = {
    "Export prohibition": 0.95,
    "Export quota": 0.70,
    "Export tax": 0.50,
    "Minimum export price": 0.35,
    "Licensing requirement": 0.25,
    "Restriction on customs clearance point for exports": 0.15,
}
_AMIS_COUNTRY = {
    "Argentina": "Argentina", "Australia": "Australia", "China": "China",
    "Egypt": "Egypt", "India": "India", "Indonesia": "Indonesia",
    "Kazakhstan": "Kazakhstan", "Mexico": "Mexico",
    "Russian Federation": "Russia", "Ukraine": "Ukraine",
    "Viet Nam": "Vietnam",
}


@dataclass
class WheatSimResult:
    countries: list[str]
    start_year: int
    end_year: int
    price: np.ndarray
    stock: np.ndarray
    harvest: np.ndarray
    consumption: np.ndarray
    exports: np.ndarray
    export_cut: np.ndarray
    spin_up_years: int = 0


def _psd_wheat_annual(countries: list[str],
                      years: list[int]) -> tuple[pd.DataFrame, pd.DataFrame]:
    psd = load_psd_country("wheat")
    prod_rows, cons_rows = [], []
    named = [c for c in countries if c != "RestOfWorld"]
    for y in years:
        sub = psd[psd["year"] == y]
        world_p = float(sub["production"].sum())
        world_c = float(sub["consumption"].sum())
        named_p = named_c = 0.0
        for c in named:
            hit = sub[sub["country"] == c]
            p = float(hit["production"].iloc[0]) if len(hit) else 0.0
            q = float(hit["consumption"].iloc[0]) if len(hit) else 0.0
            prod_rows.append(dict(country=c, year=y, production=p))
            cons_rows.append(dict(country=c, year=y, consumption=q))
            named_p += p
            named_c += q
        if "RestOfWorld" in countries:
            prod_rows.append(dict(country="RestOfWorld", year=y,
                                  production=max(world_p - named_p, 0.0)))
            cons_rows.append(dict(country="RestOfWorld", year=y,
                                  consumption=max(world_c - named_c, 0.0)))
    return pd.DataFrame(prod_rows), pd.DataFrame(cons_rows)


def _ending_stocks(countries: list[str], year: int) -> np.ndarray:
    psd = load_psd_country("wheat")
    sub = psd[psd["year"] == year]
    world = float(sub["ending_stocks"].sum())
    out = np.zeros(len(countries))
    named_s = 0.0
    for i, c in enumerate(countries):
        if c == "RestOfWorld":
            continue
        hit = sub[sub["country"] == c]
        s = float(hit["ending_stocks"].iloc[0]) if len(hit) else 0.0
        out[i] = max(s, 0.0)
        named_s += out[i]
    if "RestOfWorld" in countries:
        out[countries.index("RestOfWorld")] = max(world - named_s, 0.0)
    return out


def amis_export_cuts(countries: list[str],
                     start_year: int, end_year: int) -> np.ndarray:
    """(n, T) export-cut fraction; strongest overlapping measure wins."""
    n = len(countries)
    T = n_steps(start_year, end_year)
    cuts = np.zeros((n, T))
    name_to_i = {c: i for i, c in enumerate(countries)}
    amis = load_amis_restrictions(aggregated=True)
    amis = amis[amis["CommodityClass_Name"].astype(str) == "Wheat"]
    for _, row in amis.iterrows():
        sheaf = _AMIS_COUNTRY.get(row["Country_Name"])
        if sheaf is None or sheaf not in name_to_i:
            continue
        cut = _AMIS_CUT.get(str(row["PolicyMeasure_Name"]), 0.0)
        if cut <= 0 or pd.isna(row["Start_Date"]):
            continue
        y0, m0 = int(row["Start_Date"].year), int(row["Start_Date"].month)
        if pd.notna(row["End_Date"]):
            y1, m1 = int(row["End_Date"].year), int(row["End_Date"].month)
        else:
            y1, m1 = y0, m0
        i = name_to_i[sheaf]
        t = 0
        for year in range(start_year, end_year + 1):
            for month in range(1, 13):
                for _ in (0, 1):
                    if (y0, m0) <= (year, month) <= (y1, m1):
                        cuts[i, t] = max(cuts[i, t], cut)
                    t += 1
    return cuts


def _anchor_p0(default: float = 250.0, year: int = 2006) -> float:
    try:
        from .data_usda import load_price_series_monthly
        m = load_price_series_monthly(deflated=True)
        sub = m[m["year"] == year]["wheat"].dropna()
        if len(sub):
            return float(sub.mean())
    except (FileNotFoundError, KeyError, ValueError):
        pass
    return default


def _simulate_window(
        countries: list[str],
        H: np.ndarray,
        C_step: np.ndarray,
        cuts: np.ndarray,
        stock0: np.ndarray,
        target: np.ndarray,
        p0: float,
        elast: float,
        inv_eta: float,
        smooth: float,
        C_ann: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Core loop. Price tracks annualized STU + AMIS pressure (not harvest season)."""
    n, T = H.shape
    stock = stock0.copy()
    price = np.zeros(T)
    stock_path = np.zeros((n, T))
    cons_path = np.zeros((n, T))
    exp_path = np.zeros((n, T))
    p = float(p0)
    world_C = float(max(C_ann.sum(), 1.0))
    stu0 = float(stock.sum()) / world_C

    for t in range(T):
        avail = stock + H[:, t]
        desired = np.maximum(C_step[:, t] * (p / p0) ** elast, 0.0)

        after_food = np.maximum(0.0, avail - desired)
        exportable_raw = np.maximum(0.0, after_food - target)
        need = np.maximum(0.0, desired - avail)
        exportable = exportable_raw * (1.0 - cuts[:, t])

        total_need = float(need.sum())
        total_exp = float(exportable.sum())
        shipped = np.zeros(n)
        received = np.zeros(n)
        if total_exp > 1e-12 and total_need > 1e-12:
            fill = min(1.0, total_exp / total_need)
            received = need * fill
            shipped = exportable * (received.sum() / max(total_exp, 1e-12))

        consumption = np.minimum(desired, avail - shipped + received)
        stock = np.maximum(0.0, avail - shipped - consumption + received)
        # Free disposal / residual use above a soft capacity so bumper crops
        # cannot pile stocks without bound (keeps STU near PSD scale).
        cap = 1.55 * target
        dump = np.maximum(0.0, stock - cap)
        stock = stock - dump

        # Annualized STU (fraction of annual world consumption)
        stu = float(stock.sum()) / world_C
        blocked = float((exportable_raw * cuts[:, t]).sum())
        potential = float(exportable_raw.sum()) + 1e-9
        amis_pressure = blocked / potential
        unmet = float(np.maximum(0.0, desired - consumption).sum())
        unmet_frac = unmet / max(float(desired.sum()), 1e-9)

        stu_term = (stu0 / max(stu, 0.05)) ** inv_eta
        p_star = p0 * stu_term * (1.0 + 1.5 * amis_pressure + 1.0 * unmet_frac)
        p = float(smooth * p + (1.0 - smooth) * p_star)
        p = float(np.clip(p, 80.0, 900.0))

        price[t] = p
        stock_path[:, t] = stock
        cons_path[:, t] = consumption
        exp_path[:, t] = shipped

    return price, stock_path, cons_path, exp_path


def run_wheat_dynamics(
        countries: list[str] | None = None,
        start_year: int = 2006,
        end_year: int = 2011,
        p0: float | None = None,
        elast: float = -0.12,
        inv_eta: float = 0.65,
        smooth: float = 0.55,
        stu_target: float = 0.22,
        use_amis: bool = True,
        use_shocks: bool = True,
        stock_seed_year: int = 2005,
        spin_up_years: int = 2,
) -> WheatSimResult:
    """Run the Gate 0 wheat spine (optional spin-up, AMIS, interannual shocks)."""
    if countries is None:
        from .calibration import DATA
        countries = [d["name"] for d in DATA] + ["RestOfWorld"]

    if p0 is None:
        p0 = _anchor_p0(year=min(start_year, 2006))

    years = list(range(start_year, end_year + 1))
    n = len(countries)
    cal = load_wheat_harvest_calendar()

    # --- Spin-up on mean seasonal harvest, no AMIS ---
    spin_stock = _ending_stocks(countries, stock_seed_year)
    prod_score, cons_score = _psd_wheat_annual(countries, years)
    C_ann = np.zeros(n)
    for i, c in enumerate(countries):
        sub = cons_score[cons_score["country"] == c]
        C_ann[i] = float(sub["consumption"].mean()) if len(sub) else 0.0
    target = stu_target * C_ann

    if spin_up_years > 0:
        mean_prod = (prod_score.groupby("country", as_index=False)["production"]
                     .mean())
        spin_years = list(range(start_year - spin_up_years, start_year))
        # If PSD missing for early years, tile mean production
        tiled = pd.concat([mean_prod.assign(year=y) for y in spin_years],
                          ignore_index=True)
        H_spin = harvest_path(countries, tiled, spin_years[0], spin_years[-1],
                              calendar=cal)
        C_spin = np.tile((C_ann / STEPS_PER_YEAR)[:, None],
                         (1, H_spin.shape[1]))
        cuts0 = np.zeros_like(H_spin)
        _, stock_path_s, _, _ = _simulate_window(
            countries, H_spin, C_spin, cuts0, spin_stock, target,
            p0, elast, inv_eta, smooth, C_ann)
        spin_stock = stock_path_s[:, -1]

    # --- Score window ---
    if use_shocks:
        prod_use = prod_score
    else:
        mean_prod = (prod_score.groupby("country", as_index=False)["production"]
                     .mean())
        prod_use = pd.concat([mean_prod.assign(year=y) for y in years],
                             ignore_index=True)

    H = harvest_path(countries, prod_use, start_year, end_year, calendar=cal)
    T = H.shape[1]
    # Year-specific per-step consumption
    C_step = np.zeros((n, T))
    for yi, y in enumerate(years):
        for i, c in enumerate(countries):
            hit = cons_score[(cons_score.country == c) & (cons_score.year == y)]
            ann = float(hit.consumption.iloc[0]) if len(hit) else C_ann[i]
            C_step[i, yi * STEPS_PER_YEAR:(yi + 1) * STEPS_PER_YEAR] = (
                ann / STEPS_PER_YEAR)

    cuts = (amis_export_cuts(countries, start_year, end_year)
            if use_amis else np.zeros((n, T)))

    price, stock_path, cons_path, exp_path = _simulate_window(
        countries, H, C_step, cuts, spin_stock, target,
        p0, elast, inv_eta, smooth, C_ann)

    return WheatSimResult(
        countries=countries, start_year=start_year, end_year=end_year,
        price=price, stock=stock_path, harvest=H, consumption=cons_path,
        exports=exp_path, export_cut=cuts, spin_up_years=spin_up_years,
    )


def result_to_monthly(res: WheatSimResult) -> pd.DataFrame:
    from .calendar24 import monthly_mean_from_steps
    px = monthly_mean_from_steps(res.price, res.start_year, res.end_year)
    stu = monthly_mean_from_steps(res.stock.sum(axis=0),
                                  res.start_year, res.end_year)
    return pd.DataFrame([
        dict(year=a["year"], month=a["month"],
             model_price=a["value"], world_stock=b["value"])
        for a, b in zip(px, stu)
    ])
