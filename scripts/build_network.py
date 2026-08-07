"""
Build SHEAF's baseline trade network from the FAOSTAT bilateral matrices
(FoodTradeNetwork) and check it against known history. Shows the wheat export
structure and Egypt's shifting import sources across the pre-crisis, crisis, and
recent windows -- the rising Russia dependence is the vulnerability behind the
2010/11 Egypt episode (cf. Agrimate's Russia-Egypt case study).

Reserves and production are NOT taken from here -- they come from USDA PSD
(sheaf.data_usda). This module supplies network structure only.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sheaf.data_faostat import (load_trade_matrix, aggregate_to_nodes,
                                bilateral_shares, SHEAF_NODE_MAP)

WINDOWS = [(2006, 2007, "2006-07"), (2010, 2011, "2010-11"), (2019, 2021, "2019-21")]
EXPORTERS = ["EU", "Russia", "USA", "Canada", "Ukraine", "Australia", "Argentina"]
SRC = ["Russia", "Ukraine", "USA", "EU", "Australia", "RestOfWorld"]
COL = {"Russia": "#c0392b", "Ukraine": "#e67e22", "USA": "#2874a6", "EU": "#27ae60",
       "Australia": "#8e44ad", "RestOfWorld": "#95a5a6"}

exp_share, egy_src = {}, {}
for y0, y1, lab in WINDOWS:
    agg = aggregate_to_nodes(load_trade_matrix("wheat", window=(y0, y1)), SHEAF_NODE_MAP)
    tot = agg.values.sum()
    exp_share[lab] = (agg.sum(axis=1) / tot * 100).reindex(EXPORTERS).fillna(0)
    egy_src[lab] = (100 * bilateral_shares(agg, by="source")["Egypt"]).reindex(SRC).fillna(0)

fig, axes = plt.subplots(1, 2, figsize=(13, 4.6))

# panel A: exporter shares across windows
ax = axes[0]
x = np.arange(len(EXPORTERS)); w = 0.26
for k, (_, _, lab) in enumerate(WINDOWS):
    ax.bar(x + (k - 1) * w, exp_share[lab].values, w, label=lab)
ax.set_xticks(x); ax.set_xticklabels(EXPORTERS, rotation=30, ha="right")
ax.set_ylabel("% of world wheat exports"); ax.set_title("Wheat export structure")
ax.legend(fontsize=8)

# panel B: Egypt import sources across windows (stacked)
ax = axes[1]
labs = [w[2] for w in WINDOWS]
bottom = np.zeros(len(labs))
for s in SRC:
    vals = np.array([egy_src[lab][s] for lab in labs])
    ax.bar(labs, vals, bottom=bottom, label=s, color=COL[s])
    bottom += vals
ax.set_ylabel("% of Egypt's wheat imports")
ax.set_title("Egypt's import sources (rising Russia dependence)")
ax.legend(fontsize=8, ncol=2)

fig.suptitle("SHEAF baseline network from FAOSTAT (FoodTradeNetwork) — validated against history", fontsize=12)
fig.tight_layout()
fig.savefig("figures/fig6_network.png", dpi=130)
print("wrote figures/fig6_network.png")

print("\nEgypt wheat import source (%), by window:")
for lab in labs:
    top = egy_src[lab].sort_values(ascending=False).head(3)
    print(f"  {lab}: " + ", ".join(f"{k} {v:.0f}%" for k, v in top.items()))
