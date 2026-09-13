#!/usr/bin/env python3
"""R2 step 4: three in-memory demand-side prototypes, scored against the
official Gate 0 metrics and the four robustness assertions.

P1  Consumer budget constraint  (Agrimate Eq. 6c / Suppl. D.35).
    desired_flex = C_flex * p_hat^-eps_c / (1 + A_c (p_hat^(1-eps_c) - 1))
    eps_c is chosen per crop so the *baseline* elasticity equals the existing
    params.elast:  -(eps_c + A_c (1-eps_c)) = elast  =>
    eps_c = (|elast| - A_c) / (1 - A_c).  Only the curvature (the budget wall)
    is new, so this cannot double-count the existing elasticity at p = p0.

P2  Purchaser budget constraint (Agrimate Eq. 8c / Suppl. D.30a, D.31b/c).
    The price-free `rebuild` branch -- 86-99% of SHEAF's market demand -- is
    multiplied by the same normalised CES budget factor with the purchaser's
    own elasticity eps_d (Agrimate default 1/alpha = 1/3) and budget share
    A_d.  g(1) = 1, so the twin identity is untouched by construction.

P3  Source-share offer-price reweight (Agrimate Eq. 8c lower tier / D.30a:
    D_{r<-s} = a_{r,s} (p_off,r / p_->s)^-sigma ...).  SHEAF reweights the
    exporter->destination matrix A by a row-constant, which renormalisation
    cancels exactly; the importer's source mix S is never reweighted. P3
    applies the reweight to S, down columns, where it is not a no-op.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from r2_lib import (BASELINE, CROPS, OUT, assert_report, load_variant,
                    official_scores)

# ---------------------------------------------------------------- anchors
GLOB_ANCHOR = "MAX_LEAN_STEPS = STEPS_PER_YEAR"
GLOB_NEW = ("MAX_LEAN_STEPS = STEPS_PER_YEAR\n"
            "_REC = {}\n_A_C = 0.10\n_EPS_D = 1.0 / 3.0\n_A_D = 0.05\n")

REC_ANCHOR = "        demand = food_need + rebuild"
REC_NEW = """        demand = food_need + rebuild
        for _k, _v in (('avail', avail), ('target', target),
                       ('flex', C_flex[:, t]), ('ind', C_ind[:, t]),
                       ('rebuild', rebuild), ('food_need', food_need),
                       ('demand', demand)):
            _REC.setdefault(_k, []).append(np.asarray(_v).copy())
        _REC.setdefault('p_prev', []).append(float(p))"""

EPS_ANCHOR = "    elast = params.elast"
EPS_NEW = ("    elast = params.elast\n"
           "    _eps_c = max(0.0, (abs(elast) - _A_C) / (1.0 - _A_C))")

P1_ANCHOR = "        desired_flex = np.maximum(C_flex[:, t] * (p / p0) ** elast, 0.0)"
P1_NEW = """        _ph = max(float(p) / p0, 1e-9)
        _gc = (_ph ** (-_eps_c)
               / (1.0 + _A_C * (_ph ** (1.0 - _eps_c) - 1.0)))
        desired_flex = np.maximum(C_flex[:, t] * _gc, 0.0)"""

P2_ANCHOR = """        rebuild = params.rebuild_lambda * np.maximum(
            0.0, target - after_food_stock)"""
P2_NEW = """        _phd = max(float(p) / p0, 1e-9)
        _gd = (_phd ** (-_EPS_D)
               / (1.0 + _A_D * (_phd ** (1.0 - _EPS_D) - 1.0)))
        rebuild = params.rebuild_lambda * np.maximum(
            0.0, target - after_food_stock) * _gd"""

P3_FN_ANCHOR = """    np.divide(A_eff, row, out=A_eff, where=row > 0)
    return A_eff"""
P3_FN_NEW = """    np.divide(A_eff, row, out=A_eff, where=row > 0)
    return A_eff


def _ask_reweight_src(S: np.ndarray, ask: np.ndarray, p0: float,
                      gamma: float = 1.25) -> np.ndarray:
    \"\"\"Agrimate Eq. (8c)/(D.30a) lower tier: reweight the importer's *source*
    mix a_{r,s} by each supplier's own offer price, normalising down columns.\"\"\"
    rel = (float(p0) / np.maximum(ask, 1e-6)) ** gamma
    S_eff = S * rel[:, None]
    col = S_eff.sum(axis=0, keepdims=True)
    np.divide(S_eff, col, out=S_eff, where=col > 0)
    return S_eff"""

P3_CALL_ANCHOR = """        A_eff = _ask_reweight_dest(A, ask, p0, gamma=params.ask_comp_elast)
        shipped, received, ship = _bilateral_clear(
            offers, demand, A_eff, S, subst=params.residual_subst)"""
P3_CALL_NEW = """        A_eff = _ask_reweight_dest(A, ask, p0, gamma=params.ask_comp_elast)
        S_eff = _ask_reweight_src(S, ask, p0, gamma=params.ask_comp_elast)
        shipped, received, ship = _bilateral_clear(
            offers, demand, A_eff, S_eff, subst=params.residual_subst)"""

BASE_SUBS = [(GLOB_ANCHOR, GLOB_NEW), (REC_ANCHOR, REC_NEW),
             (EPS_ANCHOR, EPS_NEW)]

VARIANTS = {
    "baseline": [],
    "P1_consumer_budget": [(P1_ANCHOR, P1_NEW)],
    "P2_purchaser_budget": [(P2_ANCHOR, P2_NEW)],
    "P3_source_reweight": [(P3_FN_ANCHOR, P3_FN_NEW),
                           (P3_CALL_ANCHOR, P3_CALL_NEW)],
    "P1P2": [(P1_ANCHOR, P1_NEW), (P2_ANCHOR, P2_NEW)],
    "P2P3": [(P2_ANCHOR, P2_NEW), (P3_FN_ANCHOR, P3_FN_NEW),
             (P3_CALL_ANCHOR, P3_CALL_NEW)],
}


def eta_effective(mod, crop: str) -> tuple[float, float, float]:
    """Exact finite-difference elasticity of world market demand, plus the
    rebuild share, on the official scored path of this variant."""
    prep = mod.prepare_crop_run(crop, use_amis=True, use_shocks=True,
                                use_demand=False)
    mod._REC.clear()
    mod.simulate_prep(prep)
    R = {k: np.array(v) for k, v in mod._REC.items()}
    avail, target, flex, ind = R["avail"], R["target"], R["flex"], R["ind"]
    p, p0 = R["p_prev"], prep.p0
    lam, el = prep.params.rebuild_lambda, prep.params.elast
    A_C, EPS_D, A_D = mod._A_C, mod._EPS_D, mod._A_D
    eps_c = max(0.0, (abs(el) - A_C) / (1.0 - A_C))
    has_p1 = "P1" in mod.__name__ or "p1" in mod.__name__
    has_p2 = "P2" in mod.__name__ or "p2" in mod.__name__

    def demand_at(pp):
        ph = np.maximum(pp / p0, 1e-9)[:, None]
        if has_p1:
            g = ph ** (-eps_c) / (1.0 + A_C * (ph ** (1.0 - eps_c) - 1.0))
        else:
            g = ph ** el
        des = np.maximum(flex * g, 0.0) + ind
        fn = np.maximum(0.0, des - avail)
        after = np.maximum(0.0, avail - des)
        rb = lam * np.maximum(0.0, target - after)
        if has_p2:
            gd = ph ** (-EPS_D) / (1.0 + A_D * (ph ** (1.0 - EPS_D) - 1.0))
            rb = rb * gd
        return fn + rb

    d0, d1 = demand_at(p), demand_at(p * 1.01)
    chk = float(np.max(np.abs(d0 - R["demand"])))
    s0, s1 = d0.sum(axis=1), d1.sum(axis=1)
    eta = float(np.mean((s1 - s0) / np.maximum(s0, 1e-12) / np.log(1.01)))
    rb_share = float(R["rebuild"].sum() / max(R["demand"].sum(), 1e-12))
    return eta, rb_share, chk


def main() -> None:
    rows, arows = [], []
    for name, subs in VARIANTS.items():
        mod = load_variant(name.lower(), BASE_SUBS + subs)
        for crop in CROPS:
            s = official_scores(mod, crop)
            eta, rb, chk = eta_effective(mod, crop)
            b = BASELINE[crop]
            rows.append(dict(
                variant=name, crop=crop, corr=s["corr"],
                hike0708=s["hike0708"], hike1011=s["hike1011"],
                d_corr=s["corr"] - b[0], d_h07=s["hike0708"] - b[1],
                d_h10=s["hike1011"] - b[2],
                eta_market_demand=eta, rebuild_share=rb,
                recon_err=chk))
            a = assert_report(mod, crop)
            arows.append(dict(variant=name, crop=crop, **a))
            print(f"{name:20s} {crop:6s} corr={s['corr']:+.3f} "
                  f"h07=x{s['hike0708']:.2f} h10=x{s['hike1011']:.2f} "
                  f"eta={eta:+.3f} rb={rb:.2f} | "
                  + " ".join(f"{k}={'P' if v == 'PASS' else 'F'}"
                             for k, v in a.items()))

    pd.DataFrame(rows).to_csv(OUT / "r2_prototype_scores.csv", index=False)
    pd.DataFrame(arows).to_csv(OUT / "r2_prototype_asserts.csv", index=False)

    # A_D sensitivity for the chosen prototype
    mod = load_variant("p2sweep", BASE_SUBS + VARIANTS["P2_purchaser_budget"])
    srows = []
    for a_d in (0.0, 0.05, 0.10, 0.20, 0.40):
        mod._A_D = a_d
        for crop in CROPS:
            s = official_scores(mod, crop)
            eta, rb, _ = eta_effective(mod, crop)
            srows.append(dict(A_D=a_d, crop=crop, corr=s["corr"],
                              hike0708=s["hike0708"], hike1011=s["hike1011"],
                              eta_market_demand=eta))
    sw = pd.DataFrame(srows)
    sw.to_csv(OUT / "r2_P2_A_D_sweep.csv", index=False)
    print("\n== P2 A_D sweep ==")
    print(sw.to_string(index=False))

    # eps_d sensitivity at A_D = 0.05
    mod2 = load_variant("p2eps", BASE_SUBS + VARIANTS["P2_purchaser_budget"])
    erows = []
    for e_d in (0.10, 1.0 / 3.0, 0.60):
        mod2._EPS_D = e_d
        mod2._A_D = 0.05
        for crop in CROPS:
            s = official_scores(mod2, crop)
            eta, _, _ = eta_effective(mod2, crop)
            erows.append(dict(eps_d=e_d, crop=crop, corr=s["corr"],
                              hike0708=s["hike0708"], hike1011=s["hike1011"],
                              eta_market_demand=eta))
    ew = pd.DataFrame(erows)
    ew.to_csv(OUT / "r2_P2_eps_d_sweep.csv", index=False)
    print("\n== P2 eps_d sweep (A_D=0.05) ==")
    print(ew.to_string(index=False))


if __name__ == "__main__":
    main()
