"""G0-H 2006–11 hindcast score (P8). Note, not a retune.

Reads existing ``diagnostics/gate0_agrimate/`` three-scenario CSVs and
the P7 author Fig. 4 extracts. Does not run the model and does not
change ``wheat_params()``.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from sheaf.agrimate.fig4 import AUTHOR_DIR, load_author_fig4
from sheaf.agrimate.validation import (
    OUT_DEFAULT,
    SCENARIO_ORDER,
    _corr,
    _hike,
    load_usda_world_wheat,
)

SCORE_START = 2006
SCORE_END = 2011


def _fmt(x, nd: int = 2) -> str:
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "nan"
    if isinstance(x, (int, np.integer)):
        return str(int(x))
    return f"{float(x):.{nd}f}"


def load_host_prices(out_dir: Path) -> pd.DataFrame:
    raw = pd.read_csv(out_dir / "prices_three_scenarios.csv", index_col=0)
    raw.index = pd.PeriodIndex(raw.index, freq="M")
    return raw


def _window(s: pd.Series, start: int = SCORE_START, end: int = SCORE_END) -> pd.Series:
    return s[(s.index.year >= start) & (s.index.year <= end)]


def month_of_year_profile(s: pd.Series) -> pd.Series:
    s = _window(s)
    return s.groupby(s.index.month).mean()


def peak_period(s: pd.Series, y0: int, y1: int) -> pd.Period:
    w = s[(s.index.year >= y0) & (s.index.year <= y1)]
    return w.idxmax()


def score_seasonal_paths(
    prices: pd.DataFrame,
    author_monthly: pd.DataFrame,
    start: int = SCORE_START,
    end: int = SCORE_END,
) -> pd.DataFrame:
    """Path metrics: month-of-year shape, not only full-window correlation."""
    pink = _window(prices["pink_usd"], start, end)
    pink_m = month_of_year_profile(pink)
    rows = []
    for name in SCENARIO_ORDER:
        host = _window(prices[name], start, end)
        auth = author_monthly[author_monthly["scenario"] == name]
        auth_s = pd.Series(
            auth["wm_price_index"].to_numpy(float),
            index=pd.PeriodIndex(
                [pd.Period(year=int(y), month=int(m), freq="M")
                 for y, m in zip(auth["year"], auth["month"])],
                freq="M",
            ),
        )
        auth_s = _window(auth_s, start, end)
        host_m = month_of_year_profile(host)
        auth_m = month_of_year_profile(auth_s)
        h06 = float(host[host.index.year == start].mean())
        p06 = float(pink[pink.index.year == start].mean())
        a06 = float(auth_s[auth_s.index.year == start].mean())
        # year-demeaned path (seasonal residual)
        years = host.index.year.to_numpy()
        hd = host.to_numpy(float).copy()
        pd_ = pink.to_numpy(float).copy()
        for y in range(start, end + 1):
            m = years == y
            hd[m] -= hd[m].mean()
            pd_[m] -= pd_[m].mean()
        crisis = peak_period(host, 2007, 2008)
        crisis_p = peak_period(pink, 2007, 2008)
        crisis_a = peak_period(auth_s, 2007, 2008)
        rows.append({
            "scenario": name,
            "corr_vs_pink": _corr(host, pink),
            "corr_year_demeaned_vs_pink": _corr(hd, pd_),
            "moy_corr_vs_pink": _corr(host_m, pink_m),
            "moy_corr_vs_author": _corr(host_m, auth_m),
            "moy_maxmin_host": float(host_m.max() / host_m.min())
            if float(host_m.min()) else float("nan"),
            "moy_maxmin_pink": float(pink_m.max() / pink_m.min()),
            "moy_maxmin_author": float(auth_m.max() / auth_m.min())
            if float(auth_m.min()) else float("nan"),
            "moy_peak_month_host": int(host_m.idxmax()),
            "moy_trough_month_host": int(host_m.idxmin()),
            "moy_peak_month_pink": int(pink_m.idxmax()),
            "moy_peak_month_author": int(auth_m.idxmax()),
            "hike_2008_host": _hike(host, start, 2008),
            "hike_2008_pink": _hike(pink, start, 2008),
            "hike_2008_author": _hike(auth_s, start, 2008),
            "mean_2006_host_usd": h06,
            "mean_2006_pink_usd": p06,
            "mean_2006_author_index": a06,
            "level_vs_pink": h06 / p06 if p06 else float("nan"),
            "crisis_peak_host": str(crisis),
            "crisis_peak_pink": str(crisis_p),
            "crisis_peak_author": str(crisis_a),
            "sep2007_host_usd": float(host.loc[pd.Period("2007-09")])
            if pd.Period("2007-09") in host.index else float("nan"),
            "sep2007_pink_usd": float(pink.loc[pd.Period("2007-09")])
            if pd.Period("2007-09") in pink.index else float("nan"),
        })
    return pd.DataFrame(rows)


def score_quantity_anomalies(
    out_dir: Path,
    start: int = SCORE_START,
    end: int = SCORE_END,
) -> pd.DataFrame:
    usda = load_usda_world_wheat()
    usda = usda[(usda["year"] >= start) & (usda["year"] <= end)].set_index("year")
    rows = []
    for name in SCENARIO_ORDER:
        ann = pd.read_csv(out_dir / f"annual_{name}.csv")
        ann = ann[(ann["year"] >= start) & (ann["year"] <= end)].set_index("year")
        for field in ("production", "consumption", "ending_stocks"):
            m, o = ann[field], usda[field]
            with np.errstate(invalid="ignore"):
                corr_level = _corr(m, o)
                corr_anom = _corr(m - m.mean(), o - o.mean())
            rows.append({
                "scenario": name,
                "field": field,
                "corr_level": corr_level,
                "corr_anomaly": corr_anom,
                "mean_host": float(m.mean()),
                "mean_usda": float(o.mean()),
                "level_ratio": float(m.mean() / o.mean()) if float(o.mean()) else float("nan"),
            })
    return pd.DataFrame(rows)


def harvest_vs_amis_attribution(prices: pd.DataFrame) -> dict[str, float | str]:
    h = _window(prices["harvest"])
    a = _window(prices["harvest_amis"])
    d = (a - h).abs()
    return {
        "mean_abs_delta_usd": float(d.mean()),
        "max_abs_delta_usd": float(d.max()),
        "max_abs_delta_at": str(d.idxmax()),
        "mean_2007_harvest": float(h[h.index.year == 2007].mean()),
        "mean_2007_amis": float(a[a.index.year == 2007].mean()),
        "mean_2008_harvest": float(h[h.index.year == 2008].mean()),
        "mean_2008_amis": float(a[a.index.year == 2008].mean()),
        "jun2007_harvest": float(h.loc[pd.Period("2007-06")]),
        "jun2007_amis": float(a.loc[pd.Period("2007-06")]),
        "may2008_harvest": float(h.loc[pd.Period("2008-05")]),
        "may2008_amis": float(a.loc[pd.Period("2008-05")]),
    }


def write_seasonal_figure(
    prices: pd.DataFrame,
    author_monthly: pd.DataFrame,
    out_path: Path,
    start: int = SCORE_START,
    end: int = SCORE_END,
) -> Path:
    import matplotlib.pyplot as plt

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pink = month_of_year_profile(_window(prices["pink_usd"], start, end))
    fig, ax = plt.subplots(figsize=(8.5, 4.4))
    months = np.arange(1, 13)
    ax.plot(months, pink / pink.mean(), color="0.35", lw=2.0, label="Pink Sheet")
    colors = {"undisturbed": "#4c78a8", "harvest": "#f58518", "harvest_amis": "#e45756"}
    for name in SCENARIO_ORDER:
        h = month_of_year_profile(_window(prices[name], start, end))
        ax.plot(months, h / h.mean(), color=colors[name], lw=1.6, label=f"host {name}")
        auth = author_monthly[author_monthly["scenario"] == name]
        a = pd.Series(
            auth["wm_price_index"].to_numpy(float),
            index=pd.PeriodIndex(
                [pd.Period(year=int(y), month=int(m), freq="M")
                 for y, m in zip(auth["year"], auth["month"])],
                freq="M",
            ),
        )
        am = month_of_year_profile(_window(a, start, end))
        ax.plot(months, am / am.mean(), color=colors[name], lw=1.4, ls="--",
                label=f"author {name}")
    ax.set_xticks(months)
    ax.set_xlabel("month")
    ax.set_ylabel("month-of-year mean / series mean")
    ax.set_title("Seasonal path (2006–11): host vs Pink Sheet vs Agrimate Fig. 4")
    ax.legend(ncol=2, fontsize=8)
    ax.axhline(1.0, color="0.7", lw=0.8, ls=":")
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return out_path


def write_hindcast_note(
    seasonal: pd.DataFrame,
    qty: pd.DataFrame,
    attrib: dict[str, float | str],
    out_dir: Path,
) -> Path:
    """Honest G0-H score. Comparable to Agrimate, or an explicit sourced shortfall."""
    ha = seasonal[seasonal["scenario"] == "harvest_amis"].iloc[0]
    hv = seasonal[seasonal["scenario"] == "harvest"].iloc[0]
    un = seasonal[seasonal["scenario"] == "undisturbed"].iloc[0]
    prod = qty[(qty["scenario"] == "harvest_amis") & (qty["field"] == "production")].iloc[0]
    stk = qty[(qty["scenario"] == "harvest_amis") & (qty["field"] == "ending_stocks")].iloc[0]
    stk_h = qty[(qty["scenario"] == "harvest") & (qty["field"] == "ending_stocks")].iloc[0]
    cons = qty[(qty["scenario"] == "harvest_amis") & (qty["field"] == "consumption")].iloc[0]

    lines = [
        "# G0-H — 2006–11 wheat hindcast (P8)",
        "",
        "**Explicit sourced shortfall versus Agrimate Fig. 4.** Independent",
        "implementation, not a replication. Not a retune. `wheat_params()`",
        "stay αI=3.2, p_sto=0.1, xmin=0.2. Bai α_foreign=10 is listed in the",
        "P6 OAT and **not adopted** (it raises the already-too-large spike).",
        "L1–L8 stay rejected. G1/G2 stay blocked.",
        "",
        "Numbers are from `diagnostics/gate0_agrimate/` three-scenario CSVs",
        "(spin-up 2003–05, score 2006–11) and P7 author series. The runner",
        "was not re-run.",
        "",
        "## G0-U items 1–3 (pass rule before judging historical fit)",
        "",
        "1. **Source fidelity.** Met for retrieved Zenodo 14022004 code with",
        "   labelled S3/S4/A1–A6/N5. Fig. 4 NetCDF is a different executable",
        "   (AgrimateEU28+Egypt, FAO anomalies, α_foreign=3.5, ζ=1, N_for=6).",
        "2. **Numerical reliability.** Feasible (failed/fallback 0, residual 0)",
        "   but **not** first-order stationary: harvest+AMIS unconverged",
        "   1743/5832 (N5). Counted, not papered over.",
        "3. **Undisturbed dynamics.** Seasonal *shape* repeats (corr 0.98) but",
        "   the annual-mean world-price ratio 2011/2006 is **1.63**. Author",
        "   Fig. 4 baseline on the same window is 1.004. P2 drift is",
        "   unexplained. Not a price pin.",
        "",
        "Items 1–3 do **not** all hold. Item 5 is still reported, as an",
        "explicit shortfall, not as a replication claim.",
        "",
        "## Quiet-year (2006) price level",
        "",
        f"Harvest+AMIS 2006 mean is **${_fmt(ha['mean_2006_host_usd'], 1)}/t** vs Pink",
        f"Sheet **${_fmt(ha['mean_2006_pink_usd'], 1)}/t** (ratio",
        f"{_fmt(ha['level_vs_pink'], 2)}; about 31% of the observed quiet-year",
        "level). Undisturbed is lower still",
        f"(${_fmt(un['mean_2006_host_usd'], 1)}/t) because 2006 is a trough on",
        "the drifting unforced path, not a calibrated intercept.",
        "",
        "Against Agrimate Fig. 4d the same year is host D.7 index",
        f"**{_fmt(ha['mean_2006_host_usd'] / ha['mean_2006_pink_usd'], 3)}**",
        f"(USD/p0) vs author volume-weighted index **{_fmt(ha['mean_2006_author_index'], 3)}**.",
        "The host is not on Agrimate's quiet-year scale. Do not pin p_w to the",
        "2006 Pink mean to close this (hard stop).",
        "",
        "## 2007/08 hike ratio",
        "",
        "Same `_hike` helper as `score_prices.csv` (3-month rolling peak in",
        "2006–08 over 2006 mean):",
        "",
        "| series | 2008 hike | 2006 mean | 2007–08 peak month |",
        "|---|---:|---:|---|",
        f"| host harvest+AMIS | ×{_fmt(ha['hike_2008_host'], 2)} | ${_fmt(ha['mean_2006_host_usd'], 1)} | {ha['crisis_peak_host']} |",
        f"| host harvest-only | ×{_fmt(hv['hike_2008_host'], 2)} | ${_fmt(hv['mean_2006_host_usd'], 1)} | {hv['crisis_peak_host']} |",
        f"| Pink Sheet | ×{_fmt(ha['hike_2008_pink'], 2)} | ${_fmt(ha['mean_2006_pink_usd'], 1)} | {ha['crisis_peak_pink']} |",
        f"| Agrimate Fig. 4d harvest+AMIS | ×{_fmt(ha['hike_2008_author'], 2)} | index {_fmt(ha['mean_2006_author_index'], 3)} | {ha['crisis_peak_author']} |",
        "",
        "Host overshoots Pink (×4.54 vs ×1.88) **and** overshoots Agrimate",
        "(×4.54 vs ×1.62). Peak timing is also wrong: host crisis peak is",
        f"**{ha['crisis_peak_host']}** (harvest-calendar spike); Pink peaks",
        f"**{ha['crisis_peak_pink']}**; author Fig. 4d peaks **{ha['crisis_peak_author']}**.",
        "Bai α_foreign=10 is not a remedy: the P6 short-window OAT moves the",
        "2008 hike from ×2.31 to ×3.58 and blows `pidx_max` to 473. That is",
        "the wrong direction. Not adopted.",
        "",
        "## Seasonal path, not only correlation",
        "",
        "Full-window corr vs Pink is **negative** (harvest+AMIS −0.082).",
        "That is a path failure, not a noisy +0.5. Year-demeaned corr is",
        f"still negative ({_fmt(ha['corr_year_demeaned_vs_pink'], 3)}).",
        "",
        "Month-of-year mean profile (2006–11):",
        "",
        "| series | peak month | trough month | max/min | moy corr vs Pink | moy corr vs author |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for _, r in seasonal.iterrows():
        lines.append(
            f"| host {r['scenario']} | {int(r['moy_peak_month_host'])} | "
            f"{int(r['moy_trough_month_host'])} | {_fmt(r['moy_maxmin_host'], 2)} | "
            f"{_fmt(r['moy_corr_vs_pink'], 3)} | {_fmt(r['moy_corr_vs_author'], 3)} |"
        )
    lines += [
        f"| Pink Sheet | {int(ha['moy_peak_month_pink'])} | — | "
        f"{_fmt(ha['moy_maxmin_pink'], 2)} | 1 | — |",
        f"| Agrimate Fig. 4d (harvest+AMIS) | {int(ha['moy_peak_month_author'])} | — | "
        f"{_fmt(ha['moy_maxmin_author'], 2)} | — | 1 |",
        "",
        "Host within-year amplitude is **~18×** on the month-of-year mean",
        f"({_fmt(ha['moy_maxmin_host'], 1)}), versus Pink **{_fmt(ha['moy_maxmin_pink'], 2)}×**",
        f"and Agrimate Fig. 4d **{_fmt(ha['moy_maxmin_author'], 2)}×**. The host",
        "shares Agrimate's northern-harvest *calendar* (May–June peak; moy",
        f"corr vs author {_fmt(ha['moy_corr_vs_author'], 2)}) and inverts Pink",
        f"(moy corr {_fmt(ha['moy_corr_vs_pink'], 2)}). September 2007 is the",
        "clearest single-month counterexample: host harvest+AMIS",
        f"**${_fmt(ha['sep2007_host_usd'], 1)}/t** vs Pink **${_fmt(ha['sep2007_pink_usd'], 0)}/t**.",
        "Agrimate's published wheat path does not collapse off-season like",
        "that. Correlation alone would hide this.",
        "",
        "Figure: `figures/fig6_hindcast_seasonal.png`.",
        "",
        "## Production anomalies vs USDA",
        "",
        f"Harvest / harvest+AMIS production corr vs USDA world is",
        f"**{_fmt(prod['corr_level'], 3)}** (prompt ballpark +0.80). Anomaly",
        f"corr on this six-year window is the same number ({_fmt(prod['corr_anomaly'], 3)}):",
        "the series are short and the mean offset is nearly constant.",
        f"Level is close: host {_fmt(prod['mean_host'], 1)} MMT vs USDA",
        f"{_fmt(prod['mean_usda'], 1)} (ratio {_fmt(prod['level_ratio'], 3)}).",
        "Undisturbed production is the repeating 2007–09 mean, so corr vs",
        "USDA is undefined/zero — as designed.",
        "",
        "Vs Agrimate Fig. 4 harvest, production corr is 0.986 at different",
        "levels (host 542 vs author 624 MMT) because A1 is USDA PSD, not",
        "FAOSTAT Food Balances, and the region lists differ (Brazil named",
        "here; Egypt split there).",
        "",
        "## Stock *level* bias vs stock *anomaly* corr",
        "",
        "The P8 prompt's “~3× USDA world / anomaly corr ~+0.94” is the",
        "**pre-P2** echo-bug number (exporter consumer stocks ate XI).",
        "After B1 (T* delivery), harvest+AMIS ending stocks are",
        f"**{_fmt(stk['mean_host'], 1)} MMT vs USDA {_fmt(stk['mean_usda'], 1)} "
        f"= {_fmt(stk['level_ratio'], 2)}×**, not 3×. Level corr",
        f"**{_fmt(stk['corr_level'], 3)}**; anomaly corr",
        f"**{_fmt(stk['corr_anomaly'], 3)}** (again equal on this window).",
        f"Harvest-only is {_fmt(stk_h['level_ratio'], 2)}× with corr",
        f"{_fmt(stk_h['corr_level'], 3)}.",
        "",
        "Against Agrimate Fig. 4 the host is *below* author stocks (248 vs",
        "325 MMT harvest+AMIS), so the remaining USDA gap is not “the host",
        "holds three worlds of grain.” Coverage (27 nodes vs world PSD) and",
        "A1 still explain part of the level offset. Do not fit xmin or p_sto",
        "to close it.",
        "",
        f"Consumption corr vs USDA is weak ({_fmt(cons['corr_level'], 3)});",
        "mean level is close (ratio",
        f"{_fmt(cons['level_ratio'], 3)}).",
        "",
        "## Harvest-only vs harvest+AMIS attribution",
        "",
        "Production is identical by construction. AMIS wheat Δ binds 491",
        "region-steps (Argentina, China, India, Kazakhstan, Russia, Ukraine,",
        "Northern Africa; max 0.95). The two price paths are **not** identical.",
        "",
        f"- 2007 means are almost the same (${_fmt(attrib['mean_2007_harvest'], 1)} vs",
        f"  ${_fmt(attrib['mean_2007_amis'], 1)}). June 2007 is",
        f"  ${_fmt(attrib['jun2007_harvest'], 0)} harvest-only vs",
        f"  ${_fmt(attrib['jun2007_amis'], 0)} harvest+AMIS. The 2007 spike is",
        "  **harvest-driven**.",
        f"- 2008 means diverge (${_fmt(attrib['mean_2008_harvest'], 1)} vs",
        f"  ${_fmt(attrib['mean_2008_amis'], 1)}). May 2008 is",
        f"  ${_fmt(attrib['may2008_harvest'], 0)} vs ${_fmt(attrib['may2008_amis'], 0)}",
        f"  (max |Δ| ${_fmt(attrib['max_abs_delta_usd'], 0)} at",
        f"  {attrib['max_abs_delta_at']}). AMIS **adds** a 2008 spring spike",
        "  on top of an already-too-large 2007 harvest spike.",
        "- Ukraine 2007 exports 15.0 → 6.0 MMT with AMIS; 2007 consumption",
        "  1.93 → 10.3 MMT. The restriction does what E.4 says on the",
        "  exporter. It does not repair world-price *path* or *level*.",
        "",
        "Mean |price harvest+AMIS − harvest| over 2006–11 is",
        f"${_fmt(attrib['mean_abs_delta_usd'], 1)}/t.",
        "",
        "## Comparison to Agrimate published wheat Fig. 4",
        "",
        "P7 unpacked Zenodo 10688435. Headlines from `fig4.md`, restated as",
        "a hindcast verdict:",
        "",
        "- Quiet-year index: host ~0.31 vs author ~1.18.",
        "- 2008 hike: host ×4.54 vs author ×1.62 vs Pink ×1.88. Agrimate is",
        "  the closer of the two models to Pink on this metric; the host is",
        "  not comparable to Agrimate.",
        "- Seasonal amplitude: host ~18× vs author ~1.45× vs Pink ~1.07×.",
        "  Host matches Agrimate's *calendar* (moy corr 0.91) and misses",
        "  Agrimate's *amplitude*.",
        "- Undisturbed: author last/first 1.004; host 1.63 (P2).",
        "- Production anomalies track (corr 0.99) at USDA vs FAO levels.",
        "- This is **not** a bit-reproduction: different region list, FAO vs",
        "  USDA (A1), α_foreign 3.5 vs 3.2, ζ=1 vs 0, N_for 6 vs 3 months,",
        "  git `old-demand-dynamics` vs 14022004. Labelling that mismatch",
        "  does not make the host's ×4.54 hike a success.",
        "",
        "## Verdict",
        "",
        "Sourced shortfall. Gate 0 wheat is **not** at the publication bar",
        "on historical performance (DEVELOPMENT item 5) and still fails",
        "item 3 (undisturbed). Do not restore L1–L8. Do not adopt Bai",
        "α_foreign=10. Do not pin 2006. Next: P9 regional USDA tables",
        "(coverage, not a fit). P12 methods note waits on an accepted G0-H",
        "picture; this note is that picture.",
        "",
        "## Files",
        "",
        "- `score_hindcast_seasonal.csv` — path metrics used above",
        "- `score_hindcast_quantities.csv` — USDA level vs anomaly",
        "- `figures/fig6_hindcast_seasonal.png`",
        "- `fig4.md` — P7 author-series score (unchanged)",
        "",
    ]
    path = Path(out_dir) / "hindcast.md"
    path.write_text("\n".join(lines) + "\n")
    return path


def run_hindcast_score(out_dir: Path | None = None) -> dict[str, Path]:
    out_dir = Path(out_dir) if out_dir else OUT_DEFAULT
    prices = load_host_prices(out_dir)
    author = load_author_fig4(AUTHOR_DIR)
    seasonal = score_seasonal_paths(prices, author["monthly"])
    qty = score_quantity_anomalies(out_dir)
    attrib = harvest_vs_amis_attribution(prices)
    seasonal.to_csv(out_dir / "score_hindcast_seasonal.csv", index=False)
    qty.to_csv(out_dir / "score_hindcast_quantities.csv", index=False)
    fig = write_seasonal_figure(
        prices, author["monthly"],
        out_dir / "figures" / "fig6_hindcast_seasonal.png",
    )
    note = write_hindcast_note(seasonal, qty, attrib, out_dir)
    return {"note": note, "figure": fig}
