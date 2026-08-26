#!/usr/bin/env python3
"""Gate 1 E5: why maize 2010 collapses at σ=0.6.

Counterfactuals on the locked official split. Does not retune CropParams,
ρ, or σ. See overleaf/gate1_substitution/sections/next.tex.
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

from sheaf.data_usda import load_price_series_monthly
from sheaf.dynamic_coupled import run_coupled_dynamics
from sheaf.dynamic_crop import result_to_monthly
from score_subannual_crop import _corr, _hike

DIAG = ROOT / "diagnostics"
FIGS = ROOT / "figures"
HIKE_08 = (2006, 6, 2008, 3)
HIKE_10 = (2009, 6, 2011, 2)


def _row(name: str, res, pink) -> dict:
    out = {"run": name}
    for g in ("wheat", "rice", "maize"):
        obs = pink[["year", "month", g]].rename(columns={g: "obs_price"})
        m = result_to_monthly(res.by_crop[g]).merge(
            obs, on=["year", "month"], how="left")
        out[f"{g}_corr"] = _corr(m.model_price, m.obs_price)
        out[f"{g}_hike08"] = _hike(m, "model_price", *HIKE_08)
        out[f"{g}_hike10"] = _hike(m, "model_price", *HIKE_10)
        out[f"{g}_obs08"] = _hike(obs, "obs_price", *HIKE_08)
        out[f"{g}_obs10"] = _hike(obs, "obs_price", *HIKE_10)
    return out


def main():
    DIAG.mkdir(parents=True, exist_ok=True)
    FIGS.mkdir(parents=True, exist_ok=True)
    pink = load_price_series_monthly(deflated=True)
    pink = pink[(pink.year >= 2006) & (pink.year <= 2011)]
    flags = dict(use_amis=True, use_shocks=True, use_demand=False)

    print("E5 baselines σ=0 and σ=0.6...")
    s0 = run_coupled_dynamics(subst_scale=0.0, **flags)
    s06 = run_coupled_dynamics(subst_scale=0.6, **flags)
    rice0 = s0.by_crop["rice"].price.copy()

    print("E5a  σ=0.6, zero rice–maize ρ...")
    a = run_coupled_dynamics(
        subst_scale=0.6, zero_pairs=(("rice", "maize"),), **flags)
    print("E5b  σ=0.6, rice price held on σ=0 path...")
    b = run_coupled_dynamics(
        subst_scale=0.6, freeze_price={"rice": rice0}, **flags)
    print("E5c  σ=0.6, zero wheat–maize ρ...")
    c = run_coupled_dynamics(
        subst_scale=0.6, zero_pairs=(("wheat", "maize"),), **flags)

    runs = [
        ("σ=0", s0),
        ("σ=0.6", s06),
        ("σ=0.6 zero ρ_rm", a),
        ("σ=0.6 freeze rice", b),
        ("σ=0.6 zero ρ_wm", c),
    ]
    rows = [_row(name, res, pink) for name, res in runs]
    met = pd.DataFrame(rows)
    met.to_csv(DIAG / "gate1_e5_score.csv", index=False)

    m0 = float(met.loc[met.run == "σ=0", "maize_hike10"].iloc[0])
    m06 = float(met.loc[met.run == "σ=0.6", "maize_hike10"].iloc[0])
    drop = m0 - m06
    print(f"\nMaize 2010 hike: σ=0 ×{m0:.2f}  σ=0.6 ×{m06:.2f}  "
          f"drop {drop:.2f}  obs ×{float(met.maize_obs10.iloc[0]):.2f}")
    print("Restoration = share of that drop closed (1 = back at σ=0):")
    for _, r in met.iterrows():
        rest = (float(r.maize_hike10) - m06) / drop if drop else float("nan")
        print(f"  {r.run:22s}  maize10 ×{r.maize_hike10:.2f}  "
              f"restore {rest:5.0%}  maize08 ×{r.maize_hike08:.2f}  "
              f"corr {r.maize_corr:+.3f}")

    fig, ax = plt.subplots(figsize=(11, 4.2))
    obs = pink[["year", "month", "maize"]].rename(columns={"maize": "obs_price"})
    styles = {
        "σ=0": ("--", "#6c3483"),
        "σ=0.6": ("-", "0.15"),
        "σ=0.6 zero ρ_rm": ("-.", "#1e8449"),
        "σ=0.6 freeze rice": (":", "#b9770e"),
        "σ=0.6 zero ρ_wm": ("--", "#1a5276"),
    }
    x = None
    for name, res in runs:
        m = result_to_monthly(res.by_crop["maize"]).merge(
            obs, on=["year", "month"], how="left")
        if x is None:
            x = np.arange(len(m))
            ax.plot(x, m.obs_price, color="#c0392b", lw=2, label="Pink Sheet")
        ls, c = styles[name]
        ax.plot(x, m.model_price, ls=ls, color=c, lw=1.3, label=name)
    ticks = [i for i, mo in enumerate(m.month) if mo == 1]
    ax.set_xticks(ticks, [str(int(m.year.iloc[i])) for i in ticks])
    ax.set_ylabel("$/t")
    ax.set_title("E5: maize world price, official split")
    ax.legend(fontsize=7, ncol=3)
    fig.tight_layout()
    fig.savefig(FIGS / "fig_gate1_e5_maize.png", dpi=140)
    plt.close(fig)

    lines = [
        "# Gate 1 E5 — maize 2010 collapse",
        "",
        "Official split, σ=0.6 counterfactuals. CropParams / ρ structure /",
        "σ grid frozen. Restoration = share of (σ=0 − σ=0.6) maize 2010 hike",
        "closed.",
        "",
        "| Run | maize 2010 | restore | maize 2008 | maize corr |",
        "|---|---:|---:|---:|---:|",
    ]
    for _, r in met.iterrows():
        rest = (float(r.maize_hike10) - m06) / drop if drop else float("nan")
        lines.append(
            f"| {r.run} | ×{r.maize_hike10:.2f} | {rest:.0%} | "
            f"×{r.maize_hike08:.2f} | {r.maize_corr:+.3f} |"
        )
    lines += [
        "",
        f"σ=0 maize 2010 ×{m0:.2f}; σ=0.6 ×{m06:.2f}; obs ×"
        f"{float(met.maize_obs10.iloc[0]):.2f}.",
        "",
        "Figure: `figures/fig_gate1_e5_maize.png`.",
        "Table: `diagnostics/gate1_e5_score.csv`.",
    ]
    (DIAG / "gate1_e5_report.md").write_text("\n".join(lines) + "\n")
    print(f"\nwrote {FIGS / 'fig_gate1_e5_maize.png'}")
    print(f"wrote {DIAG / 'gate1_e5_score.csv'}")
    print(f"wrote {DIAG / 'gate1_e5_report.md'}")


if __name__ == "__main__":
    main()
