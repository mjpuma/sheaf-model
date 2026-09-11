#!/usr/bin/env python3
"""The offer-price floor is the glut asymmetry.

Established in 03/06: the scarcity ratio r_t is asymmetric in the *opposite*
direction (it moves more on the surplus side), the one-sided unmet truncation
accounts for at most 0.07 of the asymmetry ratio, and removing the capacity
drawdown makes the asymmetry worse. What remains is the offer-price clip in
eq. (10), q in [0.45 p0, 2.8 p0], which is asymmetric in logs
(log 0.45 = -0.80 vs log 2.8 = +1.03) and binds only on the surplus leg.

This script (a) confirms the floor is the binding cause and (b) prototypes and
scores the log-symmetric floor 1/2.8 = 0.357 p0 and a wider 0.20 p0.

Writes clr_askfloor_asym.csv, clr_askfloor_scores.csv.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import redteam_clr_lib as L  # noqa: E402

from sheaf.calendar24 import STEPS_PER_YEAR  # noqa: E402
from sheaf.dynamic_crop import prepare_crop_run  # noqa: E402

OUT = Path(__file__).resolve().parents[2] / "diagnostics/gate0_prep/redteam/clearing"
TAIL = slice(2 * STEPS_PER_YEAR, None)

FLOORS = [("shipped_0.45", 0.45), ("logsym_0.357", 1.0 / 2.8),
          ("wide_0.20", 0.20), ("none_0.01", 0.01)]
SHOCKS = (0.02, 0.05, 0.10, 0.20)


def main() -> None:
    asym, scores = [], []
    for crop in L.CROPS:
        prep = prepare_crop_run(crop, use_amis=False, use_shocks=False,
                                use_demand=False, use_industrial=False)
        for fname, f in FLOORS:
            base = L.simulate_instrumented(prep, harvest=prep.H * (1 - 1e-6),
                                           ask_floor_frac=f)
            lp0 = float(np.mean(np.log(base["price"][TAIL])))
            for s in SHOCKS:
                up = L.simulate_instrumented(prep, harvest=prep.H * (1 + s),
                                             ask_floor_frac=f)
                dn = L.simulate_instrumented(prep, harvest=prep.H * (1 - s),
                                             ask_floor_frac=f)
                lpu = float(np.mean(np.log(up["price"][TAIL])))
                lpd = float(np.mean(np.log(dn["price"][TAIL])))
                aclip = float(np.mean(np.isclose(up["mat"]["ask"], f * prep.p0,
                                                 rtol=1e-9)))
                asym.append(dict(
                    crop=crop, floor=fname, floor_frac=f, s=s,
                    resp_shortfall_pct=100 * (np.exp(lpd - lp0) - 1),
                    resp_surplus_pct=100 * (np.exp(lpu - lp0) - 1),
                    asym_ratio=abs(lpd - lp0) / max(abs(lpu - lp0), 1e-12),
                    frac_exporter_steps_at_floor_surplus=aclip,
                ))
        print(f"  asym {crop}: done")

        # official P1 rescore
        prep_s = prepare_crop_run(crop, use_amis=True, use_shocks=True,
                                  use_demand=False)
        obs07, obs10 = L.OBS_HIKES[crop]
        for fname, f in FLOORS:
            r = L.simulate_instrumented(prep_s, record_trade=False,
                                        ask_floor_frac=f)
            sc = L.score_price(r["price"], crop)
            scores.append(dict(
                crop=crop, floor=fname, floor_frac=f, corr=sc["corr"],
                h0708=sc["h0708"], h1011=sc["h1011"],
                obs_h0708=obs07, obs_h1011=obs10,
                abs_err_sum=abs(sc["h0708"] - obs07) + abs(sc["h1011"] - obs10),
                mean_price=float(r["price"].mean()),
                frac_at_floor=float(np.mean(np.isclose(
                    r["mat"]["ask"], f * prep_s.p0, rtol=1e-9))),
            ))
        # combined best-of: U1 source reweight + log-symmetric floor
        r = L.simulate_instrumented(prep_s, record_trade=False,
                                    ask_floor_frac=1.0 / 2.8,
                                    alloc_mode="source_reweight")
        sc = L.score_price(r["price"], crop)
        scores.append(dict(
            crop=crop, floor="logsym+U1_source", floor_frac=1.0 / 2.8,
            corr=sc["corr"], h0708=sc["h0708"], h1011=sc["h1011"],
            obs_h0708=obs07, obs_h1011=obs10,
            abs_err_sum=abs(sc["h0708"] - obs07) + abs(sc["h1011"] - obs10),
            mean_price=float(r["price"].mean()), frac_at_floor=np.nan))

    adf, sdf = pd.DataFrame(asym), pd.DataFrame(scores)
    adf.to_csv(OUT / "clr_askfloor_asym.csv", index=False)
    sdf.to_csv(OUT / "clr_askfloor_scores.csv", index=False)
    print("\n=== asymmetry vs offer-price floor ===")
    print(adf.to_string(index=False))
    print("\n=== official P1 rescore vs offer-price floor ===")
    print(sdf.to_string(index=False))


if __name__ == "__main__":
    main()
