#!/usr/bin/env python3
"""Country-level MY-end stocks and annual consumption vs PSD (Gate 0 P1).

No regional groupings. Each SHEAF node vs its USDA PSD row; Rest-of-World is
world minus named nodes. Official matched split: harvest + AMIS, mean flex,
USA maize industrial on.

Writes diagnostics/gate0_{crop}_country_balance.csv, gate0_{crop}_stocks.csv
(world MY-end with/without China), and figures.
Also prints which calendar month best matches PSD ending-stock *levels*
(rice Dec is a known post-kharif peak).
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from sheaf.calendar24 import STEPS_PER_YEAR
from sheaf.data_usda import load_crop_world, load_psd_country
from sheaf.dynamic_crop import run_crop_dynamics
from sheaf.marketing_years import CROP_MY_END_MONTH, my_end_month

ROOT = Path(__file__).resolve().parents[1]
DIAG = ROOT / "diagnostics"
FIGS = ROOT / "figures"

MY_END_MONTH = CROP_MY_END_MONTH

# FAO/AMIS-style tightness: world stocks that are not sitting in large
# state reserves. China stays a named SHEAF node; these series only *score*
# the traded-market remainder. Rice also drops India (second large reserve).
TIGHTNESS_DROP = {
    "wheat": (("ex_china", ("China",)),),
    "maize": (("ex_china", ("China",)),),
    "rice": (
        ("ex_china", ("China",)),
        ("ex_china_india", ("China", "India")),
    ),
}


def _psd_named_and_row(crop: str, countries: list[str], years: list[int]):
    psd = load_psd_country(crop)
    named = [c for c in countries if c != "RestOfWorld"]
    rows = []
    for y in years:
        sub = psd[psd.year == y]
        named_s = named_c = 0.0
        by_c = {}
        for c in named:
            hit = sub[sub.country == c]
            s = float(hit.ending_stocks.iloc[0]) if len(hit) else 0.0
            cons = float(hit.consumption.iloc[0]) if len(hit) else 0.0
            by_c[c] = (s, cons)
            named_s += s
            named_c += cons
        world_s = float(sub.ending_stocks.sum())
        world_c = float(sub.consumption.sum())
        by_c["RestOfWorld"] = (max(world_s - named_s, 0.0),
                               max(world_c - named_c, 0.0))
        for c, (s, cons) in by_c.items():
            rows.append(dict(year=y, country=c, psd_stock=s, psd_cons=cons))
    return pd.DataFrame(rows)


def country_balance(res, crop: str) -> pd.DataFrame:
    years = list(range(res.start_year, res.end_year + 1))
    psd = _psd_named_and_row(crop, res.countries, years)
    recs = []
    for y in years:
        t0 = (y - res.start_year) * STEPS_PER_YEAR
        t1 = t0 + STEPS_PER_YEAR
        for i, c in enumerate(res.countries):
            my = my_end_month(crop, c)
            t_my = (y - res.start_year) * STEPS_PER_YEAR + (my - 1) * 2 + 1
            recs.append(dict(
                crop=crop, year=y, country=c, my_month=my,
                model_stock=float(res.stock[i, t_my]),
                model_cons=float(res.consumption[i, t0:t1].sum()),
            ))
    out = pd.DataFrame(recs).merge(psd, on=["year", "country"], how="left")
    out["stock_ratio"] = np.where(
        out.psd_stock > 0.5, out.model_stock / out.psd_stock, np.nan)
    out["cons_ratio"] = np.where(
        out.psd_cons > 0.5, out.model_cons / out.psd_cons, np.nan)
    out = out.sort_values(["year", "country"]).reset_index(drop=True)
    # Δstock as % of mean PSD *use* (country tightness). Agrimate Fig. 4e is
    # stock Δ / typical *production* — different units, used in
    # make_agrimate_comparison.fig_global_balance, not here.
    pieces = []
    for c, g in out.groupby("country", sort=False):
        g = g.sort_values("year").copy()
        scale = float(g.psd_cons.mean()) if g.psd_cons.mean() > 0.5 else np.nan
        g["psd_dstock"] = g.psd_stock.diff() / scale * 100.0
        g["model_dstock"] = g.model_stock.diff() / scale * 100.0
        g["psd_dcons"] = g.psd_cons.diff() / scale * 100.0
        g["model_dcons"] = g.model_cons.diff() / scale * 100.0
        pieces.append(g)
    return pd.concat(pieces, ignore_index=True)


def world_consumption(df: pd.DataFrame) -> pd.DataFrame:
    """Calendar-year world use vs country-sum PSD (SHEAF P1, not Agrimate Fig. 4).

    Do not use load_crop_world consumption: that series omits the EU for wheat
    (and maize). Country-sum is the universe the model is built on. Official
    matched is mean flex + isoelastic; year-by-year PSD food/feed is a sensitivity.
    """
    w = (df.groupby("year", as_index=False)[["model_cons", "psd_cons"]]
         .sum()
         .sort_values("year")
         .reset_index(drop=True))
    scale = float(w.psd_cons.mean()) if w.psd_cons.mean() > 0.5 else np.nan
    w["cons_ratio"] = np.where(w.psd_cons > 0.5, w.model_cons / w.psd_cons, np.nan)
    w["model_dcons"] = w.model_cons.diff() / scale * 100.0
    w["psd_dcons"] = w.psd_cons.diff() / scale * 100.0
    w["cons_scale"] = scale
    return w


def consumption_metrics(df: pd.DataFrame) -> dict:
    w = world_consumption(df)
    d = w.dropna(subset=["model_dcons", "psd_dcons"])
    sign = int(sum(
        np.sign(a) == np.sign(b)
        for a, b in zip(d.model_dcons, d.psd_dcons)
        if np.isfinite(a) and np.isfinite(b)))
    a, b = w.model_cons.to_numpy(float), w.psd_cons.to_numpy(float)
    corr = float(np.corrcoef(a, b)[0, 1]) if len(w) >= 3 else float("nan")
    return dict(
        mean_cons_ratio=float(w.model_cons.sum() / w.psd_cons.sum())
        if w.psd_cons.sum() else float("nan"),
        cons_corr=corr,
        dcons_sign=sign,
        dcons_n=int(len(d)),
        cons_scale=float(w.cons_scale.iloc[0]) if len(w) else float("nan"),
    )


def _psd_row(psd: pd.DataFrame, country: str, year: int):
    hit = psd[(psd.country == country) & (psd.year == year)]
    if not len(hit):
        return 0.0, 0.0
    return float(hit.ending_stocks.iloc[0]), float(hit.consumption.iloc[0])


def world_my_end_stocks(res, crop: str) -> pd.DataFrame:
    """World MY-end stocks vs PSD, including FAO-style without-China tightness.

    World comparison month is the crop default (`CROP_MY_END_MONTH`), same as
    the existing Gate 0 world bar. Dropped nodes are subtracted at that same
    month on the model side and at local USDA MY-end on the PSD side — the
    USDA/AMIS convention, not a warehouse rewrite.
    """
    years = list(range(res.start_year, res.end_year + 1))
    my_month = CROP_MY_END_MONTH[crop]
    psd = load_psd_country(crop)
    world = load_crop_world(crop)
    idx = {c: i for i, c in enumerate(res.countries)}
    drops = TIGHTNESS_DROP[crop]
    rows = []
    for y in years:
        t_dec = (y - res.start_year + 1) * STEPS_PER_YEAR - 1
        t_my = (y - res.start_year) * STEPS_PER_YEAR + (my_month - 1) * 2 + 1
        sub = psd[psd.year == y]
        psd_s = float(sub.ending_stocks.sum())
        cons = float(world.loc[y, "consumption"]) if y in world.index else float(
            sub.consumption.sum())
        model_dec = float(res.stock[:, t_dec].sum())
        model_my = float(res.stock[:, t_my].sum())
        row = dict(
            year=y,
            my_month=my_month,
            model_ending_stock=model_dec,
            model_my_end_stock=model_my,
            psd_ending_stocks=psd_s,
            psd_consumption=cons,
            psd_stu=psd_s / cons if cons else float("nan"),
            model_stu=model_dec / cons if cons else float("nan"),
            model_my_stu=model_my / cons if cons else float("nan"),
        )
        for key, nodes in drops:
            m_drop = 0.0
            p_drop_s = 0.0
            p_drop_c = 0.0
            for name in nodes:
                i = idx.get(name)
                if i is not None:
                    m_drop += float(res.stock[i, t_my])
                s, c = _psd_row(psd, name, y)
                p_drop_s += s
                p_drop_c += c
            m_ex = model_my - m_drop
            p_ex = psd_s - p_drop_s
            c_ex = cons - p_drop_c
            row[f"model_my_end_{key}"] = m_ex
            row[f"psd_ending_{key}"] = p_ex
            row[f"psd_consumption_{key}"] = c_ex
            row[f"model_my_stu_{key}"] = m_ex / c_ex if c_ex else float("nan")
            row[f"psd_stu_{key}"] = p_ex / c_ex if c_ex else float("nan")
            if key == "ex_china":
                row["china_model_stock"] = m_drop if nodes == ("China",) else float("nan")
                row["china_psd_stock"] = p_drop_s if nodes == ("China",) else float("nan")
                row["china_psd_share"] = (
                    p_drop_s / psd_s if psd_s and nodes == ("China",) else float("nan"))
        rows.append(row)
    return pd.DataFrame(rows)


def tightness_metrics(df: pd.DataFrame) -> dict:
    """Mean model/PSD ratios for world-including and dropped-node series."""
    out = dict(
        mean_ratio_world=float(
            (df.model_my_end_stock / df.psd_ending_stocks).mean()),
        china_psd_share=float(df.china_psd_share.mean())
        if "china_psd_share" in df.columns else float("nan"),
    )
    if "model_my_end_ex_china" in df.columns:
        out["mean_ratio_ex_china"] = float(
            (df.model_my_end_ex_china / df.psd_ending_ex_china).mean())
    if "model_my_end_ex_china_india" in df.columns:
        out["mean_ratio_ex_china_india"] = float(
            (df.model_my_end_ex_china_india / df.psd_ending_ex_china_india).mean())
    return out


def _fig_world_tightness(crop: str, df: pd.DataFrame, path: Path) -> None:
    """FAO with/without-China world MY-end stocks (annual bars)."""
    years = [int(y) for y in df.year]
    x = np.arange(len(years))
    w = 0.35
    n_panel = 2 if crop != "rice" else 3
    fig, axes = plt.subplots(1, n_panel, figsize=(3.6 * n_panel, 3.2), sharey=False)

    def _bars(ax, psd, model, title):
        ax.bar(x - w / 2, psd, w, color="#1f4e79", label="PSD")
        ax.bar(x + w / 2, model, w, color="#e67e22", label="model")
        ax.set_xticks(x, years, rotation=45)
        ax.set_title(title)
        ax.set_ylabel("MMT")
        ax.legend(frameon=False, loc="upper left", fontsize=8)

    _bars(axes[0], df.psd_ending_stocks, df.model_my_end_stock,
          f"{crop.capitalize()} world MY-end")
    _bars(axes[1], df.psd_ending_ex_china, df.model_my_end_ex_china,
          "excluding China")
    if n_panel == 3:
        _bars(axes[2], df.psd_ending_ex_china_india, df.model_my_end_ex_china_india,
              "excluding China + India")
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def month_scan(res, crop: str) -> pd.DataFrame:
    """Which calendar month's world stocks best match PSD ending-stock levels."""
    years = list(range(res.start_year, res.end_year + 1))
    psd = _psd_named_and_row(crop, res.countries, years)
    world = (psd.groupby("year")["psd_stock"].sum())
    rows = []
    for month in range(1, 13):
        mod = []
        obs = []
        for y in years:
            t = (y - res.start_year) * STEPS_PER_YEAR + (month - 1) * 2 + 1
            mod.append(float(res.stock[:, t].sum()))
            obs.append(float(world.loc[y]))
        a, b = np.asarray(mod), np.asarray(obs)
        ratio = float((a / np.maximum(b, 1e-9)).mean())
        corr = float(np.corrcoef(a, b)[0, 1]) if len(a) >= 3 else float("nan")
        rows.append(dict(crop=crop, month=month, mean_ratio=ratio, corr=corr,
                         abs_log_ratio=abs(np.log(max(ratio, 1e-9)))))
    return pd.DataFrame(rows)


def _metrics(df: pd.DataFrame) -> dict:
    big = df[df.psd_stock > 1.0]
    d = df[df.year > df.year.min()]
    sign = sum(
        np.sign(a) == np.sign(b)
        for a, b in zip(d.psd_dstock, d.model_dstock)
        if np.isfinite(a) and np.isfinite(b) and abs(a) + abs(b) > 0.5)
    n_sign = sum(
        np.isfinite(a) and np.isfinite(b) and abs(a) + abs(b) > 0.5
        for a, b in zip(d.psd_dstock, d.model_dstock))
    return dict(
        n_country_years=int(len(big)),
        median_stock_ratio=float(big.stock_ratio.median()) if len(big) else float("nan"),
        mean_stock_ratio=float(big.stock_ratio.mean()) if len(big) else float("nan"),
        median_cons_ratio=float(df[df.psd_cons > 1].cons_ratio.median()),
        dstock_sign=int(sign),
        dstock_n=int(n_sign),
        **consumption_metrics(df),
    )


def _fig(crop: str, df: pd.DataFrame, path: Path) -> None:
    years = sorted(df.year.unique())
    # Focus on countries with material PSD stocks
    keep = (df.groupby("country")["psd_stock"].mean() > 2.0)
    countries = [c for c, ok in keep.items() if ok]
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 0.42 * max(len(countries), 6) + 1.6),
                             sharey=True)
    yx = np.arange(len(countries))
    # Last crisis year in window for a readable snapshot, plus mean ratio
    y_show = 2008 if 2008 in years else years[-1]
    snap = df[df.year == y_show].set_index("country")
    ax = axes[0]
    ax.barh(yx + 0.18, [snap.loc[c, "psd_stock"] for c in countries], 0.35,
            color="#1f4e79", label="PSD MY-end")
    ax.barh(yx - 0.18, [snap.loc[c, "model_stock"] for c in countries], 0.35,
            color="#e67e22", label="model MY-end")
    ax.set_yticks(yx, countries)
    ax.invert_yaxis()
    ax.set_xlabel("MMT")
    ax.set_title(f"{crop.capitalize()} MY-end stocks, {y_show}")
    ax.legend(frameon=False, loc="lower right")

    ax = axes[1]
    d07 = df[df.year == 2007].set_index("country")
    ax.barh(yx + 0.18, [d07.loc[c, "psd_dstock"] if c in d07.index else np.nan
                        for c in countries], 0.35, color="#1f4e79", label="PSD Δ")
    ax.barh(yx - 0.18, [d07.loc[c, "model_dstock"] if c in d07.index else np.nan
                        for c in countries], 0.35, color="#e67e22", label="model Δ")
    ax.axvline(0, color="0.6", lw=0.6)
    ax.set_xlabel("2007 Δ stocks / mean use (%)")
    ax.set_title("2007 stock change (country, not groupings)")
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def _fig_world_consumption(crop: str, df: pd.DataFrame, path: Path) -> None:
    """World calendar-year use vs country-sum PSD (P1, not Agrimate Fig. 4)."""
    w = world_consumption(df)
    years = [int(y) for y in w.year]
    x = np.arange(len(years))
    bw = 0.35
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.2))
    ax = axes[0]
    ax.bar(x - bw / 2, w.psd_cons, bw, color="#1f4e79", label="PSD country-sum")
    ax.bar(x + bw / 2, w.model_cons, bw, color="#e67e22", label="model")
    ax.set_xticks(x, years, rotation=45)
    ax.set_ylabel("MMT")
    ax.set_title(f"{crop.capitalize()} world consumption (calendar year)")
    ax.legend(frameon=False, loc="upper left", fontsize=8)

    ax = axes[1]
    ax.bar(x - bw / 2, w.psd_dcons, bw, color="#1f4e79", label="PSD Δ")
    ax.bar(x + bw / 2, w.model_dcons, bw, color="#e67e22", label="model Δ")
    ax.axhline(0, color="0.6", lw=0.6)
    ax.set_xticks(x, years, rotation=45)
    ax.set_ylabel("% of 2006–11 mean PSD use")
    ax.set_title("World Δ consumption")
    ax.legend(frameon=False, loc="upper left", fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--crop", choices=("wheat", "maize", "rice", "all"),
                    default="all")
    ap.add_argument("--start", type=int, default=2006)
    ap.add_argument("--end", type=int, default=2011)
    args = ap.parse_args()
    crops = (("wheat", "maize", "rice") if args.crop == "all"
             else (args.crop,))
    DIAG.mkdir(parents=True, exist_ok=True)
    FIGS.mkdir(parents=True, exist_ok=True)

    summaries = []
    for crop in crops:
        print(f"running {crop} official matched…")
        res = run_crop_dynamics(
            crop, start_year=args.start, end_year=args.end,
            use_amis=True, use_shocks=True, use_demand=False)
        df = country_balance(res, crop)
        csv_path = DIAG / f"gate0_{crop}_country_balance.csv"
        df.to_csv(csv_path, index=False)
        scan = month_scan(res, crop)
        scan_path = DIAG / f"gate0_{crop}_stock_month_scan.csv"
        scan.to_csv(scan_path, index=False)
        met = _metrics(df)
        world = world_my_end_stocks(res, crop)
        world.to_csv(DIAG / f"gate0_{crop}_stocks.csv", index=False)
        tmet = tightness_metrics(world)
        tfig = FIGS / f"fig_gate0_{crop}_world_exchina.png"
        _fig_world_tightness(crop, world, tfig)
        best = scan.loc[scan.abs_log_ratio.idxmin()]
        print(f"  median model/PSD stock (psd>1 MMT): {met['median_stock_ratio']:.2f}")
        print(f"  median model/PSD cons:              {met['median_cons_ratio']:.2f}")
        print(f"  Δstock sign {met['dstock_sign']}/{met['dstock_n']}")
        print(f"  world cons ×{met['mean_cons_ratio']:.2f}; "
              f"corr {met['cons_corr']:+.2f}; "
              f"Δcons sign {met['dcons_sign']}/{met['dcons_n']}")
        print(f"  MY-end world ×{tmet['mean_ratio_world']:.2f}; "
              f"ex-China ×{tmet['mean_ratio_ex_china']:.2f} "
              f"(China {tmet['china_psd_share']:.0%} of PSD world)")
        if "mean_ratio_ex_china_india" in tmet:
            print(f"  ex-China+India ×{tmet['mean_ratio_ex_china_india']:.2f}")
        print(f"  MY-end month used: {MY_END_MONTH[crop]}; "
              f"closest level month={int(best['month'])} "
              f"(ratio {best['mean_ratio']:.2f}, corr {best['corr']:+.2f})")
        fig_path = FIGS / f"fig_gate0_{crop}_country_stocks.png"
        _fig(crop, df, fig_path)
        cons = world_consumption(df)
        cons_path = DIAG / f"gate0_{crop}_consumption.csv"
        cons.to_csv(cons_path, index=False)
        cfig = FIGS / f"fig_gate0_{crop}_world_consumption.png"
        _fig_world_consumption(crop, df, cfig)
        print(f"  wrote {csv_path.name}, {fig_path.name}, {tfig.name}, {cfig.name}")
        summaries.append(dict(crop=crop, **met, **tmet,
                              my_month=MY_END_MONTH[crop],
                              best_month=int(best["month"]),
                              best_ratio=float(best["mean_ratio"]),
                              best_corr=float(best["corr"])))
    pd.DataFrame(summaries).to_csv(DIAG / "gate0_country_balance_summary.csv",
                                   index=False)


if __name__ == "__main__":
    main()
