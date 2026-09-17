#!/usr/bin/env python3
"""R2 step 5: falsification tests for the P2 prototype, plus figures.

F1  Is the gain the *budget constraint*, or just price-responsiveness?
    A_D = 0 collapses Agrimate's CES budget factor to a plain isoelastic
    p_hat^-eps_d. If A_D=0 captures most of the effect, the budget wall (the
    part that needs a budget) is not what is doing the work.

F2  Does P2 double-count the existing elasticity? Decompose the finite
    difference into the food_need channel (which carries params.elast) and
    the rebuild channel (which carries eps_d), and check they act on disjoint
    quantities.

F3  Twin identity: is g_d(1) == 1 to machine precision, and is the
    treatment-vs-twin free-stock path unchanged in the calm leg?

F4  Seasonality: spring/autumn ratio on the climatology path.

F5  Physical plausibility: does P2 move world consumption and stocks?

F6  (c) rationing -- how much of the unmet-demand *anomaly* that prices the
    market survives differencing against the twin?
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from r2_05_prototypes import BASE_SUBS, VARIANTS
from r2_lib import CROPS, FIGS, OUT, load_variant, official_scores


def main() -> None:
    base = load_variant("f_base", BASE_SUBS)
    p2 = load_variant("f_P2", BASE_SUBS + VARIANTS["P2_purchaser_budget"])
    p2.pop = None  # noqa - marker only

    rows_f, rows_c = [], []
    fig, axes = plt.subplots(2, 3, figsize=(14, 7))

    for j, crop in enumerate(CROPS):
        sb = official_scores(base, crop)
        sp = official_scores(p2, crop)
        rb, rp = sb["res"], sp["res"]
        prep = base.prepare_crop_run(crop, use_amis=True, use_shocks=True,
                                     use_demand=False)

        # ---- F5 physical plausibility -------------------------------------
        rows_f.append(dict(
            crop=crop,
            cons_base_mmt=float(rb.consumption.sum()),
            cons_p2_mmt=float(rp.consumption.sum()),
            cons_pct_change=100.0 * float(rp.consumption.sum()
                                          / rb.consumption.sum() - 1),
            stock_base_mean=float(rb.stock.sum(axis=0).mean()),
            stock_p2_mean=float(rp.stock.sum(axis=0).mean()),
            stock_pct_change=100.0 * float(rp.stock.sum(axis=0).mean()
                                           / rb.stock.sum(axis=0).mean() - 1),
            trade_base_mmt=float(rb.exports.sum()),
            trade_p2_mmt=float(rp.exports.sum()),
            trade_pct_change=100.0 * float(rp.exports.sum()
                                           / rb.exports.sum() - 1),
            price_mean_base=float(rb.price.mean()),
            price_mean_p2=float(rp.price.mean()),
        ))

        # ---- F6 unmet anomaly (question c) --------------------------------
        u = rb.unmet_frac
        u0 = prep.unmet_twin
        u_anom = np.maximum(0.0, u - u0)
        rows_c.append(dict(
            crop=crop,
            mean_unmet_frac=float(u.mean()),
            mean_unmet_twin=float(u0.mean()),
            mean_unmet_anomaly=float(u_anom.mean()),
            max_unmet_anomaly=float(u_anom.max()),
            frac_of_level_surviving=float(u_anom.mean() / max(u.mean(), 1e-12)),
            unmet_kappa=prep.params.unmet_kappa,
            max_price_uplift_pct=100.0 * float(
                prep.params.unmet_kappa * u_anom.max()),
        ))

        ax = axes[0, j]
        ax.plot(sb["monthly"].obs_price.to_numpy(), color="#c0392b", lw=2,
                label="Pink Sheet")
        ax.plot(sb["monthly"].model_price.to_numpy(), color="0.2", lw=1.3,
                label=f"baseline ({sb['corr']:+.3f})")
        ax.plot(sp["monthly"].model_price.to_numpy(), color="#1f77b4", lw=1.3,
                ls="--", label=f"P2 purchaser budget ({sp['corr']:+.3f})")
        ax.set_title(f"{crop}: monthly price 2006-2011")
        ax.set_ylabel("$/t")
        ax.legend(fontsize=7, frameon=False)

        ax = axes[1, j]
        ax.plot(u, color="0.4", lw=1.0, label="unmet frac (level)")
        ax.plot(u0, color="#2ca02c", lw=1.0, ls=":", label="twin unmet frac")
        ax.plot(u_anom, color="#d62728", lw=1.2, label="anomaly (prices market)")
        ax.set_title(f"{crop}: unmet demand -- level vs anomaly")
        ax.set_xlabel("step")
        ax.legend(fontsize=7, frameon=False)

    fig.tight_layout()
    fig.savefig(FIGS / "r2_prototype_and_rationing.png", dpi=140)
    plt.close(fig)

    df_f = pd.DataFrame(rows_f)
    df_c = pd.DataFrame(rows_c)
    df_f.to_csv(OUT / "r2_F5_physical_plausibility.csv", index=False)
    df_c.to_csv(OUT / "r2_F6_unmet_anomaly.csv", index=False)
    print("== F5 physical plausibility (baseline vs P2) ==")
    print(df_f.to_string(index=False))
    print("\n== F6 unmet demand: level vs twin-differenced anomaly ==")
    print(df_c.to_string(index=False))

    # ---- F1 read straight off the A_D sweep ------------------------------
    sw = pd.read_csv(OUT / "r2_P2_A_D_sweep.csv")
    eff = pd.read_csv(OUT / "r2_effective_elasticity.csv")
    rows = []
    for crop in CROPS:
        e_base = float(eff[eff.crop == crop].eta_market_demand_mean.iloc[0])
        e_a0 = float(sw[(sw.crop == crop) & (sw.A_D == 0.0)]
                     .eta_market_demand.iloc[0])
        e_a05 = float(sw[(sw.crop == crop) & (sw.A_D == 0.05)]
                      .eta_market_demand.iloc[0])
        rows.append(dict(
            crop=crop, eta_baseline=e_base,
            eta_isoelastic_only_A_D0=e_a0, eta_full_budget_A_D005=e_a05,
            share_of_gain_from_elasticity=100.0 * (e_a0 - e_base)
            / (e_a05 - e_base),
            share_of_gain_from_budget_wall=100.0 * (e_a05 - e_a0)
            / (e_a05 - e_base)))
    df1 = pd.DataFrame(rows)
    df1.to_csv(OUT / "r2_F1_budget_vs_elasticity.csv", index=False)
    print("\n== F1 what does the work: elasticity or the budget wall? ==")
    print(df1.to_string(index=False))
    print(f"\nwrote {FIGS / 'r2_prototype_and_rationing.png'}")


if __name__ == "__main__":
    main()
