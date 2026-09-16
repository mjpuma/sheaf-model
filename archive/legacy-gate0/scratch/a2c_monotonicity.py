#!/usr/bin/env python3
"""A2c: decompose the non-monotone price response found in A2b.

A2b measured dlog p / dlog H under uniform permanent harvest shortfalls and
found the sign reverses: for wheat a 1-2% shortfall LOWERS the world price
and only a shortfall of 5% or more raises it. Either the experiment is
badly posed or the map is non-monotone in harvest. This script decomposes
the channels to find out which, and repeats the test with a transient
(single-year) shortfall, which is closer to how the model is actually used.

Read-only with respect to sheaf/*.py; the module is recompiled in memory
with a per-step recorder.
"""
from __future__ import annotations

import sys
import types
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from sheaf.calendar24 import STEPS_PER_YEAR  # noqa: E402

SRC = ROOT / "sheaf" / "dynamic_crop.py"
CROPS = ("wheat", "maize", "rice")

# Record the quantities that sit between harvest and price.
PROBE_AT = "        fill = shipped / np.maximum(offers, 1e-9)"
PROBE = """        _DIAG.append(dict(
            stock_pre=float(stock.sum()), avail=float(avail.sum()),
            desired=float(desired.sum()), target=float(target.sum()),
            offers=float(offers.sum()), shipped=float(shipped.sum()),
            excess=float(np.maximum(0.0, stock - warehouse).sum()),
            warehouse=float(warehouse.sum())))
        fill = shipped / np.maximum(offers, 1e-9)"""


def build():
    src = SRC.read_text()
    if PROBE_AT not in src:
        raise SystemExit("probe anchor not found")
    mod = types.ModuleType("sheaf.dc_a2c")
    mod.__package__ = "sheaf"
    mod.__file__ = str(SRC)
    mod.__dict__["_DIAG"] = []
    sys.modules["sheaf.dc_a2c"] = mod
    exec(compile(src.replace(PROBE_AT, PROBE), mod.__file__, "exec"),
         mod.__dict__)
    return mod


def run(mod, prep, harvest):
    mod.__dict__["_DIAG"].clear()
    res = mod.simulate_prep(prep, harvest=harvest)
    d = pd.DataFrame(mod.__dict__["_DIAG"][-len(res.price):])
    return res, d


def main():
    lines = []

    def out(s=""):
        print(s)
        lines.append(s)

    mod = build()
    out("# A2c — is the map monotone in harvest?\n")

    out("## Channel decomposition, permanent uniform shortfall\n")
    out("Means over the last four years. `excess` is grain above the warehouse")
    out("cap, of which a fraction lambda_W is removed each step, so it is the")
    out("size of the drawdown channel.\n")
    rows = []
    for crop in CROPS:
        prep = mod.prepare_crop_run(crop, use_amis=False, use_shocks=False,
                                    use_demand=False, use_industrial=False)
        tail = slice(2 * STEPS_PER_YEAR, None)
        out(f"### {crop}")
        out("| shortfall | mean p | mean free | mean stock | mean excess "
            "| mean offers | mean shipped |")
        out("|---|---|---|---|---|---|---|")
        for s in (0.0, 0.01, 0.02, 0.05, 0.10):
            res, d = run(mod, prep, prep.H * (1.0 - s))
            out(f"| -{100*s:.0f}% | {np.mean(res.price[tail]):.1f} "
                f"| {np.mean(res.free_liquid[tail]):.1f} "
                f"| {d.stock_pre[tail].mean():.1f} "
                f"| {d.excess[tail].mean():.1f} "
                f"| {d.offers[tail].mean():.2f} "
                f"| {d.shipped[tail].mean():.2f} |")
            rows.append(dict(crop=crop, mode="permanent", shortfall=s,
                             price=float(np.mean(res.price[tail])),
                             free=float(np.mean(res.free_liquid[tail])),
                             stock=float(d.stock_pre[tail].mean()),
                             excess=float(d.excess[tail].mean()),
                             offers=float(d.offers[tail].mean())))
        out("")

    out("## Transient shortfall (one year only)\n")
    out("Shortfall applied to year 2 of the window only, which is closer to")
    out("how harvest anomalies actually enter. Response measured as the peak")
    out("price in the 12 steps from the start of the shock, over the")
    out("unshocked peak in the same steps.\n")
    out("| crop | -1% | -2% | -5% | -10% | monotone? |")
    out("|---|---|---|---|---|---|")
    for crop in CROPS:
        prep = mod.prepare_crop_run(crop, use_amis=False, use_shocks=False,
                                    use_demand=False, use_industrial=False)
        base, _ = run(mod, prep, prep.H)
        win = slice(STEPS_PER_YEAR, STEPS_PER_YEAR + 12)
        p0w = float(np.max(base.price[win]))
        vals = []
        for s in (0.01, 0.02, 0.05, 0.10):
            H = prep.H.copy()
            H[:, STEPS_PER_YEAR:2 * STEPS_PER_YEAR] *= (1.0 - s)
            res, _ = run(mod, prep, H)
            vals.append(float(np.max(res.price[win])) / p0w)
            rows.append(dict(crop=crop, mode="transient", shortfall=s,
                             price=float(np.max(res.price[win]))))
        mono = all(b >= a - 1e-9 for a, b in zip(vals, vals[1:])) and vals[0] >= 1.0
        out(f"| {crop} | " + " | ".join(f"x{v:.3f}" for v in vals)
            + f" | {'yes' if mono else '**NO**'} |")
    out("")

    dest = ROOT / "diagnostics" / "gate0_prep" / "a2"
    dest.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(dest / "monotonicity.csv", index=False)
    (dest / "A2C_MONOTONICITY.md").write_text("\n".join(lines) + "\n")
    print(f"\nwrote {(dest / 'A2C_MONOTONICITY.md').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
