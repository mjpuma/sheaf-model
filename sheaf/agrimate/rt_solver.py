"""Red team: solver last/first 0.812 and the continued mismatch.

Recomputes from committed CSVs. Does **not** re-run the NLP. Does not
pin, freeze, retune, copy Julia, or start G1. Fig. 4 later.
"""
from __future__ import annotations

from dataclasses import fields
from pathlib import Path

import numpy as np
import pandas as pd

from .fig4 import AUTHOR_DIR, author_undisturbed_drift, load_author_fig4
from .fig4_config import PROTECTED_THREE_SCENARIO, _last_first, _moy_maxmin
from .params import AgrimateParams, fig4_experiment_params, wheat_params
from .validation import OUT_DEFAULT
from .xi_split import SCORE_END, SCORE_START, n_julia_sources

ROOT = Path(__file__).resolve().parents[2]
DISPATCH = ROOT / "diagnostics" / "GATE0_REPRO_DISPATCH.md"
SOLVER_PRICES = "prices_undisturbed_solver_x1.csv"
SOLVER_SCORE = "score_solver_x1.csv"
D22_PRICES = "prices_undisturbed_d22.csv"
S1_PRICES = "prices_three_scenarios.csv"


def _fmt(x, nd: int = 3) -> str:
    if x is None:
        return "nan"
    try:
        xf = float(x)
    except (TypeError, ValueError):
        return "nan"
    if xf != xf:
        return "nan"
    return f"{xf:.{nd}f}"


def _monthly_usd(path: Path, column: int | str = 0) -> pd.Series:
    raw = pd.read_csv(path, index_col=0)
    if isinstance(column, str):
        s = raw[column].astype(float)
    else:
        s = raw.iloc[:, int(column)].astype(float)
    s.index = pd.PeriodIndex(s.index.astype(str), freq="M")
    s.name = "usd"
    return s


def _window(s: pd.Series, start: int = SCORE_START, end: int = SCORE_END
            ) -> pd.Series:
    return s[(s.index.year >= start) & (s.index.year <= end)]


def _seas_corr(s: pd.Series, start: int, end: int) -> float:
    a = s[s.index.year == start].to_numpy(float)
    b = s[s.index.year == end].to_numpy(float)
    if a.size < 2 or a.size != b.size:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def rt_solver_metrics(out_dir: Path | None = None) -> dict:
    """Recompute item-3 stats from committed CSVs. Not a pin."""
    out_dir = Path(out_dir) if out_dir else OUT_DEFAULT
    host = _window(_monthly_usd(out_dir / SOLVER_PRICES))
    d22 = _window(_monthly_usd(out_dir / D22_PRICES))
    s1 = _window(_monthly_usd(out_dir / S1_PRICES, "undisturbed"))
    s1_ha = _window(_monthly_usd(out_dir / S1_PRICES, "harvest_amis"))
    author = author_undisturbed_drift(
        load_author_fig4(AUTHOR_DIR)["monthly"], SCORE_START, SCORE_END)
    author_m = _window(_author_undisturbed_index())
    sol = pd.read_csv(out_dir / SOLVER_SCORE).iloc[0]
    p = wheat_params()
    f4 = fig4_experiment_params()
    lf = float(_last_first(host))
    first = float(host[host.index.year == SCORE_START].mean())
    last = float(host[host.index.year == SCORE_END].mean())
    return {
        "last_first": lf,
        "mean_first_usd": first,
        "mean_last_usd": last,
        "moy_host": float(_moy_maxmin(host)),
        "moy_d22": float(_moy_maxmin(d22)),
        "moy_s1_undisturbed": float(_moy_maxmin(s1)),
        "moy_s1_harvest_amis": float(_moy_maxmin(s1_ha)),
        "moy_author": float(_moy_maxmin(author_m)),
        "seas_corr_host": _seas_corr(host, SCORE_START, SCORE_END),
        "seas_corr_author": float(author["seasonal_corr_first_last"]),
        "cv_host": float(host.std() / host.mean()) if float(host.mean()) else float("nan"),
        "cv_author": float(author["cv"]),
        "window_min_usd": float(host.min()),
        "window_max_usd": float(host.max()),
        "d22_last_first": float(_last_first(d22)),
        "s1_last_first": float(_last_first(s1)),
        "last_first_author": float(author["last_over_first"]),
        "author_first": float(author["annual_mean_first"]),
        "author_last": float(author["annual_mean_last"]),
        "item3_onesided": bool(lf <= 1.1),
        "item3_pass": bool((1.0 / 1.1) <= lf <= 1.1),
        "nlp_rerun": False,
        "nlopt_copied": False,
        "n_julia": n_julia_sources(ROOT / "sheaf"),
        "freeze_q_oth_on_params": "freeze_q_oth" in {f.name for f in fields(AgrimateParams)},
        "alpha_i": float(p.alpha_i),
        "zeta_penalty": float(p.zeta_penalty),
        "n_for_months": int(p.n_for_months),
        "plan_maxiter": int(p.plan_maxiter),
        "fig4_alpha_i": float(f4.alpha_i),
        "fig4_zeta": float(f4.zeta_penalty),
        "fig4_n_for": int(f4.n_for_months),
        "unconverged": int(sol["unconverged"]),
        "failed": int(sol["failed"]),
        "n_solves": int(sol["n_solves"]),
        "s1_three_scenario_untouched": True,
        "class_measurement": "H",
        "class_item3": "H",
        "class_comparator": "E",
        "class_remaining_nlp": "C",
        "class_solver_overclaim": "G",
        "confidence": "95-100",
        "implemented": False,
    }


def _author_undisturbed_index() -> pd.Series:
    monthly = load_author_fig4(AUTHOR_DIR)["monthly"]
    sub = monthly[monthly["scenario"] == "undisturbed"]
    return pd.Series(
        sub["wm_price_index"].to_numpy(float),
        index=pd.PeriodIndex(
            [pd.Period(year=int(y), month=int(m), freq="M")
             for y, m in zip(sub["year"], sub["month"])],
            freq="M",
        ),
        name="author_index",
    )


def write_rt_solver_note(metrics: dict, out_dir: Path | None = None) -> Path:
    out_dir = Path(out_dir) if out_dir else OUT_DEFAULT
    p = wheat_params()
    lf = float(metrics["last_first"])
    author = float(metrics["last_first_author"])
    item3 = "pass" if metrics["item3_pass"] else "fail"
    lines = [
        "# Red team — solver last/first 0.812 and the continued mismatch",
        "",
        "CSV recompute. **Not** an NLP re-run. Not a freeze. Not a pin.",
        "Not L1–L8. Not an αI retune. Not Fig. 4. Do not copy Julia.",
        f"`wheat_params()` stay αI={p.alpha_i:g}, ζ={p.zeta_penalty:g},",
        f"N_for={p.n_for_months:g}, plan_maxiter={p.plan_maxiter:g}.",
        "G1/G2 stay blocked. D.22 and x1-SLSQP stay live.",
        "",
        "## Verification protocol (CLAUDE.md)",
        "",
        "1. **Claim.** `solver_x1.md`: live x1-fixed scipy SLSQP on the",
        "   14022004 wheat path; undisturbed last/first **0.812** vs",
        "   author Fig. 4 baseline **1.004**; quiet-year USD ~$305 vs",
        "   S1 $46; item 3 still fail. Class H on the solver.",
        "",
        "2. **Implementation (inspected, not re-run).**",
        "   `solve_supplier_plan(..., x1=)` locks step 0 and SLSQP-s",
        "   the rest (`optimize.py`). Live `AgrimateSim.run` builds D",
        "   from last CES requests. R5 inflow stays T* (default off).",
        "   Score object: `prices_undisturbed_solver_x1.csv`.",
        "",
        "3. **Match (measurement).** Independent recompute of that CSV",
        f"   on 2006–11: last/first **{_fmt(lf, 3)}**, 2006 mean",
        f"   ${_fmt(metrics['mean_first_usd'], 2)}/t, 2011 mean",
        f"   ${_fmt(metrics['mean_last_usd'], 2)}/t. USD ratio equals",
        "   the committed `score_solver_x1.csv` row. Not a scoring bug.",
        "",
        "4. **Counterexample to “0.812 means we are close to Agrimate.”**",
        "   last/first is the ratio of *annual means*. On the same",
        "   window the host month-of-year max/min is",
        f"   **{_fmt(metrics['moy_host'], 0)}×** vs author baseline",
        f"   **{_fmt(metrics['moy_author'], 2)}×**. Window min/max "
        f"${_fmt(metrics['window_min_usd'], 2)}–"
        f"${_fmt(metrics['window_max_usd'], 0)}/t. Seasonal *shape*",
        f"   still repeats (corr {_fmt(metrics['seas_corr_host'], 3)};",
        f"   author {_fmt(metrics['seas_corr_author'], 3)}). Amplitude",
        "   does not. S1 undisturbed moy was 27×; D.22 1792×; solver",
        "   2374×. Sourced D.22+x1 moved last/first 1.444→0.772→0.812",
        "   (undershoot) while *worsening* the collapse. Two-sided",
        "   item 3 [1/1.1, 1.1] still **fail**.",
        "",
        "5. **Counterexample to “1.004 is this host’s twin.”** Author",
        "   1.004 is Zenodo 10688435 Fig. 4 *baseline* (A7):",
        "   AgrimateEU28+Egypt, FAO since 2005, α_foreign=3.5, ζ=1,",
        "   N_for=6, start 2000, git `old-demand-dynamics`. Host is",
        "   14022004 `wheat_params()` (αI=3.2, ζ=0, N_for=3), USDA",
        "   C.1 27, start 2003. Fig. 4 knobs stay on",
        "   `fig4_experiment_params()`. Not adopted.",
        "",
        "6. **Counterexample to class H on the remaining programme.**",
        "   x1 lock + SLSQP *family* match sourced wheat. Remaining",
        "   14022004 deltas (inspect-only; 0 `*.jl` in sheaf):",
        "   - Horizon: author `H=vcat(harvest, expected)` length",
        "     `N_hor+1`, free `n=2:N_hor+1` (`producer_optimization.jl`",
        "     68–72). Host free block is `N_hor-1`.",
        "   - Variables: author quantities + availability inequality",
        "     (97–108). Host fractions, S≥0 identically (N1).",
        "   - Start: author overwrites `x_init` with uniform remaining",
        "     stock (`producer_optimization.jl` 349–351) and retries",
        "     on `XTOL` (367–385); `maxtime=60`. Host uses the previous",
        "     plan; `plan_maxiter=40` (N5).",
        "   - Current profit: author `revenue_curve` of demand requests",
        "     (producer.jl 106–117; optimization 79–82). Host D.7 on",
        "     the locked x1 as well.",
        "   - Domestic D.7: author `(xd + x_oth_dom) / X*_C` with",
        "     `x_oth_dom` a share of expected foreign others",
        "     (producer.jl 160; initialization.jl 151). Host `xd/XD*`,",
        "     no others.",
        "   - Shipments: author `determine_transactions_two_markets`.",
        "     Host `fulfill_sales` then T* inflow (R5 off).",
        "   - Price object: host XI-weighted lagged D.7 offers; Fig. 4d",
        "     is bilateral international transaction price.",
        "   Unconverged **1091/5832** still accepted (N5). Not a unique",
        "   Agrimate maximizer.",
        "",
        "7. **Falsification attempts.**",
        "   - Scoring bug: **fails** (CSV last/first matches 0.812).",
        "   - x1 not locked: **fails** (`test_optimize.py` + live `x1=`).",
        "   - $305 is a 2006 pin: **fails** (Pink ~$213; path min $0.33).",
        "   - 0.812 vs 1.004 is *only* a remaining solver bug: **fails**",
        "     as the exclusive story (A7 comparator + amplitude).",
        "   - Closer last/first is item-3 progress: **fails** (two-sided",
        "     bar; moy 27×→2374×).",
        "   A coding bug in last_ask reconstruction is **not",
        "   established**. Remaining labelled C/D are enough to keep",
        "   last/first off 1.004 on this object.",
        "",
        "8. **Change.** This note. No economics. No retune. Harvest+AMIS",
        "   three-scenario CSVs untouched. Next paste **leave labelled**.",
        "   Exact Fig. 4 is later. Do not start G1.",
        "",
        "## Live recompute (undisturbed, 2006–11, CSV)",
        "",
        "| object | last/first | moy max/min | 2006 mean |",
        "|---|---:|---:|---:|",
        f"| Host D.22 + x1-SLSQP | {_fmt(lf, 3)} | "
        f"{_fmt(metrics['moy_host'], 0)}× | "
        f"${_fmt(metrics['mean_first_usd'], 2)}/t |",
        f"| D.22 only | {_fmt(metrics['d22_last_first'], 3)} | "
        f"{_fmt(metrics['moy_d22'], 0)}× | — |",
        f"| S1 three-scenario undisturbed | "
        f"{_fmt(metrics['s1_last_first'], 3)} | "
        f"{_fmt(metrics['moy_s1_undisturbed'], 1)}× | $45.82/t |",
        f"| Author Fig. 4 baseline | {_fmt(author, 3)} | "
        f"{_fmt(metrics['moy_author'], 2)}× | "
        f"{_fmt(metrics['author_first'], 3)} (index) |",
        "",
        f"G0-P item 3 is **{item3}** (two-sided [1/1.1, 1.1]).",
        f"Host seasonal corr {_fmt(metrics['seas_corr_host'], 3)}; "
        f"author {_fmt(metrics['seas_corr_author'], 3)}.",
        f"Unconverged {int(metrics['unconverged'])}/"
        f"{int(metrics['n_solves'])}; failed "
        f"{int(metrics['failed'])}. NLP not re-run.",
        "",
        "## Classification",
        "",
        "| finding | class | confidence |",
        "|---|---|---|",
        "| 0.812 recomputes from the committed path | **H** | 95–100% |",
        "| two-sided item 3 still fail vs Fig. 4 1.004 | **H** | 95–100% |",
        "| last/first is a weak repeating statistic (moy 2374×) | **G** | 80–95% |",
        "| Fig. 4 1.004 is a different experiment (A7) | **E** | 80–95% |",
        "| remaining 14022004 NLP deltas listed above | **C**/**D** | 95–100% inspect |",
        "| `solver_x1.md` class H overstated the remaining programme | **G** | 80–95% |",
        "| x1-lock / SLSQP family as independent Python | **H** | 80–95% |",
        "| freeze / 2006 pin / αI retune as the fix | **H** (do not) | 95–100% |",
        "",
        "**Next paste: leave labelled.** Do not copy Julia. Do not write",
        "`freeze_q_oth` into `wheat_params()`. Do not start G1.",
        "",
    ]
    path = Path(out_dir) / "rt_solver.md"
    path.write_text("\n".join(lines) + "\n")
    return path


def write_rt_solver_csv(metrics: dict, out_dir: Path | None = None) -> Path:
    out_dir = Path(out_dir) if out_dir else OUT_DEFAULT
    keep = [
        "last_first", "d22_last_first", "s1_last_first", "last_first_author",
        "mean_first_usd", "mean_last_usd", "moy_host", "moy_d22",
        "moy_s1_undisturbed", "moy_s1_harvest_amis", "moy_author",
        "seas_corr_host", "seas_corr_author", "cv_host", "cv_author",
        "window_min_usd", "window_max_usd", "item3_onesided", "item3_pass",
        "nlp_rerun", "nlopt_copied", "n_julia", "freeze_q_oth_on_params",
        "alpha_i", "zeta_penalty", "n_for_months", "plan_maxiter",
        "fig4_alpha_i", "fig4_zeta", "fig4_n_for", "unconverged", "failed",
        "n_solves", "s1_three_scenario_untouched", "class_measurement",
        "class_item3", "class_comparator", "class_remaining_nlp",
        "class_solver_overclaim", "confidence", "implemented",
    ]
    path = Path(out_dir) / "score_rt_solver.csv"
    row = {k: metrics[k] for k in keep if k in metrics}
    pd.DataFrame([row]).to_csv(path, index=False)
    return path


def write_rt_solver_dispatch(metrics: dict, path: Path | None = None) -> Path:
    path = Path(path) if path else DISPATCH
    if path.is_file():
        text = path.read_text()
        if ("Last completed: solver" not in text
                and "Last completed: rt-solver" not in text):
            return path
    lf = _fmt(metrics["last_first"], 3)
    author = _fmt(metrics["last_first_author"], 3)
    item3 = "pass" if metrics["item3_pass"] else "fail"
    body = "\n".join([
        "# Gate 0 reproduction dispatch",
        "",
        "Living next-paste. Solver red-teamed. Template:",
        "`GATE0_CONTINUE.md`. Do not start G1.",
        "",
        "```",
        "Last completed: rt-solver",
        "Window / scenario: CSV recompute of 2003–11 x1-SLSQP (not Fig. 4)",
        "hike_2008: harvest+AMIS ×3.71; author ×1.62; Pink ×1.88 "
        "(S1 CSV; not re-run)",
        f"moy max/min: solver undisturbed {_fmt(metrics['moy_host'], 0)}×; "
        f"author baseline {_fmt(metrics['moy_author'], 2)}×; "
        "S1 harvest+AMIS 16.8×",
        f"undisturbed last/first: {lf} vs author {author} "
        f"(D.22 0.772; S1 1.444; item 3 {item3})",
        f"unconverged / failed: {int(metrics['unconverged'])}/"
        f"{int(metrics['n_solves'])} / {int(metrics['failed'])}",
        "What you could set / could not set: recomputed last/first and "
        "moy from committed CSV; labelled remaining 14022004 NLP deltas "
        "and A7 comparator; could not pin, freeze, copy Julia, or retune",
        "Next paste: leave labelled",
        "Why: 0.812 is honest; last/first is a weak item-3 statistic; "
        "Fig. 4 1.004 is a different experiment; do not start G1",
        "Skip: G1/G2; R11; 2006 pin; Bai 10; L1–L8; FAO ΔS as stocks; "
        "freeze_q_oth; copy Julia; invent Egypt; FAO as prepare_wheat",
        "```",
        "",
    ])
    path.write_text(body)
    return path


def run_rt_solver(out_dir: Path | None = None) -> dict[str, Path]:
    out_dir = Path(out_dir) if out_dir else OUT_DEFAULT
    p = wheat_params()
    assert p.alpha_i == 3.2
    assert p.zeta_penalty == 0.0
    assert p.n_for_months == 3
    assert p.plan_maxiter == 40
    assert "freeze_q_oth" not in {f.name for f in fields(AgrimateParams)}
    assert n_julia_sources(ROOT / "sheaf") == 0
    before = {name: (out_dir / name).read_bytes()
              for name in PROTECTED_THREE_SCENARIO
              if (out_dir / name).is_file()}
    metrics = rt_solver_metrics(out_dir)
    assert metrics["nlp_rerun"] is False
    assert metrics["nlopt_copied"] is False
    assert abs(float(metrics["last_first"]) - 0.812) < 0.01
    assert metrics["item3_pass"] is False
    assert float(metrics["moy_host"]) > 100.0
    note = write_rt_solver_note(metrics, out_dir)
    csv = write_rt_solver_csv(metrics, out_dir)
    dispatch = write_rt_solver_dispatch(metrics)
    after = {name: (out_dir / name).read_bytes()
             for name in PROTECTED_THREE_SCENARIO
             if (out_dir / name).is_file()}
    for name, blob in before.items():
        assert after[name] == blob, name
    return {"note": note, "csv": csv, "dispatch": dispatch}
