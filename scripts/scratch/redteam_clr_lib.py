#!/usr/bin/env python3
"""Red-team slot 2 (clearing / allocation / price formation) shared library.

Read-only with respect to ``sheaf/``. This module carries a *replica* of
``sheaf.dynamic_crop._simulate_window`` that exposes every internal array
(desired use, cover target, per-link short-side vs residual-pool shipments,
capacity drawdown, rationing) and admits switchable variants for the
prototypes in task 4. The replica is verified against the shipped
implementation to machine precision by ``verify_replica``; nothing here is
trusted until that check passes.

Variant switches (all default to the shipped behaviour):

``unmet_mode``   : "onesided" (shipped, eq. 20 truncated at zero) | "twosided"
``tat_kappa``    : >0 adds an excess-demand (tatonnement) term to p*
``clearing_mode``: "blend" (shipped) | "solve" (per-step bracketed root of a
                   flow market-clearing condition, task 4c cost probe)
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from sheaf.calendar24 import STEPS_PER_YEAR
from sheaf.data_usda import load_price_series_monthly
from sheaf.dynamic_crop import (
    CropPrep,
    _ask_reweight_dest,
    prepare_crop_run,
    simulate_prep,
)
from sheaf.seasonal import rolling_ahead_variable, steps_to_harvest_pulse

CROPS = ("wheat", "maize", "rice")


# --------------------------------------------------------------------------
# instrumented bilateral clearing
# --------------------------------------------------------------------------
def source_reweight(S: np.ndarray, ask: np.ndarray, p0: float,
                    gamma: float = 1.25) -> np.ndarray:
    """Importer-side analogue of ``_ask_reweight_dest``.

    ``S_ij`` is importer j's share of supply from exporter i, so the columns
    sum to one. Scaling row i by ``(p0/q_i)^gamma`` and then renormalising
    *columns* is non-vacuous: within a column the multiplier varies across i.
    Scaling rows and renormalising rows (what the shipped code does) is not.
    """
    rel = (float(p0) / np.maximum(ask, 1e-6)) ** gamma
    S_eff = S * rel[:, None]
    col = S_eff.sum(axis=0, keepdims=True)
    np.divide(S_eff, col, out=S_eff, where=col > 0)
    return S_eff


def clear_instrumented(offers, demand, A, S, subst=0.15):
    """``_bilateral_clear`` with the two stages kept separate.

    Returns dict with ship1 (preferred-network short side), ship2 (residual
    pool), and the unexploited leftovers on both sides after both stages.
    """
    O = offers[:, None] * A
    D = S * demand[None, :]
    ship1 = np.minimum(O, D)

    offer_left = np.maximum(0.0, offers - ship1.sum(axis=1))
    demand_left = np.maximum(0.0, demand - ship1.sum(axis=0))
    take = subst * demand_left
    tot_o = float(offer_left.sum())
    tot_t = float(take.sum())
    ship2 = np.zeros_like(ship1)
    if tot_o > 1e-15 and tot_t > 1e-15:
        fill = min(1.0, tot_o / tot_t)
        recv2 = take * fill
        w = recv2 / max(float(recv2.sum()), 1e-15)
        ship2 = offer_left[:, None] * w[None, :]
        col = ship2.sum(axis=0)
        scale = np.ones_like(recv2)
        mask = col > recv2 + 1e-15
        scale[mask] = recv2[mask] / col[mask]
        ship2 = ship2 * scale[None, :]

    ship = ship1 + ship2
    return dict(
        ship=ship, ship1=ship1, ship2=ship2,
        # what stage 1 could not match
        offer_left1=offer_left, demand_left1=demand_left,
        # what remains unexploited after BOTH stages
        offer_left2=np.maximum(0.0, offers - ship.sum(axis=1)),
        demand_left2=np.maximum(0.0, demand - ship.sum(axis=0)),
        O=O, D=D,
    )


# --------------------------------------------------------------------------
# replica of _simulate_window with instrumentation + variant switches
# --------------------------------------------------------------------------
def simulate_instrumented(
        prep: CropPrep,
        harvest=None,
        cuts=None,
        unmet_mode: str = "onesided",
        tat_kappa: float = 0.0,
        tat_mode: str = "consumption",
        alloc_mode: str = "shipped",
        alloc_gamma: float | None = None,
        ask_floor_frac: float = 0.45,
        ask_ceil_frac: float = 2.8,
        clearing_mode: str = "blend",
        drawdown_lambda: float | None = None,
        record_trade: bool = True,
) -> dict:
    H = prep.H if harvest is None else np.asarray(harvest, float)
    cuts_use = prep.cuts if cuts is None else np.asarray(cuts, float)
    C_flex, C_ind = prep.C_flex, prep.C_ind
    stock0, safety, p0 = prep.stock0.copy(), prep.safety, prep.p0
    C_ann, A, S, params = prep.C_ann, prep.A, prep.S, prep.params
    free_twin, unmet_twin = prep.free_twin, prep.unmet_twin
    H_seasonal = prep.H_seas

    n, T = H.shape
    C_step = C_flex + C_ind
    stock = stock0.copy()
    lam_W = params.warehouse_lambda if drawdown_lambda is None else drawdown_lambda

    rec = {k: np.zeros(T) for k in (
        "price", "p_star", "p_trade", "p_scar", "ratio", "free", "unmet_frac",
        "u_anom", "block_frac", "calm", "world_ship", "world_recv",
        "world_offers", "world_demand", "world_desired", "world_avail",
        "world_ship1", "world_ship2", "offer_left2", "demand_left2",
        "double_coincidence", "drawdown", "rationing", "slack", "world_H",
        "world_cons", "world_stock", "excess_above_cap", "tat_term",
        "solve_iters",
    )}
    mat = {k: np.zeros((n, T)) for k in (
        "offers", "demand", "ask", "shipped", "received", "cons", "stock",
        "desired", "target", "lean_gap", "drawdown_i", "avail",
    )}
    trade = np.zeros((n, n, T)) if record_trade else None

    p = float(p0)
    ask = np.full(n, float(p0))
    safety_w = float(max(safety.sum(), 1.0))
    carry_cap = params.max_stu * C_ann
    food_step = C_ann / STEPS_PER_YEAR

    H_exp = (H if H_seasonal is None else
             params.foresight_phi * H + (1.0 - params.foresight_phi) * H_seasonal)
    lean_h = steps_to_harvest_pulse(H_exp, frac=params.harvest_pulse_frac,
                                    max_horizon=STEPS_PER_YEAR)
    H_ahead = rolling_ahead_variable(H_exp, lean_h)
    C_ahead = rolling_ahead_variable(C_step, lean_h)

    elast, inv_eta = params.elast, params.inv_eta
    smooth, trade_w = params.smooth, params.trade_w

    for t in range(T):
        avail = stock + H[:, t]
        desired_flex = np.maximum(C_flex[:, t] * (p / p0) ** elast, 0.0)
        desired = desired_flex + C_ind[:, t]

        lean_gap = np.maximum(
            0.0, C_ahead[:, t] + C_step[:, t] - H_ahead[:, t] - H_exp[:, t])
        target = lean_gap + safety

        after_food_stock = np.maximum(0.0, avail - desired)
        food_need = np.maximum(0.0, desired - avail)
        rebuild = params.rebuild_lambda * np.maximum(0.0, target - after_food_stock)
        demand = food_need + rebuild
        offers = np.maximum(0.0, avail - desired - target) * (1.0 - cuts_use[:, t])

        gam = params.ask_comp_elast if alloc_gamma is None else alloc_gamma
        A_eff = _ask_reweight_dest(A, ask, p0, gamma=gam)
        S_eff = S
        if alloc_mode == "source_reweight":
            # The mechanism eq. (7) claims but cannot deliver: importers shift
            # their *source* mix toward cheaper exporters. Column-normalised,
            # so the per-exporter scalar does not cancel.
            S_eff = source_reweight(S, ask, p0, gamma=gam)
        elif alloc_mode != "shipped":
            raise ValueError(alloc_mode)
        cl = clear_instrumented(offers, demand, A_eff, S_eff,
                                subst=params.residual_subst)
        ship = cl["ship"]
        shipped, received = ship.sum(axis=1), ship.sum(axis=0)

        consumption = np.minimum(desired, np.maximum(0.0, avail - shipped + received))
        stock_pre = np.maximum(0.0, avail - shipped - consumption + received)
        warehouse = (carry_cap + food_step * float(params.pipeline_max_steps)
                     + (H[:, t] if params.pipeline_max_steps > 0 else 0.0))
        excess = np.maximum(0.0, stock_pre - warehouse)
        drawdown_i = lam_W * excess
        stock_new = stock_pre - drawdown_i

        fill = shipped / np.maximum(offers, 1e-9)
        fill = np.where(offers > 1e-9, fill, params.ask_target_fill)
        total_d = float(demand.sum())
        preferred_block = float((S * cuts_use[:, t][:, None] * demand[None, :]).sum())
        block_frac = preferred_block / max(total_d, 1e-9)
        rival = float(max(params.ask_rival, 0.0)) * block_frac
        ask = ask * np.exp(params.ask_alpha * (fill - params.ask_target_fill)
                           + np.where(offers > 1e-9, rival, 0.0))
        ask = (1.0 - params.ask_beta) * ask + params.ask_beta * p
        ask = np.clip(ask, ask_floor_frac * p0, ask_ceil_frac * p0)

        lean_need = float(lean_gap.sum())
        locked = float((cuts_use[:, t] * np.maximum(0.0, stock_new - target)).sum())
        free = float(stock_new.sum()) - lean_need - locked

        unmet = max(0.0, total_d - float(received.sum()))
        unmet_frac = unmet / max(total_d, 1e-9)

        shipped_sum = float(shipped.sum())
        p_trade = (float(np.dot(ask, shipped) / shipped_sum)
                   if shipped_sum > 1e-12 else p)

        u0 = float(unmet_twin[t]) if unmet_twin is not None else 0.0
        if unmet_mode == "twosided":
            u_anom = unmet_frac - u0
        else:
            u_anom = max(0.0, unmet_frac - u0)

        # excess-demand (tatonnement) term: world rationing minus world slack,
        # normalised by world desired use this step
        rationing = float(np.maximum(0.0, desired - (avail - shipped + received)).sum())
        slack = float(np.maximum(0.0, (avail - shipped + received) - desired).sum())
        tat_term = 0.0
        p_scar = np.nan
        ratio = np.nan
        calm = False
        if free_twin is None:
            p_star = p0
        else:
            twin = float(free_twin[t])
            floor0 = 0.05 * safety_w
            shift = floor0 + max(0.0, -min(free, twin))
            ratio = (twin + shift) / (free + shift)
            calm = (abs(free - twin) < 1e-6 and abs(u_anom) < 1e-9
                    and block_frac < 1e-9)
            if calm:
                p_star = p0
            else:
                ratio = float(max(ratio, 1e-12))
                p_scar = (p0 * ratio ** inv_eta
                          * (1.0 + params.unmet_kappa * u_anom
                             + params.block_kappa * block_frac))
                p_star = trade_w * p_trade + (1.0 - trade_w) * p_scar
                if tat_kappa > 0.0:
                    if tat_mode == "consumption":
                        # excess demand in the consumption market
                        z = (rationing - slack) / max(float(desired.sum()), 1e-9)
                    elif tat_mode == "traded":
                        # excess demand in the traded market (unmatched demand
                        # less unsold offers), normalised by import demand
                        z = ((float(cl["demand_left2"].sum())
                              - float(cl["offer_left2"].sum()))
                             / max(total_d, 1e-9))
                    elif tat_mode == "imbalance":
                        # bounded matching imbalance in [-1, 1]
                        dl = float(cl["demand_left2"].sum())
                        ol = float(cl["offer_left2"].sum())
                        z = (dl - ol) / max(dl + ol, 1e-12)
                    else:
                        raise ValueError(tat_mode)
                    tat_term = tat_kappa * z
                    p_star = p_star * (1.0 + tat_term)

        p = float(smooth * p + (1.0 - smooth) * p_star)
        p = float(np.clip(p, 60.0, 1200.0))

        stock = stock_new
        rec["price"][t] = p
        rec["p_star"][t] = p_star
        rec["p_trade"][t] = p_trade
        rec["p_scar"][t] = p_scar
        rec["ratio"][t] = ratio
        rec["free"][t] = free
        rec["unmet_frac"][t] = unmet_frac
        rec["u_anom"][t] = u_anom
        rec["block_frac"][t] = block_frac
        rec["calm"][t] = float(calm)
        rec["world_ship"][t] = shipped_sum
        rec["world_recv"][t] = float(received.sum())
        rec["world_ship1"][t] = float(cl["ship1"].sum())
        rec["world_ship2"][t] = float(cl["ship2"].sum())
        rec["offer_left2"][t] = float(cl["offer_left2"].sum())
        rec["demand_left2"][t] = float(cl["demand_left2"].sum())
        rec["double_coincidence"][t] = min(float(cl["offer_left2"].sum()),
                                           float(cl["demand_left2"].sum()))
        rec["world_offers"][t] = float(offers.sum())
        rec["world_demand"][t] = total_d
        rec["world_desired"][t] = float(desired.sum())
        rec["world_avail"][t] = float(avail.sum())
        rec["drawdown"][t] = float(drawdown_i.sum())
        rec["excess_above_cap"][t] = float(excess.sum())
        rec["rationing"][t] = rationing
        rec["slack"][t] = slack
        rec["world_H"][t] = float(H[:, t].sum())
        rec["world_cons"][t] = float(consumption.sum())
        rec["world_stock"][t] = float(stock_new.sum())
        rec["tat_term"][t] = tat_term
        for k, v in (("offers", offers), ("demand", demand), ("ask", ask),
                     ("shipped", shipped), ("received", received),
                     ("cons", consumption), ("stock", stock_new),
                     ("desired", desired), ("target", target),
                     ("lean_gap", lean_gap), ("drawdown_i", drawdown_i),
                     ("avail", avail)):
            mat[k][:, t] = v
        if record_trade:
            trade[:, :, t] = ship

    out = dict(rec)
    out["mat"] = mat
    out["trade"] = trade
    out["prep"] = prep
    return out


def verify_replica(crop: str = "wheat", **kw) -> dict:
    """Replica must reproduce the shipped price/stock/trade paths exactly."""
    prep = prepare_crop_run(crop, **kw)
    ref = simulate_prep(prep)
    got = simulate_instrumented(prep)
    return dict(
        crop=crop,
        max_abs_price=float(np.max(np.abs(ref.price - got["price"]))),
        max_abs_stock=float(np.max(np.abs(ref.stock - got["mat"]["stock"]))),
        max_abs_trade=float(np.max(np.abs(ref.trade - got["trade"]))),
        max_abs_unmet=float(np.max(np.abs(ref.unmet_frac - got["unmet_frac"]))),
    )


# --------------------------------------------------------------------------
# scoring (mirrors scripts/score_subannual_crop.py)
# --------------------------------------------------------------------------
def _monthly(price: np.ndarray, start_year: int, end_year: int) -> pd.DataFrame:
    from sheaf.calendar24 import monthly_mean_from_steps
    rows = monthly_mean_from_steps(price, start_year, end_year)
    return pd.DataFrame([dict(year=r["year"], month=r["month"],
                              model_price=r["value"]) for r in rows])


def _hike(df, col, y0, m0, y1, m1) -> float:
    def win(y, m):
        vals = []
        for dm in (-1, 0, 1):
            mm, yy = m + dm, y
            if mm < 1:
                mm += 12
                yy -= 1
            if mm > 12:
                mm -= 12
                yy += 1
            hit = df[(df.year == yy) & (df.month == mm)][col]
            if len(hit):
                vals.append(float(hit.iloc[0]))
        return float(np.mean(vals)) if vals else float("nan")
    b, p = win(y0, m0), win(y1, m1)
    return p / b if b and np.isfinite(b) and np.isfinite(p) else float("nan")


_OBS_CACHE: dict = {}


def obs_monthly(crop: str, start_year=2006, end_year=2011) -> pd.DataFrame:
    key = (crop, start_year, end_year)
    if key not in _OBS_CACHE:
        obs = load_price_series_monthly(deflated=True)
        obs = obs[(obs.year >= start_year) & (obs.year <= end_year)][
            ["year", "month", crop]].rename(columns={crop: "obs_price"})
        _OBS_CACHE[key] = obs
    return _OBS_CACHE[key]


def score_price(price: np.ndarray, crop: str, start_year=2006,
                end_year=2011) -> dict:
    m = _monthly(price, start_year, end_year).merge(
        obs_monthly(crop, start_year, end_year), on=["year", "month"], how="left")
    a, b = m.model_price.to_numpy(float), m.obs_price.to_numpy(float)
    msk = np.isfinite(a) & np.isfinite(b)
    corr = float(np.corrcoef(a[msk], b[msk])[0, 1]) if msk.sum() >= 6 else np.nan
    return dict(
        corr=corr,
        h0708=_hike(m, "model_price", 2006, 6, 2008, 3),
        h1011=_hike(m, "model_price", 2009, 6, 2011, 2),
    )


OBS_HIKES = {  # observed deflated Pink Sheet, same windows
    "wheat": (1.82, 1.16),
    "maize": (1.84, 1.44),
    "rice": (1.84, 0.79),
}
