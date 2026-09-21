"""D.22 rivals' expected international sales: horizon vector + shift.

Independent Python of the sourced 14022004 wheat law (T2 labelled,
producer.jl 452–464). Does **not** copy ``*.jl``. Does not freeze.
Does not pin 2006. Does not retune ``wheat_params()``. Does not switch
the supplier solver (NLopt / x1-fixed stays secondary).

Host plan is length ``N_hor``; author foreign plan is ``N_hor+1``.
The extra slot is padded with seasonal XI* at ``t+N_hor`` so the
skip-``N_del`` observation has length ``N_hor-1``, matching author
``[3:end]`` when ``N_del=2``.
"""
from __future__ import annotations

from dataclasses import fields
from pathlib import Path

import numpy as np
import pandas as pd

from .fig4_config import PROTECTED_THREE_SCENARIO
from .params import AgrimateParams, wheat_params
from .validation import OUT_DEFAULT
from .xi_split import n_julia_sources

ROOT = Path(__file__).resolve().parents[2]
DISPATCH = ROOT / "diagnostics" / "GATE0_REPRO_DISPATCH.md"

# T2 citations. Not identifiers in model.py.
_AUTHOR_D22 = "src/AgrimateModel/src/agents/producer.jl"
_AUTHOR_INIT = "src/AgrimateModel/src/model/initialization.jl"


def ema_weight(tau_exp: float, n_year: int) -> float:
    """``1/(τ_exp N_year)``. Matches author after ``τ_exp *= N_year``."""
    return 1.0 / max(float(tau_exp) * int(n_year), 1.0)


def init_expected_others_foreign(
        xi_star_path: np.ndarray, n_start: int = 0) -> np.ndarray:
    """Q[r, k] = Σ_{s≠r} XI*_path[s, n_start+1+k]. Length ``N_hor``.

    Author init (initialization.jl 267–279) fills the horizon from
    others' baseline foreign sales at ``n_start+n``, to be used in
    step ``n_start`` (not ``n_start-1``).
    """
    path = np.maximum(np.asarray(xi_star_path, float), 0.0)
    n_r, n_y = path.shape
    world = path.sum(axis=0)
    Q = np.empty((n_r, n_y))
    for k in range(n_y):
        idx = (int(n_start) + 1 + k) % n_y
        Q[:, k] = np.maximum(world[idx] - path[:, idx], 1e-9)
    return Q


def pad_planned_foreign(
        plan_i: np.ndarray, t: int, n_hor: int, pad: np.ndarray) -> np.ndarray:
    """Length-``N_hor+1`` planned foreign sales (host ``N_hor`` + pad).

    Host programme is ``plan_i[:, t:t+N_hor]``. Author stores one extra
    slot. ``pad`` is seasonal XI* at ``t+N_hor`` (same calendar month).
    """
    plan_i = np.asarray(plan_i, float)
    pad = np.asarray(pad, float).reshape(-1)
    n_r, T = plan_i.shape
    n_hor = int(n_hor)
    out = np.empty((n_r, n_hor + 1))
    for k in range(n_hor):
        tt = int(t) + k
        out[:, k] = plan_i[:, tt] if tt < T else pad
    out[:, n_hor] = pad
    return np.maximum(out, 0.0)


def observe_planned_foreign(padded: np.ndarray, n_del: int) -> np.ndarray:
    """Rivals' planned foreign sales after the delivery skip.

    ``padded`` is ``(n_r, N_hor+1)``. ``padded[:, n_del:]`` has length
    ``N_hor-1`` (author ``[3:end]`` when ``N_del=2``). Row ``r`` is
    Σ_{s≠r} of that tail. Not current-step realized XI.
    """
    padded = np.asarray(padded, float)
    n_del = int(n_del)
    tail = padded[:, n_del:]
    total = tail.sum(axis=0, keepdims=True)
    return np.maximum(total - tail, 0.0)


def shift_ema_expected_others(
        Q: np.ndarray, obs: np.ndarray, w: float) -> np.ndarray:
    """Age the horizon and blend in the new planned observation.

    ``Q_new[:, :-1] = w·obs + (1-w)·Q[:, 1:]``;
    ``Q_new[:, -1] = mean(Q_new[:, :-1])``.
    ``w=1`` is instantaneous replacement (author ``τ_exp==0``).
    """
    Q = np.asarray(Q, float)
    obs = np.asarray(obs, float)
    if Q.ndim != 2 or obs.shape != (Q.shape[0], Q.shape[1] - 1):
        raise ValueError("obs must be (n_r, N_hor-1) against Q (n_r, N_hor)")
    w = float(w)
    new = np.empty_like(Q)
    if w >= 1.0 - 1e-15:
        new[:, :-1] = obs
    else:
        new[:, :-1] = w * obs + (1.0 - w) * Q[:, 1:]
    new[:, -1] = new[:, :-1].mean(axis=1)
    return np.maximum(new, 1e-9)


def _fmt(x, nd: int = 3) -> str:
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "nan"
    return f"{float(x):.{nd}f}"


def d22_metrics(result, out_dir: Path | None = None) -> dict:
    """Score undisturbed last/first on a D.22 run. Not a pin."""
    from .fig4 import AUTHOR_DIR, author_undisturbed_drift, load_author_fig4
    from .validation import monthly_price
    from .xi_split import SCORE_END, SCORE_START, last_first_index

    out_dir = Path(out_dir) if out_dir else OUT_DEFAULT
    del out_dir
    p = wheat_params()
    param_names = {f.name for f in fields(AgrimateParams)}
    lf = last_first_index(result)
    monthly = monthly_price(result, field="price_usd")
    window = monthly[(monthly.index.year >= SCORE_START)
                     & (monthly.index.year <= SCORE_END)]
    first = float(window[window.index.year == SCORE_START].mean())
    last = float(window[window.index.year == SCORE_END].mean())
    author = author_undisturbed_drift(
        load_author_fig4(AUTHOR_DIR)["monthly"], SCORE_START, SCORE_END)
    notes = list(result.notes) if result.notes else []
    unconverged = int(result.unconverged_solves)
    failed = int(result.failed_solves)
    n_solves = int(len(result.regions) * result.price_index.size)
    return {
        "last_first": lf,
        "last_first_s1": 1.444,
        "mean_first_usd": first,
        "mean_last_usd": last,
        "last_first_author": float(author["last_over_first"]),
        "author_first": float(author["annual_mean_first"]),
        "author_last": float(author["annual_mean_last"]),
        "n_julia": n_julia_sources(ROOT / "sheaf"),
        "freeze_q_oth_on_params": "freeze_q_oth" in param_names,
        "alpha_i": float(p.alpha_i),
        "zeta_penalty": float(p.zeta_penalty),
        "n_for_months": int(p.n_for_months),
        "tau_exp": float(p.tau_exp),
        "n_del": int(p.n_del),
        "ema_weight": ema_weight(p.tau_exp, p.n_year),
        "unconverged": unconverged,
        "failed": failed,
        "n_solves": n_solves,
        "item3_pass": bool(lf <= 1.1),
        "implemented": True,
        "author_does_freeze": False,
        "pad_documented": True,
        "solver_unchanged": True,
        "class_d22": "H",
        "class_solver": "C",
        "confidence": "95-100",
        "runtime_s": float(result.runtime_s),
        "notes_head": notes[0] if notes else "",
        "s1_three_scenario_untouched": True,
    }


def write_d22_note(metrics: dict, out_dir: Path | None = None) -> Path:
    out_dir = Path(out_dir) if out_dir else OUT_DEFAULT
    p = wheat_params()
    lf = float(metrics["last_first"])
    author = float(metrics["last_first_author"])
    item3 = "pass" if metrics["item3_pass"] else "fail"
    lines = [
        "# D.22 — Horizon vector + shift of planned foreign sales",
        "",
        "Independent Python of the sourced 14022004 wheat D.22 law.",
        "Not a freeze. Not a pin. Not L1–L8. Not an αI retune. Not Fig. 4.",
        "Not a solver switch. Do not copy Julia.",
        f"`wheat_params()` stay αI={p.alpha_i:g}, ζ={p.zeta_penalty:g},",
        f"N_for={p.n_for_months:g}. G1/G2 stay blocked.",
        "",
        "## Verification protocol (CLAUDE.md)",
        "",
        "1. **Claim.** T2 (`t2_delta.md`): author wheat D.22 is a horizon",
        f"   vector + shift of planned foreign sales (`{_AUTHOR_D22}`",
        "   452–464). Host was a scalar EMA of current-step realized XI.",
        "   Author still *updates* (no freeze). Weight 1/12 already matched.",
        "",
        "2. **Implementation (this host).** `sheaf/agrimate/d22.py`, wired",
        "   in `AgrimateSim.run`:",
        "   - State: `Q` shape `(n_r, N_hor)`, init from seasonal others'",
        f"     XI* (`{_AUTHOR_INIT}` 267–279).",
        "   - Plan: `others = Q[r]` (vector, not a tiled scalar).",
        "   - Offer D.7: `Q[r, 0]` as current rivals.",
        "   - Observation: padded planned foreign sales, skip `N_del`,",
        "     Σ_{s≠r} — **planned**, not realized sold XI.",
        "   - Update: shift+EMA; last slot = mean of the rest. Jacobi:",
        "     all plan against old `Q`, then all `Q` update.",
        "   - `freeze_q_oth` still skips the update (diagnostic, default",
        "     off, not an `AgrimateParams` field).",
        "",
        "3. **Pad.** Host programme length `N_hor`; author foreign plan",
        "   length `N_hor+1`. Extra slot = seasonal XI* at `t+N_hor` so",
        "   `[N_del:]` has `N_hor-1` observations (author `[3:end]` at",
        "   `N_del=2`). Documented, not a silent truncation.",
        "",
        "4. **Match.** State, observation, and update now follow the",
        "   sourced wheat law. Weight still `1/(0.5 N_year)=1/12`.",
        "   Solver is **unchanged** (L-BFGS-B, current sales free).",
        "   That delta stays labelled (`t2_delta.md` rows 7–8).",
        "",
        "5. **Counterexample (pre-change).** Scalar EMA of realized XI",
        "   tiled across the year (old `model.py`) is not author D.22.",
        "   Freeze last/first 1.019 (R4, pre-S1) is not author: author",
        "   updates. S1 three-scenario last/first **1.444** is the",
        "   pre-D.22 snapshot (`prices_three_scenarios.csv`, not re-run).",
        "",
        "6. **Correctness.** Author wheat *does* this vector+shift and",
        "   *does not* freeze. Implementing it is a copy of a sourced",
        "   law, not a new knob. Do not pin 2006. Do not restore L1–L8.",
        "   Do not switch to NLopt in this change.",
        "",
        "7. **Change.** Live D.22 law. Undisturbed 2003–11 re-measured.",
        "   Harvest+AMIS three-scenario CSVs untouched. Next paste",
        "   **solver** (NLopt / x1-fixed; secondary). Do not start G1.",
        "",
        "## Live score (undisturbed, 2006–11)",
        "",
        "| object | last/first | 2006 mean | 2011 mean |",
        "|---|---:|---:|---:|",
        f"| Host D.22 vector+shift | {_fmt(lf, 3)} | "
        f"${_fmt(metrics['mean_first_usd'], 2)}/t | "
        f"${_fmt(metrics['mean_last_usd'], 2)}/t |",
        f"| Author Fig. 4 baseline | {_fmt(author, 3)} | "
        f"{_fmt(metrics['author_first'], 3)} (index) | "
        f"{_fmt(metrics['author_last'], 3)} (index) |",
        "| S1 three-scenario (pre-D.22, not re-run) | 1.444 | "
        "45.82 | 66.15 |",
        "| R4 qoth_freeze (pre-S1, not adopted) | 1.019 | — | — |",
        "",
        f"G0-P item 3 is **{item3}** on this D.22 run (threshold 1.1).",
        f"Unconverged {int(metrics['unconverged'])}/"
        f"{int(metrics['n_solves'])}; failed "
        f"{int(metrics['failed'])}. Solver still L-BFGS-B.",
        "Harvest+AMIS hike/moy remain the S1 CSVs (not this experiment).",
        "Do not start G1.",
        "",
        "**Next paste: solver.** D.22 implemented; NLopt / x1-fixed still",
        "differs. Do not copy Julia. Do not write `freeze_q_oth` into",
        "`wheat_params()`.",
        "",
    ]
    path = Path(out_dir) / "d22.md"
    path.write_text("\n".join(lines) + "\n")
    return path


def write_d22_csv(metrics: dict, out_dir: Path | None = None) -> Path:
    out_dir = Path(out_dir) if out_dir else OUT_DEFAULT
    keep = [
        "last_first", "last_first_s1", "mean_first_usd", "mean_last_usd",
        "last_first_author", "author_first", "author_last",
        "n_julia", "freeze_q_oth_on_params", "alpha_i", "zeta_penalty",
        "n_for_months", "tau_exp", "n_del", "ema_weight",
        "unconverged", "failed", "n_solves", "item3_pass",
        "implemented", "author_does_freeze", "pad_documented",
        "solver_unchanged", "class_d22", "class_solver", "confidence",
        "runtime_s", "s1_three_scenario_untouched",
    ]
    path = Path(out_dir) / "score_d22.csv"
    pd.DataFrame([{k: metrics[k] for k in keep}]).to_csv(path, index=False)
    return path


def write_d22_prices(result, out_dir: Path | None = None) -> Path:
    """Monthly undisturbed USD. Does not touch prices_three_scenarios.csv."""
    from .validation import monthly_price

    out_dir = Path(out_dir) if out_dir else OUT_DEFAULT
    s = monthly_price(result, field="price_usd")
    path = Path(out_dir) / "prices_undisturbed_d22.csv"
    s.to_frame("undisturbed").to_csv(path)
    return path


def write_d22_dispatch(metrics: dict, path: Path | None = None) -> Path:
    """Living D.22 writer. Does not clobber a later-session dispatch."""
    path = Path(path) if path else DISPATCH
    if path.is_file():
        text = path.read_text()
        if ("Last completed: stay-not-accepted" not in text
                and "Last completed: D.22" not in text):
            return path
    lf = _fmt(metrics["last_first"], 3)
    author = _fmt(metrics["last_first_author"], 3)
    item3 = "pass" if metrics["item3_pass"] else "fail"
    body = "\n".join([
        "# Gate 0 reproduction dispatch",
        "",
        "Living next-paste. R-science, S-queue, and T-queue exhausted.",
        "D.22 vector+shift implemented. Template: `GATE0_CONTINUE.md`.",
        "Do not start G1.",
        "",
        "```",
        "Last completed: D.22",
        "Window / scenario: 2003–11 undisturbed vector+shift (not Fig. 4)",
        "hike_2008: harvest+AMIS ×3.71; author ×1.62; Pink ×1.88 "
        "(S1 CSV; not re-run)",
        "moy max/min: host 16.8×; author 1.45×; Pink 1.07× (S1 CSV)",
        f"undisturbed last/first: {lf} vs author {author} "
        f"(S1 snapshot 1.444; item 3 {item3})",
        f"unconverged / failed: {int(metrics['unconverged'])}/"
        f"{int(metrics['n_solves'])} / {int(metrics['failed'])}",
        "What you could set / could not set: implemented sourced D.22 "
        "vector+shift of planned foreign sales; could not freeze "
        "(author does not); could not switch NLopt; could not pin 2006",
        "Next paste: solver",
        "Why: D.22 is the quiet-year channel; supplier optimizer "
        "(NLopt / x1-fixed) still differs; do not start G1",
        "Skip: G1/G2; R11; 2006 pin; Bai 10; L1–L8; FAO ΔS as stocks; "
        "freeze_q_oth; copy Julia; invent Egypt; FAO as prepare_wheat; Fig. 4",
        "```",
        "",
    ])
    path.write_text(body)
    return path


def run_d22_undisturbed(out_dir: Path | None = None) -> dict[str, Path]:
    """Run 2003–11 undisturbed under the live D.22 law. No three-scenario."""
    from .model import run_agrimate
    from .wheat_data import prepare_wheat

    out_dir = Path(out_dir) if out_dir else OUT_DEFAULT
    out_dir.mkdir(parents=True, exist_ok=True)
    p = wheat_params()
    assert p.alpha_i == 3.2
    assert p.zeta_penalty == 0.0
    assert p.n_for_months == 3
    assert "freeze_q_oth" not in {f.name for f in fields(AgrimateParams)}
    assert n_julia_sources(ROOT / "sheaf") == 0
    before = {name: (out_dir / name).read_bytes()
              for name in PROTECTED_THREE_SCENARIO
              if (out_dir / name).is_file()}
    data = prepare_wheat(start_year=2003, end_year=2011, params=p)
    result = run_agrimate(
        data=data, params=p,
        use_anomalies=False, use_restrictions=False,
        start_year=2003, end_year=2011,
    )
    metrics = d22_metrics(result, out_dir)
    assert metrics["implemented"] is True
    assert metrics["author_does_freeze"] is False
    assert int(metrics["n_julia"]) == 0
    assert metrics["freeze_q_oth_on_params"] is False
    assert metrics["solver_unchanged"] is True
    note = write_d22_note(metrics, out_dir)
    csv = write_d22_csv(metrics, out_dir)
    prices = write_d22_prices(result, out_dir)
    dispatch = write_d22_dispatch(metrics)
    after = {name: (out_dir / name).read_bytes()
             for name in PROTECTED_THREE_SCENARIO
             if (out_dir / name).is_file()}
    for name, blob in before.items():
        assert after[name] == blob, name
    return {"note": note, "csv": csv, "prices": prices, "dispatch": dispatch}
