#!/usr/bin/env python3
"""Gate 1 consumption diagnostic: world calendar-year use vs country-sum PSD.

Optional E8 leftover check. Official P1 split, frozen σ band. Not a retune
target and not a reason to pick σ*. Gate 0 consumption path leftovers stay
leftovers.

See diagnostics/GATE1_HANDOFF.md.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from score_country_balance import (  # noqa: E402
    country_balance,
    consumption_metrics,
    world_consumption,
)
from sheaf.dynamic_coupled import COUPLED_GRAINS, run_coupled_dynamics

DIAG = ROOT / "diagnostics"
FIGS = ROOT / "figures"
SCALES = (0.0, 0.3, 0.6)


def main() -> None:
    DIAG.mkdir(parents=True, exist_ok=True)
    FIGS.mkdir(parents=True, exist_ok=True)

    yearly = []
    rows = []
    for s in SCALES:
        print(f"  coupled σ={s:g} full...")
        coupled = run_coupled_dynamics(subst_scale=s, use_demand=False)
        for g in COUPLED_GRAINS:
            cbal = country_balance(coupled.by_crop[g], g)
            w = world_consumption(cbal)
            w["grain"] = g
            w["subst_scale"] = s
            yearly.append(w)
            met = consumption_metrics(cbal)
            rows.append(dict(grain=g, subst_scale=s, **met))
            print(f"    {g:5s} mean ×{met['mean_cons_ratio']:.2f}  "
                  f"corr={met['cons_corr']:+.2f}  "
                  f"Δsign {met['dcons_sign']}/{met['dcons_n']}")

    ydf = pd.concat(yearly, ignore_index=True)
    met = pd.DataFrame(rows)
    ydf.to_csv(DIAG / "gate1_consumption.csv", index=False)
    met.to_csv(DIAG / "gate1_consumption_score.csv", index=False)

    fig, axes = plt.subplots(3, 1, figsize=(11, 9.2), sharex=True)
    styles = {0.0: ("--", "#6c3483"), 0.3: ("-.", "#1e8449"),
              0.6: ("-", "0.15")}
    for ax, g in zip(axes, COUPLED_GRAINS):
        sub0 = ydf[(ydf.grain == g) & (ydf.subst_scale == 0.0)]
        ax.plot(sub0.year, sub0.psd_cons, color="#c0392b", lw=2,
                label="country-sum PSD")
        for s in SCALES:
            sub = ydf[(ydf.grain == g) & (ydf.subst_scale == s)]
            ls, c = styles[s]
            ax.plot(sub.year, sub.model_cons, ls=ls, color=c, lw=1.3,
                    label=f"σ={s:g}")
        ax.set_ylabel("MMT")
        ax.set_title(g.capitalize())
        ax.legend(fontsize=7, ncol=4)
    fig.suptitle("Gate 1 diagnostic: world calendar-year use vs PSD "
                 "(not a retune target)")
    fig.tight_layout()
    fig.savefig(FIGS / "fig_gate1_consumption.png", dpi=140)
    plt.close(fig)

    lines = [
        "# Gate 1 consumption diagnostic",
        "",
        "Official split, frozen σ band. Calendar-year world use versus",
        "country-sum PSD (same object as Gate 0). **Not a retune target.**",
        "Do not pick σ* from these ratios.",
        "",
        "| Grain | σ | mean ratio | corr | Δcons sign |",
        "|---|---:|---:|---:|---|",
    ]
    for _, r in met.iterrows():
        lines.append(
            f"| {r['grain']} | {r['subst_scale']:g} | "
            f"×{r['mean_cons_ratio']:.2f} | {r['cons_corr']:+.2f} | "
            f"{int(r['dcons_sign'])}/{int(r['dcons_n'])} |"
        )
    lines += [
        "",
        "Figure: `figures/fig_gate1_consumption.png`.",
        "Tables: `diagnostics/gate1_consumption.csv`, "
        "`diagnostics/gate1_consumption_score.csv`.",
    ]
    (DIAG / "gate1_consumption_report.md").write_text("\n".join(lines) + "\n")
    print(f"wrote {FIGS / 'fig_gate1_consumption.png'}")
    print(f"wrote {DIAG / 'gate1_consumption_score.csv'}")


if __name__ == "__main__":
    main()
