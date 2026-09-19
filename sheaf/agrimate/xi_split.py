"""R4: characterise undisturbed xd/xi wander. Does not pin. Does not retune.

Item 3: host 2011/2006 last/first ≈ 1.63 vs author 1.004. B1 delivery did
not move p_w. Candidates (labelled probes, defaults unchanged): xmin
penalty (ζ=1 off), Jacobi D.22 q_oth EMA (frozen), rolling-year replan
(calendar stride=24). No decay knob. No L1–L8.
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

from .fig4 import AUTHOR_DIR, author_undisturbed_drift, load_author_fig4
from .fig4_config import PROTECTED_THREE_SCENARIO, _last_first
from .model import AgrimateResult, run_agrimate
from .params import wheat_params
from .validation import OUT_DEFAULT, monthly_price, step_years
from .wheat_data import prepare_wheat

START_YEAR = 2003
END_YEAR = 2011
SCORE_START = 2006
SCORE_END = 2011
ROOT = Path(__file__).resolve().parents[2]
DISPATCH = ROOT / "diagnostics" / "GATE0_REPRO_DISPATCH.md"


def annual_xd_xi(result: AgrimateResult) -> pd.DataFrame:
    years = step_years(result)
    xd = result.sold_domestic
    xi = result.xi_ship
    rows = []
    for y in range(result.start_year, result.end_year + 1):
        m = years == y
        x_d = float(xd[:, m].sum()) if xd is not None else float("nan")
        x_i = float(xi[:, m].sum()) if xi is not None else float("nan")
        tot = x_d + x_i
        rows.append({
            "year": y,
            "xd": x_d,
            "xi": x_i,
            "split_xi": x_i / tot if tot else float("nan"),
            "price_index_mean": float(result.price_index[m].mean()),
            "S_producer_end": float(result.S_producer[:, int(np.where(m)[0][-1])].sum()),
        })
    return pd.DataFrame(rows)


def last_first_index(result: AgrimateResult, start: int = SCORE_START,
                     end: int = SCORE_END) -> float:
    p = monthly_price(result, field="price_index")
    s = p[(p.index.year >= start) & (p.index.year <= end)]
    return _last_first(s)


def _probe_specs() -> list[dict]:
    p = wheat_params()
    return [
        {
            "label": "default",
            "params": p,
            "replan_stride": 1,
            "freeze_q_oth": False,
            "candidate": "host (Jacobi + rolling + xmin on)",
        },
        {
            "label": "xmin_off",
            "params": replace(p, zeta_penalty=1.0),
            "replan_stride": 1,
            "freeze_q_oth": False,
            "candidate": "xmin penalty off (ζ=1)",
        },
        {
            "label": "qoth_freeze",
            "params": p,
            "replan_stride": 1,
            "freeze_q_oth": True,
            "candidate": "Jacobi D.22 q_oth frozen",
        },
        {
            "label": "calendar_replan",
            "params": p,
            "replan_stride": 24,
            "freeze_q_oth": False,
            "candidate": "rolling year off (January replan)",
        },
    ]


def _xi_range(ann: pd.DataFrame, y0: int = 2004, y1: int = 2011) -> dict:
    sub = ann[(ann["year"] >= y0) & (ann["year"] <= y1)]
    xi = sub["xi"].to_numpy(float)
    lo, hi = float(np.min(xi)), float(np.max(xi))
    mean = float(np.mean(xi))
    return {
        "xi_min": lo,
        "xi_max": hi,
        "xi_mean": mean,
        "xi_range": hi - lo,
        "xi_range_over_mean": (hi - lo) / mean if mean else float("nan"),
    }


def run_xi_split_probes(
    start_year: int = START_YEAR,
    end_year: int = END_YEAR,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    data = prepare_wheat(start_year=start_year, end_year=end_year,
                         params=wheat_params())
    annual_rows = []
    summaries = []
    author = author_undisturbed_drift(
        load_author_fig4(AUTHOR_DIR)["monthly"], SCORE_START, SCORE_END)
    for spec in _probe_specs():
        res = run_agrimate(
            data=data, params=spec["params"],
            use_anomalies=False, use_restrictions=False,
            start_year=start_year, end_year=end_year,
            replan_stride=spec["replan_stride"],
            freeze_q_oth=spec["freeze_q_oth"],
        )
        ann = annual_xd_xi(res)
        lf = last_first_index(res)
        xr = _xi_range(ann)
        n_steps = int(res.price_index.size)
        stride = int(spec["replan_stride"])
        n_solves = int(len(res.regions) * ((n_steps + stride - 1) // stride))
        for _, row in ann.iterrows():
            annual_rows.append({
                "label": spec["label"],
                **{k: row[k] for k in ann.columns},
            })
        summaries.append({
            "label": spec["label"],
            "candidate": spec["candidate"],
            "last_first": lf,
            "last_first_author": float(author["last_over_first"]),
            "failed": int(res.failed_solves),
            "unconverged": int(res.unconverged_solves),
            "n_solves": n_solves,
            "floor_binds": int(res.floor_binds),
            "runtime_s": float(res.runtime_s),
            "zeta_penalty": float(spec["params"].zeta_penalty),
            "replan_stride": stride,
            "freeze_q_oth": bool(spec["freeze_q_oth"]),
            **xr,
        })
    summary = pd.DataFrame(summaries)
    annual = pd.DataFrame(annual_rows)
    return annual, summary, author


def _fmt(x, nd: int = 3) -> str:
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "nan"
    return f"{float(x):.{nd}f}"


def _closest_probe(summary: pd.DataFrame) -> str:
    """Nearest labelled probe to author last/first. Not an adoption."""
    author = float(summary["last_first_author"].iloc[0])
    probes = summary[summary["label"] != "default"]
    gap = (probes["last_first"] - author).abs()
    i = int(gap.idxmin())
    return str(probes.loc[i, "label"])


def _wander_verdict(summary: pd.DataFrame) -> tuple[str, str]:
    """One-sentence wander report + why-line. Does not adopt a pin."""
    d = summary[summary["label"] == "default"].iloc[0]
    author = float(d["last_first_author"])
    host = float(d["last_first"])
    recoverers, movers, inert = [], [], []
    for _, r in summary.iterrows():
        if r["label"] == "default":
            continue
        lf = float(r["last_first"])
        name = str(r["label"])
        if abs(lf - author) < 0.05:
            recoverers.append(name)
        elif abs(lf - host) > 0.05:
            movers.append(f"{name} {_fmt(lf, 3)}")
        else:
            inert.append(name)
    if recoverers:
        who = ", ".join(recoverers)
        verdict = (
            f"{who} alone brings last/first to ≈ author 1.004 on this "
            "window. That is the wander *on this labelled probe*. "
            "Not adopted. Do not pin. Do not write it into wheat_params()."
        )
        why = (
            f"{who} recovers last/first on the probe; host default still "
            f"{_fmt(host, 3)}; do not pin"
        )
    elif movers:
        who = "; ".join(movers)
        inert_s = ", ".join(inert) if inert else "none"
        verdict = (
            f"Movers vs default: {who}. Inert: {inert_s}. No single "
            "labelled switch recovers author last/first. The wander is "
            "not xmin, q_oth EMA, or calendar replan *alone*. Do not add "
            "a decay knob. Do not restore L1–L8."
        )
        why = (
            "item 3 still fails; no single probe is Agrimate last/first; "
            "do not pin"
        )
    else:
        verdict = (
            "xmin_off, qoth_freeze, and calendar_replan are all inert on "
            "last/first (stay at the 1.63 host figure). Jacobi D.22 EMA, "
            "rolling year, and xmin penalty are not the wander *alone*. "
            "Do not add a decay knob. Do not restore L1–L8."
        )
        why = (
            "item 3 still fails; Jacobi/rolling/xmin probes inert; do not pin"
        )
    return verdict, why


def write_xi_split_note(annual: pd.DataFrame, summary: pd.DataFrame,
                        author: dict, out_dir: Path) -> Path:
    d = summary[summary["label"] == "default"].iloc[0]
    closest = _closest_probe(summary)
    verdict, _why = _wander_verdict(summary)
    host_xi = annual[annual["label"] == "default"]
    p = wheat_params()
    lines = [
        "# R4 — Undisturbed xd/xi split",
        "",
        "Item 3 still fails. Characterisation only. **Not a pin.**",
        f"`wheat_params()` stay αI={p.alpha_i:g}, ζ={p.zeta_penalty:g},",
        f"N_for={p.n_for_months:g}, xmin={p.xmin_share:g}. Fig. 4 knobs",
        "are not adopted. L1–L8 stay rejected. No decay knob.",
        "G1/G2 stay blocked. B1 delivery did not move p_w.",
        "",
        "Undisturbed 2003–11 (repeating H, no AMIS). Score window",
        f"**{SCORE_START}–{SCORE_END}** last/first of the annual-mean",
        "price index. Author Fig. 4 baseline last/first = "
        f"{_fmt(author['last_over_first'], 3)}.",
        "",
        "## Annual XI / XD on the default host",
        "",
        "H*=C* every year. Inverse-demand floor binds "
        f"{int(d['floor_binds'])} times. Annual international sales still",
        "wander under constant H:",
        "",
        "| year | XD MMT | XI MMT | XI/(XD+XI) | p_w mean | S_p end |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for _, r in host_xi.iterrows():
        lines.append(
            f"| {int(r['year'])} | {_fmt(r['xd'], 1)} | {_fmt(r['xi'], 1)} | "
            f"{_fmt(r['split_xi'], 3)} | {_fmt(r['price_index_mean'], 3)} | "
            f"{_fmt(r['S_producer_end'], 1)} |"
        )
    lines += [
        "",
        f"XI range 2004–11: {_fmt(d['xi_min'], 1)}–{_fmt(d['xi_max'], 1)} MMT "
        f"(span {_fmt(d['xi_range'], 1)}; "
        f"{_fmt(d['xi_range_over_mean'], 2)}× mean). That is the open",
        "price-mean channel (`undisturbed.md`).",
        "",
        "## Labelled probes (not adopted)",
        "",
        "Each probe is the default host with **one** candidate switched.",
        "Defaults recover the live path (`replan_stride=1`, `freeze_q_oth=False`,",
        "ζ=0).",
        "",
        "| label | candidate | last/first | XI span MMT | unconverged | failed |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for _, r in summary.iterrows():
        lines.append(
            f"| {r['label']} | {r['candidate']} | {_fmt(r['last_first'], 3)} | "
            f"{_fmt(r['xi_range'], 1)} | {int(r['unconverged'])}/"
            f"{int(r['n_solves'])} | {int(r['failed'])} |"
        )
    lines += [
        "",
        f"Author last/first = {_fmt(d['last_first_author'], 3)}. Host default = "
        f"{_fmt(d['last_first'], 3)} (the 1.63 figure).",
        f"Nearest labelled probe: **{closest}** (not adopted).",
        "",
        f"Reading: {verdict}",
        "",
        "Rolling year under constant H only changes how often S_p / q_oth",
        "are fed into a new programme; harvest itself is already periodic.",
        "Do not add a decay knob to force last/first = 1. Do not restore",
        "L1–L8. Do not pin.",
        "",
        "**Next paste: R5.** Item 3 remains open on the live host after",
        "this characterisation. S4 x1=demand is the next labelled",
        "experiment. R4 does not unlock G1.",
        "",
    ]
    path = out_dir / "xi_split.md"
    path.write_text("\n".join(lines))
    return path


def write_r4_dispatch(summary: pd.DataFrame, path: Path | None = None) -> Path:
    path = Path(path) if path else DISPATCH
    d = summary[summary["label"] == "default"].iloc[0]
    closest = _closest_probe(summary)
    c = summary[summary["label"] == closest].iloc[0]
    _verdict, why = _wander_verdict(summary)
    body = "\n".join([
        "# Gate 0 reproduction dispatch",
        "",
        "Living next-paste. Rewrite after every R-session from **that run’s",
        "numbers**. Do not walk R3…R12 in order. Template:",
        "`GATE0_REPRO_PROMPTS.md` (Adaptive rule).",
        "",
        "```",
        "Last completed: R4",
        "Window / scenario: 2003–11 undisturbed xd/xi (score 2006–11)",
        "hike_2008 (default → knobs → author): ×2.31 → ×2.22 → ×1.62",
        "moy max/min: 26.8× → 13.3× → 1.51×",
        f"undisturbed last/first: default {_fmt(d['last_first'], 3)} → "
        f"nearest probe {closest} {_fmt(c['last_first'], 3)} → "
        f"author {_fmt(d['last_first_author'], 3)}",
        f"unconverged / failed: default {int(d['unconverged'])}/"
        f"{int(d['n_solves'])} failed={int(d['failed'])}",
        "What you could set / could not set: xmin_off / qoth_freeze / "
        "calendar_replan labelled; no decay knob; remaining A7",
        "Next paste: R5",
        f"Why: {why}",
        "Skip: R11; G1/G2; do not adopt knobs; do not add a decay knob",
        "```",
    ])
    path.write_text(body + "\n")
    return path


def run_xi_split_score(out_dir: Path | None = None) -> dict[str, Path]:
    out_dir = Path(out_dir) if out_dir else OUT_DEFAULT
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in PROTECTED_THREE_SCENARIO:
        assert (out_dir / name).is_file(), name
    before = {name: (out_dir / name).read_bytes() for name in PROTECTED_THREE_SCENARIO}
    annual, summary, author = run_xi_split_probes()
    annual_path = out_dir / "xi_split_annual.csv"
    summary_path = out_dir / "score_xi_split.csv"
    annual.to_csv(annual_path, index=False)
    summary.to_csv(summary_path, index=False)
    note = write_xi_split_note(annual, summary, author, out_dir)
    dispatch = write_r4_dispatch(summary)
    after = {name: (out_dir / name).read_bytes() for name in PROTECTED_THREE_SCENARIO}
    assert before == after, "R4 must not overwrite 2003–11 three-scenario CSVs"
    assert wheat_params().zeta_penalty == 0.0
    assert wheat_params().alpha_i == 3.2
    return {
        "note": note, "annual": annual_path, "csv": summary_path,
        "dispatch": dispatch,
    }
