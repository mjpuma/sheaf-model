#!/usr/bin/env python3
"""A1b: why does the calm branch have work to do?

H2 established that disabling the `calm` short-circuit lets the world price
drift 19-34% in a run with no harvest anomaly, no AMIS, and no demand
shifter. That means the ask law has no rest point at p0. This script asks
why, and whether the target fill is simply mis-set.

Read-only with respect to sheaf/*.py: the module is recompiled in memory.
"""
from __future__ import annotations

import sys
import types
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from sheaf.calendar24 import STEPS_PER_YEAR  # noqa: E402
from sheaf.dynamic_crop import default_crop_params, run_crop_dynamics  # noqa: E402

CROPS = ("wheat", "maize", "rice")
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
PROBE_AT = "        p = float(smooth * p + (1.0 - smooth) * p_star)"
PROBE = """        _DIAG.append((float(p_trade), float(p_star), float(block_frac),
                      float(np.mean(fill)), float(np.min(fill)),
                      float(np.max(fill))))
        p = float(smooth * p + (1.0 - smooth) * p_star)"""


def build(name: str, calm: bool):
    src = SRC.read_text()
    if not calm:
        src = src.replace(CALM_ORIG, CALM_OFF)
    src = src.replace(PROBE_AT, PROBE)
    mod = types.ModuleType(f"sheaf.{name}")
    mod.__package__ = "sheaf"
    mod.__file__ = str(SRC)
    mod.__dict__["_DIAG"] = []
    sys.modules[f"sheaf.{name}"] = mod
    exec(compile(src, mod.__file__, "exec"), mod.__dict__)
    return mod


CALM_KW = dict(use_amis=False, use_shocks=False, use_demand=False,
               use_industrial=False)
FULL_KW = dict(use_amis=True, use_shocks=True, use_demand=False)


def main():
    lines = []

    def out(s=""):
        print(s)
        lines.append(s)

    on = build("dc_probe_on", calm=True)
    off = build("dc_probe_off", calm=False)

    out("# A1b — why the calm branch has work to do\n")
    out("The matched configuration (no harvest anomaly, no AMIS, no demand")
    out("shifter) is the one in which the note claims p* = p0 follows by")
    out("algebra. Below, what the pieces of eq (16) actually do in that run.\n")

    out("## The trade-weighted offer price in a matched run\n")
    out("p* = omega*p_tr + (1-omega)*p_scar. In a matched run p_scar = p0")
    out("exactly, so p* = p0 requires p_tr = p0.\n")
    rows = []
    for crop in CROPS:
        on.__dict__["_DIAG"].clear()
        res = on.run_crop_dynamics(crop, **CALM_KW)
        d = np.array(on.__dict__["_DIAG"], float)
        # the twin runs first inside prepare_crop_run; keep the last T rows
        T = len(res.price)
        d = d[-T:]
        p_tr, p_star, blk, f_mean, f_min, f_max = d.T
        p0 = float(res.price[0])
        w = default_crop_params(crop).trade_w
        theta = default_crop_params(crop).ask_target_fill
        implied = w * p_tr + (1.0 - w) * p0
        out(f"### {crop}  (omega = {w:.2f}, theta = {theta:.2f}, p0 = {p0:.1f} $/t)")
        out(f"- p_tr / p0: mean {np.mean(p_tr)/p0:.3f}, "
            f"range {np.min(p_tr)/p0:.3f}-{np.max(p_tr)/p0:.3f}")
        out(f"- so omega*p_tr + (1-omega)*p0 would sit at "
            f"{np.mean(implied)/p0:.3f} x p0 on average, "
            f"up to {np.max(implied)/p0:.3f} x p0")
        out(f"- realised fill in the matched run: mean {np.mean(f_mean):.3f}, "
            f"per-step min {np.min(f_min):.3f}, max {np.max(f_max):.3f}")
        out(f"- **target fill theta = {theta:.2f} versus realised mean "
            f"{np.mean(f_mean):.3f}** -> asks are pushed "
            f"{'UP' if np.mean(f_mean) > theta else 'DOWN'} every step even "
            f"with no shock\n")
        rows.append((crop, float(np.mean(f_mean)), float(theta)))

    out("## Does re-targeting theta remove the need for the branch?\n")
    out("Set ask_target_fill to the realised matched-run mean fill, disable the")
    out("calm branch, and re-measure the drift that assert_twin_identity")
    out("tolerates at 2%. This is calibration to the model's own calm state,")
    out("not to a crisis window.\n")
    for crop, f_calm, theta in rows:
        base_off = off.run_crop_dynamics(crop, **CALM_KW)
        tuned_off = off.run_crop_dynamics(crop, ask_target_fill=f_calm, **CALM_KW)
        tuned_on = on.run_crop_dynamics(crop, ask_target_fill=f_calm, **CALM_KW)
        p0 = float(base_off.price[0])

        def drift(res):
            return float(np.max(np.abs(res.price[STEPS_PER_YEAR:] - p0)) / p0)

        out(f"### {crop}")
        out(f"- theta {theta:.2f} -> {f_calm:.3f}")
        out(f"- drift, branch off, theta as shipped:  {100*drift(base_off):7.3f}%"
            f"  {'PASS' if drift(base_off) <= 0.02 else 'FAIL'}")
        out(f"- drift, branch off, theta re-targeted: {100*drift(tuned_off):7.3f}%"
            f"  {'PASS' if drift(tuned_off) <= 0.02 else 'FAIL'}")
        out(f"- drift, branch on,  theta re-targeted: {100*drift(tuned_on):7.3f}%"
            f"  (sanity: the branch pins this regardless)\n")

    out("## What re-targeting theta does to the official scores\n")
    out("Reported for completeness. A change that improves a crisis score is")
    out("not thereby justified; per CLAUDE.md the 2007/08 window is not a")
    out("fitting target. These numbers exist so the cost of the fix is visible.\n")
    sys.path.insert(0, str(ROOT / "scripts"))
    from score_subannual_crop import _corr, _hike  # noqa: E402
    from sheaf.data_usda import load_price_series_monthly  # noqa: E402
    from sheaf.dynamic_crop import result_to_monthly  # noqa: E402

    obs_all = load_price_series_monthly(deflated=True)
    for crop, f_calm, theta in rows:
        obs = obs_all[(obs_all.year >= 2006) & (obs_all.year <= 2011)][
            ["year", "month", crop]].rename(columns={crop: "obs_price"})
        out(f"### {crop}")
        for label, kw in (("as shipped", {}),
                          ("theta re-targeted", {"ask_target_fill": f_calm})):
            res = run_crop_dynamics(crop, **FULL_KW, **kw)
            m = result_to_monthly(res).merge(obs, on=["year", "month"],
                                             how="left")
            c = _corr(m.model_price, m.obs_price)
            h07 = _hike(m, "model_price", 2006, 6, 2008, 3)
            h10 = _hike(m, "model_price", 2009, 6, 2011, 2)
            out(f"- {label:18s} corr {c:+.3f}   2007/08 x{h07:.2f}   "
                f"2010/11 x{h10:.2f}")
        o07 = _hike(obs, "obs_price", 2006, 6, 2008, 3)
        o10 = _hike(obs, "obs_price", 2009, 6, 2011, 2)
        out(f"- observed            2007/08 x{o07:.2f}   2010/11 x{o10:.2f}\n")

    dest = ROOT / "diagnostics" / "gate0_prep" / "a1"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "A1B_CALM_FIXED_POINT.md").write_text("\n".join(lines) + "\n")
    print(f"\nwrote {(dest / 'A1B_CALM_FIXED_POINT.md').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
