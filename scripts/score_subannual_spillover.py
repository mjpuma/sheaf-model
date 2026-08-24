#!/usr/bin/env python3
"""Spillover diagnostic: multi-grain spine with substitution on vs off.

Runs wheat/rice/maize on the 24-step clock under subst_scale ∈ {0, 0.6},
writes monthly prices, and reports:
  - wheat crisis hike ratios (sanity vs Gate 0)
  - rice/maize price response in the 2007/08 wheat-stress window
  - attribution: share of rice/maize move attributable to substitution

Writes:
  diagnostics/subannual_spillover_score.csv
  figures/fig13_subannual_spillover.png
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from sheaf.calibration import GRAINS
from sheaf.data_usda import load_price_series_monthly
from sheaf.dynamic_grains import grains_to_monthly, run_grains_dynamics

ROOT = Path(__file__).resolve().parents[1]
DIAG = ROOT / "diagnostics"
FIGS = ROOT / "figures"


def _hike(df: pd.DataFrame, col: str, y0: int, m0: int, y1: int, m1: int) -> float:
    def win(y, m):
        vals = []
        for dm in (-1, 0, 1):
            mm, yy = m + dm, y
            if mm < 1:
                mm += 12
                yy -= 1
            if mm > 12:
                mm -= 12
                yy += 1
            hit = df[(df.year == yy) & (df.month == mm)][col]
            if len(hit):
                vals.append(float(hit.iloc[0]))
        return float(np.mean(vals)) if vals else float("nan")
    b, p = win(y0, m0), win(y1, m1)
    return p / b if b and np.isfinite(b) and np.isfinite(p) else float("nan")


def _window_mean(df: pd.DataFrame, col: str, y0: int, m0: int,
                 y1: int, m1: int) -> float:
    rows = []
    y, m = y0, m0
    while (y, m) <= (y1, m1):
        hit = df[(df.year == y) & (df.month == m)][col]
        if len(hit):
            rows.append(float(hit.iloc[0]))
        m += 1
        if m > 12:
            m = 1
            y += 1
    return float(np.mean(rows)) if rows else float("nan")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--start", type=int, default=2006)
    ap.add_argument("--end", type=int, default=2011)
    args = ap.parse_args()

    DIAG.mkdir(parents=True, exist_ok=True)
    FIGS.mkdir(parents=True, exist_ok=True)

    legs = {
        "subst_on": run_grains_dynamics(
            start_year=args.start, end_year=args.end,
            subst_scale=0.6, use_amis=True, use_shocks=True),
        "subst_off": run_grains_dynamics(
            start_year=args.start, end_year=args.end,
            subst_scale=0.0, use_amis=True, use_shocks=True),
    }

    obs = load_price_series_monthly(deflated=True)
    obs = obs[(obs.year >= args.start) & (obs.year <= args.end)]

    pieces = []
    for name, res in legs.items():
        m = grains_to_monthly(res)
        m["leg"] = name
        pieces.append(m)
    score = pd.concat(pieces, ignore_index=True)
    # attach obs
    long_obs = obs.melt(id_vars=["year", "month"],
                        value_vars=list(GRAINS),
                        var_name="grain", value_name="obs_price")
    score = score.merge(long_obs, on=["year", "month", "grain"], how="left")
    out_csv = DIAG / "subannual_spillover_score.csv"
    score.to_csv(out_csv, index=False)

    fig, axes = plt.subplots(3, 1, figsize=(11, 9), sharex=True)
    styles = {"subst_on": ("-", "0.15"), "subst_off": ("--", "#6c3483")}
    for ax, g in zip(axes, GRAINS):
        o = score[(score.leg == "subst_on") & (score.grain == g)].sort_values(
            ["year", "month"])
        x = np.arange(len(o))
        ax.plot(x, o.obs_price, color="#c0392b", lw=2, label="Pink Sheet real")
        for leg, (ls, c) in styles.items():
            s = score[(score.leg == leg) & (score.grain == g)].sort_values(
                ["year", "month"])
            ax.plot(x, s.model_price, ls=ls, color=c,
                    label=f"model {leg}", lw=1.3)
        ax.set_ylabel(f"{g} $/t")
        ax.legend(fontsize=7, loc="upper left")
        ax.set_title(g)
    ticks = list(range(0, len(x), 6))
    labels = [f"{y}-{m:02d}" for y, m in zip(o.year, o.month)]
    axes[-1].set_xticks(ticks)
    axes[-1].set_xticklabels([labels[i] for i in ticks], rotation=45,
                             ha="right", fontsize=7)
    fig.suptitle("Multi-grain spine: substitution on vs off", y=0.995)
    fig.tight_layout()
    out_fig = FIGS / "fig13_subannual_spillover.png"
    fig.savefig(out_fig, dpi=130)
    plt.close(fig)

    print(f"wrote {out_csv}")
    print(f"wrote {out_fig}")

    print("\nWheat crisis hike ratios (model):")
    for leg in ("subst_on", "subst_off"):
        w = score[(score.leg == leg) & (score.grain == "wheat")]
        print(f"  {leg}: 2007/08 ×{_hike(w, 'model_price', 2006, 6, 2008, 3):.2f}  "
              f"2010/11 ×{_hike(w, 'model_price', 2009, 6, 2011, 2):.2f}")

    # Spillover in 2007-08 peak window (Sep 2007 – Mar 2008) vs calm 2006 H1
    print("\n2007/08 stress window mean price / 2006H1 mean:")
    for g in GRAINS:
        for leg in ("subst_on", "subst_off"):
            s = score[(score.leg == leg) & (score.grain == g)]
            calm = _window_mean(s, "model_price", 2006, 1, 2006, 6)
            stress = _window_mean(s, "model_price", 2007, 9, 2008, 3)
            ratio = stress / calm if calm else float("nan")
            print(f"  {g:5s} {leg:10s}  ×{ratio:.3f}")

    print("\nSubstitution attribution "
          "(Δlog p_g(on) − Δlog p_g(off)) / Δlog p_wheat(on) in 2007/08:")
    on = score[score.leg == "subst_on"]
    off = score[score.leg == "subst_off"]

    def dlog(df, g):
        s = df[df.grain == g]
        calm = _window_mean(s, "model_price", 2006, 1, 2006, 6)
        stress = _window_mean(s, "model_price", 2007, 9, 2008, 3)
        return np.log(stress / calm)

    dw = dlog(on, "wheat")
    for g in ("rice", "maize"):
        attr = (dlog(on, g) - dlog(off, g)) / dw if dw else float("nan")
        print(f"  {g}: {attr:+.3f}")


if __name__ == "__main__":
    main()
