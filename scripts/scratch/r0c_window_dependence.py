#!/usr/bin/env python3
"""R0c: decompose SHEAF's window dependence.

R0b extended the simulation past 2011 and found the 2006-2011 maize price
correlation moving from +0.712 to +0.276 to +0.832 while the scored months
stayed identical. That test conflated two channels, and the 2007/08 control
moved too, so it cannot be read as published.

Channel A, RECALIBRATION. prepare_crop_run defines its reference objects as
means over the simulated years: C_ann is mean PSD consumption over `years`
(~L742-745), safety = stu_target * C_ann (~L746), C_flex_mean and hence the
twin's demand are means over `years` (~L750-752), and mean_prod and hence
H_seas and the spin-up are means over `years` (~L755-762). Change end_year
and all of those move, so the whole path moves, not just its tail.

Channel B, TRUNCATION. rolling_ahead_variable clips the forward window at
the array end (sheaf/seasonal.py L158), so the last MAX_LEAN_STEPS = 24
steps have a short lean-cover horizon.

This script separates them. Channel A is measured by comparing the prep
arrays themselves. Channel B is measured by padding the lean-window inputs
with a repeat of the final year, holding every calibrated object fixed.

Read-only; the module is recompiled in memory for the padding test.
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

from sheaf.calendar24 import STEPS_PER_YEAR  # noqa: E402
from sheaf.data_usda import load_price_series_monthly  # noqa: E402
from sheaf.dynamic_crop import prepare_crop_run, result_to_monthly  # noqa: E402
from score_subannual_crop import _corr, _hike  # noqa: E402

SRC = ROOT / "sheaf" / "dynamic_crop.py"
CROPS = ("wheat", "maize", "rice")
FULL = dict(use_amis=True, use_shocks=True, use_demand=False)

# Pad the lean-window inputs by one repeated year so the horizon is never
# clipped, then slice the result back. Everything else is untouched.
PAD_ORIG = """    lean_h = steps_to_harvest_pulse(
        H_exp, frac=params.harvest_pulse_frac, max_horizon=MAX_LEAN_STEPS)
    H_ahead = rolling_ahead_variable(H_exp, lean_h)
    C_ahead = rolling_ahead_variable(C_step, lean_h)"""
PAD_NEW = """    _pad = STEPS_PER_YEAR
    _He = np.concatenate([H_exp, H_exp[:, -_pad:]], axis=1)
    _Cs = np.concatenate([C_step, C_step[:, -_pad:]], axis=1)
    lean_h = steps_to_harvest_pulse(
        _He, frac=params.harvest_pulse_frac, max_horizon=MAX_LEAN_STEPS)
    H_ahead = rolling_ahead_variable(_He, lean_h)[:, :T]
    C_ahead = rolling_ahead_variable(_Cs, lean_h)[:, :T]
    lean_h = lean_h[:T]"""


def build_padded():
    src = SRC.read_text()
    if PAD_ORIG not in src:
        raise SystemExit("lean-window block not found verbatim")
    mod = types.ModuleType("sheaf.dc_pad")
    mod.__package__ = "sheaf"
    mod.__file__ = str(SRC)
    sys.modules["sheaf.dc_pad"] = mod
    exec(compile(src.replace(PAD_ORIG, PAD_NEW), mod.__file__, "exec"),
         mod.__dict__)
    return mod


def score(m, obs, crop):
    mm = m.merge(obs, on=["year", "month"], how="left")
    return (_corr(mm.model_price, mm.obs_price),
            _hike(m, "model_price", 2006, 6, 2008, 3),
            _hike(m, "model_price", 2009, 6, 2011, 2))


def main():
    lines = []

    def out(s=""):
        print(s)
        lines.append(s)

    obs_all = load_price_series_monthly(deflated=True)
    rows = []

    out("# R0c — decomposing SHEAF's window dependence\n")

    out("## Channel A — the reference objects are in-sample means\n")
    out("How much the calibrated objects move when end_year goes 2011 to 2012,")
    out("with start_year fixed. These are the same physical years in both runs.\n")
    out("| crop | Δ p0 | Δ sum(C_ann) | Δ sum(safety) | Δ H_seas over common steps | Δ stock0 |")
    out("|---|---|---|---|---|---|")
    for crop in CROPS:
        a = prepare_crop_run(crop, start_year=2006, end_year=2011, **FULL)
        b = prepare_crop_run(crop, start_year=2006, end_year=2012, **FULL)
        T = a.H.shape[1]
        dH = float(np.abs(b.H_seas[:, :T] - a.H_seas[:, :T]).max())
        out(f"| {crop} | {b.p0-a.p0:+.3f} $/t "
            f"| {b.C_ann.sum()-a.C_ann.sum():+.1f} MMT "
            f"| {b.safety.sum()-a.safety.sum():+.2f} MMT "
            f"| max |Δ| {dH:.4f} MMT "
            f"| max |Δ| {float(np.abs(b.stock0-a.stock0).max()):.3f} MMT |")
        rows.append(dict(crop=crop, channel="recalibration",
                         d_p0=b.p0 - a.p0,
                         d_cann=float(b.C_ann.sum() - a.C_ann.sum()),
                         d_safety=float(b.safety.sum() - a.safety.sum()),
                         d_hseas_max=dH,
                         d_stock0_max=float(np.abs(b.stock0 - a.stock0).max())))
    out("")
    out("If these are nonzero, R0b's extended-window test was confounded and")
    out("its maize swing cannot be attributed to the horizon. More important,")
    out("it means the scored path is a function of the window chosen.\n")

    out("## Channel B — truncation alone, everything else held fixed\n")
    out("Lean-window inputs padded with a repeat of the final year, so the")
    out("horizon is never clipped. Identical calibration, identical forcing,")
    out("identical scored months.\n")
    pad = build_padded()
    out("| crop | metric | published | horizon padded | Δ |")
    out("|---|---|---|---|---|")
    for crop in CROPS:
        obs = obs_all[(obs_all.year >= 2006) & (obs_all.year <= 2011)][
            ["year", "month", crop]].rename(columns={crop: "obs_price"})
        prep = prepare_crop_run(crop, start_year=2006, end_year=2011, **FULL)
        base = result_to_monthly(
            __import__("sheaf.dynamic_crop", fromlist=["x"])
            .simulate_prep(prep))
        prep_p = pad.prepare_crop_run(crop, start_year=2006, end_year=2011,
                                      **FULL)
        padded = pad.result_to_monthly(pad.simulate_prep(prep_p))
        for name, i in (("corr", 0), ("2007/08", 1), ("2010/11", 2)):
            va = score(base, obs, crop)[i]
            vb = score(padded, obs, crop)[i]
            fmt = "{:+.3f}" if name == "corr" else "x{:.2f}"
            out(f"| {crop} | {name} | {fmt.format(va)} | {fmt.format(vb)} "
                f"| {vb-va:+.3f} |")
            rows.append(dict(crop=crop, channel="truncation", metric=name,
                             published=va, padded=vb, delta=vb - va))
    out("")

    out("## Reading\n")
    out("Channel B is the narrow, fixable artifact: pad the lean window and")
    out("the last year stops seeing a short horizon. Channel A is the larger")
    out("question, and it is not a bug -- using in-sample means for the")
    out("climatology is a deliberate and disclosed choice. But it does mean")
    out("the headline scores are conditional on the 2006-2011 window, and if")
    out("Channel A moves a score by more than Channel B, the honest")
    out("robustness statement is about the window, not the horizon.\n")

    dest = ROOT / "diagnostics" / "redteam" / "r0"
    dest.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(dest / "window_decomposition.csv", index=False)
    (dest / "R0C_WINDOW_DEPENDENCE.md").write_text("\n".join(lines) + "\n")
    print(f"\nwrote {(dest / 'R0C_WINDOW_DEPENDENCE.md').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
