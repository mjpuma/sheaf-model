#!/usr/bin/env python3
"""A2e: is the restriction-raises-price test comparing like with like?

assert_amis_raises_price compares the restriction-only leg against the
no-AMIS leg over an episode window and requires a positive lift (floor 0.0
for maize: restrictions must not CUT the world price). Repository notes say
the rival markup alpha_r = 0.80 was set by that sign condition.

A2c/A2d established that the no-AMIS leg is pinned at p0 by the calm
conditional at every step, while the restriction-only leg is unpinned during
an episode, and that the offer-price law's own quiet level is 0.66 p0 for
wheat and 0.71 p0 for maize. If so, the measured lift is biased downward by
that gap, and a parameter may have been set to compensate for a comparison
artifact rather than for an economic effect.

This script measures the bias directly.

Read-only with respect to sheaf/*.py.
"""
from __future__ import annotations

import sys
import types
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from sheaf.calendar24 import STEPS_PER_YEAR  # noqa: E402

SRC = ROOT / "sheaf" / "dynamic_crop.py"

CALM_ORIG = """            calm = (abs(free - twin) < 1e-6 and u_anom < 1e-9
                    and block_frac < 1e-9)
            if calm:
                p_star = p0
            else:"""
CALM_OFF = """            calm = False
            if calm:
                p_star = p0
            else:"""

# windows and floors exactly as in assert_amis_raises_price (L920-952)
EPISODE = {
    "wheat": (2010, 8, 2010, 12, 0.05),
    "rice": (2008, 1, 2008, 6, 0.05),
    "maize": (2007, 5, 2008, 6, 0.00),
}


def build(name, calm=True):
    src = SRC.read_text()
    if not calm:
        src = src.replace(CALM_ORIG, CALM_OFF)
    mod = types.ModuleType(f"sheaf.{name}")
    mod.__package__ = "sheaf"
    mod.__file__ = str(SRC)
    sys.modules[f"sheaf.{name}"] = mod
    exec(compile(src, mod.__file__, "exec"), mod.__dict__)
    return mod


def lift(mod, crop, **over):
    y0, m0, y1, m1, floor = EPISODE[crop]
    tau = mod.run_crop_dynamics(crop, use_amis=True, use_shocks=False,
                                use_demand=False, use_industrial=False, **over)
    base = mod.run_crop_dynamics(crop, use_amis=False, use_shocks=False,
                                 use_demand=False, use_industrial=False, **over)
    t0 = (y0 - tau.start_year) * STEPS_PER_YEAR + (m0 - 1) * 2
    t1 = (y1 - tau.start_year) * STEPS_PER_YEAR + (m1 - 1) * 2 + 2
    p_tau = float(np.mean(tau.price[t0:t1]))
    p_base = float(np.mean(base.price[t0:t1]))
    return p_tau / p_base - 1.0, p_tau, p_base, floor


def main():
    lines = []

    def out(s=""):
        print(s)
        lines.append(s)

    on = build("dc_a2e_on", True)
    off = build("dc_a2e_off", False)

    out("# A2e — is the restriction sign test comparing like with like?\n")
    out("`lift` = mean restriction-only price / mean no-AMIS price - 1 over")
    out("the crop's episode window, exactly as assert_amis_raises_price")
    out("computes it. The no-AMIS leg is pinned at p0 at every step by the")
    out("calm conditional; the restriction-only leg is not, during an episode.\n")
    out("| crop | floor | lift as published | lift without the conditional | "
        "pinned base | unpinned base |")
    out("|---|---|---|---|---|---|")
    rows = []
    for crop in EPISODE:
        l_on, p_tau_on, p_base_on, floor = lift(on, crop)
        l_off, p_tau_off, p_base_off, _ = lift(off, crop)
        out(f"| {crop} | {floor:+.2f} | {l_on:+.3f} | {l_off:+.3f} "
            f"| {p_base_on:.1f} | {p_base_off:.1f} |")
        rows.append(dict(crop=crop, floor=floor, lift_published=l_on,
                         lift_unpinned=l_off, base_pinned=p_base_on,
                         base_unpinned=p_base_off))
    out("")

    out("## Does alpha_r survive without the conditional?\n")
    out("Repository notes state alpha_r = 0.80 was set so that isolated maize")
    out("restrictions do not cut the world price. Below, the maize lift as a")
    out("function of alpha_r, with and without the conditional. If the sign")
    out("condition holds at alpha_r = 0 once the comparison is like-for-like,")
    out("then alpha_r was compensating for the artifact, not for an economic")
    out("effect, and its justification needs restating.\n")
    out("| alpha_r | maize lift, conditional on | conditional off |")
    out("|---|---|---|")
    for ar in (0.0, 0.2, 0.4, 0.8, 1.2):
        a, *_ = lift(on, "maize", ask_rival=ar)
        b, *_ = lift(off, "maize", ask_rival=ar)
        out(f"| {ar:.1f} | {a:+.3f} | {b:+.3f} |")
        rows.append(dict(crop="maize", ask_rival=ar, lift_published=a,
                         lift_unpinned=b))
    out("")
    out("Same for wheat and rice, whose floors are +0.05:\n")
    out("| crop | alpha_r | lift, conditional on | conditional off |")
    out("|---|---|---|---|")
    for crop in ("wheat", "rice"):
        for ar in (0.0, 0.8):
            a, *_ = lift(on, crop, ask_rival=ar)
            b, *_ = lift(off, crop, ask_rival=ar)
            out(f"| {crop} | {ar:.1f} | {a:+.3f} | {b:+.3f} |")
            rows.append(dict(crop=crop, ask_rival=ar, lift_published=a,
                             lift_unpinned=b))

    dest = ROOT / "diagnostics" / "gate0_prep" / "a2"
    dest.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(dest / "amis_lift_bias.csv", index=False)
    (dest / "A2E_AMIS_LIFT_BIAS.md").write_text("\n".join(lines) + "\n")
    print(f"\nwrote {(dest / 'A2E_AMIS_LIFT_BIAS.md').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
