#!/usr/bin/env python3
"""R1 full battery: asserts, decisive calm test, official scores, runtime.

Variants scored
---------------
A  baseline           shipped ask law (reproduce diagnostics/gate0_*_report.md)
J  FOC + X* const     Agrimate-faithful: constant year-average reference
L  FOC + X*_t season  seasonal reference on realised exports
M  FOC + X*_t path    reference is the calm path itself, step by step
                      (the tautological limit: same information the calm
                      short-circuit uses, but as a smooth map)

Scores use ``_corr`` and ``_hike`` IMPORTED from scripts/score_subannual_crop.py
so they are comparable to diagnostics/gate0_*_report.md.
"""
from __future__ import annotations

import sys
import time
import traceback
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from r1_foc_core import (  # noqa: E402
    CALM_KW, CROPS, FULL_KW, ROOT, build, calibrate_refs, default_R1, drift,
)

from score_subannual_crop import _corr, _hike  # noqa: E402
from sheaf.data_usda import load_price_series_monthly  # noqa: E402

VARIANTS = [
    ("A_baseline", dict(ask_law="shipped", foc=False, price_at="offers",
                        ref_mode="scalar", rival_mode="ref")),
    ("J_FOC_Xconst", dict(ask_law="foc", foc=True, price_at="offers",
                          ref_mode="scalar", rival_mode="ref")),
    ("L_FOC_Xseason", dict(ask_law="foc", foc=True, price_at="exports",
                           ref_mode="season", rival_mode="ref")),
    ("M_FOC_Xpath", dict(ask_law="foc", foc=True, price_at="offers",
                         ref_mode="path", rival_mode="ref")),
]

ASSERTS = ("assert_twin_identity", "assert_amis_raises_price",
           "assert_no_spring_spike", "assert_amis_cuts_exports")


def run_asserts(mod) -> dict:
    out = {}
    for name in ASSERTS:
        fn = getattr(mod, name)
        for crop in CROPS:
            try:
                fn(crop)
                out[(name, crop)] = "PASS"
            except AssertionError as e:
                out[(name, crop)] = f"FAIL: {e}"
            except Exception as e:  # noqa: BLE001
                out[(name, crop)] = f"ERROR: {type(e).__name__}: {e}"
    return out


def main():
    mech_on = build(calm=True, r1=False)
    mech_off = build(calm=False, r1=False)
    obs_all = load_price_series_monthly(deflated=True)

    rows, arows = [], []
    for crop in CROPS:
        obs = obs_all[(obs_all.year >= 2006) & (obs_all.year <= 2011)][
            ["year", "month", crop]].rename(columns={crop: "obs_price"})
        o07 = _hike(obs, "obs_price", 2006, 6, 2008, 3)
        o10 = _hike(obs, "obs_price", 2009, 6, 2011, 2)
        p0 = float(mech_on.run_crop_dynamics(crop, **CALM_KW).price[0])

        for label, cfg in VARIANTS:
            t0 = time.time()
            R1 = default_R1(crop, **cfg)
            if label == "A_baseline":
                on, off = mech_on, mech_off
                calib = 0.0
            else:
                on = build(calm=True, r1=True, R1=R1)
                off = build(calm=False, r1=True, R1=R1)
                tc = time.time()
                calibrate_refs(crop, R1, mech_on, on, iters=6)
                calib = time.time() - tc

            # (b) decisive calm test: calm short-circuit DISABLED
            res_calm = off.run_crop_dynamics(crop, **CALM_KW)
            mx, lvl, amp = drift(res_calm.price, p0)

            # (c) official scores, calm branch as shipped (ON)
            t1 = time.time()
            res = on.run_crop_dynamics(crop, **FULL_KW)
            secs_run = time.time() - t1
            m = on.result_to_monthly(res).merge(obs, on=["year", "month"],
                                                how="left")
            corr = _corr(m.model_price, m.obs_price)
            h07 = _hike(m, "model_price", 2006, 6, 2008, 3)
            h10 = _hike(m, "model_price", 2009, 6, 2011, 2)

            # (a) robustness asserts
            ares = {}
            for name in ASSERTS:
                try:
                    getattr(on, name)(crop)
                    ares[name] = "PASS"
                except AssertionError as e:
                    ares[name] = f"FAIL: {e}"
                except Exception as e:  # noqa: BLE001
                    ares[name] = (f"ERROR: {type(e).__name__}: "
                                  f"{traceback.format_exc().splitlines()[-1]}")
                arows.append(dict(crop=crop, variant=label, check=name,
                                  result=ares[name]))

            rows.append(dict(
                crop=crop, variant=label, p0=p0, alpha=R1["alpha"],
                calm_max=mx, calm_level=lvl, calm_amp=amp,
                calm_pass=(mx <= 0.02),
                corr=corr, hike0708=h07, hike1011=h10,
                obs0708=o07, obs1011=o10,
                n_pass=sum(v == "PASS" for v in ares.values()),
                secs_run=secs_run, secs_calib=calib,
                secs_total=time.time() - t0))
            print(f"{crop:6s} {label:14s} calm max {mx:8.3%} lvl {lvl:7.3%} "
                  f"amp {amp:8.3%} | corr {corr:+.3f} x{h07:.2f} x{h10:.2f} "
                  f"| asserts {rows[-1]['n_pass']}/4 | run {secs_run:.1f}s "
                  f"calib {calib:.1f}s")

    df = pd.DataFrame(rows)
    da = pd.DataFrame(arows)
    d = ROOT / "diagnostics" / "redteam" / "r1"
    df.to_csv(d / "r1_battery_scores.csv", index=False)
    da.to_csv(d / "r1_battery_asserts.csv", index=False)
    print("\n" + df.to_string(index=False,
                              float_format=lambda x: f"{x:.4f}"))
    print(f"\nwrote {(d / 'r1_battery_scores.csv').relative_to(ROOT)}")
    print(f"wrote {(d / 'r1_battery_asserts.csv').relative_to(ROOT)}")
    print("\nassert failures:")
    for r in da[da.result != "PASS"].itertuples():
        print(f"  {r.crop:6s} {r.variant:14s} {r.check:26s} {r.result[:150]}")


if __name__ == "__main__":
    main()
