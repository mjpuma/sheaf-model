#!/usr/bin/env python3
"""R1 step 0: re-validate the harness against the CURRENT Gate 0 baseline.

The baseline moved after the predecessor's scans were written: the scarcity
ratio is now bounded in the asymmetric `free < 0 <= twin` regime
(`sheaf/dynamic_crop.py` L704-717, R0f). Maize therefore moved
+0.712 -> +0.781 / x1.97 -> x2.22 / x1.70 -> x1.61, and any maize baseline in
`diagnostics/redteam/r1/r1_variant_scan*.csv` is stale.

This script checks three things before anything else is believed:
  1. the in-memory recompiled module (`r1_foc_core.build`) reproduces the
     scores of the *imported* `sheaf.dynamic_crop`, bit for bit;
  2. those scores match the published +0.720 / +0.781 / +0.678 headline;
  3. the calm short-circuit's own failure size (calm branch OFF, matched
     forcing) on the CURRENT tree, for all three crops.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from r1_foc_core import (  # noqa: E402
    CALM_KW, CROPS, FULL_KW, ROOT, build, drift,
)

from score_subannual_crop import _corr, _hike  # noqa: E402
from sheaf import dynamic_crop as shipped  # noqa: E402
from sheaf.data_usda import load_price_series_monthly  # noqa: E402

PUBLISHED = {  # diagnostics/redteam/r0/R0_REPORT.md post-fix table
    "wheat": (+0.720, 2.27, 1.45),
    "maize": (+0.781, 2.22, 1.61),
    "rice": (+0.678, 1.72, 0.82),
}


def score(mod, crop, obs):
    res = mod.run_crop_dynamics(crop, **FULL_KW)
    m = mod.result_to_monthly(res).merge(obs, on=["year", "month"], how="left")
    return (_corr(m.model_price, m.obs_price),
            _hike(m, "model_price", 2006, 6, 2008, 3),
            _hike(m, "model_price", 2009, 6, 2011, 2),
            res)


def main():
    mech_on = build(calm=True, r1=False)
    mech_off = build(calm=False, r1=False)
    obs_all = load_price_series_monthly(deflated=True)
    rows = []
    for crop in CROPS:
        obs = obs_all[(obs_all.year >= 2006) & (obs_all.year <= 2011)][
            ["year", "month", crop]].rename(columns={crop: "obs_price"})
        t0 = time.time()
        c_s, h07_s, h10_s, res_s = score(shipped, crop, obs)
        secs_shipped = time.time() - t0
        c_r, h07_r, h10_r, res_r = score(mech_on, crop, obs)
        ident = float(np.max(np.abs(res_s.price - res_r.price)))
        p0 = float(mech_on.run_crop_dynamics(crop, **CALM_KW).price[0])
        mx, lvl, amp = drift(mech_off.run_crop_dynamics(crop, **CALM_KW).price,
                             p0)
        pc, ph7, ph10 = PUBLISHED[crop]
        rows.append(dict(
            crop=crop, p0=p0,
            corr_shipped=c_s, corr_recompiled=c_r, corr_published=pc,
            h0708_shipped=h07_s, h0708_published=ph7,
            h1011_shipped=h10_s, h1011_published=ph10,
            recompile_max_abs_price_diff=ident,
            matches_published=(abs(c_s - pc) < 5e-4 and abs(h07_s - ph7) < 5e-3
                               and abs(h10_s - ph10) < 5e-3),
            calmoff_max=mx, calmoff_level=lvl, calmoff_amp=amp,
            secs_per_crop=secs_shipped))
        print(f"{crop:6s} shipped corr {c_s:+.4f} x{h07_s:.3f} x{h10_s:.3f} | "
              f"recompiled corr {c_r:+.4f} (|dp|max {ident:.2e}) | "
              f"published corr {pc:+.3f} x{ph7:.2f} x{ph10:.2f} | "
              f"calm-OFF max {mx:.3%} lvl {lvl:.3%} amp {amp:.3%} | "
              f"{secs_shipped:.1f}s")
    df = pd.DataFrame(rows)
    out = ROOT / "diagnostics" / "redteam" / "r1" / "r1_validate.csv"
    df.to_csv(out, index=False)
    print(f"\nall match published: {bool(df.matches_published.all())}")
    print(f"wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
