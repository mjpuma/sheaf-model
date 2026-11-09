#!/usr/bin/env python3
"""Gate 0 v2 status figure: PIK develop-substitution-claude on the published wheat inputs.

World price and year-end world stocks for the published author run, three
equivalent one-consumer setups of the new host, and the undisturbed run.

    python3 plots/gate0_v2_status.py [out.png]
"""
from __future__ import annotations

import glob
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "diagnostics" / "gate0_v2"))
from score_gate0 import load, monthly_world_price, price_metrics, year_end_stocks  # noqa: E402

AUTHOR = glob.glob("/Users/mjp38/GitHub/agrimate-2025/data-v3/data/hindcasting_analysis/raw_data/"
                   "*export_restrictions=2007-2011*.nc")[0]
RUNS = Path("/Users/mjp38/GitHub/agrimate/data/gate0_v2")
OUT = Path(sys.argv[1] if len(sys.argv) > 1 else
           Path(__file__).resolve().parents[1] / "diagnostics" / "gate0_v2" / "gate0_v2_status.png")

SETUPS = [
    ("wheat_t312_published", "new host, default consumer", "#1f77b4"),
    ("wheat_t312_published_one", "new host, 1 consumer via files", "#ff7f0e"),
    ("wheat_t312_published_two", "new host, 2 half-size consumers", "#2ca02c"),
]


def nc(name):
    return glob.glob(str(RUNS / name / "netcdf" / "*.nc"))[0]


def series(path, t_max=312):
    run = load(path)
    prices = monthly_world_price(run, t_max)
    t = np.array([y + (m - 0.5) / 12 for (y, m) in prices])
    return run, t, np.array(list(prices.values())), price_metrics(prices), year_end_stocks(run, t_max)


author_run, ta, pa, ma, sa = series(AUTHOR)

fig, (ax, bx) = plt.subplots(2, 1, figsize=(9.5, 8.2), gridspec_kw={"height_ratios": [3, 2]})

for lo, hi in ((2007.5, 2008.5), (2010.5, 2011.5)):
    ax.axvspan(lo, hi, color="0.93", zorder=0)
ax.plot(ta, pa, lw=4, color="0.7", label=f"Kuhla et al. 2025 (published)   "
        f"07/08 {ma['r0708']:.3f}, 10/11 {ma['r1011']:.3f}, peak {ma['peak']:.3f}")
for name, label, color in SETUPS:
    _, t, p, m, s = series(nc(name))
    ax.plot(t, p, lw=1.2, color=color, label=f"{label}   "
            f"07/08 {m['r0708']:.3f}, 10/11 {m['r1011']:.3f}, peak {m['peak']:.3f}")
    years = sorted(s)
    bx.plot(years, [100 * (s[y] / sa[y] - 1) for y in years], "o-", ms=4, lw=1.2, color=color, label=label)
_, tu, pu, _, _ = series(nc("wheat_t312_published_undisturbed"))
ax.plot(tu, pu, lw=1.0, ls="--", color="k", label="new host, no anomalies or restrictions")
ax.set_xlim(2000, 2013)
ax.set_ylabel("world wheat price index (monthly)")
ax.legend(loc="upper left", fontsize=8, frameon=False)
ax.text(2008.0, 0.82, "2007/08", ha="center", fontsize=8, color="0.4")
ax.text(2011.0, 0.82, "2010/11", ha="center", fontsize=8, color="0.4")
ax.set_ylim(0.75, None)
ax.set_title("Gate 0 on PIK develop-substitution-claude: wheat hindcast, published 2025 inputs",
             fontsize=11)

bx.axhspan(-0.5, 0.5, color="0.93", zorder=0)
bx.axhline(0, color="0.5", lw=0.8)
bx.set_xlim(2000, 2013)
bx.set_ylabel("year-end world stocks,\n% gap to published run")
bx.legend(loc="upper left", fontsize=8, frameon=False)
bx.text(2012.9, 0.42, "±0.5 % bar", ha="right", va="top", fontsize=8, color="0.4")

fig.text(0.01, 0.005,
         "Snapshot of develop-consumers f492df9, no code edits; one consumer per region; baseline 2007-2009; "
         "SLSQP maxtime 60 s.\nThe three new-host setups are the same model up to float rounding; their spread "
         "shows run-to-run sensitivity. Repeat runs of one setup are identical.",
         fontsize=7.5, color="0.3", va="bottom")
fig.tight_layout(rect=(0, 0.045, 1, 1))
OUT.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT, dpi=170)
print(OUT)
