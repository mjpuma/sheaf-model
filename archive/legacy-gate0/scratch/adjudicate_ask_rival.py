#!/usr/bin/env python3
"""Adjudicate A5 finding 1 against A2e/A2f.

A5 measured the maize sign condition as the test was written and found it
crosses zero at ask_rival ~ 0.751, concluding the default 0.80 is a
constrained boundary value (category H, "the docstring is accurate").

A2e/A2f established that the test as written compares an unpinned tau leg
against a baseline pinned at p0 by the calm branch, and that on a
like-for-like test maize clears the floor at ask_rival = 0.0.

Both are correct measurements of different tests. This script locates the
crossing under BOTH, so the adjudication rests on a number rather than on
whose reasoning sounds better. The question that decides it: under the
corrected test, is the default 0.80 still implied by the sign condition?

Run after commit cafb8ba, which fixed assert_amis_raises_price, so the
library assertion is now the corrected test.
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
    prepare_crop_run,
    run_crop_dynamics,
    simulate_prep,
)

EPISODE = {
    "wheat": (2010, 8, 2010, 12, 0.05),
    "rice": (2008, 1, 2008, 6, 0.05),
    "maize": (2007, 5, 2008, 6, 0.00),
}
KW = dict(use_shocks=False, use_demand=False, use_industrial=False)


def lift(crop, ar, corrected):
    y0, m0, y1, m1, floor = EPISODE[crop]
    tau = run_crop_dynamics(crop, use_amis=True, ask_rival=ar, **KW)
    if corrected:
        pb = prepare_crop_run(crop, use_amis=False, ask_rival=ar, **KW)
        base = simulate_prep(pb, harvest=pb.H * (1.0 - 1e-6))
    else:
        base = run_crop_dynamics(crop, use_amis=False, ask_rival=ar, **KW)
    t0 = (y0 - tau.start_year) * STEPS_PER_YEAR + (m0 - 1) * 2
    t1 = (y1 - tau.start_year) * STEPS_PER_YEAR + (m1 - 1) * 2 + 2
    return float(np.mean(tau.price[t0:t1]) / np.mean(base.price[t0:t1])) - 1.0


def crossing(crop, corrected, lo=0.0, hi=1.2):
    """Smallest ask_rival clearing the floor, bisected to 0.005."""
    floor = EPISODE[crop][4]
    if lift(crop, lo, corrected) >= floor:
        return lo, True   # already clears at zero
    while hi - lo > 0.005:
        mid = 0.5 * (lo + hi)
        if lift(crop, mid, corrected) >= floor:
            hi = mid
        else:
            lo = mid
    return hi, False


def main():
    lines = []

    def out(s=""):
        print(s)
        lines.append(s)

    out("# Adjudication — does the sign condition pin `ask_rival`?\n")
    out("A5 finding 1 (category H) versus A2e/A2f. Resolved by locating the")
    out("crossing under both versions of the test.\n")
    out("| crop | floor | crossing, test as written | crossing, corrected test |")
    out("|---|---|---|---|")
    rows = []
    for crop in ("maize", "wheat", "rice"):
        x_old, free_old = crossing(crop, corrected=False)
        x_new, free_new = crossing(crop, corrected=True)
        f = EPISODE[crop][4]
        out(f"| {crop} | {f:+.2f} | "
            + ("clears at 0.0" if free_old else f"{x_old:.3f}") + " | "
            + ("clears at 0.0" if free_new else f"{x_new:.3f}") + " |")
        rows.append(dict(crop=crop, floor=f, crossing_old=x_old,
                         clears_at_zero_old=free_old, crossing_new=x_new,
                         clears_at_zero_new=free_new))
    out("")

    out("## Margin at the shipped value\n")
    out("| crop | lift at ask_rival=0, corrected | lift at 0.80, corrected | floor |")
    out("|---|---|---|---|")
    for crop in ("maize", "wheat", "rice"):
        l0 = lift(crop, 0.0, True)
        l8 = lift(crop, 0.80, True)
        out(f"| {crop} | {l0:+.4f} | {l8:+.4f} | {EPISODE[crop][4]:+.2f} |")
        rows.append(dict(crop=crop, lift0_corrected=l0, lift08_corrected=l8))

    out("\n## Resolution\n")
    out("If maize clears at 0.0 on the corrected test, then the sign")
    out("condition no longer selects 0.80 and A5 finding 1 cannot stand as")
    out("category H, however accurate it is about the test A5 was given. If")
    out("maize instead crosses somewhere in (0, 0.80), the condition still")
    out("constrains the parameter but no longer selects the shipped value,")
    out("and the honest reading is that the margin, not the sign, is the")
    out("open question. Either way the code comment as written is wrong.\n")

    dest = ROOT / "diagnostics" / "gate0_prep" / "a5"
    pd.DataFrame(rows).to_csv(dest / "adjudication_ask_rival.csv", index=False)
    (dest / "ADJUDICATION_ASK_RIVAL.md").write_text("\n".join(lines) + "\n")
    print(f"\nwrote {(dest / 'ADJUDICATION_ASK_RIVAL.md').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
