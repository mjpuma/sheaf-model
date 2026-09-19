"""R2: labelled Fig. 4-config comparison. Does not replace wheat_params().

A7: Zenodo 10688435 main_output is AgrimateEU28+Egypt, FAO anomalies,
α_foreign=3.5, ζ=1, N_for=6, start 2000, git old-demand-dynamics.
This module sets the knobs that live on AgrimateParams and scores a
short 2006–08 harvest+AMIS (and undisturbed) against wheat_params()
on the same USDA WheatData. It does not adopt those knobs as defaults,
does not restore L1–L8, and does not overwrite the 2003–11 three-scenario
CSVs.
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

from .equations import alpha_domestic_d10
from .faostat_fb import inventory as faostat_inventory
from .fig4 import AUTHOR_DIR, author_undisturbed_drift, load_author_fig4
from .model import AgrimateResult, run_agrimate
from .params import AgrimateParams, fig4_experiment_params, wheat_params
from .regions import D9_ALPHA, REGION_NAMES
from .validation import OUT_DEFAULT, _hike, monthly_price
from .wheat_data import WheatData, prepare_wheat

START_YEAR = 2006
END_YEAR = 2008

CAN_SET = (
    "alpha_i=3.5",
    "alpha_nash=3.0",
    "zeta_penalty=1.0",
    "n_for_months=6",
)

CANNOT_SET = (
    "FAOSTAT Food Balances (A1)",
    "AgrimateEU28 + Egypt extra (host is AgrimateRegionsWheat: EU-27, Brazil named, Egypt in Northern Africa)",
    "start 2000-01-01",
    "FAO production anomalies since 2005",
    "git old-demand-dynamics",
    "Zenodo 14022004 author Julia",
)

PROTECTED_THREE_SCENARIO = (
    "prices_three_scenarios.csv",
    "score_prices.csv",
    "score_supply_stocks.csv",
    "annual_undisturbed.csv",
    "annual_harvest.csv",
    "annual_harvest_amis.csv",
)


def fig4_experiment_region_path(path: Path | str | None = None) -> Path | None:
    """Optional FAO/EU28 data path. None until those arrays are vendored.

    A caller may pass a directory; if it does not contain AgrimateEU28
    plus FAO Food Balances, this still returns None (A1 / A7).
    """
    if path is None:
        return None
    folder = Path(path)
    if not folder.is_dir():
        return None
    names = {p.name.lower() for p in folder.iterdir() if p.is_file()}
    has_fb = any("food_balance" in n or n.endswith("fbs.csv") for n in names)
    has_eu28 = any("eu28" in n or "agrimateeu28" in n for n in names)
    if has_fb and has_eu28:
        return folder
    return None


def apply_alpha_i(data: WheatData, alpha_i: float) -> WheatData:
    """Keep USDA H/C/S/E0/AMIS; apply D.10 residual αD for this αI.

    Tbl. D.9 named-exporter αD stays the D.9 numbers (not scaled).
    """
    alpha_d = np.array([
        D9_ALPHA[r] if r in D9_ALPHA else alpha_domestic_d10(
            alpha_i, float(data.XI_star[i]), float(data.XI_world))
        for i, r in enumerate(data.regions)
    ], dtype=float)
    return replace(data, alpha_d=alpha_d)


def _wheat_params_are_14022004() -> bool:
    p = wheat_params()
    return (
        p.alpha_i == 3.2
        and p.zeta_penalty == 0.0
        and p.n_for_months == 3
        and p.p_sto_annual == 0.1
        and p.xmin_share == 0.2
    )


def what_is_settable() -> dict:
    """Label A7: what R2 can copy vs what is still missing."""
    fb = faostat_inventory()
    return {
        "can_set": list(CAN_SET),
        "cannot_set": list(CANNOT_SET),
        "region_path": fig4_experiment_region_path(),
        "n_host_regions": len(REGION_NAMES),
        "host_has_egypt_node": "Egypt" in REGION_NAMES,
        "host_has_eu28": "EU-28" in REGION_NAMES,
        "faostat_fb_files": list(fb["food_balance_files"]),
        "usda_is_default": bool(fb["usda_is_default"]),
        "author_julia_in_repo": False,
        "wheat_params_unchanged": _wheat_params_are_14022004(),
    }


def _moy_maxmin(s: pd.Series) -> float:
    g = s.groupby(s.index.month).mean()
    lo = float(g.min())
    return float(g.max() / lo) if lo and np.isfinite(lo) else float("nan")


def _last_first(s: pd.Series) -> float:
    years = sorted({int(y) for y in s.index.year})
    if len(years) < 2:
        return float("nan")
    first = float(s[s.index.year == years[0]].mean())
    last = float(s[s.index.year == years[-1]].mean())
    return last / first if first and np.isfinite(first) else float("nan")


def _author_monthly(scenario: str, start: int, end: int) -> pd.Series:
    monthly = load_author_fig4(AUTHOR_DIR)["monthly"]
    sub = monthly[monthly["scenario"] == scenario]
    s = pd.Series(
        sub["wm_price_index"].to_numpy(float),
        index=pd.PeriodIndex(
            [pd.Period(year=int(y), month=int(m), freq="M")
             for y, m in zip(sub["year"], sub["month"])],
            freq="M",
        ),
        name="author_index",
    )
    return s[(s.index.year >= start) & (s.index.year <= end)]


def _score_run(
    label: str,
    scenario: str,
    params: AgrimateParams,
    result: AgrimateResult,
    author: pd.Series,
) -> dict:
    p = monthly_price(result)
    window = p[(p.index.year >= START_YEAR) & (p.index.year <= END_YEAR)]
    n_solves = len(result.regions) * int(result.price_index.size)
    return {
        "label": label,
        "scenario": scenario,
        "alpha_i": float(params.alpha_i),
        "alpha_nash": float(params.alpha_nash),
        "zeta_penalty": float(params.zeta_penalty),
        "n_for_months": int(params.n_for_months),
        "p_sto_annual": float(params.p_sto_annual),
        "xmin_share": float(params.xmin_share),
        "hike_2008": _hike(window, START_YEAR, 2008),
        "hike_2008_author": _hike(author, START_YEAR, 2008),
        "moy_maxmin": _moy_maxmin(window),
        "moy_maxmin_author": _moy_maxmin(author),
        "last_first": _last_first(window),
        "mean_2006_usd": float(window[window.index.year == START_YEAR].mean())
        if (window.index.year == START_YEAR).any() else float("nan"),
        "pidx_min": float(np.nanmin(result.price_index)),
        "pidx_max": float(np.nanmax(result.price_index)),
        "failed": int(result.failed_solves),
        "unconverged": int(result.unconverged_solves),
        "n_solves": int(n_solves),
        "runtime_s": float(result.runtime_s),
    }


def run_fig4_config_comparison(
    start_year: int = START_YEAR,
    end_year: int = END_YEAR,
) -> tuple[WheatData, pd.DataFrame]:
    """Same USDA WheatData; default vs Fig. 4 knobs. Short window."""
    default = wheat_params()
    fig4 = fig4_experiment_params()
    data = prepare_wheat(start_year=start_year, end_year=end_year, params=default)
    data_default = apply_alpha_i(data, default.alpha_i)
    data_fig4 = apply_alpha_i(data, fig4.alpha_i)
    rows = []
    for label, params, wheat in (
        ("default", default, data_default),
        ("fig4_knobs", fig4, data_fig4),
    ):
        for scenario, anomalies, restrictions in (
            ("harvest_amis", True, True),
            ("undisturbed", False, False),
        ):
            res = run_agrimate(
                data=wheat, params=params,
                use_anomalies=anomalies, use_restrictions=restrictions,
                start_year=start_year, end_year=end_year,
            )
            author = _author_monthly(scenario, start_year, end_year)
            rows.append(_score_run(label, scenario, params, res, author))
    return data, pd.DataFrame(rows)


def knobs_moved_fig4_metrics(summary: pd.DataFrame) -> dict[str, float | bool]:
    """Adaptive-table inputs. Hike toward ×1.62 or moy max/min down by ≥2."""
    ha = summary[(summary["scenario"] == "harvest_amis")]
    d = ha[ha["label"] == "default"].iloc[0]
    c = ha[ha["label"] == "fig4_knobs"].iloc[0]
    hike_d = float(d["hike_2008"])
    hike_c = float(c["hike_2008"])
    moy_d = float(d["moy_maxmin"])
    moy_c = float(c["moy_maxmin"])
    author_h = float(d["hike_2008_author"])
    toward_hike = (
        abs(hike_c - author_h) + 1e-9 < abs(hike_d - author_h)
        and abs(hike_c - hike_d) >= 0.10
    )
    moy_drop = (moy_d - moy_c) >= 2.0
    barely = (abs(hike_c - hike_d) < 0.10) and ((moy_d - moy_c) < 2.0)
    return {
        "hike_default": hike_d,
        "hike_comparison": hike_c,
        "hike_author": author_h,
        "moy_default": moy_d,
        "moy_comparison": moy_c,
        "moy_author": float(d["moy_maxmin_author"]),
        "toward_hike": toward_hike,
        "moy_drop_ge2": moy_drop,
        "barely_moved": barely,
        "moved": toward_hike or moy_drop,
    }


def choose_next_paste(summary: pd.DataFrame) -> tuple[str, str]:
    """First-match adaptive table from GATE0_REPRO_PROMPTS.md."""
    moved = knobs_moved_fig4_metrics(summary)
    und = summary[(summary["scenario"] == "undisturbed")
                  & (summary["label"] == "fig4_knobs")]
    last_first = float(und.iloc[0]["last_first"]) if not und.empty else float("nan")
    if moved["moved"]:
        return "R10", (
            "Fig. 4 knobs moved hike toward ×1.62 or cut moy max/min by ≥2; "
            "score vs author series before treating it as a win."
        )
    why = (
        "Knobs ran on USDA/EU-27; hike/amplitude did not close Fig. 4. "
        "Item 3 / XI split is next."
    )
    if np.isfinite(last_first) and last_first > 1.1:
        why = (
            "Fig. 4 knobs did not remove undisturbed wander "
            f"(last/first {last_first:.3f} on 2006–08). Characterise XI split."
        )
    return "R4", why


def _fmt(x, nd: int = 2) -> str:
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "nan"
    return f"{float(x):.{nd}f}"


def _row(summary: pd.DataFrame, label: str, scenario: str) -> pd.Series:
    return summary[(summary["label"] == label)
                   & (summary["scenario"] == scenario)].iloc[0]


def write_fig4_config_note(summary: pd.DataFrame, out_dir: Path) -> Path:
    avail = what_is_settable()
    ha_d = _row(summary, "default", "harvest_amis")
    ha_c = _row(summary, "fig4_knobs", "harvest_amis")
    un_d = _row(summary, "default", "undisturbed")
    un_c = _row(summary, "fig4_knobs", "undisturbed")
    moved = knobs_moved_fig4_metrics(summary)
    next_id, why = choose_next_paste(summary)
    author_drift = author_undisturbed_drift(
        load_author_fig4(AUTHOR_DIR)["monthly"], START_YEAR, END_YEAR)
    n_solves = int(ha_d["n_solves"])
    lines = [
        "# Fig. 4-config comparison (R2)",
        "",
        "Labelled comparison. **Not a retune.** `wheat_params()` stay",
        "αI=3.2, ζ=0, N_for=3. Fig. 4 knobs live on",
        "`fig4_experiment_params()` (αI=3.5, ζ=1, N_for=6).",
        "L1–L8 stay rejected. Bai α_foreign=10 is not adopted.",
        "Unforced price is not pinned. G1/G2 stay blocked.",
        "USDA 27-node WheatData is unchanged (A1).",
        "",
        f"Window **{START_YEAR}–{END_YEAR}** harvest+AMIS and undisturbed.",
        "Does **not** overwrite 2003–11 three-scenario CSVs.",
        "",
        "## What this object can set",
        "",
        ", ".join(avail["can_set"]) + ".",
        "",
        "## What this object cannot set",
        "",
    ]
    for item in avail["cannot_set"]:
        lines.append(f"- {item}")
    lines += [
        "",
        f"Optional region/data path: `{avail['region_path']}` "
        f"(host Egypt node={avail['host_has_egypt_node']}, "
        f"EU-28={avail['host_has_eu28']}; FAO FB files="
        f"{avail['faostat_fb_files'] or 'none'}).",
        "",
        "## 2006–08 scores",
        "",
        "| label | scenario | hike_2008 | moy max/min | last/first | "
        "unconverged | failed | 2006 mean USD |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for _, r in summary.iterrows():
        lines.append(
            f"| {r['label']} | {r['scenario']} | ×{_fmt(r['hike_2008'])} | "
            f"{_fmt(r['moy_maxmin'], 1)}× | {_fmt(r['last_first'], 3)} | "
            f"{int(r['unconverged'])}/{int(r['n_solves'])} | "
            f"{int(r['failed'])} | {_fmt(r['mean_2006_usd'], 1)} |"
        )
    lines += [
        "",
        f"Author harvest+AMIS on this window: hike ×{_fmt(ha_d['hike_2008_author'])}, "
        f"moy {_fmt(ha_d['moy_maxmin_author'], 2)}×. Author undisturbed "
        f"last/first {START_YEAR}–{END_YEAR} = "
        f"{_fmt(author_drift['last_over_first'], 3)}.",
        "",
        "Default vs Fig. 4 knobs (harvest+AMIS): hike "
        f"×{_fmt(ha_d['hike_2008'])} → ×{_fmt(ha_c['hike_2008'])} "
        f"(author ×{_fmt(ha_d['hike_2008_author'])}); moy "
        f"{_fmt(ha_d['moy_maxmin'], 1)}× → {_fmt(ha_c['moy_maxmin'], 1)}× "
        f"(author {_fmt(ha_d['moy_maxmin_author'], 2)}×). "
        f"toward_hike={moved['toward_hike']}; "
        f"moy_drop_ge2={moved['moy_drop_ge2']}; "
        f"barely_moved={moved['barely_moved']}.",
        "",
        "Undisturbed last/first on this short window: default "
        f"{_fmt(un_d['last_first'], 3)} → knobs {_fmt(un_c['last_first'], 3)} "
        f"(author {_fmt(author_drift['last_over_first'], 3)}). "
        "This is **not** the 2006–11 1.630 figure; do not pin.",
        "",
        f"Unconverged harvest+AMIS: default {int(ha_d['unconverged'])}/{n_solves} "
        f"(failed={int(ha_d['failed'])}); knobs "
        f"{int(ha_c['unconverged'])}/{int(ha_c['n_solves'])} "
        f"(failed={int(ha_c['failed'])}).",
        "",
        f"**Next paste: {next_id}.** {why}",
        "",
        "Do not adopt `fig4_experiment_params()` as `wheat_params()`.",
        "Do not start G1.",
        "",
    ]
    path = out_dir / "fig4_config.md"
    path.write_text("\n".join(lines))
    return path


def write_dispatch(summary: pd.DataFrame,
                   path: Path | None = None) -> Path:
    path = Path(path) if path else (
        Path(__file__).resolve().parents[2] / "diagnostics" / "GATE0_REPRO_DISPATCH.md"
    )
    ha_d = _row(summary, "default", "harvest_amis")
    ha_c = _row(summary, "fig4_knobs", "harvest_amis")
    un_c = _row(summary, "fig4_knobs", "undisturbed")
    un_d = _row(summary, "default", "undisturbed")
    next_id, why = choose_next_paste(summary)
    author_und = author_undisturbed_drift(
        load_author_fig4(AUTHOR_DIR)["monthly"], START_YEAR, END_YEAR)
    skip = "R11 (defaults unchanged); G1/G2; R6 as a gate (obtain-or-leave)"
    if next_id == "R10":
        skip = "R11; G1/G2; R7 unless asked; R6 as a gate"
    body = "\n".join([
        "# Gate 0 reproduction dispatch",
        "",
        "Living next-paste. Rewrite after every R-session from **that run’s",
        "numbers**. Do not walk R3…R12 in order. Template:",
        "`GATE0_REPRO_PROMPTS.md` (Adaptive rule).",
        "",
        "```",
        "Last completed: R2",
        f"Window / scenario: {START_YEAR}–{END_YEAR} harvest+AMIS (+ undisturbed)",
        f"hike_2008 (default → comparison → author): "
        f"×{_fmt(ha_d['hike_2008'])} → ×{_fmt(ha_c['hike_2008'])} → "
        f"×{_fmt(ha_d['hike_2008_author'])}",
        f"moy max/min (default → comparison → author): "
        f"{_fmt(ha_d['moy_maxmin'], 1)}× → {_fmt(ha_c['moy_maxmin'], 1)}× → "
        f"{_fmt(ha_d['moy_maxmin_author'], 2)}×",
        f"undisturbed last/first (host default → knobs → author 2006–08): "
        f"{_fmt(un_d['last_first'], 3)} → {_fmt(un_c['last_first'], 3)} → "
        f"{_fmt(author_und['last_over_first'], 3)}",
        f"unconverged / failed: default {int(ha_d['unconverged'])}/{int(ha_d['n_solves'])} "
        f"failed={int(ha_d['failed'])}; knobs {int(ha_c['unconverged'])}/{int(ha_c['n_solves'])} "
        f"failed={int(ha_c['failed'])}",
        "What you could set / could not set: αI=3.5, ζ=1, N_for=6 set;",
        "  FAO FB / EU28+Egypt / start-2000 / FAO anomalies / old-demand-dynamics /",
        "  14022004 Julia still not in repo",
        f"Next paste: {next_id}",
        f"Why: {why}",
        f"Skip: {skip}",
        "```",
        "",
    ])
    path.write_text(body)
    return path


def run_fig4_config_score(out_dir: Path | None = None) -> dict[str, Path]:
    out_dir = Path(out_dir) if out_dir else OUT_DEFAULT
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in PROTECTED_THREE_SCENARIO:
        assert (out_dir / name).is_file(), name
    before = {name: (out_dir / name).read_bytes() for name in PROTECTED_THREE_SCENARIO}
    _data, summary = run_fig4_config_comparison()
    csv = out_dir / "score_fig4_config.csv"
    summary.to_csv(csv, index=False)
    note = write_fig4_config_note(summary, out_dir)
    dispatch = write_dispatch(summary)
    after = {name: (out_dir / name).read_bytes() for name in PROTECTED_THREE_SCENARIO}
    assert before == after, "R2 must not overwrite 2003–11 three-scenario CSVs"
    return {"note": note, "csv": csv, "dispatch": dispatch}
