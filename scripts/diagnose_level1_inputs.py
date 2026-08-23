#!/usr/bin/env python3
"""Diagnostic CSVs + multi-panel plots for Level-1 observation inputs.

Rebuilds the three observation layers that feed the Level-1 hindcast so they
can be checked regularly without running the model:

  1. USDA PSD country production anomalies (forcing multipliers ξ − 1)
  2. OECD/AMIS export-restriction → τ schedule ($/t)
  3. USDA baseline Q / D0 / stocks vs the illustrative DATA table

Writes:
  diagnostics/level1_psd_anomalies.csv
  diagnostics/level1_amis_tau.csv
  diagnostics/level1_baseline_quantities.csv
  diagnostics/level1_observed_prices.csv
  figures/fig7_psd_country_anomalies.png
  figures/fig8_amis_tau_schedule.png
  figures/fig9_usda_baseline_quantities.png
  figures/fig11_observed_world_prices.png

Example:
  python scripts/diagnose_level1_inputs.py
  python scripts/diagnose_level1_inputs.py --years 2005 2012
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from sheaf.calibration import GRAINS, build_countries
from sheaf.data_usda import (
    amis_tau_schedule,
    country_production_shocks,
    detrend_anomalies,
    load_price_series,
    load_psd_country,
)

ROOT = Path(__file__).resolve().parents[1]
DIAG = ROOT / "diagnostics"
FIGS = ROOT / "figures"

COL = {"wheat": "#c0392b", "rice": "#2874a6", "maize": "#d68910"}
CRISES = [(2007.5, 2008.5), (2010.5, 2011.5)]

# Focus panels on exporters / crisis actors (RestOfWorld omitted from shocks).
FOCUS = [
    "Russia", "Ukraine", "Kazakhstan", "Australia", "Argentina",
    "India", "China", "USA", "EU", "Vietnam", "Thailand",
]


def _years_range(y0: int, y1: int) -> list[int]:
    return list(range(y0, y1 + 1))


def build_psd_anomaly_table(years: list[int],
                            countries: list[str] | None = None) -> pd.DataFrame:
    """Long table: year, country, grain, production_mmt, anomaly, xi."""
    names = countries or FOCUS
    rows = []
    psd_all = load_psd_country("all")
    for grain in GRAINS:
        for cname in names:
            sub = (psd_all[(psd_all["country"] == cname) & (psd_all["grain"] == grain)]
                   .set_index("year")["production"]
                   .sort_index())
            if sub.empty or sub.dropna().shape[0] < 5:
                continue
            an = detrend_anomalies(sub)["anomaly"]
            for y in years:
                if y not in sub.index:
                    continue
                prod = float(sub.loc[y]) if np.isfinite(sub.loc[y]) else np.nan
                a = float(an.loc[y]) if y in an.index and np.isfinite(an.loc[y]) else np.nan
                rows.append(dict(
                    year=y, country=cname, grain=grain,
                    production_mmt=prod,
                    anomaly=a,
                    xi=(1.0 + a) if np.isfinite(a) else np.nan,
                ))
    return pd.DataFrame(rows)


def build_amis_tau_table(years: list[int]) -> pd.DataFrame:
    """Long table from amis_tau_schedule over the USDA node set."""
    countries, _, grains, _ = build_countries(quantities="usda")
    sched = amis_tau_schedule(countries, grains, years)
    name = [c.name for c in countries]
    rows = []
    for t, y in enumerate(years):
        mat = sched[t]
        for i, cname in enumerate(name):
            for g, grain in enumerate(grains):
                tau = float(mat[i, g])
                if tau > 0:
                    rows.append(dict(year=y, country=cname, grain=grain, tau=tau))
    return pd.DataFrame(rows)


def build_baseline_table(baseline_years=(2019, 2020, 2021)) -> pd.DataFrame:
    """Side-by-side illustrative vs USDA overlay quantities (named nodes)."""
    ill, _, grains, _ = build_countries(quantities="illustrative")
    usda, _, _, _ = build_countries(quantities="usda",
                                    baseline_years=baseline_years)
    by_ill = {c.name: c for c in ill}
    rows = []
    for c in usda:
        if c.name == "RestOfWorld":
            # RoW only exists after overlay; still useful to record.
            for g, grain in enumerate(grains):
                rows.append(dict(
                    country=c.name, grain=grain,
                    prod_illustrative=np.nan, cons_illustrative=np.nan,
                    prod_usda=float(c.production[g]),
                    cons_usda=float(c.demand.D0[g]),
                    ending_stocks_seed=float(
                        (c.mkt_stock[g] if c.mkt_stock is not None else 0.0)
                        + (c.gov_stock[g] if c.gov_stock is not None else 0.0)),
                ))
            continue
        ci = by_ill[c.name]
        for g, grain in enumerate(grains):
            stock = 0.0
            if c.mkt_stock is not None:
                stock += float(c.mkt_stock[g])
            if c.gov_stock is not None:
                stock += float(c.gov_stock[g])
            rows.append(dict(
                country=c.name, grain=grain,
                prod_illustrative=float(ci.production[g]),
                cons_illustrative=float(ci.demand.D0[g]),
                prod_usda=float(c.production[g]),
                cons_usda=float(c.demand.D0[g]),
                ending_stocks_seed=stock,
            ))
    return pd.DataFrame(rows)


def plot_psd_anomalies(df: pd.DataFrame, out: Path):
    """3×N panels: production anomaly (%) for focus countries, one grain/col."""
    countries = [c for c in FOCUS if c in set(df.country)]
    n = len(countries)
    fig, axes = plt.subplots(n, 3, figsize=(12, max(2.2 * n, 6)),
                             sharex=True, squeeze=False)
    for j, grain in enumerate(GRAINS):
        for i, cname in enumerate(countries):
            ax = axes[i, j]
            sub = df[(df.country == cname) & (df.grain == grain)].sort_values("year")
            if sub.empty:
                ax.set_visible(False)
                continue
            ax.plot(sub.year, 100 * sub.anomaly, "o-", ms=3, color=COL[grain], lw=1)
            ax.axhline(0, color="0.7", lw=0.7)
            for a, b in CRISES:
                ax.axvspan(a, b, color="0.9", zorder=0)
            if j == 0:
                ax.set_ylabel(cname, fontsize=8)
            if i == 0:
                ax.set_title(grain, color=COL[grain])
            if i == n - 1:
                ax.set_xlabel("year")
            ax.tick_params(labelsize=7)
    fig.suptitle("PSD country production anomalies (% vs LOWESS) — crisis windows shaded",
                 fontsize=12)
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    plt.close(fig)


def plot_amis_tau(df: pd.DataFrame, years: list[int], out: Path):
    """Three heatmaps (wheat / rice / maize): country × year τ ($/t)."""
    if df.empty:
        fig, ax = plt.subplots(figsize=(8, 3))
        ax.text(0.5, 0.5, "no AMIS τ in window", ha="center", va="center")
        ax.axis("off")
        fig.savefig(out, dpi=130)
        plt.close(fig)
        return

    fig, axes = plt.subplots(1, 3, figsize=(14, 5.5))
    for ax, grain in zip(axes, GRAINS):
        sub = df[df.grain == grain]
        countries = sorted(sub.country.unique()) if not sub.empty else []
        if not countries:
            ax.set_title(f"{grain}: (none)")
            ax.axis("off")
            continue
        mat = np.zeros((len(countries), len(years)))
        for i, cname in enumerate(countries):
            for j, y in enumerate(years):
                hit = sub[(sub.country == cname) & (sub.year == y)]
                if not hit.empty:
                    mat[i, j] = float(hit.tau.iloc[0])
        im = ax.imshow(mat, aspect="auto", cmap="YlOrRd", vmin=0, vmax=120)
        ax.set_yticks(range(len(countries)))
        ax.set_yticklabels(countries, fontsize=8)
        ax.set_xticks(range(len(years)))
        ax.set_xticklabels(years, rotation=90, fontsize=7)
        ax.set_title(f"{grain} τ ($/t)")
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.suptitle("AMIS → SHEAF export-tax schedule (strongest overlapping measure)",
                 fontsize=12)
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    plt.close(fig)


def plot_baseline(df: pd.DataFrame, out: Path):
    """Two rows × 3 grains: USDA vs illustrative production and consumption."""
    named = df[df.country != "RestOfWorld"].copy()
    countries = sorted(named.country.unique())
    x = np.arange(len(countries))
    w = 0.38

    fig, axes = plt.subplots(2, 3, figsize=(14, 7), sharey=False)
    for j, grain in enumerate(GRAINS):
        sub = named[named.grain == grain].set_index("country").loc[countries]
        ax = axes[0, j]
        ax.bar(x - w / 2, sub.prod_illustrative, w, label="illustrative", color="0.65")
        ax.bar(x + w / 2, sub.prod_usda, w, label="USDA PSD", color=COL[grain])
        ax.set_title(f"{grain} production (MMT)")
        ax.set_xticks(x)
        ax.set_xticklabels(countries, rotation=90, fontsize=7)
        if j == 0:
            ax.set_ylabel("MMT")
            ax.legend(fontsize=7)

        ax = axes[1, j]
        ax.bar(x - w / 2, sub.cons_illustrative, w, label="illustrative", color="0.65")
        ax.bar(x + w / 2, sub.cons_usda, w, label="USDA PSD", color=COL[grain], alpha=0.85)
        ax.set_title(f"{grain} consumption D0 (MMT)")
        ax.set_xticks(x)
        ax.set_xticklabels(countries, rotation=90, fontsize=7)
        if j == 0:
            ax.set_ylabel("MMT")

    # annotate RoW wheat in a small text box on the production panel
    row = df[(df.country == "RestOfWorld") & (df.grain == "wheat")]
    if not row.empty:
        axes[0, 0].text(
            0.02, 0.98,
            f"RoW wheat prod={row.prod_usda.iloc[0]:.0f} MMT",
            transform=axes[0, 0].transAxes, va="top", fontsize=8, color="0.3")

    fig.suptitle("Baseline quantities: illustrative DATA vs USDA PSD overlay",
                 fontsize=12)
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    plt.close(fig)


def build_observed_prices_table(years: list[int]) -> pd.DataFrame:
    """Pink Sheet nominal + real prices for the diagnostic window."""
    real = load_price_series(deflated=True).loc[years[0]:years[-1]]
    nom = load_price_series(deflated=False).loc[years[0]:years[-1]]
    rows = []
    for y in real.index:
        for g in GRAINS:
            rows.append(dict(
                year=int(y), grain=g,
                price_real_2010_usd_mt=float(real.loc[y, g]),
                price_nominal_usd_mt=float(nom.loc[y, g]),
            ))
    return pd.DataFrame(rows)


def plot_observed_prices(df: pd.DataFrame, out: Path):
    """3 panels: real Pink Sheet prices with crisis shading + YoY %."""
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2))
    for ax, grain in zip(axes, GRAINS):
        sub = df[df.grain == grain].sort_values("year")
        ax.plot(sub.year, sub.price_real_2010_usd_mt, "o-", color=COL[grain],
                label="real 2010$", lw=1.5)
        ax.plot(sub.year, sub.price_nominal_usd_mt, "--", color="0.45",
                label="nominal", lw=1)
        for a, b in CRISES:
            ax.axvspan(a, b, color="0.9", zorder=0)
        ax.set_title(grain)
        ax.set_xlabel("year")
        ax.set_ylabel("$/t")
        ax.legend(fontsize=7)
    fig.suptitle("Observed world prices (World Bank Pink Sheet) — Level-1 target",
                 fontsize=12)
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--start", type=int, default=2005)
    ap.add_argument("--end", type=int, default=2012)
    ap.add_argument("--baseline-years", nargs="+", type=int,
                    default=[2019, 2020, 2021])
    args = ap.parse_args()
    years = _years_range(args.start, args.end)

    DIAG.mkdir(parents=True, exist_ok=True)
    FIGS.mkdir(parents=True, exist_ok=True)

    print("building PSD anomaly table…")
    anom = build_psd_anomaly_table(years)
    anom_path = DIAG / "level1_psd_anomalies.csv"
    anom.to_csv(anom_path, index=False)

    print("building AMIS τ table…")
    tau = build_amis_tau_table(years)
    tau_path = DIAG / "level1_amis_tau.csv"
    tau.to_csv(tau_path, index=False)

    print("building baseline quantity table…")
    base = build_baseline_table(tuple(args.baseline_years))
    base_path = DIAG / "level1_baseline_quantities.csv"
    base.to_csv(base_path, index=False)

    print("building observed price table…")
    prices = build_observed_prices_table(years)
    price_path = DIAG / "level1_observed_prices.csv"
    prices.to_csv(price_path, index=False)

    fig7 = FIGS / "fig7_psd_country_anomalies.png"
    fig8 = FIGS / "fig8_amis_tau_schedule.png"
    fig9 = FIGS / "fig9_usda_baseline_quantities.png"
    fig11 = FIGS / "fig11_observed_world_prices.png"
    print("plotting…")
    plot_psd_anomalies(anom, fig7)
    plot_amis_tau(tau, years, fig8)
    plot_baseline(base, fig9)
    plot_observed_prices(prices, fig11)

    # Quick console checksums for regular eyeballing
    print(f"\nwrote {anom_path}  ({len(anom)} rows)")
    print(f"wrote {tau_path}  ({len(tau)} rows)")
    print(f"wrote {base_path}  ({len(base)} rows)")
    print(f"wrote {price_path}  ({len(prices)} rows)")
    print(f"wrote {fig7}")
    print(f"wrote {fig8}")
    print(f"wrote {fig9}")
    print(f"wrote {fig11}")

    # Sanity: Russia wheat 2010 should be a large negative anomaly; AMIS τ > 0
    ru = anom[(anom.country == "Russia") & (anom.grain == "wheat") & (anom.year == 2010)]
    if not ru.empty and np.isfinite(ru.anomaly.iloc[0]):
        print(f"\nchecksum Russia wheat 2010 anomaly={100*ru.anomaly.iloc[0]:+.1f}%  "
              f"xi={ru.xi.iloc[0]:.3f}")
    ru_tau = tau[(tau.country == "Russia") & (tau.grain == "wheat") & (tau.year == 2010)]
    if not ru_tau.empty:
        print(f"checksum Russia wheat 2010 tau={ru_tau.tau.iloc[0]:.0f} $/t")

    # Also confirm country_production_shocks path matches the table
    countries, _, grains, _ = build_countries(quantities="usda")
    shocks = country_production_shocks(countries, grains, years)
    i = next(i for i, c in enumerate(countries) if c.name == "Russia")
    t2010 = years.index(2010) if 2010 in years else None
    if t2010 is not None:
        print(f"checksum shocks[2010] Russia wheat xi={shocks[t2010][i, 0]:.3f}")


if __name__ == "__main__":
    main()
