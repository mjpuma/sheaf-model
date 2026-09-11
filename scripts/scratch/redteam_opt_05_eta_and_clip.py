#!/usr/bin/env python3
"""Red team / optimisation, probe 5: is eta calibratable, and is rice clipped?

Probe 4 found (i) p^tr and p^scar are near-uncorrelated in the shipped
model and p^tr carries omega = 0.70-0.80 of the weight; (ii) rice has
51% of active exporter-steps pinned at an offer-price bound; (iii) under
the exporter FOC the whole world price collapses onto the inverse-demand
schedule and the 2007/08 amplitude drops to x1.2-1.3.

Three questions follow.

E1  ETA IS THE ONLY STRUCTURAL AMPLITUDE PARAMETER LEFT UNDER THE FOC, and
    it is currently classified reduced_form (inv_eta = 0.85-1.00, implied
    demand elasticity over accessible stock -1.0 to -1.18). Is it
    estimable from data? Regress log real price on log stock-to-use,
    annually, from USDA PSD + deflated World Bank Pink Sheet:
        log p_y = a - eta * log(S_y / C_y) + b * y
    world and ex-China, several windows. d log p / d log STU = -eta.

E2  RICE CLIP DEPENDENCE. Sweep the offer-price upper bound (shipped
    2.8 p0) under the shipped ask law and record the 2007/08 hike. If the
    hike moves with the bound, the bound is a calibration parameter.

E3  CAN A CALIBRATED ETA CARRY THE AMPLITUDE UNDER THE FOC? Sweep inv_eta
    in the FOC mode and see whether the observed hikes are reachable with
    an eta inside the empirical confidence range from E1, while keeping
    the calm rest point and the four assertions.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

from sheaf.calendar24 import STEPS_PER_YEAR  # noqa: E402
from sheaf.data_usda import load_price_series_monthly, load_psd_country  # noqa: E402
from sheaf.dynamic_crop import _EXPORTER_WINDOWS  # noqa: E402

sys.path.insert(0, str(ROOT / "scripts" / "scratch"))
from redteam_opt_03_exporter_foc import _hike  # noqa: E402
from redteam_opt_04_foc_diagnosis import build, go, score  # noqa: E402

OUT = ROOT / "diagnostics" / "gate0_prep" / "redteam" / "optimisation"
OUT.mkdir(parents=True, exist_ok=True)
CROPS = ("wheat", "maize", "rice")
_EXCL = {"wheat": ("China",), "maize": ("China",), "rice": ("China", "India")}


def _ols(y, X):
    """OLS with HAC(3) standard errors (Newey-West), returns beta, se."""
    X = np.column_stack([np.ones(len(y)), X])
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    e = y - X @ b
    n, k = X.shape
    XtX_inv = np.linalg.pinv(X.T @ X)
    S = (e[:, None] * X).T @ (e[:, None] * X)
    L = 3
    for l in range(1, L + 1):
        w = 1.0 - l / (L + 1)
        G = (e[l:, None] * X[l:]).T @ (e[:-l, None] * X[:-l])
        S += w * (G + G.T)
    V = XtX_inv @ S @ XtX_inv * n / max(n - k, 1)
    return b, np.sqrt(np.maximum(np.diag(V), 0.0))


def e1_estimate_eta(rows):
    print("\n== E1: empirical eta = -d log(real price) / d log(stock-to-use) ==")
    px = load_price_series_monthly(deflated=True)
    for crop in CROPS:
        psd = load_psd_country(crop)
        pa = (px.groupby("year")[crop].mean().dropna())
        for label, excl in (("world", ()), ("ex-" + "+".join(_EXCL[crop]),
                                            _EXCL[crop])):
            g = psd.copy()
            if excl:
                g = g[~g["country"].isin(excl)]
            ann = g.groupby("year")[["ending_stocks", "consumption"]].sum()
            ann = ann[(ann.consumption > 0) & (ann.ending_stocks > 0)]
            for w0, w1 in ((1980, 2015), (1990, 2011), (2000, 2015)):
                s = ann[(ann.index >= w0) & (ann.index <= w1)]
                yrs = [y for y in s.index if y in pa.index]
                if len(yrs) < 12:
                    continue
                stu = (s.loc[yrs, "ending_stocks"]
                       / s.loc[yrs, "consumption"]).to_numpy(float)
                p = pa.loc[yrs].to_numpy(float)
                yv = np.log(p)
                Xv = np.column_stack([np.log(stu),
                                      np.asarray(yrs, float) - np.mean(yrs)])
                b, se = _ols(yv, Xv)
                eta, eta_se = -b[1], se[1]
                print(f"  {crop:6s} {label:14s} {w0}-{w1} n={len(yrs):3d}  "
                      f"eta = {eta:6.2f} +/- {eta_se:.2f}   "
                      f"95% CI [{eta - 1.96*eta_se:6.2f}, "
                      f"{eta + 1.96*eta_se:6.2f}]   "
                      f"implied demand elast {-1/eta if eta>0 else np.nan:+.3f}")
                rows.append(dict(crop=crop, aggregate=label, y0=w0, y1=w1,
                                 n=len(yrs), eta=eta, eta_se=eta_se,
                                 ci_lo=eta - 1.96 * eta_se,
                                 ci_hi=eta + 1.96 * eta_se,
                                 shipped_inv_eta={"wheat": 1.00, "maize": 0.85,
                                                  "rice": 0.95}[crop]))


def e2_clip(rows):
    """Sweep the offer-price ceiling under the shipped ask law."""
    print("\n== E2: is the crisis amplitude set by the offer-price ceiling? ==")
    import sheaf.dynamic_crop as dc
    import redteam_opt_04_foc_diagnosis as m4
    src = m4.simulate
    obs_all = load_price_series_monthly(deflated=True)
    for crop in CROPS:
        obs = obs_all[(obs_all.year >= 2006) & (obs_all.year <= 2011)][
            ["year", "month", crop]].rename(columns={crop: "obs_price"})
        for cap in (1.6, 2.0, 2.8, 4.0, 10.0):
            # monkeypatch the clip inside the scratch copy only
            code = src.__code__
            m4.simulate = _with_cap(src, cap)
            prep, tw, cfg = m4.build(crop, use_amis=True, use_shocks=True,
                                     use_demand=False, law="ask")
            out = m4.go(prep, tw, cfg)
            s = m4.score(prep, out, obs)
            q = out["ask"] / prep.p0
            act = out["offers"] > 1e-9
            print(f"  {crop:6s} ceiling={cap:5.2f} p0   corr {s['corr']:+.3f}  "
                  f"2007/08 x{s['hike_0708']:.2f}  2010/11 x{s['hike_1011']:.2f}"
                  f"   mean q/p0 {float(np.mean(q[act])):.2f}  "
                  f"share at ceiling "
                  f"{float(np.mean(q[act] >= cap - 1e-9)):.1%}")
            rows.append(dict(crop=crop, ceiling=cap, **s,
                             mean_q_over_p0=float(np.mean(q[act])),
                             share_at_ceiling=float(
                                 np.mean(q[act] >= cap - 1e-9))))
            m4.simulate = src


def _with_cap(fn, cap):
    """Wrap simulate so the offer-price ceiling is `cap` * p0."""
    import redteam_opt_04_foc_diagnosis as m4
    orig_clip = np.clip

    def wrapper(*a, **k):
        p0 = a[6] if len(a) > 6 else k["p0"]

        def clip(x, lo, hi, *aa, **kk):
            if (isinstance(hi, float) and abs(hi - 2.8 * p0) < 1e-9):
                hi = cap * p0
            return orig_clip(x, lo, hi, *aa, **kk)
        m4.np.clip = clip
        try:
            return fn(*a, **k)
        finally:
            m4.np.clip = orig_clip
    return wrapper


def e3_eta_sweep(rows):
    print("\n== E3: can a calibrated eta carry the amplitude under the FOC? ==")
    import redteam_opt_04_foc_diagnosis as m4
    obs_all = load_price_series_monthly(deflated=True)
    win_tau = {"wheat": (2010, 8, 2010, 12, 0.05),
               "rice": (2008, 1, 2008, 6, 0.05),
               "maize": (2007, 5, 2008, 6, 0.0)}
    for crop in CROPS:
        obs = obs_all[(obs_all.year >= 2006) & (obs_all.year <= 2011)][
            ["year", "month", crop]].rename(columns={crop: "obs_price"})
        o07 = _hike(obs, "obs_price", 2006, 6, 2008, 3)
        o10 = _hike(obs, "obs_price", 2009, 6, 2011, 2)
        print(f"  {crop} observed: 2007/08 x{o07:.2f}  2010/11 x{o10:.2f}")
        for eta in (0.85, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0):
            cfg_kw = dict(law="foc", psi=1.0, use_ces=True)
            prep, tw, cfg = m4.build(crop, use_amis=True, use_shocks=True,
                                     use_demand=False, **cfg_kw)
            prep.params.__dict__  # frozen dataclass; rebuild via replace
            from dataclasses import replace
            prep2 = prep
            object.__setattr__(prep2, "params",
                               replace(prep.params, inv_eta=eta))
            # twin must use the same eta
            prep3, tw3, cfg3 = m4.build(crop, use_amis=True, use_shocks=True,
                                        use_demand=False, **cfg_kw)
            object.__setattr__(prep3, "params",
                               replace(prep3.params, inv_eta=eta))
            Ht = (prep3.H if prep3.params.twin_harvest == "realized"
                  else prep3.H_seas)
            tw3 = m4.simulate(Ht, prep3.C_flex_twin, prep3.C_ind_twin,
                              np.zeros_like(Ht), prep3.stock0.copy(),
                              prep3.safety, prep3.p0, prep3.C_ann, prep3.A,
                              prep3.S, prep3.params, free_twin=None,
                              H_seasonal=prep3.H_seas, **cfg3)
            out = m4.go(prep3, tw3, cfg3)
            s = m4.score(prep3, out, obs)
            # calm rest point, conditional off
            pc, tc, cc = m4.build(crop, use_amis=False, use_shocks=False,
                                  use_demand=False, use_industrial=False,
                                  calm_branch=False, **cfg_kw)
            object.__setattr__(pc, "params", replace(pc.params, inv_eta=eta))
            Htc = pc.H if pc.params.twin_harvest == "realized" else pc.H_seas
            tc = m4.simulate(Htc, pc.C_flex_twin, pc.C_ind_twin,
                             np.zeros_like(Htc), pc.stock0.copy(), pc.safety,
                             pc.p0, pc.C_ann, pc.A, pc.S, pc.params,
                             free_twin=None, H_seasonal=pc.H_seas, **cc)
            oc = m4.go(pc, tc, cc)
            drift = float(np.max(np.abs(oc["price"][STEPS_PER_YEAR:] - pc.p0))
                          / pc.p0)
            # A2: restriction raises price, unpinned baseline
            pt, tt, ct = m4.build(crop, use_amis=True, use_shocks=False,
                                  use_demand=False, use_industrial=False,
                                  **cfg_kw)
            object.__setattr__(pt, "params", replace(pt.params, inv_eta=eta))
            Htt = pt.H if pt.params.twin_harvest == "realized" else pt.H_seas
            tt = m4.simulate(Htt, pt.C_flex_twin, pt.C_ind_twin,
                             np.zeros_like(Htt), pt.stock0.copy(), pt.safety,
                             pt.p0, pt.C_ann, pt.A, pt.S, pt.params,
                             free_twin=None, H_seasonal=pt.H_seas, **ct)
            tau = m4.go(pt, tt, ct)
            pb, tb, cb = m4.build(crop, use_amis=False, use_shocks=False,
                                  use_demand=False, use_industrial=False,
                                  **cfg_kw)
            object.__setattr__(pb, "params", replace(pb.params, inv_eta=eta))
            Htb = pb.H if pb.params.twin_harvest == "realized" else pb.H_seas
            tb = m4.simulate(Htb, pb.C_flex_twin, pb.C_ind_twin,
                             np.zeros_like(Htb), pb.stock0.copy(), pb.safety,
                             pb.p0, pb.C_ann, pb.A, pb.S, pb.params,
                             free_twin=None, H_seasonal=pb.H_seas, **cb)
            base = m4.go(pb, tb, cb, harvest=pb.H * (1 - 1e-6))
            y0, m0, y1, m1, floor = win_tau[crop]
            t0 = (y0 - pt.start_year) * STEPS_PER_YEAR + (m0 - 1) * 2
            t1 = (y1 - pt.start_year) * STEPS_PER_YEAR + (m1 - 1) * 2 + 2
            lift = (float(np.mean(tau["price"][t0:t1]))
                    / max(float(np.mean(base["price"][t0:t1])), 1e-9) - 1.0)
            print(f"    eta={eta:4.2f}  corr {s['corr']:+.3f}  "
                  f"2007/08 x{s['hike_0708']:.2f}  2010/11 x{s['hike_1011']:.2f}"
                  f"   calm drift {drift:6.3%}  A2 lift {lift:+7.2%} "
                  f"{'P' if lift >= floor else 'F'}")
            rows.append(dict(crop=crop, eta=eta, obs_0708=o07, obs_1011=o10,
                             calm_drift=drift, A2_lift=lift, A2_floor=floor,
                             A2_pass=bool(lift >= floor), **s))


def main():
    r1, r2, r3 = [], [], []
    e1_estimate_eta(r1)
    e2_clip(r2)
    e3_eta_sweep(r3)
    pd.DataFrame(r1).to_csv(OUT / "eta_empirical.csv", index=False)
    pd.DataFrame(r2).to_csv(OUT / "ask_clip_sensitivity.csv", index=False)
    pd.DataFrame(r3).to_csv(OUT / "foc_eta_sweep.csv", index=False)
    print(f"\nwrote 3 CSVs to {OUT}")


if __name__ == "__main__":
    main()
