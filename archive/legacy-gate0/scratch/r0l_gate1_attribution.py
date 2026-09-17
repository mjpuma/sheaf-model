#!/usr/bin/env python3
"""R0l: attribute the new Gate 1 rice spillover-sign failure.

After the two shipped fixes, Gate 1's spillover-sign hard bar fails for
rice at sigma=0.6 (x0.984, was x1.039). The bar asks that switching on
cross-commodity substitution raise the 2007/08 hike relative to sigma=0.
Rice at sigma=0.3 still passes (x1.029), so the failure is marginal and
confined to the largest substitution setting.

This attributes it to one fix or the other by reverting each in isolation
inside dynamic_coupled, in memory. Read-only.
"""
from __future__ import annotations

import sys
import types
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

SRC = ROOT / "sheaf" / "dynamic_coupled.py"

PT_NEW = "p_trade = (float(np.dot(ask_path[g][:, t], shipped) / shipped_sum)"
PT_OLD = "p_trade = (float(np.dot(ask_g, shipped) / shipped_sum)"

SC_NEW = """            if free < 0.0 <= twin:
                # Unbounded otherwise: the shift would reduce the denominator
                # to floor0 and the ratio would be twin/floor0, set by the
                # regulariser rather than by scarcity. Mirrors the same fix
                # in dynamic_crop._simulate_window.
                ratio = (twin + floor0) / (0.10 * float(st.sum()) + floor0)
            else:
                shift = floor0 + max(0.0, -min(free, twin))
                ratio = (twin + shift) / (free + shift)"""
SC_OLD = """            shift = floor0 + max(0.0, -min(free, twin))
            ratio = (twin + shift) / (free + shift)"""


def build(revert_ptrade: bool, revert_scarcity: bool, tag: str):
    src = SRC.read_text()
    if revert_ptrade:
        assert PT_NEW in src
        src = src.replace(PT_NEW, PT_OLD)
    if revert_scarcity:
        assert SC_NEW in src
        src = src.replace(SC_NEW, SC_OLD)
    name = f"sheaf.dcoup_{tag}"
    mod = types.ModuleType(name)
    mod.__package__ = "sheaf"
    mod.__file__ = str(SRC)
    sys.modules[name] = mod
    exec(compile(src, mod.__file__, "exec"), mod.__dict__)
    return mod


def hike(price, months, y0, m0, y1, m1):
    """3-month-mean peak over 3-month-mean base, on a monthly frame."""
    def win(y, m):
        sel = [(yy, mm) for (yy, mm) in months
               if (yy, mm) in [(y, m), (y, m + 1 if m < 12 else 1),
                               (y, m + 2 if m < 11 else m + 2 - 12)]]
        idx = [months.index(s) for s in sel]
        return float(np.mean([price[i] for i in idx])) if idx else np.nan
    return win(y1, m1) / win(y0, m0)


def main():
    lines = []

    def out(s=""):
        print(s)
        lines.append(s)

    out("# R0l — attributing the Gate 1 rice spillover-sign failure\n")
    out("The bar is the 2007/08 full hike at sigma>0 divided by the same")
    out("hike at sigma=0; it must exceed 1. Rice at sigma=0.6 now returns")
    out("0.984. Each fix is reverted in isolation below.\n")
    out("| variant | rice sigma=0.3 | rice sigma=0.6 | verdict |")
    out("|---|---|---|---|")

    rows = []
    variants = (
        ("both fixes (shipped)", False, False, "both"),
        ("revert p_trade only", True, False, "nopt"),
        ("revert scarcity only", False, True, "nosc"),
        ("revert both (pre-fix)", True, True, "none"),
    )
    for label, rp, rs, tag in variants:
        mod = build(rp, rs, tag)
        vals = {}
        for sig in (0.0, 0.3, 0.6):
            res = mod.run_coupled_dynamics(
                sigma=sig, use_amis=True, use_shocks=True, use_demand=False)
            # rice index within GRAINS
            from sheaf.calibration import GRAINS
            gi = list(GRAINS).index("rice")
            p = res.price[gi] if res.price.ndim > 1 else res.price
            # steps: 2006-06 base -> index 10; 2008-03 peak -> index 50
            base = float(np.mean(p[10:16]))
            peak = float(np.mean(p[50:56]))
            vals[sig] = peak / base
        r3 = vals[0.3] / vals[0.0]
        r6 = vals[0.6] / vals[0.0]
        ok = "pass" if (r3 > 1 and r6 > 1) else "**FAIL**"
        out(f"| {label} | x{r3:.3f} | x{r6:.3f} | {ok} |")
        rows.append(dict(variant=label, ratio_03=r3, ratio_06=r6))
    out("")
    out("Approximate windows are used here (fixed step indices rather than")
    out("the scorer's calendar merge), so the absolute values differ a little")
    out("from scripts/score_gate1.py. The comparison across rows is the point.\n")

    dest = ROOT / "diagnostics" / "redteam" / "r0"
    dest.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(dest / "gate1_attribution.csv", index=False)
    (dest / "R0L_GATE1_ATTRIBUTION.md").write_text("\n".join(lines) + "\n")
    print(f"\nwrote {(dest / 'R0L_GATE1_ATTRIBUTION.md').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
