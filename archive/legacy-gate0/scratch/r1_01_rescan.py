#!/usr/bin/env python3
"""R1 step 1: re-run the calm-rest-point variant scan on the CURRENT tree.

Why re-run rather than cite. The predecessor's `r1_variant_scan.csv` and
`r1_variant_scan2.csv` were committed at `fa71f82`; `929cec4` then replaced
dead destination-share reweighting with live CES *source*-share competition
(`_ask_reweight_src`, `dynamic_crop.py` L524-538). That changes which
exporter ships to whom, hence offers, fills, asks, stocks and the twin. So
every row of both scans is stale for all three crops, not only maize.

Variants A-L are the predecessor's, re-labelled identically. Added here:

  M  FOC q, P(offers), X*_t = the matched *path*, riv ref
       the tautological limit: same information the calm branch uses, but
       as a continuous map.
  N  FOC q, P(exports), X* const, riv ref
       the gap in the predecessor's grid. `exports` has roughly half the
       coefficient of variation of `offers` (r1_calm_quantities.csv), and a
       constant X* is what Agrimate Eq (D.9) actually specifies
       ("averaged over the agricultural year"), so this is the cell most
       likely to hold.
  O  mech q, P(exports), X* const, riv ref  -- N with the FOC quantity off,
       to attribute any movement to the price law vs the quantity law.

Metrics, all on the matched run (no anomaly, no AMIS, no demand shifter)
with the calm short-circuit DISABLED:
  drift_max   max_t |p_t - p0| / p0  over t >= 24 -- the assert_twin_identity
              metric, tolerance 2%
  drift_level |mean p - p0| / p0     -- the LEVEL error
  drift_amp   (max p - min p) / p0   -- the seasonal AMPLITUDE
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from r1_foc_core import (  # noqa: E402
    ALPHA_I, CALM_KW, CROPS, ROOT, build, calibrate_refs, default_R1, drift,
)

# label, ask_law, price_at, foc, ref_mode, rival_mode, alpha_mult
VARIANTS = [
    ("A  shipped ask law", "shipped", "offers", False, "scalar", "ref", 1.0),
    ("B  FOC q, P(offers), X* const, riv ewma", "foc", "offers", True, "scalar", "ewma", 1.0),
    ("C  FOC q, P(offers), X*_t seas, riv ewma", "foc", "offers", True, "season", "ewma", 1.0),
    ("D  mech q, P(exports), X*_t seas, riv ewma", "foc", "exports", False, "season", "ewma", 1.0),
    ("E  FOC q, P(exports), X*_t seas, riv ewma", "foc", "exports", True, "season", "ewma", 1.0),
    ("F  mech q, P(offers), X*_t seas, riv ewma", "foc", "offers", False, "season", "ewma", 1.0),
    ("G  C with alpha = 1.0", "foc", "offers", True, "season", "ewma", None),
    ("H  mech q, P(offers), X*_t seas, riv ref", "foc", "offers", False, "season", "ref", 1.0),
    ("I  FOC q, P(offers), X*_t seas, riv ref", "foc", "offers", True, "season", "ref", 1.0),
    ("J  FOC q, P(offers), X* const, riv ref", "foc", "offers", True, "scalar", "ref", 1.0),
    ("K  mech q, P(exports), X*_t seas, riv ref", "foc", "exports", False, "season", "ref", 1.0),
    ("L  FOC q, P(exports), X*_t seas, riv ref", "foc", "exports", True, "season", "ref", 1.0),
    ("M  FOC q, P(offers), X*_t path, riv ref", "foc", "offers", True, "path", "ref", 1.0),
    ("N  FOC q, P(exports), X* const, riv ref", "foc", "exports", True, "scalar", "ref", 1.0),
    ("O  mech q, P(exports), X* const, riv ref", "foc", "exports", False, "scalar", "ref", 1.0),
]


def main():
    mech_on = build(calm=True, r1=False)
    rows = []
    for crop in CROPS:
        p0 = float(mech_on.run_crop_dynamics(crop, **CALM_KW).price[0])
        for (label, ask_law, price_at, foc, ref_mode, rival, amul) in VARIANTS:
            t0 = time.time()
            alpha = (ALPHA_I[crop] * amul if amul is not None else 1.0)
            R1 = default_R1(crop, alpha=alpha, ask_law=ask_law,
                            price_at=price_at, foc=foc, ref_mode=ref_mode,
                            rival_mode=rival)
            r1_on = build(calm=True, r1=True, R1=R1)
            r1_off = build(calm=False, r1=True, R1=R1)
            hist = calibrate_refs(crop, R1, mech_on, r1_on, iters=6)
            R1["_trace"], R1["_clip"] = [], []
            res = r1_off.run_crop_dynamics(crop, **CALM_KW)
            T = len(res.price)
            tr = np.array(R1["_trace"], float)[-T:]
            mx, lvl, amp = drift(res.price, p0)
            q = (res.offers if price_at == "offers" else res.exports)
            qw = q.sum(axis=0)
            rows.append(dict(
                crop=crop, variant=label, alpha=alpha,
                drift_max=mx, drift_level=lvl, drift_amp=amp,
                pass_2pct=(mx <= 0.02),
                hold_back=1.0 - tr[:, 1].sum() / max(tr[:, 0].sum(), 1e-9),
                corner_frac=float(tr[:, 2].mean()),
                clip_frac=float(np.mean(R1["_clip"][-T:]) if R1["_clip"] else 0.0),
                q_cv=float(qw.std() / max(qw.mean(), 1e-12)),
                xstar_conv=abs(hist[-1] / max(hist[-2], 1e-12) - 1.0),
                secs=time.time() - t0))
            print(f"{crop:6s} {label:42s} max {mx:8.3%} lvl {lvl:8.3%} "
                  f"amp {amp:8.3%} hold {rows[-1]['hold_back']:5.2f} "
                  f"corner {rows[-1]['corner_frac']:5.2f} "
                  f"clip {rows[-1]['clip_frac']:5.2f} ({time.time()-t0:.1f}s)")
    df = pd.DataFrame(rows)
    out = ROOT / "diagnostics" / "redteam" / "r1" / "r1_rescan_postces.csv"
    df.to_csv(out, index=False)
    print(f"\npass_2pct anywhere: {bool(df.pass_2pct.any())}")
    print(f"wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
