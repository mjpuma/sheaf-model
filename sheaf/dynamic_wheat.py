"""Agrimate-aligned wheat dynamics (Gate 0).

24 steps/year. Bilateral offers, lean foresight, adaptive ask prices.

See README §8 for the full equation set and symbol table. Implementation
summary:

  avail_i = S_i + H_i
  desired_i = C_i (p / p0)^ε
  lean from expected harvest ahead (blend of seasonal + realized)
  target_i = lean_i + safety_i
  D_i = food shortfall + λ·stock-gap     (purchase demand)
  O_i = max(0, avail − desired − target)·(1 − τ_i)   (AMIS-cut offers)

  Armington clear with ask-reweighted destination shares.
  Exporter ask q_i adapts to fill rates (Agrimate-like offer prices).
  World p blends trade-weighted asks with twin free-stock / blockage signal.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .calendar24 import STEPS_PER_YEAR, n_steps
from .data_faostat import (
    SHEAF_NODE_MAP,
    aggregate_to_nodes,
    bilateral_shares,
    load_trade_matrix,
)
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
UNMET_KAPPA = 5.0
BLOCK_KAPPA = 4.5
REBUILD_LAMBDA = 0.20
# Adaptive ask prices (Agrimate-like suppliers)
ASK_ALPHA = 0.15          # speed of ask adjustment to fill gaps
ASK_TARGET_FILL = 0.70    # target offer fill rate
ASK_COMP_ELAST = 1.25     # destination reweight ∝ (q̄/q_i)^γ
TRADE_PRICE_WEIGHT = 0.35 # blend of trade-weighted asks into p*
# Harvest foresight: weight on realized path vs seasonal expectation
FORESIGHT_PHI = 0.55


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
    free_liquid: np.ndarray | None = None  # physical free (name kept for score API)
    free_twin: np.ndarray | None = None
    unmet_frac: np.ndarray | None = None
    offers: np.ndarray | None = None
    purchase_demand: np.ndarray | None = None
    ask: np.ndarray | None = None  # exporter ask prices q_{i,t}


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
    n = len(countries)
    out = np.zeros((n, T))
    for yi, y in enumerate(years):
        for i, c in enumerate(countries):
            hit = cons_score[(cons_score.country == c) & (cons_score.year == y)]
            ann = float(hit.consumption.iloc[0]) if len(hit) else C_ann[i]
            out[i, yi * STEPS_PER_YEAR:(yi + 1) * STEPS_PER_YEAR] = (
                ann / STEPS_PER_YEAR)
    return out


def load_trade_shares(countries: list[str],
                      window: tuple[int, int] = (2006, 2007),
                      ) -> tuple[np.ndarray, np.ndarray]:
    """Return (A_dest, S_src) share matrices with zero diagonal.

    A[i,j] = share of exporter i's offers destined to j (rows sum to 1).
    S[i,j] = share of importer j's purchases sourced from i (cols sum to 1).
    """
    E = aggregate_to_nodes(
        load_trade_matrix("wheat", window=window), SHEAF_NODE_MAP)
    E = E.reindex(index=countries, columns=countries, fill_value=0.0)
    A = bilateral_shares(E, by="destination").to_numpy(dtype=float)
    S = bilateral_shares(E, by="source").to_numpy(dtype=float)
    np.fill_diagonal(A, 0.0)
    np.fill_diagonal(S, 0.0)
    row = A.sum(axis=1, keepdims=True)
    np.divide(A, row, out=A, where=row > 0)
    col = S.sum(axis=0, keepdims=True)
    np.divide(S, col, out=S, where=col > 0)
    return A, S


def _ask_reweight_dest(A: np.ndarray, ask: np.ndarray, p0: float,
                       gamma: float = ASK_COMP_ELAST) -> np.ndarray:
    """Reweight destination shares toward cheaper ask prices; renorm rows."""
    rel = (float(p0) / np.maximum(ask, 1e-6)) ** gamma
    A_eff = A * rel[:, None]
    row = A_eff.sum(axis=1, keepdims=True)
    np.divide(A_eff, row, out=A_eff, where=row > 0)
    return A_eff


def _bilateral_clear(offers: np.ndarray, demand: np.ndarray,
                     A: np.ndarray, S: np.ndarray,
                     subst: float = 0.15,
                     ) -> tuple[np.ndarray, np.ndarray]:
    """Armington-style clear: preferred sources first, limited substitution."""
    O = offers[:, None] * A
    D = S * demand[None, :]
    ship = np.minimum(O, D)

    offer_left = np.maximum(0.0, offers - ship.sum(axis=1))
    demand_left = np.maximum(0.0, demand - ship.sum(axis=0))
    take = subst * demand_left
    tot_o = float(offer_left.sum())
    tot_t = float(take.sum())
    if tot_o > 1e-15 and tot_t > 1e-15:
        fill = min(1.0, tot_o / tot_t)
        recv2 = take * fill
        w = recv2 / max(float(recv2.sum()), 1e-15)
        ship2 = offer_left[:, None] * w[None, :]
        col = ship2.sum(axis=0)
        scale = np.ones_like(recv2)
        mask = col > recv2 + 1e-15
        scale[mask] = recv2[mask] / col[mask]
        ship2 *= scale[None, :]
        ship = ship + ship2

    return ship.sum(axis=1), ship.sum(axis=0)


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
        A: np.ndarray,
        S: np.ndarray,
        free_twin: np.ndarray | None = None,
        unmet_twin: np.ndarray | None = None,
        H_seasonal: np.ndarray | None = None,
        pulse_frac: float | None = None,
        unmet_kappa: float = UNMET_KAPPA,
        block_kappa: float = BLOCK_KAPPA,
        rebuild_lambda: float = REBUILD_LAMBDA,
        foresight_phi: float = FORESIGHT_PHI,
        ask_alpha: float = ASK_ALPHA,
        trade_w: float = TRADE_PRICE_WEIGHT,
) -> tuple[np.ndarray, ...]:
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
    offer_path = np.zeros((n, T))
    demand_path = np.zeros((n, T))
    ask_path = np.zeros((n, T))
    p = float(p0)
    ask = np.full(n, float(p0))
    safety_w = float(max(safety.sum(), 1.0))
    warehouse = np.maximum(4.0 * C_ann, 8.0 * safety)

    # Expected harvest path for lean foresight (adaptive / seasonal blend).
    if H_seasonal is None:
        H_exp = H
    else:
        H_exp = foresight_phi * H + (1.0 - foresight_phi) * H_seasonal

    lean_h = steps_to_harvest_pulse(H_exp, frac=pulse_frac,
                                    max_horizon=MAX_LEAN_STEPS)
    H_ahead = rolling_ahead_variable(H_exp, lean_h)
    C_ahead = rolling_ahead_variable(C_step, lean_h)

    for t in range(T):
        avail = stock + H[:, t]
        desired = np.maximum(C_step[:, t] * (p / p0) ** elast, 0.0)

        lean_gap = np.maximum(
            0.0,
            C_ahead[:, t] + C_step[:, t] - H_ahead[:, t] - H_exp[:, t],
        )
        target = lean_gap + safety

        after_food_stock = np.maximum(0.0, avail - desired)
        food_need = np.maximum(0.0, desired - avail)
        rebuild = rebuild_lambda * np.maximum(0.0, target - after_food_stock)
        demand = food_need + rebuild
        offers = np.maximum(0.0, avail - desired - target) * (1.0 - cuts[:, t])
        offer_path[:, t] = offers
        demand_path[:, t] = demand
        ask_path[:, t] = ask

        A_eff = _ask_reweight_dest(A, ask, p0)
        shipped, received = _bilateral_clear(offers, demand, A_eff, S)

        consumption = np.minimum(
            desired, np.maximum(0.0, avail - shipped + received))
        stock = np.maximum(0.0, avail - shipped - consumption + received)
        stock = stock - np.maximum(0.0, stock - warehouse)

        # Adaptive ask: raise if sold out (fill high), cut if left on shelf.
        fill = shipped / np.maximum(offers, 1e-9)
        fill = np.where(offers > 1e-9, fill, ASK_TARGET_FILL)
        ask = ask * np.exp(ask_alpha * (fill - ASK_TARGET_FILL))
        # Soft mean-reversion toward the current world price (anchors level).
        ask = 0.82 * ask + 0.18 * p
        ask = np.clip(ask, 0.45 * p0, 2.8 * p0)

        lean_need = float(lean_gap.sum())
        free = float(stock.sum()) - lean_need
        free_path[t] = free

        total_d = float(demand.sum())
        unmet = max(0.0, total_d - float(received.sum()))
        unmet_frac = unmet / max(total_d, 1e-9)
        unmet_path[t] = unmet_frac

        preferred_block = float((S * cuts[:, t][:, None] * demand[None, :]).sum())
        block_frac = preferred_block / max(total_d, 1e-9)

        shipped_sum = float(shipped.sum())
        if shipped_sum > 1e-12:
            p_trade = float(np.dot(ask, shipped) / shipped_sum)
        else:
            p_trade = p

        if free_twin is None:
            # Twin / spin-up: hold p0 so free/unmet baselines are physical-only.
            p_star = p0
        else:
            twin = float(free_twin[t])
            floor = 0.05 * safety_w
            ratio = (twin + floor) / max(free + floor, floor)
            if ratio >= 1.0:
                free_term = ratio ** inv_eta
            else:
                free_term = ratio ** (0.20 * inv_eta)
            u0 = float(unmet_twin[t]) if unmet_twin is not None else 0.0
            u_anom = max(0.0, unmet_frac - u0)
            p_scar = (p0 * free_term
                      * (1.0 + unmet_kappa * u_anom + block_kappa * block_frac))
            # Calm match to twin: no trade-price drift (preserves twin identity).
            calm = (abs(ratio - 1.0) < 1e-6 and u_anom < 1e-9
                    and block_frac < 1e-9)
            if calm:
                p_star = p0
            else:
                p_star = trade_w * p_trade + (1.0 - trade_w) * p_scar
        p = float(smooth * p + (1.0 - smooth) * p_star)
        p = float(np.clip(p, 80.0, 900.0))

        price[t] = p
        stock_path[:, t] = stock
        cons_path[:, t] = consumption
        exp_path[:, t] = shipped

    return (price, stock_path, cons_path, exp_path,
            free_path, unmet_path, offer_path, demand_path, ask_path)


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
        trade_window: tuple[int, int] = (2006, 2007),
) -> WheatSimResult:
    """Run Gate 0 wheat spine: bilateral offers + path-matched twin pricing."""
    if countries is None:
        from .calibration import DATA
        countries = [d["name"] for d in DATA] + ["RestOfWorld"]

    if p0 is None:
        p0 = _anchor_p0(year=min(start_year, 2006))

    years = list(range(start_year, end_year + 1))
    n = len(countries)
    cal = load_wheat_harvest_calendar()
    A, S = load_trade_shares(countries, window=trade_window)

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

    spin_stock = _ending_stocks(countries, stock_seed_year)
    if spin_up_years > 0:
        spin_years = list(range(start_year - spin_up_years, start_year))
        tiled_spin = pd.concat([mean_prod.assign(year=y) for y in spin_years],
                               ignore_index=True)
        H_spin = harvest_path(countries, tiled_spin, spin_years[0],
                              spin_years[-1], calendar=cal)
        C_spin = np.tile((C_ann / STEPS_PER_YEAR)[:, None],
                         (1, H_spin.shape[1]))
        _, stock_path_s, _, _, _, _, _, _, _ = _simulate_window(
            H_spin, C_spin, np.zeros_like(H_spin), spin_stock, safety,
            p0, elast, inv_eta, smooth, C_ann, A, S, free_twin=None)
        spin_stock = stock_path_s[:, -1]

    T = len(years) * STEPS_PER_YEAR
    C_step = _consumption_path(countries, cons_score, C_ann, years, T)

    H_twin = harvest_path(countries, tiled_mean, start_year, end_year,
                          calendar=cal)
    _, _, _, _, free_twin, unmet_twin, _, _, _ = _simulate_window(
        H_twin, C_step, np.zeros_like(H_twin), spin_stock.copy(), safety,
        p0, elast, inv_eta, smooth, C_ann, A, S, free_twin=None,
        H_seasonal=H_twin)

    if use_shocks:
        H = harvest_path(countries, prod_score, start_year, end_year,
                         calendar=cal)
    else:
        H = H_twin.copy()
    cuts = (amis_export_cuts(countries, start_year, end_year)
            if use_amis else np.zeros((n, T)))

    (price, stock_path, cons_path, exp_path,
     free_liq, unmet, offers, demand, ask) = _simulate_window(
        H, C_step, cuts, spin_stock.copy(), safety,
        p0, elast, inv_eta, smooth, C_ann, A, S,
        free_twin=free_twin, unmet_twin=unmet_twin, H_seasonal=H_twin)

    return WheatSimResult(
        countries=countries, start_year=start_year, end_year=end_year,
        price=price, stock=stock_path, harvest=H, consumption=cons_path,
        exports=exp_path, export_cut=cuts, spin_up_years=spin_up_years,
        free_liquid=free_liq, free_twin=free_twin, unmet_frac=unmet,
        offers=offers, purchase_demand=demand, ask=ask,
    )


def assert_twin_identity(tol_price: float = 0.02,
                         tol_free: float = 1.0) -> None:
    """No shocks + no AMIS ⇒ flat at p0; free ≡ twin."""
    res = run_wheat_dynamics(use_amis=False, use_shocks=False)
    p0 = float(res.price[0])
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
    """Tau-only ban-window prices must exceed no-AMIS prices by min_lift."""
    tau = run_wheat_dynamics(use_amis=True, use_shocks=False)
    base = run_wheat_dynamics(use_amis=False, use_shocks=False)
    t0 = (2010 - tau.start_year) * STEPS_PER_YEAR + (8 - 1) * 2
    t1 = (2010 - tau.start_year) * STEPS_PER_YEAR + (12 - 1) * 2 + 2
    p_tau = float(np.mean(tau.price[t0:t1]))
    p_base = float(np.mean(base.price[t0:t1]))
    lift = p_tau / max(p_base, 1e-9) - 1.0
    if lift < min_lift:
        raise AssertionError(
            f"AMIS vs no-AMIS ban-window lift {lift:.3%} < {min_lift:.3%} "
            f"(tau={p_tau:.1f}, base={p_base:.1f})")


def assert_no_spring_spike(max_ratio: float = 1.25) -> None:
    """Mean Mar–Apr price must not dwarf Sep–Oct."""
    res = run_wheat_dynamics(use_amis=True, use_shocks=True)
    m = result_to_monthly(res)
    spring = float(m[m.month.isin([3, 4])]["model_price"].mean())
    autumn = float(m[m.month.isin([9, 10])]["model_price"].mean())
    ratio = spring / max(autumn, 1e-9)
    if ratio > max_ratio:
        raise AssertionError(
            f"spring/autumn={ratio:.3f} > {max_ratio} (lean-season artifact)")


def assert_amis_cuts_exports(max_offer_ratio: float = 0.20,
                             max_ship_ratio: float = 0.85) -> None:
    """Russia offers (and shipments) fall in the 2010 ban window vs no-AMIS."""
    tau = run_wheat_dynamics(use_amis=True, use_shocks=False)
    base = run_wheat_dynamics(use_amis=False, use_shocks=False)
    i = tau.countries.index("Russia")
    t0 = (2010 - tau.start_year) * STEPS_PER_YEAR + (8 - 1) * 2
    t1 = (2010 - tau.start_year) * STEPS_PER_YEAR + (12 - 1) * 2 + 2
    if tau.offers is None or base.offers is None:
        raise AssertionError("offers not recorded")
    off_tau = float(np.mean(tau.offers[i, t0:t1]))
    off_base = float(np.mean(base.offers[i, t0:t1]))
    off_ratio = off_tau / max(off_base, 1e-9)
    if off_ratio > max_offer_ratio:
        raise AssertionError(
            f"Russia ban-window offer ratio={off_ratio:.3f} > {max_offer_ratio}")
    exp_tau = float(np.mean(tau.exports[i, t0:t1]))
    exp_base = float(np.mean(base.exports[i, t0:t1]))
    exp_ratio = exp_tau / max(exp_base, 1e-9)
    if exp_ratio > max_ship_ratio:
        raise AssertionError(
            f"Russia ban-window export ratio={exp_ratio:.3f} > {max_ship_ratio}")


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
