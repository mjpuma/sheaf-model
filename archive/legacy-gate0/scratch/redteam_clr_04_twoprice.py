#!/usr/bin/env python3
"""Task 3/4 — the two-price structure, the inertness of the ask-competition
channel, the Gate 2 revenue seam, and the cost of a real clearing solve.

(a) clr_supply_demand.csv  offered export supply vs import demand: is either
    side ever the marginal one?
(b) clr_gamma_inert.csv     ablation of gamma (ask_comp_elast) on the trade
    matrix and on official-P1 scores -- does relative offer price actually
    allocate anything?
(c) clr_gate2_revenue.csv   dispersion of q_i across exporters and the error
    Gate 2's welfare makes by valuing exports at p_t rather than q_i.
(d) clr_price_variance.csv  variance decomposition of p* between the offer
    channel (omega p_trade) and the scarcity channel ((1-omega) p_scar).
(e) clr_solver_cost.csv     wall-clock cost of the parked annual spatial-
    equilibrium QP, as the reference for what a per-step solve would cost.
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
from sheaf.dynamic_crop import _ask_reweight_dest, prepare_crop_run  # noqa: E402

OUT = Path(__file__).resolve().parents[2] / "diagnostics/gate0_prep/redteam/clearing"
OUT.mkdir(parents=True, exist_ok=True)


def main() -> None:
    sd, gi, g2, pv = [], [], [], []
    for crop in L.CROPS:
        prep = prepare_crop_run(crop, use_amis=True, use_shocks=True,
                                use_demand=False)
        r = L.simulate_instrumented(prep)
        m = r["mat"]
        n, T = m["stock"].shape

        # (a) offered supply vs import demand
        sd.append(dict(
            crop=crop,
            mean_offers_MMT=float(r["world_offers"].mean()),
            mean_import_demand_MMT=float(r["world_demand"].mean()),
            offers_over_demand=float(r["world_offers"].mean()
                                     / r["world_demand"].mean()),
            min_offers_over_demand=float(np.min(
                r["world_offers"] / np.maximum(r["world_demand"], 1e-12))),
            steps_offers_below_demand=int(np.sum(
                r["world_offers"] < r["world_demand"])),
            mean_trade_MMT=float(r["world_ship"].mean()),
            trade_over_offers=float(r["world_ship"].mean()
                                    / r["world_offers"].mean()),
            trade_over_demand=float(r["world_ship"].mean()
                                    / r["world_demand"].mean()),
            mean_rationing_pct_of_desired=100 * float(np.mean(
                r["rationing"] / np.maximum(r["world_desired"], 1e-12))),
            max_rationing_pct_of_desired=100 * float(np.max(
                r["rationing"] / np.maximum(r["world_desired"], 1e-12))),
        ))

        # (b) gamma ablation: does relative offer price allocate?
        base_trade = r["trade"].copy()
        for gam in (0.0, 0.25, 1.25, 3.0, 8.0):
            rg = L.simulate_instrumented(prep, record_trade=True)  # placeholder
            # rebuild with gamma override via params replace
            from dataclasses import replace
            prep_g = prepare_crop_run(crop, use_amis=True, use_shocks=True,
                                      use_demand=False, ask_comp_elast=gam)
            rg = L.simulate_instrumented(prep_g)
            sc = L.score_price(rg["price"], crop)
            # allocation distance on the *same* offers/asks: recompute stage-1
            # shipments at gamma vs at the shipped 1.25 using the baseline state
            d_link = np.zeros(T)
            for t in range(T):
                Ag = _ask_reweight_dest(prep.A, m["ask"][:, t], prep.p0, gamma=gam)
                A0 = _ask_reweight_dest(prep.A, m["ask"][:, t], prep.p0, gamma=1.25)
                c_g = L.clear_instrumented(m["offers"][:, t], m["demand"][:, t],
                                           Ag, prep.S,
                                           subst=prep.params.residual_subst)
                c_0 = L.clear_instrumented(m["offers"][:, t], m["demand"][:, t],
                                           A0, prep.S,
                                           subst=prep.params.residual_subst)
                tot = max(float(c_0["ship"].sum()), 1e-12)
                d_link[t] = 0.5 * float(np.abs(c_g["ship"] - c_0["ship"]).sum()) / tot
            gi.append(dict(
                crop=crop, gamma=gam, corr=sc["corr"],
                h0708=sc["h0708"], h1011=sc["h1011"],
                mean_price=float(rg["price"].mean()),
                partner_reallocation_frac_mean=float(d_link.mean()),
                partner_reallocation_frac_max=float(d_link.max()),
                full_run_trade_L1_over_volume=float(
                    0.5 * np.abs(rg["trade"] - base_trade).sum()
                    / base_trade.sum()),
            ))

        # (c) Gate 2 revenue seam: q_i vs p_t
        q, x = m["ask"], m["shipped"]
        rev_p = (r["price"][None, :] * x).sum(axis=1)
        rev_q = (q * x).sum(axis=1)
        shipping = x.sum(axis=1) > 1e-6
        for i, c in enumerate(prep.countries):
            if not shipping[i]:
                continue
            g2.append(dict(
                crop=crop, country=c,
                exports_MMT=float(x[i].sum()),
                revenue_at_world_p=float(rev_p[i]),
                revenue_at_own_q=float(rev_q[i]),
                rel_err=float(rev_p[i] / max(rev_q[i], 1e-12) - 1.0),
                mean_q_over_p=float(np.mean(
                    (q[i] / r["price"])[x[i] > 1e-9]) if (x[i] > 1e-9).any()
                    else np.nan),
            ))
        # cross-exporter dispersion of q, volume-weighted, per step
        wq = np.zeros(T)
        for t in range(T):
            w = x[:, t]
            if w.sum() < 1e-9:
                continue
            mu = np.dot(q[:, t], w) / w.sum()
            wq[t] = np.sqrt(np.dot(w, (q[:, t] - mu) ** 2) / w.sum()) / mu
        g2.append(dict(crop=crop, country="__WORLD_q_dispersion__",
                       exports_MMT=float(x.sum()),
                       revenue_at_world_p=float(rev_p.sum()),
                       revenue_at_own_q=float(rev_q.sum()),
                       rel_err=float(rev_p.sum() / rev_q.sum() - 1.0),
                       mean_q_over_p=float(np.mean(wq[wq > 0]))))

        # (d) variance decomposition of p*
        ok = np.isfinite(r["p_scar"]) & (r["calm"] < 0.5)
        w_ = prep.params.trade_w
        a = w_ * r["p_trade"][ok]
        b = (1 - w_) * r["p_scar"][ok]
        pv.append(dict(
            crop=crop, omega=w_, steps_priced_by_law=int(ok.sum()), T=T,
            var_offer_channel=float(np.var(a)),
            var_scarcity_channel=float(np.var(b)),
            cov=float(np.cov(a, b)[0, 1]),
            offer_share_of_var=float(
                (np.var(a) + np.cov(a, b)[0, 1]) / np.var(a + b)),
            corr_pstar_ptrade=float(np.corrcoef(r["p_star"][ok],
                                                r["p_trade"][ok])[0, 1]),
            corr_pstar_pscar=float(np.corrcoef(r["p_star"][ok],
                                               r["p_scar"][ok])[0, 1]),
            mean_p_trade=float(r["p_trade"][ok].mean()),
            mean_p_scar=float(r["p_scar"][ok].mean()),
        ))
        print(f"  {crop}: done")

    for name, rows in (("clr_supply_demand", sd), ("clr_gamma_inert", gi),
                       ("clr_gate2_revenue", g2), ("clr_price_variance", pv)):
        df = pd.DataFrame(rows)
        df.to_csv(OUT / f"{name}.csv", index=False)
        if name != "clr_gate2_revenue":
            print(f"\n=== {name} ===")
            print(df.to_string(index=False))
    g2df = pd.DataFrame(g2)
    print("\n=== gate2 revenue seam (world rows + top exporters) ===")
    print(g2df[g2df.country == "__WORLD_q_dispersion__"].to_string(index=False))
    print(g2df[g2df.country != "__WORLD_q_dispersion__"]
          .sort_values(["crop", "exports_MMT"], ascending=[True, False])
          .groupby("crop").head(5).to_string(index=False))

    # (e) solver cost reference: the parked annual spatial-equilibrium QP
    rows = []
    try:
        from sheaf.annual import SheafModel  # noqa: F401
        from sheaf.annual.core import SpatialEquilibrium, build_demand_system
        from sheaf.calibration import DATA, GRAINS, RHO, build_countries
        cs = build_countries()
        n = len(cs)
        systems = [build_demand_system(c.a, RHO) if False else None for c in cs]
        # build via the model's own path instead
        import sheaf.annual.core as AC
        t0 = time.perf_counter()
        mdl = SheafModel(build_countries())
        t_build = time.perf_counter() - t0
        t0 = time.perf_counter()
        res = mdl.run(years=1)
        t_year = time.perf_counter() - t0
        rows.append(dict(object="annual SheafModel.run(years=1)",
                         n_nodes=n, n_grains=len(GRAINS),
                         build_s=t_build, run_s=t_year,
                         implied_144_step_s=144 * t_year,
                         note="includes the year-IBR game, so an upper bound"))
    except Exception as exc:  # pragma: no cover
        rows.append(dict(object="annual import/run failed", n_nodes=-1,
                         n_grains=-1, build_s=np.nan, run_s=np.nan,
                         implied_144_step_s=np.nan, note=repr(exc)[:200]))
    # bare QP timing
    try:
        import sheaf.annual.core as AC
        from sheaf.calibration import RHO, GRAINS, build_countries
        cs = build_countries()
        n = len(cs)
        systems = [AC.build_demand_system(c, RHO) for c in cs] \
            if hasattr(AC, "build_demand_system") else None
    except Exception:
        systems = None
    pd.DataFrame(rows).to_csv(OUT / "clr_solver_cost.csv", index=False)
    print("\n=== solver cost reference ===")
    print(pd.DataFrame(rows).to_string(index=False))


if __name__ == "__main__":
    main()
