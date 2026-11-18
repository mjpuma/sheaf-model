#!/usr/bin/env python3
"""Gate 0 v2 four-crop figure: monthly world price on Kilian's 2026-11-18 inputs.

Each crop is shown against the observed World Bank price PIK's plot code uses
(US HRW wheat, US maize, Thai 5% rice; soybeans added), and wheat also against
the published run (Kuhla et al. 2025). Steps where
cross-border trade falls below 10 % of its 2000-2005 median are marked,
because a few small trades then set the index.

    python3 plots/gate0_v2_fourcrop.py [out.png]
"""
from __future__ import annotations

import glob
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "diagnostics" / "gate0_v2"))
from score_gate0 import load, monthly_world_price, price_metrics  # noqa: E402

AUTHOR = glob.glob("/Users/mjp38/GitHub/agrimate-2025/data-v3/data/hindcasting_analysis/raw_data/"
                   "*export_restrictions=2007-2011*.nc")[0]
RUNS = Path("/Users/mjp38/GitHub/agrimate/data/gate0_v2")
OUT = Path(sys.argv[1] if len(sys.argv) > 1 else
           Path(__file__).resolve().parents[1] / "diagnostics" / "gate0_v2" / "gate0_v2_fourcrop.png")
YMAX = 3.0
PRICES = Path(__file__).resolve().parents[1] / "data" / "world_prices"
OBS_COLOR = "#b5651d"


def observed():
    """World Bank Pink Sheet, MUV-deflated, monthly. Soybean is not in the grains
    extract, so it is read from the monthly workbook and deflated with the same
    per-year real/nominal ratio."""
    df = pd.read_csv(PRICES / "pink_sheet_grains_monthly.csv")
    out = {g: d.set_index(["year", "month"]).price_real_2010_usd_mt for g, d in df.groupby("grain")}
    w = df[df.grain == "wheat"]
    ratio = (w.price_real_2010_usd_mt / w.price_nominal_usd_mt).groupby(w.year).mean()
    sheet = pd.read_excel(PRICES / "CMO-Historical-Data-Monthly.xlsx", sheet_name="Monthly Prices", header=None)
    col = [j for j in range(sheet.shape[1]) if str(sheet.iloc[4, j]).strip() == "Soybeans"][0]
    rows = sheet.iloc[6:, [0, col]].dropna()
    soy = {}
    for label, v in rows.itertuples(index=False):
        y, m = int(str(label)[:4]), int(str(label)[5:])
        if y in ratio.index and isinstance(v, (int, float)):
            soy[(y, m)] = float(v) * ratio[y]
    out["soybean"] = pd.Series(soy)
    return out


def scaled_observed(series, model_t, model_p):
    """Scale the observed series so its 2000-2012 mean equals the model's, as in
    plot_wm_price_timeseries (src/plot.jl)."""
    keys = [(y, m) for y in range(2000, 2013) for m in range(1, 13)]
    obs = np.array([series[k] for k in keys])
    t = np.array([y + (m - 0.5) / 12 for (y, m) in keys])
    obs = obs * model_p.mean() / obs.mean()
    base = obs[:72].mean()
    win = lambda y0: obs[(y0 - 2000) * 12 + 6:(y0 - 2000) * 12 + 18].mean() / base
    return t, obs, win(2007), win(2010)


def monthly(run):
    prices = monthly_world_price(run, 312)
    t = np.array([y + (m - 0.5) / 12 for (y, m) in prices])
    return t, np.array(list(prices.values())), price_metrics(prices)


def thin_steps(run):
    off = ~np.eye(run["q"].shape[1], dtype=bool)
    trade = np.array([run["q"][t][off].sum() for t in range(312)])
    thin = np.where(trade < 0.1 * np.median(trade[:144]))[0]
    return [run["times"][t].year + (run["times"][t].timetuple().tm_yday - 0.5) / 365 for t in thin]


OBS = observed()
fig, axes = plt.subplots(2, 2, figsize=(7.2, 4.3), sharex=True)
for ax, crop in zip(axes.flat, ["wheat", "rice", "maize", "soybean"]):
    for lo, hi in ((2007.5, 2008.5), (2010.5, 2011.5)):
        ax.axvspan(lo, hi, color="0.92", zorder=0)
    run = load(glob.glob(str(RUNS / f"{crop}_t312_kilian_v2" / "netcdf" / "*.nc"))[0])
    t, p, m = monthly(run)
    if crop == "wheat":
        ta, pa, _ = monthly(load(AUTHOR))
        ax.plot(ta, pa, lw=3, color="0.7", label="published (Kuhla et al. 2025)")
    to, po, o0708, o1011 = scaled_observed(OBS[crop], t, p)
    ax.plot(to, po, lw=1.1, color=OBS_COLOR, label="observed (World Bank, deflated)")
    ax.plot(t, p, lw=1.1, color="#1f4e9c", label="new branch, Kilian's inputs")
    thin = thin_steps(run)
    if thin:
        ax.plot(thin, [0.12] * len(thin), "|", color="#c0392b", ms=7, mew=1.5,
                label="trade < 10 % of normal")
    if p.max() > YMAX:
        ax.annotate(f"peak {p.max():.1f}", xy=(t[np.argmax(p)], YMAX), xytext=(4, -10),
                    textcoords="offset points", fontsize=7, color="#1f4e9c")
    ax.set_ylim(0, YMAX)
    ax.set_xlim(2000, 2013)
    ax.set_title(f"{crop}   07/08 {m['r0708']:.2f} (obs. {o0708:.2f})   "
                 f"10/11 {m['r1011']:.2f} (obs. {o1011:.2f})", fontsize=7.5, loc="left")
    ax.tick_params(labelsize=7)
    ax.axhline(1, color="0.6", lw=0.5)
    if crop in ("wheat", "rice"):
        ax.legend(fontsize=6.5, frameon=True, framealpha=0.95, edgecolor="none", loc="upper left")
for ax in axes[:, 0]:
    ax.set_ylabel("world price index", fontsize=7.5)
fig.tight_layout(pad=0.4)
OUT.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT, dpi=220)
print(OUT)
