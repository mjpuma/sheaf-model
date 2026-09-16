#!/usr/bin/env python3
"""R2 step 3b: the effective price elasticity of SHEAF's *market* demand.

`params.elast` is the elasticity of desired consumption, not of the demand
that reaches the market. Market demand is
    demand = max(0, desired - avail) + lambda * max(0, target - (avail-desired))
so for a country that is not food-short the price response is damped by
`rebuild_lambda` (0.08). This script measures the true aggregate elasticity by
exact finite difference on the recorded state: recompute the demand block at
1.01 * p holding stock, target and availability fixed.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from r2_lib import CROPS, OUT, load_variant

REC_ANCHOR = "MAX_LEAN_STEPS = STEPS_PER_YEAR"
REC_NEW = "MAX_LEAN_STEPS = STEPS_PER_YEAR\n_REC = {}"
DEM_ANCHOR = "        demand = food_need + rebuild"
DEM_NEW = """        demand = food_need + rebuild
        for _k, _v in (('avail', avail), ('target', target),
                       ('flex', C_flex[:, t]), ('ind', C_ind[:, t]),
                       ('demand', demand)):
            _REC.setdefault(_k, []).append(np.asarray(_v).copy())
        _REC.setdefault('p_prev', []).append(float(p))"""


def main() -> None:
    mod = load_variant("r2eff", [(REC_ANCHOR, REC_NEW), (DEM_ANCHOR, DEM_NEW)])
    rows = []
    for crop in CROPS:
        prep = mod.prepare_crop_run(crop, use_amis=True, use_shocks=True,
                                    use_demand=False)
        mod._REC.clear()
        res = mod.simulate_prep(prep)
        R = {k: np.array(v) for k, v in mod._REC.items()}
        avail, target = R["avail"], R["target"]
        flex, ind, dem0 = R["flex"], R["ind"], R["demand"]
        p = R["p_prev"]
        p0, lam, el = prep.p0, prep.params.rebuild_lambda, prep.params.elast

        def demand_at(pp):
            des = np.maximum(flex * (pp[:, None] / p0) ** el, 0.0) + ind
            fn = np.maximum(0.0, des - avail)
            after = np.maximum(0.0, avail - des)
            rb = lam * np.maximum(0.0, target - after)
            return fn + rb

        d0, d1 = demand_at(p), demand_at(p * 1.01)
        s0, s1 = d0.sum(axis=1), d1.sum(axis=1)      # world per step
        eta = (s1 - s0) / np.maximum(s0, 1e-12) / np.log(1.01)
        # consumption-side elasticity for comparison
        c0 = (np.maximum(flex * (p[:, None] / p0) ** el, 0.0) + ind).sum(axis=1)
        c1 = (np.maximum(flex * (p[:, None] * 1.01 / p0) ** el, 0.0)
              + ind).sum(axis=1)
        eta_c = (c1 - c0) / np.maximum(c0, 1e-12) / np.log(1.01)

        t0, t1 = 24 + 10, 48 + 12
        rows.append(dict(
            crop=crop, params_elast=el, rebuild_lambda=lam,
            eta_market_demand_mean=float(np.mean(eta)),
            eta_market_demand_crisis=float(np.mean(eta[t0:t1])),
            eta_consumption_mean=float(np.mean(eta_c)),
            damping_factor=float(np.mean(eta) / el),
            check_dem0_match=float(np.max(np.abs(d0 - dem0))),
        ))
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "r2_effective_elasticity.csv", index=False)
    print(df.to_string(index=False))
    print("\nAgrimate purchaser (Eq. D.30a, eps_d=1/3, A*_d small): "
          "eta ~= -(eps_d + A_d(1-eps_d)) ~= -0.35")
    print("Agrimate consumer  (Eq. D.35, eps_c=0.1, A*_c=0.1):       "
          f"eta ~= {-(0.1 + 0.1 * 0.9):.3f}")


if __name__ == "__main__":
    main()
