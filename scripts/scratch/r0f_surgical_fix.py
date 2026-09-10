#!/usr/bin/env python3
"""R0f: a surgical fix for the asymmetric negative-accessible-stock case.

R0e confirmed the mechanism and showed that a blanket floor on both sides of
the scarcity ratio removes maize's fragility (spread 0.557 -> 0.059) but
regresses rice badly (2007/08 x1.72 -> x2.40 against an observed x1.84, and
2010/11 x0.82 -> x1.11 against an observed x0.79, turning a decline into a
rise). So that probe is rejected.

The reason rice moved is that rice's negative-F regime is BENIGN: F and
F_twin are both about -36.8, so the shift cancels and the ratio is 1.01.
Only maize has the pathological case, where F goes negative (-15.2) while
F_twin stays strongly positive (+207.1), making the shift-based ratio 35.10
and the price jump x4.13 in one step.

So the fix should fire only on that asymmetry. Where F < 0 <= F_twin, the
shift-based ratio is not measuring scarcity -- it is measuring
F_twin / (0.05*sum(safety)), which is set by an arbitrary constant. In that
case alone, floor the denominator on physical world stock, which cannot be
negative. Everywhere else, leave the shipped formula untouched.

Read-only: the module is recompiled in memory.
"""
from __future__ import annotations

import sys
import types
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from sheaf.data_usda import load_price_series_monthly  # noqa: E402
from sheaf.dynamic_crop import (  # noqa: E402
    assert_amis_cuts_exports,
    assert_amis_raises_price,
    assert_no_spring_spike,
    assert_twin_identity,
    result_to_monthly,
    run_crop_dynamics,
)
from score_subannual_crop import _corr, _hike  # noqa: E402

SRC = ROOT / "sheaf" / "dynamic_crop.py"
CROPS = ("wheat", "maize", "rice")
FULL = dict(use_amis=True, use_shocks=True, use_demand=False)

ORIG = """            floor0 = 0.05 * safety_w
            shift = floor0 + max(0.0, -min(free, twin))
            ratio = (twin + shift) / (free + shift)"""
SURGICAL = """            floor0 = 0.05 * safety_w
            if free < 0.0 <= twin:
                # Lean requirement exceeds physical stock while the reference
                # does not. The shift-based ratio here is F_twin/floor0, set
                # by an arbitrary constant rather than by scarcity, so floor
                # the denominator on physical stock, which cannot be negative.
                ratio = (twin + floor0) / (0.10 * float(stock.sum()) + floor0)
            else:
                shift = floor0 + max(0.0, -min(free, twin))
                ratio = (twin + shift) / (free + shift)"""


def build():
    src = SRC.read_text()
    if ORIG not in src:
        raise SystemExit("scarcity block not found verbatim")
    mod = types.ModuleType("sheaf.dc_surgical")
    mod.__package__ = "sheaf"
    mod.__file__ = str(SRC)
    sys.modules["sheaf.dc_surgical"] = mod
    exec(compile(src.replace(ORIG, SURGICAL), mod.__file__, "exec"),
         mod.__dict__)
    return mod


def main():
    lines = []

    def out(s=""):
        print(s)
        lines.append(s)

    obs_all = load_price_series_monthly(deflated=True)
    fix = build()
    rows = []

    out("# R0f — surgical fix for the asymmetric negative-F case\n")
    out("Fires only where F < 0 <= F_twin. Everywhere else the shipped")
    out("formula is untouched, so wheat (F never negative) and rice (F and")
    out("F_twin negative together) should be bit-identical.\n")

    out("## 1. Is it actually surgical?\n")
    out("| crop | max |Δ price| over 144 steps | steps changed |")
    out("|---|---|---|")
    for crop in CROPS:
        a = run_crop_dynamics(crop, **FULL)
        b = fix.run_crop_dynamics(crop, **FULL)
        d = np.abs(b.price - a.price)
        out(f"| {crop} | {d.max():.6f} $/t | {int((d > 1e-9).sum())}/144 |")
        rows.append(dict(crop=crop, kind="surgical", max_dprice=float(d.max()),
                         n_changed=int((d > 1e-9).sum())))
    out("")

    out("## 2. The maize transient\n")
    for crop in ("maize",):
        a = run_crop_dynamics(crop, **FULL)
        b = fix.run_crop_dynamics(crop, **FULL)
        da = np.abs(np.diff(a.price[:24])).max()
        db = np.abs(np.diff(b.price[:24])).max()
        out(f"- {crop} largest one-step move in year 1: **{da:.1f} $/t** "
            f"published, **{db:.1f} $/t** with the fix")
        out(f"- {crop} year-1 price range: {a.price[:24].min():.1f}-"
            f"{a.price[:24].max():.1f} published, "
            f"{b.price[:24].min():.1f}-{b.price[:24].max():.1f} with the fix")
        rows.append(dict(crop=crop, kind="transient", jump_pub=float(da),
                         jump_fix=float(db)))
    out("")

    out("## 3. Scores\n")
    out("| crop | metric | published | surgical fix | Δ | observed |")
    out("|---|---|---|---|---|---|")
    for crop in CROPS:
        obs = obs_all[(obs_all.year >= 2006) & (obs_all.year <= 2011)][
            ["year", "month", crop]].rename(columns={crop: "obs_price"})
        o07 = _hike(obs, "obs_price", 2006, 6, 2008, 3)
        o10 = _hike(obs, "obs_price", 2009, 6, 2011, 2)
        vals = {}
        for label, runner, conv in (
                ("pub", run_crop_dynamics, result_to_monthly),
                ("fix", fix.run_crop_dynamics, fix.result_to_monthly)):
            m = conv(runner(crop, **FULL))
            mm = m.merge(obs, on=["year", "month"], how="left")
            vals[label] = (_corr(mm.model_price, mm.obs_price),
                           _hike(m, "model_price", 2006, 6, 2008, 3),
                           _hike(m, "model_price", 2009, 6, 2011, 2))
        out(f"| {crop} | corr | {vals['pub'][0]:+.3f} | {vals['fix'][0]:+.3f} "
            f"| {vals['fix'][0]-vals['pub'][0]:+.3f} | — |")
        out(f"| {crop} | 2007/08 | x{vals['pub'][1]:.2f} | x{vals['fix'][1]:.2f} "
            f"| {vals['fix'][1]-vals['pub'][1]:+.3f} | x{o07:.2f} |")
        out(f"| {crop} | 2010/11 | x{vals['pub'][2]:.2f} | x{vals['fix'][2]:.2f} "
            f"| {vals['fix'][2]-vals['pub'][2]:+.3f} | x{o10:.2f} |")
        rows.append(dict(crop=crop, kind="score", corr_pub=vals['pub'][0],
                         corr_fix=vals['fix'][0], h07_pub=vals['pub'][1],
                         h07_fix=vals['fix'][1], h10_pub=vals['pub'][2],
                         h10_fix=vals['fix'][2], obs07=o07, obs10=o10))
    out("")

    out("## 4. Fragility\n")
    out("| crop | version | end 2011 | end 2012 | end 2013 | spread |")
    out("|---|---|---|---|---|---|")
    for crop in CROPS:
        obs = obs_all[(obs_all.year >= 2006) & (obs_all.year <= 2011)][
            ["year", "month", crop]].rename(columns={crop: "obs_price"})
        for label, runner, conv in (
                ("published", run_crop_dynamics, result_to_monthly),
                ("surgical", fix.run_crop_dynamics, fix.result_to_monthly)):
            v = []
            for end in (2011, 2012, 2013):
                m = conv(runner(crop, start_year=2006, end_year=end, **FULL))
                m = m[(m.year >= 2006) & (m.year <= 2011)]
                mm = m.merge(obs, on=["year", "month"], how="left")
                v.append(_corr(mm.model_price, mm.obs_price))
            out(f"| {crop} | {label} | {v[0]:+.3f} | {v[1]:+.3f} | {v[2]:+.3f} "
                f"| **{max(v)-min(v):.3f}** |")
            rows.append(dict(crop=crop, kind="fragility", version=label,
                             spread=max(v) - min(v)))
    out("")

    out("## 5. Assertions under the fix\n")
    for crop in CROPS:
        res = []
        for f in (assert_twin_identity, assert_amis_raises_price,
                  assert_no_spring_spike, assert_amis_cuts_exports):
            g = getattr(fix, f.__name__)
            try:
                g(crop)
                res.append("PASS")
            except AssertionError as e:
                res.append(f"FAIL({str(e)[:50]})")
        out(f"- {crop}: {res}")
    out("")

    dest = ROOT / "diagnostics" / "redteam" / "r0"
    dest.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(dest / "surgical_fix.csv", index=False)
    (dest / "R0F_SURGICAL_FIX.md").write_text("\n".join(lines) + "\n")
    print(f"\nwrote {(dest / 'R0F_SURGICAL_FIX.md').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
