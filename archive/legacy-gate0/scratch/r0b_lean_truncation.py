#!/usr/bin/env python3
"""R0b: the lean-cover horizon truncates at the end of the run.

`rolling_ahead_variable` (sheaf/seasonal.py L156-159) computes the forward
window as `t1 = min(t + 1 + h, T)`, so within MAX_LEAN_STEPS of the array
end the lean-cover horizon is short. MAX_LEAN_STEPS = STEPS_PER_YEAR = 24,
so the last 24 steps of any run see a truncated horizon.

That zone overlaps the 2010/11 scoring window. The peak month 2011-02 is
step ~122 of 144, i.e. 22 steps from the end, so its horizon is clipped.

Test: extend the simulation by one and two extra years of climatology, then
score EXACTLY the same calendar months. Any change in a 2006-2011 metric is
attributable to the truncation, since the scored months and their forcing
are otherwise identical.

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
from score_subannual_crop import _corr, _hike  # noqa: E402

CROPS = ("wheat", "maize", "rice")
FULL = dict(use_amis=True, use_shocks=True, use_demand=False)


def main():
    lines = []

    def out(s=""):
        print(s)
        lines.append(s)

    obs_all = load_price_series_monthly(deflated=True)
    out("# R0b — does the truncated lean horizon touch a scored number?\n")
    out("Same scored months (2006-2011) in every row. The only difference is")
    out("how much climatology lies beyond the end of the simulation, which")
    out("determines whether the lean-cover forward window is clipped.\n")
    out("| crop | end_year | corr | 2007/08 | 2010/11 | observed 07/08 | observed 10/11 |")
    out("|---|---|---|---|---|---|---|")

    rows = []
    for crop in CROPS:
        obs = obs_all[(obs_all.year >= 2006) & (obs_all.year <= 2011)][
            ["year", "month", crop]].rename(columns={crop: "obs_price"})
        o07 = _hike(obs, "obs_price", 2006, 6, 2008, 3)
        o10 = _hike(obs, "obs_price", 2009, 6, 2011, 2)
        for end in (2011, 2012, 2013):
            res = run_crop_dynamics(crop, start_year=2006, end_year=end, **FULL)
            m = result_to_monthly(res)
            m = m[(m.year >= 2006) & (m.year <= 2011)]
            mm = m.merge(obs, on=["year", "month"], how="left")
            c = _corr(mm.model_price, mm.obs_price)
            h07 = _hike(m, "model_price", 2006, 6, 2008, 3)
            h10 = _hike(m, "model_price", 2009, 6, 2011, 2)
            flag = " (published)" if end == 2011 else ""
            out(f"| {crop} | {end}{flag} | {c:+.3f} | x{h07:.2f} | x{h10:.2f} "
                f"| x{o07:.2f} | x{o10:.2f} |")
            rows.append(dict(crop=crop, end_year=end, corr=c, hike_0708=h07,
                             hike_1011=h10, obs_0708=o07, obs_1011=o10))
    out("")

    df = pd.DataFrame(rows)
    out("## Size of the artifact\n")
    out("| crop | Δcorr | Δ2007/08 | Δ2010/11 | (end_year 2012 vs 2011) |")
    out("|---|---|---|---|---|")
    for crop in CROPS:
        a = df[(df.crop == crop) & (df.end_year == 2011)].iloc[0]
        b = df[(df.crop == crop) & (df.end_year == 2012)].iloc[0]
        out(f"| {crop} | {b.corr-a.corr:+.3f} | {b.hike_0708-a.hike_0708:+.3f} "
            f"| {b.hike_1011-a.hike_1011:+.3f} | |")
    out("")
    out("2007/08 is far from the array end, so its ratio is the control: it")
    out("should be unchanged. 2010/11 sits inside the truncation zone, so any")
    out("movement there is the artifact. If 2007/08 also moves, the extra year")
    out("is changing more than the horizon and this test is confounded --")
    out("say so rather than reading the 2010/11 number.\n")

    dest = ROOT / "diagnostics" / "redteam" / "r0"
    dest.mkdir(parents=True, exist_ok=True)
    df.to_csv(dest / "lean_horizon_truncation.csv", index=False)
    (dest / "R0B_LEAN_TRUNCATION.md").write_text("\n".join(lines) + "\n")
    print(f"\nwrote {(dest / 'R0B_LEAN_TRUNCATION.md').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
