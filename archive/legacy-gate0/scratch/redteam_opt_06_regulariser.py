#!/usr/bin/env python3
"""Red team / optimisation, probe 6: the regulariser and the missing convexity.

Diagnosis assembled from probes 1-5:

  * eq (18) of dynamics.tex regularises the scarcity ratio,
        r_t = (F^twin + f)/(F + f),   f = 0.05 sum_i s_i + max(0, -min(F,F^twin))
    and dynamics.tex already records that f is 4.8 / 3.1 / 10.3 % of mean
    accessible stock and that F < 0 at 58/144 steps for rice.
  * The competitive-storage price function P(availability) is strongly
    CONVEX: flat at ample stocks, explosive near stockout. An additive
    shift f in the denominator removes exactly that convexity, because as
    F -> 0 the ratio tends to (F^twin + f)/f, a FINITE ceiling, rather
    than diverging.  The implied maximum scarcity price is therefore
        p^scar_max = p0 * ((F^twin + f)/f)^eta,
    a hard, parameter-set cap that no shock can exceed.
  * With the convexity suppressed, the shipped model gets its crisis
    amplitude from the ask law drifting into its own [0.45, 2.8] p0
    guardrail instead (probe 5, E2).

TEST.  Shrink the regulariser coefficient c in f = c * sum_i s_i under the
exporter FOC (probe 3), changing NO other parameter, and ask whether the
2007/08 amplitude returns. If it does, the amplitude is available from the
optimisation principle and was being suppressed, not absent.

Also reports the implied analytic ceiling p^scar_max / p0 per crop at each
c, so the reader can see the cap directly.
"""
from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

from sheaf.calendar24 import STEPS_PER_YEAR  # noqa: E402
from sheaf.data_usda import load_price_series_monthly  # noqa: E402
from sheaf.dynamic_crop import (  # noqa: E402
    MAX_LEAN_STEPS,
    _bilateral_clear,
    _EXPORTER_WINDOWS,
    prepare_crop_run,
    result_to_monthly,
)
from sheaf.seasonal import rolling_ahead_variable, steps_to_harvest_pulse  # noqa: E402

sys.path.insert(0, str(ROOT / "scripts" / "scratch"))
from redteam_opt_03_exporter_foc import (  # noqa: E402
    _hike, as_result, reweight_dest_shipped, reweight_source_ces,
)

OUT = ROOT / "diagnostics" / "gate0_prep" / "redteam" / "optimisation"
OUT.mkdir(parents=True, exist_ok=True)
CROPS = ("wheat", "maize", "rice")


def simulate(H, C_flex, C_ind, cuts, stock0, safety, p0, C_ann, A, S, params,
             free_twin=None, unmet_twin=None, H_seasonal=None,
             free_twin_country=None, law="foc", use_ces=True,
             calm_branch=True, reg_c=0.05, mu=1.0):
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
    ratio_path = np.zeros(T)
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
            reg_i = reg_c * safety + np.maximum(0.0, -np.minimum(F_i, Ft_i))
            r_own = (Ft_i + reg_i) / np.maximum(F_i + reg_i, 1e-12)
            ask = mu * p0 * np.maximum(r_own, 1e-12) ** inv_eta
        ask = np.clip(ask, 0.45 * p0, 2.8 * p0)

        unmet = max(0.0, total_d - float(received.sum()))
        u_frac = unmet / max(total_d, 1e-9)
        unmet_path[t] = u_frac
        p_trade = (float(np.dot(ask, shipped) / shipped.sum())
                   if shipped.sum() > 1e-12 else p)

        if free_twin is None:
            p_star = p0
        else:
            tw = float(free_twin[t])
            sh = reg_c * safety_w + max(0.0, -min(free, tw))
            ratio = max((tw + sh) / (free + sh), 1e-12)
            ratio_path[t] = ratio
            u0 = float(unmet_twin[t]) if unmet_twin is not None else 0.0
            u_an = max(0.0, u_frac - u0)
            p_scar = (p0 * ratio ** inv_eta
                      * (1.0 + params.unmet_kappa * u_an
                         + params.block_kappa * block_frac))
            calm = (abs(free - tw) < 1e-6 and u_an < 1e-9 and block_frac < 1e-9)
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
                ratio=ratio_path)


def build_and_run(crop, reg_c, law="foc", use_ces=True, calm_branch=True,
                  harvest_scale=None, **kw):
    prep = prepare_crop_run(crop, **kw)
    cfg = dict(law=law, use_ces=use_ces, calm_branch=calm_branch, reg_c=reg_c)
    Ht = prep.H if prep.params.twin_harvest == "realized" else prep.H_seas
    tw = simulate(Ht, prep.C_flex_twin, prep.C_ind_twin, np.zeros_like(Ht),
                  prep.stock0.copy(), prep.safety, prep.p0, prep.C_ann,
                  prep.A, prep.S, prep.params, free_twin=None,
                  H_seasonal=prep.H_seas, **cfg)
    H = prep.H if harvest_scale is None else prep.H * harvest_scale
    out = simulate(H, prep.C_flex, prep.C_ind, prep.cuts, prep.stock0.copy(),
                   prep.safety, prep.p0, prep.C_ann, prep.A, prep.S,
                   prep.params, free_twin=tw["free"], unmet_twin=tw["unmet"],
                   H_seasonal=prep.H_seas,
                   free_twin_country=tw["free_country"], **cfg)
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
    rows = []
    win_tau = {"wheat": (2010, 8, 2010, 12, 0.05),
               "rice": (2008, 1, 2008, 6, 0.05),
               "maize": (2007, 5, 2008, 6, 0.0)}
    print("\n== analytic ceiling on the scarcity price, p_scar_max / p0 ==")
    print("   (F -> 0 gives r -> (F_twin + f)/f, a finite cap)")
    for crop in CROPS:
        prep = prepare_crop_run(crop, use_amis=True, use_shocks=True,
                                use_demand=False)
        sw = float(prep.safety.sum())
        Ftw = float(np.mean(prep.free_twin))
        for c in (0.05, 0.02, 0.01, 0.005):
            f = c * sw
            cap = ((Ftw + f) / f) ** prep.params.inv_eta
            print(f"  {crop:6s} c={c:.3f}  f={f:6.2f} MMT "
                  f"({f/max(Ftw,1e-9):6.1%} of mean F_twin={Ftw:6.1f})  "
                  f"p_scar_max/p0 = {cap:9.1f}")

    print("\n== regulariser sweep under the exporter FOC (nothing else moved) ==")
    for crop in CROPS:
        obs = obs_all[(obs_all.year >= 2006) & (obs_all.year <= 2011)][
            ["year", "month", crop]].rename(columns={crop: "obs_price"})
        o07 = _hike(obs, "obs_price", 2006, 6, 2008, 3)
        o10 = _hike(obs, "obs_price", 2009, 6, 2011, 2)
        print(f"  {crop} observed: 2007/08 x{o07:.2f}  2010/11 x{o10:.2f}   "
              f"[shipped ask law: see probe 3]")
        for c in (0.05, 0.02, 0.01, 0.005, 0.002):
            prep, tw, out = build_and_run(
                crop, c, use_amis=True, use_shocks=True, use_demand=False)
            s = score(prep, out, obs)
            # calm rest point, conditional off
            _, _, oc = build_and_run(
                crop, c, calm_branch=False, use_amis=False, use_shocks=False,
                use_demand=False, use_industrial=False)
            drift = float(np.max(np.abs(oc["price"][STEPS_PER_YEAR:] - prep.p0))
                          / prep.p0)
            # A2 restriction lift, unpinned baseline
            pt, _, tau = build_and_run(crop, c, use_amis=True,
                                       use_shocks=False, use_demand=False,
                                       use_industrial=False)
            _, _, base = build_and_run(crop, c, use_amis=False,
                                       use_shocks=False, use_demand=False,
                                       use_industrial=False,
                                       harvest_scale=1 - 1e-6)
            y0, m0, y1, m1, floor = win_tau[crop]
            t0 = (y0 - pt.start_year) * STEPS_PER_YEAR + (m0 - 1) * 2
            t1 = (y1 - pt.start_year) * STEPS_PER_YEAR + (m1 - 1) * 2 + 2
            lift = (float(np.mean(tau["price"][t0:t1]))
                    / max(float(np.mean(base["price"][t0:t1])), 1e-9) - 1.0)
            # A4 exporter offer cut
            country, a0, b0, a1, b1 = _EXPORTER_WINDOWS[crop]
            i = pt.countries.index(country)
            u0 = (a0 - pt.start_year) * STEPS_PER_YEAR + (b0 - 1) * 2
            u1 = (a1 - pt.start_year) * STEPS_PER_YEAR + (b1 - 1) * 2 + 2
            off_r = (float(np.mean(tau["offers"][i, u0:u1]))
                     / max(float(np.mean(base["offers"][i, u0:u1])), 1e-9))
            max_off = 0.20 if crop == "wheat" else 0.70
            print(f"    reg_c={c:.3f}  corr {s['corr']:+.3f}  "
                  f"2007/08 x{s['hike_0708']:.2f}  2010/11 x{s['hike_1011']:.2f}"
                  f"   calm {drift:6.3%}  A2 {lift:+7.2%}"
                  f"{'P' if lift >= floor else 'F'}  "
                  f"A4 x{off_r:.3f}{'P' if off_r <= max_off else 'F'}")
            rows.append(dict(crop=crop, reg_c=c, obs_0708=o07, obs_1011=o10,
                             calm_drift=drift, A2_lift=lift,
                             A2_pass=bool(lift >= floor),
                             A4_offer_ratio=off_r,
                             A4_pass=bool(off_r <= max_off), **s))
    pd.DataFrame(rows).to_csv(OUT / "foc_regulariser_sweep.csv", index=False)
    print(f"\nwrote {OUT/'foc_regulariser_sweep.csv'}")


if __name__ == "__main__":
    main()
