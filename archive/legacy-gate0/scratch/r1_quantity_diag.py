#!/usr/bin/env python3
"""R1 diagnostic: which Gate 0 quantity is Agrimate's X_I?

Agrimate prices at *sales* (Eq (5)/D.24: p_off = P(X_I), X_I = sales to the
international market), and its supplier sets p_off precisely so that incoming
demand equals its planned sales (Suppl. D.7.1.5 A).  In Gate 0, ``offers`` is
a capacity (surplus above cover) and ``exports`` is realised trade; the two
differ by the fill ratio, which A1b measured at 0.32-0.62 in a calm run.

An inverse-demand offer price p0*(X/X*)^-alpha only has a rest point at p0 if
X sits at X* in a calm market.  So: how seasonal / how stable are the
candidate X's on the calm path?
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from r1_foc_core import CALM_KW, CROPS, ROOT, build  # noqa: E402


def stats(v: np.ndarray) -> dict:
    v = np.asarray(v, float)
    ny = len(v) // 24
    blk = v[: ny * 24].reshape(ny, 24)
    seas = blk.mean(axis=0)
    m = float(v.mean())
    return dict(mean=m, cv=float(v.std() / max(m, 1e-12)),
                seas_cv=float(seas.std() / max(m, 1e-12)),
                p05=float(np.percentile(v, 5) / max(m, 1e-12)),
                p95=float(np.percentile(v, 95) / max(m, 1e-12)),
                seas_min=float(seas.min() / max(m, 1e-12)),
                seas_max=float(seas.max() / max(m, 1e-12)))


def main():
    mech = build(calm=True, foc=False)
    rows = []
    for crop in CROPS:
        res = mech.run_crop_dynamics(crop, **CALM_KW)
        for label, v in (("offers", res.offers.sum(axis=0)),
                         ("exports", res.exports.sum(axis=0)),
                         ("demand", res.purchase_demand.sum(axis=0))):
            rows.append(dict(crop=crop, quantity=label, **stats(v)))
        fill = res.exports.sum(axis=0) / np.maximum(res.offers.sum(axis=0), 1e-9)
        rows.append(dict(crop=crop, quantity="fill(world)", **stats(fill)))
    df = pd.DataFrame(rows)
    pd.set_option("display.width", 200)
    print(df.to_string(index=False, float_format=lambda x: f"{x:8.3f}"))
    out = ROOT / "diagnostics" / "redteam" / "r1" / "r1_calm_quantities.csv"
    df.to_csv(out, index=False)
    print(f"\nwrote {out.relative_to(ROOT)}")

    # what alpha-driven price amplitude does each candidate imply?
    print("\nimplied |log p| amplitude of p0*(X/X*)^-alpha on the calm path")
    print("(alpha from Agrimate Tbl D.8: wheat 3.5, maize 2.7, rice 2.2)")
    al = {"wheat": 3.5, "maize": 2.7, "rice": 2.2}
    for crop in CROPS:
        res = mech.run_crop_dynamics(crop, **CALM_KW)
        for label, v in (("offers", res.offers.sum(axis=0)),
                         ("exports", res.exports.sum(axis=0))):
            v = np.asarray(v, float)
            r = v / max(v.mean(), 1e-12)
            lp = -al[crop] * np.log(np.maximum(r, 1e-6))
            print(f"  {crop:6s} {label:8s} exp(range) = "
                  f"[{np.exp(lp.min()):7.3f}, {np.exp(lp.max()):8.3f}] x p0, "
                  f"sd(log p) = {lp.std():.3f}")


if __name__ == "__main__":
    main()
