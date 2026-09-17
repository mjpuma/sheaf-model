#!/usr/bin/env python3
"""R2 shared harness: baseline reproduction + in-memory recompile of
``sheaf/dynamic_crop.py`` with demand-side patches.

Read-only with respect to ``sheaf/*.py``: every variant is produced by
``exec``-compiling the module source with a textual substitution, exactly as
``scripts/scratch/a1_equation_audit.py`` does.
"""
from __future__ import annotations

import sys
import types
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
_SCRIPTS = str(ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

SRC = ROOT / "sheaf" / "dynamic_crop.py"
CROPS = ("wheat", "maize", "rice")
OUT = ROOT / "diagnostics" / "redteam" / "r2"
FIGS = ROOT / "figures" / "scratch" / "r2"
OUT.mkdir(parents=True, exist_ok=True)
FIGS.mkdir(parents=True, exist_ok=True)

# Published baselines quoted in the R2 brief (corr, hike 2007/08, hike 2010/11).
BASELINE = {
    "wheat": (0.720, 2.27, 1.45),
    "maize": (0.712, 1.97, 1.70),
    "rice": (0.678, 1.72, 0.82),
}
OBS_HIKE = {"wheat": (1.82, 1.16), "maize": (1.84, 1.44), "rice": (1.84, 0.79)}

WIN_0708 = (2006, 6, 2008, 3)
WIN_1011 = (2009, 6, 2011, 2)


def load_variant(name: str, subs: list[tuple[str, str]] | None = None):
    """Recompile ``sheaf.dynamic_crop`` under a new module name with textual
    substitutions applied. Every ``old`` must appear verbatim."""
    src = SRC.read_text()
    for old, new in (subs or []):
        if old not in src:
            raise SystemExit(f"[{name}] anchor not found verbatim:\n{old[:300]}")
        src = src.replace(old, new, 1)
    modname = f"sheaf.dynamic_crop_{name}"
    mod = types.ModuleType(modname)
    mod.__package__ = "sheaf"
    mod.__file__ = str(SRC)
    sys.modules[modname] = mod
    exec(compile(src, mod.__file__, "exec"), mod.__dict__)
    return mod


def score_leg(mod, crop: str, **kw):
    """Official P1 'full' leg: harvest + AMIS + mean flex (+industrial)."""
    return mod.run_crop_dynamics(crop, start_year=2006, end_year=2011,
                                 use_amis=True, use_shocks=True,
                                 use_demand=False, **kw)


def official_scores(mod, crop: str, **kw) -> dict:
    """corr / hike07 / hike10 for the official 'full' leg, using _corr and
    _hike imported from scripts/score_subannual_crop.py."""
    from score_subannual_crop import _corr, _hike
    from sheaf.data_usda import load_price_series_monthly

    res = score_leg(mod, crop, **kw)
    m = mod.result_to_monthly(res)
    obs = load_price_series_monthly(deflated=True)
    obs = obs[(obs.year >= 2006) & (obs.year <= 2011)][
        ["year", "month", crop]].rename(columns={crop: "obs_price"})
    m = m.merge(obs, on=["year", "month"], how="left")
    return dict(
        crop=crop,
        corr=_corr(m.model_price, m.obs_price),
        hike0708=_hike(m, "model_price", *WIN_0708),
        hike1011=_hike(m, "model_price", *WIN_1011),
        res=res, monthly=m,
    )


def assert_report(mod, crop: str, **kw) -> dict:
    """Run the four robustness asserts, returning pass/fail + message."""
    out = {}
    for label, fn in (
            ("twin", mod.assert_twin_identity),
            ("amis_price", mod.assert_amis_raises_price),
            ("amis_exports", mod.assert_amis_cuts_exports),
            ("spring", mod.assert_no_spring_spike),
    ):
        try:
            fn(crop, **kw)
            out[label] = "PASS"
        except AssertionError as e:
            out[label] = f"FAIL: {e}"
        except Exception as e:  # noqa: BLE001
            out[label] = f"ERROR: {type(e).__name__}: {e}"
    return out


def fmt_scores(tag: str, rows: list[dict]) -> str:
    lines = [f"### {tag}", "",
             "| crop | corr | 2007/08 | 2010/11 | published corr/h07/h10 |",
             "|---|---|---|---|---|"]
    for r in rows:
        b = BASELINE[r["crop"]]
        lines.append(
            f"| {r['crop']} | {r['corr']:+.3f} | x{r['hike0708']:.2f} | "
            f"x{r['hike1011']:.2f} | {b[0]:+.3f} / x{b[1]:.2f} / x{b[2]:.2f} |")
    return "\n".join(lines)
