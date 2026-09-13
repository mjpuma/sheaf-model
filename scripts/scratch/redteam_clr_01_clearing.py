#!/usr/bin/env python3
"""Task 1 — is the Gate 0 market cleared, and in what sense?

Writes diagnostics/gate0_prep/redteam/clearing/*.csv:
  clr_massbalance.csv    accounting identities + capacity drawdown volume
  clr_residual_pool.csv  prescribed-network vs residual-pool trade share
  clr_unexploited.csv    offers and demand left unmatched simultaneously
  clr_walras.csv         does a flow-clearing price exist in the price bounds?
  clr_signs.csv          sign consistency of price change vs excess demand
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
OUT.mkdir(parents=True, exist_ok=True)

START, END = 2006, 2011


def episode_mask(T: int, start_year: int) -> dict[str, np.ndarray]:
    """Jul(y)-Jun(y+1) marketing windows as step masks."""
    def win(y0, m0, y1, m1):
        t0 = (y0 - start_year) * STEPS_PER_YEAR + (m0 - 1) * 2
        t1 = (y1 - start_year) * STEPS_PER_YEAR + (m1 - 1) * 2 + 2
        m = np.zeros(T, bool)
        m[max(t0, 0):min(t1, T)] = True
        return m
    e0708 = win(2007, 7, 2008, 6)
    e1011 = win(2010, 7, 2011, 6)
    return {"all": np.ones(T, bool), "2007/08": e0708, "2010/11": e1011,
            "calm": ~(e0708 | e1011)}


def main() -> None:
    mb, rp, ux, wl, sg = [], [], [], [], []
    for crop in L.CROPS:
        # Official P1 matched leg: harvest + AMIS + mean flex.
        prep = prepare_crop_run(crop, start_year=START, end_year=END,
                                use_amis=True, use_shocks=True, use_demand=False)
        r = L.simulate_instrumented(prep)
        m = r["mat"]
        n, T = m["stock"].shape
        eps = episode_mask(T, START)
        pr = prep.params

        # ---------------- mass balance ----------------
        stock_prev = np.concatenate([prep.stock0[:, None], m["stock"][:, :-1]], axis=1)
        avail = stock_prev + prep.H
        resid = (avail - m["shipped"] + m["received"] - m["cons"]
                 - m["stock"] - m["drawdown_i"])
        mb.append(dict(
            crop=crop, n=n, T=T,
            avail_recomputed_max_abs_err=float(np.max(np.abs(avail - m["avail"]))),
            massbalance_max_abs_MMT=float(np.max(np.abs(resid))),
            massbalance_rel_to_world_avail=float(
                np.max(np.abs(resid)) / avail.sum(axis=0).mean()),
            world_ship_minus_recv_max_abs=float(
                np.max(np.abs(r["world_ship"] - r["world_recv"]))),
            total_harvest_MMT=float(prep.H.sum()),
            total_drawdown_MMT=float(r["drawdown"].sum()),
            drawdown_pct_of_harvest=100 * float(r["drawdown"].sum() / prep.H.sum()),
            drawdown_pct_of_consumption=100 * float(
                r["drawdown"].sum() / r["world_cons"].sum()),
            total_trade_MMT=float(r["world_ship"].sum()),
            drawdown_over_trade=float(r["drawdown"].sum() / r["world_ship"].sum()),
            steps_with_drawdown=int((r["drawdown"] > 1e-9).sum()),
        ))

        # ---------------- residual pool ----------------
        # per-link split of stage 1: exporter-side vs importer-side binding
        A_share_bind = np.zeros(T)
        S_share_bind = np.zeros(T)
        for t in range(T):
            from sheaf.dynamic_crop import _ask_reweight_dest
            A_eff = _ask_reweight_dest(prep.A, m["ask"][:, t] if t == 0 else
                                       m["ask"][:, t], prep.p0,
                                       gamma=pr.ask_comp_elast)
            cl = L.clear_instrumented(m["offers"][:, t], m["demand"][:, t],
                                      A_eff, prep.S, subst=pr.residual_subst)
            o_bind = cl["O"] < cl["D"]
            A_share_bind[t] = float(cl["ship1"][o_bind].sum())
            S_share_bind[t] = float(cl["ship1"][~o_bind].sum())
        for name, msk in eps.items():
            tot = float(r["world_ship"][msk].sum())
            rp.append(dict(
                crop=crop, episode=name, steps=int(msk.sum()),
                world_trade_MMT=tot,
                network_MMT=float(r["world_ship1"][msk].sum()),
                residual_MMT=float(r["world_ship2"][msk].sum()),
                residual_share=float(r["world_ship2"][msk].sum() / max(tot, 1e-12)),
                residual_share_step_mean=float(np.mean(
                    r["world_ship2"][msk] / np.maximum(r["world_ship"][msk], 1e-12))),
                residual_share_step_max=float(np.max(
                    r["world_ship2"][msk] / np.maximum(r["world_ship"][msk], 1e-12))),
                exporter_side_binding_share=float(
                    A_share_bind[msk].sum() / max(float(r["world_ship1"][msk].sum()), 1e-12)),
                trade_over_world_demand=float(
                    tot / max(float(r["world_demand"][msk].sum()), 1e-12)),
            ))

        # ---------------- unexploited gains from trade ----------------
        both = (r["offer_left2"] > 1e-9) & (r["demand_left2"] > 1e-9)
        ux.append(dict(
            crop=crop,
            steps_both_sides_left=int(both.sum()), T=T,
            frac_steps_both_sides_left=float(both.mean()),
            mean_offer_left_MMT=float(r["offer_left2"].mean()),
            mean_demand_left_MMT=float(r["demand_left2"].mean()),
            mean_world_trade_MMT=float(r["world_ship"].mean()),
            mean_double_coincidence_MMT=float(r["double_coincidence"].mean()),
            double_coincidence_over_trade=float(
                r["double_coincidence"].sum() / max(r["world_ship"].sum(), 1e-12)),
            offer_left_over_offers=float(
                r["offer_left2"].sum() / max(r["world_offers"].sum(), 1e-12)),
            demand_left_over_demand=float(
                r["demand_left2"].sum() / max(r["world_demand"].sum(), 1e-12)),
            # rationing / slack coexistence in the *consumption* market
            steps_rationing_and_slack=int(((r["rationing"] > 1e-9)
                                           & (r["slack"] > 1e-9)).sum()),
            mean_rationing_MMT=float(r["rationing"].mean()),
            mean_slack_MMT=float(r["slack"].mean()),
        ))

        # ---------------- Walras: does a clearing price exist? ----------------
        # Flow condition: desired use d(p) = availability minus desired cover.
        # d(p) = sum_i C_flex (p/p0)^eps + sum_i C_ind  (storage demand is the
        # price-independent target T_it, so it cannot equilibrate p).
        Cf = prep.C_flex.sum(axis=0)
        Ci = prep.C_ind.sum(axis=0)
        supply_for_use = avail.sum(axis=0) - m["target"].sum(axis=0)
        exists = np.zeros(T, bool)
        p_clear = np.full(T, np.nan)
        for t in range(T):
            def z(p):  # excess demand for the consumption flow
                return Cf[t] * (p / prep.p0) ** pr.elast + Ci[t] - supply_for_use[t]
            lo, hi = 60.0, 1200.0
            zl, zh = z(lo), z(hi)
            if zl * zh < 0:
                exists[t] = True
                for _ in range(80):
                    mid = 0.5 * (lo + hi)
                    if z(lo) * z(mid) <= 0:
                        hi = mid
                    else:
                        lo = mid
                p_clear[t] = 0.5 * (lo + hi)
        # local elasticity of excess supply wrt price at the realised price
        dlnZ = np.zeros(T)
        for t in range(T):
            p = r["price"][t]
            d0 = Cf[t] * (p / prep.p0) ** pr.elast + Ci[t]
            dd = Cf[t] * pr.elast * (p / prep.p0) ** pr.elast
            dlnZ[t] = dd / max(abs(supply_for_use[t] - d0), 1e-12)
        wl.append(dict(
            crop=crop, T=T,
            steps_with_interior_clearing_price=int(exists.sum()),
            mean_supply_for_use_MMT=float(supply_for_use.mean()),
            mean_desired_use_MMT=float(r["world_desired"].mean()),
            supply_over_desired_use=float(
                supply_for_use.mean() / r["world_desired"].mean()),
            excess_supply_at_pmax_MMT=float(np.mean(
                supply_for_use - (Cf * (1200 / prep.p0) ** pr.elast + Ci))),
            steps_excess_supply_at_pmax=int(np.sum(
                supply_for_use > Cf * (1200 / prep.p0) ** pr.elast + Ci)),
            price_move_to_absorb_1pct_harvest_pct=float(np.mean(
                0.01 * r["world_H"] / np.maximum(
                    abs(Cf * pr.elast / 100.0), 1e-12))),
            storage_demand_price_elasticity=0.0,
        ))

        # ---------------- sign consistency ----------------
        dp = np.diff(r["price"], prepend=prep.p0)
        z = (r["rationing"] - r["slack"]) / np.maximum(r["world_desired"], 1e-9)
        gap = r["free"] - prep.free_twin  # accessible stock vs twin (>0 = loose)
        agree_z = np.sign(dp) == np.sign(z)
        agree_gap = np.sign(dp) == -np.sign(gap)
        sg.append(dict(
            crop=crop, T=T,
            frac_dp_agrees_with_excess_demand=float(agree_z.mean()),
            corr_dp_excess_demand=float(np.corrcoef(dp, z)[0, 1]),
            frac_z_positive=float((z > 1e-12).mean()),
            frac_dp_agrees_with_stock_gap=float(agree_gap.mean()),
            corr_logp_stockgap=float(np.corrcoef(np.log(r["price"]), gap)[0, 1]),
            frac_steps_price_above_p0=float((r["price"] > prep.p0).mean()),
            frac_steps_stock_below_twin=float((gap < 0).mean()),
            frac_steps_unmet_below_twin=float(
                (r["unmet_frac"] < prep.unmet_twin).mean()),
            frac_steps_u_anom_truncated=float((r["u_anom"] <= 0).mean()),
        ))
        print(f"  {crop}: done")

    for name, rows in (("clr_massbalance", mb), ("clr_residual_pool", rp),
                       ("clr_unexploited", ux), ("clr_walras", wl),
                       ("clr_signs", sg)):
        df = pd.DataFrame(rows)
        df.to_csv(OUT / f"{name}.csv", index=False)
        print(f"\n=== {name} ===")
        print(df.to_string(index=False))


if __name__ == "__main__":
    main()
