#!/usr/bin/env python3
"""Task 4 — prototype and score the ranked upgrades.

U1  repair the ask-competition channel: reweight the *source* shares S_ij
    (column-normalised) instead of the destination shares A_ij
    (row-normalised, which cancels the multiplier identically).
U2  two-sided unmet-demand channel (already scored in 03; repeated here with
    the Russia-2010 rerouting mechanism check).
U3  excess-demand (tatonnement) term, three definitions of excess demand.

Also: honest cost of a per-step clearing solve, measured on the parked
annual spatial-equilibrium QP in sheaf/annual/.

Writes clr_upgrade_scores.csv, clr_u1_mechanism.csv, clr_solver_cost.csv.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import redteam_clr_lib as L  # noqa: E402

from sheaf.calendar24 import STEPS_PER_YEAR  # noqa: E402
from sheaf.dynamic_crop import prepare_crop_run  # noqa: E402

OUT = Path(__file__).resolve().parents[2] / "diagnostics/gate0_prep/redteam/clearing"
OUT.mkdir(parents=True, exist_ok=True)

CASES = [
    ("U0_shipped", dict()),
    ("U1_source_reweight_g1.25", dict(alloc_mode="source_reweight")),
    ("U1_source_reweight_g0.5", dict(alloc_mode="source_reweight", alloc_gamma=0.5)),
    ("U1_source_reweight_g3.0", dict(alloc_mode="source_reweight", alloc_gamma=3.0)),
    ("U2_unmet_twosided", dict(unmet_mode="twosided")),
    ("U1+U2", dict(alloc_mode="source_reweight", unmet_mode="twosided")),
    ("U3_tat_traded_k0.05", dict(tat_kappa=0.05, tat_mode="traded")),
    ("U3_tat_imbalance_k0.05", dict(tat_kappa=0.05, tat_mode="imbalance")),
    ("U3_tat_imbalance_k0.15", dict(tat_kappa=0.15, tat_mode="imbalance")),
    ("U3_tat_imbalance_k0.40", dict(tat_kappa=0.40, tat_mode="imbalance")),
]

# Agrimate's own mechanism check (their Figs. 6-7): after Russia's Aug 2010
# ban, Egypt's source mix should shift away from Russia.
MECH = dict(wheat=("Russia", "Egypt", 2010, 8, 2011, 6))


def main() -> None:
    rows, mech = [], []
    for crop in L.CROPS:
        prep = prepare_crop_run(crop, use_amis=True, use_shocks=True,
                                use_demand=False)
        obs07, obs10 = L.OBS_HIKES[crop]
        for name, var in CASES:
            t0 = time.perf_counter()
            r = L.simulate_instrumented(prep, **var)
            dt = time.perf_counter() - t0
            sc = L.score_price(r["price"], crop)
            rows.append(dict(
                crop=crop, variant=name, corr=sc["corr"],
                h0708=sc["h0708"], h1011=sc["h1011"],
                obs_h0708=obs07, obs_h1011=obs10,
                abs_err_sum=abs(sc["h0708"] - obs07) + abs(sc["h1011"] - obs10),
                mean_price=float(r["price"].mean()),
                residual_share=float(r["world_ship2"].sum()
                                     / max(r["world_ship"].sum(), 1e-12)),
                mean_rationing_pct=100 * float(np.mean(
                    r["rationing"] / np.maximum(r["world_desired"], 1e-12))),
                runtime_s=dt,
            ))
            if crop in MECH:
                exp_, imp_, y0, m0, y1, m1 = MECH[crop]
                i = prep.countries.index(exp_)
                j = prep.countries.index(imp_)
                t0s = (y0 - prep.start_year) * STEPS_PER_YEAR + (m0 - 1) * 2
                t1s = (y1 - prep.start_year) * STEPS_PER_YEAR + (m1 - 1) * 2 + 2
                X = r["trade"]
                pre = slice(0, t0s)
                ban = slice(t0s, t1s)
                def share(sl):
                    tot = X[:, j, sl].sum()
                    return float(X[i, j, sl].sum() / max(tot, 1e-12))
                mech.append(dict(crop=crop, variant=name,
                                 exporter=exp_, importer=imp_,
                                 share_pre_ban=share(pre),
                                 share_during_ban=share(ban),
                                 delta=share(ban) - share(pre)))
        print(f"  {crop}: done")

    df = pd.DataFrame(rows)
    df.to_csv(OUT / "clr_upgrade_scores.csv", index=False)
    print("\n=== upgrade scores, official P1 leg ===")
    print(df[["crop", "variant", "corr", "h0708", "obs_h0708", "h1011",
              "obs_h1011", "abs_err_sum", "residual_share",
              "mean_rationing_pct"]].to_string(index=False))
    md = pd.DataFrame(mech)
    md.to_csv(OUT / "clr_u1_mechanism.csv", index=False)
    print("\n=== Agrimate Fig. 6-7 mechanism check: Russia share of Egypt "
          "receipts, pre-ban vs Aug2010-Jun2011 ===")
    print(md.to_string(index=False))

    # ------------- solver cost: the parked annual SPE QP -------------
    srows = []
    try:
        from sheaf.annual import SheafModel, build_countries
        c1, transport, grains, fm = build_countries(substitution=True)
        n, G = len(c1), len(grains)
        t0 = time.perf_counter()
        mdl = SheafModel(c1, transport, grains, freight_mult=fm, play_game=False)
        t_build = time.perf_counter() - t0
        t0 = time.perf_counter()
        mdl.run(1)
        t1 = time.perf_counter() - t0
        srows.append(dict(object="annual QP, 1 period, game OFF",
                          n_nodes=n, n_grains=G, build_s=t_build,
                          per_period_s=t1,
                          implied_144_steps_s=144 * t1,
                          implied_3crops_x_5legs_s=3 * 5 * 144 * t1,
                          note="one cvxpy solve per period"))
        c2, transport2, grains2, fm2 = build_countries(substitution=True)
        mdl2 = SheafModel(c2, transport2, grains2, freight_mult=fm2,
                          play_game=True, game_grid=13, game_iters=3)
        t0 = time.perf_counter()
        mdl2.run(1)
        t2 = time.perf_counter() - t0
        srows.append(dict(object="annual QP + year-IBR game, 1 period",
                          n_nodes=n, n_grains=G, build_s=np.nan,
                          per_period_s=t2, implied_144_steps_s=144 * t2,
                          implied_3crops_x_5legs_s=3 * 5 * 144 * t2,
                          note="Gate 2 analogue cost"))
    except Exception as exc:
        srows.append(dict(object="annual run failed", n_nodes=-1, n_grains=-1,
                          build_s=np.nan, per_period_s=np.nan,
                          implied_144_steps_s=np.nan,
                          implied_3crops_x_5legs_s=np.nan, note=repr(exc)[:300]))
    # shipped Gate 0 cost for comparison
    prep = prepare_crop_run("wheat", use_amis=True, use_shocks=True,
                            use_demand=False)
    t0 = time.perf_counter()
    for _ in range(5):
        L.simulate_instrumented(prep, record_trade=False)
    t_g0 = (time.perf_counter() - t0) / 5
    srows.append(dict(object="Gate 0 shipped map, 144 steps",
                      n_nodes=len(prep.countries), n_grains=1,
                      build_s=np.nan, per_period_s=t_g0 / 144,
                      implied_144_steps_s=t_g0,
                      implied_3crops_x_5legs_s=3 * 5 * t_g0,
                      note="no inner solve"))
    sdf = pd.DataFrame(srows)
    sdf.to_csv(OUT / "clr_solver_cost.csv", index=False)
    print("\n=== solver cost reference ===")
    print(sdf.to_string(index=False))


if __name__ == "__main__":
    main()
