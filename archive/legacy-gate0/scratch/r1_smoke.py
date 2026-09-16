#!/usr/bin/env python3
"""R1 smoke test: does the FOC patch run, and what does the calm run do?"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from r1_foc_core import (  # noqa: E402
    CALM_KW, CROPS, build, calibrate_refs, default_R1,
)

from sheaf.calendar24 import STEPS_PER_YEAR  # noqa: E402


def drift(price, p0):
    tail = price[STEPS_PER_YEAR:]
    return (float(np.max(np.abs(tail - p0)) / p0),
            float(abs(np.mean(tail) - p0) / p0),
            float((np.max(tail) - np.min(tail)) / p0))


def main():
    mech_on = build(calm=True, foc=False)
    mech_off = build(calm=False, foc=False)
    for crop in CROPS:
        t0 = time.time()
        R1 = default_R1(crop)
        foc_on = build(calm=True, foc=True, R1=R1)
        foc_off = build(calm=False, foc=True, R1=R1)
        hist = calibrate_refs(crop, R1, mech_on, foc_on, "scalar",
                              iters=5, verbose=True)
        b = mech_off.run_crop_dynamics(crop, **CALM_KW)
        p0 = float(mech_on.run_crop_dynamics(crop, **CALM_KW).price[0])
        R1["_trace"] = []
        f = foc_off.run_crop_dynamics(crop, **CALM_KW)
        tr = np.array(R1["_trace"], float)[-len(f.price):]
        print(f"{crop}: p0={p0:.1f}  alpha={R1['alpha']}  X*={hist[-1]:.3f}")
        print(f"  mech calm-off drift max/mean/amp: "
              f"{drift(b.price, p0)[0]:.3%} / {drift(b.price, p0)[1]:.3%} / "
              f"{drift(b.price, p0)[2]:.3%}")
        print(f"  FOC  calm-off drift max/mean/amp: "
              f"{drift(f.price, p0)[0]:.3%} / {drift(f.price, p0)[1]:.3%} / "
              f"{drift(f.price, p0)[2]:.3%}")
        print(f"  offers held back: mean x/xbar = "
              f"{tr[:, 1].sum() / max(tr[:, 0].sum(), 1e-9):.3f}, "
              f"corner frac = {tr[:, 2].mean():.3f}")
        print(f"  clip binding frac = {np.mean(R1.get('_clip', [0])):.4f}")
        print(f"  wall {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
