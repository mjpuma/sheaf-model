#!/usr/bin/env python3
"""Red team / optimisation, probe 4: why does the exporter FOC lose amplitude?

Probe 3 found the own-stock FOC
    q_i,t = mu p0 ((F^twin_i + f_i)/(F_i + f_i))^eta
makes a quiet market an exact rest point and passes all four robustness
assertions, but collapses the 2007/08 hike (wheat x1.24 vs x2.27 shipped,
observed x1.82) and the correlation.

Hypothesis H1 (composition bias).  p^tr is SHIPMENT-weighted.  Under the
FOC a tight exporter has a high q and, being tight, ships little, so it
receives little weight.  p^tr is therefore biased toward abundant, cheap
exporters exactly when the world is tight, muting the crisis.  The shipped
ask law does not suffer this as badly because its asks are sticky and
nearly homogeneous across exporters.

Hypothesis H2 (wrong argument).  Agrimate's offer price (their Eq. 3, 5)
is isoelastic inverse demand evaluated at the exporter's own expected
supply PLUS ALL COMPETITORS' expected supplies -- a common world-scarcity
signal, differentiated only through the exporter's own quantity choice.
The own-stock FOC uses the wrong state variable: own stock instead of the
world pool.

Tests
  D1  dispersion of q across exporters, share pinned at the [0.45,2.8]p0
      bounds, and corr(p^tr, p^scar), per mode.
  D2  a family q_i = p0 * r_world^(eta(1-psi)) * r_own_i^(eta psi).
      psi = 1 is probe 3's FOC; psi = 0 is the Agrimate-style common
      world-scarcity offer price (which makes p^tr == p^scar and omega
      irrelevant).  One parameter psi replaces four.
  D3  offer-weighted rather than shipment-weighted p^tr, to isolate H1.
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
    MAX_LEAN_STEPS,
    _bilateral_clear,
    _EXPORTER_WINDOWS,
    prepare_crop_run,
    result_to_monthly,
)
from sheaf.seasonal import rolling_ahead_variable, steps_to_harvest_pulse  # noqa: E402

sys.path.insert(0, str(ROOT / "scripts" / "scratch"))
from redteam_opt_03_exporter_foc import (  # noqa: E402
    _hike,
    as_result,
    reweight_dest_shipped,
    reweight_source_ces,
)

OUT = ROOT / "diagnostics" / "gate0_prep" / "redteam" / "optimisation"
OUT.mkdir(parents=True, exist_ok=True)
CROPS = ("wheat", "maize", "rice")


def simulate(H, C_flex, C_ind, cuts, stock0, safety, p0, C_ann, A, S, params,
             free_twin=None, unmet_twin=None, H_seasonal=None,
             free_twin_country=None, law="ask", psi=1.0, mu=1.0,
             use_ces=False, calm_branch=True, ptr_weight="ship"):
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
    ptr_path = np.zeros(T)
    pscar_path = np.zeros(T)
    at_bound = np.zeros(T)
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
        lean_need = float(lean_gap.sum())
        locked = float((cuts[:, t] * np.maximum(0.0, stock - target)).sum())
        free = float(stock.sum()) - lean_need - locked
        free_path[t] = free

        if law == "ask":
            fill = shipped / np.maximum(offers, 1e-9)
            fill = np.where(offers > 1e-9, fill, params.ask_target_fill)
            rival = float(max(params.ask_rival, 0.0)) * block_frac
            ask = ask * np.exp(
                params.ask_alpha * (fill - params.ask_target_fill)
                + np.where(offers > 1e-9, rival, 0.0))
            ask = (1.0 - params.ask_beta) * ask + params.ask_beta * p
        else:
            Ft_i = (free_twin_country[:, t] if free_twin_country is not None
                    else F_i)
            reg_i = 0.05 * safety + np.maximum(0.0, -np.minimum(F_i, Ft_i))
            r_own = (Ft_i + reg_i) / np.maximum(F_i + reg_i, 1e-12)
            if free_twin is None:
                r_w = 1.0
            else:
                tw = float(free_twin[t])
                sh = 0.05 * safety_w + max(0.0, -min(free, tw))
                r_w = max((tw + sh) / (free + sh), 1e-12)
            ask = (mu * p0
                   * r_w ** (inv_eta * (1.0 - psi))
                   * np.maximum(r_own, 1e-12) ** (inv_eta * psi))
        raw = ask.copy()
        ask = np.clip(ask, 0.45 * p0, 2.8 * p0)
        act = offers > 1e-9
        at_bound[t] = (float(np.mean(np.abs(raw[act] - ask[act]) > 1e-12))
                       if act.any() else np.nan)

        unmet = max(0.0, total_d - float(received.sum()))
        u_frac = unmet / max(total_d, 1e-9)
        unmet_path[t] = u_frac

        w = shipped if ptr_weight == "ship" else offers
        p_trade = float(np.dot(ask, w) / w.sum()) if w.sum() > 1e-12 else p
        ptr_path[t] = p_trade

        if free_twin is None:
            p_star = p0
            pscar_path[t] = p0
        else:
            tw = float(free_twin[t])
            sh = 0.05 * safety_w + max(0.0, -min(free, tw))
            ratio = max((tw + sh) / (free + sh), 1e-12)
            u0 = float(unmet_twin[t]) if unmet_twin is not None else 0.0
            u_an = max(0.0, u_frac - u0)
            p_scar = (p0 * ratio ** inv_eta
                      * (1.0 + params.unmet_kappa * u_an
                         + params.block_kappa * block_frac))
            pscar_path[t] = p_scar
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
                p_trade=ptr_path, p_scar=pscar_path, at_bound=at_bound)


def build(crop, **cfg):
    kw = {k: cfg.pop(k) for k in list(cfg)
          if k in ("use_amis", "use_shocks", "use_demand", "use_industrial",
                   "ask_rival")}
    prep = prepare_crop_run(crop, **kw)
    Ht = prep.H if prep.params.twin_harvest == "realized" else prep.H_seas
    tw = simulate(Ht, prep.C_flex_twin, prep.C_ind_twin, np.zeros_like(Ht),
                  prep.stock0.copy(), prep.safety, prep.p0, prep.C_ann,
                  prep.A, prep.S, prep.params, free_twin=None,
                  H_seasonal=prep.H_seas, **cfg)
    return prep, tw, cfg


def go(prep, tw, cfg, harvest=None, cuts=None):
    return simulate(
        prep.H if harvest is None else harvest, prep.C_flex, prep.C_ind,
        prep.cuts if cuts is None else cuts, prep.stock0.copy(), prep.safety,
        prep.p0, prep.C_ann, prep.A, prep.S, prep.params,
        free_twin=tw["free"], unmet_twin=tw["unmet"], H_seasonal=prep.H_seas,
        free_twin_country=tw["free_country"], **cfg)


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
    d1, d2 = [], []

    print("\n== D1: offer-price dispersion, bound pinning, p_tr vs p_scar ==")
    for crop in CROPS:
        for tag, cfg in (("ask", dict(law="ask")),
                         ("foc psi=1", dict(law="foc", psi=1.0)),
                         ("foc psi=0", dict(law="foc", psi=0.0))):
            prep, tw, cfg2 = build(crop, use_amis=True, use_shocks=True,
                                   use_demand=False, **cfg)
            o = go(prep, tw, cfg2)
            act = o["offers"] > 1e-9
            q = o["ask"] / prep.p0
            disp = float(np.nanmean([np.std(q[act[:, t], t])
                                     for t in range(q.shape[1])
                                     if act[:, t].sum() > 1]))
            corr_ts = float(np.corrcoef(o["p_trade"], o["p_scar"])[0, 1])
            rel = float(np.mean(o["p_trade"] / np.maximum(o["p_scar"], 1e-9)))
            print(f"  {crop:6s} {tag:9s} cross-exporter sd(q/p0)={disp:.3f}  "
                  f"mean q/p0={float(np.mean(q[act])):.3f}  "
                  f"share at bound={float(np.nanmean(o['at_bound'])):.2%}  "
                  f"corr(p_tr,p_scar)={corr_ts:+.3f}  "
                  f"mean p_tr/p_scar={rel:.3f}")
            d1.append(dict(crop=crop, law=tag, sd_q=disp,
                           mean_q=float(np.mean(q[act])),
                           share_at_bound=float(np.nanmean(o["at_bound"])),
                           corr_ptr_pscar=corr_ts, mean_ptr_over_pscar=rel))

    print("\n== D2/D3: psi family, omega, and p_tr weighting ==")
    for crop in CROPS:
        obs = obs_all[(obs_all.year >= 2006) & (obs_all.year <= 2011)][
            ["year", "month", crop]].rename(columns={crop: "obs_price"})
        o07 = _hike(obs, "obs_price", 2006, 6, 2008, 3)
        o10 = _hike(obs, "obs_price", 2009, 6, 2011, 2)
        print(f"  {crop} observed: corr 1.000  2007/08 x{o07:.2f}  "
              f"2010/11 x{o10:.2f}")
        cases = [("ask  ship", dict(law="ask"), False, "ship")]
        for psi in (0.0, 0.25, 0.5, 0.75, 1.0):
            cases.append((f"foc psi={psi:.2f} ship",
                          dict(law="foc", psi=psi), True, "ship"))
        for psi in (0.5, 1.0):
            cases.append((f"foc psi={psi:.2f} offr",
                          dict(law="foc", psi=psi), True, "offer"))
        for tag, cfg, ces, w in cases:
            prep, tw, cfg2 = build(crop, use_amis=True, use_shocks=True,
                                   use_demand=False, use_ces=ces,
                                   ptr_weight=w, **cfg)
            out = go(prep, tw, cfg2)
            s = score(prep, out, obs)
            # calm rest point with the conditional off
            pc, tc, cc = build(crop, use_amis=False, use_shocks=False,
                               use_demand=False, use_industrial=False,
                               use_ces=ces, ptr_weight=w, calm_branch=False,
                               **cfg)
            oc = go(pc, tc, cc)
            drift = float(np.max(np.abs(oc["price"][STEPS_PER_YEAR:] - pc.p0))
                          / pc.p0)
            print(f"    {tag:20s} corr {s['corr']:+.3f}  "
                  f"2007/08 x{s['hike_0708']:.2f}  2010/11 x{s['hike_1011']:.2f}"
                  f"   calm drift {drift:7.3%}")
            d2.append(dict(crop=crop, case=tag, obs_0708=o07, obs_1011=o10,
                           calm_drift_no_branch=drift, **s))

    pd.DataFrame(d1).to_csv(OUT / "foc_dispersion.csv", index=False)
    pd.DataFrame(d2).to_csv(OUT / "foc_psi_family.csv", index=False)
    print(f"\nwrote {OUT/'foc_dispersion.csv'}\nwrote {OUT/'foc_psi_family.csv'}")


if __name__ == "__main__":
    main()
