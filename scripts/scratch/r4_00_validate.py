#!/usr/bin/env python3
"""R4 step 0 — verify the replica and reproduce the published baselines."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

import r4_lib as L

OUT = Path(__file__).resolve().parents[2] / "diagnostics" / "redteam" / "r4"
OUT.mkdir(parents=True, exist_ok=True)


def main():
    rows = []
    for crop in L.CROPS:
        v = L.verify_replica(crop, use_amis=True, use_shocks=True,
                             use_demand=False)
        prep, out = L.official_price(crop)
        s = L.score(out["price"], crop)
        c0, h07_0, h10_0 = L.SHIPPED[crop]
        noop = L.reweight_is_noop(prep)
        v.pop("crop", None)
        rows.append(dict(crop=crop, **v, corr=s["corr"], h0708=s["h0708"],
                         h1011=s["h1011"], ref_corr=c0, ref_h0708=h07_0,
                         ref_h1011=h10_0,
                         d_corr=s["corr"] - c0, d_h0708=s["h0708"] - h07_0,
                         d_h1011=s["h1011"] - h10_0,
                         reweight_max_abs_dev=noop))
        print(f"{crop}: replica dp={v['d_price']:.3e} dtrade={v['d_trade']:.3e} "
              f"| corr {s['corr']:+.3f} (ref {c0:+.3f})  "
              f"07/08 x{s['h0708']:.2f} (ref x{h07_0:.2f})  "
              f"10/11 x{s['h1011']:.2f} (ref x{h10_0:.2f})  "
              f"| A-reweight max|dev| = {noop:.3e}")
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "r4_00_validate.csv", index=False)
    print(f"\nwrote {OUT / 'r4_00_validate.csv'}")


if __name__ == "__main__":
    main()
