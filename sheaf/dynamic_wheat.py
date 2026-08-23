"""Minimal Agrimate-aligned wheat dynamics (Gate 0).

24 steps/year. Out-of-equilibrium stock–trade with exogenous AMIS export cuts.

Within-year timing (robustness rules)
-------------------------------------
1. **Harvest calendars** — triangular peak-month weights (`sheaf.seasonal`).
2. **Lean-horizon foresight** — targets = max(0, C_lean − H_lean) + safety;
   warehouses carry grain (no binding dump of harvest).
3. **Path-matched twin pricing** — every run has a twin with the same
   year-by-year demand, mean harvest, and no AMIS. Price responds only to
   *liquid* free-stock anomalies (inventory behind export cuts is not
   world-available) and to unmet demand after trade rationing.
   ⇒ no additive AMIS wedge; ⇒ (no shocks, no AMIS) ≈ flat at p0.
4. **AMIS quantity cuts** affect the physical exportable set; price feels
   them via trapped stocks + unmet imports, not a reduced-form surcharge.
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
HARVEST_PULSE_FRAC = 0.12


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
    # Diagnostics for robustness checks
    free_liquid: np.ndarray | None = None
    free_twin: np.ndarray | None = None
    unmet_frac: np.ndarray | None = None


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


def _consumption_path(countries: list[str], cons_score: pd.DataFrame,
                      C_ann: np.ndarray, years: list[int],
                      T: int) -> np.ndarray:
    """Year-specific demand, flat within year (MMT per step)."""
    n = len(countries)
    out = np.zeros((n, T))
    for yi, y in enumerate(years):
        for i, c in enumerate(countries):
            hit = cons_score[(cons_score.country == c) & (cons_score.year == y)]
            ann = float(hit.consumption.iloc[0]) if len(hit) else C_ann[i]
            out[i, yi * STEPS_PER_YEAR:(yi + 1) * STEPS_PER_YEAR] = (
                ann / STEPS_PER_YEAR)
    return out


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
        free_twin: np.ndarray | None = None,
        pulse_frac: float | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray,
           np.ndarray, np.ndarray]:
    """Physical stock–trade loop; price from liquid free vs path-matched twin.

    ``free_twin`` is length T from the mean-H / no-AMIS twin. If None, this
    pass *is* the twin: prices stay near p0 and liquid free is recorded.
    """
    if pulse_frac is None:
        pulse_frac = HARVEST_PULSE_FRAC
    n, T = H.shape
    stock = stock0.copy()
    price = np.zeros(T)
    stock_path = np.zeros((n, T))
    cons_path = np.zeros((n, T))
    exp_path = np.zeros((n, T))
    free_path = np.zeros(T)
    unmet_path = np.zeros(T)
    p = float(p0)
    safety_w = float(max(safety.sum(), 1.0))
    # Soft capacity only — large enough not to destroy ordinary harvest carry.
    warehouse = np.maximum(4.0 * C_ann, 8.0 * safety)

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
        # Soft warehouse: only trim extreme overflow (should rarely bind).
        overflow = np.maximum(0.0, stock - warehouse)
        stock = stock - overflow

        lean_need = float(lean_gap.sum())
        # Liquid stocks: grain behind export cuts is not available to the
        # world market (Agrimate-style trade friction).
        liquid = float((stock * (1.0 - cuts[:, t])).sum())
        free = liquid - lean_need
        free_path[t] = free

        unmet = float(np.maximum(0.0, desired - consumption).sum())
        unmet_frac = unmet / max(float(desired.sum()), 1e-9)
        unmet_path[t] = unmet_frac

        if free_twin is None:
            # Twin pass: hold p0 so free_twin is a pure physical baseline.
            p_star = p0
        else:
            twin = float(free_twin[t])
            # Small floor only — do NOT add full safety_w to both sides
            # (that compressed scarcity ratios toward 1 and killed AMIS signal).
            floor = 0.05 * safety_w
            ratio = (twin + floor) / max(free + floor, floor)
            # Physical channels only: free anomaly + unmet after rationing.
            p_star = p0 * (ratio ** inv_eta) * (1.0 + 3.0 * unmet_frac)

        p = float(smooth * p + (1.0 - smooth) * p_star)
        p = float(np.clip(p, 80.0, 900.0))

        price[t] = p
        stock_path[:, t] = stock
        cons_path[:, t] = consumption
        exp_path[:, t] = shipped

    return price, stock_path, cons_path, exp_path, free_path, unmet_path


def run_wheat_dynamics(
        countries: list[str] | None = None,
        start_year: int = 2006,
        end_year: int = 2011,
        p0: float | None = None,
        elast: float = -0.12,
        inv_eta: float = 0.85,
        smooth: float = 0.70,
        stu_target: float = 0.18,
        use_amis: bool = True,
        use_shocks: bool = True,
        stock_seed_year: int = 2005,
        spin_up_years: int = 2,
) -> WheatSimResult:
    """Run Gate 0 wheat spine with path-matched twin pricing."""
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
    tiled_mean = pd.concat([mean_prod.assign(year=y) for y in years],
                           ignore_index=True)

    # --- spin-up: mean harvest, mean-year demand rate, no AMIS ---
    spin_stock = _ending_stocks(countries, stock_seed_year)
    if spin_up_years > 0:
        spin_years = list(range(start_year - spin_up_years, start_year))
        tiled_spin = pd.concat([mean_prod.assign(year=y) for y in spin_years],
                               ignore_index=True)
        H_spin = harvest_path(countries, tiled_spin, spin_years[0],
                              spin_years[-1], calendar=cal)
        C_spin = np.tile((C_ann / STEPS_PER_YEAR)[:, None],
                         (1, H_spin.shape[1]))
        _, stock_path_s, _, _, _, _ = _simulate_window(
            H_spin, C_spin, np.zeros_like(H_spin), spin_stock, safety,
            p0, elast, inv_eta, smooth, C_ann, free_twin=None)
        spin_stock = stock_path_s[:, -1]

    # Shared year-by-year demand for twin and treatment.
    T = len(years) * STEPS_PER_YEAR
    C_step = _consumption_path(countries, cons_score, C_ann, years, T)

    # Twin: mean harvest, same C_step, no AMIS.
    H_twin = harvest_path(countries, tiled_mean, start_year, end_year,
                          calendar=cal)
    _, _, _, _, free_twin, _ = _simulate_window(
        H_twin, C_step, np.zeros_like(H_twin), spin_stock.copy(), safety,
        p0, elast, inv_eta, smooth, C_ann, free_twin=None)

    # Treatment harvest / cuts.
    if use_shocks:
        H = harvest_path(countries, prod_score, start_year, end_year,
                         calendar=cal)
    else:
        H = H_twin.copy()
    cuts = (amis_export_cuts(countries, start_year, end_year)
            if use_amis else np.zeros((n, T)))

    # Identity check path: when H==H_twin and cuts==0, free must match twin
    # and prices stay near p0 (enforced by using free_twin in pricing).
    price, stock_path, cons_path, exp_path, free_liq, unmet = _simulate_window(
        H, C_step, cuts, spin_stock.copy(), safety,
        p0, elast, inv_eta, smooth, C_ann, free_twin=free_twin)

    return WheatSimResult(
        countries=countries, start_year=start_year, end_year=end_year,
        price=price, stock=stock_path, harvest=H, consumption=cons_path,
        exports=exp_path, export_cut=cuts, spin_up_years=spin_up_years,
        free_liquid=free_liq, free_twin=free_twin, unmet_frac=unmet,
    )


def assert_twin_identity(tol_price: float = 0.02,
                         tol_free: float = 1.0) -> None:
    """Hard robustness check: no shocks + no AMIS ⇒ ≈ twin ⇒ flat near p0."""
    res = run_wheat_dynamics(use_amis=False, use_shocks=False)
    p0 = float(res.price[0])
    # After short burn-in, prices should hug p0.
    tail = res.price[STEPS_PER_YEAR:]
    rel = np.max(np.abs(tail - p0)) / max(p0, 1.0)
    if rel > tol_price:
        raise AssertionError(
            f"neither-path price drift {rel:.3%} > {tol_price:.3%} "
            f"(p0={p0:.1f}, range=[{tail.min():.1f},{tail.max():.1f}])")
    if res.free_liquid is None or res.free_twin is None:
        raise AssertionError("free paths not recorded")
    free_err = float(np.max(np.abs(res.free_liquid - res.free_twin)))
    if free_err > tol_free:
        raise AssertionError(
            f"neither-path free≠twin max|Δ|={free_err:.3f} > {tol_free}")


def assert_amis_raises_price(min_lift: float = 0.08) -> None:
    """Tau-only: Russia-ban window must lift prices vs pre-ban baseline."""
    res = run_wheat_dynamics(use_amis=True, use_shocks=False)
    # Jun 2010 (pre ban) vs Oct 2010 (ban on)
    t_pre = (2010 - res.start_year) * STEPS_PER_YEAR + (6 - 1) * 2
    t_ban = (2010 - res.start_year) * STEPS_PER_YEAR + (10 - 1) * 2
    pre = float(np.mean(res.price[t_pre:t_pre + 2]))
    ban = float(np.mean(res.price[t_ban:t_ban + 2]))
    lift = ban / max(pre, 1e-9) - 1.0
    if lift < min_lift:
        raise AssertionError(
            f"AMIS ban-window lift {lift:.3%} < {min_lift:.3%} "
            f"(pre={pre:.1f}, ban={ban:.1f})")


def assert_no_spring_spike(max_ratio: float = 1.25) -> None:
    """Mean Mar–Apr price must not dwarf Sep–Oct (fake lean-season spike)."""
    res = run_wheat_dynamics(use_amis=True, use_shocks=True)
    m = result_to_monthly(res)
    spring = float(m[m.month.isin([3, 4])]["model_price"].mean())
    autumn = float(m[m.month.isin([9, 10])]["model_price"].mean())
    ratio = spring / max(autumn, 1e-9)
    if ratio > max_ratio:
        raise AssertionError(
            f"spring/autumn={ratio:.3f} > {max_ratio} (lean-season artifact)")


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
