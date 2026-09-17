#!/usr/bin/env python3
"""R4 — the identity-map claim, worked in situ, plus its numerical shadow.

Claim under test (raised by a parallel seam): `_ask_reweight_dest` is a
bit-for-bit identity map, therefore `ask_comp_elast` does nothing.

Step 4 of the protocol (counterexample) and step 5 (prove it correct) are
both run here:

  A. ALGEBRAIC. Prove A_eff == A whenever rows of A sum to 1, and find the
     only two ways the function can fail to be the identity (a zero row, and
     a row that does not sum to 1). Check both against the shipped matrices.
  B. IN SITU. Delete the call entirely (alloc_mode="nodest") and compare the
     whole 144-step price path bitwise against HEAD.
  C. CONSEQUENCE. The claim's *conclusion* ("ask_comp_elast does nothing")
     is about the model, not the function. Measured separately in r4_04.
  D. AMPLIFICATION. r4_04 found the pre-CES path is not exactly flat in
     sigma even though the only sigma channel there is the identity map.
     Measure how far a 1-ulp perturbation travels in 144 steps.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

import r4_lib as L
from sheaf.dynamic_crop import _ask_reweight_dest, prepare_crop_run

OUT = Path(__file__).resolve().parents[2] / "diagnostics" / "redteam" / "r4"
OUT.mkdir(parents=True, exist_ok=True)


def algebraic() -> pd.DataFrame:
    """A — where can the identity break?"""
    rows = []
    for crop in L.CROPS:
        prep = prepare_crop_run(crop, use_amis=False, use_shocks=False,
                                use_demand=False, use_industrial=False)
        A = prep.A
        rs = A.sum(axis=1)
        # the two structural exceptions
        zero_rows = np.where(rs < 1e-15)[0]
        offunit = np.where((rs > 1e-15) & (np.abs(rs - 1.0) > 1e-12))[0]
        # a hand-built counterexample: an A whose rows do NOT sum to 1
        B = A * 2.0
        ask = np.linspace(0.5, 2.0, A.shape[0]) * prep.p0
        devB = float(np.max(np.abs(
            _ask_reweight_dest(B, ask, prep.p0, gamma=1.25) - B)))
        rows.append(dict(
            crop=crop, n=A.shape[0],
            n_zero_rows=len(zero_rows),
            zero_rows=";".join(prep.countries[i] for i in zero_rows),
            n_rows_off_unit=len(offunit),
            dev_on_shipped_A=float(np.max(np.abs(
                _ask_reweight_dest(A, ask, prep.p0, gamma=1.25) - A))),
            dev_on_unnormalised_A=devB))
    return pd.DataFrame(rows)


def in_situ() -> pd.DataFrame:
    """B — delete the call and compare the whole simulated path."""
    rows = []
    for crop in L.CROPS:
        prep = prepare_crop_run(crop, use_amis=True, use_shocks=True,
                                use_demand=False)
        base = L.run_prep(prep, alloc_mode="shipped")
        tw_n = L.retwin(prep, alloc_mode="nodest")
        nod = L.run_prep(prep, twin=tw_n, alloc_mode="nodest")
        s_b, s_n = L.score(base["price"], crop), L.score(nod["price"], crop)
        d = np.abs(base["price"] - nod["price"])
        rows.append(dict(
            crop=crop,
            max_abs_dprice=float(d.max()),
            max_rel_dprice=float((d / np.maximum(base["price"], 1e-9)).max()),
            n_steps_bit_identical=int(np.sum(d == 0.0)),
            n_steps=len(d),
            max_abs_dtrade=float(np.max(np.abs(base["trade"] - nod["trade"]))),
            corr_shipped=s_b["corr"], corr_nodest=s_n["corr"],
            h0708_shipped=s_b["h0708"], h0708_nodest=s_n["h0708"],
            h1011_shipped=s_b["h1011"], h1011_nodest=s_n["h1011"]))
    return pd.DataFrame(rows)


def amplification() -> pd.DataFrame:
    """D — how far does one ulp travel in 144 steps?

    Perturb the initial stock vector by one relative ulp and follow the
    divergence of the price path. This bounds how much of the r4_04 `nosrc`
    sigma-dependence is real economics (none: the channel is the identity)
    and how much is round-off amplified by the map.
    """
    rows = []
    for crop in L.CROPS:
        prep = prepare_crop_run(crop, use_amis=True, use_shocks=True,
                                use_demand=False)
        base = L.run_prep(prep)
        eps = np.finfo(float).eps
        prep2 = prepare_crop_run(crop, use_amis=True, use_shocks=True,
                                 use_demand=False)
        prep2.stock0[:] = prep2.stock0 * (1.0 + eps)
        pert = L.run_prep(prep2)
        d = np.abs(base["price"] - pert["price"])
        rel = d / np.maximum(base["price"], 1e-9)
        first = int(np.argmax(rel > 1e-12)) if (rel > 1e-12).any() else -1
        s_b, s_p = L.score(base["price"], crop), L.score(pert["price"], crop)
        rows.append(dict(
            crop=crop, perturbation_rel=float(eps),
            max_rel_dprice=float(rel.max()),
            amplification=float(rel.max() / eps),
            first_step_rel_gt_1e12=first,
            d_corr=s_p["corr"] - s_b["corr"],
            d_h0708=s_p["h0708"] - s_b["h0708"],
            d_h1011=s_p["h1011"] - s_b["h1011"]))
    return pd.DataFrame(rows)


def main():
    print("=== A. algebraic: where can the identity break? ===")
    a = algebraic()
    a.to_csv(OUT / "r4_05_identity_algebraic.csv", index=False)
    print(a.to_string(index=False))

    print("\n=== B. in situ: delete the call, compare the whole path ===")
    b = in_situ()
    b.to_csv(OUT / "r4_05_identity_insitu.csv", index=False)
    print(b.to_string(index=False, float_format=lambda x: f"{x:.4g}"))

    print("\n=== D. one-ulp amplification over 144 steps ===")
    d = amplification()
    d.to_csv(OUT / "r4_05_amplification.csv", index=False)
    print(d.to_string(index=False, float_format=lambda x: f"{x:.4g}"))
    print(f"\nwrote CSVs to {OUT}")


if __name__ == "__main__":
    main()
