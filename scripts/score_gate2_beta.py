#!/usr/bin/env python3
"""Gate 2 beta: Russia wheat, synthetic harvest cut, illustrative BR.

Does not score AMIS / 2008 / 2010. See diagnostics/GATE2_PLAN.md.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sheaf.dynamic_policy import (
    PolicyKnobs,
    gov_buffer,
    grid_best_response,
    prepare_beta,
    shock_year_harvest,
)

DIAG = ROOT / "diagnostics"
FIGS = ROOT / "figures"


def _table(rows: list[dict], scenario: str) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    df.insert(0, "scenario", scenario)
    return df


def _md_table(tab: pd.DataFrame) -> str:
    cols = ["scenario", "tau", "W", "revenue", "penalty", "mean_stock",
            "min_stock", "mean_price", "sum_exports"]
    sub = tab[cols].copy()
    lines = [
        "| " + " | ".join(cols) + " |",
        "| " + " | ".join("---" for _ in cols) + " |",
    ]
    for _, r in sub.iterrows():
        cells = [
            str(r["scenario"]),
            f"{r['tau']:.1f}",
            f"{r['W']:.1f}",
            f"{r['revenue']:.1f}",
            f"{r['penalty']:.1f}",
            f"{r['mean_stock']:.2f}",
            f"{r['min_stock']:.2f}",
            f"{r['mean_price']:.1f}",
            f"{r['sum_exports']:.2f}",
        ]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def main() -> None:
    DIAG.mkdir(parents=True, exist_ok=True)
    FIGS.mkdir(parents=True, exist_ok=True)
    knobs = PolicyKnobs()
    prep = prepare_beta(knobs)
    H_calm = prep.H
    H_shock = shock_year_harvest(
        prep, knobs.exporter, knobs.shock_year, knobs.harvest_mult)
    s_gov = gov_buffer(prep, knobs)

    tau_calm, rows_calm = grid_best_response(prep, H_calm, knobs)
    tau_shock, rows_shock = grid_best_response(prep, H_shock, knobs)
    tab = pd.concat([_table(rows_calm, "calm"), _table(rows_shock, "shock")],
                    ignore_index=True)
    tab.to_csv(DIAG / "gate2_beta_score.csv", index=False)

    x0 = next(r["sum_exports"] for r in rows_shock if r["tau"] == 0.0)
    xstar = next(r["sum_exports"] for r in rows_shock if r["tau"] == tau_shock)
    bars = [
        ("calm τ* = 0", tau_calm == 0.0),
        ("shock τ* > 0", tau_shock > 0.0),
        ("shock τ* cuts shipments vs τ=0", xstar < x0),
    ]

    print(f"knobs: {knobs}")
    print(f"s_gov = {s_gov:.3f} MMT  (φ={knobs.gov_stu:g} × C_ann)")
    print(f"calm  τ* = {tau_calm:g}")
    print(f"shock τ* = {tau_shock:g}")
    print(tab.to_string(index=False, float_format=lambda x: f"{x:.4g}"))
    for name, ok in bars:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2), sharey=True)
    for ax, name, rows, star in (
            (axes[0], "calm (climatology)", rows_calm, tau_calm),
            (axes[1], f"shock (Russia harvest ×{knobs.harvest_mult:g} in "
                      f"{knobs.shock_year})", rows_shock, tau_shock)):
        taus = [r["tau"] for r in rows]
        Ws = [r["W"] for r in rows]
        ax.plot(taus, Ws, "-o", color="0.15")
        ax.axvline(star, color="#c0392b", ls="--", lw=1.2, label=f"τ*={star:g}")
        ax.set_title(name)
        ax.set_xlabel("τ (export cut)")
        ax.set_xticks(list(knobs.tau_grid))
        ax.legend(fontsize=8)
    axes[0].set_ylabel(r"illustrative $W$ (revenue − $\alpha\cdot$ year-mean gap$^2$)")
    fig.suptitle("Gate 2 beta: Russia wheat, one-player grid BR "
                 "(not an AMIS hindcast)")
    fig.tight_layout()
    fig.savefig(FIGS / "fig_gate2_beta_welfare.png", dpi=140)
    plt.close(fig)

    bar_lines = "\n".join(
        f"- [{'PASS' if ok else 'FAIL'}] {name}" for name, ok in bars)
    lines = [
        "# Gate 2 beta",
        "",
        f"Exporter {knobs.exporter} wheat. Synthetic {knobs.shock_year} "
        f"harvest ×{knobs.harvest_mult:g}. AMIS off. Illustrative "
        f"`gov_stu`={knobs.gov_stu:g}, `fs_stock_weight`="
        f"{knobs.fs_stock_weight:g}. Government buffer s_gov = "
        f"{s_gov:.2f} MMT.",
        "",
        f"- Calm τ* = **{tau_calm:g}**",
        f"- Shock τ* = **{tau_shock:g}**",
        "",
        bar_lines,
        "",
        "Not scored against 2008/10 AMIS. See `diagnostics/GATE2_PLAN.md`.",
        "",
        _md_table(tab),
        "",
        "Table: `diagnostics/gate2_beta_score.csv`.",
        "Figure: `figures/fig_gate2_beta_welfare.png`.",
    ]
    (DIAG / "gate2_beta_report.md").write_text("\n".join(lines) + "\n")
    print(f"wrote {FIGS / 'fig_gate2_beta_welfare.png'}")


if __name__ == "__main__":
    main()
