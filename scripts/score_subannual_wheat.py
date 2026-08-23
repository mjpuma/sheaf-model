#!/usr/bin/env python3
"""Score sub-annual wheat Gate 0 vs monthly Pink Sheet.

Legs (24 steps/yr, play_game N/A — exogenous AMIS quantity cuts):
  full    — seasonal PSD harvest + AMIS export cuts
  shocks  — seasonal PSD harvest, no AMIS
  tau     — mean-year seasonal harvest (no interannual anomaly) + AMIS

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

from sheaf.calendar24 import STEPS_PER_YEAR, n_steps
from sheaf.calibration import DATA
from sheaf.data_usda import load_price_series_monthly
from sheaf.dynamic_wheat import (
    WheatSimResult,
    _ending_stocks,
    _psd_wheat_annual,
    amis_export_cuts,
    result_to_monthly,
    run_wheat_dynamics,
)
from sheaf.seasonal import harvest_path, load_wheat_harvest_calendar

ROOT = Path(__file__).resolve().parents[1]
DIAG = ROOT / "diagnostics"
FIGS = ROOT / "figures"


def _corr(a, b) -> float:
    a, b = np.asarray(a, float), np.asarray(b, float)
    mask = np.isfinite(a) & np.isfinite(b)
    if mask.sum() < 6:
        return float("nan")
    return float(np.corrcoef(a[mask], b[mask])[0, 1])


def _run_with_harvest(countries, H, cuts, start, end, stock_year=2005,
                      p0=250.0, elast=-0.25, kappa=0.08, buffer_frac=0.08):
    """Core loop shared by legs (harvest + cuts injected)."""
    n, T = len(countries), n_steps(start, end)
    years = list(range(start, end + 1))
    _, cons = _psd_wheat_annual(countries, years)
    C_ann = np.zeros(n)
    for i, c in enumerate(countries):
        sub = cons[cons.country == c]
        C_ann[i] = float(sub.consumption.mean()) if len(sub) else 0.0
    C_step = C_ann / STEPS_PER_YEAR
    stock = _ending_stocks(countries, stock_year)
    buffer = buffer_frac * C_ann
    price = np.zeros(T)
    stock_path = np.zeros((n, T))
    cons_path = np.zeros((n, T))
    exp_path = np.zeros((n, T))
    p = float(p0)
    stu_target = 6.0
    for t in range(T):
        avail = stock + H[:, t]
        desired = np.maximum(C_step * (p / p0) ** elast, 0.0)
        exportable = np.maximum(0.0, avail - desired - buffer) * (1.0 - cuts[:, t])
        need = np.maximum(0.0, desired - avail)
        total_need, total_exp = float(need.sum()), float(exportable.sum())
        shipped = np.zeros(n)
        received = np.zeros(n)
        if total_exp > 1e-12 and total_need > 1e-12:
            fill = min(1.0, total_exp / total_need)
            received = need * fill
            shipped = exportable * (received.sum() / total_exp)
        consumption = np.minimum(desired, avail - shipped + received)
        stock = np.maximum(0.0, avail - shipped - consumption + received)
        stu_steps = float(stock.sum()) / max(float(C_step.sum()), 1e-9)
        unmet = float(np.maximum(0.0, desired - consumption).sum())
        unmet_frac = unmet / max(float(desired.sum()), 1e-9)
        stu_gap = (stu_target - stu_steps) / stu_target
        signal = float(np.clip(0.5 * stu_gap + 0.5 * unmet_frac, -0.5, 0.5))
        p = float(np.clip(p * np.exp(kappa * signal), 80.0, 800.0))
        price[t] = p
        stock_path[:, t] = stock
        cons_path[:, t] = consumption
        exp_path[:, t] = shipped
    return WheatSimResult(
        countries=countries, start_year=start, end_year=end,
        price=price, stock=stock_path, harvest=H, consumption=cons_path,
        exports=exp_path, export_cut=cuts)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--start", type=int, default=2006)
    ap.add_argument("--end", type=int, default=2011)
    args = ap.parse_args()

    DIAG.mkdir(parents=True, exist_ok=True)
    FIGS.mkdir(parents=True, exist_ok=True)

    countries = [d["name"] for d in DATA] + ["RestOfWorld"]
    years = list(range(args.start, args.end + 1))
    prod, _ = _psd_wheat_annual(countries, years)
    cal = load_wheat_harvest_calendar()
    H_full = harvest_path(countries, prod, args.start, args.end, calendar=cal)

    mean_prod = prod.groupby("country", as_index=False)["production"].mean()
    tiled = pd.concat(
        [mean_prod.assign(year=y) for y in years], ignore_index=True)
    H_base = harvest_path(countries, tiled, args.start, args.end, calendar=cal)

    cuts = amis_export_cuts(countries, args.start, args.end)
    zero = np.zeros_like(cuts)

    legs = {
        "full": _run_with_harvest(countries, H_full, cuts, args.start, args.end),
        "shocks": _run_with_harvest(countries, H_full, zero, args.start, args.end),
        "tau": _run_with_harvest(countries, H_base, cuts, args.start, args.end),
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


if __name__ == "__main__":
    main()
