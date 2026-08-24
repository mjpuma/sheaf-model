"""Multi-grain sub-annual spine with cross-price substitution (PAUSED).

**Paused (2026-08-24):** do not treat this module as Gate 0 complete.
Prove wheat / maize / rice **separately** via ``sheaf.dynamic_crop`` and
``scripts/score_subannual_crop.py`` first — see
``diagnostics/GATE0_PER_CROP_PLAN.md``. This file remains a prototype for
substitution tests after per-crop Gate 0 soft bars are green.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .calendar24 import STEPS_PER_YEAR, n_steps
from .calibration import GRAINS, OWN_ELAST, P0, RHO
from .data_usda import load_amis_restrictions, load_psd_country, load_price_series_monthly
from .seasonal import (
    harvest_path,
    load_harvest_calendar,
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
_AMIS_CLASS = {
    "wheat": "Wheat",
    "rice": "Rice",
    "maize": "Maize",
}

HARVEST_PULSE_FRAC = 0.12
REBUILD_LAMBDA = 0.20
STU_TARGET = 0.18
SMOOTH = 0.70
INV_ETA = 0.75
UNMET_KAPPA = 4.0


@dataclass
class GrainsSimResult:
    countries: list[str]
    grains: tuple[str, ...]
    start_year: int
    end_year: int
    price: np.ndarray          # (G, T)
    stock: np.ndarray          # (G, n, T)
    harvest: np.ndarray        # (G, n, T)
    consumption: np.ndarray    # (G, n, T)
    exports: np.ndarray        # (G, n, T)
    export_cut: np.ndarray     # (G, n, T)
    subst_scale: float = 0.0
    spin_up_years: int = 0


def cross_price_exponents(subst_scale: float) -> np.ndarray:
    """(G,G) isoelastic exponents: own = OWN_ELAST; cross > 0 for substitutes."""
    G = len(GRAINS)
    eta = np.zeros((G, G))
    for g in range(G):
        eta[g, g] = float(OWN_ELAST[g])
        for h in range(G):
            if g == h:
                continue
            # When h's price rises, demand for substitute g rises.
            eta[g, h] = float(subst_scale) * float(RHO[g, h]) * abs(float(OWN_ELAST[g]))
    return eta


def _psd_annual(crop: str, countries: list[str],
                years: list[int]) -> tuple[pd.DataFrame, pd.DataFrame]:
    psd = load_psd_country(crop)
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


def _ending_stocks(crop: str, countries: list[str], year: int) -> np.ndarray:
    psd = load_psd_country(crop)
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


def amis_export_cuts_grain(countries: list[str], grain: str,
                           start_year: int, end_year: int) -> np.ndarray:
    """(n, T) AMIS quantity cuts for one grain class."""
    n = len(countries)
    T = n_steps(start_year, end_year)
    cuts = np.zeros((n, T))
    cls = _AMIS_CLASS.get(grain)
    if cls is None:
        return cuts
    name_to_i = {c: i for i, c in enumerate(countries)}
    amis = load_amis_restrictions(aggregated=True)
    amis = amis[amis["CommodityClass_Name"].astype(str) == cls]
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


def _anchor_prices(year: int = 2006) -> np.ndarray:
    out = P0.astype(float).copy()
    try:
        m = load_price_series_monthly(deflated=True)
        sub = m[m["year"] == year]
        for gi, g in enumerate(GRAINS):
            s = sub[g].dropna()
            if len(s):
                out[gi] = float(s.mean())
    except (FileNotFoundError, KeyError, ValueError):
        pass
    return out


def _pool_clear(offers: np.ndarray, demand: np.ndarray
                ) -> tuple[np.ndarray, np.ndarray]:
    """Single-pool rationing (used when bilateral E0 is unavailable)."""
    n = offers.shape[0]
    total_need = float(demand.sum())
    total_exp = float(offers.sum())
    shipped = np.zeros(n)
    received = np.zeros(n)
    if total_exp > 1e-12 and total_need > 1e-12:
        fill = min(1.0, total_exp / total_need)
        received = demand * fill
        shipped = offers * (float(received.sum()) / max(total_exp, 1e-12))
    return shipped, received


def _simulate_grains(
        H: np.ndarray,          # (G, n, T)
        C_step: np.ndarray,     # (G, n, T)
        cuts: np.ndarray,       # (G, n, T)
        stock0: np.ndarray,     # (G, n)
        safety: np.ndarray,     # (G, n)
        p0: np.ndarray,         # (G,)
        eta: np.ndarray,        # (G, G) demand exponents
        H_seas: np.ndarray,     # (G, n, T)
        free_twin: np.ndarray | None,  # (G, T) or None
        unmet_twin: np.ndarray | None = None,  # (G, T) or None
        foresight_phi: float = 0.55,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    G, n, T = H.shape
    stock = stock0.copy()
    price = np.zeros((G, T))
    stock_path = np.zeros((G, n, T))
    cons_path = np.zeros((G, n, T))
    exp_path = np.zeros((G, n, T))
    free_path = np.zeros((G, T))
    unmet_path = np.zeros((G, T))
    p = p0.astype(float).copy()
    warehouse = np.maximum(4.0 * safety / max(STU_TARGET, 1e-6), 8.0 * safety)

    # Precompute lean horizons on expected harvest (per grain, world pulse).
    H_exp = foresight_phi * H + (1.0 - foresight_phi) * H_seas
    lean_h = np.zeros((G, T), dtype=int)
    H_ahead = np.zeros_like(H)
    C_ahead = np.zeros_like(C_step)
    for g in range(G):
        lean_h[g] = steps_to_harvest_pulse(
            H_exp[g], frac=HARVEST_PULSE_FRAC, max_horizon=STEPS_PER_YEAR)
        H_ahead[g] = rolling_ahead_variable(H_exp[g], lean_h[g])
        C_ahead[g] = rolling_ahead_variable(C_step[g], lean_h[g])

    for t in range(T):
        # Cross-price food demand (isoelastic around p0)
        rel = np.maximum(p / p0, 1e-6)
        # factor_g = prod_h rel_h ** eta[g,h]
        log_fac = eta @ np.log(rel)
        fac = np.exp(log_fac)  # (G,)

        for g in range(G):
            avail = stock[g] + H[g, :, t]
            desired = np.maximum(C_step[g, :, t] * fac[g], 0.0)
            lean_gap = np.maximum(
                0.0,
                C_ahead[g, :, t] + C_step[g, :, t]
                - H_ahead[g, :, t] - H_exp[g, :, t],
            )
            target = lean_gap + safety[g]
            after_food = np.maximum(0.0, avail - desired)
            food_need = np.maximum(0.0, desired - avail)
            rebuild = REBUILD_LAMBDA * np.maximum(0.0, target - after_food)
            demand = food_need + rebuild
            offers = np.maximum(0.0, avail - desired - target) * (
                1.0 - cuts[g, :, t])
            shipped, received = _pool_clear(offers, demand)
            consumption = np.minimum(
                desired, np.maximum(0.0, avail - shipped + received))
            stock[g] = np.maximum(
                0.0, avail - shipped - consumption + received)
            stock[g] = stock[g] - np.maximum(0.0, stock[g] - warehouse[g])

            lean_need = float(lean_gap.sum())
            free = float(stock[g].sum()) - lean_need
            free_path[g, t] = free
            total_d = float(demand.sum())
            unmet = max(0.0, total_d - float(received.sum()))
            unmet_frac = unmet / max(total_d, 1e-9)
            unmet_path[g, t] = unmet_frac

            if free_twin is None:
                p_star = float(p0[g])
            else:
                twin = float(free_twin[g, t])
                # Shift so both free and twin map to positive slack; when
                # free == twin the ratio is exactly 1 even if both are negative.
                floor0 = 0.05 * float(max(safety[g].sum(), 1.0))
                shift = floor0 + max(0.0, -min(free, twin))
                ratio = (twin + shift) / (free + shift)
                if abs(free - twin) < 1e-6:
                    p_star = float(p0[g])
                else:
                    ratio = float(max(ratio, 1e-12))
                    if ratio >= 1.0:
                        free_term = ratio ** INV_ETA
                    else:
                        free_term = ratio ** (0.2 * INV_ETA)
                    u_ref = (float(unmet_twin[g, t])
                             if unmet_twin is not None else 0.0)
                    u_anom = max(0.0, unmet_frac - u_ref)
                    p_star = (float(p0[g]) * free_term
                              * (1.0 + UNMET_KAPPA * u_anom))

            p[g] = float(SMOOTH * p[g] + (1.0 - SMOOTH) * p_star)
            p[g] = float(np.clip(p[g], 60.0, 1200.0))
            price[g, t] = p[g]
            stock_path[g, :, t] = stock[g]
            cons_path[g, :, t] = consumption
            exp_path[g, :, t] = shipped

    return price, stock_path, cons_path, exp_path, free_path, unmet_path


def run_grains_dynamics(
        countries: list[str] | None = None,
        grains: tuple[str, ...] = GRAINS,
        start_year: int = 2006,
        end_year: int = 2011,
        subst_scale: float = 0.6,
        use_amis: bool = True,
        use_shocks: bool = True,
        stock_seed_year: int = 2005,
        spin_up_years: int = 2,
) -> GrainsSimResult:
    """Run multi-grain spine; ``subst_scale=0`` decouples grains."""
    if countries is None:
        from .calibration import DATA
        countries = [d["name"] for d in DATA] + ["RestOfWorld"]

    grains = tuple(grains)
    G = len(grains)
    n = len(countries)
    years = list(range(start_year, end_year + 1))
    T = len(years) * STEPS_PER_YEAR
    p0 = _anchor_prices(year=min(start_year, 2006))
    # Align p0 to requested grain order
    g_index = {g: i for i, g in enumerate(GRAINS)}
    p0_use = np.array([p0[g_index[g]] for g in grains], float)
    eta_full = cross_price_exponents(subst_scale)
    eta = np.array([[eta_full[g_index[ga], g_index[gb]] for gb in grains]
                    for ga in grains], float)

    H = np.zeros((G, n, T))
    H_seas = np.zeros((G, n, T))
    C_step = np.zeros((G, n, T))
    cuts = np.zeros((G, n, T))
    safety = np.zeros((G, n))
    stock0 = np.zeros((G, n))

    for gi, g in enumerate(grains):
        cal = load_harvest_calendar(g)
        prod, cons = _psd_annual(g, countries, years)
        C_ann = np.zeros(n)
        for i, c in enumerate(countries):
            sub = cons[cons["country"] == c]
            C_ann[i] = float(sub["consumption"].mean()) if len(sub) else 0.0
        safety[gi] = STU_TARGET * C_ann
        mean_prod = (prod.groupby("country", as_index=False)["production"]
                     .mean())
        tiled = pd.concat([mean_prod.assign(year=y) for y in years],
                          ignore_index=True)
        H_seas[gi] = harvest_path(countries, tiled, start_year, end_year,
                                  calendar=cal)
        if use_shocks:
            H[gi] = harvest_path(countries, prod, start_year, end_year,
                                 calendar=cal)
        else:
            H[gi] = H_seas[gi].copy()
        for yi, y in enumerate(years):
            for i, c in enumerate(countries):
                hit = cons[(cons.country == c) & (cons.year == y)]
                ann = float(hit.consumption.iloc[0]) if len(hit) else C_ann[i]
                C_step[gi, i, yi * STEPS_PER_YEAR:(yi + 1) * STEPS_PER_YEAR] = (
                    ann / STEPS_PER_YEAR)
        if use_amis:
            cuts[gi] = amis_export_cuts_grain(
                countries, g, start_year, end_year)
        stock0[gi] = _ending_stocks(g, countries, stock_seed_year)

    # Spin-up on seasonal harvest, no AMIS
    if spin_up_years > 0:
        spin_years = list(range(start_year - spin_up_years, start_year))
        T_spin = len(spin_years) * STEPS_PER_YEAR
        H_spin = np.zeros((G, n, T_spin))
        C_spin = np.zeros((G, n, T_spin))
        for gi, g in enumerate(grains):
            cal = load_harvest_calendar(g)
            prod, cons = _psd_annual(g, countries, years)
            mean_prod = (prod.groupby("country", as_index=False)["production"]
                         .mean())
            tiled = pd.concat([mean_prod.assign(year=y) for y in spin_years],
                              ignore_index=True)
            H_spin[gi] = harvest_path(
                countries, tiled, spin_years[0], spin_years[-1], calendar=cal)
            C_ann = safety[gi] / STU_TARGET
            C_spin[gi] = np.tile((C_ann / STEPS_PER_YEAR)[:, None],
                                 (1, T_spin))
        _, sp, _, _, _, _ = _simulate_grains(
            H_spin, C_spin, np.zeros_like(H_spin), stock0, safety, p0_use,
            eta, H_spin, free_twin=None, unmet_twin=None)
        stock0 = sp[:, :, -1]

    # Twin: seasonal H, no AMIS, same C
    _, _, _, _, free_twin, unmet_twin = _simulate_grains(
        H_seas, C_step, np.zeros_like(H_seas), stock0.copy(), safety, p0_use,
        eta, H_seas, free_twin=None, unmet_twin=None)

    price, stock, cons, exp, _, _ = _simulate_grains(
        H, C_step, cuts, stock0.copy(), safety, p0_use, eta, H_seas,
        free_twin=free_twin, unmet_twin=unmet_twin)

    return GrainsSimResult(
        countries=countries, grains=grains,
        start_year=start_year, end_year=end_year,
        price=price, stock=stock, harvest=H, consumption=cons,
        exports=exp, export_cut=cuts, subst_scale=subst_scale,
        spin_up_years=spin_up_years,
    )


def grains_to_monthly(res: GrainsSimResult) -> pd.DataFrame:
    from .calendar24 import monthly_mean_from_steps
    rows = []
    for gi, g in enumerate(res.grains):
        px = monthly_mean_from_steps(
            res.price[gi], res.start_year, res.end_year)
        for a in px:
            rows.append(dict(year=a["year"], month=a["month"],
                             grain=g, model_price=a["value"],
                             subst_scale=res.subst_scale))
    return pd.DataFrame(rows)
