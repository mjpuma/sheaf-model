#!/usr/bin/env python3
"""Score sub-annual wheat Gate 0 vs monthly Pink Sheet.

Legs (24 steps/yr):
  full    — interannual PSD harvest + AMIS export cuts
  shocks  — interannual PSD harvest, no AMIS
  tau     — mean-year seasonal harvest + AMIS

Writes:
  diagnostics/subannual_wheat_score.csv
  figures/fig12_subannual_wheat_gate0.png
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from sheaf.data_usda import load_price_series_monthly
from sheaf.dynamic_wheat import result_to_monthly, run_wheat_dynamics

ROOT = Path(__file__).resolve().parents[1]
DIAG = ROOT / "diagnostics"
FIGS = ROOT / "figures"


def _corr(a, b) -> float:
    a, b = np.asarray(a, float), np.asarray(b, float)
    mask = np.isfinite(a) & np.isfinite(b)
    if mask.sum() < 6:
        return float("nan")
    return float(np.corrcoef(a[mask], b[mask])[0, 1])


def _hike(df: pd.DataFrame, col: str, y0: int, m0: int, y1: int, m1: int) -> float:
    """Peak/base using mean of a 3-month window around (y, m)."""
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


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--start", type=int, default=2006)
    ap.add_argument("--end", type=int, default=2011)
    args = ap.parse_args()

    DIAG.mkdir(parents=True, exist_ok=True)
    FIGS.mkdir(parents=True, exist_ok=True)

    legs = {
        "full": run_wheat_dynamics(
            start_year=args.start, end_year=args.end,
            use_amis=True, use_shocks=True),
        "shocks": run_wheat_dynamics(
            start_year=args.start, end_year=args.end,
            use_amis=False, use_shocks=True),
        "tau": run_wheat_dynamics(
            start_year=args.start, end_year=args.end,
            use_amis=True, use_shocks=False),
    }

    obs = load_price_series_monthly(deflated=True)
    obs = obs[(obs.year >= args.start) & (obs.year <= args.end)][
        ["year", "month", "wheat"]].rename(columns={"wheat": "obs_price"})

    pieces = []
    for name, res in legs.items():
        m = result_to_monthly(res)
        m["leg"] = name
        pieces.append(m.merge(obs, on=["year", "month"], how="left"))
    score = pd.concat(pieces, ignore_index=True)
    score_path = DIAG / "subannual_wheat_score.csv"
    score.to_csv(score_path, index=False)

    fig, axes = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
    o = score[score.leg == "full"].sort_values(["year", "month"])
    x = np.arange(len(o))
    labels = [f"{y}-{m:02d}" for y, m in zip(o.year, o.month)]
    styles = {"full": ("-", "0.15"), "shocks": ("--", "#6c3483"),
              "tau": ("-.", "#1e8449")}

    ax = axes[0]
    ax.plot(x, o.obs_price, color="#c0392b", lw=2, label="Pink Sheet real")
    for leg, (ls, c) in styles.items():
        s = score[score.leg == leg].sort_values(["year", "month"])
        ax.plot(x, s.model_price, ls=ls, color=c, label=f"model {leg}", lw=1.3)
    for y0, y1 in [(2007, 2008), (2010, 2011)]:
        i0 = next(i for i, (y, m) in enumerate(zip(o.year, o.month))
                  if (y, m) == (y0, 1))
        i1 = next(i for i, (y, m) in enumerate(zip(o.year, o.month))
                  if (y, m) == (y1, 12))
        ax.axvspan(i0, i1, color="0.9", zorder=0)
    ax.set_ylabel("$/t")
    ax.set_title("Gate 0 sub-annual wheat (24 steps/yr) vs monthly Pink Sheet")
    ax.legend(fontsize=8)

    ax = axes[1]
    for leg, (ls, c) in styles.items():
        s = score[score.leg == leg].sort_values(["year", "month"])
        ax.plot(x, s.model_price - s.obs_price, ls=ls, color=c, label=leg)
    ax.axhline(0, color="0.6", lw=0.8)
    ax.set_ylabel("model − obs $/t")
    ax.set_xlabel("month")
    ticks = list(range(0, len(x), 6))
    ax.set_xticks(ticks)
    ax.set_xticklabels([labels[i] for i in ticks], rotation=45, ha="right",
                       fontsize=7)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig_path = FIGS / "fig12_subannual_wheat_gate0.png"
    fig.savefig(fig_path, dpi=130)
    plt.close(fig)

    print(f"wrote {score_path}")
    print(f"wrote {fig_path}")
    print("\nMonthly wheat corr(model, obs):")
    for leg in ("full", "shocks", "tau"):
        s = score[score.leg == leg]
        print(f"  {leg:7s}  corr={_corr(s.model_price, s.obs_price):+.3f}")

    # Within-year timing diagnostics (Gate 0 hard: foresight / calendars).
    full = score[score.leg == "full"].copy()
    full["model_d"] = full.groupby("year")["model_price"].transform(
        lambda s: s - s.mean())
    full["obs_d"] = full.groupby("year")["obs_price"].transform(
        lambda s: s - s.mean())
    mp = full.groupby("month")[["model_price", "obs_price"]].mean()
    spring = float(full[full.month.isin([3, 4])]["model_price"].mean())
    autumn = float(full[full.month.isin([9, 10])]["model_price"].mean())
    print("\nWithin-year timing (full leg):")
    print(f"  within-year demeaned corr={_corr(full.model_d, full.obs_d):+.3f}")
    print(f"  month-profile corr={_corr(mp.model_price, mp.obs_price):+.3f}")
    print(f"  spring/autumn mean ratio={spring / max(autumn, 1e-9):.3f} "
          f"(obs≈0.96; >1.5 = fake lean-season spike)")

    print("\nCrisis window hike ratios (3-mo mean peak/base):")
    windows = [
        ("2007/08", 2006, 6, 2008, 3),
        ("2010/11", 2009, 6, 2011, 2),
    ]
    for label, y0, m0, y1, m1 in windows:
        print(f"  {label}: obs×{_hike(obs, 'obs_price', y0, m0, y1, m1):.2f}  ",
              end="")
        for leg in ("full", "shocks", "tau"):
            s = score[score.leg == leg]
            print(f"{leg}×{_hike(s, 'model_price', y0, m0, y1, m1):.2f}  ",
                  end="")
        print()


if __name__ == "__main__":
    main()
