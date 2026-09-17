#!/usr/bin/env python3
"""R1 variant scan 2: consistent rival expectation.

Scan 1 mixed a slow EWMA rival expectation (Agrimate D.22, tau_exp = 0.5
N_year) with a seasonal reference X*_t.  That is internally inconsistent:
the EWMA drives Q_oth to its *annual mean* while X*_t moves seasonally, so
X_i + Q_oth is compared against the wrong denominator and the ask collapses
onto its clip.  Here Q_oth is instead set at the rivals' own reference level
(``rival_mode = "ref"``), which is the specification under which

    ask_i = p0 * ((X_i - x*_i + X*) / X*) ^ (-alpha)

has an exact rest point at p0 whenever X_i sits at its reference x*_i.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from r1_foc_core import (  # noqa: E402
    ALPHA_I, CALM_KW, CROPS, ROOT, build, calibrate_refs, default_R1, drift,
)

VARIANTS = [
    # label,                              price_at,  foc,   ref_mode, rival
    ("H  mech q, P(offers), X*_t, riv ref", "offers", False, "season", "ref"),
    ("I  FOC  q, P(offers), X*_t, riv ref", "offers", True,  "season", "ref"),
    ("J  FOC  q, P(offers), X* const, riv ref", "offers", True, "scalar", "ref"),
    ("K  mech q, P(exports), X*_t, riv ref", "exports", False, "season", "ref"),
    ("L  FOC  q, P(exports), X*_t, riv ref", "exports", True, "season", "ref"),
]


def main():
    mech_on = build(calm=True, r1=False)
    rows = []
    for crop in CROPS:
        p0 = float(mech_on.run_crop_dynamics(crop, **CALM_KW).price[0])
        for (label, price_at, foc, ref_mode, rival) in VARIANTS:
            t0 = time.time()
            R1 = default_R1(crop, ask_law="foc", price_at=price_at, foc=foc,
                            ref_mode=ref_mode, rival_mode=rival)
            r1_on = build(calm=True, r1=True, R1=R1)
            r1_off = build(calm=False, r1=True, R1=R1)
            hist = calibrate_refs(crop, R1, mech_on, r1_on, iters=6)
            R1["_trace"], R1["_clip"] = [], []
            res = r1_off.run_crop_dynamics(crop, **CALM_KW)
            T = len(res.price)
            tr = np.array(R1["_trace"], float)[-T:]
            mx, lvl, amp = drift(res.price, p0)
            rows.append(dict(
                crop=crop, variant=label, alpha=R1["alpha"],
                drift_max=mx, drift_level=lvl, drift_amp=amp,
                pass_2pct=(mx <= 0.02),
                hold_back=1.0 - tr[:, 1].sum() / max(tr[:, 0].sum(), 1e-9),
                corner_frac=float(tr[:, 2].mean()),
                clip_frac=float(np.mean(R1["_clip"][-T:]) if R1["_clip"] else 0.0),
                xstar_conv=abs(hist[-1] / max(hist[-2], 1e-12) - 1.0),
                secs=time.time() - t0))
            print(f"{crop:6s} {label:42s} max {mx:8.3%} lvl {lvl:7.3%} "
                  f"amp {amp:8.3%} hold {rows[-1]['hold_back']:5.2f} "
                  f"clip {rows[-1]['clip_frac']:5.2f} "
                  f"({time.time() - t0:.1f}s)")
    df = pd.DataFrame(rows)
    out = ROOT / "diagnostics" / "redteam" / "r1" / "r1_variant_scan2.csv"
    df.to_csv(out, index=False)
    print(f"\nwrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
