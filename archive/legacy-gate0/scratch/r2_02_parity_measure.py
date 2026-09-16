#!/usr/bin/env python3
"""R2 step 2: measurements for parity questions (a), (c), (d).

(a) Budget constraint. Agrimate Eq. (6c)/(D.35) with B*_c,s = p*C*/A*_c,s
    gives, in ratio form with p_hat = p/p0,

        C(p_hat)/C* = p_hat^(-eps_c) / (1 + A*(p_hat^(1-eps_c) - 1)),

    whose local elasticity is -(eps_c + s(p))(1-eps_c)... more precisely
        dlnC/dlnp = (1-eps_c)(1 - s(p)) - 1 = -[eps_c + s(p)(1-eps_c)],
    where s(p) is the *current* budget share. s -> 1 as p -> inf, so the
    elasticity tends to -1 and expenditure is capped at B* = C*/A*.
    SHEAF Gate 0 (dynamic_crop.py:595) uses C/C* = p_hat^elast, constant
    elasticity, unbounded expenditure. This script measures the gap on the
    official scored path.

(c) Rationing. Counts steps where aggregate offers >= aggregate demand yet
    demand still goes unmet -- i.e. unmet caused by the short-side/residual
    rule rather than by physical world scarcity.

(d) Storage cap. Instruments _simulate_window to record `desired` and the
    availability cap, and reports how often the cap binds.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from r2_lib import CROPS, OUT, load_variant, official_scores

# Agrimate defaults (Suppl. Table D.8): eps_c = 0.1 (consumer),
# eps_d = 1/alpha = 1/3 (purchaser), sigma = 2 (supplier substitution).
EPS_C = 0.1
A_GRID = (0.05, 0.10, 0.20, 0.40)

REC_ANCHOR = "MAX_LEAN_STEPS = STEPS_PER_YEAR"
REC_NEW = "MAX_LEAN_STEPS = STEPS_PER_YEAR\n_REC = {}"
CONS_ANCHOR = """        consumption = np.minimum(
            desired, np.maximum(0.0, avail - shipped + received))"""
CONS_NEW = """        _cap = np.maximum(0.0, avail - shipped + received)
        consumption = np.minimum(desired, _cap)
        _REC.setdefault('desired', []).append(desired.copy())
        _REC.setdefault('cap', []).append(_cap.copy())
        _REC.setdefault('avail', []).append(avail.copy())
        _REC.setdefault('flex', []).append(C_flex[:, t].copy())
        _REC.setdefault('ind', []).append(C_ind[:, t].copy())
        _REC.setdefault('p_prev', []).append(float(p))"""


def agri_ratio(p_hat, a_star, eps_c=EPS_C):
    """Agrimate Eq. (D.35) unconstrained branch, normalised to 1 at p_hat=1."""
    p_hat = np.asarray(p_hat, float)
    x = p_hat ** (1.0 - eps_c)
    return p_hat ** (-eps_c) / (1.0 + a_star * (x - 1.0))


def main() -> None:
    mod = load_variant("r2rec", [(REC_ANCHOR, REC_NEW),
                                 (CONS_ANCHOR, CONS_NEW)])
    base = load_variant("r2b2")

    rows_a, rows_c, rows_d, rows_ctry = [], [], [], []

    for crop in CROPS:
        prep = mod.prepare_crop_run(crop, use_amis=True, use_shocks=True,
                                    use_demand=False)
        mod._REC.clear()
        res = mod.simulate_prep(prep)
        rec = {k: np.array(v) for k, v in mod._REC.items()}   # (T, n) or (T,)
        desired = rec["desired"].T          # (n, T)
        cap = rec["cap"].T
        flex = rec["flex"].T
        ind = rec["ind"].T
        p_prev = rec["p_prev"]              # price used to form demand at t
        p0 = prep.p0
        countries = prep.countries
        T = desired.shape[1]
        p_hat = np.asarray(p_prev) / p0
        elast = prep.params.elast

        # ---------- (d) does the availability cap bind? ----------
        bind = desired - cap > 1e-9
        shortfall = np.maximum(0.0, desired - cap)
        rows_d.append(dict(
            crop=crop, n_country_steps=int(desired.size),
            frac_steps_cap_binds=float(bind.mean()),
            mmt_desired=float(desired.sum()),
            mmt_unconsumed_by_cap=float(shortfall.sum()),
            pct_of_desired=100.0 * float(shortfall.sum() / desired.sum()),
            max_country_frac=float(bind.mean(axis=1).max()),
            worst_country=countries[int(np.argmax(bind.mean(axis=1)))],
        ))

        # ---------- (c) is the short side a clearing rule? ----------
        off = res.offers.sum(axis=0)
        dem = res.purchase_demand.sum(axis=0)
        got = res.received.sum(axis=0)
        unmet = np.maximum(0.0, dem - got)
        slack = off >= dem - 1e-9          # world supply on offer covers demand
        rows_c.append(dict(
            crop=crop, T=T,
            steps_offers_cover_demand=int(slack.sum()),
            steps_offers_cover_but_unmet=int(
                np.sum(slack & (unmet > 1e-6 * np.maximum(dem, 1e-9)))),
            mean_unmet_frac_when_covered=float(
                np.mean((unmet / np.maximum(dem, 1e-9))[slack])
                if slack.any() else np.nan),
            mean_unmet_frac_all=float(np.mean(unmet / np.maximum(dem, 1e-9))),
            mmt_offers_unshipped=float(np.sum(off - res.exports.sum(axis=0))),
            mmt_demand_unmet=float(unmet.sum()),
        ))

        # ---------- (a) budget-constraint counterfactual ----------
        # Peak = the 3-step window with the highest simulated price in 2007/08.
        t_peak = int(np.argmax(res.price[: 3 * 24]))
        ph_peak = float(res.price[t_peak] / p0)
        sheaf_ratio_peak = ph_peak ** elast
        for a in A_GRID:
            r = float(agri_ratio(ph_peak, a))
            rows_a.append(dict(
                crop=crop, a_star=a, eps_c=EPS_C, sheaf_elast=elast,
                t_peak=t_peak, p_peak_over_p0=ph_peak,
                sheaf_demand_ratio=sheaf_ratio_peak,
                agrimate_demand_ratio=r,
                extra_destruction_pp=100.0 * (sheaf_ratio_peak - r),
                implied_elast_at_peak=float(
                    -(EPS_C + (a * ph_peak ** (1 - EPS_C)
                              / (1 + a * (ph_peak ** (1 - EPS_C) - 1)))
                      * (1 - EPS_C))),
                # world flex MMT foregone in that step
                world_flex_mmt_step=float(flex[:, t_peak].sum()),
                mmt_gap_at_peak=float(
                    flex[:, t_peak].sum() * (sheaf_ratio_peak - r)),
            ))

        # per-country, over the 2007/08 hike window (steps for 2007-06..2008-06)
        t0 = (2007 - 2006) * 24 + (6 - 1) * 2
        t1 = (2008 - 2006) * 24 + (6 - 1) * 2 + 2
        ph_win = p_hat[t0:t1]
        for i, c in enumerate(countries):
            f = flex[i, t0:t1]
            if f.sum() <= 1e-9:
                continue
            sheaf_q = f * ph_win ** elast
            row = dict(crop=crop, country=c,
                       flex_mmt_window=float(f.sum()),
                       ind_mmt_window=float(ind[i, t0:t1].sum()),
                       sheaf_mmt=float(sheaf_q.sum()),
                       mean_p_hat=float(ph_win.mean()))
            for a in A_GRID:
                q = f * agri_ratio(ph_win, a)
                row[f"agri_mmt_A{a:.2f}"] = float(q.sum())
                row[f"gap_mmt_A{a:.2f}"] = float(sheaf_q.sum() - q.sum())
                row[f"gap_pct_A{a:.2f}"] = 100.0 * float(
                    (sheaf_q.sum() - q.sum()) / sheaf_q.sum())
            rows_ctry.append(row)

    for name, rows in (("r2_a_budget_peak.csv", rows_a),
                       ("r2_c_rationing.csv", rows_c),
                       ("r2_d_storage_cap.csv", rows_d),
                       ("r2_a_budget_country.csv", rows_ctry)):
        pd.DataFrame(rows).to_csv(OUT / name, index=False)

    print("== (d) availability / storage cap ==")
    print(pd.DataFrame(rows_d).to_string(index=False))
    print("\n== (c) short-side rationing ==")
    print(pd.DataFrame(rows_c).to_string(index=False))
    print("\n== (a) budget constraint at the simulated 2007/08 peak ==")
    print(pd.DataFrame(rows_a).to_string(index=False))
    print("\n== (a) per-country, 2007-06..2008-06, A*=0.20 ==")
    d = pd.DataFrame(rows_ctry)
    for crop in CROPS:
        s = d[d.crop == crop].sort_values("gap_mmt_A0.20", ascending=False)
        print(f"\n{crop}:")
        print(s[["country", "flex_mmt_window", "sheaf_mmt",
                 "agri_mmt_A0.20", "gap_mmt_A0.20", "gap_pct_A0.20"]]
              .head(8).to_string(index=False))


if __name__ == "__main__":
    main()
