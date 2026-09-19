"""Agrimate Fig. 4 author series (Zenodo 10688435) vs this host.

The published wheat experiments live in ``main_output/data/*.nc`` of
record 10688435 (Kuhla 2024, CC-BY-4.0). World-market price follows
author ``plot_wm_price_timeseries``: volume-weighted international
(non-domestic) transaction price. Quantities are nansum'd over the 27
AgrimateEU28+Egypt nodes and converted 1000 t → MMT.

This is a comparison, not a replication: the NetCDF global attributes
are a different executable than Zenodo 14022004 ``AgrimateParams``
(see ``diagnostics/gate0_agrimate/fig4.md``). Do not retune αI / p_sto /
xmin / λ to close the gap.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from sheaf.agrimate.validation import SCENARIO_ORDER, _corr, _hike, _rmse

ROOT = Path(__file__).resolve().parents[2]
OUT_DEFAULT = ROOT / "diagnostics" / "gate0_agrimate"
AUTHOR_DIR = OUT_DEFAULT / "author_fig4"

# Host three-scenario names ← author main_output filenames.
AUTHOR_SCENARIO_FILES = {
    "undisturbed": (
        "agrimate_baseline=2007-2009_extra_regions=(Egypt=EGY)"
        "_regions=AgrimateEU28_start=2000-01-01.nc"
    ),
    "harvest": (
        "agrimate_baseline=2007-2009_extra_regions=(Egypt=EGY)"
        "_production_anomalies=FAOsince-2005_regions=AgrimateEU28"
        "_start=2000-01-01.nc"
    ),
    "harvest_amis": (
        "agrimate_baseline=2007-2009_export_restrictions=2007-2011"
        "_extra_regions=(Egypt=EGY)_production_anomalies=FAOsince-2005"
        "_regions=AgrimateEU28_start=2000-01-01.nc"
    ),
}

KT_TO_MMT = 1.0 / 1000.0  # NetCDF units are "1000 tonne"
AUTHOR_START_YEAR = 2000
STEPS_PER_YEAR = 24


def world_market_price_index(
    quantity: np.ndarray,
    price: np.ndarray,
) -> np.ndarray:
    """Volume-weighted international transaction price (plot.jl Fig. 4d).

    ``quantity`` and ``price`` are (producer, consumer, time). Domestic
    (diagonal) flows are dropped. Missing pairs are skipped (NaN).
    """
    q = np.asarray(quantity, float)
    p = np.asarray(price, float)
    if q.ndim != 3 or q.shape != p.shape:
        raise ValueError("quantity and price must be (R, R, T) and aligned")
    r = q.shape[0]
    off = ~np.eye(r, dtype=bool)
    q = np.where(off[:, :, None], q, np.nan)
    p = np.where(off[:, :, None], p, np.nan)
    value = q * p
    qsum = np.nansum(q, axis=(0, 1))
    vsum = np.nansum(value, axis=(0, 1))
    out = np.full(q.shape[2], np.nan, dtype=float)
    np.divide(vsum, qsum, out=out, where=qsum > 0)
    return out


def _step_years(n_t: int, start_year: int = AUTHOR_START_YEAR) -> np.ndarray:
    return start_year + np.arange(n_t) // STEPS_PER_YEAR


def _step_months(n_t: int) -> np.ndarray:
    return (np.arange(n_t) % STEPS_PER_YEAR) // 2 + 1


def _decode_regions(var) -> list[str]:
    return [str(r) for r in var[:]]


def extract_scenario_from_nc(path: Path, scenario: str) -> dict[str, pd.DataFrame]:
    """Pull Fig. 4 world + regional series from one author NetCDF."""
    from netCDF4 import Dataset  # optional; extraction only

    ds = Dataset(path)
    try:
        regions = _decode_regions(ds.variables["region"])
        harvest = np.array(ds.variables["harvest"][:], float)
        cons = np.array(ds.variables["consumption"][:], float)
        sp = np.array(ds.variables["producer storage"][:], float)
        sc = np.array(ds.variables["consumer storage"][:], float)
        xi = np.array(ds.variables["sales foreign"][:], float)
        qty = np.array(ds.variables["transaction quantity"][:], float)
        price = np.array(ds.variables["transaction price"][:], float)
        attrs = {k: str(ds.getncattr(k)) for k in ds.ncattrs()}
    finally:
        ds.close()

    n_r, n_t = harvest.shape
    years = _step_years(n_t)
    months = _step_months(n_t)
    wm = world_market_price_index(qty, price)
    h_world = np.nansum(harvest, axis=0) * KT_TO_MMT
    c_world = np.nansum(cons, axis=0) * KT_TO_MMT
    sp_world = np.nansum(sp, axis=0) * KT_TO_MMT
    sc_world = np.nansum(sc, axis=0) * KT_TO_MMT
    xi_world = np.nansum(xi, axis=0) * KT_TO_MMT

    monthly_rows = []
    n_m = n_t // 2
    wm_m = np.full(n_m, np.nan)
    # Volume-weight the two half-month international baskets (plot.jl).
    r = qty.shape[0]
    off = ~np.eye(r, dtype=bool)
    q_off = np.where(off[:, :, None], qty, np.nan)
    v_off = q_off * np.where(off[:, :, None], price, np.nan)
    q_step = np.nansum(q_off, axis=(0, 1))
    v_step = np.nansum(v_off, axis=(0, 1))
    for m_i in range(n_m):
        sl = slice(2 * m_i, 2 * m_i + 2)
        qs = np.nansum(q_step[sl])
        vs = np.nansum(v_step[sl])
        wm_m[m_i] = vs / qs if qs > 0 else np.nan
        y = int(years[2 * m_i])
        mo = int(months[2 * m_i])
        monthly_rows.append({
            "year": y,
            "month": mo,
            "scenario": scenario,
            "wm_price_index": float(wm_m[m_i]),
            "harvest_mmt": float(np.nansum(h_world[sl])),
            "consumption_mmt": float(np.nansum(c_world[sl])),
            "producer_storage_mmt": float(sp_world[2 * m_i + 1]),
            "consumer_storage_mmt": float(sc_world[2 * m_i + 1]),
            "sales_foreign_mmt": float(np.nansum(xi_world[sl])),
        })
    monthly = pd.DataFrame(monthly_rows)

    annual_rows = []
    y0, y1 = int(years.min()), int(years.max())
    for y in range(y0, y1 + 1):
        m = years == y
        last = int(np.where(m)[0][-1])
        annual_rows.append({
            "year": y,
            "scenario": scenario,
            "production": float(np.nansum(harvest[:, m]) * KT_TO_MMT),
            "consumption": float(np.nansum(cons[:, m]) * KT_TO_MMT),
            "exports": float(np.nansum(xi[:, m]) * KT_TO_MMT),
            "ending_stocks": float(
                (np.nansum(sp[:, last]) + np.nansum(sc[:, last])) * KT_TO_MMT
            ),
            "S_producer": float(np.nansum(sp[:, last]) * KT_TO_MMT),
            "S_consumer": float(np.nansum(sc[:, last]) * KT_TO_MMT),
            "wm_price_index_mean": float(np.nanmean(wm[m])),
        })
    annual = pd.DataFrame(annual_rows)

    regional_rows = []
    for i, name in enumerate(regions):
        for y in range(y0, y1 + 1):
            m = years == y
            last = int(np.where(m)[0][-1])
            regional_rows.append({
                "year": y,
                "scenario": scenario,
                "region": name,
                "production": float(np.nansum(harvest[i, m]) * KT_TO_MMT),
                "consumption": float(np.nansum(cons[i, m]) * KT_TO_MMT),
                "exports": float(np.nansum(xi[i, m]) * KT_TO_MMT),
                "S_producer": float(sp[i, last] * KT_TO_MMT)
                if np.isfinite(sp[i, last]) else float("nan"),
                "S_consumer": float(sc[i, last] * KT_TO_MMT)
                if np.isfinite(sc[i, last]) else float("nan"),
            })
    regional = pd.DataFrame(regional_rows)
    attr_row = pd.DataFrame([{
        "scenario": scenario,
        "file": path.name,
        **attrs,
        "n_regions": n_r,
        "n_steps": n_t,
        "region_list": "|".join(regions),
    }])
    return {
        "monthly": monthly,
        "annual": annual,
        "regional": regional,
        "attrs": attr_row,
    }


def extract_author_fig4(nc_dir: Path, out_dir: Path | None = None) -> Path:
    """Extract the three main_output NetCDFs to committed CSVs."""
    nc_dir = Path(nc_dir)
    out_dir = Path(out_dir) if out_dir else AUTHOR_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    parts = {k: [] for k in ("monthly", "annual", "regional", "attrs")}
    for scenario, fname in AUTHOR_SCENARIO_FILES.items():
        path = nc_dir / fname
        if not path.is_file():
            raise FileNotFoundError(path)
        extracted = extract_scenario_from_nc(path, scenario)
        for k, df in extracted.items():
            parts[k].append(df)
    monthly = pd.concat(parts["monthly"], ignore_index=True)
    annual = pd.concat(parts["annual"], ignore_index=True)
    regional = pd.concat(parts["regional"], ignore_index=True)
    attrs = pd.concat(parts["attrs"], ignore_index=True)
    monthly.to_csv(out_dir / "monthly_world.csv", index=False)
    annual.to_csv(out_dir / "annual_world.csv", index=False)
    regional.to_csv(out_dir / "annual_regional.csv", index=False)
    attrs.to_csv(out_dir / "netcdf_attrs.csv", index=False)
    (out_dir / "netcdf_attrs.json").write_text(
        json.dumps(attrs.to_dict(orient="records"), indent=2) + "\n"
    )
    return out_dir


def load_author_fig4(author_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    d = Path(author_dir) if author_dir else AUTHOR_DIR
    monthly = pd.read_csv(d / "monthly_world.csv")
    annual = pd.read_csv(d / "annual_world.csv")
    regional = pd.read_csv(d / "annual_regional.csv")
    attrs = pd.read_csv(d / "netcdf_attrs.csv")
    return {
        "monthly": monthly, "annual": annual,
        "regional": regional, "attrs": attrs,
    }


def host_monthly_index(prices_csv: Path) -> pd.DataFrame:
    """Host monthly D.7 index from ``prices_three_scenarios.csv`` (USD / p0)."""
    raw = pd.read_csv(prices_csv, index_col=0)
    raw.index = pd.PeriodIndex(raw.index, freq="M")
    p0 = float(raw.loc[raw.index.year == 2006, "pink_usd"].mean())
    rows = []
    for name in SCENARIO_ORDER:
        if name not in raw.columns:
            continue
        s = raw[name].astype(float) / p0
        for period, val in s.items():
            rows.append({
                "year": int(period.year),
                "month": int(period.month),
                "scenario": name,
                "host_price_index": float(val),
                "host_usd": float(raw.loc[period, name]),
                "pink_usd": float(raw.loc[period, "pink_usd"]),
                "p0": p0,
            })
    return pd.DataFrame(rows)


def _monthly_series(df: pd.DataFrame, value: str, scenario: str) -> pd.Series:
    sub = df[df["scenario"] == scenario]
    idx = [
        pd.Period(year=int(y), month=int(m), freq="M")
        for y, m in zip(sub["year"], sub["month"])
    ]
    return pd.Series(sub[value].to_numpy(float), index=idx, name=value)


def score_fig4_prices(
    host_m: pd.DataFrame,
    author_m: pd.DataFrame,
    score_start: int = 2006,
    score_end: int = 2011,
) -> pd.DataFrame:
    rows = []
    for name in SCENARIO_ORDER:
        host = _monthly_series(host_m, "host_price_index", name)
        auth = _monthly_series(author_m, "wm_price_index", name)
        both = pd.concat([host.rename("host"), auth.rename("author")],
                         axis=1).dropna()
        both = both[(both.index.year >= score_start)
                    & (both.index.year <= score_end)]
        h06 = float(both["host"][both.index.year == score_start].mean())
        a06 = float(both["author"][both.index.year == score_start].mean())
        host_n = both["host"] / h06 if h06 else both["host"]
        auth_n = both["author"] / a06 if a06 else both["author"]
        rows.append({
            "scenario": name,
            "corr_index": _corr(both["host"], both["author"]),
            "rmse_index": _rmse(both["host"], both["author"]),
            "corr_2006eq1": _corr(host_n, auth_n),
            "rmse_2006eq1": _rmse(host_n, auth_n),
            "hike_2008_host": _hike(both["host"], score_start, 2008),
            "hike_2008_author": _hike(both["author"], score_start, 2008),
            "mean_2006_host": h06,
            "mean_2006_author": a06,
            "n_months": int(len(both)),
        })
    return pd.DataFrame(rows)


def score_fig4_supply(
    host_annual: dict[str, pd.DataFrame],
    author_annual: pd.DataFrame,
    score_start: int = 2006,
    score_end: int = 2011,
) -> pd.DataFrame:
    fields = ("production", "consumption", "exports", "ending_stocks")
    rows = []
    for name in SCENARIO_ORDER:
        host = host_annual[name]
        host = host[(host["year"] >= score_start) & (host["year"] <= score_end)]
        auth = author_annual[author_annual["scenario"] == name]
        auth = auth[(auth["year"] >= score_start) & (auth["year"] <= score_end)]
        both = host.set_index("year")[list(fields)].add_suffix("_h").join(
            auth.set_index("year")[list(fields)].add_suffix("_a"), how="inner"
        )
        for field in fields:
            rows.append({
                "scenario": name,
                "field": field,
                "corr": _corr(both[f"{field}_h"], both[f"{field}_a"]),
                "rmse": _rmse(both[f"{field}_h"], both[f"{field}_a"]),
                "mean_host": float(both[f"{field}_h"].mean()),
                "mean_author": float(both[f"{field}_a"].mean()),
            })
    return pd.DataFrame(rows)


def score_fig4_regional(
    host_regional: dict[tuple[str, str], pd.DataFrame],
    author_regional: pd.DataFrame,
    score_start: int = 2006,
    score_end: int = 2011,
) -> pd.DataFrame:
    """Compare host Ukraine / Eastern Africa annual tables to author."""
    fields = ("production", "consumption", "exports", "S_producer", "S_consumer")
    rows = []
    for (scenario, region), host in host_regional.items():
        auth = author_regional[
            (author_regional["scenario"] == scenario)
            & (author_regional["region"] == region)
        ]
        if auth.empty:
            continue
        host = host[(host["year"] >= score_start) & (host["year"] <= score_end)]
        auth = auth[(auth["year"] >= score_start) & (auth["year"] <= score_end)]
        h = host.set_index("year")
        a = auth.set_index("year")
        for field in fields:
            if field not in h.columns or field not in a.columns:
                continue
            rows.append({
                "scenario": scenario,
                "region": region,
                "field": field,
                "corr": _corr(h[field], a[field]),
                "rmse": _rmse(h[field], a[field]),
                "mean_host": float(h[field].mean()),
                "mean_author": float(a[field].mean()),
            })
    return pd.DataFrame(rows)


def author_undisturbed_drift(author_m: pd.DataFrame,
                             score_start: int = 2006,
                             score_end: int = 2011) -> dict[str, float]:
    s = _monthly_series(author_m, "wm_price_index", "undisturbed")
    s = s[(s.index.year >= score_start) & (s.index.year <= score_end)]
    annual = [float(s[s.index.year == y].mean())
              for y in range(score_start, score_end + 1)]
    first, last = annual[0], annual[-1]
    return {
        "annual_mean_first": first,
        "annual_mean_last": last,
        "last_over_first": last / first if first else float("nan"),
        "cv": float(s.std() / s.mean()) if float(s.mean()) else float("nan"),
        "seasonal_corr_first_last": _corr(
            s[s.index.year == score_start].to_numpy(),
            s[s.index.year == score_end].to_numpy(),
        ),
    }


def _fmt(x, nd: int = 3) -> str:
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "nan"
    if isinstance(x, (int, np.integer)):
        return str(int(x))
    return f"{float(x):.{nd}f}"


def write_fig4_report(
    prices: pd.DataFrame,
    supply: pd.DataFrame,
    regional: pd.DataFrame,
    attrs: pd.DataFrame,
    drift: dict[str, float],
    out_dir: Path,
    score_start: int = 2006,
    score_end: int = 2011,
) -> Path:
    out_dir = Path(out_dir)
    a0 = attrs.iloc[0]
    lines = [
        "# Agrimate Fig. 4 — author series vs this host (P7)",
        "",
        "Independent implementation. Do **not** claim replication.",
        "",
        "## G0-U items 1–3 (before historical fit)",
        "",
        "Pass rule from `DEVELOPMENT.md`: items 1–3 must be honest before",
        "judging item 5. P2 drift remains unexplained; this page still",
        "compares, and it does not claim replication.",
        "",
        "1. **Source fidelity.** Met for retrieved Zenodo 14022004 code with",
        "   labelled S3/S4/A1–A6/N5. The Fig. 4 NetCDF is a *different*",
        "   executable than that host (see experiment mismatch below).",
        "2. **Numerical reliability.** Plans are feasible (residual 0,",
        "   failed/fallback 0) but **not** first-order stationary: harvest+AMIS",
        "   unconverged scipy 1743/5832 (N5). Counted, not papered over.",
        "3. **Undisturbed dynamics.** Seasonal shape repeats (corr 0.98) but",
        "   the annual-mean world-price ratio 2011/2006 is **1.63** (`undisturbed.md`).",
        "   Author Fig. 4 baseline on the same window is repeating",
        f"   (last/first = {_fmt(drift['last_over_first'], 3)},",
        f"   seasonal corr {_fmt(drift['seasonal_corr_first_last'], 3)}).",
        "   P2 drift is unexplained. Not a price pin.",
        "",
        "## Author experiment (Zenodo 10688435 main_output)",
        "",
        "- record: 10.5281/zenodo.10688435; data.zip md5 `2f3809c66e78b72b3c74971051f89529`.",
        f"- region set: `AgrimateEU28` + extra Egypt=EGY ({int(a0.get('n_regions', 27))} nodes;",
        "  Egypt split out; EU-28 not EU-27;",
        "  Brazil is inside Rest of South America). Host is AgrimateRegionsWheat",
        "  (Brazil named, EU-27, Egypt inside Northern Africa).",
        f"- α_foreign=`{a0.get('α_foreign', '')}`; α=`{a0.get('α', '')}`;",
        f"  ζ=`{a0.get('ζ', '')}`; N_for=`{a0.get('N_for', '')}`;",
        f"  p_sto=`{a0.get('p_sto', '')}`; σ=`{a0.get('σ', '')}`; ε_c=`{a0.get('ε_c', '')}`.",
        f"- anomalies: FAO since 2005; restrictions 2007–2011; baseline 2007–2009;",
        f"  start `{a0.get('start', '2000-01-01')}`; crop `{a0.get('crops', 'wheat')}`.",
        f"- gitcommit `{a0.get('gitcommit', '')}` (old-demand-dynamics, not",
        "  the later 14022004 equal-sales-penalty tree).",
        "- World price in Fig. 4d is the volume-weighted international",
        "  transaction price, not D.7 on world XI*. Host scores XI-weighted",
        "  lagged D.7 offers × p0 / p0 (`world_price.md`). Author",
        "  `plot_wm_price_timeseries` is not in-tree.",
        "- PDF digitisation in `diagnostics/redteam/r5/` was **not** used.",
        "",
        "Host defaults stay 14022004 `AgrimateParams` (αI=3.2, ζ=0 penalty on,",
        "N_for=3 months). No retune to Fig. 4 knobs or to Bai α_foreign=10.",
        "",
        f"Score window {score_start}–{score_end}. Pink Sheet stays a side column;",
        "the target here is the author series.",
        "",
        "## World-market price index vs Fig. 4d",
        "",
        "| scenario | corr (index) | RMSE index | corr (2006=1) | 2008 hike host | hike author | 2006 mean host | 2006 author |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for _, r in prices.iterrows():
        lines.append(
            f"| {r['scenario']} | {_fmt(r['corr_index'])} | {_fmt(r['rmse_index'])} "
            f"| {_fmt(r['corr_2006eq1'])} | ×{_fmt(r['hike_2008_host'], 2)} "
            f"| ×{_fmt(r['hike_2008_author'], 2)} | {_fmt(r['mean_2006_host'])} "
            f"| {_fmt(r['mean_2006_author'])} |"
        )
    lines += [
        "",
        "Author harvest+AMIS 2008 hike is the published-experiment number to",
        "beat, not Pink Sheet ×1.88. Host hike remains several times larger",
        "and 2006 levels are ~0.3 vs author ~1.1. Correlation of the raw",
        "index is not a replication claim.",
        "",
        "## World supply / consumption / stocks vs Fig. 4 series",
        "",
        "Author units 1000 t, converted /1000 → MMT. Host is the 27-node USDA",
        "sum (A1). Level bias is expected. Undisturbed production corr is nan",
        "because both series are constant (author repeating FAO baseline,",
        "host repeating USDA 2007–09 mean) at different levels (542 vs 631 MMT).",
        "",
        "| scenario | field | corr | RMSE | mean host | mean author |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for _, r in supply.iterrows():
        lines.append(
            f"| {r['scenario']} | {r['field']} | {_fmt(r['corr'])} | {_fmt(r['rmse'], 2)} "
            f"| {_fmt(r['mean_host'], 2)} | {_fmt(r['mean_author'], 2)} |"
        )
    lines += [
        "",
        "## Regional (host tables that exist: Ukraine, Eastern Africa)",
        "",
        "Author Egypt is a split node; host folds Egypt into Northern Africa.",
        "EU-28 vs EU-27 is labelled, not equated. Only shared names below.",
        "",
        "| scenario | region | field | corr | RMSE | mean host | mean author |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    if regional is None or regional.empty:
        lines.append("| — | — | — | — | — | — | — |")
    else:
        for _, r in regional.iterrows():
            lines.append(
                f"| {r['scenario']} | {r['region']} | {r['field']} | {_fmt(r['corr'])} "
                f"| {_fmt(r['rmse'], 2)} | {_fmt(r['mean_host'], 2)} "
                f"| {_fmt(r['mean_author'], 2)} |"
            )
    lines += [
        "",
        "## Verdict",
        "",
        "Independent implementation, Fig. 4 series **in hand**, scored, **not",
        "a replication**. G0-U (3) fails on the host (drift 1.63 vs author",
        "1.00). G0-U (2) is N5, not a unique maximizer. Do not restore L1–L8.",
        "Do not retune αI. P8 writes the G0-H hindcast note from these numbers.",
        "",
        "## Files",
        "",
        "- `author_fig4/PROVENANCE.txt`",
        "- `author_fig4/monthly_world.csv`, `annual_world.csv`, `annual_regional.csv`",
        "- `score_fig4_prices.csv`, `score_fig4_supply.csv`, `score_fig4_regional.csv`",
        "- `figures/fig4_author_vs_host_prices.png` (diagnostic overlay)",
        "",
    ]
    path = out_dir / "fig4.md"
    path.write_text("\n".join(lines) + "\n")
    return path


def write_fig4_price_figure(
    host_m: pd.DataFrame,
    author_m: pd.DataFrame,
    out_path: Path,
    score_start: int = 2006,
    score_end: int = 2011,
) -> Path:
    import matplotlib.pyplot as plt

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    colors = {
        "undisturbed": "#4c78a8",
        "harvest": "#f58518",
        "harvest_amis": "#e45756",
    }
    fig, axes = plt.subplots(2, 1, figsize=(9.5, 6.5), sharex=True)
    for name in SCENARIO_ORDER:
        h = _monthly_series(host_m, "host_price_index", name)
        a = _monthly_series(author_m, "wm_price_index", name)
        h = h[(h.index.year >= score_start) & (h.index.year <= score_end)]
        a = a[(a.index.year >= score_start) & (a.index.year <= score_end)]
        t_h = [p.to_timestamp() for p in h.index]
        t_a = [p.to_timestamp() for p in a.index]
        axes[0].plot(t_h, h.values, color=colors[name], lw=1.4, label=f"host {name}")
        axes[0].plot(t_a, a.values, color=colors[name], lw=1.4, ls="--",
                     label=f"author {name}")
        h0 = float(h[h.index.year == score_start].mean())
        a0 = float(a[a.index.year == score_start].mean())
        axes[1].plot(t_h, h.values / h0, color=colors[name], lw=1.4)
        axes[1].plot(t_a, a.values / a0, color=colors[name], lw=1.4, ls="--")
    axes[0].set_ylabel("price index")
    axes[0].set_title("Fig. 4d world-market index (solid host D.7, dashed author tx)")
    axes[0].legend(ncol=2, fontsize=8)
    axes[1].set_ylabel("index / 2006 mean")
    axes[1].set_title("Same series, 2006 = 1 (not a pin)")
    axes[1].axhline(1.0, color="0.6", lw=0.8, ls=":")
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return out_path


def load_host_annual(out_dir: Path) -> dict[str, pd.DataFrame]:
    out_dir = Path(out_dir)
    return {
        "undisturbed": pd.read_csv(out_dir / "annual_undisturbed.csv"),
        "harvest": pd.read_csv(out_dir / "annual_harvest.csv"),
        "harvest_amis": pd.read_csv(out_dir / "annual_harvest_amis.csv"),
    }


def load_host_regional(out_dir: Path) -> dict[tuple[str, str], pd.DataFrame]:
    out_dir = Path(out_dir)
    tables = {}
    for scenario, tag in (
        ("undisturbed", "undisturbed"),
        ("harvest", "harvest"),
        ("harvest_amis", "harvest_amis"),
    ):
        for region, stem in (
            ("Ukraine", "ukraine"),
            ("Eastern Africa", "eastern_africa"),
        ):
            path = out_dir / f"{stem}_{tag}.csv"
            if path.is_file():
                tables[(scenario, region)] = pd.read_csv(path)
    return tables


def run_fig4_score(
    out_dir: Path | None = None,
    author_dir: Path | None = None,
    score_start: int = 2006,
    score_end: int = 2011,
) -> dict[str, Path]:
    out_dir = Path(out_dir) if out_dir else OUT_DEFAULT
    author = load_author_fig4(author_dir)
    host_m = host_monthly_index(out_dir / "prices_three_scenarios.csv")
    prices = score_fig4_prices(host_m, author["monthly"], score_start, score_end)
    supply = score_fig4_supply(
        load_host_annual(out_dir), author["annual"], score_start, score_end
    )
    regional = score_fig4_regional(
        load_host_regional(out_dir), author["regional"], score_start, score_end
    )
    drift = author_undisturbed_drift(author["monthly"], score_start, score_end)
    prices.to_csv(out_dir / "score_fig4_prices.csv", index=False)
    supply.to_csv(out_dir / "score_fig4_supply.csv", index=False)
    regional.to_csv(out_dir / "score_fig4_regional.csv", index=False)
    fig = write_fig4_price_figure(
        host_m, author["monthly"],
        out_dir / "figures" / "fig4_author_vs_host_prices.png",
        score_start, score_end,
    )
    report = write_fig4_report(
        prices, supply, regional, author["attrs"], drift, out_dir,
        score_start, score_end,
    )
    return {"report": report, "figure": fig}
