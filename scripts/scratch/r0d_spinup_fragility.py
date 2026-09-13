#!/usr/bin/env python3
"""R0d: why is the maize score fragile, and is the spin-up transient the cause?

R0c found the lean-horizon truncation negligible (max delta 0.012 on any
metric) but showed that a ~1% change in maize's climatological inputs moves
its 2006-2011 monthly price correlation from +0.712 to +0.276. Wheat and
rice are stable under the same perturbation.

A3's earlier pass noted a candidate cause: maize's largest single-step price
move in the whole dataset is at step 22 (2006-12a), where the price goes
95.5 -> 393.9 $/t, a factor of 4.1, inside the first model year. If the
score is sensitive to a spin-up transient, then the published correlation is
partly a statement about the transient rather than about the crisis.

Note that assert_twin_identity ALREADY discards price[:24] as transient
(dynamic_crop.py ~L907). The scoring script does not.

Read-only.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from sheaf.data_usda import load_price_series_monthly  # noqa: E402
from sheaf.dynamic_crop import result_to_monthly, run_crop_dynamics  # noqa: E402
from score_subannual_crop import _corr  # noqa: E402

CROPS = ("wheat", "maize", "rice")
FULL = dict(use_amis=True, use_shocks=True, use_demand=False)


def main():
    lines = []

    def out(s=""):
        print(s)
        lines.append(s)

    obs_all = load_price_series_monthly(deflated=True)
    rows = []

    out("# R0d — the spin-up transient and the fragility of the maize score\n")

    out("## The transient itself\n")
    out("Largest single-step price move in the first model year, and where the")
    out("first year's prices sit relative to the reference.\n")
    out("| crop | p0 | max |Δp| in year 1 | at step | as ratio | year-1 price range |")
    out("|---|---|---|---|---|---|")
    for crop in CROPS:
        res = run_crop_dynamics(crop, **FULL)
        p = res.price
        d = np.abs(np.diff(p[:24]))
        i = int(np.argmax(d))
        out(f"| {crop} | {p[0]:.1f} | {d[i]:.1f} $/t | {i}->{i+1} "
            f"| x{p[i+1]/max(p[i],1e-9):.2f} "
            f"| {p[:24].min():.1f}-{p[:24].max():.1f} $/t |")
        rows.append(dict(crop=crop, kind="transient", p0=float(p[0]),
                         max_jump=float(d[i]), step=i,
                         ratio=float(p[i + 1] / max(p[i], 1e-9)),
                         y1_min=float(p[:24].min()),
                         y1_max=float(p[:24].max())))
    out("")

    out("## Correlation with and without the spin-up year\n")
    out("`end_year` is varied only to perturb the in-sample climatology by")
    out("about 1%, exactly as in R0c; the scored months are held fixed. The")
    out("question is whether dropping the first model year stabilises the")
    out("score.\n")
    out("| crop | scored months | end 2011 | end 2012 | end 2013 | spread |")
    out("|---|---|---|---|---|---|")
    for crop in CROPS:
        for lo, label in ((2006, "2006-2011 (published)"),
                          (2007, "2007-2011 (drop spin-up)")):
            obs = obs_all[(obs_all.year >= lo) & (obs_all.year <= 2011)][
                ["year", "month", crop]].rename(columns={crop: "obs_price"})
            vals = []
            for end in (2011, 2012, 2013):
                res = run_crop_dynamics(crop, start_year=2006, end_year=end,
                                        **FULL)
                m = result_to_monthly(res)
                m = m[(m.year >= lo) & (m.year <= 2011)]
                mm = m.merge(obs, on=["year", "month"], how="left")
                vals.append(_corr(mm.model_price, mm.obs_price))
            spread = max(vals) - min(vals)
            out(f"| {crop} | {label} | {vals[0]:+.3f} | {vals[1]:+.3f} "
                f"| {vals[2]:+.3f} | **{spread:.3f}** |")
            rows.append(dict(crop=crop, kind="stability", scored_from=lo,
                             corr_2011=vals[0], corr_2012=vals[1],
                             corr_2013=vals[2], spread=spread))
    out("")

    out("## Reading\n")
    out("A score whose spread across a 1% recalibration is comparable to the")
    out("score itself is not measuring what it claims to measure. If dropping")
    out("the spin-up year collapses the spread, the fix is to score on")
    out("2007-2011 -- which is what the twin-identity test already does -- and")
    out("the published maize correlation should be restated. If the spread")
    out("survives, the fragility is in the maize path itself and is a larger")
    out("problem than a scoring convention.\n")

    dest = ROOT / "diagnostics" / "redteam" / "r0"
    dest.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(dest / "spinup_fragility.csv", index=False)
    (dest / "R0D_SPINUP_FRAGILITY.md").write_text("\n".join(lines) + "\n")
    print(f"\nwrote {(dest / 'R0D_SPINUP_FRAGILITY.md').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
