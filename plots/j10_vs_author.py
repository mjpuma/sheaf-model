#!/usr/bin/env python3
"""Gate 0 J10 figure: our run against the author's published wheat run.

Reads the CSVs written by `peek_agrimate_partial_run.jl` (J10_CSV,
J10_STOCK_CSV), so it needs no NetCDF reader. Usage:

    python3 plots/j10_vs_author.py <compare_dir> <out.png>
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

CMP = Path(sys.argv[1] if len(sys.argv) > 1 else "/Users/mjp38/GitHub/agrimate-2025/j10_compare")
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else CMP / "j10_vs_author.png")

price = np.genfromtxt(CMP / "price_monthly.csv", delimiter=",", names=True)
stock = np.genfromtxt(CMP / "stocks_annual.csv", delimiter=",", names=True)

t = price["year"] + (price["month"] - 0.5) / 12.0

fig, axes = plt.subplots(3, 1, figsize=(9, 9.5), gridspec_kw={"height_ratios": [3, 1, 2]})

ax = axes[0]
ax.plot(t, price["author"], lw=3.2, color="0.72", label="Kuhla et al. 2025 (published)")
ax.plot(t, price["local"], lw=1.2, color="crimson", label="SHEAF run of the published code")
ax.set_ylabel("world market price index")
ax.set_title("Wheat, harvest shocks + export restrictions, on the authors' own calibration")
ax.legend(loc="upper left", frameon=False)
ax.grid(alpha=0.25)

ax = axes[1]
ax.plot(t, 100 * (price["local"] / price["author"] - 1), lw=1.0, color="crimson")
ax.axhline(0, color="0.72", lw=1.5)
ax.set_ylabel("difference (%)")
ax.grid(alpha=0.25)
lim = max(0.6, 1.15 * np.abs(100 * (price["local"] / price["author"] - 1)).max())
ax.set_ylim(-lim, lim)

ax = axes[2]
w = 0.38
x = np.arange(len(stock["year"]))
ax.bar(x - w / 2, stock["author"], w, color="0.72", label="published")
ax.bar(x + w / 2, stock["local"], w, color="crimson", label="our run")
ax.set_xticks(x)
ax.set_xticklabels([str(int(y)) for y in stock["year"]])
ax.set_ylabel("world end-of-year stocks (Mt)")
ax.legend(frameon=False)
ax.grid(alpha=0.25, axis="y")

for ax in axes:
    ax.spines[["top", "right"]].set_visible(False)

fig.tight_layout()
fig.savefig(OUT, dpi=150)
print(f"wrote {OUT}")
