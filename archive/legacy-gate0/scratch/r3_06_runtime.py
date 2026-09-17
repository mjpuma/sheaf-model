#!/usr/bin/env python3
"""R3-06: runtime cost of the R3 prototypes (complexity-budget input)."""
from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "scratch"))

from r3_02_prototypes import build  # noqa: E402

OUT = ROOT / "diagnostics" / "redteam" / "r3"
P1 = dict(use_amis=True, use_shocks=True, use_demand=False)
CROPS = ("wheat", "maize", "rice")


def main() -> None:
    rows = []
    for name, kw in (("V0_baseline", {}), ("V1_agrimate_exp", dict(agri_exp=True)),
                     ("V3_pre_update_ask", dict(pre_ask=True))):
        mod = build(f"dc_rt_{name.split('_')[0].lower()}", **kw)
        mod.run_crop_dynamics("wheat", **P1)  # warm the data caches
        best = min(_timed(mod) for _ in range(3))
        rows.append(dict(variant=name, best_3crop_seconds=best))
        print(f"{name}: best-of-3 three-crop run {best:.3f} s")
    df = pd.DataFrame(rows)
    b = float(df.loc[df.variant == "V0_baseline", "best_3crop_seconds"].iloc[0])
    df["pct_vs_V0"] = 100.0 * (df.best_3crop_seconds / b - 1.0)
    df.to_csv(OUT / "r3_runtime.csv", index=False)
    print(df.to_string(index=False))


def _timed(mod) -> float:
    t0 = time.perf_counter()
    for crop in CROPS:
        mod.run_crop_dynamics(crop, **P1)
    return time.perf_counter() - t0


if __name__ == "__main__":
    main()
