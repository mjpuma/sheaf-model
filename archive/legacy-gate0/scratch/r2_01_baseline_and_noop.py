#!/usr/bin/env python3
"""R2 step 1: (i) reproduce the published Gate 0 scores to validate the
harness; (ii) test whether ``_ask_reweight_dest`` actually reweights anything.

Question (b) of the R2 brief asks whether SHEAF's "Armington with offer-price
reweighting" is equivalent to Agrimate's CES purchaser problem (Eq. 8c /
D.30a). Agrimate reweights the purchaser's *source* shares a_{r,s} by the
*suppliers'* offer prices. SHEAF's ``_ask_reweight_dest`` multiplies row i of
the exporter->destination matrix A by a scalar that depends only on i, then
renormalises the row. Algebraically that is the identity on any row-stochastic
A. This script checks that claim numerically and then confirms it end-to-end
by sweeping ``ask_comp_elast``.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from r2_lib import CROPS, OUT, load_variant, official_scores


def main() -> None:
    base = load_variant("r2base")
    out = []

    # ---- (i) algebraic no-op check on the real A matrices -----------------
    print("== _ask_reweight_dest identity check ==")
    rows = []
    for crop in CROPS:
        prep = base.prepare_crop_run(crop, use_amis=True, use_shocks=True,
                                     use_demand=False)
        A = prep.A
        rowsum = A.sum(axis=1)
        n = A.shape[0]
        rng = np.random.default_rng(0)
        worst = 0.0
        for _ in range(200):
            ask = prep.p0 * np.exp(rng.normal(0, 0.5, n))
            A_eff = base._ask_reweight_dest(A, ask, prep.p0, gamma=1.25)
            worst = max(worst, float(np.max(np.abs(A_eff - A))))
        # extreme gamma
        for g in (0.0, 1.25, 8.0):
            ask = prep.p0 * np.linspace(0.4, 2.8, n)
            A_eff = base._ask_reweight_dest(A, ask, prep.p0, gamma=g)
            worst = max(worst, float(np.max(np.abs(A_eff - A))))
        rows.append(dict(crop=crop, n_nodes=n,
                         n_rows_sum_to_1=int(np.sum(np.abs(rowsum - 1) < 1e-12)),
                         n_rows_zero=int(np.sum(rowsum < 1e-15)),
                         max_abs_A_eff_minus_A=worst))
        print(f"  {crop}: max|A_eff - A| over 203 ask draws = {worst:.3e} "
              f"(rows summing to 1: {rows[-1]['n_rows_sum_to_1']}/{n}, "
              f"zero rows: {rows[-1]['n_rows_zero']})")
    pd.DataFrame(rows).to_csv(OUT / "r2_ask_reweight_noop.csv", index=False)

    # ---- (ii) end-to-end: does ask_comp_elast move any score? -------------
    print("\n== official scores; ask_comp_elast sweep ==")
    recs = []
    for crop in CROPS:
        for g in (0.0, 1.25, 8.0):
            s = official_scores(base, crop, ask_comp_elast=g)
            recs.append(dict(crop=crop, ask_comp_elast=g, corr=s["corr"],
                             hike0708=s["hike0708"], hike1011=s["hike1011"],
                             price_sum=float(np.sum(s["res"].price))))
            print(f"  {crop:6s} gamma={g:4.2f}  corr={s['corr']:+.4f}  "
                  f"h07=x{s['hike0708']:.3f}  h10=x{s['hike1011']:.3f}  "
                  f"sum(p)={recs[-1]['price_sum']:.6f}")
    df = pd.DataFrame(recs)
    df.to_csv(OUT / "r2_ask_comp_elast_sweep.csv", index=False)

    print("\n== baseline reproduction (gamma = 1.25, shipped defaults) ==")
    for crop in CROPS:
        r = df[(df.crop == crop) & (df.ask_comp_elast == 1.25)].iloc[0]
        print(f"  {crop:6s} corr={r.corr:+.3f}  h07=x{r.hike0708:.2f}  "
              f"h10=x{r.hike1011:.2f}")


if __name__ == "__main__":
    main()
