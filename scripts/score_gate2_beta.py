#!/usr/bin/env python3
"""Gate 2 beta: Russia wheat, Headey-clock actions, nested year BR.

Does not score AMIS / 2008 / 2010. Does not re-run Gate 0 or Gate 1.
Choropleths (who / fortnights on / stock ratio) are part of every run.
See diagnostics/GAME_CLOCK.md and diagnostics/GATE2_PLAN.md.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sheaf.calendar24 import STEPS_PER_YEAR
from sheaf.dynamic_crop import simulate_prep
from sheaf.dynamic_policy import (
    PolicyKnobs,
    exporter_index,
    gov_buffer,
    grid_best_response,
    prepare_beta,
    shock_year_harvest,
    simulate_headey,
    year_slice,
)
from sheaf.maps import plot_categories, plot_choropleth, safe_min_ratio

DIAG = ROOT / "diagnostics"
FIGS = ROOT / "figures"
WP_FIGS = ROOT / "overleaf" / "gate2_assessment" / "figures"


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
    sl = year_slice(prep, knobs.shock_year)
    i = exporter_index(prep, knobs.exporter)

    tau_calm, rows_calm = grid_best_response(prep, H_calm, knobs)
    tau_shock, rows_shock = grid_best_response(prep, H_shock, knobs)
    tab = pd.concat([_table(rows_calm, "calm"), _table(rows_shock, "shock")],
                    ignore_index=True)
    tab.to_csv(DIAG / "gate2_beta_score.csv", index=False)

    _, cuts_calm, meta_calm = simulate_headey(prep, H_calm, knobs)
    res_closed, cuts_shock, meta_shock = simulate_headey(prep, H_shock, knobs)
    res_calm = simulate_prep(prep, harvest=H_calm)
    res_open = simulate_prep(prep, harvest=H_shock)
    kz = "Kazakhstan"
    ua = "Ukraine"
    ru_c = meta_calm["by_player"][knobs.exporter]
    ru_s = meta_shock["by_player"][knobs.exporter]
    kz_c = meta_calm["by_player"][kz]
    kz_s = meta_shock["by_player"][kz]
    i_kz = exporter_index(prep, kz)
    i_ua = exporter_index(prep, ua)

    def _min_ratio(res, idx) -> float:
        s = np.asarray(res.stock[idx, sl], float)
        c = np.asarray(res_calm.stock[idx, sl], float)
        return float((s / np.maximum(c, 1e-9)).min())

    ua_open_min = _min_ratio(res_open, i_ua)
    kz_closed_min = _min_ratio(res_closed, i_kz)

    x0 = next(r["sum_exports"] for r in rows_shock if r["tau"] == 0.0)
    xstar = next(r["sum_exports"] for r in rows_shock if r["tau"] == tau_shock)
    calm_all_off = all(
        meta_calm["by_player"][n]["n_year"] == 0 for n in knobs.players)
    bars = [
        ("nested year: calm τ* = 0", tau_calm == 0.0),
        ("nested year: shock τ* > 0", tau_shock > 0.0),
        ("nested year: shock τ* cuts shipments vs τ=0", xstar < x0),
        ("Headey: calm all players τ_t = 0", calm_all_off),
        ("Headey: shock Russia some τ_t > 0", ru_s["max_tau"] > 0.0),
        ("Headey: shock Kazakhstan some τ_t > 0 (no own harvest cut)",
         kz_s["n_year"] > 0),
        ("Headey: Kazakhstan lags or ties Russia",
         kz_s["first_on"] is not None and ru_s["first_on"] is not None
         and kz_s["first_on"] >= ru_s["first_on"]),
        ("Headey: Russia cuts shipments vs open",
         ru_s["closed_exports"] < ru_s["open_exports"]),
    ]

    print(f"knobs: {knobs}")
    print(f"s_gov = {s_gov:.3f} MMT  (φ={knobs.gov_stu:g} × C_ann)")
    print(f"nested year  calm τ* = {tau_calm:g}  shock τ* = {tau_shock:g}")
    print(f"Headey Russia  calm on={ru_c['n_year']}  shock on={ru_s['n_year']}/24  "
          f"first={ru_s['first_on']}  min ratio={ru_s['min_ratio']:.3f}")
    print(f"Headey Kazakhstan  calm on={kz_c['n_year']}  shock on={kz_s['n_year']}/24  "
          f"first={kz_s['first_on']}  min ratio={kz_s['min_ratio']:.3f}")
    print(f"Ukraine open min ratio={ua_open_min:.3f}  "
          f"KZ closed min ratio={kz_closed_min:.3f}")
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
        ax.set_xlabel("τ (year-open-loop, nested)")
        ax.set_xticks(list(knobs.tau_grid))
        ax.legend(fontsize=8)
    axes[0].set_ylabel(r"illustrative $W$ (revenue − $\alpha\cdot$ year-mean gap$^2$)")
    fig.suptitle("Gate 2 nested year BR (not the Headey path; not AMIS)")
    fig.tight_layout()
    fig.savefig(FIGS / "fig_gate2_beta_welfare.png", dpi=140)
    plt.close(fig)

    steps = list(range(STEPS_PER_YEAR))
    fig2, ax = plt.subplots(figsize=(8.4, 4.0))
    ax.step(steps, cuts_shock[i, sl], where="mid", color="#c0392b",
            label=f"Russia τ_t (harvest ×{knobs.harvest_mult:g})")
    ax.step(steps, cuts_shock[i_kz, sl], where="mid", color="#2471a3",
            label="Kazakhstan τ_t (no harvest cut)")
    ax.step(steps, cuts_calm[i, sl], where="mid", color="0.75",
            ls=":", label="calm (both)")
    ax.set_ylim(-0.05, max(knobs.tau_on, 0.9) + 0.15)
    ax.set_xlabel(f"fortnight in {knobs.shock_year}")
    ax.set_ylabel("τ_t (export cut)")
    ax.set_title("Cascade: Russia harvest shock, both play the same type "
                 "(not AMIS)")
    ax.legend(fontsize=8)
    fig2.tight_layout()
    fig2.savefig(FIGS / "fig_gate2_headey_tau.png", dpi=140)
    plt.close(fig2)

    fig3, ax = plt.subplots(figsize=(8.4, 4.2))
    for name, color, res, ls, lab in (
            ("Russia", "#c0392b", res_open, "-", "Russia open"),
            ("Kazakhstan", "#2471a3", res_open, "-", "Kazakhstan open"),
            ("Ukraine", "#7d3c98", res_open, "-", "Ukraine open (not a player)"),
            ("Kazakhstan", "#2471a3", res_closed, "--", "Kazakhstan closed"),
    ):
        j = exporter_index(prep, name)
        ratio = (np.asarray(res.stock[j, sl], float)
                 / np.maximum(np.asarray(res_calm.stock[j, sl], float), 1e-9))
        ax.plot(steps, ratio, color=color, ls=ls, label=lab)
    ax.axhline(knobs.stock_ratio_trigger, color="0.35", ls=":",
               label=f"trigger r={knobs.stock_ratio_trigger:g}")
    ax.set_xlabel(f"fortnight in {knobs.shock_year}")
    ax.set_ylabel(r"$S_t / S^{\mathrm{calm}}_t$")
    ax.set_title("Open-path stock ratios after Russia harvest ×0.50 "
                 "(closed Kazakhstan dashed)")
    ax.legend(fontsize=7, ncol=2)
    fig3.tight_layout()
    fig3.savefig(FIGS / "fig_gate2_ratios.png", dpi=140)
    plt.close(fig3)

    named = [c for c in prep.countries if c != "RestOfWorld"]
    roles = {}
    n_on = {}
    open_min = {}
    for name in named:
        if name == knobs.exporter:
            roles[name] = "harvest shock"
        elif name in knobs.players:
            roles[name] = "player (no harvest cut)"
        else:
            roles[name] = "on market, not playing"
        j = exporter_index(prep, name)
        open_min[name] = safe_min_ratio(
            res_open.stock[j, sl], res_calm.stock[j, sl])
        n_on[name] = int(meta_shock["by_player"][name]["n_year"]) if name in meta_shock["by_player"] else 0
    plot_categories(
        roles, FIGS / "fig_gate2_map_roles.png",
        title="Who plays (same type; not AMIS, not 2008)")
    plot_choropleth(
        n_on, FIGS / "fig_gate2_map_on.png",
        title=f"Fortnights on in {knobs.shock_year} (of 24)",
        label="fortnights with τ_t = τ_on",
        cmap="YlOrRd", vmin=0, vmax=24)
    plot_choropleth(
        open_min, FIGS / "fig_gate2_map_ratio.png",
        title="Open-path min $S_t/S^{\\mathrm{calm}}_t$ after Russia harvest ×0.50",
        label=r"min $S/S^{\mathrm{calm}}$",
        cmap="RdYlBu", vmin=0.40, vmax=1.05, vcenter=knobs.stock_ratio_trigger)

    bar_lines = "\n".join(
        f"- [{'PASS' if ok else 'FAIL'}] {name}" for name, ok in bars)
    lines = [
        "# Gate 2 beta",
        "",
        f"Players {', '.join(knobs.players)}. Synthetic {knobs.shock_year} "
        f"{knobs.exporter} harvest ×{knobs.harvest_mult:g}; Kazakhstan harvest "
        f"unchanged. AMIS off. Illustrative types: "
        f"`gov_stu`={knobs.gov_stu:g}, `fs_stock_weight`="
        f"{knobs.fs_stock_weight:g}, `tau_on`={knobs.tau_on:g}, "
        f"`stock_ratio_trigger`={knobs.stock_ratio_trigger:g}. "
        f"s_gov (Russia) = {s_gov:.2f} MMT.",
        "",
        "Gate 0 and Gate 1 were **not** re-run. Clock: "
        "`diagnostics/GAME_CLOCK.md`.",
        "",
        "### Headey path (headline)",
        "",
        f"- Russia calm on: **{ru_c['n_year']}** / 24; shock on: "
        f"**{ru_s['n_year']}** / 24 (first step {ru_s['first_on']}, "
        f"min S/S_calm = {ru_s['min_ratio']:.2f})",
        f"- Kazakhstan calm on: **{kz_c['n_year']}** / 24; shock on: "
        f"**{kz_s['n_year']}** / 24 (first step {kz_s['first_on']}, "
        f"min S/S_calm = {kz_s['min_ratio']:.2f}) — no own harvest cut",
        f"- Russia shipments {ru_s['open_exports']:.2f} → "
        f"{ru_s['closed_exports']:.2f} MMT",
        f"- Kazakhstan shipments {kz_s['open_exports']:.2f} → "
        f"{kz_s['closed_exports']:.2f} MMT",
        f"- Ukraine open min S/S_calm = {ua_open_min:.2f} (not a player; "
        f"above r={knobs.stock_ratio_trigger:g})",
        f"- Kazakhstan closed min S/S_calm = {kz_closed_min:.2f} "
        f"(open {kz_s['min_ratio']:.2f}; cuts raise the trough)",
        "",
        "Cascade is **harvest diversion** (Kazakhstan’s open-path "
        "S/S_calm already below r after Russia’s harvest fails), not "
        "sequential ban-on-ban IBR. Ukraine is on the market but does "
        "not play.",
        "",
        "### Nested year-open-loop BR (diagnostic)",
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
        "Figures: `figures/fig_gate2_beta_welfare.png`, "
        "`figures/fig_gate2_headey_tau.png`, "
        "`figures/fig_gate2_ratios.png`, "
        "`figures/fig_gate2_map_roles.png`, "
        "`figures/fig_gate2_map_on.png`, "
        "`figures/fig_gate2_map_ratio.png`.",
        "Assessment note: `overleaf/gate2_assessment/`.",
    ]
    (DIAG / "gate2_beta_report.md").write_text("\n".join(lines) + "\n")
    WP_FIGS.mkdir(parents=True, exist_ok=True)
    fig_names = (
        "fig_gate2_beta_welfare.png", "fig_gate2_headey_tau.png",
        "fig_gate2_ratios.png", "fig_gate2_map_roles.png",
        "fig_gate2_map_on.png", "fig_gate2_map_ratio.png",
    )
    for name in fig_names:
        shutil.copy2(FIGS / name, WP_FIGS / name)
        print(f"wrote {FIGS / name}")
    print(f"copied figures → {WP_FIGS}")
    print(f"Ukraine open min ratio={ua_open_min:.3f}  "
          f"KZ closed min ratio={kz_closed_min:.3f}")


if __name__ == "__main__":
    main()
