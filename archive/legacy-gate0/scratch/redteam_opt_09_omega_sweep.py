#!/usr/bin/env python3
"""Red team / optimisation, probe 9: can the structural channel carry more weight?

Probe 7 showed p^tr carries 63-118% of the realised move in p*, and probe 8
showed that replacing the argument of eq (17) with a SUPPLY FLOW (Agrimate
Eq. 3 analogue) raises both the price correlation and corr(p, p^scar) on all
three crops at zero parameter cost.

The decisive question for the Potsdam objection is whether the weight omega
on the non-structural offer-price average can be REDUCED -- i.e. whether the
inverse-demand channel can carry more of the world price -- without losing
score. This probe sweeps omega for each scarcity argument.

omega = 0 is the pure inverse-demand world price: p* = p^scar, no offer-price
average at all. That is the strongest available answer to "do we need an
optimisation principle", because it makes the world price the marginal
valuation of the marginal unit and nothing else.
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
from sheaf.dynamic_crop import _EXPORTER_WINDOWS, prepare_crop_run  # noqa: E402

sys.path.insert(0, str(ROOT / "scripts" / "scratch"))
from redteam_opt_03_exporter_foc import _hike  # noqa: E402
import redteam_opt_08_flow_scarcity as m8  # noqa: E402

OUT = ROOT / "diagnostics" / "gate0_prep" / "redteam" / "optimisation"
CROPS = ("wheat", "maize", "rice")
WIN = {"wheat": (2010, 8, 2010, 12, 0.05),
       "rice": (2008, 1, 2008, 6, 0.05),
       "maize": (2007, 5, 2008, 6, 0.0)}


def _patched(crop, omega, **kw):
    """prepare_crop_run then override trade_w on the frozen params."""
    prep = prepare_crop_run(crop, **kw)
    object.__setattr__(prep, "params", replace(prep.params, trade_w=omega))
    return prep


def run_case(crop, omega, law, scar, use_ces, **kw):
    """Replicates m8.build_run with omega overridden everywhere."""
    prep = _patched(crop, omega, **{k: v for k, v in kw.items()
                                    if k not in ("harvest_scale",
                                                 "calm_branch")})
    cfg = dict(law=law, scar=scar, use_ces=use_ces,
               calm_branch=kw.get("calm_branch", True))
    Ht = prep.H if prep.params.twin_harvest == "realized" else prep.H_seas
    tw = m8.simulate(Ht, prep.C_flex_twin, prep.C_ind_twin,
                     np.zeros_like(Ht), prep.stock0.copy(), prep.safety,
                     prep.p0, prep.C_ann, prep.A, prep.S, prep.params,
                     free_twin=None, twin_flow=None, H_seasonal=prep.H_seas,
                     **cfg)
    o_tw = tw["offers"].sum(axis=0)
    tf = dict(offers=o_tw, offers_scale=max(float(o_tw.mean()), 1e-9),
              avail=tw["avail"], avail_scale=max(float(tw["avail"].mean()), 1e-9))
    hs = kw.get("harvest_scale")
    H = prep.H if hs is None else prep.H * hs
    out = m8.simulate(H, prep.C_flex, prep.C_ind, prep.cuts,
                      prep.stock0.copy(), prep.safety, prep.p0, prep.C_ann,
                      prep.A, prep.S, prep.params, free_twin=tw["free"],
                      unmet_twin=tw["unmet"], H_seasonal=prep.H_seas,
                      free_twin_country=tw["free_country"], twin_flow=tf,
                      **cfg)
    return prep, tw, out


def main():
    obs_all = load_price_series_monthly(deflated=True)
    rows = []
    for crop in CROPS:
        obs = obs_all[(obs_all.year >= 2006) & (obs_all.year <= 2011)][
            ["year", "month", crop]].rename(columns={crop: "obs_price"})
        o07 = _hike(obs, "obs_price", 2006, 6, 2008, 3)
        o10 = _hike(obs, "obs_price", 2009, 6, 2011, 2)
        shipped_w = prepare_crop_run(crop, use_amis=False, use_shocks=False,
                                     use_demand=False).params.trade_w
        print(f"\n=== {crop}: observed 2007/08 x{o07:.2f}  2010/11 x{o10:.2f}"
              f"   (shipped omega = {shipped_w:.2f}) ===")
        for law, scar, ces in (("ask", "stock", False),
                               ("ask", "offers", False),
                               ("ask", "avail", False),
                               ("foc", "offers", True),
                               ("foc", "avail", True)):
            print(f"  -- law={law} scar={scar} --")
            for omega in (0.0, 0.2, 0.4, 0.6, shipped_w, 1.0):
                base_kw = dict(use_shocks=False, use_demand=False,
                               use_industrial=False)
                prep, tw, out = run_case(crop, omega, law, scar, ces,
                                         use_amis=True, use_shocks=True,
                                         use_demand=False)
                s = m8.score(prep, out, obs)
                c_ps = float(np.corrcoef(out["price"], out["p_scar"])[0, 1])
                _, _, oc = run_case(crop, omega, law, scar, ces,
                                    use_amis=False, calm_branch=False,
                                    **base_kw)
                drift = float(np.max(np.abs(oc["price"][STEPS_PER_YEAR:]
                                            - prep.p0)) / prep.p0)
                pt, _, tau = run_case(crop, omega, law, scar, ces,
                                      use_amis=True, **base_kw)
                _, _, bs = run_case(crop, omega, law, scar, ces,
                                    use_amis=False, harvest_scale=1 - 1e-6,
                                    **base_kw)
                wy0, wm0, wy1, wm1, floor = WIN[crop]
                t0 = (wy0 - pt.start_year) * STEPS_PER_YEAR + (wm0 - 1) * 2
                t1 = (wy1 - pt.start_year) * STEPS_PER_YEAR + (wm1 - 1) * 2 + 2
                lift = (float(np.mean(tau["price"][t0:t1]))
                        / max(float(np.mean(bs["price"][t0:t1])), 1e-9) - 1)
                country, a0, b0, a1, b1 = _EXPORTER_WINDOWS[crop]
                i = pt.countries.index(country)
                u0 = (a0 - pt.start_year) * STEPS_PER_YEAR + (b0 - 1) * 2
                u1 = (a1 - pt.start_year) * STEPS_PER_YEAR + (b1 - 1) * 2 + 2
                off_r = (float(np.mean(tau["offers"][i, u0:u1]))
                         / max(float(np.mean(bs["offers"][i, u0:u1])), 1e-9))
                max_off = 0.20 if crop == "wheat" else 0.70
                tag = " <- shipped" if abs(omega - shipped_w) < 1e-9 else ""
                print(f"     omega={omega:.2f}  corr {s['corr']:+.3f}  "
                      f"2007/08 x{s['hike_0708']:.2f}  "
                      f"2010/11 x{s['hike_1011']:.2f}  "
                      f"corr(p,p^scar) {c_ps:+.3f}  calm {drift:6.2%}  "
                      f"A2 {lift:+7.2%}{'P' if lift >= floor else 'F'}  "
                      f"A4 x{off_r:.2f}{'P' if off_r <= max_off else 'F'}{tag}")
                rows.append(dict(crop=crop, law=law, scar=scar, omega=omega,
                                 shipped_omega=shipped_w, obs_0708=o07,
                                 obs_1011=o10, corr_p_pscar=c_ps,
                                 calm_drift=drift, A2_lift=lift,
                                 A2_pass=bool(lift >= floor),
                                 A4_offer_ratio=off_r,
                                 A4_pass=bool(off_r <= max_off), **s))
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "omega_sweep.csv", index=False)
    print(f"\nwrote {OUT/'omega_sweep.csv'}")

    print("\n== best configuration per crop by |corr| with all 3 asserts passing ==")
    for crop in CROPS:
        sub = df[(df.crop == crop) & df.A2_pass & df.A4_pass]
        sub = sub.sort_values("corr", ascending=False).head(4)
        for _, r in sub.iterrows():
            print(f"  {crop:6s} law={r.law:4s} scar={r.scar:7s} "
                  f"omega={r.omega:.2f}  corr {r.corr:+.3f}  "
                  f"2007/08 x{r.hike_0708:.2f} (obs x{r.obs_0708:.2f})  "
                  f"2010/11 x{r.hike_1011:.2f} (obs x{r.obs_1011:.2f})  "
                  f"calm {r.calm_drift:.2%}")


if __name__ == "__main__":
    main()
