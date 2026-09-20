"""R4: characterise undisturbed xd/xi wander. Does not pin. Does not retune.

Item 3: host 2011/2006 last/first ≈ 1.63 vs author 1.004. B1 delivery did
not move p_w. Candidates (labelled probes, defaults unchanged): xmin
penalty (ζ=1 off), Jacobi D.22 q_oth EMA (frozen), rolling-year replan
(calendar stride=24). No decay knob. No L1–L8.

S2: re-measure last/first on the S1 member-sum host from the existing
three-scenario prices. Still >1.1; no sourced D.22 variant. Label and
stop. freeze_q_oth stays diagnostic, default off, not wheat_params().
"""
from __future__ import annotations

from dataclasses import fields, replace
from pathlib import Path

import numpy as np
import pandas as pd

from .fig4 import AUTHOR_DIR, author_undisturbed_drift, load_author_fig4
from .fig4_config import PROTECTED_THREE_SCENARIO, _last_first
from .model import AgrimateResult, run_agrimate
from .params import AgrimateParams, wheat_params
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
    rec_why = []
    for _, r in summary.iterrows():
        if r["label"] == "default":
            continue
        lf = float(r["last_first"])
        name = str(r["label"])
        bit = f"{name} {_fmt(lf, 3)}"
        if abs(lf - author) < 0.05:
            recoverers.append(bit)
            rec_why.append(bit)
        elif abs(lf - host) > 0.05:
            movers.append(bit)
        else:
            inert.append(name)
    if recoverers:
        who = "; ".join(recoverers)
        extra = ""
        if movers:
            extra = f" Other probes move the wrong way ({'; '.join(movers)})."
        if inert:
            extra += f" Inert: {', '.join(inert)}."
        verdict = (
            f"{who} is within 0.05 of author {_fmt(author, 3)} on this "
            f"window.{extra} That is the last/first wander *on this labelled "
            "probe*, not a sourced Agrimate freeze: author D.22 still updates "
            "q_oth and still has last/first ≈ 1. Not adopted. Do not pin. "
            "Do not write freeze_q_oth into wheat_params()."
        )
        why = (
            f"{'; '.join(rec_why)} ≈ author {_fmt(author, 3)}; host still "
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
        "XI volume is not the last/first object: qoth_freeze still spans",
        f"{_fmt(summary.loc[summary['label']=='qoth_freeze', 'xi_min'].iloc[0], 1)}"
        f"–{_fmt(summary.loc[summary['label']=='qoth_freeze', 'xi_max'].iloc[0], 1)} "
        "MMT. The 2006–11 mean-price ratio is the D.7 offer mix under",
        "live vs frozen D.22. Author Agrimate updates q_oth; freezing it",
        "here is a diagnostic isolation, not a copy of the paper.",
        "xmin_off and calendar_replan each move last/first *below* 1",
        "(not a pin to 1). Calendar replan also zeros year-end S_p",
        "(N2's original reason for rolling year).",
        "",
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
    """Historical R4 writer. Does not clobber a moved living dispatch."""
    path = Path(path) if path else DISPATCH
    if path.is_file() and "Last completed: R4" not in path.read_text():
        return path
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


def n_julia_sources(root: Path | None = None) -> int:
    """Count in-tree author Julia. 14022004 is not vendored."""
    root = Path(root) if root else ROOT
    return sum(1 for p in root.rglob("*.jl") if ".git" not in p.parts)


def live_host_last_first(prices_path: Path | None = None) -> dict:
    """Undisturbed 2011/2006 last/first from the living three-scenario CSV.

    Does not re-run NLP. Does not freeze q_oth. Does not pin.
    """
    path = Path(prices_path) if prices_path else OUT_DEFAULT / "prices_three_scenarios.csv"
    df = pd.read_csv(path, index_col=0)
    idx = pd.PeriodIndex(df.index, freq="M")
    s = pd.Series(df["undisturbed"].to_numpy(float), index=idx)
    window = s[(s.index.year >= SCORE_START) & (s.index.year <= SCORE_END)]
    first = float(window[window.index.year == SCORE_START].mean())
    last = float(window[window.index.year == SCORE_END].mean())
    author = author_undisturbed_drift(
        load_author_fig4(AUTHOR_DIR)["monthly"], SCORE_START, SCORE_END)
    p = wheat_params()
    param_names = {f.name for f in fields(AgrimateParams)}
    return {
        "last_first": _last_first(window),
        "mean_first_usd": first,
        "mean_last_usd": last,
        "last_first_author": float(author["last_over_first"]),
        "author_first": float(author["annual_mean_first"]),
        "author_last": float(author["annual_mean_last"]),
        "n_julia": n_julia_sources(),
        "freeze_q_oth_on_params": "freeze_q_oth" in param_names,
        "alpha_i": p.alpha_i,
        "zeta_penalty": p.zeta_penalty,
        "n_for_months": p.n_for_months,
        "p_sto_annual": p.p_sto_annual,
        "xmin_share": p.xmin_share,
        "pre_s1_last_first": 1.630,
        "r4_freeze_last_first": 1.019,
    }


def write_s2_item3_note(metrics: dict, out_dir: Path) -> Path:
    """Label item 3 on the member-sum host. Does not adopt freeze."""
    p = wheat_params()
    lf = float(metrics["last_first"])
    author = float(metrics["last_first_author"])
    lines = [
        "# S2 — Item 3 re-measure on the A8 member-sum host",
        "",
        "Not a pin. Not a freeze. Not a decay knob. Not L1–L8. Not an αI",
        f"retune. `wheat_params()` stay αI={p.alpha_i:g}, ζ={p.zeta_penalty:g},",
        f"N_for={p.n_for_months:g}, p_sto={p.p_sto_annual:g}, xmin={p.xmin_share:g}.",
        "Fig. 4 knobs stay on the comparison object. G1/G2 stay blocked.",
        "",
        "## Verification protocol (CLAUDE.md)",
        "",
        "1. **Claim.** DEVELOPMENT item 3 / Agrimate undisturbed: after",
        "spin-up, repeating seasonal behaviour. Author Fig. 4 baseline",
        "last/first of the annual-mean world-price index 2011/2006 =",
        f"**{_fmt(author, 3)}**.",
        "",
        "2. **Implementation.** D.22 `q_oth` EMA in `sheaf/agrimate/model.py`",
        "(`AgrimateSim.__init__` `freeze_q_oth=False`; init",
        "`q_oth = max(XI*_world − XI*_r, 1e-9)`; each step",
        "`q_oth = (1−w_exp)·q_oth + w_exp·realized_oth` unless freeze).",
        "`freeze_q_oth` is an `AgrimateSim` / `run_agrimate` kwarg, **not**",
        "an `AgrimateParams` field and **not** in `wheat_params()`.",
        "",
        "3. **Match.** Live host still updates `q_oth` (D.22). N2 rolling",
        "year (`replan_stride=1`) and N3 Jacobi IBR unchanged. Author D.22",
        "still updates `q_oth` (R4 / `GATE0_DEPARTURES.md`).",
        "",
        "4. **Counterexample.** On the S1 member-sum host, undisturbed",
        f"`prices_three_scenarios.csv` 2006–11 last/first = **{_fmt(lf, 3)}**",
        f"(USD annual mean ${_fmt(metrics['mean_first_usd'], 2)} → "
        f"${_fmt(metrics['mean_last_usd'], 2)}). Author **{_fmt(author, 3)}**",
        f"(index {_fmt(metrics['author_first'], 3)} → "
        f"{_fmt(metrics['author_last'], 3)}). Pre-S1 pooled-mean host was",
        f"**{_fmt(metrics['pre_s1_last_first'], 3)}**. Member-sum moved the",
        "ratio; it did not recover Agrimate. Threshold 1.1 still failed.",
        "",
        "5. **Correctness argument (do not adopt freeze).** R4",
        f"`qoth_freeze` last/first **{_fmt(metrics['r4_freeze_last_first'], 3)}**",
        "on the *pre-S1* host was a diagnostic isolation. Author still",
        "updates `q_oth` and still has last/first ≈ 1. There is **no**",
        "sourced D.22 variant in retrieved 14022004 wheat: this tree has",
        f"**{int(metrics['n_julia'])}** `*.jl` files.",
        "`scripts/fetch_external_data.py` does not mention 14022004.",
        "`freeze_q_oth` is not an `AgrimateParams` field (absent, as",
        "required). Without a sourced freeze (or other D.22 variant) from",
        "author wheat code, adopting it would be a new economic law, not a",
        "copy. Label and stop.",
        "",
        "6. **Change.** None to economics. This note labels item 3 on the",
        "member-sum host. `freeze_q_oth` stays default False. Do not pin",
        "the unforced world price to the 2006 mean. Do not restore L1–L8.",
        "",
        "## Live score (USD, 2006–11, from prices_three_scenarios.csv)",
        "",
        "| object | last/first | 2006 mean | 2011 mean |",
        "|---|---:|---:|---:|",
        f"| Host undisturbed | {_fmt(lf, 3)} | "
        f"{_fmt(metrics['mean_first_usd'], 2)} | "
        f"{_fmt(metrics['mean_last_usd'], 2)} |",
        f"| Author Fig. 4 baseline | {_fmt(author, 3)} | "
        f"{_fmt(metrics['author_first'], 3)} (index) | "
        f"{_fmt(metrics['author_last'], 3)} (index) |",
        f"| Pre-S1 host (R4 default) | {_fmt(metrics['pre_s1_last_first'], 3)} | — | — |",
        f"| R4 qoth_freeze (pre-S1, not adopted) | "
        f"{_fmt(metrics['r4_freeze_last_first'], 3)} | — | — |",
        "",
        "G0-P item 3 remains **fail**. Historical R4 probes stay in",
        "`xi_split.md` (including that note's **Next paste: R5**).",
        "**Next paste: S3.** A1 after A8 (USDA `ending_stocks` only;",
        "never FAO ΔS as stocks). Do not start G1/G2.",
        "",
    ]
    path = Path(out_dir) / "item3.md"
    path.write_text("\n".join(lines))
    return path


def write_s2_dispatch(metrics: dict, path: Path | None = None) -> Path:
    """Living S2 writer. Does not clobber a later S-session dispatch."""
    path = Path(path) if path else DISPATCH
    if path.is_file():
        text = path.read_text()
        if "Last completed: S1" not in text and "Last completed: S2" not in text:
            return path
    lf = _fmt(metrics["last_first"], 3)
    author = _fmt(metrics["last_first_author"], 3)
    body = "\n".join([
        "# Gate 0 reproduction dispatch",
        "",
        "Living next-paste. R-science queue exhausted. Template:",
        "`GATE0_NEXT_PROMPTS.md` (S1–S6). Do not walk R8…R12 as science.",
        "",
        "```",
        "Last completed: S2",
        "Window / scenario: 2003–11 undisturbed last/first on USDA member-sum host",
        "hike_2008 harvest+AMIS 2006–08: ×3.71 (S1; author ×1.62)",
        "moy max/min harvest+AMIS: 16.8× (author 1.45×)",
        f"undisturbed last/first: {lf} vs author {author} (was 1.630 pre-S1)",
        "unconverged / failed: harvest+AMIS 2304 / 0 (S1; not re-run)",
        "What you could set / could not set: item 3 labelled; no sourced D.22; freeze not adopted; USDA S; A7 cannot-set",
        "Next paste: S3",
        f"Why: last/first {lf} > 1.1; 0 Julia; freeze stays diagnostic default off; do not pin",
        "Skip: R8-as-science; R11; G1/G2; 2006 pin; Bai 10; L1–L8; FAO ΔS as stocks",
        "```",
    ])
    path.write_text(body + "\n")
    return path


def run_s2_item3_score(out_dir: Path | None = None) -> dict[str, Path]:
    """Label item 3 from living prices. Does not re-run NLP or freeze probes."""
    out_dir = Path(out_dir) if out_dir else OUT_DEFAULT
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in PROTECTED_THREE_SCENARIO:
        assert (out_dir / name).is_file(), name
    before = {name: (out_dir / name).read_bytes() for name in PROTECTED_THREE_SCENARIO}
    metrics = live_host_last_first(out_dir / "prices_three_scenarios.csv")
    assert metrics["last_first"] > 1.1
    assert metrics["n_julia"] == 0
    assert metrics["freeze_q_oth_on_params"] is False
    assert wheat_params().alpha_i == 3.2
    assert wheat_params().zeta_penalty == 0.0
    csv_path = out_dir / "score_item3.csv"
    pd.DataFrame([metrics]).to_csv(csv_path, index=False)
    note = write_s2_item3_note(metrics, out_dir)
    dispatch = write_s2_dispatch(metrics)
    after = {name: (out_dir / name).read_bytes() for name in PROTECTED_THREE_SCENARIO}
    assert before == after, "S2 must not overwrite 2003–11 three-scenario CSVs"
    return {"note": note, "csv": csv_path, "dispatch": dispatch}
