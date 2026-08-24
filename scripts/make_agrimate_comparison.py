#!/usr/bin/env python3
"""Agrimate-style Gate 0 figures and Overleaf tables (Kuhla et al. 2025).

Reproduces the *checks* in Agrimate Fig. 3, Fig. 4a/b/e, Fig. 5–7 (wheat),
and Suppl. Figs. G.1–G.2 (rice, maize). Soybean is out of SHEAF's grain set.

Agrimate's published scenarios are:
  baseline            — climatology harvest, no AMIS
  production          — year-by-year harvest, no AMIS
  full (matched)      — harvest + AMIS  (endogenous consumption only)

SHEAF official matched (P1 headline) is harvest + AMIS + mean flex, with USA
maize industrial (RFS residual) on as a structural mandate. Year-by-year PSD
food/feed is an extra dashed sensitivity, not the Agrimate-matched series.

Writes PDFs under overleaf/gate0_agrimate/figures/ and a metrics.tex snippet.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from sheaf.calendar24 import STEPS_PER_YEAR, steps_in_month
from sheaf.data_usda import load_crop_world, load_price_series_monthly, load_psd_country
from sheaf.dynamic_crop import run_crop_dynamics

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "overleaf" / "gate0_agrimate"
FIG = OUT / "figures"
TAB = OUT / "tables"

# Agrimate Fig. 4 palette
C_BASE = "#7f7f7f"
C_PROD = "#2ca02c"
C_FULL = "#e67e22"
C_OBS = "#1f4e79"
C_SHEAF = "#6c3483"

MY_END_MONTH = {"wheat": 5, "maize": 8, "rice": 12}


def _months(res):
    rows = []
    for y in range(res.start_year, res.end_year + 1):
        for m in range(1, 13):
            rows.append((y, m))
    return rows


def _monthly_mean(res, arr1d: np.ndarray) -> np.ndarray:
    out = []
    for y, m in _months(res):
        idx = steps_in_month(y, m, res.start_year)
        out.append(float(np.mean(arr1d[idx])))
    return np.asarray(out)


def _monthly_sum(res, arr1d: np.ndarray) -> np.ndarray:
    out = []
    for y, m in _months(res):
        idx = steps_in_month(y, m, res.start_year)
        out.append(float(np.sum(arr1d[idx])))
    return np.asarray(out)


def _xdates(res):
    return [pd.Timestamp(y, m, 1) for y, m in _months(res)]


def _withheld(res) -> np.ndarray:
    cut = np.asarray(res.export_cut, float)
    off = np.asarray(res.offers, float)
    w = np.zeros_like(off)
    mask = cut > 1e-9
    w[mask] = off[mask] * cut[mask] / np.maximum(1.0 - cut[mask], 1e-6)
    return w


def _corr(a, b) -> float:
    a, b = np.asarray(a, float), np.asarray(b, float)
    m = np.isfinite(a) & np.isfinite(b)
    if m.sum() < 6:
        return float("nan")
    return float(np.corrcoef(a[m], b[m])[0, 1])


def _hike(dates, series, y0, m0, y1, m1) -> float:
    def win(y, m):
        vals = []
        for dm in (-1, 0, 1):
            mm, yy = m + dm, y
            if mm < 1:
                mm += 12
                yy -= 1
            if mm > 12:
                mm -= 12
                yy += 1
            for i, d in enumerate(dates):
                if d.year == yy and d.month == mm:
                    vals.append(float(series[i]))
        return float(np.mean(vals)) if vals else float("nan")
    b, p = win(y0, m0), win(y1, m1)
    return p / b if b and np.isfinite(b) and np.isfinite(p) else float("nan")


def _obs_series(crop, dates):
    pink = load_price_series_monthly(deflated=True)
    out = []
    for d in dates:
        hit = pink[(pink.year == d.year) & (pink.month == d.month)]
        out.append(float(hit[crop].iloc[0]) if len(hit) else np.nan)
    return np.asarray(out)


def _run_crop(crop: str) -> dict:
    print(f"  running {crop} legs…")
    legs = {
        "baseline": run_crop_dynamics(
            crop, use_amis=False, use_shocks=False, use_demand=False,
            use_industrial=False),
        "production": run_crop_dynamics(
            crop, use_amis=False, use_shocks=True, use_demand=False),
        "full_matched": run_crop_dynamics(
            crop, use_amis=True, use_shocks=True, use_demand=False),
        "full_sheaf": run_crop_dynamics(
            crop, use_amis=True, use_shocks=True, use_demand=True),
    }
    return legs


def _style():
    plt.rcParams.update({
        "font.size": 9,
        "axes.titlesize": 10,
        "axes.labelsize": 9,
        "legend.fontsize": 8,
        "figure.dpi": 140,
        "savefig.bbox": "tight",
        "pdf.fonttype": 42,
        "axes.spines.top": False,
        "axes.spines.right": False,
    })


def fig_forcing(crop, legs, dates):
    """Agrimate Fig. 3 / G.* panels a–b: harvest and restricted exports."""
    full = legs["full_matched"]
    base = legs["baseline"]
    prod = legs["production"]
    h_full = _monthly_sum(full, full.harvest.sum(axis=0))
    h_base = _monthly_sum(base, base.harvest.sum(axis=0))
    h_prod = _monthly_sum(prod, prod.harvest.sum(axis=0))
    anom = (h_prod / np.maximum(h_base, 1e-9) - 1.0) * 100.0
    withheld = _monthly_sum(full, _withheld(full).sum(axis=0))

    fig, axes = plt.subplots(3, 1, figsize=(7.2, 6.4), sharex=True)
    ax = axes[0]
    ax.plot(dates, h_base, color=C_BASE, ls="-.", lw=1.2, label="baseline harvest")
    ax.plot(dates, h_prod, color=C_PROD, ls="-", lw=1.4, label="production anomalies")
    ax.set_ylabel("World harvest\n(MMT / month)")
    ax.set_title(f"{crop.capitalize()}: harvest, anomaly, restricted exports")
    ax.legend(loc="upper right", frameon=False)

    ax = axes[1]
    ax.axhline(0, color="0.7", lw=0.6)
    ax.plot(dates, anom, color=C_PROD, lw=1.4)
    ax.set_ylabel("Harvest anomaly\n(% baseline)")

    ax = axes[2]
    ax.fill_between(dates, withheld, color=C_FULL, alpha=0.7, lw=0)
    ax.set_ylabel("Restricted exports\n(MMT / month)")
    ax.set_xlabel("Month")
    fig.autofmt_xdate()
    fig.savefig(FIG / f"fig_forcing_{crop}.pdf")
    fig.savefig(FIG / f"fig_forcing_{crop}.png")
    plt.close(fig)


def fig_prices(crop, legs, dates, obs, metrics: dict):
    """Agrimate Fig. 4a / G.* panel c."""
    p_base = _monthly_mean(legs["baseline"], legs["baseline"].price)
    p_prod = _monthly_mean(legs["production"], legs["production"].price)
    p_full = _monthly_mean(legs["full_matched"], legs["full_matched"].price)
    p_sheaf = _monthly_mean(legs["full_sheaf"], legs["full_sheaf"].price)

    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    ax.plot(dates, obs, color=C_OBS, ls="--", lw=1.6,
            label="Pink Sheet (real, 2010 $)")
    ax.plot(dates, p_base, color=C_BASE, ls="-.", lw=1.1, label="baseline")
    ax.plot(dates, p_prod, color=C_PROD, ls=":", lw=1.5,
            label="production anomalies")
    ax.plot(dates, p_full, color=C_FULL, ls="-", lw=1.6,
            label="full (harvest + AMIS)")
    if np.nanmax(np.abs(p_sheaf - p_full)) > 5:
        ax.plot(dates, p_sheaf, color=C_SHEAF, ls="--", lw=1.2,
                label="SHEAF full (+ year-by-year demand)")
    ax.set_ylabel("World price ($/t)")
    ax.set_title(f"{crop.capitalize()} world price — Agrimate scenario split")
    ax.legend(loc="upper left", frameon=False, ncol=2)
    fig.autofmt_xdate()
    fig.savefig(FIG / f"fig_prices_{crop}.pdf")
    fig.savefig(FIG / f"fig_prices_{crop}.png")
    plt.close(fig)

    metrics[crop] = dict(
        corr_matched=_corr(p_full, obs),
        corr_sheaf=_corr(p_sheaf, obs),
        corr_prod=_corr(p_prod, obs),
        hike07_obs=_hike(dates, obs, 2006, 6, 2008, 3),
        hike07_matched=_hike(dates, p_full, 2006, 6, 2008, 3),
        hike07_sheaf=_hike(dates, p_sheaf, 2006, 6, 2008, 3),
        hike07_prod=_hike(dates, p_prod, 2006, 6, 2008, 3),
        hike10_obs=_hike(dates, obs, 2009, 6, 2011, 2),
        hike10_matched=_hike(dates, p_full, 2009, 6, 2011, 2),
        hike10_sheaf=_hike(dates, p_sheaf, 2009, 6, 2011, 2),
        hike10_prod=_hike(dates, p_prod, 2009, 6, 2011, 2),
    )


def fig_global_balance(crop, legs):
    """Agrimate Fig. 4b,e: annual supply and stock *changes* vs PSD."""
    world = load_crop_world(crop)
    full = legs["full_sheaf"]
    years = list(range(full.start_year, full.end_year + 1))
    base_years = [2007, 2008, 2009]
    mean_p = float(world.loc[base_years, "production"].mean())
    my = MY_END_MONTH[crop]

    psd_supply = []
    psd_dstock = []
    mod_supply = []
    mod_dstock = []
    prev_psd = float(world.loc[years[0] - 1, "ending_stocks"]) if (years[0] - 1) in world.index else np.nan
    prev_mod = np.nan
    for y in years:
        psd_supply.append((float(world.loc[y, "production"]) / mean_p - 1.0) * 100.0)
        end = float(world.loc[y, "ending_stocks"])
        psd_dstock.append(((end - prev_psd) / mean_p) * 100.0 if np.isfinite(prev_psd) else np.nan)
        prev_psd = end

        t0 = (y - full.start_year) * STEPS_PER_YEAR
        t1 = t0 + STEPS_PER_YEAR
        h = float(full.harvest[:, t0:t1].sum())
        mod_supply.append((h / mean_p - 1.0) * 100.0)
        t_my = (y - full.start_year) * STEPS_PER_YEAR + (my - 1) * 2 + 1
        st = float(full.stock[:, t_my].sum())
        mod_dstock.append(((st - prev_mod) / mean_p) * 100.0 if np.isfinite(prev_mod) else np.nan)
        prev_mod = st

    x = np.arange(len(years))
    w = 0.35
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.8))
    ax = axes[0]
    ax.bar(x - w / 2, psd_supply, w, color=C_OBS, label="PSD production")
    ax.bar(x + w / 2, mod_supply, w, color=C_FULL, label="model harvest")
    ax.axhline(0, color="0.5", lw=0.6)
    ax.set_xticks(x, years)
    ax.set_ylabel("% vs 2007–09 mean production")
    ax.set_title(f"{crop.capitalize()} global supply change")
    ax.legend(frameon=False)

    ax = axes[1]
    ax.bar(x - w / 2, psd_dstock, w, color=C_OBS, label="PSD Δ ending stocks")
    ax.bar(x + w / 2, mod_dstock, w, color=C_FULL, label=f"model Δ MY-end (m={my})")
    ax.axhline(0, color="0.5", lw=0.6)
    ax.set_xticks(x, years)
    ax.set_title(f"{crop.capitalize()} global stock change")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(FIG / f"fig_balance_{crop}.pdf")
    fig.savefig(FIG / f"fig_balance_{crop}.png")
    plt.close(fig)

    # sign agreement excluding first year (Δstock needs lag)
    s_ag = sum(np.sign(a) == np.sign(b) for a, b in zip(psd_supply, mod_supply)
               if np.isfinite(a) and np.isfinite(b))
    k_ag = sum(np.sign(a) == np.sign(b)
               for a, b in zip(psd_dstock[1:], mod_dstock[1:])
               if np.isfinite(a) and np.isfinite(b))
    return dict(supply_sign=s_ag, supply_n=len(years),
                stock_sign=k_ag, stock_n=len(years) - 1)


def fig_regional_2007(crop, legs):
    """Agrimate Fig. 4c–g style, as bars (SHEAF nodes, not 28-region map)."""
    psd = load_psd_country(crop)
    full = legs["full_sheaf"]
    countries = [c for c in full.countries if c != "RestOfWorld"]
    base_years = [2007, 2008, 2009]

    def psd_mean(c, col):
        sub = psd[(psd.country == c) & (psd.year.isin(base_years))]
        return float(sub[col].mean()) if len(sub) else np.nan

    names, p_obs, p_mod, s_obs, s_mod = [], [], [], [], []
    y = 2007
    t0 = (y - full.start_year) * STEPS_PER_YEAR
    t1 = t0 + STEPS_PER_YEAR
    my = MY_END_MONTH[crop]
    t_my = (y - full.start_year) * STEPS_PER_YEAR + (my - 1) * 2 + 1
    t_my0 = (y - 1 - full.start_year) * STEPS_PER_YEAR + (my - 1) * 2 + 1
    for i, c in enumerate(full.countries):
        if c == "RestOfWorld":
            continue
        mp = psd_mean(c, "production")
        hit = psd[(psd.country == c) & (psd.year == y)]
        if mp < 1.0 or not len(hit):
            continue
        names.append(c)
        p_obs.append((float(hit.production.iloc[0]) / mp - 1.0) * 100.0)
        h = float(full.harvest[i, t0:t1].sum())
        p_mod.append((h / mp - 1.0) * 100.0)
        ms = psd_mean(c, "production")  # stock Δ as % of typical production
        e07 = float(hit.ending_stocks.iloc[0])
        hit0 = psd[(psd.country == c) & (psd.year == y - 1)]
        e06 = float(hit0.ending_stocks.iloc[0]) if len(hit0) else np.nan
        s_obs.append(((e07 - e06) / ms) * 100.0 if np.isfinite(e06) else np.nan)
        if t_my0 >= 0:
            s_mod.append(((float(full.stock[i, t_my])
                           - float(full.stock[i, t_my0])) / ms) * 100.0)
        else:
            s_mod.append(np.nan)

    order = np.argsort(np.abs(p_obs))[::-1]
    names = [names[k] for k in order]
    p_obs = [p_obs[k] for k in order]
    p_mod = [p_mod[k] for k in order]
    s_obs = [s_obs[k] for k in order]
    s_mod = [s_mod[k] for k in order]
    yx = np.arange(len(names))

    fig, axes = plt.subplots(1, 2, figsize=(8.2, 4.6), sharey=True)
    ax = axes[0]
    ax.barh(yx + 0.18, p_obs, 0.35, color=C_OBS, label="PSD")
    ax.barh(yx - 0.18, p_mod, 0.35, color=C_FULL, label="model")
    ax.axvline(0, color="0.5", lw=0.6)
    ax.set_yticks(yx, names)
    ax.set_xlabel("2007 production vs 2007–09 mean (%)")
    ax.set_title("Regional supply change, 2007")
    ax.legend(frameon=False)
    ax.invert_yaxis()

    ax = axes[1]
    ax.barh(yx + 0.18, s_obs, 0.35, color=C_OBS, label="PSD")
    ax.barh(yx - 0.18, s_mod, 0.35, color=C_FULL, label="model")
    ax.axvline(0, color="0.5", lw=0.6)
    ax.set_xlabel("2007 Δ stocks / mean production (%)")
    ax.set_title("Regional stock change, 2007")
    fig.tight_layout()
    fig.savefig(FIG / f"fig_regional2007_{crop}.pdf")
    fig.savefig(FIG / f"fig_regional2007_{crop}.png")
    plt.close(fig)


def fig_russia_egypt(legs, dates):
    """Agrimate Fig. 5–7 wheat: Russia supplier, Egypt purchaser, bilateral share."""
    full = legs["full_matched"]
    base = legs["baseline"]
    prod = legs["production"]
    sheaf = legs["full_sheaf"]
    ir = full.countries.index("Russia")
    ie = full.countries.index("Egypt")

    def pack(res, i):
        return dict(
            h=_monthly_sum(res, res.harvest[i]),
            x=_monthly_sum(res, res.exports[i]),
            s=_monthly_mean(res, res.stock[i]),
            q=_monthly_mean(res, res.ask[i]),
            w=_monthly_sum(res, _withheld(res)[i]),
            recv=_monthly_sum(res, res.received[i]) if res.received is not None else None,
            c=_monthly_sum(res, res.consumption[i]),
        )

    series = {k: pack(v, ir) for k, v in
              [("baseline", base), ("production", prod),
               ("full", full), ("sheaf", sheaf)]}
    egy = {k: pack(v, ie) for k, v in
           [("baseline", base), ("production", prod),
            ("full", full), ("sheaf", sheaf)]}

    def ru_eg(res):
        return _monthly_sum(res, res.trade[ir, ie, :])

    fig, axes = plt.subplots(3, 2, figsize=(7.4, 7.0), sharex=True)
    specs = [
        (0, 0, "h", "Russia harvest (MMT/mo)", False),
        (0, 1, "q", "Russia ask ($/t)", False),
        (1, 0, "x", "Russia exports (MMT/mo)", False),
        (1, 1, "w", "Russia withheld (MMT/mo)", False),
        (2, 0, "s", "Russia stocks (MMT)", False),
    ]
    styles = [("baseline", C_BASE, "-."), ("production", C_PROD, ":"),
              ("full", C_FULL, "-")]
    for r, c, key, ylab, _ in specs:
        ax = axes[r, c]
        for name, col, ls in styles:
            ax.plot(dates, series[name][key], color=col, ls=ls, lw=1.3, label=name)
        ax.set_ylabel(ylab)
    axes[0, 0].legend(frameon=False, fontsize=7)
    axes[0, 0].set_title("Wheat — Russia supplier (Agrimate Fig. 5)")

    ax = axes[2, 1]
    for name, col, ls in styles:
        ax.plot(dates, egy[name]["recv"], color=col, ls=ls, lw=1.3, label=name)
    ax.set_ylabel("Egypt receipts (MMT/mo)")
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(FIG / "fig_russia_wheat.pdf")
    fig.savefig(FIG / "fig_russia_wheat.png")
    plt.close(fig)

    fig, axes = plt.subplots(3, 1, figsize=(7.2, 6.2), sharex=True)
    ax = axes[0]
    for name, col, ls in styles:
        ax.plot(dates, egy[name]["c"], color=col, ls=ls, lw=1.3, label=name)
    ax.set_ylabel("Egypt consumption\n(MMT/mo)")
    ax.set_title("Wheat — Egypt purchaser (Agrimate Fig. 6)")
    ax.legend(frameon=False)

    ax = axes[1]
    for name, col, ls in styles:
        ax.plot(dates, egy[name]["s"], color=col, ls=ls, lw=1.3)
    ax.set_ylabel("Egypt stocks (MMT)")

    ax = axes[2]
    tot = egy["full"]["recv"]
    share = ru_eg(full) / np.maximum(tot, 1e-9) * 100.0
    share_b = ru_eg(base) / np.maximum(egy["baseline"]["recv"], 1e-9) * 100.0
    ax.plot(dates, share_b, color=C_BASE, ls="-.", lw=1.2, label="baseline Russia share")
    ax.plot(dates, share, color=C_FULL, ls="-", lw=1.5, label="full Russia share")
    ax.set_ylabel("Russia share of\nEgypt receipts (%)")
    ax.set_xlabel("Month")
    ax.legend(frameon=False)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(FIG / "fig_egypt_wheat.pdf")
    fig.savefig(FIG / "fig_egypt_wheat.png")
    plt.close(fig)


def write_metrics_tex(metrics: dict, signs: dict):
    TAB.mkdir(parents=True, exist_ok=True)
    lines = [
        r"% auto-generated by scripts/make_agrimate_comparison.py",
        r"\begin{tabular}{l rr rrr rrr}",
        r"\toprule",
        r" & \multicolumn{3}{c}{monthly corr} & "
        r"\multicolumn{3}{c}{2007/08 hike} & "
        r"\multicolumn{3}{c}{2010/11 hike} \\",
        r"\cmidrule(lr){2-3}\cmidrule(lr){4-6}\cmidrule(lr){7-9}",
        r"Crop & matched & SHEAF & matched & SHEAF & obs "
        r"& matched & SHEAF & obs \\",
        r"\midrule",
    ]
    for crop in ("wheat", "maize", "rice"):
        m = metrics[crop]
        lines.append(
            f"{crop} & {m['corr_matched']:+.2f} & {m['corr_sheaf']:+.2f} & "
            f"$\\times${m['hike07_matched']:.2f} & $\\times${m['hike07_sheaf']:.2f} & "
            f"$\\times${m['hike07_obs']:.2f} & "
            f"$\\times${m['hike10_matched']:.2f} & $\\times${m['hike10_sheaf']:.2f} & "
            f"$\\times${m['hike10_obs']:.2f} \\\\"
        )
    lines += [r"\bottomrule", r"\end{tabular}"]
    (TAB / "price_metrics.tex").write_text("\n".join(lines) + "\n")

    lines = [
        r"% auto-generated",
        r"\begin{tabular}{l cc}",
        r"\toprule",
        r"Crop & Supply-change sign (6 y) & Stock-change sign (5 y) \\",
        r"\midrule",
    ]
    for crop in ("wheat", "maize", "rice"):
        s = signs[crop]
        lines.append(
            f"{crop} & {s['supply_sign']}/{s['supply_n']} & "
            f"{s['stock_sign']}/{s['stock_n']} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    (TAB / "balance_signs.tex").write_text("\n".join(lines) + "\n")


def main():
    _style()
    FIG.mkdir(parents=True, exist_ok=True)
    TAB.mkdir(parents=True, exist_ok=True)
    metrics, signs = {}, {}
    wheat_legs = None
    dates = None
    for crop in ("wheat", "maize", "rice"):
        print(f"=== {crop} ===")
        legs = _run_crop(crop)
        if dates is None:
            dates = _xdates(legs["full_sheaf"])
        obs = _obs_series(crop, dates)
        fig_forcing(crop, legs, dates)
        fig_prices(crop, legs, dates, obs, metrics)
        signs[crop] = fig_global_balance(crop, legs)
        fig_regional_2007(crop, legs)
        if crop == "wheat":
            wheat_legs = legs
    fig_russia_egypt(wheat_legs, dates)
    write_metrics_tex(metrics, signs)
    print("wrote", FIG)
    print("metrics", metrics)
    print("signs", signs)


if __name__ == "__main__":
    main()
