#!/usr/bin/env python3
"""R4 task 1 — parity audit: market power, network, clearing, RoW share.

(a) Exporter knockout: does a large exporter move the world price, and is the
    move proportional to its share of world offers?  Channel decomposition by
    switching off the two reduced-form terms (ask_rival, block_kappa).
(b) Trade-window sensitivity (2006-2007 vs 2010-2011 FAOSTAT E0).
(c) Realised substitution when a source is blocked (replacement ratio).
(d) RestOfWorld share of production / consumption / trade per crop.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

import r4_lib as L
from sheaf.calendar24 import STEPS_PER_YEAR
from sheaf.data_usda import load_psd_country
from sheaf.dynamic_crop import _psd_annual, prepare_crop_run

OUT = Path(__file__).resolve().parents[2] / "diagnostics" / "redteam" / "r4"
OUT.mkdir(parents=True, exist_ok=True)

# knockout window: full calendar year 2008 (24 steps) — averages the harvest
# calendar so northern and southern exporters are treated alike.
KO_Y0, KO_Y1 = 2008, 2008


def _slice(y0, m0, y1, m1, start_year=2006):
    t0 = (y0 - start_year) * STEPS_PER_YEAR + (m0 - 1) * 2
    t1 = (y1 - start_year) * STEPS_PER_YEAR + (m1 - 1) * 2 + 2
    return t0, t1


# --------------------------------------------------------------------------
# (a) exporter knockout
# --------------------------------------------------------------------------
def knockouts(crop: str, variants: dict) -> pd.DataFrame:
    rows = []
    t0, t1 = _slice(KO_Y0, 1, KO_Y1, 12)
    for vname, ov in variants.items():
        prep = prepare_crop_run(crop, use_amis=False, use_shocks=False,
                                use_demand=False, use_industrial=False, **ov)
        Hp = prep.H * (1.0 - 1e-6)          # unpin the calm branch
        base = L.run_prep(prep, harvest=Hp)
        p_base = float(np.mean(base["price"][t0:t1]))
        world_off = base["offers"][:, t0:t1].sum()
        for i, c in enumerate(prep.countries):
            share = float(base["offers"][i, t0:t1].sum() / max(world_off, 1e-12))
            if share < 1e-4:
                continue
            cuts = np.zeros_like(prep.cuts)
            cuts[i, t0:t1] = 1.0
            ko = L.run_prep(prep, cuts=cuts, harvest=Hp)
            p_ko = float(np.mean(ko["price"][t0:t1]))
            lost = float((base["exports"][i, t0:t1] - ko["exports"][i, t0:t1]).sum())
            others = [j for j in range(len(prep.countries)) if j != i]
            gained = float((ko["exports"][np.ix_(others)][:, t0:t1]
                            - base["exports"][np.ix_(others)][:, t0:t1]).sum())
            rows.append(dict(
                crop=crop, variant=vname, country=c, offer_share=share,
                p_base=p_base, p_ko=p_ko, lift=p_ko / p_base - 1.0,
                lost_mmt=lost, replaced_mmt=gained,
                replacement_ratio=(gained / lost if lost > 1e-9 else np.nan),
                d_world_ship=float(ko["exports"][:, t0:t1].sum()
                                   - base["exports"][:, t0:t1].sum()),
                d_p_trade=float(np.mean(ko["p_trade"][t0:t1]
                                        - base["p_trade"][t0:t1]) / p_base),
                d_free=float(np.mean(ko["free"][t0:t1] - base["free"][t0:t1])),
                mean_block_frac=float(np.mean(ko["block_frac"][t0:t1])),
            ))
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# (b) trade-window sensitivity
# --------------------------------------------------------------------------
def trade_window_scan(crop: str) -> pd.DataFrame:
    rows = []
    for win in ((2006, 2007), (2010, 2011), (2019, 2021)):
        prep = prepare_crop_run(crop, use_amis=True, use_shocks=True,
                                use_demand=False, trade_window=win)
        out = L.run_prep(prep)
        s = L.score(out["price"], crop)
        rows.append(dict(crop=crop, window=f"{win[0]}-{win[1]}", **s))
    # structural distance between the windows
    cs = prepare_crop_run(crop, use_amis=False, use_shocks=False,
                          use_demand=False).countries
    E06 = L.trade_matrix_nodes(crop, cs, (2006, 2007)).to_numpy(float)
    E10 = L.trade_matrix_nodes(crop, cs, (2010, 2011)).to_numpy(float)
    n06 = E06 / max(E06.sum(), 1e-12)
    n10 = E10 / max(E10.sum(), 1e-12)
    for r in rows:
        r["L1_share_dist_0607_vs_1011"] = float(np.abs(n06 - n10).sum())
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# (c) realised substitution on the scored path (Russia 2010 etc.)
# --------------------------------------------------------------------------
_EPISODES = {
    "wheat": [("Russia", 2010, 8, 2010, 12)],
    "maize": [("Argentina", 2007, 5, 2008, 1), ("Ukraine", 2010, 10, 2011, 6)],
    "rice": [("Vietnam", 2008, 9, 2008, 11), ("India", 2007, 10, 2007, 12)],
}


def substitution(crop: str) -> pd.DataFrame:
    prep_f = prepare_crop_run(crop, use_amis=True, use_shocks=True,
                              use_demand=False)
    prep_s = prepare_crop_run(crop, use_amis=False, use_shocks=True,
                              use_demand=False)
    full = L.run_prep(prep_f)
    shk = L.run_prep(prep_s)
    rows = []
    for c, y0, m0, y1, m1 in _EPISODES.get(crop, []):
        i = prep_f.countries.index(c)
        t0, t1 = _slice(y0, m0, y1, m1)
        off_f = float(full["offers"][i, t0:t1].mean())
        off_s = float(shk["offers"][i, t0:t1].mean())
        shp_f = float(full["exports"][i, t0:t1].mean())
        shp_s = float(shk["exports"][i, t0:t1].mean())
        lost = float((shk["exports"][i, t0:t1] - full["exports"][i, t0:t1]).sum())
        oth = [j for j in range(len(prep_f.countries)) if j != i]
        gained = float((full["exports"][oth][:, t0:t1]
                        - shk["exports"][oth][:, t0:t1]).sum())
        # unexploited double coincidence: offers left AND demand left
        rows.append(dict(
            crop=crop, country=c, window=f"{y0}-{m0:02d}->{y1}-{m1:02d}",
            offer_ratio=off_f / max(off_s, 1e-12),
            ship_ratio=shp_f / max(shp_s, 1e-12),
            lost_mmt=lost, replaced_mmt=gained,
            replacement_ratio=gained / lost if lost > 1e-9 else np.nan,
            world_ship_ratio=float(full["exports"][:, t0:t1].sum()
                                   / max(shk["exports"][:, t0:t1].sum(), 1e-12)),
            mean_block_frac=float(full["block_frac"][t0:t1].mean()),
        ))
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# (d) RestOfWorld weight
# --------------------------------------------------------------------------
def row_share(crop: str) -> pd.DataFrame:
    prep = prepare_crop_run(crop, use_amis=False, use_shocks=False,
                            use_demand=False)
    cs = prep.countries
    years = list(range(prep.start_year, prep.end_year + 1))
    prod, cons = _psd_annual(crop, cs, years)
    p = prod.groupby("country").production.mean()
    q = cons.groupby("country").consumption.mean()
    E = L.trade_matrix_nodes(crop, cs, (2006, 2007)).to_numpy(float)
    np.fill_diagonal(E, 0.0)
    irow = cs.index("RestOfWorld")
    exp_i, imp_j = E.sum(axis=1), E.sum(axis=0)
    # model offers/shipments on the official leg
    prep_f = prepare_crop_run(crop, use_amis=True, use_shocks=True,
                              use_demand=False)
    full = L.run_prep(prep_f)
    off = full["offers"].sum(axis=1)
    shp = full["exports"].sum(axis=1)
    rcv = full["received"].sum(axis=1)
    n_named = len(cs) - 1
    return pd.DataFrame([dict(
        crop=crop, n_nodes=len(cs), n_named=n_named,
        row_prod_share=float(p["RestOfWorld"] / p.sum()),
        row_cons_share=float(q["RestOfWorld"] / q.sum()),
        row_faostat_export_share=float(exp_i[irow] / max(exp_i.sum(), 1e-12)),
        row_faostat_import_share=float(imp_j[irow] / max(imp_j.sum(), 1e-12)),
        row_model_offer_share=float(off[irow] / max(off.sum(), 1e-12)),
        row_model_ship_share=float(shp[irow] / max(shp.sum(), 1e-12)),
        row_model_recv_share=float(rcv[irow] / max(rcv.sum(), 1e-12)),
        hhi_faostat_exports=float(((exp_i / max(exp_i.sum(), 1e-12)) ** 2).sum()),
        hhi_model_ship=float(((shp / max(shp.sum(), 1e-12)) ** 2).sum()),
    )])


def main():
    variants = {
        "shipped": dict(),
        "no_ask_rival": dict(ask_rival=0.0),
        "no_rival_no_block": dict(ask_rival=0.0, block_kappa=0.0),
    }
    ko = pd.concat([knockouts(c, variants) for c in L.CROPS], ignore_index=True)
    ko.to_csv(OUT / "r4_01_knockout.csv", index=False)

    print("=== (a) exporter knockout: lift vs share ===")
    for crop in L.CROPS:
        for v in variants:
            sub = ko[(ko.crop == crop) & (ko.variant == v)]
            if len(sub) < 3:
                continue
            r = np.corrcoef(sub.offer_share, sub.lift)[0, 1]
            slope = np.polyfit(sub.offer_share, sub.lift, 1)[0]
            print(f"  {crop:5s} {v:18s} n={len(sub):2d}  "
                  f"corr(share,lift)={r:+.3f}  slope={slope:+.3f}  "
                  f"max lift={sub.lift.max():+.3f} "
                  f"({sub.loc[sub.lift.idxmax(),'country']})")

    tw = pd.concat([trade_window_scan(c) for c in L.CROPS], ignore_index=True)
    tw.to_csv(OUT / "r4_01_trade_window.csv", index=False)
    print("\n=== (b) trade-window sensitivity ===")
    print(tw.to_string(index=False, float_format=lambda x: f"{x:.3f}"))

    sb = pd.concat([substitution(c) for c in L.CROPS], ignore_index=True)
    sb.to_csv(OUT / "r4_01_substitution.csv", index=False)
    print("\n=== (c) realised substitution ===")
    print(sb.to_string(index=False, float_format=lambda x: f"{x:.3f}"))

    rw = pd.concat([row_share(c) for c in L.CROPS], ignore_index=True)
    rw.to_csv(OUT / "r4_01_restofworld.csv", index=False)
    print("\n=== (d) RestOfWorld weight ===")
    print(rw.to_string(index=False, float_format=lambda x: f"{x:.3f}"))
    print(f"\nwrote CSVs to {OUT}")


if __name__ == "__main__":
    main()
