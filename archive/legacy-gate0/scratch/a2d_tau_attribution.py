#!/usr/bin/env python3
"""A2d: does the calm conditional contaminate the attribution table?

A1c found the conditional fires 0/144 steps in the official and harvest-only
legs, which suggested no scored number depends on it. But it fires 24-32
steps in the RESTRICTION-ONLY leg, and that leg supplies the `tau` column of
the attribution table in diagnostics/gate0_*_report.md -- the number cited
as evidence that 2007/08 is restriction-led.

A2c showed why that matters: the conditional pins a matched run at exactly
p0, while the offer-price law's own level in a quiet market is well below
p0 (0.66 p0 wheat, 0.71 p0 maize). So a hike ratio whose BASE window is
pinned and whose PEAK window is not is measuring the release of the pin as
well as the restriction.

This script locates the pinned steps relative to the scoring windows and
recomputes the affected ratios with the conditional disabled.

Read-only with respect to sheaf/*.py.
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

SRC = ROOT / "sheaf" / "dynamic_crop.py"
CROPS = ("wheat", "maize", "rice")

CALM_ORIG = """            calm = (abs(free - twin) < 1e-6 and u_anom < 1e-9
                    and block_frac < 1e-9)
            if calm:
                p_star = p0
            else:"""
CALM_OFF = """            calm = False
            if calm:
                p_star = p0
            else:"""
CALM_DEF_AT = "    for t in range(T):"
CALM_DEF = "    calm = False\n    for t in range(T):"
PROBE_AT = "        p = float(smooth * p + (1.0 - smooth) * p_star)"
PROBE = """        _DIAG.append(1.0 if (free_twin is not None and calm) else 0.0)
        p = float(smooth * p + (1.0 - smooth) * p_star)"""

TAU_KW = dict(use_amis=True, use_shocks=False, use_demand=False,
              use_industrial=False)
WINDOWS = (("2007/08", 2006, 6, 2008, 3), ("2010/11", 2009, 6, 2011, 2))


def build(name, calm=True):
    src = SRC.read_text()
    if not calm:
        src = src.replace(CALM_ORIG, CALM_OFF)
    src = src.replace(CALM_DEF_AT, CALM_DEF, 1).replace(PROBE_AT, PROBE)
    mod = types.ModuleType(f"sheaf.{name}")
    mod.__package__ = "sheaf"
    mod.__file__ = str(SRC)
    mod.__dict__["_DIAG"] = []
    sys.modules[f"sheaf.{name}"] = mod
    exec(compile(src, mod.__file__, "exec"), mod.__dict__)
    return mod


def main():
    lines = []

    def out(s=""):
        print(s)
        lines.append(s)

    from score_subannual_crop import _hike  # noqa: E402
    from sheaf.data_usda import load_price_series_monthly  # noqa: E402

    on = build("dc_a2d_on", calm=True)
    off = build("dc_a2d_off", calm=False)
    obs_all = load_price_series_monthly(deflated=True)

    out("# A2d — the conditional and the attribution table\n")
    out("The `tau` column of the attribution table comes from the")
    out("restriction-only leg (use_amis=True, use_shocks=False). The")
    out("conditional fires in that leg. Below: where it fires relative to the")
    out("scoring windows, and what the ratios become without it.\n")

    rows = []
    for crop in CROPS:
        on.__dict__["_DIAG"].clear()
        res_on = on.run_crop_dynamics(crop, **TAU_KW)
        fired = np.array(on.__dict__["_DIAG"][-len(res_on.price):], float)
        res_off = off.run_crop_dynamics(crop, **TAU_KW)

        m_on = on.result_to_monthly(res_on)
        m_off = off.result_to_monthly(res_off)
        obs = obs_all[(obs_all.year >= 2006) & (obs_all.year <= 2011)][
            ["year", "month", crop]].rename(columns={crop: "obs_price"})

        out(f"## {crop}\n")
        p0 = float(res_on.price[0])
        out(f"- conditional fires at {int(fired.sum())}/{len(fired)} steps of "
            f"the restriction-only leg")
        # where, in calendar terms
        idx = np.flatnonzero(fired > 0)
        if len(idx):
            def cal(t):
                y = 2006 + t // STEPS_PER_YEAR
                mo = 1 + (t % STEPS_PER_YEAR) // 2
                return f"{y}-{mo:02d}"
            out(f"- first fires {cal(idx[0])}, last {cal(idx[-1])}; "
                f"contiguous from the start: "
                f"{'yes' if np.array_equal(idx, np.arange(len(idx))) else 'no'}")
        for label, a0, b0, a1, b1 in WINDOWS:
            h_on = _hike(m_on, "model_price", a0, b0, a1, b1)
            h_off = _hike(m_off, "model_price", a0, b0, a1, b1)
            h_obs = _hike(obs, "obs_price", a0, b0, a1, b1)
            out(f"- {label}: tau hike as published **x{h_on:.2f}**, "
                f"without the conditional **x{h_off:.2f}** "
                f"(observed x{h_obs:.2f})")
            rows.append(dict(crop=crop, window=label, tau_published=h_on,
                             tau_no_conditional=h_off, observed=h_obs,
                             fired=int(fired.sum())))
        # base-window level, which is what the pin distorts
        base_on = m_on[(m_on.year == 2006) & (m_on.month.between(5, 7))].model_price.mean()
        base_off = m_off[(m_off.year == 2006) & (m_off.month.between(5, 7))].model_price.mean()
        out(f"- 2007/08 base window level: pinned {base_on:.1f} vs unpinned "
            f"{base_off:.1f} $/t (p0 = {p0:.1f})\n")

    out("## Reading\n")
    out("If the published tau ratio is materially above the unpinned one, the")
    out("attribution number is partly an artifact of comparing a pinned base")
    out("against an unpinned peak, and the restriction-led claim for that crop")
    out("needs restating. A1c's 'no scored number depends on the conditional'")
    out("was too strong: it holds for the price correlation and for the full")
    out("and harvest-only hike ratios, not for the tau column.\n")

    dest = ROOT / "diagnostics" / "gate0_prep" / "a2"
    dest.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(dest / "tau_attribution.csv", index=False)
    (dest / "A2D_TAU_ATTRIBUTION.md").write_text("\n".join(lines) + "\n")
    print(f"\nwrote {(dest / 'A2D_TAU_ATTRIBUTION.md').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
