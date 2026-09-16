#!/usr/bin/env python3
"""R0g: falsifying the surgical fix -- is the 0.10 floor just another knob?

R0f's fix floors the scarcity denominator at 0.10 * physical world stock in
the one regime where F < 0 <= F_twin. That 0.10 is a new constant, and the
obvious objection is that it replaces an arbitrary constant (0.05 *
sum(safety), via the regulariser) with a differently arbitrary one.

The fix earns its place only if the results are insensitive to it over a
wide range. If maize's score and fragility move a lot with the coefficient,
the fix is a knob and should be rejected in favour of recording the
pathology and taking it to the coauthors.

Also tested here: the floor's binding frequency, and whether the fix
survives the ask_rival = 0 setting under which the maize sign condition is
nearly binding.

Read-only.
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
from score_subannual_crop import _corr, _hike  # noqa: E402

SRC = ROOT / "sheaf" / "dynamic_crop.py"
CROPS = ("wheat", "maize", "rice")
FULL = dict(use_amis=True, use_shocks=True, use_demand=False)

ORIG = """            floor0 = 0.05 * safety_w
            shift = floor0 + max(0.0, -min(free, twin))
            ratio = (twin + shift) / (free + shift)"""
TMPL = """            floor0 = 0.05 * safety_w
            if free < 0.0 <= twin:
                ratio = (twin + floor0) / ({phi} * float(stock.sum()) + floor0)
            else:
                shift = floor0 + max(0.0, -min(free, twin))
                ratio = (twin + shift) / (free + shift)"""


def build(phi, tag):
    src = SRC.read_text()
    mod = types.ModuleType(f"sheaf.dc_phi{tag}")
    mod.__package__ = "sheaf"
    mod.__file__ = str(SRC)
    sys.modules[f"sheaf.dc_phi{tag}"] = mod
    exec(compile(src.replace(ORIG, TMPL.format(phi=phi)), mod.__file__,
                 "exec"), mod.__dict__)
    return mod


def main():
    lines = []

    def out(s=""):
        print(s)
        lines.append(s)

    obs_all = load_price_series_monthly(deflated=True)
    rows = []

    out("# R0g — is the 0.10 floor a knob?\n")
    out("Sweeping the floor coefficient over a factor of eight. Wheat and")
    out("rice never enter the branch, so only maize can move.\n")
    out("| floor | maize corr | maize 2007/08 | maize 2010/11 | maize spread "
        "| wheat corr | rice corr |")
    out("|---|---|---|---|---|---|---|")

    phis = (0.05, 0.075, 0.10, 0.15, 0.20, 0.40)
    for k, phi in enumerate(phis):
        mod = build(phi, k)
        cell = {}
        for crop in CROPS:
            obs = obs_all[(obs_all.year >= 2006) & (obs_all.year <= 2011)][
                ["year", "month", crop]].rename(columns={crop: "obs_price"})
            m = mod.result_to_monthly(mod.run_crop_dynamics(crop, **FULL))
            mm = m.merge(obs, on=["year", "month"], how="left")
            c = _corr(mm.model_price, mm.obs_price)
            cell[crop] = (c, _hike(m, "model_price", 2006, 6, 2008, 3),
                          _hike(m, "model_price", 2009, 6, 2011, 2))
            if crop == "maize":
                v = []
                for end in (2011, 2012, 2013):
                    m2 = mod.result_to_monthly(mod.run_crop_dynamics(
                        crop, start_year=2006, end_year=end, **FULL))
                    m2 = m2[(m2.year >= 2006) & (m2.year <= 2011)]
                    mm2 = m2.merge(obs, on=["year", "month"], how="left")
                    v.append(_corr(mm2.model_price, mm2.obs_price))
                spread = max(v) - min(v)
        out(f"| {phi:.3f} | {cell['maize'][0]:+.3f} | x{cell['maize'][1]:.2f} "
            f"| x{cell['maize'][2]:.2f} | {spread:.3f} "
            f"| {cell['wheat'][0]:+.3f} | {cell['rice'][0]:+.3f} |")
        rows.append(dict(phi=phi, maize_corr=cell['maize'][0],
                         maize_h07=cell['maize'][1],
                         maize_h10=cell['maize'][2], maize_spread=spread,
                         wheat_corr=cell['wheat'][0],
                         rice_corr=cell['rice'][0]))
    out("")
    out("Published maize for comparison: +0.712 / x1.97 / x1.70, spread 0.557.")
    out("Observed maize: x1.84 (2007/08), x1.44 (2010/11).\n")

    out("## How often does the branch fire?\n")
    mod = build(0.10, 99)
    for crop in CROPS:
        r = mod.run_crop_dynamics(crop, **FULL)
        n = int(((r.free_liquid < 0) & (r.free_twin >= 0)).sum())
        out(f"- {crop}: F < 0 <= F_twin at **{n}/144** steps")
        rows.append(dict(phi=None, crop=crop, n_fire=n))
    out("")

    out("## Does the fix survive ask_rival = 0?\n")
    out("A2 established that ask_rival has no surviving justification but is")
    out("load-bearing for amplitude. If the fix only works at ask_rival =")
    out("0.80 it is entangled with a parameter that may not survive.\n")
    out("| crop | ask_rival | published | with fix |")
    out("|---|---|---|---|")
    for crop in CROPS:
        obs = obs_all[(obs_all.year >= 2006) & (obs_all.year <= 2011)][
            ["year", "month", crop]].rename(columns={crop: "obs_price"})
        for ar in (0.0, 0.80):
            import sheaf.dynamic_crop as base
            vals = []
            for label, mm_ in (("pub", base), ("fix", mod)):
                m = mm_.result_to_monthly(
                    mm_.run_crop_dynamics(crop, ask_rival=ar, **FULL))
                z = m.merge(obs, on=["year", "month"], how="left")
                vals.append(_corr(z.model_price, z.obs_price))
            out(f"| {crop} | {ar:.2f} | {vals[0]:+.3f} | {vals[1]:+.3f} |")
            rows.append(dict(phi=0.10, crop=crop, ask_rival=ar,
                             corr_pub=vals[0], corr_fix=vals[1]))
    out("")

    out("## Verdict criterion\n")
    out("The fix is defensible if maize's correlation and fragility are flat")
    out("across the floor sweep. It is a knob, and should be rejected, if the")
    out("score tracks the coefficient. Note that a floor which is never")
    out("binding for two of three crops cannot be a fitted parameter for")
    out("them -- the relevant question is entirely about maize.\n")

    dest = ROOT / "diagnostics" / "redteam" / "r0"
    dest.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(dest / "floor_sensitivity.csv", index=False)
    (dest / "R0G_FLOOR_SENSITIVITY.md").write_text("\n".join(lines) + "\n")
    print(f"\nwrote {(dest / 'R0G_FLOOR_SENSITIVITY.md').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
