#!/usr/bin/env python3
"""R2 step 3: decompose SHEAF's purchase demand into the price-responsive
part and the price-inelastic part.

SHEAF (dynamic_crop.py:606-610):
    food_need = max(0, desired - avail)        <- inherits (p/p0)**elast
    rebuild   = rebuild_lambda * max(0, target - after_food_stock)
    demand    = food_need + rebuild

`rebuild` contains no price term at all. Agrimate's purchaser restock
(Suppl. Eq. D.31a/b) converts the physical restock Delta D into a budget-share
increment p_->s * Delta D / B_d,s and clips the share to [0,1] (Eq. D.31c), so
Agrimate's restocking demand IS budget-limited. This script measures how much
of SHEAF's crisis-peak import demand sits in the price-free branch.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from r2_lib import CROPS, OUT, load_variant

REC_ANCHOR = "MAX_LEAN_STEPS = STEPS_PER_YEAR"
REC_NEW = "MAX_LEAN_STEPS = STEPS_PER_YEAR\n_REC = {}"
DEM_ANCHOR = "        demand = food_need + rebuild"
DEM_NEW = """        demand = food_need + rebuild
        _REC.setdefault('food_need', []).append(food_need.copy())
        _REC.setdefault('rebuild', []).append(rebuild.copy())
        _REC.setdefault('desired', []).append(desired.copy())
        _REC.setdefault('p_prev', []).append(float(p))"""


def main() -> None:
    mod = load_variant("r2dec", [(REC_ANCHOR, REC_NEW), (DEM_ANCHOR, DEM_NEW)])
    rows = []
    for crop in CROPS:
        prep = mod.prepare_crop_run(crop, use_amis=True, use_shocks=True,
                                    use_demand=False)
        mod._REC.clear()
        res = mod.simulate_prep(prep)
        fn = np.array(mod._REC["food_need"]).T
        rb = np.array(mod._REC["rebuild"]).T
        p = np.array(mod._REC["p_prev"])
        ph = p / prep.p0
        tot = fn + rb

        # crisis window 2007-06 .. 2008-06
        t0, t1 = 24 + 10, 48 + 12
        for lab, sl in (("full_window", slice(None)),
                        ("crisis_0708", slice(t0, t1)),
                        ("calm_2009", slice(3 * 24, 4 * 24))):
            f, r = fn[:, sl].sum(), rb[:, sl].sum()
            rows.append(dict(
                crop=crop, window=lab,
                food_need_mmt=float(f), rebuild_mmt=float(r),
                rebuild_share=float(r / max(f + r, 1e-12)),
                mean_p_hat=float(ph[sl].mean()),
            ))
        # at the simulated peak step
        t_peak = int(np.argmax(res.price[:72]))
        rows.append(dict(
            crop=crop, window=f"peak_step_{t_peak}",
            food_need_mmt=float(fn[:, t_peak].sum()),
            rebuild_mmt=float(rb[:, t_peak].sum()),
            rebuild_share=float(rb[:, t_peak].sum()
                                / max(tot[:, t_peak].sum(), 1e-12)),
            mean_p_hat=float(ph[t_peak]),
        ))
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "r2_demand_decomposition.csv", index=False)
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
