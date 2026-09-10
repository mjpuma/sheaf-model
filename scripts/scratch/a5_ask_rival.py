#!/usr/bin/env python3
"""A5 support: assertion cross-check + ask_rival sign-condition sweep.

1. Run the four *library* assertions unmodified at baseline for all three
   crops, to show the transcriptions in a5_ablation.py agree where they can
   be compared (defaults).
2. Sweep `ask_rival` and record the isolated-tau price lift in each crop's
   primary ban window (the statistic assert_amis_raises_price tests). The
   CropParams docstring (L118-121) claims 0.80 is the smallest shared value
   at which isolated maize tau does not cut world price, and that 0.40
   still cuts. This measures that claim. It is NOT a retune.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from sheaf.calendar24 import STEPS_PER_YEAR  # noqa: E402
from sheaf.dynamic_crop import (  # noqa: E402
    assert_amis_cuts_exports,
    assert_amis_raises_price,
    assert_no_spring_spike,
    assert_twin_identity,
    run_crop_dynamics,
)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from a5_ablation import CROPS, END, OUT, START  # noqa: E402

print("=== 1. library assertions at baseline (unmodified) ===")
for crop in CROPS:
    for fn in (assert_twin_identity, assert_amis_raises_price,
               assert_no_spring_spike, assert_amis_cuts_exports):
        try:
            fn(crop)
            print(f"  {crop:6s} {fn.__name__:26s} PASS")
        except AssertionError as e:
            print(f"  {crop:6s} {fn.__name__:26s} FAIL: {e}")

_WIN = {"wheat": (2010, 8, 2010, 12, 0.05),
        "rice": (2008, 1, 2008, 6, 0.05),
        "maize": (2007, 5, 2008, 6, 0.0)}

print("\n=== 2. ask_rival sweep: isolated-tau lift in the assert window ===")
rows = []
grid = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 1.0, 1.2]
for crop in CROPS:
    y0, m0, y1, m1, floor = _WIN[crop]
    for v in grid:
        tau = run_crop_dynamics(crop, start_year=START, end_year=END,
                                use_amis=True, use_shocks=False,
                                use_demand=False, use_industrial=False,
                                ask_rival=v)
        base = run_crop_dynamics(crop, start_year=START, end_year=END,
                                 use_amis=False, use_shocks=False,
                                 use_demand=False, use_industrial=False,
                                 ask_rival=v)
        t0 = (y0 - tau.start_year) * STEPS_PER_YEAR + (m0 - 1) * 2
        t1 = (y1 - tau.start_year) * STEPS_PER_YEAR + (m1 - 1) * 2 + 2
        p_tau = float(np.mean(tau.price[t0:t1]))
        p_base = float(np.mean(base.price[t0:t1]))
        lift = p_tau / max(p_base, 1e-9) - 1.0
        rows.append(dict(crop=crop, ask_rival=v, p_tau=p_tau, p_base=p_base,
                         lift=lift, floor=floor, passes=lift >= floor))
        print(f"  {crop:6s} ask_rival={v:.1f}  lift={lift:+.4f}  "
              f"floor={floor:+.2f}  {'PASS' if lift >= floor else 'FAIL'}")
df = pd.DataFrame(rows)
df.to_csv(OUT / "ask_rival_sweep.csv", index=False)
print(f"\nwrote {OUT / 'ask_rival_sweep.csv'}")

for crop in CROPS:
    s = df[df.crop == crop]
    ok = s[s.passes]
    thr = ok.ask_rival.min() if len(ok) else float("nan")
    print(f"  {crop}: smallest swept ask_rival that passes = {thr}")

print("\n=== 3. fine maize threshold (0.70-0.82) ===")
fine = []
for v in [0.70, 0.72, 0.74, 0.75, 0.76, 0.78, 0.80, 0.82]:
    tau = run_crop_dynamics("maize", start_year=START, end_year=END,
                            use_amis=True, use_shocks=False, use_demand=False,
                            use_industrial=False, ask_rival=v)
    base = run_crop_dynamics("maize", start_year=START, end_year=END,
                             use_amis=False, use_shocks=False,
                             use_demand=False, use_industrial=False,
                             ask_rival=v)
    t0 = (2007 - 2006) * STEPS_PER_YEAR + (5 - 1) * 2
    t1 = (2008 - 2006) * STEPS_PER_YEAR + (6 - 1) * 2 + 2
    lift = float(np.mean(tau.price[t0:t1])) / float(np.mean(base.price[t0:t1])) - 1.0
    fine.append(dict(crop="maize", ask_rival=v, lift=lift, passes=lift >= 0.0))
    print(f"  maize ask_rival={v:.2f} lift={lift:+.5f} "
          f"{'PASS' if lift >= 0 else 'FAIL'}")
pd.DataFrame(fine).to_csv(OUT / "ask_rival_fine_maize.csv", index=False)
