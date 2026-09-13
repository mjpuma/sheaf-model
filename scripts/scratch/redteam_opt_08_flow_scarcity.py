#!/usr/bin/env python3
"""Red team / optimisation, probe 8: the sign of the scarcity channel.

Probe 7 established that on the official scored leg the scarcity ratio
r_t = (F^twin+f)/(F+f) moves the WRONG WAY across both crisis windows for
wheat (1.032 -> 0.873) and rice (0.991 -> 0.152), so the pure
inverse-demand price p0 r^eta FALLS while the observed price rises, and
p^tr carries 63-118% of the realised move in p*.

MECHANISM HYPOTHESIS (M1).  F is a STOCK residual and the twin is priced
at p0 by construction (dynamics.tex, "Twin closure"). When the treatment
price rises, eq (1) cuts desired demand, so the treatment consumes less
than the twin and ACCUMULATES stock relative to it. F - F^twin therefore
rises with p, r falls, and p^scar falls. The scarcity channel is a
negative feedback on price and can be self-defeating.
Test: corr(p_t, F_t - F^twin_t) > 0 on the scored leg.

CANDIDATE FIX (Agrimate-aligned).  Agrimate's price function (their Eq. 3)
is isoelastic inverse demand over SUPPLY FLOWS to the market -- own
expected supply plus competitors' -- not over a stock residual. Replacing
the argument of eq (17) with a flow keeps eta, adds no parameter and no
state, and makes the export restriction tau enter the price through the
quantity it actually reduces (offers, eq 5) rather than through the
ad hoc `locked` term and kappa_b.
    scar="offers"  r_t = (sum_i O^twin_i,t + f_o) / (sum_i O_i,t + f_o)
    scar="avail"   r_t = (sum_i avail^twin_i,t + f_a) / (sum_i avail_i,t + f_a)
Both are tested under the shipped ask law and under the exporter FOC.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

from sheaf.calendar24 import STEPS_PER_YEAR  # noqa: E402
from sheaf.data_usda import load_price_series_monthly  # noqa: E402
from sheaf.dynamic_crop import (  # noqa: E402
    MAX_LEAN_STEPS, _bilateral_clear, _EXPORTER_WINDOWS, prepare_crop_run,
    result_to_monthly,
)
from sheaf.seasonal import rolling_ahead_variable, steps_to_harvest_pulse  # noqa: E402

sys.path.insert(0, str(ROOT / "scripts" / "scratch"))
from redteam_opt_03_exporter_foc import (  # noqa: E402
    _hike, as_result, reweight_dest_shipped, reweight_source_ces,
)
import redteam_opt_04_foc_diagnosis as m4  # noqa: E402

OUT = ROOT / "diagnostics" / "gate0_prep" / "redteam" / "optimisation"
OUT.mkdir(parents=True, exist_ok=True)
CROPS = ("wheat", "maize", "rice")


def simulate(H, C_flex, C_ind, cuts, stock0, safety, p0, C_ann, A, S, params,
             free_twin=None, unmet_twin=None, H_seasonal=None,
             free_twin_country=None, twin_flow=None,
             law="ask", scar="stock", use_ces=False, calm_branch=True):
    n, T = H.shape
    C_step = C_flex + C_ind
    stock = stock0.copy()
    price = np.zeros(T)
    stock_path = np.zeros((n, T))
    cons_path = np.zeros((n, T))
    exp_path = np.zeros((n, T))
    free_path = np.zeros(T)
    free_country = np.zeros((n, T))
    unmet_path = np.zeros(T)
    offer_path = np.zeros((n, T))
    demand_path = np.zeros((n, T))
    ask_path = np.zeros((n, T))
    recv_path = np.zeros((n, T))
    trade_path = np.zeros((n, n, T))
    avail_path = np.zeros(T)
    ratio_path = np.zeros(T)
    pscar_path = np.zeros(T)
    ptr_path = np.zeros(T)
    p = float(p0)
    ask = np.full(n, float(p0))
    safety_w = float(max(safety.sum(), 1.0))
    carry_cap = params.max_stu * C_ann
    food_step = C_ann / STEPS_PER_YEAR
    H_exp = H if H_seasonal is None else (
        params.foresight_phi * H + (1.0 - params.foresight_phi) * H_seasonal)
    lean_h = steps_to_harvest_pulse(H_exp, frac=params.harvest_pulse_frac,
                                    max_horizon=MAX_LEAN_STEPS)
    H_ahead = rolling_ahead_variable(H_exp, lean_h)
    C_ahead = rolling_ahead_variable(C_step, lean_h)
    elast, inv_eta = params.elast, params.inv_eta
    smooth, trade_w = params.smooth, params.trade_w

    for t in range(T):
        avail = stock + H[:, t]
        avail_path[t] = float(avail.sum())
        desired = np.maximum(C_flex[:, t] * (p / p0) ** elast, 0.0) + C_ind[:, t]
        lean_gap = np.maximum(
            0.0, C_ahead[:, t] + C_step[:, t] - H_ahead[:, t] - H_exp[:, t])
        target = lean_gap + safety
        after = np.maximum(0.0, avail - desired)
        demand = (np.maximum(0.0, desired - avail)
                  + params.rebuild_lambda * np.maximum(0.0, target - after))
        offers = np.maximum(0.0, avail - desired - target) * (1.0 - cuts[:, t])
        offer_path[:, t] = offers
        demand_path[:, t] = demand
        ask_path[:, t] = ask
        A_eff = reweight_dest_shipped(A, ask, p0, params.ask_comp_elast)
        S_eff = (reweight_source_ces(S, ask, p0, params.ask_comp_elast)
                 if use_ces else S)
        shipped, received, ship = _bilateral_clear(
            offers, demand, A_eff, S_eff, subst=params.residual_subst)
        recv_path[:, t] = received
        trade_path[:, :, t] = ship
        consumption = np.minimum(
            desired, np.maximum(0.0, avail - shipped + received))
        stock = np.maximum(0.0, avail - shipped - consumption + received)
        warehouse = (carry_cap + food_step * float(params.pipeline_max_steps)
                     + (H[:, t] if params.pipeline_max_steps > 0 else 0.0))
        stock = stock - params.warehouse_lambda * np.maximum(
            0.0, stock - warehouse)
        total_d = float(demand.sum())
        block_frac = float(
            (S * cuts[:, t][:, None] * demand[None, :]).sum()) / max(total_d, 1e-9)
        F_i = stock - lean_gap
        free_country[:, t] = F_i
        locked = float((cuts[:, t] * np.maximum(0.0, stock - target)).sum())
        free = float(stock.sum()) - float(lean_gap.sum()) - locked
        free_path[t] = free

        if law == "ask":
            fill = shipped / np.maximum(offers, 1e-9)
            fill = np.where(offers > 1e-9, fill, params.ask_target_fill)
            ask = ask * np.exp(
                params.ask_alpha * (fill - params.ask_target_fill)
                + np.where(offers > 1e-9,
                           max(params.ask_rival, 0.0) * block_frac, 0.0))
            ask = (1.0 - params.ask_beta) * ask + params.ask_beta * p
        else:
            Ft_i = (free_twin_country[:, t] if free_twin_country is not None
                    else F_i)
            reg_i = 0.05 * safety + np.maximum(0.0, -np.minimum(F_i, Ft_i))
            r_own = (Ft_i + reg_i) / np.maximum(F_i + reg_i, 1e-12)
            ask = p0 * np.maximum(r_own, 1e-12) ** inv_eta
        ask = np.clip(ask, 0.45 * p0, 2.8 * p0)

        unmet = max(0.0, total_d - float(received.sum()))
        u_frac = unmet / max(total_d, 1e-9)
        unmet_path[t] = u_frac
        p_trade = (float(np.dot(ask, shipped) / shipped.sum())
                   if shipped.sum() > 1e-12 else p)
        ptr_path[t] = p_trade

        if free_twin is None and twin_flow is None:
            p_star = p0
            ratio_path[t] = 1.0
            pscar_path[t] = p0
        else:
            u0 = float(unmet_twin[t]) if unmet_twin is not None else 0.0
            u_an = max(0.0, u_frac - u0)
            if scar == "stock":
                tw = float(free_twin[t])
                sh = 0.05 * safety_w + max(0.0, -min(free, tw))
                ratio = max((tw + sh) / (free + sh), 1e-12)
                calm_x = abs(free - tw) < 1e-6
            elif scar == "offers":
                tw = float(twin_flow["offers"][t])
                base = float(twin_flow["offers_scale"])
                # tau reduces O directly, so the restriction enters here
                sh = 0.05 * base
                ratio = max((tw + sh) / (float(offers.sum()) + sh), 1e-12)
                calm_x = abs(float(offers.sum()) - tw) < 1e-9
            else:
                tw = float(twin_flow["avail"][t])
                base = float(twin_flow["avail_scale"])
                sh = 0.05 * base
                ratio = max((tw + sh) / (float(avail.sum()) + sh), 1e-12)
                calm_x = abs(float(avail.sum()) - tw) < 1e-9
            ratio_path[t] = ratio
            p_scar = (p0 * ratio ** inv_eta
                      * (1.0 + params.unmet_kappa * u_an
                         + params.block_kappa * block_frac))
            pscar_path[t] = p_scar
            calm = calm_x and u_an < 1e-9 and block_frac < 1e-9
            p_star = p0 if (calm and calm_branch) else (
                trade_w * p_trade + (1.0 - trade_w) * p_scar)
        p = float(np.clip(smooth * p + (1.0 - smooth) * p_star, 60.0, 1200.0))
        price[t] = p
        stock_path[:, t] = stock
        cons_path[:, t] = consumption
        exp_path[:, t] = shipped

    return dict(price=price, stock=stock_path, consumption=cons_path,
                exports=exp_path, free=free_path, free_country=free_country,
                unmet=unmet_path, offers=offer_path, demand=demand_path,
                ask=ask_path, received=recv_path, trade=trade_path,
                avail=avail_path, ratio=ratio_path, p_scar=pscar_path,
                p_trade=ptr_path)


def build_run(crop, law="ask", scar="stock", use_ces=False,
              calm_branch=True, harvest_scale=None, **kw):
    prep = prepare_crop_run(crop, **kw)
    cfg = dict(law=law, scar=scar, use_ces=use_ces, calm_branch=calm_branch)
    Ht = prep.H if prep.params.twin_harvest == "realized" else prep.H_seas
    tw = simulate(Ht, prep.C_flex_twin, prep.C_ind_twin, np.zeros_like(Ht),
                  prep.stock0.copy(), prep.safety, prep.p0, prep.C_ann,
                  prep.A, prep.S, prep.params, free_twin=None, twin_flow=None,
                  H_seasonal=prep.H_seas, **cfg)
    o_tw = tw["offers"].sum(axis=0)
    twin_flow = dict(offers=o_tw, offers_scale=max(float(o_tw.mean()), 1e-9),
                     avail=tw["avail"],
                     avail_scale=max(float(tw["avail"].mean()), 1e-9))
    H = prep.H if harvest_scale is None else prep.H * harvest_scale
    out = simulate(H, prep.C_flex, prep.C_ind, prep.cuts, prep.stock0.copy(),
                   prep.safety, prep.p0, prep.C_ann, prep.A, prep.S,
                   prep.params, free_twin=tw["free"], unmet_twin=tw["unmet"],
                   H_seasonal=prep.H_seas,
                   free_twin_country=tw["free_country"],
                   twin_flow=twin_flow, **cfg)
    return prep, tw, out


def score(prep, out, obs):
    m = result_to_monthly(as_result(prep, out)).merge(
        obs, on=["year", "month"], how="left")
    a, b = m.model_price.to_numpy(float), m.obs_price.to_numpy(float)
    k = np.isfinite(a) & np.isfinite(b)
    return dict(
        corr=float(np.corrcoef(a[k], b[k])[0, 1]) if k.sum() > 5 else np.nan,
        hike_0708=_hike(m, "model_price", 2006, 6, 2008, 3),
        hike_1011=_hike(m, "model_price", 2009, 6, 2011, 2))


def main():
    obs_all = load_price_series_monthly(deflated=True)
    print("\n== M1: is the stock-based scarcity channel a negative feedback? ==")
    fb = []
    for crop in CROPS:
        prep, tw, out = build_run(crop, law="ask", scar="stock",
                                  use_amis=True, use_shocks=True,
                                  use_demand=False)
        gap = out["free"] - np.asarray(prep.free_twin, float)
        c_pg = float(np.corrcoef(out["price"], gap)[0, 1])
        c_pr = float(np.corrcoef(out["price"], out["ratio"])[0, 1])
        c_ps = float(np.corrcoef(out["price"], out["p_scar"])[0, 1])
        cons_gap = float((out["consumption"].sum() - tw["consumption"].sum())
                         / max(tw["consumption"].sum(), 1e-9))
        print(f"  {crop:6s} corr(p_t, F_t - F^twin_t) = {c_pg:+.3f}   "
              f"corr(p_t, r_t) = {c_pr:+.3f}   "
              f"corr(p_t, p^scar_t) = {c_ps:+.3f}")
        print(f"         cumulative consumption vs twin: {cons_gap:+.2%} "
              f"(demand suppression accumulates as stock)")
        fb.append(dict(crop=crop, corr_p_stockgap=c_pg, corr_p_ratio=c_pr,
                       corr_p_pscar=c_ps, cons_vs_twin=cons_gap))

    print("\n== flow-based scarcity argument (Agrimate Eq. 3 analogue) ==")
    rows = []
    win_tau = {"wheat": (2010, 8, 2010, 12, 0.05),
               "rice": (2008, 1, 2008, 6, 0.05),
               "maize": (2007, 5, 2008, 6, 0.0)}
    for crop in CROPS:
        obs = obs_all[(obs_all.year >= 2006) & (obs_all.year <= 2011)][
            ["year", "month", crop]].rename(columns={crop: "obs_price"})
        o07 = _hike(obs, "obs_price", 2006, 6, 2008, 3)
        o10 = _hike(obs, "obs_price", 2009, 6, 2011, 2)
        print(f"  {crop} observed: 2007/08 x{o07:.2f}  2010/11 x{o10:.2f}")
        for law in ("ask", "foc"):
            for scar in ("stock", "offers", "avail"):
                ces = law == "foc"
                prep, tw, out = build_run(crop, law=law, scar=scar,
                                          use_ces=ces, use_amis=True,
                                          use_shocks=True, use_demand=False)
                s = score(prep, out, obs)
                c_ps = float(np.corrcoef(out["price"], out["p_scar"])[0, 1])
                # does p^scar now move the right way in the crisis?
                rr = out["ratio"]
                # calm rest point
                _, _, oc = build_run(crop, law=law, scar=scar, use_ces=ces,
                                     calm_branch=False, use_amis=False,
                                     use_shocks=False, use_demand=False,
                                     use_industrial=False)
                drift = float(np.max(np.abs(oc["price"][STEPS_PER_YEAR:]
                                            - prep.p0)) / prep.p0)
                # A2 restriction lift
                pt, _, tau = build_run(crop, law=law, scar=scar, use_ces=ces,
                                       use_amis=True, use_shocks=False,
                                       use_demand=False, use_industrial=False)
                _, _, base = build_run(crop, law=law, scar=scar, use_ces=ces,
                                       use_amis=False, use_shocks=False,
                                       use_demand=False,
                                       use_industrial=False,
                                       harvest_scale=1 - 1e-6)
                wy0, wm0, wy1, wm1, floor = win_tau[crop]
                t0 = (wy0 - pt.start_year) * STEPS_PER_YEAR + (wm0 - 1) * 2
                t1 = (wy1 - pt.start_year) * STEPS_PER_YEAR + (wm1 - 1) * 2 + 2
                lift = (float(np.mean(tau["price"][t0:t1]))
                        / max(float(np.mean(base["price"][t0:t1])), 1e-9) - 1)
                print(f"    {law:4s} scar={scar:7s} corr {s['corr']:+.3f}  "
                      f"2007/08 x{s['hike_0708']:.2f}  "
                      f"2010/11 x{s['hike_1011']:.2f}  "
                      f"corr(p,p^scar) {c_ps:+.3f}  r mean {rr.mean():.2f}  "
                      f"calm {drift:6.2%}  A2 {lift:+7.2%}"
                      f"{'P' if lift >= floor else 'F'}")
                rows.append(dict(crop=crop, law=law, scar=scar,
                                 obs_0708=o07, obs_1011=o10,
                                 corr_p_pscar=c_ps, r_mean=float(rr.mean()),
                                 calm_drift=drift, A2_lift=lift,
                                 A2_pass=bool(lift >= floor), **s))
    pd.DataFrame(fb).to_csv(OUT / "scarcity_feedback.csv", index=False)
    pd.DataFrame(rows).to_csv(OUT / "flow_scarcity.csv", index=False)
    print(f"\nwrote {OUT/'scarcity_feedback.csv'}\nwrote {OUT/'flow_scarcity.csv'}")


if __name__ == "__main__":
    main()
