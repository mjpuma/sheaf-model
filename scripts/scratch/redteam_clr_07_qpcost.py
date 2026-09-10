#!/usr/bin/env python3
"""Task 4c cost probe — what does a real clearing solve cost in this codebase?

Times the parked annual spatial-equilibrium QP (sheaf/annual/core.py) at the
same node count Gate 0 uses (18), for three commodities and for one, and
compares against the shipped Gate 0 map. This is the honest reference for
option (c): a per-step price that solves a market-clearing condition.
"""
from __future__ import annotations

import copy
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import redteam_clr_lib as L  # noqa: E402

from sheaf.annual import build_countries  # noqa: E402
from sheaf.annual.core import SpatialEquilibrium, build_demand_system  # noqa: E402
from sheaf.calibration import RHO  # noqa: E402
from sheaf.dynamic_crop import prepare_crop_run  # noqa: E402

OUT = Path(__file__).resolve().parents[2] / "diagnostics/gate0_prep/redteam/clearing"
OUT.mkdir(parents=True, exist_ok=True)


def main() -> None:
    cs, transport, grains, fm = build_countries(substitution=True)
    n, G = len(cs), len(grains)
    # Timing only needs a well-posed PD demand system of the right dimension.
    from sheaf.calibration import P0
    p0v = np.asarray(P0, float)
    own = np.array([-0.25, -0.30, -0.20])[:G]
    systems = [build_demand_system(
        grains, np.maximum(np.asarray(c.production, float), 1.0), p0v, own, RHO)
        for c in cs]
    avail = np.array([np.maximum(c.production, 0.1) for c in cs], float)

    rows = []
    for label, gsel in (("3 commodities", list(range(G))), ("1 commodity", [0])):
        spe = SpatialEquilibrium(transport.copy(),
                                 tuple(grains[g] for g in gsel),
                                 freight_mult=np.asarray(fm)[gsel])
        sysd = []
        for s in systems:
            s2 = copy.deepcopy(s)
            s2.Minv = np.ascontiguousarray(s.Minv[np.ix_(gsel, gsel)])
            s2.M = np.ascontiguousarray(s.M[np.ix_(gsel, gsel)])
            s2.a = np.ascontiguousarray(s.a[gsel])
            sysd.append(s2)
        av = np.ascontiguousarray(avail[:, gsel])
        z = np.zeros((n, len(gsel)))
        spe.solve(sysd, av, z, z)          # warm
        reps = 8
        t0 = time.perf_counter()
        for _ in range(reps):
            spe.solve(sysd, av, z, z)
        dt = (time.perf_counter() - t0) / reps
        rows.append(dict(object=f"annual SPE QP, {label}, n={n}",
                         per_solve_s=dt, per_144_step_run_s=144 * dt))

    prep = prepare_crop_run("wheat", use_amis=True, use_shocks=True,
                            use_demand=False)
    t0 = time.perf_counter()
    for _ in range(20):
        L.simulate_instrumented(prep, record_trade=False)
    t_g0 = (time.perf_counter() - t0) / 20
    rows.append(dict(object="Gate 0 shipped map, 144 steps, n=18",
                     per_solve_s=t_g0 / 144, per_144_step_run_s=t_g0))

    df = pd.DataFrame(rows)
    ref = float(df.iloc[-1].per_144_step_run_s)
    df["x_gate0_run"] = df.per_144_step_run_s / ref
    # a scored crop needs: spin-up (2y=48 steps) + twin (144) + treatment (144)
    df["one_scored_crop_s"] = df.per_solve_s * (48 + 144 + 144)
    df["three_crops_four_legs_s"] = df.one_scored_crop_s * 3 * 4
    # Gate 2 grid best response: 13-point grid x 3 IBR iterations of full runs
    df["gate2_ibr_13x3_s"] = df.one_scored_crop_s * 13 * 3
    df.to_csv(OUT / "clr_qp_cost.csv", index=False)
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
