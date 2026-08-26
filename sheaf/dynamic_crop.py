"""Single-crop Agrimate-style sub-annual market (Gate 0 per crop).

One grain at a time on the 24-step clock: stocks, lean foresight, bilateral
Armington trade, adaptive exporter ask prices, exogenous AMIS quantity cuts.

World price each step is **ask-dominated** (trade-weighted asks), with a
path-matched twin scarcity residual. Demand is split into price-elastic
food/feed and inelastic industrial/ethanol (USA maize FSI excess vs 2000–04).
The twin is mean harvest, mean flex demand, zero industrial excess, no AMIS.
See diagnostics/GATE0_PER_CROP_PLAN.md and GATE0_PARAMETERIZATION.md.

Wheat remains available via ``sheaf.dynamic_wheat`` (thin wrap).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .calendar24 import STEPS_PER_YEAR, n_steps
from .calibration import GRAINS, P0
from .data_faostat import (
    SHEAF_NODE_MAP,
    aggregate_to_nodes,
    bilateral_shares,
    load_trade_matrix,
)
from .data_usda import (
    detrend_anomalies,
    load_amis_restrictions,
    load_psd_country,
    load_psd_use_split,
    load_price_series_monthly,
)
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

MAX_LEAN_STEPS = STEPS_PER_YEAR

# Exporter bite checks: (country, y0, m0, y1, m1)
# Maize: Argentina harvest is Mar–May; tight year-end carry zeroes winter
# offers, so the check must sit on harvest months while a quota/tax is on
# (not Jan–Jun, which is mostly empty + post-quota price-induced extra offers).
_EXPORTER_WINDOWS = {
    "wheat": ("Russia", 2010, 8, 2010, 12),
    "rice": ("Vietnam", 2008, 9, 2008, 11),
    "maize": ("Argentina", 2007, 5, 2007, 5),
}


@dataclass(frozen=True)
class CropParams:
    """Gate 0 single-crop parameters (see diagnostics/GATE0_PARAMETERIZATION.md).

    Classification
    --------------
    structural : fixed by data / Agrimate lineage / accounting identities
    literature : taken from published short-run elasticities / STU norms
    reduced_form : phenomenological but sign-constrained; not freely fit per crisis
    """
    crop: str
    # literature — short-run food/feed demand elasticity
    elast: float
    # literature — safety / capacity as stock-to-use of annual consumption
    stu_target: float = 0.18
    max_stu: float = 0.28
    # structural — extra intra-year pipeline is remaining food until the next
    # harvest pulse (capped). Not a multiple of peak harvest, and not a
    # calendar-Dec dump (that stocked-out Q1 and spiked prices).
    seasonal_buffer_steps: float = 0.0
    pipeline_max_steps: int = 12  # 6 months of use; structural working stocks
    # reduced_form — partial-adjustment rebuild toward lean+safety target
    rebuild_lambda: float = 0.08
    # reduced_form — drain of warehouse overflow. Defaults to rebuild λ.
    # Rice (pipeline=0): overflow is not working inventory; drain faster.
    warehouse_lambda: float = 0.08
    # reduced_form — inverse elasticity of scarcity price vs free-stock ratio
    inv_eta: float = 0.90
    # reduced_form — AR(1) price smoother toward within-step target
    smooth: float = 0.65
    # reduced_form — weight on trade-weighted asks in p* (rest = scarcity)
    trade_w: float = 0.70
    # reduced_form — unmet-anomaly and preferred-source blockage multipliers
    unmet_kappa: float = 2.5
    block_kappa: float = 3.5
    # reduced_form — ask adaptation (Agrimate-like offer prices)
    ask_alpha: float = 0.15
    ask_target_fill: float = 0.70
    ask_comp_elast: float = 1.25
    ask_beta: float = 0.18
    # reduced_form — survivors mark up when preferred sources are blocked
    # (Agrimate oligopolist channel). Sign: >= 0. Zero ⇒ own-fill law only.
    # 0.80 is the smallest shared value at which isolated maize τ does not
    # cut world price (0.40 still cuts; not fit to 2008 peaks).
    ask_rival: float = 0.80
    # structural — harvest foresight blend; pulse definition
    foresight_phi: float = 0.55
    harvest_pulse_frac: float = 0.12
    # structural — residual Armington pool after preferred links
    residual_subst: float = 0.15
    # structural — twin harvest: seasonal mean vs realized
    twin_harvest: str = "seasonal"
    # structural — harvest forcing: signed LOWESS anomalies vs trend
    # (Agrimate). "full" keeps surpluses; "shortfalls_only" clips to ≤ 1.
    shock_mode: str = "full"
    # structural — industrial/ethanol: nodes whose FSI excess vs pre-mandate
    # baseline is treated as price-inelastic (RFS-style). Empty = none.
    industrial_nodes: tuple[str, ...] = ()
    # structural — years that define the pre-mandate FSI baseline
    ind_base_years: tuple[int, int] = (2000, 2004)


def default_crop_params(crop: str) -> CropParams:
    """Crop-specific defaults; shared knobs identical unless noted in the doc."""
    crop = crop.lower().strip()
    shared = dict(
        rebuild_lambda=0.08,
        smooth=0.65,
        ask_alpha=0.15,
        ask_target_fill=0.70,
        ask_comp_elast=1.25,
        ask_beta=0.18,
        harvest_pulse_frac=0.12,
        residual_subst=0.15,
        ask_rival=0.80,
    )
    if crop == "wheat":
        # Supply-shock identifiable (2006/07 balance deficit). Seasonal twin.
        return CropParams(
            crop=crop, elast=-0.15, stu_target=0.20, max_stu=0.28,
            seasonal_buffer_steps=0.0,
            inv_eta=1.00, trade_w=0.70, unmet_kappa=2.5, block_kappa=4.0,
            foresight_phi=0.55, twin_harvest="seasonal", shock_mode="full",
            industrial_nodes=(), **shared)
    if crop == "maize":
        # US maize FSI excess vs 2000–04 is the RFS/ethanol mandate (inelastic).
        # Food+feed remain price-elastic. Full harvest; demand twin is mean C.
        return CropParams(
            crop=crop, elast=-0.25, stu_target=0.16, max_stu=0.18,
            seasonal_buffer_steps=0.0,
            inv_eta=0.85, trade_w=0.80, unmet_kappa=2.5, block_kappa=4.0,
            foresight_phi=0.50, twin_harvest="seasonal", shock_mode="full",
            industrial_nodes=("USA",), **shared)
    if crop == "rice":
        # Restriction-led 2008; no industrial split in PSD. Seasonal twin.
        return CropParams(
            crop=crop, elast=-0.20, stu_target=0.18, max_stu=0.22,
            seasonal_buffer_steps=0.0, pipeline_max_steps=0,
            inv_eta=0.95, trade_w=0.72, unmet_kappa=2.5, block_kappa=4.5,
            foresight_phi=0.55, twin_harvest="seasonal", shock_mode="full",
            industrial_nodes=(), **shared)
    raise ValueError(f"unsupported crop {crop!r}")


@dataclass
class CropSimResult:
    crop: str
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
    free_liquid: np.ndarray | None = None
    free_twin: np.ndarray | None = None
    unmet_frac: np.ndarray | None = None
    offers: np.ndarray | None = None
    purchase_demand: np.ndarray | None = None
    ask: np.ndarray | None = None
    received: np.ndarray | None = None
    trade: np.ndarray | None = None  # (n, n, T) exporter i → importer j
    params: CropParams | None = None
    industrial: np.ndarray | None = None  # (n, T) inelastic use


@dataclass
class CropPrep:
    """Arrays for one Gate 0 crop, ready to simulate (single or coupled)."""
    crop: str
    countries: list[str]
    start_year: int
    end_year: int
    params: CropParams
    p0: float
    H: np.ndarray
    H_seas: np.ndarray
    C_flex: np.ndarray
    C_ind: np.ndarray
    C_flex_twin: np.ndarray
    C_ind_twin: np.ndarray
    cuts: np.ndarray
    stock0: np.ndarray
    safety: np.ndarray
    C_ann: np.ndarray
    A: np.ndarray
    S: np.ndarray
    free_twin: np.ndarray
    unmet_twin: np.ndarray
    spin_up_years: int


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


def _harvest_anomaly_scalars(crop: str, countries: list[str],
                             years: list[int],
                             hist_pad: int = 12,
                             window_years: int = 10) -> np.ndarray:
    """(n, n_years) multipliers = 1 + LOWESS production anomaly.

    Climatology (twin) stays the score-window *mean* seasonal path. Treatment
    harvest is that climatology times these scalars — not raw PSD year totals.
    Raw totals treat post-2008 trend growth as a 2006 'shortfall' against the
    in-sample mean (wheat 2006 is −9% vs 2006–11 mean, −4% vs LOWESS).
    """
    y0 = int(min(years)) - int(hist_pad)
    y1 = int(max(years))
    prod_hist, _ = _psd_annual(crop, countries, list(range(y0, y1 + 1)))
    n, n_y = len(countries), len(years)
    out = np.ones((n, n_y))
    year_index = {y: yi for yi, y in enumerate(years)}
    for i, c in enumerate(countries):
        sub = (prod_hist[prod_hist["country"] == c]
               .set_index("year")["production"]
               .astype(float))
        sub = sub[np.isfinite(sub) & (sub > 1e-9)]
        if len(sub) < 8:
            continue
        anom = detrend_anomalies(sub, window_years=window_years)["anomaly"]
        for y, yi in year_index.items():
            if y in anom.index and np.isfinite(anom.loc[y]):
                out[i, yi] = float(1.0 + anom.loc[y])
    return out


def _apply_harvest_scalars(prod_score: pd.DataFrame, countries: list[str],
                           years: list[int], mean_prod: pd.DataFrame,
                           scalars: np.ndarray,
                           shortfalls_only: bool = False) -> pd.DataFrame:
    """Replace annual production with climatology_mean × (1 + anomaly)."""
    mean_map = {str(r.country): float(r.production)
                for r in mean_prod.itertuples(index=False)}
    rows = []
    for i, c in enumerate(countries):
        m = mean_map.get(c, 0.0)
        for yi, y in enumerate(years):
            s = float(scalars[i, yi])
            if shortfalls_only:
                s = min(s, 1.0)
            rows.append(dict(country=c, year=y, production=m * s))
    return pd.DataFrame(rows)


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


def amis_export_cuts(crop: str, countries: list[str],
                     start_year: int, end_year: int) -> np.ndarray:
    n = len(countries)
    T = n_steps(start_year, end_year)
    cuts = np.zeros((n, T))
    cls = _AMIS_CLASS.get(crop)
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


def _anchor_p0(crop: str, year: int = 2006) -> float:
    default = float(P0[GRAINS.index(crop)]) if crop in GRAINS else 250.0
    try:
        m = load_price_series_monthly(deflated=True)
        sub = m[m["year"] == year][crop].dropna()
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


def _annual_to_steps(ann: np.ndarray, n_years: int, T: int) -> np.ndarray:
    """(n, n_years) annual MMT → (n, T) per-step MMT."""
    n = ann.shape[0]
    out = np.zeros((n, T))
    for yi in range(n_years):
        out[:, yi * STEPS_PER_YEAR:(yi + 1) * STEPS_PER_YEAR] = (
            ann[:, yi:yi + 1] / STEPS_PER_YEAR)
    return out


def _demand_blocks(crop: str, countries: list[str], years: list[int],
                   cons_score: pd.DataFrame, C_ann: np.ndarray,
                   params: CropParams) -> tuple[np.ndarray, np.ndarray]:
    """Return (C_flex, C_ind) annual MMT arrays shaped (n, n_years).

    Industrial (inelastic) = max(0, FSI − mean FSI over ``ind_base_years``)
    on ``params.industrial_nodes`` only (USA maize = ethanol/RFS). All other
    use is flex and faces ``params.elast``. Residuals go to RestOfWorld.
    """
    n = len(countries)
    n_y = len(years)
    C_tot = np.zeros((n, n_y))
    for yi, y in enumerate(years):
        for i, c in enumerate(countries):
            hit = cons_score[(cons_score.country == c) & (cons_score.year == y)]
            C_tot[i, yi] = (float(hit.consumption.iloc[0]) if len(hit)
                            else C_ann[i])
    C_ind = np.zeros((n, n_y))
    nodes = set(params.industrial_nodes)
    if not nodes:
        return C_tot, C_ind
    try:
        use = load_psd_use_split(crop)
    except FileNotFoundError:
        return C_tot, C_ind
    y0, y1 = params.ind_base_years
    for i, c in enumerate(countries):
        if c not in nodes:
            continue
        sub = use[use["country"] == c]
        if sub.empty:
            continue
        base = sub[(sub.year >= y0) & (sub.year <= y1)]["fsi"]
        fsi0 = float(base.mean()) if len(base) else 0.0
        for yi, y in enumerate(years):
            hit = sub[sub.year == y]
            fsi = float(hit.fsi.iloc[0]) if len(hit) else 0.0
            C_ind[i, yi] = max(0.0, fsi - fsi0)
            # Never exceed recorded total use.
            C_ind[i, yi] = min(C_ind[i, yi], C_tot[i, yi])
    C_flex = np.maximum(0.0, C_tot - C_ind)
    return C_flex, C_ind


# Crisis-window FAOSTAT rice E0 files have a zero Vietnam row (data hole).
# Destination mix is taken from 2019–21; scale is ~Vietnam's observed share of
# world rice exports (USDA/FAO order of magnitude), not a 2008 price knob.
_VNM_RICE_EXPORT_SHARE = 0.12
_VNM_RICE_PATTERN_WINDOW = (2019, 2021)


def _repair_vietnam_rice_e0(E: pd.DataFrame, countries: list[str]) -> pd.DataFrame:
    """Fill a missing Vietnam rice export row from a later vintage's mix."""
    if "Vietnam" not in E.index:
        return E
    if float(E.loc["Vietnam"].sum()) > 1e-12:
        return E
    E_ref = aggregate_to_nodes(
        load_trade_matrix("rice", window=_VNM_RICE_PATTERN_WINDOW),
        SHEAF_NODE_MAP)
    E_ref = E_ref.reindex(index=countries, columns=countries, fill_value=0.0)
    row = E_ref.loc["Vietnam"].to_numpy(dtype=float, copy=True)
    i = countries.index("Vietnam")
    row[i] = 0.0
    s = float(row.sum())
    if s <= 1e-15:
        return E
    scale = _VNM_RICE_EXPORT_SHARE * float(E.to_numpy().sum())
    out = E.copy()
    out.loc["Vietnam"] = (row / s) * scale
    return out


def load_trade_shares(crop: str, countries: list[str],
                      window: tuple[int, int] = (2006, 2007),
                      ) -> tuple[np.ndarray, np.ndarray]:
    """Return (A_dest, S_src) share matrices with zero diagonal."""
    E = aggregate_to_nodes(
        load_trade_matrix(crop, window=window), SHEAF_NODE_MAP)
    E = E.reindex(index=countries, columns=countries, fill_value=0.0)
    if crop.lower().strip() == "rice":
        E = _repair_vietnam_rice_e0(E, countries)
    A = bilateral_shares(E, by="destination").to_numpy(dtype=float, copy=True)
    S = bilateral_shares(E, by="source").to_numpy(dtype=float, copy=True)
    np.fill_diagonal(A, 0.0)
    np.fill_diagonal(S, 0.0)
    row = A.sum(axis=1, keepdims=True)
    np.divide(A, row, out=A, where=row > 0)
    col = S.sum(axis=0, keepdims=True)
    np.divide(S, col, out=S, where=col > 0)
    return A, S


def _ask_reweight_dest(A: np.ndarray, ask: np.ndarray, p0: float,
                       gamma: float = 1.25) -> np.ndarray:
    rel = (float(p0) / np.maximum(ask, 1e-6)) ** gamma
    A_eff = A * rel[:, None]
    row = A_eff.sum(axis=1, keepdims=True)
    np.divide(A_eff, row, out=A_eff, where=row > 0)
    return A_eff


def _bilateral_clear(offers: np.ndarray, demand: np.ndarray,
                     A: np.ndarray, S: np.ndarray,
                     subst: float = 0.15,
                     ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
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

    return ship.sum(axis=1), ship.sum(axis=0), ship


def _simulate_window(
        H: np.ndarray,
        C_flex: np.ndarray,
        C_ind: np.ndarray,
        cuts: np.ndarray,
        stock0: np.ndarray,
        safety: np.ndarray,
        p0: float,
        C_ann: np.ndarray,
        A: np.ndarray,
        S: np.ndarray,
        params: CropParams,
        free_twin: np.ndarray | None = None,
        unmet_twin: np.ndarray | None = None,
        H_seasonal: np.ndarray | None = None,
) -> tuple[np.ndarray, ...]:
    n, T = H.shape
    C_step = C_flex + C_ind
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
    recv_path = np.zeros((n, T))
    trade_path = np.zeros((n, n, T))
    p = float(p0)
    ask = np.full(n, float(p0))
    safety_w = float(max(safety.sum(), 1.0))
    carry_cap = params.max_stu * C_ann
    food_step = C_ann / STEPS_PER_YEAR

    if H_seasonal is None:
        H_exp = H
    else:
        H_exp = (params.foresight_phi * H
                 + (1.0 - params.foresight_phi) * H_seasonal)

    lean_h = steps_to_harvest_pulse(
        H_exp, frac=params.harvest_pulse_frac, max_horizon=MAX_LEAN_STEPS)
    H_ahead = rolling_ahead_variable(H_exp, lean_h)
    C_ahead = rolling_ahead_variable(C_step, lean_h)

    elast = params.elast
    inv_eta = params.inv_eta
    smooth = params.smooth
    trade_w = params.trade_w

    for t in range(T):
        avail = stock + H[:, t]
        # Flex use (food+feed) isoelastic; industrial/ethanol inelastic.
        desired_flex = np.maximum(C_flex[:, t] * (p / p0) ** elast, 0.0)
        desired = desired_flex + C_ind[:, t]

        # Lean cover: demand through the horizon less expected harvest
        # (README §8). Current step included via C_step / H_exp.
        lean_gap = np.maximum(
            0.0,
            C_ahead[:, t] + C_step[:, t] - H_ahead[:, t] - H_exp[:, t],
        )
        target = lean_gap + safety

        after_food_stock = np.maximum(0.0, avail - desired)
        food_need = np.maximum(0.0, desired - avail)
        rebuild = params.rebuild_lambda * np.maximum(
            0.0, target - after_food_stock)
        demand = food_need + rebuild
        offers = np.maximum(0.0, avail - desired - target) * (1.0 - cuts[:, t])
        offer_path[:, t] = offers
        demand_path[:, t] = demand
        ask_path[:, t] = ask

        A_eff = _ask_reweight_dest(A, ask, p0, gamma=params.ask_comp_elast)
        shipped, received, ship = _bilateral_clear(
            offers, demand, A_eff, S, subst=params.residual_subst)
        recv_path[:, t] = received
        trade_path[:, :, t] = ship

        consumption = np.minimum(
            desired, np.maximum(0.0, avail - shipped + received))
        stock = np.maximum(0.0, avail - shipped - consumption + received)
        # Carry + constant working stocks (pipeline_max_steps of use).
        # Same-step harvest pads W only when there is a working-stock pipeline
        # (pulse crops). Year-round rice (pipeline=0) must clip toward carry;
        # padding W with H_t every step stored the monsoon as if it were silos.
        warehouse = (
            carry_cap
            + food_step * float(params.pipeline_max_steps)
            + (H[:, t] if params.pipeline_max_steps > 0 else 0.0)
        )
        # Soft clip (same λ as rebuild): one-step destroy of harvest-shoulder
        # excess was incinerating ~10% of wheat/maize harvest and starving
        # lean-season offers. W remains the attractor.
        excess = np.maximum(0.0, stock - warehouse)
        stock = stock - params.warehouse_lambda * excess

        fill = shipped / np.maximum(offers, 1e-9)
        fill = np.where(offers > 1e-9, fill, params.ask_target_fill)
        total_d = float(demand.sum())
        preferred_block = float(
            (S * cuts[:, t][:, None] * demand[None, :]).sum())
        block_frac = preferred_block / max(total_d, 1e-9)
        rival = float(max(params.ask_rival, 0.0)) * block_frac
        ask = ask * np.exp(
            params.ask_alpha * (fill - params.ask_target_fill)
            + np.where(offers > 1e-9, rival, 0.0))
        ask = (1.0 - params.ask_beta) * ask + params.ask_beta * p
        ask = np.clip(ask, 0.45 * p0, 2.8 * p0)

        lean_need = float(lean_gap.sum())
        # Physical free minus surplus locked behind export cuts — withheld
        # grain is not world-market accessible (else a ban looks like abundance).
        locked = float(
            (cuts[:, t] * np.maximum(0.0, stock - target)).sum())
        free = float(stock.sum()) - lean_need - locked
        free_path[t] = free

        unmet = max(0.0, total_d - float(received.sum()))
        unmet_frac = unmet / max(total_d, 1e-9)
        unmet_path[t] = unmet_frac

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
            floor0 = 0.05 * safety_w
            shift = floor0 + max(0.0, -min(free, twin))
            ratio = (twin + shift) / (free + shift)
            u0 = float(unmet_twin[t]) if unmet_twin is not None else 0.0
            u_anom = max(0.0, unmet_frac - u0)
            calm = (abs(free - twin) < 1e-6 and u_anom < 1e-9
                    and block_frac < 1e-9)
            if calm:
                p_star = p0
            else:
                ratio = float(max(ratio, 1e-12))
                # Symmetric inverse-elasticity: surplus must lower p so flex
                # demand can eat it. Muting abundance was storing gluts.
                free_term = ratio ** inv_eta
                p_scar = (p0 * free_term
                          * (1.0 + params.unmet_kappa * u_anom
                             + params.block_kappa * block_frac))
                p_star = trade_w * p_trade + (1.0 - trade_w) * p_scar

        p = float(smooth * p + (1.0 - smooth) * p_star)
        p = float(np.clip(p, 60.0, 1200.0))

        price[t] = p
        stock_path[:, t] = stock
        cons_path[:, t] = consumption
        exp_path[:, t] = shipped

    return (price, stock_path, cons_path, exp_path,
            free_path, unmet_path, offer_path, demand_path, ask_path,
            recv_path, trade_path)


def prepare_crop_run(
        crop: str = "wheat",
        countries: list[str] | None = None,
        start_year: int = 2006,
        end_year: int = 2011,
        p0: float | None = None,
        params: CropParams | None = None,
        use_amis: bool = True,
        use_shocks: bool = True,
        use_demand: bool = True,
        use_industrial: bool | None = None,
        stock_seed_year: int = 2005,
        spin_up_years: int = 2,
        trade_window: tuple[int, int] = (2006, 2007),
        **overrides,
) -> CropPrep:
    """Build Gate 0 arrays (harvest, demand, AMIS, twin) without simulating
    the treatment path. ``run_crop_dynamics`` and Gate 1 coupling share this.
    """
    crop = crop.lower().strip()
    if crop not in _AMIS_CLASS:
        raise ValueError(f"unsupported crop {crop!r}; expected one of "
                         f"{tuple(_AMIS_CLASS)}")

    if params is None:
        params = default_crop_params(crop)
    if overrides:
        from dataclasses import fields, replace
        allowed = {f.name for f in fields(CropParams)} - {"crop"}
        patch = {k: v for k, v in overrides.items() if k in allowed}
        if patch:
            params = replace(params, **patch)

    if countries is None:
        from .calibration import DATA
        countries = [d["name"] for d in DATA] + ["RestOfWorld"]

    if p0 is None:
        p0 = _anchor_p0(crop, year=min(start_year, 2006))
    if use_industrial is None:
        use_industrial = bool(params.industrial_nodes)

    years = list(range(start_year, end_year + 1))
    n = len(countries)
    n_y = len(years)
    cal = load_harvest_calendar(crop)
    A, S = load_trade_shares(crop, countries, window=trade_window)

    prod_score, cons_score = _psd_annual(crop, countries, years)
    C_ann = np.zeros(n)
    for i, c in enumerate(countries):
        sub = cons_score[cons_score["country"] == c]
        C_ann[i] = float(sub["consumption"].mean()) if len(sub) else 0.0
    safety = params.stu_target * C_ann

    C_flex_y, C_ind_y = _demand_blocks(
        crop, countries, years, cons_score, C_ann, params)
    C_flex_mean = C_flex_y.mean(axis=1)
    C_flex_twin_y = np.repeat(C_flex_mean[:, None], n_y, axis=1)
    C_ind_twin_y = np.zeros_like(C_ind_y)

    mean_prod = (prod_score.groupby("country", as_index=False)["production"]
                 .mean())
    tiled_mean = pd.concat([mean_prod.assign(year=y) for y in years],
                           ignore_index=True)

    spin_stock = _ending_stocks(crop, countries, stock_seed_year)
    spin_stock = np.minimum(
        spin_stock,
        np.maximum(params.max_stu * C_ann, 1.5 * safety))

    T = n_y * STEPS_PER_YEAR
    C_flex_twin = _annual_to_steps(C_flex_twin_y, n_y, T)
    C_ind_twin = _annual_to_steps(C_ind_twin_y, n_y, T)
    C_flex = (_annual_to_steps(C_flex_y, n_y, T) if use_demand
              else C_flex_twin)
    C_ind = (_annual_to_steps(C_ind_y, n_y, T) if use_industrial
             else C_ind_twin)

    if spin_up_years > 0:
        spin_years = list(range(start_year - spin_up_years, start_year))
        tiled_spin = pd.concat([mean_prod.assign(year=y) for y in spin_years],
                               ignore_index=True)
        H_spin = harvest_path(countries, tiled_spin, spin_years[0],
                              spin_years[-1], calendar=cal)
        C_flex_spin = np.tile((C_flex_mean / STEPS_PER_YEAR)[:, None],
                              (1, H_spin.shape[1]))
        C_ind_spin = np.zeros_like(C_flex_spin)
        _, stock_path_s, _, _, _, _, _, _, _, _, _ = _simulate_window(
            H_spin, C_flex_spin, C_ind_spin, np.zeros_like(H_spin),
            spin_stock, safety, p0, C_ann, A, S, params, free_twin=None)
        spin_stock = stock_path_s[:, -1]

    H_seas = harvest_path(countries, tiled_mean, start_year, end_year,
                          calendar=cal)
    if use_shocks:
        scalars = _harvest_anomaly_scalars(crop, countries, years)
        prod_forced = _apply_harvest_scalars(
            prod_score, countries, years, mean_prod, scalars,
            shortfalls_only=(params.shock_mode == "shortfalls_only"))
        H = harvest_path(countries, prod_forced, start_year, end_year,
                         calendar=cal)
    else:
        H = H_seas.copy()

    if params.twin_harvest == "realized":
        H_for_twin = H
    else:
        H_for_twin = H_seas

    _, _, _, _, free_twin, unmet_twin, _, _, _, _, _ = _simulate_window(
        H_for_twin, C_flex_twin, C_ind_twin, np.zeros_like(H_for_twin),
        spin_stock.copy(), safety, p0, C_ann, A, S, params,
        free_twin=None, H_seasonal=H_seas)

    cuts = (amis_export_cuts(crop, countries, start_year, end_year)
            if use_amis else np.zeros((n, T)))

    return CropPrep(
        crop=crop, countries=countries, start_year=start_year,
        end_year=end_year, params=params, p0=float(p0),
        H=H, H_seas=H_seas, C_flex=C_flex, C_ind=C_ind,
        C_flex_twin=C_flex_twin, C_ind_twin=C_ind_twin, cuts=cuts,
        stock0=spin_stock, safety=safety, C_ann=C_ann, A=A, S=S,
        free_twin=free_twin, unmet_twin=unmet_twin,
        spin_up_years=spin_up_years,
    )


def run_crop_dynamics(
        crop: str = "wheat",
        countries: list[str] | None = None,
        start_year: int = 2006,
        end_year: int = 2011,
        p0: float | None = None,
        params: CropParams | None = None,
        use_amis: bool = True,
        use_shocks: bool = True,
        use_demand: bool = True,
        use_industrial: bool | None = None,
        stock_seed_year: int = 2005,
        spin_up_years: int = 2,
        trade_window: tuple[int, int] = (2006, 2007),
        **overrides,
) -> CropSimResult:
    """Run single-crop Gate 0 spine (ask-dominated bilateral market).

    ``use_shocks``: climatological seasonal harvest times LOWESS production
    anomalies (else seasonal mean). Raw PSD year totals are not used as
    levels — they mix shocks with trend and contaminate the in-sample mean.
    ``use_demand``: year-by-year flex food/feed (else mean flex).
    ``use_industrial``: inelastic industrial/ethanol residual (USA maize RFS).
    Default ``None`` → on iff ``params.industrial_nodes`` is nonempty.
    Official P1 matched split is mean flex + industrial on + harvest ± AMIS.
    Twin identity requires ``use_industrial=False`` (no-mandate climatology).
    ``use_amis``: exogenous AMIS quantity cuts.

    Pass ``params=`` or field overrides. See
    ``diagnostics/GATE0_PARAMETERIZATION.md``.
    """
    prep = prepare_crop_run(
        crop, countries=countries, start_year=start_year, end_year=end_year,
        p0=p0, params=params, use_amis=use_amis, use_shocks=use_shocks,
        use_demand=use_demand, use_industrial=use_industrial,
        stock_seed_year=stock_seed_year, spin_up_years=spin_up_years,
        trade_window=trade_window, **overrides)
    return simulate_prep(prep)


def simulate_prep(prep: CropPrep, cuts: np.ndarray | None = None,
                  harvest: np.ndarray | None = None) -> CropSimResult:
    """Run the Gate 0 market on an already-built ``CropPrep``.

    ``cuts`` / ``harvest`` override the prep arrays without rebuilding
    AMIS, trade shares, or the calm twin. Used by the Gate 2 policy beta.
    """
    H = prep.H if harvest is None else harvest
    cuts_use = prep.cuts if cuts is None else cuts
    (price, stock_path, cons_path, exp_path,
     free_liq, unmet, offers, demand, ask, received, trade) = _simulate_window(
        H, prep.C_flex, prep.C_ind, cuts_use, prep.stock0.copy(),
        prep.safety, prep.p0, prep.C_ann, prep.A, prep.S, prep.params,
        free_twin=prep.free_twin, unmet_twin=prep.unmet_twin,
        H_seasonal=prep.H_seas)
    return CropSimResult(
        crop=prep.crop, countries=prep.countries, start_year=prep.start_year,
        end_year=prep.end_year, price=price, stock=stock_path, harvest=H,
        consumption=cons_path, exports=exp_path, export_cut=cuts_use,
        spin_up_years=prep.spin_up_years, free_liquid=free_liq,
        free_twin=prep.free_twin, unmet_frac=unmet, offers=offers,
        purchase_demand=demand, ask=ask, received=received, trade=trade,
        params=prep.params, industrial=prep.C_ind,
    )


def result_to_monthly(res: CropSimResult) -> pd.DataFrame:
    from .calendar24 import monthly_mean_from_steps
    px = monthly_mean_from_steps(res.price, res.start_year, res.end_year)
    stu = monthly_mean_from_steps(res.stock.sum(axis=0),
                                  res.start_year, res.end_year)
    return pd.DataFrame([
        dict(year=a["year"], month=a["month"],
             model_price=a["value"], world_stock=b["value"])
        for a, b in zip(px, stu)
    ])


def assert_twin_identity(crop: str = "wheat", tol_price: float = 0.02,
                         tol_free: float = 1.0) -> None:
    """No harvest / demand / AMIS shocks ⇒ free ≡ twin and price flat at p0."""
    res = run_crop_dynamics(crop, use_amis=False, use_shocks=False,
                            use_demand=False, use_industrial=False)
    p0 = float(res.price[0])
    tail = res.price[STEPS_PER_YEAR:]
    rel = float(np.max(np.abs(tail - p0)) / max(p0, 1.0))
    if rel > tol_price:
        raise AssertionError(
            f"{crop}: neither-path price drift {rel:.3%} > {tol_price:.3%} "
            f"(p0={p0:.1f}, range=[{tail.min():.1f},{tail.max():.1f}])")
    if res.free_liquid is None or res.free_twin is None:
        raise AssertionError(f"{crop}: free paths not recorded")
    free_err = float(np.max(np.abs(res.free_liquid - res.free_twin)))
    if free_err > tol_free:
        raise AssertionError(
            f"{crop}: neither-path free≠twin max|Δ|={free_err:.3f} > {tol_free}")


def assert_amis_raises_price(crop: str = "wheat",
                             min_lift: float | None = None) -> None:
    """Tau-only vs no-AMIS in the crop's primary ban window.

    Maize floor is 0 (must not *cut* world price). Offer-cut assert remains
    the quantity check.
    """
    if crop == "wheat":
        y0, m0, y1, m1 = 2010, 8, 2010, 12
        floor = 0.05
    elif crop == "rice":
        y0, m0, y1, m1 = 2008, 1, 2008, 6
        floor = 0.05
    elif crop == "maize":
        y0, m0, y1, m1 = 2007, 5, 2008, 6
        floor = 0.0
    else:
        return
    if min_lift is None:
        min_lift = floor
    tau = run_crop_dynamics(crop, use_amis=True, use_shocks=False,
                            use_demand=False, use_industrial=False)
    base = run_crop_dynamics(crop, use_amis=False, use_shocks=False,
                             use_demand=False, use_industrial=False)
    t0 = (y0 - tau.start_year) * STEPS_PER_YEAR + (m0 - 1) * 2
    t1 = (y1 - tau.start_year) * STEPS_PER_YEAR + (m1 - 1) * 2 + 2
    p_tau = float(np.mean(tau.price[t0:t1]))
    p_base = float(np.mean(base.price[t0:t1]))
    lift = p_tau / max(p_base, 1e-9) - 1.0
    if lift < min_lift:
        raise AssertionError(
            f"{crop}: AMIS vs no-AMIS lift {lift:.3%} < {min_lift:.3%} "
            f"(tau={p_tau:.1f}, base={p_base:.1f})")


def assert_no_spring_spike(crop: str = "wheat",
                           max_ratio: float = 1.25) -> None:
    """Lean-cover accounting must not create a fake spring spike on climatology.

    Full-path maize can still have a real NH lean (harvest in autumn); that is
    not this assert.
    """
    res = run_crop_dynamics(
        crop, use_amis=False, use_shocks=False, use_demand=False,
        use_industrial=False)
    m = result_to_monthly(res)
    spring = float(m[m.month.isin([3, 4])]["model_price"].mean())
    autumn = float(m[m.month.isin([9, 10])]["model_price"].mean())
    ratio = spring / max(autumn, 1e-9)
    if ratio > max_ratio:
        raise AssertionError(
            f"{crop}: spring/autumn={ratio:.3f} > {max_ratio}")


def assert_amis_cuts_exports(crop: str = "wheat",
                             max_offer_ratio: float | None = None,
                             max_ship_ratio: float | None = None) -> None:
    # Wheat Russia ban ≈0.95 → very low offers; maize/rice quotas/taxes milder.
    if max_offer_ratio is None:
        max_offer_ratio = 0.20 if crop == "wheat" else 0.70
    if max_ship_ratio is None:
        max_ship_ratio = 0.85 if crop == "wheat" else 0.95
    country, y0, m0, y1, m1 = _EXPORTER_WINDOWS[crop]
    tau = run_crop_dynamics(crop, use_amis=True, use_shocks=False,
                            use_demand=False, use_industrial=False)
    base = run_crop_dynamics(crop, use_amis=False, use_shocks=False,
                             use_demand=False, use_industrial=False)
    if country not in tau.countries:
        raise AssertionError(f"{crop}: {country} not in node set")
    i = tau.countries.index(country)
    t0 = (y0 - tau.start_year) * STEPS_PER_YEAR + (m0 - 1) * 2
    t1 = (y1 - tau.start_year) * STEPS_PER_YEAR + (m1 - 1) * 2 + 2
    if tau.offers is None or base.offers is None:
        raise AssertionError(f"{crop}: offers not recorded")
    off_tau = float(np.mean(tau.offers[i, t0:t1]))
    off_base = float(np.mean(base.offers[i, t0:t1]))
    # If baseline offers are tiny, skip (node not an exporter for this crop).
    if off_base < 1e-6:
        raise AssertionError(
            f"{crop}: {country} baseline offers≈0 in check window "
            f"— pick a different exporter window")
    off_ratio = off_tau / off_base
    if off_ratio > max_offer_ratio:
        raise AssertionError(
            f"{crop}: {country} offer ratio={off_ratio:.3f} > {max_offer_ratio}")
    exp_tau = float(np.mean(tau.exports[i, t0:t1]))
    exp_base = float(np.mean(base.exports[i, t0:t1]))
    # Shipments are softer than offers (rerouting / residual pool). Wheat ban
    # should still cut Russia shipments; maize/rice quotas need not.
    if crop == "wheat":
        exp_ratio = exp_tau / max(exp_base, 1e-9)
        if exp_ratio > max_ship_ratio:
            raise AssertionError(
                f"{crop}: {country} export ratio={exp_ratio:.3f} > {max_ship_ratio}")
