#!/usr/bin/env python3
"""Rice on Kilian's 2026-11-18 inputs, four shock settings.

Top: monthly world market price. Bottom: Southeast Asia supplier storage.
The no-shock run is unstable, so the export bans are not what breaks rice.

    python3 plots/gate0_v2_rice_scenarios.py [out.png]
"""
from __future__ import annotations

import glob
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import netCDF4
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "diagnostics" / "gate0_v2"))
from score_gate0 import load, monthly_world_price, price_metrics  # noqa: E402

RUNS = Path("/Users/mjp38/GitHub/agrimate/data/gate0_v2")
PRICES = Path(__file__).resolve().parents[1] / "data" / "world_prices"
OUT = Path(sys.argv[1] if len(sys.argv) > 1 else
           Path(__file__).resolve().parents[1] / "diagnostics" / "gate0_v2" / "gate0_v2_rice_scenarios.png")

SCENARIOS = [
    ("undisturbed", "no shocks", "#7f7f7f", "--"),
    ("anomalies_only", "harvest shocks only", "#1f77b4", "-"),
    ("restrictions_only", "export restrictions only", "#ff7f0e", "-"),
    ("crisis", "both", "#d62728", "-"),
]


def nc(scenario):
    name = "rice_t312_kilian_v2" if scenario == "crisis" else f"rice_t312_kilian_v2_{scenario}"
    return glob.glob(str(RUNS / name / "netcdf" / "*.nc"))[0]


def observed_rice(model_mean):
    df = pd.read_csv(PRICES / "pink_sheet_grains_monthly.csv")
    rice = df[df.grain == "rice"].set_index(["year", "month"]).price_real_2010_usd_mt
    keys = [(y, m) for y in range(2000, 2013) for m in range(1, 13)]
    obs = np.array([rice[k] for k in keys])
    obs = obs * model_mean / obs.mean()
    t = np.array([y + (m - 0.5) / 12 for (y, m) in keys])
    return t, obs


def se_asia_storage(path):
    ds = netCDF4.Dataset(path)
    var = ds.variables["supplier storage"]
    x = np.ma.filled(var[:].astype(float), np.nan)
    regions = [str(r) for r in ds.variables["region"][:]]
    i = regions.index("Southeast Asia")
    order = [var.dimensions.index("time")] + [k for k, d in enumerate(var.dimensions) if d != "time"]
    stor = np.transpose(x, order)[:, i] / 1e3
    tvar = ds.variables["time"]
    times = netCDF4.num2date(tvar[:], units=tvar.units, calendar=getattr(tvar, "calendar", "standard"))
    t = np.array([tm.year + (tm.timetuple().tm_yday - 0.5) / 365 for tm in times])
    ds.close()
    return t, stor


fig, (ax, bx) = plt.subplots(2, 1, figsize=(7.2, 4.6), sharex=True)
for lo, hi in ((2007.5, 2008.5), (2010.5, 2011.5)):
    ax.axvspan(lo, hi, color="0.93", zorder=0)
    bx.axvspan(lo, hi, color="0.93", zorder=0)

crisis = load(nc("crisis"))
prices = monthly_world_price(crisis, 312)
to, po = observed_rice(np.mean(list(prices.values())))
ax.plot(to, po, color="#b5651d", lw=1.3, label="observed Thai 5% (deflated)", zorder=2)

for key, label, color, ls in SCENARIOS:
    run = load(nc(key))
    p = monthly_world_price(run, 312)
    m = price_metrics(p)
    t = np.array([y + (mo - 0.5) / 12 for (y, mo) in p])
    y = np.array(list(p.values()))
    ax.plot(t, y, color=color, ls=ls, lw=1.15,
            label=f"{label}   07/08 {m['r0708']:.2f}, peak {m['peak']:.1f}", zorder=3)
    ts, stor = se_asia_storage(nc(key))
    bx.plot(ts, stor, color=color, ls=ls, lw=0.9, label=label)

ax.set_ylim(0, 4)
ax.set_ylabel("world rice price index", fontsize=8)
ax.legend(fontsize=6.5, frameon=False, loc="upper left", ncol=2)
ax.set_title("Rice, Kilian's 2026-11-18 inputs. Price clipped at 4 "
             "(no-shock peak 11 in 2002; restrictions-only peak 68 in 2011).",
             fontsize=8, loc="left")
ax.tick_params(labelsize=7)

bx.set_xlim(2000, 2013)
bx.set_ylabel("Southeast Asia\nsupplier storage (Mt)", fontsize=8)
bx.tick_params(labelsize=7)
bx.set_ylim(0, None)

fig.tight_layout(pad=0.45)
OUT.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT, dpi=220)
print(OUT)
