#!/usr/bin/env python3
"""R1 step 2: is the FOC rest point absent, or present but unstable?

Three questions, in order.

(1) HARNESS IDENTITY. Variant A ("shipped ask law") routes through the R1
    patch with `foc=False, ask_law="shipped"`, which should reproduce
    `sheaf/dynamic_crop.py` line for line. `r1_00_validate.py` measured the
    unpatched calm-OFF drift for wheat at 26.12%; `r1_01_rescan.py` measured
    variant A at 23.79%. Either the patch is not the identity it claims to
    be, or one of the two harnesses is wrong. Settled here by comparing
    price paths directly.

(2) EXISTENCE OF THE REST POINT. Under
        ask_i = p0 * ((X_i + Q_oth_i) / X*) ^ (-alpha),  Q_oth_i = X* - x*_i
    the ask equals p0 exactly when X_i = x*_i. In a matched run the scarcity
    ratio is 1, so p_scar = p0, so p* = trade_w*p_trade + (1-trade_w)*p0 = p0.
    So p0 IS an algebraic fixed point of the R1 map whenever the reference
    equals the matched quantity path. Variant M sets the reference to that
    path step by step, and still drifts 70%/46%/62%. Checked here by
    evaluating the ask law's residual ON the reference path itself, which
    separates "no fixed point" from "fixed point not reached".

(3) STABILITY. If the fixed point exists, the drift must come from
    divergence away from it. Measured by seeding the calm-OFF run at the
    reference and tracking |p_t - p0| step by step, plus a one-step gain
    estimate d log(ask) / d log(p) around the rest point.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from r1_foc_core import (  # noqa: E402
    ALPHA_I, CALM_KW, CROPS, ROOT, build, calibrate_refs, default_R1, drift,
    priced_q, refs_from,
)

from sheaf import dynamic_crop as shipped  # noqa: E402
from sheaf.calendar24 import STEPS_PER_YEAR  # noqa: E402


def q1_identity():
    print("=" * 78)
    print("(1) harness identity: R1 patch with foc off, ask_law shipped")
    print("=" * 78)
    mech_off = build(calm=False, r1=False)
    rows = []
    for crop in CROPS:
        R1 = default_R1(crop, ask_law="shipped", foc=False, ref_mode="scalar",
                        rival_mode="ref", xstar=1.0, xref=np.ones(1))
        pat_off = build(calm=False, r1=True, R1=R1)
        a = mech_off.run_crop_dynamics(crop, **CALM_KW)
        b = pat_off.run_crop_dynamics(crop, **CALM_KW)
        p0 = float(build(calm=True, r1=False)
                   .run_crop_dynamics(crop, **CALM_KW).price[0])
        dp = float(np.max(np.abs(a.price - b.price)))
        do = float(np.max(np.abs(a.offers - b.offers)))
        rows.append(dict(crop=crop, max_abs_dprice=dp, max_abs_doffers=do,
                         drift_unpatched=drift(a.price, p0)[0],
                         drift_patched=drift(b.price, p0)[0]))
        print(f"  {crop:6s} max|dp| {dp:.3e}  max|d offers| {do:.3e}  "
              f"drift unpatched {rows[-1]['drift_unpatched']:.3%} vs "
              f"patched {rows[-1]['drift_patched']:.3%}")
    return pd.DataFrame(rows)


def q2_residual_on_reference():
    """Evaluate the R1 ask law ON the calibrated reference path.

    If ask == p0 to machine precision at the reference, the fixed point
    exists and the drift is a stability problem, not a specification one.
    """
    print("=" * 78)
    print("(2) ask-law residual evaluated on its own reference path")
    print("=" * 78)
    mech_on = build(calm=True, r1=False)
    rows = []
    for crop in CROPS:
        for mode, price_at in (("scalar", "offers"), ("scalar", "exports"),
                               ("path", "offers")):
            R1 = default_R1(crop, ask_law="foc", foc=True, price_at=price_at,
                            ref_mode=mode, rival_mode="ref")
            r1_on = build(calm=True, r1=True, R1=R1)
            hist = calibrate_refs(crop, R1, mech_on, r1_on, iters=8)
            res = r1_on.run_crop_dynamics(crop, **CALM_KW)
            X = priced_q(res, price_at)               # (n, T) at the ref
            p0 = float(res.price[0])
            alpha = float(R1["alpha"])
            n, T = X.shape
            err = np.zeros(T)
            for t in range(T):
                ix = t if mode == "path" else t % STEPS_PER_YEAR
                Rref = np.asarray(R1["xstar"], float)
                Rref = float(Rref) if Rref.ndim == 0 else float(
                    Rref[ix % Rref.shape[0]])
                xr = np.asarray(R1["xref"], float)
                xr = xr if xr.ndim == 1 else xr[:, ix % xr.shape[1]]
                q_oth = np.maximum(Rref - xr, 1e-9)
                ask = p0 * (np.maximum(X[:, t] + q_oth, 1e-12)
                            / max(Rref, 1e-9)) ** (-alpha)
                err[t] = float(np.max(np.abs(ask / p0 - 1.0)))
            rows.append(dict(crop=crop, ref_mode=mode, price_at=price_at,
                             max_ask_resid=float(err[STEPS_PER_YEAR:].max()),
                             med_ask_resid=float(np.median(err[STEPS_PER_YEAR:])),
                             xstar_conv=abs(hist[-1] / max(hist[-2], 1e-12) - 1)))
            print(f"  {crop:6s} ref={mode:6s} price_at={price_at:8s} "
                  f"max|ask/p0-1| on reference {rows[-1]['max_ask_resid']:.3e} "
                  f"median {rows[-1]['med_ask_resid']:.3e} "
                  f"(X* conv {rows[-1]['xstar_conv']:.2e})")
    return pd.DataFrame(rows)


def q3_divergence():
    print("=" * 78)
    print("(3) divergence away from the rest point, calm branch OFF")
    print("=" * 78)
    mech_on = build(calm=True, r1=False)
    rows = []
    for crop in CROPS:
        p0 = float(mech_on.run_crop_dynamics(crop, **CALM_KW).price[0])
        for label, mode, price_at in (("J", "scalar", "offers"),
                                      ("N", "scalar", "exports"),
                                      ("M", "path", "offers")):
            R1 = default_R1(crop, ask_law="foc", foc=True, price_at=price_at,
                            ref_mode=mode, rival_mode="ref")
            r1_on = build(calm=True, r1=True, R1=R1)
            r1_off = build(calm=False, r1=True, R1=R1)
            calibrate_refs(crop, R1, mech_on, r1_on, iters=8)
            res = r1_off.run_crop_dynamics(crop, **CALM_KW)
            d = np.abs(res.price - p0) / p0
            # geometric growth rate over the first two years
            seg = d[2:48]
            seg = seg[seg > 1e-14]
            g = (float(np.exp(np.polyfit(np.arange(len(seg)),
                                         np.log(seg), 1)[0])) if len(seg) > 8
                 else np.nan)
            rows.append(dict(crop=crop, variant=label,
                             d_t2=float(d[2]), d_t6=float(d[6]),
                             d_t12=float(d[12]), d_t24=float(d[24]),
                             d_t48=float(d[48]), d_max=float(d.max()),
                             growth_per_step=g))
            print(f"  {crop:6s} {label} |dp|/p0 at t=2,6,12,24,48: "
                  f"{d[2]:.2e} {d[6]:.2e} {d[12]:.2e} {d[24]:.2e} {d[48]:.2e} "
                  f"| fitted growth/step {g:.3f}")
    return pd.DataFrame(rows)


def main():
    d = ROOT / "diagnostics" / "redteam" / "r1"
    q1_identity().to_csv(d / "r1_identity.csv", index=False)
    q2_residual_on_reference().to_csv(d / "r1_ref_residual.csv", index=False)
    q3_divergence().to_csv(d / "r1_divergence.csv", index=False)
    print(f"\nwrote r1_identity.csv, r1_ref_residual.csv, r1_divergence.csv "
          f"in {d.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
