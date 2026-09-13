#!/usr/bin/env python3
"""R0i: raw price response to a harvest shortfall, both signs made explicit.

R0h reported maize price flexibility of +24.19 at a 1% shortfall, i.e. the
WRONG SIGN -- a harvest shortfall apparently lowering the price -- while
rice sat at |4.2-4.9|, squarely in the band implied both by its own demand
elasticity (5.0) and by Agrimate's alpha (3.0-3.5).

A log-ratio can mislead when the baseline is pinned flat, so this script
reports the raw mean and peak prices rather than only the derived
elasticity, checks monotonicity across a finer grid of shortfalls, and
compares the model before and after the R0f scarcity fix so that the fix is
not blamed for something that predates it.

The candidate explanation to test is A1's finding that the offer-price law
has no rest point: realised fill in a quiet market is well below the target
fill, so asks drift DOWN every step. If that downward drift is larger than
the scarcity signal from a small shortfall, the net price response inverts.

Read-only; the pre-fix module is reconstructed in memory.
"""
from __future__ import annotations

import sys
import types
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from sheaf.dynamic_crop import prepare_crop_run, simulate_prep  # noqa: E402

SRC = ROOT / "sheaf" / "dynamic_crop.py"
CROPS = ("wheat", "maize", "rice")

# Reconstruct the pre-R0f formula by reversing the committed fix.
POST = """            if free < 0.0 <= twin:
                # Lean requirement exceeds physical stock while the reference
                # does not. The shift below would then reduce the denominator
                # to floor0, making the ratio ≈ twin/floor0 — a number set by
                # the regulariser rather than by scarcity (maize 2006-12a:
                # ratio 35.1, price ×4.13 in one step). Floor the denominator
                # on physical stock instead, which cannot go negative.
                ratio = (twin + floor0) / (0.10 * float(stock.sum()) + floor0)
            else:
                shift = floor0 + max(0.0, -min(free, twin))
                ratio = (twin + shift) / (free + shift)"""
PRE = """            shift = floor0 + max(0.0, -min(free, twin))
            ratio = (twin + shift) / (free + shift)"""


def build_prefix():
    src = SRC.read_text()
    if POST not in src:
        raise SystemExit("post-fix block not found verbatim")
    mod = types.ModuleType("sheaf.dc_prefix")
    mod.__package__ = "sheaf"
    mod.__file__ = str(SRC)
    sys.modules["sheaf.dc_prefix"] = mod
    exec(compile(src.replace(POST, PRE), mod.__file__, "exec"), mod.__dict__)
    return mod


def main():
    lines = []

    def out(s=""):
        print(s)
        lines.append(s)

    pre = build_prefix()
    rows = []
    shortfalls = (0.0, 0.005, 0.01, 0.02, 0.03, 0.05, 0.075, 0.10, 0.15)

    out("# R0i — raw price response to a uniform harvest shortfall\n")
    out("Matched configuration (no AMIS, no shocks, no demand anomaly, no")
    out("industrial), so this is the model's own transfer function. Prices in")
    out("2010 $/t. A well-behaved market has mean price rising monotonically")
    out("with the shortfall.\n")

    for label, mod in (("after the R0f fix", None), ("before the R0f fix", pre)):
        out(f"## {label}\n")
        out("| crop | " + " | ".join(f"−{int(s*1000)/10:g}%"
                                     for s in shortfalls) + " |")
        out("|---" * (len(shortfalls) + 1) + "|")
        for crop in CROPS:
            prep_fn = prepare_crop_run if mod is None else mod.prepare_crop_run
            sim_fn = simulate_prep if mod is None else mod.simulate_prep
            prep = prep_fn(crop, use_amis=False, use_shocks=False,
                           use_demand=False, use_industrial=False)
            means = []
            for s in shortfalls:
                r = sim_fn(prep, harvest=prep.H * (1.0 - s))
                means.append(float(np.mean(r.price)))
            out(f"| {crop} | " + " | ".join(f"{m:.1f}" for m in means) + " |")
            mono = all(b >= a - 1e-9 for a, b in zip(means, means[1:]))
            rows.append(dict(version=label, crop=crop, monotone=mono,
                             p0=float(prep.p0),
                             **{f"s{int(s*1000)}": m
                                for s, m in zip(shortfalls, means)}))
        out("")
        out("| crop | monotone in the shortfall? | reference p0 |")
        out("|---|---|---|")
        for crop in CROPS:
            rec = [r for r in rows
                   if r["version"] == label and r["crop"] == crop][0]
            out(f"| {crop} | {'yes' if rec['monotone'] else '**NO**'} "
                f"| {rec['p0']:.1f} $/t |")
        out("")

    out("## Reading\n")
    out("A non-monotone or inverted response is a formulation problem, not a")
    out("calibration one: it means a scarcer world can be a cheaper world in")
    out("this model over some range. Comparing the two panels attributes it")
    out("either to the R0f fix or to something older. A1's rest-point finding")
    out("predicts the inversion is older than the fix, because the downward")
    out("drift in the offer-price law is present in both versions.\n")
    out("For orientation: Agrimate's world-market inverse elasticity is 3.0")
    out("(Suppl. D.7.4.1) and its international-market alpha_I is 3.5 (Tbl.")
    out("D.8), both on flows, so a 1% shortfall there moves the price by")
    out("roughly 3%.\n")

    dest = ROOT / "diagnostics" / "redteam" / "r0"
    dest.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(dest / "shortfall_response.csv", index=False)
    (dest / "R0I_SHORTFALL_RESPONSE.md").write_text("\n".join(lines) + "\n")
    print(f"\nwrote {(dest / 'R0I_SHORTFALL_RESPONSE.md').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
