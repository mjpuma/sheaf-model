#!/usr/bin/env python3
"""Red-team slot R4 (market power / trade network) shared library.

Read-only with respect to ``sheaf/`` and ``scripts/``. Carries a *replica* of
``sheaf.dynamic_crop._simulate_window`` verified to machine precision against
the shipped implementation (``verify_replica``), plus switchable variants used
to prototype an Agrimate-style oligopolistic channel:

``mp_alpha``    : >0 activates a share-dependent (Cournot / Agrimate Eq. D.9)
                  markup on exporter offer prices. 0 = shipped behaviour.
``mp_form``     : "exp"    log mu_i = alpha * (s_i - s_ref_i)   (linearised
                           Lerner, safe for all shares)
                  "lerner" mu_i = (1 - alpha*s_ref_i)/(1 - alpha*s_i), capped
``alloc_mode``  : "shipped"  A-row reweight exactly as shipped (a no-op, see
                             ``reweight_is_noop``)
                  "source"   CES-over-sources reweight of S by offer price
                             (Agrimate Eq. 8c with sigma = ask_comp_elast)
                  "agrimate" source CES allocation + proportional supplier
                             rationing (no exporter destination-mix cap)
``ask_rival``   : override via ``params`` overrides on ``prepare_crop_run``.

Scoring uses ``_corr`` / ``_hike`` imported from
``scripts/score_subannual_crop.py`` so the numbers are the official ones.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
for _p in (str(ROOT), str(ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from sheaf.calendar24 import STEPS_PER_YEAR, monthly_mean_from_steps
from sheaf.data_faostat import (
    SHEAF_NODE_MAP,
    aggregate_to_nodes,
    load_trade_matrix,
)
from sheaf.data_usda import load_price_series_monthly
from sheaf.dynamic_crop import (
    CropPrep,
    _ask_reweight_dest,
    _bilateral_clear,
    _repair_vietnam_rice_e0,
    prepare_crop_run,
    simulate_prep,
)
from sheaf.seasonal import rolling_ahead_variable, steps_to_harvest_pulse

from score_subannual_crop import _corr, _hike  # official metrics

CROPS = ("wheat", "maize", "rice")
OBS_HIKES = {"wheat": (1.82, 1.16), "maize": (1.84, 1.44), "rice": (1.84, 0.79)}
# published shipped-baseline scores (diagnostics/gate0_prep/a5/)
SHIPPED = {
    "wheat": (0.720, 2.27, 1.45),
    "maize": (0.712, 1.97, 1.70),
    "rice": (0.678, 1.72, 0.82),
}


# --------------------------------------------------------------------------
# baseline (FAOSTAT) exporter shares — Agrimate's X*_{I,r} / X*_I
# --------------------------------------------------------------------------
def baseline_export_shares(crop: str, countries: list[str],
                           window: tuple[int, int] = (2006, 2007)) -> np.ndarray:
    E = aggregate_to_nodes(load_trade_matrix(crop, window=window),
                           SHEAF_NODE_MAP)
    E = E.reindex(index=countries, columns=countries, fill_value=0.0)
    if crop.lower().strip() == "rice":
        E = _repair_vietnam_rice_e0(E, countries)
    M = E.to_numpy(dtype=float, copy=True)
    np.fill_diagonal(M, 0.0)
    row = M.sum(axis=1)
    tot = float(row.sum())
    return row / tot if tot > 0 else row


def trade_matrix_nodes(crop: str, countries: list[str],
                       window: tuple[int, int] = (2006, 2007)) -> pd.DataFrame:
    E = aggregate_to_nodes(load_trade_matrix(crop, window=window),
                           SHEAF_NODE_MAP)
    return E.reindex(index=countries, columns=countries, fill_value=0.0)


# --------------------------------------------------------------------------
# allocation variants
# --------------------------------------------------------------------------
def _source_reweight(S: np.ndarray, ask: np.ndarray, p0: float,
                     sigma: float) -> np.ndarray:
    """CES-over-sources: importer j tilts its source mix toward cheap offers.

    Agrimate Eq. (8c): a_rs * (p_off,r / p_->s)^-sigma, renormalised over r.
    """
    rel = (float(p0) / np.maximum(ask, 1e-6)) ** sigma
    S_eff = S * rel[:, None]
    col = S_eff.sum(axis=0, keepdims=True)
    np.divide(S_eff, col, out=S_eff, where=col > 0)
    return S_eff


def _agrimate_clear(offers, demand, S_eff, subst):
    """Purchaser CES allocation + proportional supplier rationing.

    No exporter destination-mix cap (that is the SHEAF-specific constraint).
    Residual pool identical in form to the shipped one so the only difference
    under test is the removal of the row-side cap.
    """
    req = S_eff * demand[None, :]                       # requests i <- j
    req_i = req.sum(axis=1)
    ration = np.ones_like(offers)
    hot = req_i > offers
    ration[hot] = offers[hot] / np.maximum(req_i[hot], 1e-15)
    ship = req * ration[:, None]

    offer_left = np.maximum(0.0, offers - ship.sum(axis=1))
    demand_left = np.maximum(0.0, demand - ship.sum(axis=0))
    take = subst * demand_left
    tot_o, tot_t = float(offer_left.sum()), float(take.sum())
    if tot_o > 1e-15 and tot_t > 1e-15:
        fill = min(1.0, tot_o / tot_t)
        recv2 = take * fill
        w = recv2 / max(float(recv2.sum()), 1e-15)
        ship2 = offer_left[:, None] * w[None, :]
        col = ship2.sum(axis=0)
        scale = np.ones_like(recv2)
        mask = col > recv2 + 1e-15
        scale[mask] = recv2[mask] / col[mask]
        ship = ship + ship2 * scale[None, :]
    return ship.sum(axis=1), ship.sum(axis=0), ship


# --------------------------------------------------------------------------
# replica of _simulate_window with the market-power / allocation switches
# --------------------------------------------------------------------------
def simulate_r4(
        H, C_flex, C_ind, cuts, stock0, safety, p0, C_ann, A, S, params,
        free_twin=None, unmet_twin=None, H_seasonal=None,
        mp_alpha: float = 0.0,
        mp_form: str = "exp",
        s_ref: np.ndarray | None = None,
        flow_alpha: float = 0.0,
        x_ref: np.ndarray | None = None,
        alloc_mode: str = "shipped",
        record: bool = True,
) -> dict:
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
    askeff_path = np.zeros((n, T))
    markup_path = np.ones((n, T))
    flow_path = np.ones(T)
    share_path = np.zeros((n, T))
    recv_path = np.zeros((n, T))
    block_path = np.zeros(T)
    ptrade_path = np.zeros(T)
    pscar_path = np.full(T, np.nan)
    trade_path = np.zeros((n, n, T)) if record else None

    p = float(p0)
    ask = np.full(n, float(p0))
    safety_w = float(max(safety.sum(), 1.0))
    carry_cap = params.max_stu * C_ann
    food_step = C_ann / STEPS_PER_YEAR

    H_exp = H if H_seasonal is None else (
        params.foresight_phi * H + (1.0 - params.foresight_phi) * H_seasonal)
    lean_h = steps_to_harvest_pulse(H_exp, frac=params.harvest_pulse_frac,
                                    max_horizon=STEPS_PER_YEAR)
    H_ahead = rolling_ahead_variable(H_exp, lean_h)
    C_ahead = rolling_ahead_variable(C_step, lean_h)

    elast, inv_eta = params.elast, params.inv_eta
    smooth, trade_w = params.smooth, params.trade_w
    sigma = params.ask_comp_elast

    for t in range(T):
        avail = stock + H[:, t]
        desired_flex = np.maximum(C_flex[:, t] * (p / p0) ** elast, 0.0)
        desired = desired_flex + C_ind[:, t]

        lean_gap = np.maximum(
            0.0, C_ahead[:, t] + C_step[:, t] - H_ahead[:, t] - H_exp[:, t])
        target = lean_gap + safety

        after_food_stock = np.maximum(0.0, avail - desired)
        food_need = np.maximum(0.0, desired - avail)
        rebuild = params.rebuild_lambda * np.maximum(
            0.0, target - after_food_stock)
        demand = food_need + rebuild
        offers = np.maximum(0.0, avail - desired - target) * (1.0 - cuts[:, t])

        # ---- Agrimate-style share-dependent markup on the offer price ----
        tot_o = float(offers.sum())
        share = offers / tot_o if tot_o > 1e-12 else np.zeros(n)
        markup = np.ones(n)
        if mp_alpha > 0.0:
            sr = (np.zeros(n) if s_ref is None else s_ref[:, t])
            if mp_form == "lerner":
                num = np.clip(1.0 - mp_alpha * sr, 0.05, None)
                den = np.clip(1.0 - mp_alpha * share, 0.05, None)
                markup = num / den
            else:
                markup = np.exp(mp_alpha * (share - sr))
            markup = np.clip(markup, 0.25, 4.0)

        # ---- Agrimate Eq. (D.9): common isoelastic inverse demand on the
        # total supply to the international market, relative to baseline ----
        flow = 1.0
        if flow_alpha > 0.0 and x_ref is not None:
            xr = float(x_ref[t])
            f = 0.02 * float(np.mean(x_ref)) + 1e-9
            flow = float(np.clip(((xr + f) / (tot_o + f)) ** flow_alpha,
                                 0.25, 4.0))
        markup = markup * flow
        ask_eff = ask * markup

        if alloc_mode == "shipped":
            A_eff = _ask_reweight_dest(A, ask_eff, p0, gamma=sigma)
            shipped, received, ship = _bilateral_clear(
                offers, demand, A_eff, S, subst=params.residual_subst)
        elif alloc_mode == "source":
            A_eff = _ask_reweight_dest(A, ask_eff, p0, gamma=sigma)
            S_eff = _source_reweight(S, ask_eff, p0, sigma)
            shipped, received, ship = _bilateral_clear(
                offers, demand, A_eff, S_eff, subst=params.residual_subst)
        elif alloc_mode == "agrimate":
            S_eff = _source_reweight(S, ask_eff, p0, sigma)
            shipped, received, ship = _agrimate_clear(
                offers, demand, S_eff, params.residual_subst)
        else:
            raise ValueError(f"alloc_mode={alloc_mode!r}")

        consumption = np.minimum(
            desired, np.maximum(0.0, avail - shipped + received))
        stock = np.maximum(0.0, avail - shipped - consumption + received)
        warehouse = (carry_cap + food_step * float(params.pipeline_max_steps)
                     + (H[:, t] if params.pipeline_max_steps > 0 else 0.0))
        excess = np.maximum(0.0, stock - warehouse)
        stock = stock - params.warehouse_lambda * excess

        fill = shipped / np.maximum(offers, 1e-9)
        fill = np.where(offers > 1e-9, fill, params.ask_target_fill)
        total_d = float(demand.sum())
        preferred_block = float((S * cuts[:, t][:, None] * demand[None, :]).sum())
        block_frac = preferred_block / max(total_d, 1e-9)
        rival = float(max(params.ask_rival, 0.0)) * block_frac
        ask = ask * np.exp(params.ask_alpha * (fill - params.ask_target_fill)
                           + np.where(offers > 1e-9, rival, 0.0))
        ask = (1.0 - params.ask_beta) * ask + params.ask_beta * p
        ask = np.clip(ask, 0.45 * p0, 2.8 * p0)

        lean_need = float(lean_gap.sum())
        locked = float((cuts[:, t] * np.maximum(0.0, stock - target)).sum())
        free = float(stock.sum()) - lean_need - locked

        unmet = max(0.0, total_d - float(received.sum()))
        unmet_frac = unmet / max(total_d, 1e-9)

        # shipped code evaluates p_trade on the *updated* ask vector
        shipped_sum = float(shipped.sum())
        ask_idx = ask * markup
        p_trade = (float(np.dot(ask_idx, shipped) / shipped_sum)
                   if shipped_sum > 1e-12 else p)

        p_scar = np.nan
        if free_twin is None:
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
                p_scar = (p0 * ratio ** inv_eta
                          * (1.0 + params.unmet_kappa * u_anom
                             + params.block_kappa * block_frac))
                p_star = trade_w * p_trade + (1.0 - trade_w) * p_scar

        p = float(smooth * p + (1.0 - smooth) * p_star)
        p = float(np.clip(p, 60.0, 1200.0))

        price[t] = p
        stock_path[:, t] = stock
        cons_path[:, t] = consumption
        exp_path[:, t] = shipped
        free_path[t] = free
        unmet_path[t] = unmet_frac
        offer_path[:, t] = offers
        demand_path[:, t] = demand
        ask_path[:, t] = ask
        askeff_path[:, t] = ask_eff
        markup_path[:, t] = markup
        flow_path[t] = flow
        share_path[:, t] = share
        recv_path[:, t] = received
        block_path[t] = block_frac
        ptrade_path[t] = p_trade
        pscar_path[t] = p_scar
        if record:
            trade_path[:, :, t] = ship

    return dict(price=price, stock=stock_path, cons=cons_path,
                exports=exp_path, free=free_path, unmet=unmet_path,
                offers=offer_path, demand=demand_path, ask=ask_path,
                ask_eff=askeff_path, markup=markup_path, flow=flow_path,
                share=share_path,
                received=recv_path, block_frac=block_path,
                p_trade=ptrade_path, p_scar=pscar_path, trade=trade_path)


# --------------------------------------------------------------------------
# prep-level drivers
# --------------------------------------------------------------------------
def retwin(prep: CropPrep, alloc_mode: str = "shipped") -> dict:
    """Recompute the calm twin under a given allocation rule.

    Returns free / unmet reference paths and the per-step offer shares s*_r.
    With ``alloc_mode="shipped"`` these reproduce ``prep.free_twin`` /
    ``prep.unmet_twin`` exactly, which is the self-consistency check.
    """
    H_for_twin = prep.H if prep.params.twin_harvest == "realized" else prep.H_seas
    out = simulate_r4(
        H_for_twin, prep.C_flex_twin, prep.C_ind_twin,
        np.zeros_like(H_for_twin), prep.stock0.copy(), prep.safety, prep.p0,
        prep.C_ann, prep.A, prep.S, prep.params,
        free_twin=None, H_seasonal=prep.H_seas,
        alloc_mode=alloc_mode, record=False)
    return dict(free_twin=out["free"], unmet_twin=out["unmet"],
                s_ref=out["share"], x_ref=out["offers"].sum(axis=0))


def run_prep(prep: CropPrep, cuts=None, harvest=None, twin: dict | None = None,
             **kw) -> dict:
    H = prep.H if harvest is None else harvest
    cuts_use = prep.cuts if cuts is None else cuts
    ft = prep.free_twin if twin is None else twin["free_twin"]
    ut = prep.unmet_twin if twin is None else twin["unmet_twin"]
    if twin is not None:
        kw.setdefault("s_ref", twin["s_ref"])
        kw.setdefault("x_ref", twin["x_ref"])
    return simulate_r4(
        H, prep.C_flex, prep.C_ind, cuts_use, prep.stock0.copy(),
        prep.safety, prep.p0, prep.C_ann, prep.A, prep.S, prep.params,
        free_twin=ft, unmet_twin=ut, H_seasonal=prep.H_seas, **kw)


def verify_replica(crop: str = "wheat", **kw) -> dict:
    prep = prepare_crop_run(crop, **kw)
    ref = simulate_prep(prep)
    got = run_prep(prep)
    return dict(crop=crop,
                d_price=float(np.max(np.abs(ref.price - got["price"]))),
                d_stock=float(np.max(np.abs(ref.stock - got["stock"]))),
                d_trade=float(np.max(np.abs(ref.trade - got["trade"]))),
                d_exp=float(np.max(np.abs(ref.exports - got["exports"]))))


# --------------------------------------------------------------------------
# scoring (official _corr / _hike)
# --------------------------------------------------------------------------
_OBS: dict = {}


def obs_monthly(crop: str, y0=2006, y1=2011) -> pd.DataFrame:
    key = (crop, y0, y1)
    if key not in _OBS:
        o = load_price_series_monthly(deflated=True)
        o = o[(o.year >= y0) & (o.year <= y1)][["year", "month", crop]].rename(
            columns={crop: "obs_price"})
        _OBS[key] = o
    return _OBS[key]


def to_monthly(price, y0=2006, y1=2011) -> pd.DataFrame:
    rows = monthly_mean_from_steps(np.asarray(price, float), y0, y1)
    return pd.DataFrame([dict(year=r["year"], month=r["month"],
                              model_price=r["value"]) for r in rows])


def score(price, crop: str, y0=2006, y1=2011) -> dict:
    m = to_monthly(price, y0, y1).merge(obs_monthly(crop, y0, y1),
                                        on=["year", "month"], how="left")
    return dict(corr=_corr(m.model_price, m.obs_price),
                h0708=_hike(m, "model_price", 2006, 6, 2008, 3),
                h1011=_hike(m, "model_price", 2009, 6, 2011, 2))


def official_price(crop: str, **kw) -> np.ndarray:
    """Official P1 matched leg: harvest + AMIS, mean flex, industrial default."""
    prep = prepare_crop_run(crop, use_amis=True, use_shocks=True,
                            use_demand=False, **{k: v for k, v in kw.items()
                                                 if k in _PREP_KEYS})
    sim_kw = {k: v for k, v in kw.items() if k not in _PREP_KEYS}
    return prep, run_prep(prep, **sim_kw)


_PREP_KEYS = {"ask_rival", "inv_eta", "trade_w", "residual_subst",
              "ask_comp_elast", "block_kappa", "unmet_kappa", "ask_alpha",
              "ask_beta", "elast", "smooth"}


# --------------------------------------------------------------------------
# the four robustness assertions, re-expressed against the variant model
# --------------------------------------------------------------------------
_LIFT_WINDOW = {"wheat": (2010, 8, 2010, 12, 0.05),
                "rice": (2008, 1, 2008, 6, 0.05),
                "maize": (2007, 5, 2008, 6, 0.00)}
_EXPORTER_WIN = {"wheat": ("Russia", 2010, 8, 2010, 12, 0.20, 0.85),
                 "rice": ("Vietnam", 2008, 9, 2008, 11, 0.70, None),
                 "maize": ("Argentina", 2007, 5, 2007, 5, 0.70, None)}


def _steps(y0, m0, y1, m1, sy=2006):
    return ((y0 - sy) * STEPS_PER_YEAR + (m0 - 1) * 2,
            (y1 - sy) * STEPS_PER_YEAR + (m1 - 1) * 2 + 2)


def asserts(crop: str, alloc_mode="shipped", overrides: dict | None = None,
            **sim_kw) -> dict:
    ov = dict(overrides or {})
    calm = dict(use_shocks=False, use_demand=False, use_industrial=False)

    # 1. twin identity + 4. no spring spike (same calm run)
    prep = prepare_crop_run(crop, use_amis=False, **calm, **ov)
    tw = retwin(prep, alloc_mode=alloc_mode)
    res = run_prep(prep, twin=tw, alloc_mode=alloc_mode, **sim_kw)
    p0 = float(res["price"][0])
    tail = res["price"][STEPS_PER_YEAR:]
    twin_drift = float(np.max(np.abs(tail - p0)) / max(p0, 1.0))
    twin_free = float(np.max(np.abs(res["free"] - tw["free_twin"])))
    m = to_monthly(res["price"], prep.start_year, prep.end_year)
    spring = float(m[m.month.isin([3, 4])].model_price.mean())
    autumn = float(m[m.month.isin([9, 10])].model_price.mean())
    spring_ratio = spring / max(autumn, 1e-9)

    # 2. AMIS raises price (perturbed baseline, A2f protocol)
    y0, m0, y1, m1, floor = _LIFT_WINDOW[crop]
    prep_t = prepare_crop_run(crop, use_amis=True, **calm, **ov)
    tw_t = retwin(prep_t, alloc_mode=alloc_mode)
    tau = run_prep(prep_t, twin=tw_t, alloc_mode=alloc_mode, **sim_kw)
    base = run_prep(prep, twin=tw, harvest=prep.H * (1.0 - 1e-6),
                    alloc_mode=alloc_mode, **sim_kw)
    t0, t1 = _steps(y0, m0, y1, m1, prep.start_year)
    lift = (float(np.mean(tau["price"][t0:t1]))
            / max(float(np.mean(base["price"][t0:t1])), 1e-9) - 1.0)

    # 3. AMIS cuts exporter offers (and wheat shipments)
    country, a0, b0, a1, b1, max_off, max_shp = _EXPORTER_WIN[crop]
    base2 = run_prep(prep, twin=tw, alloc_mode=alloc_mode, **sim_kw)
    i = prep.countries.index(country)
    u0, u1 = _steps(a0, b0, a1, b1, prep.start_year)
    off_ratio = (float(np.mean(tau["offers"][i, u0:u1]))
                 / max(float(np.mean(base2["offers"][i, u0:u1])), 1e-12))
    shp_ratio = (float(np.mean(tau["exports"][i, u0:u1]))
                 / max(float(np.mean(base2["exports"][i, u0:u1])), 1e-12))

    return dict(
        twin_drift=twin_drift, twin_free_err=twin_free,
        twin_pass=bool(twin_drift <= 0.02 and twin_free <= 1.0),
        lift=lift, lift_floor=floor, lift_pass=bool(lift >= floor),
        offer_ratio=off_ratio, offer_max=max_off,
        offer_pass=bool(off_ratio <= max_off),
        ship_ratio=shp_ratio, ship_max=max_shp,
        ship_pass=bool(max_shp is None or shp_ratio <= max_shp),
        spring_ratio=spring_ratio, spring_pass=bool(spring_ratio <= 1.25),
    )


def reweight_is_noop(prep: CropPrep, gamma: float = 1.25) -> float:
    """max|A_eff - A| for a random ask vector — 0 means the reweight is inert."""
    rng = np.random.default_rng(0)
    ask = prep.p0 * np.exp(rng.normal(0, 0.4, size=prep.A.shape[0]))
    A_eff = _ask_reweight_dest(prep.A, ask, prep.p0, gamma=gamma)
    return float(np.max(np.abs(A_eff - prep.A)))
