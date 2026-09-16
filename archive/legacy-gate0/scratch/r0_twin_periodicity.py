#!/usr/bin/env python3
"""R0: is SHEAF's twin annually periodic, as Agrimate's baseline is?

Agrimate's baseline is an inter-annual Nash-baseline state solved quasi
analytically (Suppl. D.7.4) under an explicit PERIODICITY CONDITION: "the
yearly supply has to match the yearly consumption in this idealized
baseline setting; the periodicity condition prohibits a year's beginning
storage level to differ from the ending one" (Suppl. ~L2507-2509).

SHEAF's reference is a different object: a climatological twin run
(harvest = H_seas, mean flex demand, no industrial, tau = 0), simulated
forward from a two-year spin-up. Nothing in that construction enforces
periodicity. If the twin's stocks drift year over year, then the scarcity
ratio r_t = (F_twin + f)/(F + f) is measured against a moving denominator,
and the "reference trajectory" is a transient rather than a steady cycle.

This matters for the Potsdam question "what is the baseline?" and it is
cheap to settle. Read-only.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from sheaf.calendar24 import STEPS_PER_YEAR  # noqa: E402
from sheaf.dynamic_crop import prepare_crop_run, simulate_prep  # noqa: E402

CROPS = ("wheat", "maize", "rice")


def main():
    lines = []

    def out(s=""):
        print(s)
        lines.append(s)

    out("# R0 — is the SHEAF twin annually periodic?\n")
    out("Agrimate's baseline enforces a periodicity condition: a year's")
    out("beginning storage equals its ending storage. SHEAF's twin is a")
    out("forward climatological simulation with no such condition. Below,")
    out("what the twin actually does.\n")

    rows = []
    for crop in CROPS:
        # The twin is simulated inside prepare_crop_run; reproduce it exactly
        # by running the same configuration with free_twin unset, which is
        # what the calm/twin pass does.
        prep = prepare_crop_run(crop, use_amis=False, use_shocks=False,
                                use_demand=False, use_industrial=False)
        twin = simulate_prep(prep)   # matched run: free == free_twin exactly
        stock_w = twin.stock.sum(axis=0)
        free = prep.free_twin
        n_y = len(stock_w) // STEPS_PER_YEAR

        out(f"## {crop}\n")
        out("| model year | world stock at year start (MMT) | year-end (MMT) "
            "| drift over year | mean accessible stock F_twin |")
        out("|---|---|---|---|---|")
        for y in range(n_y):
            a = y * STEPS_PER_YEAR
            b = a + STEPS_PER_YEAR - 1
            d = stock_w[b] - stock_w[a]
            out(f"| {2006+y} | {stock_w[a]:.1f} | {stock_w[b]:.1f} | "
                f"{d:+.1f} | {np.mean(free[a:b+1]):.1f} |")
            rows.append(dict(crop=crop, year=2006 + y,
                             stock_start=float(stock_w[a]),
                             stock_end=float(stock_w[b]), drift=float(d),
                             free_mean=float(np.mean(free[a:b + 1]))))
        first = stock_w[0]
        last = stock_w[-1]
        out("")
        out(f"- world stock, first step {first:.1f} MMT, last step {last:.1f} "
            f"MMT: net drift **{100*(last/first-1):+.1f}%** over "
            f"{n_y} model years")
        # periodicity of the object that actually enters the price map
        f_y = np.array([np.mean(free[y*STEPS_PER_YEAR:(y+1)*STEPS_PER_YEAR])
                        for y in range(n_y)])
        out(f"- annual-mean accessible stock F_twin by year: "
            + ", ".join(f"{v:.1f}" for v in f_y))
        out(f"- spread across years: {100*(f_y.max()/f_y.min()-1):.1f}% "
            f"(a periodic baseline would be 0%)")
        # is the seasonal shape at least repeating?
        shapes = np.array([free[y*STEPS_PER_YEAR:(y+1)*STEPS_PER_YEAR]
                           for y in range(n_y)])
        corr = np.corrcoef(shapes[1], shapes[-1])[0, 1]
        out(f"- correlation of the within-year F_twin shape, year 2 vs final "
            f"year: {corr:+.3f} (1.0 would mean the seasonal cycle repeats "
            f"exactly)\n")

    out("## Reading\n")
    out("A drifting twin is not automatically a defect: SHEAF's reference is")
    out("documented as a trajectory rather than a constant, and a two-year")
    out("spin-up is a deliberate choice. The question is whether the drift is")
    out("small enough that r_t reads as scarcity rather than as baseline")
    out("transient. If the annual-mean accessible stock moves by more across")
    out("the twin's own years than a crisis moves it, then the denominator is")
    out("doing work the numerator was supposed to do, and the honest fix is")
    out("either Agrimate's periodicity condition or a longer spin-up.\n")

    dest = ROOT / "diagnostics" / "redteam" / "r0"
    dest.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(dest / "twin_periodicity.csv", index=False)
    (dest / "R0_TWIN_PERIODICITY.md").write_text("\n".join(lines) + "\n")
    print(f"\nwrote {(dest / 'R0_TWIN_PERIODICITY.md').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
