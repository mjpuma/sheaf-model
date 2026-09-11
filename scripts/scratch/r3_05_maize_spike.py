#!/usr/bin/env python3
"""R3-05: the maize Dec-2006 single-step artefact.

Fig. r3_fig2 shows a one-step maize price spike near step 22 (Dec 2006) in the
shipped model that V1 removes. Hypothesis: the harvest anomaly scalar is a
CALENDAR-year step (`_apply_harvest_scalars`), so a flat-phi forward window
straddling 31 Dec reads next year's anomaly at full weight phi, producing a
discontinuity in the lean gap and hence in offers. Agrimate's lag-decaying
weight damps whatever sits at the far end of the window, so the discontinuity
enters at w_k instead of phi.

Measured here: the largest one-step price jump per crop, where it lands, and
the lean-gap discontinuity at the calendar boundary.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "scratch"))

from sheaf.calendar24 import STEPS_PER_YEAR  # noqa: E402
from r3_02_prototypes import build as build_variant  # noqa: E402

CROPS = ("wheat", "maize", "rice")
OUT = ROOT / "diagnostics" / "redteam" / "r3"
P1 = dict(use_amis=True, use_shocks=True, use_demand=False)


def step_label(t: int, y0: int = 2006) -> str:
    y = y0 + t // STEPS_PER_YEAR
    m = (t % STEPS_PER_YEAR) // 2 + 1
    return f"{y}-{m:02d}"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    lines, rows = [], []

    def out(s: str = "") -> None:
        print(s)
        lines.append(s)

    out("# R3-05 - the calendar-boundary price artefact\n")
    mods = {"V0": build_variant("dc_r3s_v0"),
            "V1": build_variant("dc_r3s_v1", agri_exp=True)}
    out("| crop | variant | max 1-step |dp/p| | at | max p | min p | "
        "mean |dp/p| at Dec->Jan boundaries |")
    out("|---|---|---|---|---|---|---|")
    for crop in CROPS:
        for vname, mod in mods.items():
            p = mod.run_crop_dynamics(crop, **P1).price
            r = np.abs(np.diff(p)) / np.maximum(p[:-1], 1e-9)
            i = int(np.argmax(r))
            # Dec 2nd half -> Jan 1st half transitions
            bnd = [y * STEPS_PER_YEAR - 1 for y in range(1, len(p) //
                                                         STEPS_PER_YEAR)]
            bnd_mean = float(np.mean([r[b] for b in bnd if b < len(r)]))
            out(f"| {crop} | {vname} | {r[i]:.1%} | {step_label(i)} | "
                f"{p.max():.0f} | {p.min():.0f} | {bnd_mean:.2%} |")
            rows.append(dict(crop=crop, variant=vname,
                             max_step_move=float(r[i]),
                             at=step_label(i), p_max=float(p.max()),
                             p_min=float(p.min()),
                             mean_boundary_move=bnd_mean))
    out("")
    out("Note: the boundary column averages the Dec-2nd-half -> Jan-1st-half "
        "step, which is where `_apply_harvest_scalars` switches the annual "
        "anomaly multiplier.\n")
    pd.DataFrame(rows).to_csv(OUT / "r3_boundary_artefact.csv", index=False)
    (OUT / "R3_05_BOUNDARY.md").write_text("\n".join(lines) + "\n")
    print(f"wrote {OUT / 'R3_05_BOUNDARY.md'}")


if __name__ == "__main__":
    main()
