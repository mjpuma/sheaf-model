#!/usr/bin/env python3
"""A5 figures (scratch): hike-ratio ablation bars + ask_rival sign condition."""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "diagnostics" / "gate0_prep" / "a5"
FIG = ROOT / "figures" / "scratch" / "a5"
FIG.mkdir(parents=True, exist_ok=True)

g = pd.read_csv(OUT / "ablation_grid.csv")
sweep = pd.read_csv(OUT / "ask_rival_sweep.csv")
fine = pd.read_csv(OUT / "ask_rival_fine_maize.csv")

order = ["baseline", "trade_w=1.0", "trade_w=0.0", "ask_rival=0.0",
         "block_kappa=0.0", "unmet_kappa=0.0", "foresight_phi=0.0",
         "foresight_phi=1.0", "ask_alpha=0.0", "rebuild_lambda=0.0"]
crops = ["wheat", "maize", "rice"]

fig, axes = plt.subplots(1, 3, figsize=(15, 4.6), sharey=False)
for ax, crop in zip(axes, crops):
    f = g[(g.crop == crop) & (g.leg == "full")].set_index("ablation").loc[order]
    x = np.arange(len(order))
    w = 0.38
    ax.bar(x - w / 2, f.hike_2007_08, w, color="#1f4e79", label="2007/08")
    ax.bar(x + w / 2, f.hike_2010_11, w, color="#e67e22", label="2010/11")
    ax.axhline(f.obs_hike_2007_08.iloc[0], color="#1f4e79", ls="--", lw=1,
               label="obs 2007/08")
    ax.axhline(f.obs_hike_2010_11.iloc[0], color="#e67e22", ls=":", lw=1.2,
               label="obs 2010/11")
    ax.axhline(1.0, color="0.6", lw=0.8)
    ax.set_xticks(x, order, rotation=55, ha="right", fontsize=7)
    ax.set_title(f"{crop} — full leg hike ratio")
    ax.set_ylabel("3-mo mean peak / base")
    if crop == "wheat":
        ax.legend(frameon=False, fontsize=7)
fig.suptitle("A5 channel ablation: hike ratios (measurement only, not a retune)",
             fontsize=10)
fig.tight_layout()
p1 = FIG / "fig_a5_hike_ablation.png"
fig.savefig(p1, dpi=140)
plt.close(fig)

fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
ax = axes[0]
for crop, c in zip(crops, ("#1f4e79", "#c0392b", "#1e8449")):
    s = sweep[sweep.crop == crop].sort_values("ask_rival")
    ax.plot(s.ask_rival, 100 * s.lift, "o-", color=c, label=crop, ms=4)
ax.axhline(0, color="0.3", lw=1)
ax.axvline(0.80, color="0.5", ls="--", lw=1, label="default 0.80")
ax.set_xlabel("ask_rival")
ax.set_ylabel("isolated-τ price lift in assert window (%)")
ax.set_title("assert_amis_raises_price statistic")
ax.legend(frameon=False, fontsize=8)

ax = axes[1]
s = fine.sort_values("ask_rival")
ax.plot(s.ask_rival, 100 * s.lift, "o-", color="#c0392b", ms=5)
ax.axhline(0, color="0.3", lw=1)
ax.axvline(0.80, color="0.5", ls="--", lw=1)
ax.set_xlabel("ask_rival")
ax.set_ylabel("maize lift (%)")
ax.set_title("maize sign condition binds near 0.75; default 0.80")
fig.tight_layout()
p2 = FIG / "fig_a5_ask_rival_sign.png"
fig.savefig(p2, dpi=140)
plt.close(fig)
print(f"wrote {p1}\nwrote {p2}")
