"""
Build and visualise the hindcast forcing for the 2007/08 and 2010/11 crises from
USDA PSD data (world-aggregate series shipped under data/usda_world/, sourced from
the AgRichter Scale repo). This is step 1 of the Agrimate-style validation: derive
the detrended production anomalies that force the hindcast, and check they line up
with the two crises. Per-country anomalies (from a local PSD export) drive the full
network hindcast and the endogenous export-restriction test.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sheaf.data_usda import load_crop_world, detrend_anomalies, stock_to_use

CROPS = ("wheat", "rice", "maize")
COL = {"wheat": "#c0392b", "rice": "#2874a6", "maize": "#d68910"}
CRISES = [(2007.5, 2008.5, "2007/08"), (2010.5, 2011.5, "2010/11")]

fig, axes = plt.subplots(1, 3, figsize=(15, 4.2))

# panel 1: production vs LOWESS trend
ax = axes[0]
for c in CROPS:
    df = load_crop_world(c).loc[2000:2015]
    tr = detrend_anomalies(load_crop_world(c)["production"]).loc[2000:2015, "trend"]
    ax.plot(df.index, df["production"], "o-", ms=3, color=COL[c], label=f"{c} production")
    ax.plot(tr.index, tr.values, "--", color=COL[c], alpha=0.6)
ax.set_title("Production vs LOWESS trend"); ax.set_ylabel("MMT"); ax.set_xlabel("year")
ax.legend(fontsize=7)

# panel 2: relative production anomalies with crisis windows
ax = axes[1]
for c in CROPS:
    an = detrend_anomalies(load_crop_world(c)["production"]).loc[2000:2015, "anomaly"]
    ax.plot(an.index, 100 * an.values, "o-", ms=3, color=COL[c], label=c)
ax.axhline(0, color="0.7", lw=0.8)
for a, b, lab in CRISES:
    ax.axvspan(a, b, color="0.88")
ax.set_title("Detrended production anomalies (forcing)")
ax.set_ylabel("% deviation from trend"); ax.set_xlabel("year"); ax.legend(fontsize=8)

# panel 3: wheat stock-to-use ratio
ax = axes[2]
sur = stock_to_use(load_crop_world("wheat")).loc[2000:2015]
ax.plot(sur.index, sur.values, "o-", color=COL["wheat"])
for a, b, lab in CRISES:
    ax.axvspan(a, b, color="0.88")
ax.set_title("Wheat stock-to-use ratio"); ax.set_ylabel("ending stocks / consumption")
ax.set_xlabel("year")

fig.suptitle("SHEAF hindcast forcing from USDA PSD (world aggregate) — crises shaded", fontsize=13)
fig.tight_layout()
fig.savefig("figures/fig5_usda_forcing.png", dpi=130)
print("wrote figures/fig5_usda_forcing.png")

# console: crisis-year anomalies
print("\nProduction anomalies (% vs trend):")
for c in CROPS:
    an = detrend_anomalies(load_crop_world(c)["production"])["anomaly"]
    yrs = [2006, 2007, 2008, 2010, 2011]
    print("  %-6s " % c + "  ".join(f"{y}:{100*an.loc[y]:+5.1f}%" for y in yrs))
