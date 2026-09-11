#!/usr/bin/env python3
"""Red-team census, experiment 4: why is gamma exactly inert?

Experiment 3 found ||dJ|| = 0.000 for `ask_comp_elast` at BOTH step sizes,
which is not "small" but exactly zero. That is a claim about the code, not
about economics, so it is worth settling directly rather than by inference.

Claim under test - note eq. (11) / `sections/dynamics.tex` L128-134:

    "Preferred destination shares are reweighted toward low offer prices,
     A~_ij,t  proportional to  A_ij (p0 / q_i,t-1)^gamma,  sum_j A~_ij = 1."

Implementation - `sheaf/dynamic_crop.py` L503-509, `_ask_reweight_dest`.

The re-weighting factor rel_i = (p0/q_i)^gamma carries only the EXPORTER
index i, and it multiplies row i of A. The row is then renormalised to sum
to one. A constant factor on a row is annihilated by renormalising that
row, so

    A~_ij = A_ij rel_i / sum_j (A_ij rel_i) = A_ij / sum_j A_ij = A_ij,

for every gamma, whenever the row already sums to one - which
`load_trade_shares` guarantees at L496-497.

We check three things: the algebra numerically on the real matrices, the
exact equality of A_eff and A for a wide sweep of gamma and offer prices,
and the equality of the scored output for gamma across four orders of
magnitude.
"""
from __future__ import annotations

import json

import numpy as np

from redteam_cen_00_harness import CROPS, ROOT, score_full_leg
from sheaf.dynamic_crop import _ask_reweight_dest, load_trade_shares

OUT = ROOT / "diagnostics" / "gate0_prep" / "redteam" / "census"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    report = {}

    print("=== 1. Is A_eff == A on the real trade matrices? ===")
    rng = np.random.default_rng(0)
    worst = 0.0
    for crop in CROPS:
        from sheaf.calibration import DATA
        countries = [d["name"] for d in DATA] + ["RestOfWorld"]
        A, _ = load_trade_shares(crop, countries)
        p0 = 250.0
        row_sums = A.sum(axis=1)
        n_zero_rows = int((row_sums < 1e-12).sum())
        for gamma in (0.0, 0.25, 1.25, 3.0, 10.0):
            for trial in range(5):
                # Offer prices spanning the clip band [0.45 p0, 2.8 p0].
                ask = rng.uniform(0.45 * p0, 2.8 * p0, size=A.shape[0])
                A_eff = _ask_reweight_dest(A, ask, p0, gamma=gamma)
                d = float(np.max(np.abs(A_eff - A)))
                worst = max(worst, d)
        print(f"  {crop:6s} n={A.shape[0]} rows, {n_zero_rows} all-zero rows, "
              f"max|A_eff - A| over gamma x ask sweep = {worst:.3e}")
    report["max_abs_A_eff_minus_A"] = worst
    print(f"  WORST over all crops / gammas / draws: {worst:.3e}")

    print("\n=== 2. Does the scored output move with gamma? ===")
    rows = {}
    for crop in CROPS:
        rows[crop] = {}
        for gamma in (0.0, 0.01, 1.25, 5.0, 50.0):
            s = score_full_leg(crop, ask_comp_elast=gamma)
            rows[crop][gamma] = s
            print(f"  {crop:6s} gamma={gamma:6.2f}  corr {s['corr']:+.9f}  "
                  f"07/08 {s['h0708']:.9f}  10/11 {s['h1011']:.9f}")
        ref = rows[crop][1.25]
        dev = max(abs(rows[crop][g][k] - ref[k])
                  for g in rows[crop] for k in ("corr", "h0708", "h1011"))
        print(f"  {crop:6s} max deviation from the default gamma=1.25: {dev:.3e}")
        report[f"{crop}_max_dev_over_gamma"] = dev

    print("\n=== 3. Verdict ===")
    # "Exact" here means exact to floating-point: the algebra cancels, so the
    # only residue is rounding in the divide-then-renormalise round trip.
    exact = (report["max_abs_A_eff_minus_A"] < 1e-14
             and all(report[f"{c}_max_dev_over_gamma"] < 1e-12 for c in CROPS))
    print("  `_ask_reweight_dest` is a no-op to floating-point exactness: "
          f"{'CONFIRMED' if exact else 'NOT confirmed'}")
    print("  Consequence: eq. (11) of the note (price-responsive destination")
    print("  re-weighting) is not implemented; buyers never shift toward")
    print("  cheaper origins within the preferred network. gamma = 1.25 is a")
    print("  phantom parameter.")
    report["exact_noop_confirmed"] = bool(exact)
    (OUT / "cen04_reweight_noop.json").write_text(json.dumps(report, indent=2))
    print(f"\nwrote {OUT / 'cen04_reweight_noop.json'}")


if __name__ == "__main__":
    main()
