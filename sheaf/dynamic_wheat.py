"""Minimal Agrimate-aligned wheat dynamics (Gate 0 prototype).

24 steps/year. Out-of-equilibrium stock–trade adjustment with exogenous AMIS
export quantity cuts. Single commodity (wheat). Not a full Agrimate agent
clone — a thin spine to score monthly prices before adding multi-commodity
and the endogenous game.

State (per node i, each step t):
  stock_i,  local availability after harvest
World:
  p_t  world price index ($/t)

Step:
  1. harvest arrives
  2. desired consumption from isoelastic demand at last price
  3. exportable surplus = max(0, avail - desired - buffer), × (1 - AMIS cut)
  4. import demand from shortfall nodes
  5. ration exportable pool to importers
  6. carry stocks; update world price from excess demand / stock-to-use
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .calendar24 import STEPS_PER_YEAR, n_steps
from .data_usda import load_amis_restrictions, load_psd_country
from .seasonal import harvest_path, load_wheat_harvest_calendar

# Agrimate-style quantity cuts on exportable surplus
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
    price: np.ndarray          # (T,) world $/t
    stock: np.ndarray          # (n, T) end-of-step stocks
    harvest: np.ndarray        # (n, T)
    consumption: np.ndarray    # (n, T)
    exports: np.ndarray        # (n, T) gross exports
    export_cut: np.ndarray     # (n, T) AMIS cut fraction applied


def _psd_wheat_annual(countries: list[str],
                      years: list[int]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (production table, consumption table) country–year MMT."""
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
    named = [c for c in countries if c != "RestOfWorld"]
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
    """(n, T) export-cut fraction in [0, 1]; strongest overlapping measure wins."""
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
        y0 = int(row["Start_Date"].year)
        m0 = int(row["Start_Date"].month)
        if pd.notna(row["End_Date"]):
            y1 = int(row["End_Date"].year)
            m1 = int(row["End_Date"].month)
        else:
            y1, m1 = y0, m0
        i = name_to_i[sheaf]
        # mark all steps whose (year, month) overlaps [start, end]
        t = 0
        for year in range(start_year, end_year + 1):
            for month in range(1, 13):
                for _half in (0, 1):
                    if (year, month) >= (y0, m0) and (year, month) <= (y1, m1):
                        cuts[i, t] = max(cuts[i, t], cut)
                    t += 1
    return cuts


def run_wheat_dynamics(
        countries: list[str] | None = None,
        start_year: int = 2006,
        end_year: int = 2011,
        p0: float = 250.0,
        elast: float = -0.25,
        kappa: float = 0.08,
        buffer_frac: float = 0.08,
        use_amis: bool = True,
        stock_seed_year: int = 2005,
) -> WheatSimResult:
    """Run the Gate 0 wheat spine. Returns step-level series."""
    if countries is None:
        from .calibration import DATA
        countries = [d["name"] for d in DATA] + ["RestOfWorld"]

    years = list(range(start_year, end_year + 1))
    n = len(countries)
    T = n_steps(start_year, end_year)

    prod, cons = _psd_wheat_annual(countries, years)
    C_ann = np.zeros(n)
    for i, c in enumerate(countries):
        sub = cons[cons["country"] == c]
        C_ann[i] = float(sub["consumption"].mean()) if len(sub) else 0.0
    C_step = C_ann / STEPS_PER_YEAR

    H = harvest_path(countries, prod, start_year, end_year,
                     calendar=load_wheat_harvest_calendar())
    cuts = (amis_export_cuts(countries, start_year, end_year)
            if use_amis else np.zeros((n, T)))

    stock = _ending_stocks(countries, stock_seed_year)
    buffer = buffer_frac * C_ann

    price = np.zeros(T)
    stock_path = np.zeros((n, T))
    cons_path = np.zeros((n, T))
    exp_path = np.zeros((n, T))
    p = float(p0)
    # Target stocks ≈ 0.25 years of consumption ≈ 6 steps of C_step
    stu_target = 6.0

    for t in range(T):
        avail = stock + H[:, t]
        desired = C_step * (p / p0) ** elast
        desired = np.maximum(desired, 0.0)

        exportable = np.maximum(0.0, avail - desired - buffer)
        exportable *= (1.0 - cuts[:, t])

        need = np.maximum(0.0, desired - avail)
        total_need = float(need.sum())
        total_exp = float(exportable.sum())

        shipped = np.zeros(n)
        received = np.zeros(n)
        if total_exp > 1e-12 and total_need > 1e-12:
            fill = min(1.0, total_exp / total_need)
            received = need * fill
            shipped = exportable * (received.sum() / total_exp)

        consumption = np.minimum(desired, avail - shipped + received)
        stock = np.maximum(0.0, avail - shipped - consumption + received)

        # Damped log-price update from STU gap + unmet import demand
        stu_steps = float(stock.sum()) / max(float(C_step.sum()), 1e-9)
        unmet = float(np.maximum(0.0, desired - consumption).sum())
        unmet_frac = unmet / max(float(desired.sum()), 1e-9)
        stu_gap = (stu_target - stu_steps) / stu_target
        signal = float(np.clip(0.5 * stu_gap + 0.5 * unmet_frac, -0.5, 0.5))
        p = float(p * np.exp(kappa * signal))
        p = float(np.clip(p, 80.0, 800.0))

        price[t] = p
        stock_path[:, t] = stock
        cons_path[:, t] = consumption
        exp_path[:, t] = shipped

    return WheatSimResult(
        countries=countries, start_year=start_year, end_year=end_year,
        price=price, stock=stock_path, harvest=H, consumption=cons_path,
        exports=exp_path, export_cut=cuts,
    )


def result_to_monthly(res: WheatSimResult) -> pd.DataFrame:
    """Aggregate step prices (and world stock) to monthly means."""
    from .calendar24 import monthly_mean_from_steps
    px = monthly_mean_from_steps(res.price, res.start_year, res.end_year)
    stu = monthly_mean_from_steps(res.stock.sum(axis=0),
                                  res.start_year, res.end_year)
    rows = []
    for a, b in zip(px, stu):
        rows.append(dict(year=a["year"], month=a["month"],
                         model_price=a["value"], world_stock=b["value"]))
    return pd.DataFrame(rows)
