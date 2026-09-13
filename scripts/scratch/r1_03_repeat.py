#!/usr/bin/env python3
"""R1 step 3: is a Gate 0 run repeatable within one process?

`r1_00_validate.py` measured wheat's calm-OFF drift at 26.122%;
`r1_01_rescan.py` and `r1_02_stability.py` measured the same quantity at
23.788% from a byte-identical module. The only difference between the two
call sites is what was run BEFORE. That is a repeatability question and it
has to be settled before any R1 number is reported, because if a Gate 0 run
depends on execution order then every diagnostic in the repository inherits
that dependence.

Sequence tested: run the matched calm-OFF wheat path (a) cold, (b) again,
(c) after a FULL_KW scored run of the shipped module, (d) again.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from r1_foc_core import CALM_KW, CROPS, FULL_KW, ROOT, build, drift  # noqa: E402

from sheaf import dynamic_crop as shipped  # noqa: E402


def main():
    rows = []
    for crop in CROPS:
        mech_on = build(calm=True, r1=False)
        mech_off = build(calm=False, r1=False)
        p0 = float(mech_on.run_crop_dynamics(crop, **CALM_KW).price[0])

        a = mech_off.run_crop_dynamics(crop, **CALM_KW).price
        b = mech_off.run_crop_dynamics(crop, **CALM_KW).price
        _ = shipped.run_crop_dynamics(crop, **FULL_KW)
        c = mech_off.run_crop_dynamics(crop, **CALM_KW).price
        d = shipped.run_crop_dynamics(crop, **CALM_KW).price
        e = mech_off.run_crop_dynamics(crop, **CALM_KW).price

        rows.append(dict(
            crop=crop, p0=p0,
            drift_a_cold=drift(a, p0)[0], drift_b_repeat=drift(b, p0)[0],
            drift_c_after_full=drift(c, p0)[0],
            drift_d_shipped_module=drift(d, p0)[0],
            drift_e_repeat=drift(e, p0)[0],
            max_ab=float(np.max(np.abs(a - b))),
            max_ac=float(np.max(np.abs(a - c))),
            max_ad=float(np.max(np.abs(a - d))),
            max_ae=float(np.max(np.abs(a - e)))))
        r = rows[-1]
        print(f"{crop:6s} drift cold {r['drift_a_cold']:.4%} repeat "
              f"{r['drift_b_repeat']:.4%} after-FULL {r['drift_c_after_full']:.4%} "
              f"shipped-mod {r['drift_d_shipped_module']:.4%} again "
              f"{r['drift_e_repeat']:.4%}")
        print(f"        max|dp| a-b {r['max_ab']:.2e} a-c {r['max_ac']:.2e} "
              f"a-d {r['max_ad']:.2e} a-e {r['max_ae']:.2e}")
    df = pd.DataFrame(rows)
    out = ROOT / "diagnostics" / "redteam" / "r1" / "r1_repeatability.csv"
    df.to_csv(out, index=False)
    print(f"\nwrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
