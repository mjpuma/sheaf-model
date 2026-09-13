#!/usr/bin/env python3
"""R1 variant scan: the decisive calm test across candidate exporter laws.

THE DECISIVE TEST (task 3b): with the calm short-circuit in
``_simulate_window`` DISABLED, does a matched run (no harvest anomaly, no
AMIS, no demand shifter) hold at p0?  The shipped ask law fails this at
25 / 34 / 19 % (wheat / maize / rice), per diagnostics/gate0_prep/a1/.

Reported per variant: max |p - p0| / p0 (the assert_twin_identity metric,
tolerance 2 %), the mean level error, and the peak-to-trough amplitude --
because a smooth seasonal cycle centred on p0 is a different object from a
level drift, and the shipped law's failure is mostly a level failure.
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
    # label,                    ask_law, price_at,  foc,  ref_mode, alpha_mult
    ("A  shipped ask law",      "shipped", "offers", False, "scalar", 1.0),
    ("B  FOC q + P(offers), X* scalar", "foc", "offers", True, "scalar", 1.0),
    ("C  FOC q + P(offers), X* season", "foc", "offers", True, "season", 1.0),
    ("D  mech q + P(exports), X* season", "foc", "exports", False, "season", 1.0),
    ("E  FOC q + P(exports), X* season", "foc", "exports", True, "season", 1.0),
    ("F  mech q + P(offers), X* season", "foc", "offers", False, "season", 1.0),
    ("G  C with alpha/3.5 (~1.0)", "foc", "offers", True, "season", None),
]


def main():
    mech_on = build(calm=True, r1=False)
    rows = []
    for crop in CROPS:
        p0 = float(mech_on.run_crop_dynamics(crop, **CALM_KW).price[0])
        for (label, ask_law, price_at, foc, ref_mode, amul) in VARIANTS:
            t0 = time.time()
            alpha = (ALPHA_I[crop] * amul if amul is not None else 1.0)
            R1 = default_R1(crop, alpha=alpha, ask_law=ask_law,
                            price_at=price_at, foc=foc, ref_mode=ref_mode)
            r1_on = build(calm=True, r1=True, R1=R1)
            r1_off = build(calm=False, r1=True, R1=R1)
            hist = calibrate_refs(crop, R1, mech_on, r1_on, iters=6)
            R1["_trace"], R1["_clip"] = [], []
            res = r1_off.run_crop_dynamics(crop, **CALM_KW)
            T = len(res.price)
            tr = np.array(R1["_trace"], float)[-T:]
            mx, lvl, amp = drift(res.price, p0)
            q = (res.offers if price_at == "offers" else res.exports)
            qw = q.sum(axis=0)
            rows.append(dict(
                crop=crop, variant=label, alpha=alpha,
                drift_max=mx, drift_level=lvl, drift_amp=amp,
                pass_2pct=(mx <= 0.02),
                hold_back=1.0 - tr[:, 1].sum() / max(tr[:, 0].sum(), 1e-9),
                corner_frac=float(tr[:, 2].mean()),
                clip_frac=float(np.mean(R1["_clip"][-T:]) if R1["_clip"] else 0.0),
                q_cv=float(qw.std() / max(qw.mean(), 1e-12)),
                xstar_conv=abs(hist[-1] / max(hist[-2], 1e-12) - 1.0),
                secs=time.time() - t0))
            print(f"{crop:6s} {label:36s} max {mx:8.3%} lvl {lvl:7.3%} "
                  f"amp {amp:8.3%} hold {rows[-1]['hold_back']:5.2f} "
                  f"clip {rows[-1]['clip_frac']:5.2f} "
                  f"({time.time() - t0:.1f}s)")
    df = pd.DataFrame(rows)
    out = ROOT / "diagnostics" / "redteam" / "r1" / "r1_variant_scan.csv"
    df.to_csv(out, index=False)
    print(f"\nwrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
