"""R10: score the R2 Fig. 4-knob run against author_fig4/.

Reads ``score_fig4_config.csv`` (2006–08 harvest+AMIS and undisturbed).
Does **not** re-run the host, does not overwrite three-scenario CSVs,
and does not adopt ``fig4_experiment_params()`` as ``wheat_params()``.
FAO/EU28 remain cannot-set (A7). Pink Sheet is a side column, not an
adoption criterion.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from .fig4 import AUTHOR_DIR, author_undisturbed_drift, load_author_fig4
from .fig4_config import (
    CANNOT_SET,
    CAN_SET,
    END_YEAR,
    PROTECTED_THREE_SCENARIO,
    START_YEAR,
    _author_monthly,
    _fmt,
    _last_first,
    _row,
    what_is_settable,
)
from .params import wheat_params
from .validation import OUT_DEFAULT, pink_sheet_monthly

ROOT = Path(__file__).resolve().parents[2]
DISPATCH = ROOT / "diagnostics" / "GATE0_REPRO_DISPATCH.md"


def p0_2006() -> float:
    """2006 Pink mean. Unit scale for host USD → index. Not a path pin."""
    pink = pink_sheet_monthly()
    return float(pink[pink.index.year == 2006].mean())


def score_r2_against_author(
    summary: pd.DataFrame | None = None,
    out_dir: Path | None = None,
) -> pd.DataFrame:
    """Add author 2006 index and last/first to the R2 comparison table."""
    out_dir = Path(out_dir) if out_dir else OUT_DEFAULT
    if summary is None:
        csv = out_dir / "score_fig4_config.csv"
        if not csv.is_file():
            raise FileNotFoundError(csv)
        summary = pd.read_csv(csv)
    p0 = p0_2006()
    rows = []
    for _, r in summary.iterrows():
        scenario = str(r["scenario"])
        author = _author_monthly(scenario, START_YEAR, END_YEAR)
        a06 = author[author.index.year == START_YEAR]
        host_usd = float(r["mean_2006_usd"])
        rows.append({
            "label": r["label"],
            "scenario": scenario,
            "alpha_i": float(r["alpha_i"]),
            "zeta_penalty": float(r["zeta_penalty"]),
            "n_for_months": int(r["n_for_months"]),
            "hike_2008": float(r["hike_2008"]),
            "hike_2008_author": float(r["hike_2008_author"]),
            "moy_maxmin": float(r["moy_maxmin"]),
            "moy_maxmin_author": float(r["moy_maxmin_author"]),
            "last_first": float(r["last_first"]),
            "last_first_author": _last_first(author),
            "mean_2006_usd": host_usd,
            "mean_2006_index": host_usd / p0 if p0 else float("nan"),
            "mean_2006_author_index": float(a06.mean()) if len(a06) else float("nan"),
            "p0": p0,
            "failed": int(r["failed"]),
            "unconverged": int(r["unconverged"]),
            "n_solves": int(r["n_solves"]),
            "adopted": False,
        })
    return pd.DataFrame(rows)


def knobs_are_not_a_fig4_match(scored: pd.DataFrame) -> dict[str, float | bool]:
    """R10 verdict on the knobs we could set. Remaining A7 still open."""
    ha = _row(scored, "fig4_knobs", "harvest_amis")
    d = _row(scored, "default", "harvest_amis")
    un = _row(scored, "fig4_knobs", "undisturbed")
    hike_gap = abs(float(ha["hike_2008"]) - float(ha["hike_2008_author"]))
    moy_gap = abs(float(ha["moy_maxmin"]) - float(ha["moy_maxmin_author"]))
    index_gap = abs(float(ha["mean_2006_index"]) - float(ha["mean_2006_author_index"]))
    return {
        "hike_knobs": float(ha["hike_2008"]),
        "hike_default": float(d["hike_2008"]),
        "hike_author": float(ha["hike_2008_author"]),
        "moy_knobs": float(ha["moy_maxmin"]),
        "moy_default": float(d["moy_maxmin"]),
        "moy_author": float(ha["moy_maxmin_author"]),
        "index_knobs": float(ha["mean_2006_index"]),
        "index_default": float(d["mean_2006_index"]),
        "index_author": float(ha["mean_2006_author_index"]),
        "und_last_first_knobs": float(un["last_first"]),
        "und_last_first_author": float(un["last_first_author"]),
        "hike_still_above_author": float(ha["hike_2008"]) > float(ha["hike_2008_author"]),
        "moy_still_above_author": float(ha["moy_maxmin"]) > 3.0,
        "quiet_year_not_closer": index_gap + 1e-9 >= abs(
            float(d["mean_2006_index"]) - float(d["mean_2006_author_index"])
        ),
        "match": hike_gap < 0.15 and moy_gap < 1.0 and index_gap < 0.15,
        "adopted": False,
    }


def write_fig4_author_score_note(scored: pd.DataFrame, out_dir: Path) -> Path:
    avail = what_is_settable()
    ha_d = _row(scored, "default", "harvest_amis")
    ha_c = _row(scored, "fig4_knobs", "harvest_amis")
    un_d = _row(scored, "default", "undisturbed")
    un_c = _row(scored, "fig4_knobs", "undisturbed")
    verdict = knobs_are_not_a_fig4_match(scored)
    author_und = author_undisturbed_drift(
        load_author_fig4(AUTHOR_DIR)["monthly"], START_YEAR, END_YEAR)
    p = wheat_params()
    lines = [
        "# Fig. 4 knobs vs author series (R10)",
        "",
        "Scores the **R2 comparison run** (2006–08, USDA 27-node WheatData,",
        "`fig4_experiment_params()`) against `author_fig4/`. Does **not**",
        "re-run the 2003–11 three-scenario host. **Not a retune.**",
        f"`wheat_params()` stay αI={p.alpha_i:g}, ζ={p.zeta_penalty:g},",
        f"N_for={p.n_for_months:g}. Bai α_foreign=10 is not adopted.",
        "L1–L8 stay rejected. Unforced price is not pinned. G1/G2 stay blocked.",
        "",
        "Window is **2006–2008 with no 2003 spin-up**. P7/P8 2006–11 numbers",
        "(harvest+AMIS 2006 index 0.306, hike ×4.54, moy 17.8×, undisturbed",
        "last/first 1.63) are a different path. Do not mix them.",
        "",
        "## What was scored (settable knobs)",
        "",
        ", ".join(CAN_SET) + ".",
        "",
        "## Remaining A7 (cannot set)",
        "",
    ]
    for item in CANNOT_SET:
        lines.append(f"- {item}")
    lines += [
        "",
        f"Optional region/data path: `{avail['region_path']}` "
        f"(Egypt node={avail['host_has_egypt_node']}, "
        f"EU-28={avail['host_has_eu28']}; FAO FB files="
        f"{avail['faostat_fb_files'] or 'none'}).",
        "",
        "## 2006–08 vs author_fig4",
        "",
        "Host index = 2006 mean USD / p0 (p0 = 2006 Pink mean, unit scale).",
        "Author index is `wm_price_index` on the same months. Not a 2006 pin.",
        "",
        "| label | scenario | 2006 index | 2006 author | hike | hike author | "
        "moy | moy author | last/first | last/first author |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for _, r in scored.iterrows():
        lines.append(
            f"| {r['label']} | {r['scenario']} | "
            f"{_fmt(r['mean_2006_index'], 3)} | "
            f"{_fmt(r['mean_2006_author_index'], 3)} | "
            f"×{_fmt(r['hike_2008'])} | ×{_fmt(r['hike_2008_author'])} | "
            f"{_fmt(r['moy_maxmin'], 1)}× | {_fmt(r['moy_maxmin_author'], 2)}× | "
            f"{_fmt(r['last_first'], 3)} | {_fmt(r['last_first_author'], 3)} |"
        )
    pink06 = float(ha_c["p0"])
    lines += [
        "",
        "Harvest+AMIS (knobs we could set vs author vs same-window default):",
        f"- 2008 hike ×{_fmt(ha_c['hike_2008'])} vs author "
        f"×{_fmt(ha_c['hike_2008_author'])} (default ×{_fmt(ha_d['hike_2008'])}).",
        f"- Quiet-year index {_fmt(ha_c['mean_2006_index'], 3)} vs author "
        f"{_fmt(ha_c['mean_2006_author_index'], 3)} (default "
        f"{_fmt(ha_d['mean_2006_index'], 3)}). Knobs moved **away** from",
        "  the author quiet year.",
        f"- moy max/min {_fmt(ha_c['moy_maxmin'], 1)}× vs author "
        f"{_fmt(ha_c['moy_maxmin_author'], 2)}× (default "
        f"{_fmt(ha_d['moy_maxmin'], 1)}×). Toward author; still ~9× too large.",
        f"- Undisturbed last/first {_fmt(un_c['last_first'], 3)} vs author "
        f"{_fmt(author_und['last_over_first'], 3)} (default "
        f"{_fmt(un_d['last_first'], 3)}). Worse, not repeating.",
        "",
        f"Pink Sheet 2006 mean is ${_fmt(pink06, 1)}/t (side column).",
        f"Knobs 2006 USD ${_fmt(ha_c['mean_2006_usd'], 1)}/t "
        f"({_fmt(ha_c['mean_2006_index'], 2)}× Pink) vs default "
        f"${_fmt(ha_d['mean_2006_usd'], 1)}/t. Pink corr is **not** an",
        "adoption criterion. Knobs that move Pink are not adopted.",
        "",
        f"**match={verdict['match']}.** hike_still_above_author="
        f"{verdict['hike_still_above_author']}; "
        f"moy_still_above_author={verdict['moy_still_above_author']}; "
        f"quiet_year_not_closer={verdict['quiet_year_not_closer']}; "
        "adopted=False.",
        "",
        "Do not put αI=3.5 / ζ=1 / N_for=6 into `wheat_params()`.",
        "Do not restore L1–L8. Do not start G1.",
        "",
        "**Next paste: R9.** N5 on this comparison object (unconverged",
        f"{int(ha_c['unconverged'])}/{int(ha_c['n_solves'])} harvest+AMIS).",
        "Remaining A7 (FAO/EU28/start-2000/FAO anomalies/old-demand-dynamics)",
        "still blocks a full Fig. 4 executable. R4 still pending for item 3.",
        "",
    ]
    path = out_dir / "fig4_config_score.md"
    path.write_text("\n".join(lines))
    return path


def write_r10_dispatch(scored: pd.DataFrame, path: Path | None = None) -> Path:
    path = Path(path) if path else DISPATCH
    ha_d = _row(scored, "default", "harvest_amis")
    ha_c = _row(scored, "fig4_knobs", "harvest_amis")
    un_d = _row(scored, "default", "undisturbed")
    un_c = _row(scored, "fig4_knobs", "undisturbed")
    author_und = author_undisturbed_drift(
        load_author_fig4(AUTHOR_DIR)["monthly"], START_YEAR, END_YEAR)
    body = "\n".join([
        "# Gate 0 reproduction dispatch",
        "",
        "Living next-paste. Rewrite after every R-session from **that run’s",
        "numbers**. Do not walk R3…R12 in order. Template:",
        "`GATE0_REPRO_PROMPTS.md` (Adaptive rule).",
        "",
        "```",
        "Last completed: R10",
        f"Window / scenario: {START_YEAR}–{END_YEAR} fig4_knobs vs author_fig4",
        f"hike_2008 (default → knobs → author): "
        f"×{_fmt(ha_d['hike_2008'])} → ×{_fmt(ha_c['hike_2008'])} → "
        f"×{_fmt(ha_c['hike_2008_author'])}",
        f"moy max/min: {_fmt(ha_d['moy_maxmin'], 1)}× → "
        f"{_fmt(ha_c['moy_maxmin'], 1)}× → {_fmt(ha_c['moy_maxmin_author'], 2)}×",
        f"2006 index: {_fmt(ha_d['mean_2006_index'], 3)} → "
        f"{_fmt(ha_c['mean_2006_index'], 3)} → "
        f"{_fmt(ha_c['mean_2006_author_index'], 3)} (knobs moved away)",
        f"undisturbed last/first: {_fmt(un_d['last_first'], 3)} → "
        f"{_fmt(un_c['last_first'], 3)} → {_fmt(author_und['last_over_first'], 3)}",
        f"unconverged / failed: knobs {int(ha_c['unconverged'])}/"
        f"{int(ha_c['n_solves'])} failed={int(ha_c['failed'])}",
        "What you could set / could not set: αI=3.5, ζ=1, N_for=6 scored; remaining A7",
        "Next paste: R9",
        "Why: not a Fig. 4 match; do not adopt; N5 on this object next",
        "Skip: R11; G1/G2; R6 as a gate; do not adopt knobs for Pink",
        "```",
    ])
    path.write_text(body + "\n")
    return path


def run_fig4_author_score(out_dir: Path | None = None) -> dict[str, Path]:
    out_dir = Path(out_dir) if out_dir else OUT_DEFAULT
    for name in PROTECTED_THREE_SCENARIO:
        assert (out_dir / name).is_file(), name
    before = {name: (out_dir / name).read_bytes() for name in PROTECTED_THREE_SCENARIO}
    r2_csv = out_dir / "score_fig4_config.csv"
    assert r2_csv.is_file(), r2_csv
    scored = score_r2_against_author(out_dir=out_dir)
    csv = out_dir / "score_fig4_config_author.csv"
    scored.to_csv(csv, index=False)
    note = write_fig4_author_score_note(scored, out_dir)
    dispatch = write_r10_dispatch(scored)
    after = {name: (out_dir / name).read_bytes() for name in PROTECTED_THREE_SCENARIO}
    assert before == after, "R10 must not overwrite 2003–11 three-scenario CSVs"
    assert wheat_params().alpha_i == 3.2
    return {"note": note, "csv": csv, "dispatch": dispatch}
