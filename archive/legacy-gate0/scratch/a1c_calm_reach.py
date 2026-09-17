#!/usr/bin/env python3
"""A1c: does the calm branch affect any scored result?

A1b showed the branch is what makes the reference identity hold, and that
re-targeting theta does not rescue it. The remaining question decides how
serious that is: if the branch never fires in a scored configuration, it
changes no published number and the defect is confined to the claim we make
about the model, not to the model's output.

Read-only with respect to sheaf/*.py.
"""
from __future__ import annotations

import sys
import types
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from sheaf.calendar24 import STEPS_PER_YEAR  # noqa: E402

CROPS = ("wheat", "maize", "rice")
SRC = ROOT / "sheaf" / "dynamic_crop.py"

PROBE_AT = "        p = float(smooth * p + (1.0 - smooth) * p_star)"
PROBE = """        _DIAG.append((float(p_star), 1.0 if (free_twin is not None and calm)
                      else 0.0, float(free_twin[t]) if free_twin is not None
                      else float('nan'), float(free)))
        p = float(smooth * p + (1.0 - smooth) * p_star)"""
# `calm` is only bound inside the treatment branch; give it a default so the
# twin pass (free_twin is None) does not raise a NameError.
CALM_DEF_AT = "    for t in range(T):"
CALM_DEF = "    calm = False\n    for t in range(T):"


def build():
    src = SRC.read_text()
    src = src.replace(CALM_DEF_AT, CALM_DEF, 1).replace(PROBE_AT, PROBE)
    mod = types.ModuleType("sheaf.dc_calmcount")
    mod.__package__ = "sheaf"
    mod.__file__ = str(SRC)
    mod.__dict__["_DIAG"] = []
    sys.modules["sheaf.dc_calmcount"] = mod
    exec(compile(src, mod.__file__, "exec"), mod.__dict__)
    return mod


LEGS = {
    "full (official)": dict(use_amis=True, use_shocks=True, use_demand=False),
    "shocks only": dict(use_amis=False, use_shocks=True, use_demand=False),
    "tau only": dict(use_amis=True, use_shocks=False, use_demand=False,
                     use_industrial=False),
    "matched (assert)": dict(use_amis=False, use_shocks=False,
                             use_demand=False, use_industrial=False),
}


def main():
    lines = []

    def out(s=""):
        print(s)
        lines.append(s)

    mod = build()
    out("# A1c — does the calm branch touch a scored result?\n")
    out("Counts steps where the branch fires (`free_twin` set, and")
    out("|free-twin| < 1e-6, u_anom < 1e-9, block_frac < 1e-9), per leg.")
    out("144 steps per run.\n")

    for crop in CROPS:
        out(f"## {crop}\n")
        for label, kw in LEGS.items():
            mod.__dict__["_DIAG"].clear()
            res = mod.run_crop_dynamics(crop, **kw)
            d = np.array(mod.__dict__["_DIAG"], float)
            T = len(res.price)
            d = d[-T:]
            fired = int(d[:, 1].sum())
            p0 = float(res.price[0]) if label == "matched (assert)" else None
            extra = ""
            if p0 is not None:
                drift = np.max(np.abs(res.price[STEPS_PER_YEAR:] - p0)) / p0
                extra = f", price drift {100*drift:.3f}%"
            out(f"- {label:18s} calm fires {fired:3d}/{T} steps{extra}")
        out("")

    out("## Reading\n")
    out("If the branch fires only in the matched configuration, then it")
    out("determines whether `assert_twin_identity` passes but changes no")
    out("number in `diagnostics/gate0_*_report.md`. The defect is then in the")
    out("claim -- the note calls the identity algebraic when it is enforced --")
    out("and not in any scored output. If it also fires in the scored legs,")
    out("that is a different and larger problem.\n")

    dest = ROOT / "diagnostics" / "gate0_prep" / "a1"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "A1C_CALM_REACH.md").write_text("\n".join(lines) + "\n")
    print(f"\nwrote {(dest / 'A1C_CALM_REACH.md').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
