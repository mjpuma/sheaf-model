#!/usr/bin/env python3
"""A5 support checks (read-only).

1. Overrides land. `prepare_crop_run` silently drops any keyword that is not
   a CropParams field (L720-724), so confirm each ablation is actually in
   `res.params`, and show what happens to a deliberate typo.
2. The calm twin is rebuilt per ablation. L803-806 simulates `free_twin`
   with the same `params`, so a CropParams override moves the twin as well
   as the treatment path -- meaning a prep cannot be reused across
   ablations. Measure how far the twin moves.
3. Fine-grained per-crop delta scan for near-inert channels.
"""
from __future__ import annotations

import sys
from dataclasses import fields
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from sheaf.dynamic_crop import (  # noqa: E402
    CropParams,
    prepare_crop_run,
    run_crop_dynamics,
)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from a5_ablation import ABLATIONS, CROPS, END, OUT, START  # noqa: E402

print("=== 1. override landing ===")
for lab, ov in ABLATIONS:
    if not ov:
        continue
    res = run_crop_dynamics("wheat", start_year=START, end_year=END,
                            use_amis=True, use_shocks=True, use_demand=False,
                            **ov)
    ok = all(getattr(res.params, k) == v for k, v in ov.items())
    print(f"  {lab:20s} landed={ok}  "
          + " ".join(f"{k}={getattr(res.params, k)}" for k in ov))

names = {f.name for f in fields(CropParams)}
print(f"  CropParams fields: {len(names)}; all ablation keys present: "
      f"{all(k in names for _, ov in ABLATIONS for k in ov)}")
bad = run_crop_dynamics("wheat", start_year=START, end_year=END,
                        use_amis=True, use_shocks=True, use_demand=False,
                        trade_weight=1.0)
ref = run_crop_dynamics("wheat", start_year=START, end_year=END,
                        use_amis=True, use_shocks=True, use_demand=False)
print(f"  typo 'trade_weight=1.0' silently ignored (identical to baseline): "
      f"{np.allclose(bad.price, ref.price)}  -- no error raised")

print("\n=== 2. does an ablation move the calm twin? ===")
rows = []
for crop in CROPS:
    p_base = prepare_crop_run(crop, start_year=START, end_year=END,
                              use_amis=True, use_shocks=True,
                              use_demand=False)
    for lab, ov in ABLATIONS:
        if not ov:
            continue
        p = prepare_crop_run(crop, start_year=START, end_year=END,
                             use_amis=True, use_shocks=True,
                             use_demand=False, **ov)
        d_free = float(np.max(np.abs(p.free_twin - p_base.free_twin)))
        d_unmet = float(np.max(np.abs(p.unmet_twin - p_base.unmet_twin)))
        d_H = float(np.max(np.abs(p.H - p_base.H)))
        d_cuts = float(np.max(np.abs(p.cuts - p_base.cuts)))
        rows.append(dict(crop=crop, ablation=lab, d_free_twin=d_free,
                         d_unmet_twin=d_unmet, d_H=d_H, d_cuts=d_cuts))
        print(f"  {crop:6s} {lab:20s} max|Δfree_twin|={d_free:.4g} "
              f"max|Δunmet_twin|={d_unmet:.4g} "
              f"(ΔH={d_H:.3g}, Δcuts={d_cuts:.3g})")
tw = pd.DataFrame(rows)
tw.to_csv(OUT / "twin_shift.csv", index=False)

print("\n=== 3. per-crop fine delta scan ===")
grid = pd.read_csv(OUT / "ablation_grid.csv")
keys = ["corr", "hike_2007_08", "hike_2010_11", "amis_lift", "offer_ratio",
        "ship_ratio", "spring_autumn", "twin_price_drift", "twin_free_err"]
base = grid[grid.ablation == "baseline"].set_index(["crop", "leg"])
out = []
for crop in CROPS:
    for lab, _ in ABLATIONS:
        if lab == "baseline":
            continue
        sub = grid[(grid.ablation == lab) & (grid.crop == crop)].set_index(
            ["crop", "leg"])
        b = base[base.index.get_level_values("crop") == crop]
        worst, wk = 0.0, ""
        for k in keys:
            d = (sub[k] - b[k]).abs().max()
            d = 0.0 if not np.isfinite(d) else float(d)
            if d > worst:
                worst, wk = d, k
        out.append(dict(crop=crop, ablation=lab, max_abs_delta=worst,
                        worst_metric=wk))
        print(f"  {crop:6s} {lab:20s} max|Δ|={worst:.4g} on {wk}")
pd.DataFrame(out).to_csv(OUT / "delta_scan.csv", index=False)
print(f"\nwrote {OUT / 'twin_shift.csv'}, {OUT / 'delta_scan.csv'}")
