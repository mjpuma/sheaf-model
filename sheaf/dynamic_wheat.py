"""Minimal Agrimate-aligned wheat dynamics (Gate 0).

24 steps/year. Out-of-equilibrium stock–trade with exogenous AMIS export cuts.

Within-year timing (Gate 0 hard requirement)
--------------------------------------------
1. **Harvest calendars** — triangular peak-month weights
   (`sheaf.seasonal`, `data/crop_calendars/wheat_harvest_months.csv`).
2. **Lean-horizon foresight** — agents look ahead to the next global harvest
   pulse; target stocks = max(0, C_lean − H_lean) + safety. Grain is carried
   in warehouses (not dumped after harvest).
3. **Seasonal-baseline pricing** — free stocks (= inventory − lean need) are
   scored against a mean-year / no-AMIS twin path by calendar step, so the
   expected spring lean is not a crisis.
4. **Structural AMIS pressure** — export cuts weighted by each node's mean
   annual surplus (not by the seasonally varying exportable pile), so harvest
   months do not mechanically inflate restriction pressure.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .calendar24 import STEPS_PER_YEAR, n_steps
from .data_usda import load_amis_restrictions, load_psd_country
from .seasonal import (
    harvest_path,
    load_wheat_harvest_calendar,
    rolling_ahead_variable,
    steps_to_harvest_pulse,
)

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

MAX_LEAN_STEPS = STEPS_PER_YEAR
HARVEST_PULSE_FRAC = 0.12  # ~12% of annual world H ≈ one NH peak month


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


def _structural_surplus(H: np.ndarray, C_ann: np.ndarray) -> np.ndarray:
    """Mean annual production − consumption, floored at 0 (MMT/year)."""
    n, T = H.shape
    n_years = max(T // STEPS_PER_YEAR, 1)
    H_ann = H[:, : n_years * STEPS_PER_YEAR].reshape(
        n, n_years, STEPS_PER_YEAR).sum(axis=2).mean(axis=1)
    return np.maximum(H_ann - C_ann, 0.0)


def _simulate_window(
        H: np.ndarray,
        C_step: np.ndarray,
        cuts: np.ndarray,
        stock0: np.ndarray,
        safety: np.ndarray,
        p0: float,
        elast: float,
        inv_eta: float,
        smooth: float,
        C_ann: np.ndarray,
        surplus: np.ndarray,
        seasonal_free: np.ndarray | None = None,
        pulse_frac: float = HARVEST_PULSE_FRAC,
        record_free: bool = False,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray | None]:
    """Core loop with lean foresight + optional seasonal-baseline pricing.

    If ``seasonal_free`` is None, prices stay near ``p0`` (baseline twin pass).
    If provided (length 24), free-stock anomalies vs that calendar profile
    drive the scarcity term.
    """
    n, T = H.shape
    stock = stock0.copy()
    price = np.zeros(T)
    stock_path = np.zeros((n, T))
    cons_path = np.zeros((n, T))
    exp_path = np.zeros((n, T))
    free_path = np.zeros(T) if record_free else None
    p = float(p0)
    safety_w = float(safety.sum())
    surplus_w = float(max(surplus.sum(), 1e-9))
    warehouse = np.maximum(1.5 * C_ann, 3.0 * safety)

    lean_h = steps_to_harvest_pulse(H, frac=pulse_frac,
                                    max_horizon=MAX_LEAN_STEPS)
    H_ahead = rolling_ahead_variable(H, lean_h)
    C_ahead = rolling_ahead_variable(C_step, lean_h)

    for t in range(T):
        avail = stock + H[:, t]
        desired = np.maximum(C_step[:, t] * (p / p0) ** elast, 0.0)

        lean_gap = np.maximum(
            0.0,
            C_ahead[:, t] + C_step[:, t] - H_ahead[:, t] - H[:, t],
        )
        target = lean_gap + safety

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
        stock = np.minimum(stock, warehouse)

        lean_need = float(lean_gap.sum())
        free = float(stock.sum()) - lean_need
        if free_path is not None:
            free_path[t] = free

        # Structural AMIS: surplus-weighted mean cut (seasonally flat for a
        # given policy set; jumps when Russia/Ukraine bans turn on).
        amis_pressure = float((cuts[:, t] * surplus).sum()) / surplus_w
        unmet = float(np.maximum(0.0, desired - consumption).sum())
        unmet_frac = unmet / max(float(desired.sum()), 1e-9)

        if seasonal_free is None:
            # Baseline twin: hold near p0 (only mild unmet feedback).
            p_star = p0 * (1.0 + 0.25 * unmet_frac)
        else:
            base = float(seasonal_free[t % STEPS_PER_YEAR])
            level = free + safety_w
            base_level = base + safety_w
            # ratio > 1 when free is below the seasonal normal.
            ratio = base_level / max(level, 0.08 * safety_w)
            p_star = (p0 * (ratio ** inv_eta)
                      * (1.0 + 1.6 * amis_pressure + 1.1 * unmet_frac))

        p = float(smooth * p + (1.0 - smooth) * p_star)
        p = float(np.clip(p, 80.0, 900.0))

        price[t] = p
        stock_path[:, t] = stock
        cons_path[:, t] = consumption
        exp_path[:, t] = shipped

    return price, stock_path, cons_path, exp_path, free_path


def run_wheat_dynamics(
        countries: list[str] | None = None,
        start_year: int = 2006,
        end_year: int = 2011,
        p0: float | None = None,
        elast: float = -0.12,
        inv_eta: float = 0.50,
        smooth: float = 0.55,
        stu_target: float = 0.18,
        use_amis: bool = True,
        use_shocks: bool = True,
        stock_seed_year: int = 2005,
        spin_up_years: int = 2,
) -> WheatSimResult:
    """Run the Gate 0 wheat spine with lean foresight + seasonal baseline."""
    if countries is None:
        from .calibration import DATA
        countries = [d["name"] for d in DATA] + ["RestOfWorld"]

    if p0 is None:
        p0 = _anchor_p0(year=min(start_year, 2006))

    years = list(range(start_year, end_year + 1))
    n = len(countries)
    cal = load_wheat_harvest_calendar()

    prod_score, cons_score = _psd_wheat_annual(countries, years)
    C_ann = np.zeros(n)
    for i, c in enumerate(countries):
        sub = cons_score[cons_score["country"] == c]
        C_ann[i] = float(sub["consumption"].mean()) if len(sub) else 0.0
    safety = stu_target * C_ann

    mean_prod = (prod_score.groupby("country", as_index=False)["production"]
                 .mean())

    def _C_for(H: np.ndarray, cons_df: pd.DataFrame,
               yrs: list[int]) -> np.ndarray:
        T = H.shape[1]
        out = np.zeros((n, T))
        for yi, y in enumerate(yrs):
            for i, c in enumerate(countries):
                hit = cons_df[(cons_df.country == c) & (cons_df.year == y)]
                ann = float(hit.consumption.iloc[0]) if len(hit) else C_ann[i]
                out[i, yi * STEPS_PER_YEAR:(yi + 1) * STEPS_PER_YEAR] = (
                    ann / STEPS_PER_YEAR)
        return out

    # --- spin-up on mean harvest, no AMIS ---
    spin_stock = _ending_stocks(countries, stock_seed_year)
    if spin_up_years > 0:
        spin_years = list(range(start_year - spin_up_years, start_year))
        tiled = pd.concat([mean_prod.assign(year=y) for y in spin_years],
                          ignore_index=True)
        H_spin = harvest_path(countries, tiled, spin_years[0], spin_years[-1],
                              calendar=cal)
        C_spin = np.tile((C_ann / STEPS_PER_YEAR)[:, None],
                         (1, H_spin.shape[1]))
        surplus_spin = _structural_surplus(H_spin, C_ann)
        _, stock_path_s, _, _, _ = _simulate_window(
            H_spin, C_spin, np.zeros_like(H_spin), spin_stock, safety,
            p0, elast, inv_eta, smooth, C_ann, surplus_spin,
            seasonal_free=None)
        spin_stock = stock_path_s[:, -1]

    # --- seasonal free-stock baseline (mean harvest, no AMIS) ---
    tiled_base = pd.concat([mean_prod.assign(year=y) for y in years],
                           ignore_index=True)
    H_base = harvest_path(countries, tiled_base, start_year, end_year,
                          calendar=cal)
    C_base = np.tile((C_ann / STEPS_PER_YEAR)[:, None], (1, H_base.shape[1]))
    surplus_base = _structural_surplus(H_base, C_ann)
    _, _, _, _, free_base = _simulate_window(
        H_base, C_base, np.zeros_like(H_base), spin_stock.copy(), safety,
        p0, elast, inv_eta, smooth, C_ann, surplus_base,
        seasonal_free=None, record_free=True)
    seasonal_free = np.array([
        float(free_base[s::STEPS_PER_YEAR].mean())
        for s in range(STEPS_PER_YEAR)
    ])

    # --- crisis / counterfactual path ---
    if use_shocks:
        prod_use = prod_score
    else:
        prod_use = tiled_base
    H = harvest_path(countries, prod_use, start_year, end_year, calendar=cal)
    C_step = _C_for(H, cons_score, years)
    surplus = _structural_surplus(H, C_ann)
    cuts = (amis_export_cuts(countries, start_year, end_year)
            if use_amis else np.zeros_like(H))

    price, stock_path, cons_path, exp_path, _ = _simulate_window(
        H, C_step, cuts, spin_stock, safety,
        p0, elast, inv_eta, smooth, C_ann, surplus,
        seasonal_free=seasonal_free)

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
