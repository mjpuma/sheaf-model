#!/usr/bin/env python3
"""Final measurements and figures for the clearing red-team slot.

(a) clr_noarb.csv     no-arbitrage test with the price condition attached:
    volume of import demand left unmet while an *unrestricted* exporter holds
    unsold grain it is asking LESS than the world price for.
(b) clr_omega.csv     omega sweep. Agrimate's published world market price is
    the volume-weighted index of international export prices, i.e. exactly
    SHEAF's p_trade, so omega = 1 is the Agrimate price definition and
    omega < 1 is a SHEAF-specific addition. Which scores better?
(c) clr_qp_cost.csv   single-commodity spatial-equilibrium QP timing, the
    like-for-like cost of a per-step clearing solve for one crop.
(d) figures fig_clr_*.png
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import redteam_clr_lib as L  # noqa: E402

from sheaf.calendar24 import STEPS_PER_YEAR  # noqa: E402
from sheaf.dynamic_crop import _ask_reweight_dest, prepare_crop_run  # noqa: E402

OUT = Path(__file__).resolve().parents[2] / "diagnostics/gate0_prep/redteam/clearing"
OUT.mkdir(parents=True, exist_ok=True)


def main() -> None:
    na, om = [], []
    fig, axes = plt.subplots(3, 3, figsize=(15, 11))
    for k, crop in enumerate(L.CROPS):
        prep = prepare_crop_run(crop, use_amis=True, use_shocks=True,
                                use_demand=False)
        r = L.simulate_instrumented(prep)
        m = r["mat"]
        n, T = m["stock"].shape

        # ---------- (a) no-arbitrage with the price condition ----------
        vol_cheap_unsold = np.zeros(T)   # unsold grain held by exporters with q<p
        vol_unmet = np.zeros(T)
        gains = np.zeros(T)
        for t in range(T):
            A_eff = _ask_reweight_dest(prep.A, m["ask"][:, t], prep.p0,
                                       gamma=prep.params.ask_comp_elast)
            cl = L.clear_instrumented(m["offers"][:, t], m["demand"][:, t],
                                      A_eff, prep.S,
                                      subst=prep.params.residual_subst)
            ol, dl = cl["offer_left2"], cl["demand_left2"]
            cheap = (m["ask"][:, t] < r["price"][t]) & (prep.cuts[:, t] < 1e-9)
            vol_cheap_unsold[t] = float(ol[cheap].sum())
            vol_unmet[t] = float(dl.sum())
            gains[t] = min(vol_cheap_unsold[t], vol_unmet[t])
        na.append(dict(
            crop=crop, T=T,
            mean_unmet_demand_MMT=float(vol_unmet.mean()),
            mean_cheap_unsold_MMT=float(vol_cheap_unsold.mean()),
            mean_unexploited_gain_MMT=float(gains.mean()),
            mean_world_trade_MMT=float(r["world_ship"].mean()),
            unexploited_over_trade=float(gains.sum()
                                         / max(r["world_ship"].sum(), 1e-12)),
            steps_with_unexploited_gain=int((gains > 1e-9).sum()),
            frac_steps_with_unexploited_gain=float((gains > 1e-9).mean()),
        ))

        # ---------- (b) omega sweep ----------
        obs07, obs10 = L.OBS_HIKES[crop]
        for w in (0.0, 0.3, 0.5, prep.params.trade_w, 0.9, 1.0):
            prep_w = prepare_crop_run(crop, use_amis=True, use_shocks=True,
                                      use_demand=False, trade_w=w)
            rw = L.simulate_instrumented(prep_w, record_trade=False)
            sc = L.score_price(rw["price"], crop)
            om.append(dict(
                crop=crop, omega=w, is_shipped=bool(w == prep.params.trade_w),
                is_agrimate_definition=bool(w == 1.0),
                corr=sc["corr"], h0708=sc["h0708"], h1011=sc["h1011"],
                obs_h0708=obs07, obs_h1011=obs10,
                abs_err_sum=abs(sc["h0708"] - obs07) + abs(sc["h1011"] - obs10),
                mean_price=float(rw["price"].mean()),
            ))

        # ---------- figures ----------
        yrs = prep.start_year + np.arange(T) / STEPS_PER_YEAR
        ax = axes[k, 0]
        ax.plot(yrs, r["world_offers"], label="offered export supply $O_t$", lw=1.2)
        ax.plot(yrs, r["world_demand"], label="import demand $D_t$", lw=1.2)
        ax.plot(yrs, r["world_ship"], label="shipments $X_t$", lw=1.6, color="k")
        ax.set_yscale("log")
        ax.set_title(f"{crop}: the traded market never balances")
        ax.set_ylabel("MMT per step")
        ax.legend(fontsize=7)

        ax = axes[k, 1]
        share = r["world_ship2"] / np.maximum(r["world_ship"], 1e-12)
        ax.plot(yrs, 100 * share, lw=1.0)
        ax.axhline(100 * r["world_ship2"].sum() / r["world_ship"].sum(),
                   color="r", ls="--",
                   label=f"window mean {100*r['world_ship2'].sum()/r['world_ship'].sum():.1f}%")
        ax.set_title(f"{crop}: share of trade via residual pool $\\nu$")
        ax.set_ylabel("% of shipments")
        ax.legend(fontsize=7)

        ax = axes[k, 2]
        ax.plot(yrs, r["price"], color="k", lw=1.4, label="$p_t$")
        ax.plot(yrs, r["p_trade"], lw=1.0, label="$p^{tr}_t$ (Agrimate def.)")
        ax.plot(yrs, r["p_scar"], lw=1.0, label="$p^{scar}_t$")
        ax.set_title(f"{crop}: the two price channels")
        ax.set_ylabel("2010 $/t")
        ax.legend(fontsize=7)
        print(f"  {crop}: done")

    fig.tight_layout()
    fig.savefig(OUT / "fig_clr_clearing.png", dpi=130)
    plt.close(fig)

    # glut asymmetry figure
    g = pd.read_csv(OUT / "clr_glut_permanent.csv")
    g = g[g["mode"] == "onesided"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    for crop in L.CROPS:
        s = g[g.crop == crop]
        axes[0].plot(100 * s.s, s.resp_shortfall_pct, "o-", label=f"{crop} shortfall")
        axes[0].plot(100 * s.s, -s.resp_surplus_pct, "s--",
                     label=f"{crop} surplus (sign-flipped)")
        axes[1].plot(100 * s.s, s.asym_ratio, "o-", label=crop)
    axes[0].set_xlabel("|harvest shock| (%)")
    axes[0].set_ylabel("|price response| (%)")
    axes[0].set_title("shortfall vs surplus response")
    axes[0].legend(fontsize=7)
    axes[1].axhline(1.0, color="k", ls=":")
    axes[1].set_xlabel("|harvest shock| (%)")
    axes[1].set_ylabel("asymmetry ratio")
    axes[1].set_title("shortfall response / surplus response")
    axes[1].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "fig_clr_glut_asymmetry.png", dpi=130)
    plt.close(fig)

    nadf, omdf = pd.DataFrame(na), pd.DataFrame(om)
    nadf.to_csv(OUT / "clr_noarb.csv", index=False)
    omdf.to_csv(OUT / "clr_omega.csv", index=False)
    print("\n=== no-arbitrage test (price condition attached) ===")
    print(nadf.to_string(index=False))
    print("\n=== omega sweep (omega=1 is the Agrimate price definition) ===")
    print(omdf.to_string(index=False))

    # ---------- (c) single-commodity QP cost ----------
    rows = []
    try:
        from sheaf.annual import build_countries
        from sheaf.annual.core import SpatialEquilibrium, build_demand_system
        from sheaf.calibration import RHO
        cs, transport, grains, fm = build_countries(substitution=True)
        n, G = len(cs), len(grains)
        systems = [build_demand_system(c, RHO) for c in cs]
        avail = np.array([[max(c.production[g], 0.1) for g in range(G)]
                          for c in cs], float)
        for label, gsel in (("3 grains", list(range(G))), ("1 grain", [0])):
            spe = SpatialEquilibrium(transport.copy(),
                                     tuple(grains[g] for g in gsel),
                                     freight_mult=fm[gsel])
            sysd = []
            for s in systems:
                import copy
                s2 = copy.deepcopy(s)
                s2.Minv = s.Minv[np.ix_(gsel, gsel)]
                s2.a = s.a[gsel]
                sysd.append(s2)
            av = avail[:, gsel]
            tax = np.zeros((n, len(gsel)))
            tar = np.zeros((n, len(gsel)))
            spe.solve(sysd, av, tax, tar)  # warm the compile
            t0 = time.perf_counter()
            reps = 5
            for _ in range(reps):
                spe.solve(sysd, av, tax, tar)
            dt = (time.perf_counter() - t0) / reps
            rows.append(dict(qp=label, n_nodes=n, per_solve_s=dt,
                             per_144_step_run_s=144 * dt,
                             x_gate0_map=144 * dt / 0.0139,
                             three_crops_five_legs_s=3 * 5 * 144 * dt))
    except Exception as exc:
        rows.append(dict(qp="failed", n_nodes=-1, per_solve_s=np.nan,
                         per_144_step_run_s=np.nan, x_gate0_map=np.nan,
                         three_crops_five_legs_s=np.nan))
        print("QP timing failed:", repr(exc)[:300])
    qdf = pd.DataFrame(rows)
    qdf.to_csv(OUT / "clr_qp_cost.csv", index=False)
    print("\n=== single-commodity QP cost ===")
    print(qdf.to_string(index=False))


if __name__ == "__main__":
    main()
