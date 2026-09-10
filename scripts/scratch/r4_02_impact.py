#!/usr/bin/env python3
"""R4 task 1(a)/1(c) — marginal price impact and mechanism-level substitution.

Part A: marginal supply cut (10%) on one exporter at a time over calendar 2008.
  price impact elasticity  eta_i = -dlog p / dlog x_i
  implied Agrimate alpha   alpha_i = eta_i / s_i     (Cournot: dlogP/dlogx_i = -alpha*s_i)
  s_i measured both as offer share and as realised shipment share.

Part B: static, one-step clearing comparison with a source blocked —
  shipped short-side clearing vs Agrimate-style CES source reallocation with
  proportional supplier rationing. Isolates the mechanism from dynamics.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

import r4_lib as L
from r4_lib import _agrimate_clear, _source_reweight
from sheaf.calendar24 import STEPS_PER_YEAR
from sheaf.dynamic_crop import _bilateral_clear, prepare_crop_run

OUT = Path(__file__).resolve().parents[2] / "diagnostics" / "redteam" / "r4"
OUT.mkdir(parents=True, exist_ok=True)

EPS = 0.10          # marginal supply cut
AGRIMATE_ALPHA_I = {"wheat": 3.2, "maize": 2.7, "rice": 2.2}


def _sl(y0, m0, y1, m1, sy=2006):
    return ((y0 - sy) * STEPS_PER_YEAR + (m0 - 1) * 2,
            (y1 - sy) * STEPS_PER_YEAR + (m1 - 1) * 2 + 2)


def marginal_impact(crop: str, variants: dict) -> pd.DataFrame:
    rows = []
    t0, t1 = _sl(2008, 1, 2008, 12)
    for vname, ov in variants.items():
        prep = prepare_crop_run(crop, use_amis=False, use_shocks=False,
                                use_demand=False, use_industrial=False, **ov)
        Hp = prep.H * (1.0 - 1e-6)
        base = L.run_prep(prep, harvest=Hp)
        p_b = float(np.mean(base["price"][t0:t1]))
        off_b = base["offers"][:, t0:t1].sum(axis=1)
        shp_b = base["exports"][:, t0:t1].sum(axis=1)
        for i, c in enumerate(prep.countries):
            if shp_b[i] < 1e-6 and off_b[i] < 1e-6:
                continue
            cuts = np.zeros_like(prep.cuts)
            cuts[i, t0:t1] = EPS
            r = L.run_prep(prep, cuts=cuts, harvest=Hp)
            p_r = float(np.mean(r["price"][t0:t1]))
            x_b = float(shp_b[i])
            x_r = float(r["exports"][i, t0:t1].sum())
            if x_b < 1e-6 or x_r < 1e-9:
                continue
            dlp = np.log(p_r / p_b)
            dlx = np.log(x_r / x_b)
            if abs(dlx) < 1e-9:
                continue
            eta = -dlp / dlx
            s_off = float(off_b[i] / max(off_b.sum(), 1e-12))
            s_shp = float(shp_b[i] / max(shp_b.sum(), 1e-12))
            rows.append(dict(
                crop=crop, variant=vname, country=c,
                offer_share=s_off, ship_share=s_shp,
                dlogp=dlp, dlogx=dlx, eta_price_impact=eta,
                alpha_from_offer_share=eta / s_off if s_off > 1e-6 else np.nan,
                alpha_from_ship_share=eta / s_shp if s_shp > 1e-6 else np.nan,
                agrimate_alpha_I=AGRIMATE_ALPHA_I[crop],
            ))
    return pd.DataFrame(rows)


def static_substitution(crop: str) -> pd.DataFrame:
    """One-step clearing with a source removed: shipped vs Agrimate CES."""
    prep = prepare_crop_run(crop, use_amis=False, use_shocks=True,
                            use_demand=False)
    base = L.run_prep(prep)
    A, S, p0 = prep.A, prep.S, prep.p0
    sigma = prep.params.ask_comp_elast
    subst = prep.params.residual_subst
    episodes = {"wheat": [("Russia", 2010, 8, 2010, 12)],
                "maize": [("USA", 2008, 1, 2008, 12),
                          ("Argentina", 2007, 5, 2008, 1)],
                "rice": [("Vietnam", 2008, 9, 2008, 11),
                         ("India", 2007, 10, 2007, 12)]}
    rows = []
    for c, y0, m0, y1, m1 in episodes[crop]:
        i = prep.countries.index(c)
        t0, t1 = _sl(y0, m0, y1, m1)
        acc = dict(base_ship=0.0, sh_lost=0.0, sh_rep=0.0,
                   ce_lost=0.0, ce_rep=0.0, ag_lost=0.0, ag_rep=0.0,
                   unmet_sh=0.0, unmet_ag=0.0, dem=0.0)
        for t in range(t0, t1):
            off = base["offers"][:, t].copy()
            dem = base["demand"][:, t].copy()
            ask = base["ask"][:, t].copy()
            A_eff = A                                    # reweight is a no-op
            S_eff = _source_reweight(S, ask, p0, sigma)
            # baseline (no block)
            sh0, _, _ = _bilateral_clear(off, dem, A_eff, S, subst=subst)
            ag0, _, _ = _agrimate_clear(off, dem, S_eff, subst)
            # blocked
            offb = off.copy()
            offb[i] = 0.0
            shb, rvb, _ = _bilateral_clear(offb, dem, A_eff, S, subst=subst)
            # CES re-allocation: drop i from the source mix and renormalise
            S_blk = S_eff.copy()
            S_blk[i, :] = 0.0
            col = S_blk.sum(axis=0, keepdims=True)
            np.divide(S_blk, col, out=S_blk, where=col > 0)
            agb, rva, _ = _agrimate_clear(offb, dem, S_blk, subst)
            oth = [j for j in range(len(off)) if j != i]
            acc["base_ship"] += float(sh0.sum())
            acc["sh_lost"] += float(sh0[i] - shb[i])
            acc["sh_rep"] += float(shb[oth].sum() - sh0[oth].sum())
            acc["ag_lost"] += float(ag0[i] - agb[i])
            acc["ag_rep"] += float(agb[oth].sum() - ag0[oth].sum())
            acc["unmet_sh"] += float(max(0.0, dem.sum() - rvb.sum()))
            acc["unmet_ag"] += float(max(0.0, dem.sum() - rva.sum()))
            acc["dem"] += float(dem.sum())
        rows.append(dict(
            crop=crop, country=c, window=f"{y0}-{m0:02d}->{y1}-{m1:02d}",
            n_steps=t1 - t0,
            shipped_lost=acc["sh_lost"], shipped_replaced=acc["sh_rep"],
            shipped_replacement=acc["sh_rep"] / max(acc["sh_lost"], 1e-12),
            ces_lost=acc["ag_lost"], ces_replaced=acc["ag_rep"],
            ces_replacement=acc["ag_rep"] / max(acc["ag_lost"], 1e-12),
            unmet_frac_shipped=acc["unmet_sh"] / max(acc["dem"], 1e-12),
            unmet_frac_ces=acc["unmet_ag"] / max(acc["dem"], 1e-12),
        ))
    return pd.DataFrame(rows)


def main():
    variants = {"shipped": dict(),
                "no_rival_no_block": dict(ask_rival=0.0, block_kappa=0.0)}
    mi = pd.concat([marginal_impact(c, variants) for c in L.CROPS],
                   ignore_index=True)
    mi.to_csv(OUT / "r4_02_marginal_impact.csv", index=False)
    pd.set_option("display.width", 220)
    print("=== marginal price impact (10% supply cut, calendar 2008) ===")
    for crop in L.CROPS:
        for v in variants:
            s = mi[(mi.crop == crop) & (mi.variant == v)]
            s = s[s.ship_share > 0.01].sort_values("ship_share", ascending=False)
            if s.empty:
                continue
            r = (np.corrcoef(s.ship_share, s.eta_price_impact)[0, 1]
                 if len(s) > 2 else np.nan)
            print(f"\n{crop} / {v}   corr(ship_share, eta)={r:+.3f}   "
                  f"Agrimate alpha_I={AGRIMATE_ALPHA_I[crop]}")
            print(s[["country", "ship_share", "eta_price_impact",
                     "alpha_from_ship_share"]].to_string(
                index=False, float_format=lambda x: f"{x:.3f}"))

    ss = pd.concat([static_substitution(c) for c in L.CROPS],
                   ignore_index=True)
    ss.to_csv(OUT / "r4_02_static_substitution.csv", index=False)
    print("\n=== static one-step substitution: shipped vs Agrimate CES ===")
    print(ss.to_string(index=False, float_format=lambda x: f"{x:.3f}"))
    print(f"\nwrote CSVs to {OUT}")


if __name__ == "__main__":
    main()
