#!/usr/bin/env python3
"""R4 step 0 (redone at HEAD) — replica parity + the identity-map verdict.

The inherited R4 CSVs were produced before two baseline moves (d4830c8 R0
scarcity bound; 929cec4 CES origin competition). This script

  (i)  re-verifies the r4_lib replica against the *current* `_simulate_window`
       to machine precision on all three crops,
  (ii) reproduces the current official scores,
  (iii) works the verification protocol on the claim that `_ask_reweight_dest`
       is a bit-for-bit identity map, and on the *consequence* claim that
       `ask_comp_elast` therefore does nothing. Those are separate claims and
       at HEAD they have different answers.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

import r4_lib as L
from sheaf.dynamic_crop import (
    _ask_reweight_dest,
    _ask_reweight_src,
    prepare_crop_run,
    run_crop_dynamics,
)

OUT = Path(__file__).resolve().parents[2] / "diagnostics" / "redteam" / "r4"
OUT.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------------------------
# (i)/(ii) replica parity and current official scores
# --------------------------------------------------------------------------
def validate() -> pd.DataFrame:
    rows = []
    for crop in L.CROPS:
        v = L.verify_replica(crop, use_amis=True, use_shocks=True,
                             use_demand=False)
        prep, out = L.official_price(crop)
        s = L.score(out["price"], crop)
        c0, h07, h10 = L.SHIPPED[crop]
        v.pop("crop", None)
        rows.append(dict(crop=crop, **v, corr=s["corr"], h0708=s["h0708"],
                         h1011=s["h1011"], ref_corr=c0, ref_h0708=h07,
                         ref_h1011=h10, d_corr=s["corr"] - c0,
                         d_h0708=s["h0708"] - h07, d_h1011=s["h1011"] - h10))
        print(f"{crop:5s}: replica dp={v['d_price']:.3e} "
              f"dtrade={v['d_trade']:.3e} dstock={v['d_stock']:.3e} | "
              f"corr {s['corr']:+.4f} (ref {c0:+.3f})  "
              f"07/08 x{s['h0708']:.3f} (ref x{h07:.2f})  "
              f"10/11 x{s['h1011']:.3f} (ref x{h10:.2f})")
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------
# (iii) the identity-map claim, worked as two separate claims
# --------------------------------------------------------------------------
def identity_map() -> pd.DataFrame:
    """Claim 1a: `_ask_reweight_dest(A, ask) == A` exactly.
    Claim 1b: therefore `ask_comp_elast` is inert.
    """
    rng = np.random.default_rng(7)
    rows = []
    for crop in L.CROPS:
        prep = prepare_crop_run(crop, use_amis=False, use_shocks=False,
                                use_demand=False, use_industrial=False)
        n = prep.A.shape[0]
        # 1a — adversarial ask vectors, including the clip bounds the model
        # can actually reach (0.45*p0 .. 2.8*p0) and extreme gammas.
        dev_dest, dev_src = 0.0, 0.0
        for gamma in (0.0, 0.25, 1.25, 4.0, 8.0, 20.0):
            for _ in range(40):
                ask = prep.p0 * np.exp(rng.normal(0, 1.2, size=n))
                ask = np.clip(ask, 0.45 * prep.p0, 2.8 * prep.p0)
                dev_dest = max(dev_dest, float(np.max(np.abs(
                    _ask_reweight_dest(prep.A, ask, prep.p0, gamma=gamma)
                    - prep.A))))
                dev_src = max(dev_src, float(np.max(np.abs(
                    _ask_reweight_src(prep.S, ask, prep.p0, gamma=gamma)
                    - prep.S))))
        rowsum = prep.A.sum(axis=1)
        colsum = prep.S.sum(axis=0)
        rows.append(dict(
            crop=crop, n_nodes=n,
            A_rows_sum_to_1=int(np.sum(np.abs(rowsum - 1.0) < 1e-12)),
            A_rows_zero=int(np.sum(rowsum < 1e-15)),
            S_cols_sum_to_1=int(np.sum(np.abs(colsum - 1.0) < 1e-12)),
            max_abs_dest_dev=dev_dest,
            max_abs_src_dev=dev_src,
            eps_machine=float(np.finfo(float).eps)))
    return pd.DataFrame(rows)


def sigma_sweep() -> pd.DataFrame:
    """Claim 1b, executed: does `ask_comp_elast` move the official scores?

    Run at HEAD (dest no-op + live source CES) and under `alloc_mode="nosrc"`
    (the pre-929cec4 code path, destination reweight only). If the consequence
    claim were true at HEAD, both rows would be flat in sigma.
    """
    rows = []
    for crop in L.CROPS:
        for sigma in (0.0, 0.5, 1.25, 3.0, 8.0):
            # HEAD path, through the shipped entry point (no replica involved)
            res = run_crop_dynamics(crop, use_amis=True, use_shocks=True,
                                    use_demand=False, ask_comp_elast=sigma)
            s_head = L.score(res.price, crop)
            # pre-CES path, through the replica
            prep = prepare_crop_run(crop, use_amis=True, use_shocks=True,
                                    use_demand=False, ask_comp_elast=sigma)
            tw = L.retwin(prep, alloc_mode="nosrc")
            out = L.run_prep(prep, twin=tw, alloc_mode="nosrc")
            s_nos = L.score(out["price"], crop)
            rows.append(dict(crop=crop, ask_comp_elast=sigma,
                             head_corr=s_head["corr"],
                             head_h0708=s_head["h0708"],
                             head_h1011=s_head["h1011"],
                             nosrc_corr=s_nos["corr"],
                             nosrc_h0708=s_nos["h0708"],
                             nosrc_h1011=s_nos["h1011"]))
    return pd.DataFrame(rows)


def main():
    print("=== (i)/(ii) replica parity vs HEAD + official scores ===")
    v = validate()
    v.to_csv(OUT / "r4_04_validate.csv", index=False)

    print("\n=== (iii-a) reweight algebra: dest vs src ===")
    idm = identity_map()
    idm.to_csv(OUT / "r4_04_identity_map.csv", index=False)
    print(idm.to_string(index=False))

    print("\n=== (iii-b) ask_comp_elast sweep: HEAD vs pre-CES path ===")
    sw = sigma_sweep()
    sw.to_csv(OUT / "r4_04_sigma_sweep.csv", index=False)
    print(sw.to_string(index=False, float_format=lambda x: f"{x:.4f}"))
    print(f"\nwrote CSVs to {OUT}")


if __name__ == "__main__":
    main()
