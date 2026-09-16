#!/usr/bin/env python3
"""R0e: the negative-accessible-stock regime, and a fix for it.

R0d found maize's price jumps 91.6 -> 393.9 $/t (x4.13) at step 21->22 of
the first model year, and that maize's 2006-2011 correlation swings across
+0.08 to +0.83 under a ~1% recalibration while wheat and rice are stable.

A1 independently recorded that maize's accessible stock F = sum(stock) -
lean_need - locked goes NEGATIVE at exactly one step, t=22, where F = -15.2
MMT against a twin of 207.1 MMT, and that the regularised ratio there is
35.10 against an unregularised -13.64. Rice's F is negative at 58 of 144
steps.

Hypothesis: the spike, the fragility and the negative-F regime are one
phenomenon. When F < 0 the regulariser f_t = 0.05*sum(safety) +
max(0, -min(F, F_twin)) makes the denominator F + f_t collapse to
0.05*sum(safety), so the ratio becomes (F_twin - F + 0.05*sum(safety)) /
(0.05*sum(safety)) -- a number of order F_twin / (0.05*sum(safety)), which
for maize is 207 / 6.5 = 32. The price then follows p0 * r^inv_eta.

If that is right, the scarcity ratio is not measuring scarcity in this
regime; it is measuring how far the lean requirement exceeds physical
stock, divided by an arbitrary constant.

This script confirms the mechanism and prototypes one bounded alternative.
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
    prepare_crop_run,
    result_to_monthly,
    run_crop_dynamics,
    simulate_prep,
)
from score_subannual_crop import _corr, _hike  # noqa: E402

SRC = ROOT / "sheaf" / "dynamic_crop.py"
CROPS = ("wheat", "maize", "rice")
FULL = dict(use_amis=True, use_shocks=True, use_demand=False)

ORIG = """            floor0 = 0.05 * safety_w
            shift = floor0 + max(0.0, -min(free, twin))
            ratio = (twin + shift) / (free + shift)"""
# Bounded alternative: measure scarcity against PHYSICAL world stock, which
# cannot go negative, instead of against a forward requirement that can.
# The lean requirement still enters, but as a floor on the denominator
# rather than through an unbounded shift.
FIXED = """            floor0 = 0.05 * safety_w
            _phys = float(stock.sum())
            _den = max(free, 0.10 * _phys)
            ratio = (max(twin, 0.10 * _phys) + floor0) / (_den + floor0)"""


def build_fixed():
    src = SRC.read_text()
    if ORIG not in src:
        raise SystemExit("scarcity block not found verbatim")
    mod = types.ModuleType("sheaf.dc_scarfix")
    mod.__package__ = "sheaf"
    mod.__file__ = str(SRC)
    sys.modules["sheaf.dc_scarfix"] = mod
    exec(compile(src.replace(ORIG, FIXED), mod.__file__, "exec"), mod.__dict__)
    return mod


def main():
    lines = []

    def out(s=""):
        print(s)
        lines.append(s)

    obs_all = load_price_series_monthly(deflated=True)
    rows = []

    out("# R0e — the negative-accessible-stock regime\n")

    out("## 1. Confirming the mechanism\n")
    out("| crop | steps with F<0 | worst F | F_twin there | ratio there "
        "| price step before/after | 0.05*sum(safety) |")
    out("|---|---|---|---|---|---|---|")
    for crop in CROPS:
        prep = prepare_crop_run(crop, **FULL)
        res = simulate_prep(prep)
        F, Ftw = res.free_liquid, res.free_twin
        sw = float(max(prep.safety.sum(), 1.0))
        f0 = 0.05 * sw
        neg = np.flatnonzero(F < 0)
        i = int(np.argmin(F))
        shift = f0 + max(0.0, -min(F[i], Ftw[i]))
        ratio = (Ftw[i] + shift) / (F[i] + shift)
        pb = res.price[i - 1] if i > 0 else res.price[i]
        out(f"| {crop} | {len(neg)}/144 | {F[i]:.1f} | {Ftw[i]:.1f} "
            f"| {ratio:.2f} | {pb:.1f} -> {res.price[i]:.1f} $/t "
            f"| {f0:.2f} MMT |")
        rows.append(dict(crop=crop, kind="mechanism", n_neg=len(neg),
                         worst_F=float(F[i]), twin_there=float(Ftw[i]),
                         ratio_there=float(ratio), step=i,
                         price_before=float(pb),
                         price_at=float(res.price[i]), floor0=f0))
    out("")
    out("The ratio in the negative regime is of order F_twin / (0.05*sum(")
    out("safety)), which is a property of the regulariser rather than of")
    out("scarcity. Confirmed if the ratio above is close to that quotient.\n")

    out("## 2. A bounded alternative\n")
    out("Denominator floored at 10% of physical world stock, which cannot go")
    out("negative, instead of shifted by an unbounded state-dependent term.")
    out("One new constant, no new free parameter beyond the 0.10 floor, and")
    out("the unbounded branch disappears. This is a PROBE, not a proposal.\n")
    fix = build_fixed()
    out("| crop | metric | published | bounded ratio | Δ |")
    out("|---|---|---|---|---|")
    for crop in CROPS:
        obs = obs_all[(obs_all.year >= 2006) & (obs_all.year <= 2011)][
            ["year", "month", crop]].rename(columns={crop: "obs_price"})
        for label, mod in (("published", None), ("bounded", fix)):
            if mod is None:
                m = result_to_monthly(run_crop_dynamics(crop, **FULL))
            else:
                m = mod.result_to_monthly(mod.run_crop_dynamics(crop, **FULL))
            c = _corr(m.merge(obs, on=["year", "month"],
                              how="left").model_price,
                      m.merge(obs, on=["year", "month"],
                              how="left").obs_price)
            h07 = _hike(m, "model_price", 2006, 6, 2008, 3)
            h10 = _hike(m, "model_price", 2009, 6, 2011, 2)
            if label == "published":
                base = (c, h07, h10)
            else:
                out(f"| {crop} | corr | {base[0]:+.3f} | {c:+.3f} "
                    f"| {c-base[0]:+.3f} |")
                out(f"| {crop} | 2007/08 | x{base[1]:.2f} | x{h07:.2f} "
                    f"| {h07-base[1]:+.3f} |")
                out(f"| {crop} | 2010/11 | x{base[2]:.2f} | x{h10:.2f} "
                    f"| {h10-base[2]:+.3f} |")
                rows.append(dict(crop=crop, kind="bounded_probe",
                                 corr_pub=base[0], corr_fix=c,
                                 h07_pub=base[1], h07_fix=h07,
                                 h10_pub=base[2], h10_fix=h10))
    out("")

    out("## 3. Does the bounded ratio remove the fragility?\n")
    out("Same ~1% recalibration probe as R0c/R0d, on the bounded version.\n")
    out("| crop | version | end 2011 | end 2012 | end 2013 | spread |")
    out("|---|---|---|---|---|---|")
    for crop in CROPS:
        obs = obs_all[(obs_all.year >= 2006) & (obs_all.year <= 2011)][
            ["year", "month", crop]].rename(columns={crop: "obs_price"})
        for label, mod in (("published", None), ("bounded", fix)):
            vals = []
            for end in (2011, 2012, 2013):
                runner = (run_crop_dynamics if mod is None
                          else mod.run_crop_dynamics)
                conv = (result_to_monthly if mod is None
                        else mod.result_to_monthly)
                m = conv(runner(crop, start_year=2006, end_year=end, **FULL))
                m = m[(m.year >= 2006) & (m.year <= 2011)]
                mm = m.merge(obs, on=["year", "month"], how="left")
                vals.append(_corr(mm.model_price, mm.obs_price))
            sp = max(vals) - min(vals)
            out(f"| {crop} | {label} | {vals[0]:+.3f} | {vals[1]:+.3f} "
                f"| {vals[2]:+.3f} | **{sp:.3f}** |")
            rows.append(dict(crop=crop, kind="fragility", version=label,
                             corr_2011=vals[0], corr_2012=vals[1],
                             corr_2013=vals[2], spread=sp))
    out("")
    out("## Reading\n")
    out("The probe earns consideration only if it both (a) removes the")
    out("unbounded branch and the 4x transient, and (b) collapses the maize")
    out("spread, without wrecking the scores. If it collapses the spread but")
    out("costs a lot of correlation, that is a real trade and belongs in front")
    out("of the coauthors, not in a silent commit.\n")

    dest = ROOT / "diagnostics" / "redteam" / "r0"
    dest.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(dest / "negative_free_regime.csv", index=False)
    (dest / "R0E_NEGATIVE_FREE.md").write_text("\n".join(lines) + "\n")
    print(f"\nwrote {(dest / 'R0E_NEGATIVE_FREE.md').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
