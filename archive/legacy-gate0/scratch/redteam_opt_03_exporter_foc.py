#!/usr/bin/env python3
"""Red team / optimisation, probe 3: an exporter FOC in place of the ask law.

READ-ONLY on sheaf/. This module re-implements ``_simulate_window`` with
switches so the candidate can be scored against the shipped spine without
touching it. The baseline mode is checked bit-for-bit against
``sheaf.dynamic_crop.simulate_prep`` before anything else is reported.

MODES
  ask        shipped offer-price law, eq (13) of dynamics.tex
  foc        offer price = marginal valuation of own accessible stock,
                 q_i,t = mu * p0 * ((F^twin_i,t + f_i)/(F_i,t + f_i))^eta
             This is the country-level analogue of p_scar, which probe 2(a)
             established is exactly U'(F) for a CRRA felicity over
             accessible stock.  mu = 1 is the competitive (price-taking)
             case; mu > 1 is a Lerner markup.
             REMOVES ask_alpha, ask_target_fill, ask_rival, ask_beta.
  ces        fixes the Armington reweight so it acts on SOURCE shares,
                 S~_ij  propto  S_ij (p0/q_i)^gamma  normalised over i,
             which is the CES expenditure-minimising import share of
             importer j over origins i with elasticity of substitution
             gamma.  The shipped code reweights DESTINATION shares by a
             row-constant and renormalises the row, which probe 1 proved
             is the identity map.
  foc+ces    both

CALM BRANCH can be switched off in every mode, which is the test of
whether a quiet market is a genuine rest point.
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
    simulate_prep,
)
from sheaf.dynamic_crop import CropSimResult  # noqa: E402
from sheaf.seasonal import rolling_ahead_variable, steps_to_harvest_pulse  # noqa: E402

OUT = ROOT / "diagnostics" / "gate0_prep" / "redteam" / "optimisation"
OUT.mkdir(parents=True, exist_ok=True)

CROPS = ("wheat", "maize", "rice")


# --------------------------------------------------------------- allocation
def reweight_dest_shipped(A, ask, p0, gamma):
    """Verbatim sheaf/dynamic_crop.py::_ask_reweight_dest (a no-op)."""
    rel = (float(p0) / np.maximum(ask, 1e-6)) ** gamma
    A_eff = A * rel[:, None]
    row = A_eff.sum(axis=1, keepdims=True)
    np.divide(A_eff, row, out=A_eff, where=row > 0)
    return A_eff


def reweight_source_ces(S, ask, p0, gamma):
    """CES import shares over origins: S~_ij propto S_ij (p0/q_i)^gamma.

    Column j of the result is importer j's expenditure-minimising share
    vector over origins for a CES aggregator with elasticity of
    substitution ``gamma`` and preference weights S[:, j].
    """
    rel = (float(p0) / np.maximum(ask, 1e-6)) ** gamma
    S_eff = S * rel[:, None]
    col = S_eff.sum(axis=0, keepdims=True)
    np.divide(S_eff, col, out=S_eff, where=col > 0)
    # keep importers with no preferred sources at zero, as the shipped S does
    S_eff *= (S.sum(axis=0, keepdims=True) > 0)
    return S_eff


# ---------------------------------------------------------------- the window
def simulate(
        H, C_flex, C_ind, cuts, stock0, safety, p0, C_ann, A, S, params,
        free_twin=None, unmet_twin=None, H_seasonal=None,
        free_twin_country=None,
        mode="ask", calm_branch=True, foc_mu=1.0,
):
    """Gate 0 two-week map with switchable offer-price law and allocation."""
    use_foc = "foc" in mode
    use_ces = "ces" in mode

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
    p = float(p0)
    ask = np.full(n, float(p0))
    safety_w = float(max(safety.sum(), 1.0))
    carry_cap = params.max_stu * C_ann
    food_step = C_ann / STEPS_PER_YEAR

    H_exp = H if H_seasonal is None else (
        params.foresight_phi * H + (1.0 - params.foresight_phi) * H_seasonal)

    lean_h = steps_to_harvest_pulse(
        H_exp, frac=params.harvest_pulse_frac, max_horizon=MAX_LEAN_STEPS)
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
        rebuild = params.rebuild_lambda * np.maximum(
            0.0, target - after_food_stock)
        demand = food_need + rebuild
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
        excess = np.maximum(0.0, stock - warehouse)
        stock = stock - params.warehouse_lambda * excess

        total_d = float(demand.sum())
        preferred_block = float((S * cuts[:, t][:, None] * demand[None, :]).sum())
        block_frac = preferred_block / max(total_d, 1e-9)

        # ---- country-level accessible stock (the FOC's state) ----
        F_i = stock - lean_gap
        free_country[:, t] = F_i

        # ---- offer price ----
        if use_foc:
            Ft_i = (free_twin_country[:, t] if free_twin_country is not None
                    else F_i)
            reg = 0.05 * safety + np.maximum(0.0, -np.minimum(F_i, Ft_i))
            ratio_i = (Ft_i + reg) / np.maximum(F_i + reg, 1e-12)
            ask = foc_mu * p0 * np.maximum(ratio_i, 1e-12) ** inv_eta
        else:
            fill = shipped / np.maximum(offers, 1e-9)
            fill = np.where(offers > 1e-9, fill, params.ask_target_fill)
            rival = float(max(params.ask_rival, 0.0)) * block_frac
            ask = ask * np.exp(
                params.ask_alpha * (fill - params.ask_target_fill)
                + np.where(offers > 1e-9, rival, 0.0))
            ask = (1.0 - params.ask_beta) * ask + params.ask_beta * p
        ask = np.clip(ask, 0.45 * p0, 2.8 * p0)

        lean_need = float(lean_gap.sum())
        locked = float((cuts[:, t] * np.maximum(0.0, stock - target)).sum())
        free = float(stock.sum()) - lean_need - locked
        free_path[t] = free

        unmet = max(0.0, total_d - float(received.sum()))
        unmet_frac = unmet / max(total_d, 1e-9)
        unmet_path[t] = unmet_frac

        shipped_sum = float(shipped.sum())
        p_trade = (float(np.dot(ask, shipped) / shipped_sum)
                   if shipped_sum > 1e-12 else p)

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
            if calm and calm_branch:
                p_star = p0
            else:
                ratio = float(max(ratio, 1e-12))
                p_scar = (p0 * ratio ** inv_eta
                          * (1.0 + params.unmet_kappa * u_anom
                             + params.block_kappa * block_frac))
                p_star = trade_w * p_trade + (1.0 - trade_w) * p_scar

        p = float(np.clip(smooth * p + (1.0 - smooth) * p_star, 60.0, 1200.0))
        price[t] = p
        stock_path[:, t] = stock
        cons_path[:, t] = consumption
        exp_path[:, t] = shipped

    return dict(price=price, stock=stock_path, consumption=cons_path,
                exports=exp_path, free=free_path, free_country=free_country,
                unmet=unmet_path, offers=offer_path, demand=demand_path,
                ask=ask_path, received=recv_path, trade=trade_path)


# ------------------------------------------------------------------ harness
def build(crop, mode="ask", calm_branch=True, foc_mu=1.0, **kw):
    """prep + a mode-consistent twin (world and per-country accessible stock)."""
    prep = prepare_crop_run(crop, **kw)
    H_for_twin = prep.H if prep.params.twin_harvest == "realized" else prep.H_seas
    tw = simulate(
        H_for_twin, prep.C_flex_twin, prep.C_ind_twin,
        np.zeros_like(H_for_twin), prep.stock0.copy(), prep.safety, prep.p0,
        prep.C_ann, prep.A, prep.S, prep.params, free_twin=None,
        H_seasonal=prep.H_seas, mode=mode, calm_branch=calm_branch,
        foc_mu=foc_mu)
    return prep, tw


def run(prep, tw, mode="ask", calm_branch=True, foc_mu=1.0,
        cuts=None, harvest=None):
    H = prep.H if harvest is None else harvest
    c = prep.cuts if cuts is None else cuts
    return simulate(
        H, prep.C_flex, prep.C_ind, c, prep.stock0.copy(), prep.safety,
        prep.p0, prep.C_ann, prep.A, prep.S, prep.params,
        free_twin=tw["free"], unmet_twin=tw["unmet"], H_seasonal=prep.H_seas,
        free_twin_country=tw["free_country"], mode=mode,
        calm_branch=calm_branch, foc_mu=foc_mu)


def as_result(prep, out, H=None, cuts=None):
    return CropSimResult(
        crop=prep.crop, countries=prep.countries, start_year=prep.start_year,
        end_year=prep.end_year, price=out["price"], stock=out["stock"],
        harvest=prep.H if H is None else H, consumption=out["consumption"],
        exports=out["exports"],
        export_cut=prep.cuts if cuts is None else cuts,
        spin_up_years=prep.spin_up_years, free_liquid=out["free"],
        free_twin=prep.free_twin, unmet_frac=out["unmet"],
        offers=out["offers"], purchase_demand=out["demand"], ask=out["ask"],
        received=out["received"], trade=out["trade"], params=prep.params)


def _hike(df, col, y0, m0, y1, m1):
    def win(y, m):
        v = []
        for dm in (-1, 0, 1):
            mm, yy = m + dm, y
            if mm < 1:
                mm, yy = mm + 12, yy - 1
            if mm > 12:
                mm, yy = mm - 12, yy + 1
            hit = df[(df.year == yy) & (df.month == mm)][col]
            if len(hit):
                v.append(float(hit.iloc[0]))
        return float(np.mean(v)) if v else float("nan")
    b, pk = win(y0, m0), win(y1, m1)
    return pk / b if b and np.isfinite(b) and np.isfinite(pk) else float("nan")


def score_leg(prep, out, obs):
    m = result_to_monthly(as_result(prep, out)).merge(
        obs, on=["year", "month"], how="left")
    a = m.model_price.to_numpy(float)
    b = m.obs_price.to_numpy(float)
    k = np.isfinite(a) & np.isfinite(b)
    corr = float(np.corrcoef(a[k], b[k])[0, 1]) if k.sum() > 5 else float("nan")
    return dict(corr=corr,
                hike_0708=_hike(m, "model_price", 2006, 6, 2008, 3),
                hike_1011=_hike(m, "model_price", 2009, 6, 2011, 2))


# ------------------------------------------------------------------- checks
def check_baseline_fidelity():
    """Mode 'ask' must reproduce the shipped spine bit-for-bit."""
    print("\n== fidelity: mode='ask' vs sheaf.dynamic_crop ==")
    ok = True
    for crop in CROPS:
        prep, tw = build(crop, mode="ask", use_amis=True, use_shocks=True,
                         use_demand=False)
        mine = run(prep, tw, mode="ask")
        theirs = simulate_prep(prep)
        d = max(float(np.max(np.abs(mine["price"] - theirs.price))),
                float(np.max(np.abs(mine["exports"] - theirs.exports))),
                float(np.max(np.abs(mine["ask"] - theirs.ask))))
        print(f"  {crop:6s} max|delta| vs shipped = {d:.3e}   "
              f"twin free max|delta| = "
              f"{float(np.max(np.abs(tw['free'] - prep.free_twin))):.3e}")
        ok &= d == 0.0
    print(f"  fidelity exact: {ok}")
    return ok


def calm_rest_point(rows):
    """Is a quiet market a fixed point WITHOUT the calm conditional?"""
    print("\n== calm rest point, conditional OFF ==")
    for crop in CROPS:
        for mode in ("ask", "ces", "foc", "foc+ces"):
            for cb in (True, False):
                prep, tw = build(crop, mode=mode, calm_branch=cb,
                                 use_amis=False, use_shocks=False,
                                 use_demand=False, use_industrial=False)
                out = run(prep, tw, mode=mode, calm_branch=cb)
                p = out["price"]
                p0 = float(prep.p0)
                tail = p[STEPS_PER_YEAR:]
                drift = float(np.max(np.abs(tail - p0)) / max(p0, 1.0))
                if not cb:
                    print(f"  {crop:6s} {mode:8s} calm_branch=off  "
                          f"drift = {drift:8.3%}  "
                          f"{'PASS' if drift <= 0.02 else 'FAIL'} (tol 2%)")
                rows.append(dict(crop=crop, mode=mode, calm_branch=cb,
                                 drift=drift, p0=p0,
                                 passes_2pct=drift <= 0.02))


def robustness(rows):
    """The four assertions in dynamic_crop.py L900-1013, per mode."""
    print("\n== robustness assertions per mode ==")
    win_tau = {"wheat": (2010, 8, 2010, 12, 0.05),
               "rice": (2008, 1, 2008, 6, 0.05),
               "maize": (2007, 5, 2008, 6, 0.0)}
    for crop in CROPS:
        for mode in ("ask", "ces", "foc", "foc+ces"):
            kw = dict(use_shocks=False, use_demand=False, use_industrial=False)
            # --- A2: AMIS raises price (unpinned baseline) ---
            prep_t, tw_t = build(crop, mode=mode, use_amis=True, **kw)
            tau = run(prep_t, tw_t, mode=mode)
            prep_b, tw_b = build(crop, mode=mode, use_amis=False, **kw)
            base = run(prep_b, tw_b, mode=mode, harvest=prep_b.H * (1 - 1e-6))
            y0, m0, y1, m1, floor = win_tau[crop]
            t0 = (y0 - prep_t.start_year) * STEPS_PER_YEAR + (m0 - 1) * 2
            t1 = (y1 - prep_t.start_year) * STEPS_PER_YEAR + (m1 - 1) * 2 + 2
            lift = (float(np.mean(tau["price"][t0:t1]))
                    / max(float(np.mean(base["price"][t0:t1])), 1e-9) - 1.0)
            # --- A1: twin identity (conditional ON, as shipped) ---
            prep_c, tw_c = build(crop, mode=mode, use_amis=False, **kw)
            calm = run(prep_c, tw_c, mode=mode)
            tail = calm["price"][STEPS_PER_YEAR:]
            drift = float(np.max(np.abs(tail - prep_c.p0)) / prep_c.p0)
            free_err = float(np.max(np.abs(calm["free"] - tw_c["free"])))
            # --- A3: no spring spike ---
            m = result_to_monthly(as_result(prep_c, calm))
            spring = float(m[m.month.isin([3, 4])].model_price.mean())
            autumn = float(m[m.month.isin([9, 10])].model_price.mean())
            # --- A4: AMIS cuts exporter offers/shipments ---
            country, a0, b0, a1, b1 = _EXPORTER_WINDOWS[crop]
            i = prep_t.countries.index(country)
            u0 = (a0 - prep_t.start_year) * STEPS_PER_YEAR + (b0 - 1) * 2
            u1 = (a1 - prep_t.start_year) * STEPS_PER_YEAR + (b1 - 1) * 2 + 2
            prep_n, tw_n = build(crop, mode=mode, use_amis=False, **kw)
            nb = run(prep_n, tw_n, mode=mode)
            off_r = (float(np.mean(tau["offers"][i, u0:u1]))
                     / max(float(np.mean(nb["offers"][i, u0:u1])), 1e-9))
            shp_r = (float(np.mean(tau["exports"][i, u0:u1]))
                     / max(float(np.mean(nb["exports"][i, u0:u1])), 1e-9))
            max_off = 0.20 if crop == "wheat" else 0.70
            rows.append(dict(
                crop=crop, mode=mode,
                A1_twin_drift=drift, A1_free_err=free_err,
                A1_pass=bool(drift <= 0.02 and free_err <= 1.0),
                A2_amis_lift=lift, A2_floor=floor, A2_pass=bool(lift >= floor),
                A3_spring_autumn=spring / max(autumn, 1e-9),
                A3_pass=bool(spring / max(autumn, 1e-9) <= 1.25),
                A4_country=country, A4_offer_ratio=off_r,
                A4_ship_ratio=shp_r, A4_max_offer=max_off,
                A4_pass=bool(off_r <= max_off)))
            r = rows[-1]
            print(f"  {crop:6s} {mode:8s} "
                  f"A1 drift {drift:7.3%} {'P' if r['A1_pass'] else 'F'} | "
                  f"A2 lift {lift:+8.2%} (>={floor:.0%}) "
                  f"{'P' if r['A2_pass'] else 'F'} | "
                  f"A3 {r['A3_spring_autumn']:.3f} "
                  f"{'P' if r['A3_pass'] else 'F'} | "
                  f"A4 {country} offer x{off_r:.3f} "
                  f"{'P' if r['A4_pass'] else 'F'}")


def scores(rows):
    print("\n== official matched scores per mode (corr, crisis hikes) ==")
    obs_all = load_price_series_monthly(deflated=True)
    for crop in CROPS:
        obs = obs_all[(obs_all.year >= 2006) & (obs_all.year <= 2011)][
            ["year", "month", crop]].rename(columns={crop: "obs_price"})
        o07 = _hike(obs, "obs_price", 2006, 6, 2008, 3)
        o10 = _hike(obs, "obs_price", 2009, 6, 2011, 2)
        print(f"  {crop} observed: 2007/08 x{o07:.2f}  2010/11 x{o10:.2f}")
        for mode in ("ask", "ces", "foc", "foc+ces"):
            for mu in ((1.0,) if "foc" not in mode else (1.0, 1.1, 1.25)):
                prep, tw = build(crop, mode=mode, foc_mu=mu, use_amis=True,
                                 use_shocks=True, use_demand=False)
                out = run(prep, tw, mode=mode, foc_mu=mu)
                s = score_leg(prep, out, obs)
                # rival-markup ablation only meaningful in ask mode
                print(f"    {mode:8s} mu={mu:.2f}  corr {s['corr']:+.3f}  "
                      f"2007/08 x{s['hike_0708']:.2f}  "
                      f"2010/11 x{s['hike_1011']:.2f}")
                rows.append(dict(crop=crop, mode=mode, foc_mu=mu,
                                 obs_hike_0708=o07, obs_hike_1011=o10, **s))


def ask_rival_needed(rows):
    """Does foc mode still produce the maize sign without ask_rival?"""
    print("\n== is ask_rival still load-bearing under the FOC? ==")
    obs_all = load_price_series_monthly(deflated=True)
    for crop in CROPS:
        obs = obs_all[(obs_all.year >= 2006) & (obs_all.year <= 2011)][
            ["year", "month", crop]].rename(columns={crop: "obs_price"})
        for mode in ("ask", "foc+ces"):
            for ar in (0.0, 0.80):
                prep, tw = build(crop, mode=mode, use_amis=True,
                                 use_shocks=True, use_demand=False,
                                 ask_rival=ar)
                out = run(prep, tw, mode=mode)
                s = score_leg(prep, out, obs)
                print(f"    {crop:6s} {mode:8s} ask_rival={ar:.2f}  "
                      f"corr {s['corr']:+.3f}  "
                      f"2007/08 x{s['hike_0708']:.2f}  "
                      f"2010/11 x{s['hike_1011']:.2f}")
                rows.append(dict(crop=crop, mode=mode, ask_rival=ar, **s))


def main():
    if not check_baseline_fidelity():
        print("!! prototype does not reproduce the shipped spine; stopping")
        return
    r_calm, r_rob, r_sc, r_ar = [], [], [], []
    calm_rest_point(r_calm)
    robustness(r_rob)
    scores(r_sc)
    ask_rival_needed(r_ar)
    pd.DataFrame(r_calm).to_csv(OUT / "foc_calm_rest_point.csv", index=False)
    pd.DataFrame(r_rob).to_csv(OUT / "foc_robustness.csv", index=False)
    pd.DataFrame(r_sc).to_csv(OUT / "foc_scores.csv", index=False)
    pd.DataFrame(r_ar).to_csv(OUT / "foc_ask_rival.csv", index=False)
    print(f"\nwrote 4 CSVs to {OUT}")


if __name__ == "__main__":
    main()
