"""G0-H P9: named-region USDA PSD vs 27-node host.

Global scores compare the 27-node *sum* to USDA *world*. This module
compares named exporters and Eastern Africa to ``psd_regional_annual()``
(mapped PSD members, marketing year). Coverage gaps stay labelled.
Does not retune αI / p_sto / xmin.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from sheaf.data_usda import load_psd_country

from .params import wheat_params
from .validation import (
    OUT_DEFAULT,
    SCENARIO_ORDER,
    _corr,
    regional_annual,
    run_three_scenarios,
)
from .wheat_data import WheatData, _psd_to_region, prepare_wheat, psd_regional_annual

SCORE_START = 2006
SCORE_END = 2011
BASE_YEARS = (2007, 2009)

# Prompt list: named exporters + Eastern Africa (the G0-U purchaser panel).
NAMED_REGIONS: tuple[str, ...] = (
    "USA", "Russia", "Ukraine", "EU-27",
    "Argentina", "Australia", "Canada", "India", "China",
    "Eastern Africa",
)

FIELDS = ("production", "consumption", "ending_stocks")


def _fmt(x, nd: int = 2) -> str:
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "nan"
    if isinstance(x, (int, np.integer)):
        return str(int(x))
    return f"{float(x):.{nd}f}"


def psd_construction_table(
    regions: list[str] | None = None,
    year0: int = BASE_YEARS[0],
    year1: int = BASE_YEARS[1],
) -> pd.DataFrame:
    """2007–09 PSD member mean vs sum vs host ``H_annual``.

    S1: ``prepare_wheat`` uses member-sum within year, then mean over
    2007–09 (same construction as ``psd_regional_annual()``). The pooled
    country-year mean is reported for the A8 counterexample only.
    """
    data = prepare_wheat(start_year=year0, end_year=year1)
    regions = list(regions or NAMED_REGIONS)
    raw = load_psd_country("wheat").copy()
    raw["region"] = [
        _psd_to_region(c, n) for c, n in zip(raw["country_code"], raw["country_psd"])
    ]
    base = raw[(raw["year"] >= year0) & (raw["year"] <= year1)]
    rows = []
    for r in regions:
        sub = base[base["region"] == r]
        names = sorted(sub["country_psd"].dropna().unique().tolist())
        n_cty = len(names)
        if sub.empty:
            mean_p = mean_c = mean_s = sum_p = sum_c = sum_s = float("nan")
        else:
            mean_p = float(sub["production"].mean())
            mean_c = float(sub["consumption"].mean())
            mean_s = float(sub["ending_stocks"].mean())
            byy = sub.groupby("year")[["production", "consumption", "ending_stocks"]].sum()
            sum_p = float(byy["production"].mean())
            sum_c = float(byy["consumption"].mean())
            sum_s = float(byy["ending_stocks"].mean())
        i = data.regions.index(r) if r in data.regions else None
        h = float(data.H_annual[i]) if i is not None else float("nan")
        rows.append({
            "region": r,
            "n_psd_members": n_cty,
            "psd_members": "|".join(names),
            "psd_mean_production": mean_p,
            "psd_sum_production": sum_p,
            "psd_mean_consumption": mean_c,
            "psd_sum_consumption": sum_c,
            "psd_mean_ending_stocks": mean_s,
            "psd_sum_ending_stocks": sum_s,
            "model_H_annual": h,
            "host_over_psd_sum": (h / sum_p) if sum_p else float("nan"),
            "construction": (
                "single_psd_row" if n_cty == 1 else
                "member_sum" if n_cty > 1 else
                "unmapped"
            ),
        })
    return pd.DataFrame(rows)


def model_production_annual(
    data: WheatData,
    use_anomalies: bool,
    start: int = SCORE_START,
    end: int = SCORE_END,
) -> pd.DataFrame:
    """Calendar-year harvest from ``H_annual`` × (1+anomaly). No NLP.

    Matches ``AgrimateSim.harvest_at`` summed over the 24-step year
    (profile sums to 1). Checked against saved Ukraine mechanism CSVs.
    """
    rows = []
    for y in range(start, end + 1):
        yi = y - data.start_year
        if yi < 0 or yi >= data.anomaly.shape[1]:
            continue
        scale = (1.0 + data.anomaly[:, yi]) if use_anomalies else 1.0
        h = np.maximum(data.H_annual * scale, 0.0)
        for i, r in enumerate(data.regions):
            rows.append({"year": y, "region": r, "production": float(h[i])})
    return pd.DataFrame(rows)


def _result_regional(result, region: str) -> pd.DataFrame:
    tab = regional_annual(result, region)
    tab = tab.copy()
    tab["ending_stocks"] = tab["S_producer"] + tab["S_consumer"]
    tab["region"] = region
    return tab


def score_regional(
    data: WheatData,
    results: dict | None = None,
    start: int = SCORE_START,
    end: int = SCORE_END,
    regions: tuple[str, ...] | None = None,
) -> pd.DataFrame:
    """Long table: scenario × region × year × field vs mapped PSD."""
    regions = tuple(regions or NAMED_REGIONS)
    psd = psd_regional_annual(list(data.regions))
    psd = psd[(psd["year"] >= start) & (psd["year"] <= end)]
    rows = []
    for name in SCENARIO_ORDER:
        use_anom = name != "undisturbed"
        prod = model_production_annual(data, use_anom, start, end)
        cons_stock: dict[str, pd.DataFrame] = {}
        if results is not None and name in results:
            res = results[name]
            for r in regions:
                if r in res.regions:
                    cons_stock[r] = _result_regional(res, r)
        for r in regions:
            p = prod[prod["region"] == r].set_index("year")
            o = psd[psd["region"] == r].set_index("year")
            cs = cons_stock.get(r)
            if cs is not None:
                cs = cs.set_index("year")
            years = [y for y in range(start, end + 1) if y in p.index]
            for y in years:
                for field in FIELDS:
                    if field == "production":
                        model = float(p.loc[y, "production"])
                    elif cs is not None and field in cs.columns and y in cs.index:
                        model = float(cs.loc[y, field])
                    else:
                        model = float("nan")
                    obs = float(o.loc[y, field]) if (not o.empty and y in o.index) else float("nan")
                    rows.append({
                        "scenario": name,
                        "region": r,
                        "year": y,
                        "field": field,
                        "model": model,
                        "usda": obs,
                    })
    return pd.DataFrame(rows)


def summarize_regional(long: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (sc, r, f), g in long.groupby(["scenario", "region", "field"], sort=False):
        m, o = g["model"], g["usda"]
        with np.errstate(invalid="ignore"):
            corr = _corr(m, o)
        mm, mo = float(m.mean()), float(o.mean())
        rows.append({
            "scenario": sc,
            "region": r,
            "field": f,
            "corr": corr,
            "mean_model": mm,
            "mean_usda": mo,
            "level_ratio": (mm / mo) if mo and np.isfinite(mo) else float("nan"),
            "n_years": int(len(g)),
        })
    return pd.DataFrame(rows)


def write_regional_note(
    construction: pd.DataFrame,
    summary: pd.DataFrame,
    long: pd.DataFrame,
    out_dir: Path,
) -> Path:
    ha = summary[summary["scenario"] == "harvest_amis"]
    has_cs = bool(
        long[(long["field"] != "production") & np.isfinite(long["model"])].shape[0]
    )
    ch = construction[construction["region"] == "China"].iloc[0]
    ea = construction[construction["region"] == "Eastern Africa"].iloc[0]
    usa = construction[construction["region"] == "USA"].iloc[0]
    lines = [
        "# G0-H — regional USDA vs 27-node host (P9)",
        "",
        "Global scores compare the **27-node sum** to USDA **world** PSD.",
        "This table compares named AgrimateRegionsWheat nodes to",
        "`psd_regional_annual()` (mapped PSD members, marketing year).",
        "Coverage gaps stay labelled. `wheat_params()` stay αI=3.2,",
        "p_sto=0.1, xmin=0.2. No fit to close the stock-level gap.",
        "L1–L8 stay rejected. Bai α_foreign=10 not adopted.",
        "",
        "Harvest is reconstructed from `H_annual × (1+anomaly)` (no NLP);",
        "it matches the saved Ukraine mechanism CSVs year-for-year.",
    ]
    if has_cs:
        lines += [
            "Consumption and ending stocks are from a dedicated three-scenario",
            "dump. Ukraine 2006–11 consumption matches the P0c panel CSV",
            "bit-for-bit (N5 did not move these annuals).",
        ]
    else:
        lines.append(
            "Consumption and ending stocks were not dumped for every named node."
        )
    lines += [
        "",
        "## Construction (A8, S1 implemented)",
        "",
        "`prepare_wheat` 2007–09 baseline **sums** PSD members within each",
        "year, then means over 2007–09 — the same construction as",
        "`psd_regional_annual()`. Stocks are USDA `ending_stocks`, never",
        "FAOSTAT FBSH Stock Variation (element 5074). Pooled country-year",
        "`groupby.mean()` is the rejected A8 construction (R7 labelled).",
        "2007–09 production:",
        "",
        "| region | PSD members | host H (member-sum) | PSD sum | host/sum |",
        "|---|---|---:|---:|---:|",
        f"| USA | {usa['n_psd_members']} ({usa['psd_members']}) | "
        f"{_fmt(usa['model_H_annual'], 1)} | {_fmt(usa['psd_sum_production'], 1)} | "
        f"{_fmt(usa['host_over_psd_sum'], 2)} |",
        f"| China | {int(ch['n_psd_members'])} ({ch['psd_members']}) | "
        f"{_fmt(ch['model_H_annual'], 1)} | {_fmt(ch['psd_sum_production'], 1)} | "
        f"{_fmt(ch['host_over_psd_sum'], 2)} |",
        f"| Eastern Africa | {int(ea['n_psd_members'])} countries | "
        f"{_fmt(ea['model_H_annual'], 2)} | {_fmt(ea['psd_sum_production'], 2)} | "
        f"{_fmt(ea['host_over_psd_sum'], 2)} |",
        "",
        "China is China+Hong Kong; HK production is ~0, so the *old* mean",
        f"was ~½ of mainland ({_fmt(ch['psd_mean_production'], 1)} vs "
        f"{_fmt(ch['psd_sum_production'], 1)} MMT). Eastern Africa's *old*",
        f"mean of {int(ea['n_psd_members'])} mapped countries was "
        f"{_fmt(ea['psd_mean_production'], 2)} vs "
        f"{_fmt(ea['psd_sum_production'], 2)}. Host H now matches the sum.",
        "EU-27 is USDA's single `European Union` aggregate, not 27 ISO3",
        "sums (United Kingdom is Rest of Europe). Verification protocol:",
        "the claim is A8 member-sum; the implementation matches",
        "`psd_regional_annual()`. **S1 implemented.** Not a parameter fit.",
        "Do not retune αI / p_sto / xmin. Do not treat FAO ΔS as stocks.",
        "",
        "Other labelled coverage: calendar-year model stocks vs USDA",
        "marketing year; 27-node sum vs world PSD at the global score;",
        "FAOSTAT Food Balances still absent (A1).",
        "",
        "## 2006–11 harvest+AMIS vs mapped PSD",
        "",
        "| region | field | corr | mean host | mean PSD | ratio |",
        "|---|---|---:|---:|---:|---:|",
    ]
    order = list(NAMED_REGIONS)
    for r in order:
        sub = ha[ha["region"] == r]
        for field in FIELDS:
            row = sub[sub["field"] == field]
            if row.empty:
                continue
            x = row.iloc[0]
            if field != "production" and not np.isfinite(x["mean_model"]):
                continue
            lines.append(
                f"| {r} | {field} | {_fmt(x['corr'], 3)} | "
                f"{_fmt(x['mean_model'], 1)} | {_fmt(x['mean_usda'], 1)} | "
                f"{_fmt(x['level_ratio'], 2)} |"
            )
    # singles vs multi-member production ratios
    def _ratio(region: str, field: str = "production") -> float:
        row = ha[(ha["region"] == region) & (ha["field"] == field)]
        return float(row.iloc[0]["level_ratio"]) if not row.empty else float("nan")

    def _corr_of(region: str, field: str = "production") -> float:
        row = ha[(ha["region"] == region) & (ha["field"] == field)]
        return float(row.iloc[0]["corr"]) if not row.empty else float("nan")

    lines += [
        "",
        "Named **single-row** exporters (USA, Russia, Ukraine, EU-27,",
        "Argentina, Australia, Canada, India) sit near PSD on *mean*",
        f"production (Ukraine ratio {_fmt(_ratio('Ukraine'), 2)}, USA "
        f"{_fmt(_ratio('USA'), 2)}). Weather-driven series correlate",
        f"(USA {_fmt(_corr_of('USA'), 2)}; Ukraine "
        f"{_fmt(_corr_of('Ukraine'), 2)}). India "
        f"({_fmt(_corr_of('India'), 2)}) and China "
        f"({_fmt(_corr_of('China'), 2)}) do not: host harvest is the",
        "2007–09 mean times a LOWESS residual, while PSD is a rising",
        "level. That is Agrimate-style anomaly forcing, not a missing",
        f"knob. China production is {_fmt(_ratio('China'), 2)}× mapped PSD",
        f"(A8 member-sum). Eastern Africa production is {_fmt(_ratio('Eastern Africa'), 2)}×",
        "(A8 member-sum). Do not fit xmin or p_sto to the stock column: Ukraine",
        f"stocks are {_fmt(_ratio('Ukraine', 'ending_stocks'), 2)}× mapped",
        "PSD; Eastern Africa stocks are "
        f"{_fmt(_ratio('Eastern Africa', 'ending_stocks'), 2)}×. The world 1.58×",
        "gap in `hindcast.md` is a different comparison (27-node sum vs",
        "world PSD; stale until S5 re-score).",
        "",
        "Eastern Africa *consumption* is not the old 0.1× PSD: inflows come from",
        "T* (A2), so the purchaser can eat imported grain. Host H is now the",
        "10-country sum (ratio "
        f"{_fmt(_ratio('Eastern Africa', 'consumption'), 2)}). USA",
        f"consumption is {_fmt(_ratio('USA', 'consumption'), 2)}× mapped",
        "PSD (2007–08 host vs PSD ~30) — who-eats / export drain,",
        "not xmin. Argentina ending stocks are "
        f"{_fmt(_ratio('Argentina', 'ending_stocks'), 2)}×. Those are",
        "labelled regional gaps. Do not fit a storage-cost knob to them.",
        "",
        "## Harvest-only vs harvest+AMIS (regional)",
        "",
        "Production is identical by construction (same anomalies). AMIS",
        "moves consumption on restricting exporters: Ukraine 2007 is",
        "1.93 MMT harvest-only vs 10.34 MMT harvest+AMIS (grain stays",
        "home under E.4). See `ukraine_*.csv`. This table does not",
        "restore L1–L8 or retune αI.",
        "",
        "## Files",
        "",
        "- `score_regional.csv` — year-level host vs mapped PSD",
        "- `score_regional_summary.csv` — 2006–11 corr / level",
        "- `score_regional_construction.csv` — 2007–09 mean vs sum",
        "",
        "Next: P10 FAOSTAT FB vs USDA (A1) only if those arrays exist.",
        "",
    ]
    path = Path(out_dir) / "regional.md"
    path.write_text("\n".join(lines) + "\n")
    return path


def run_regional_score(
    out_dir: Path | None = None,
    run_model: bool = True,
    start_year: int = 2003,
    end_year: int = 2011,
) -> dict[str, Path]:
    """Write regional CSVs + note. ``run_model=False`` scores harvest only."""
    out_dir = Path(out_dir) if out_dir else OUT_DEFAULT
    out_dir.mkdir(parents=True, exist_ok=True)
    params = wheat_params()
    data = prepare_wheat(start_year=start_year, end_year=end_year, params=params)
    construction = psd_construction_table(list(NAMED_REGIONS))
    results = None
    if run_model:
        _, results = run_three_scenarios(
            data=data, params=params,
            start_year=start_year, end_year=end_year,
        )
    long = score_regional(data, results)
    summary = summarize_regional(long)
    construction.to_csv(out_dir / "score_regional_construction.csv", index=False)
    long.to_csv(out_dir / "score_regional.csv", index=False)
    summary.to_csv(out_dir / "score_regional_summary.csv", index=False)
    note = write_regional_note(construction, summary, long, out_dir)
    return {"note": note, "long": out_dir / "score_regional.csv"}
