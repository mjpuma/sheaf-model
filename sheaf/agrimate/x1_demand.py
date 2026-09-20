"""R5: labelled S4 x1=demand experiment. Default off. Does not retune.

Author two-market x1 is fixed to D.30/D.30a requests (S4). Host default
still delivers T*+domestic. This module turns that assignment on as
``x1_from_demand=True`` (Ndel-lagged foreign requests replace
``dest.T @ XI_lag``). Not a min(supply, demand) CES ration. Not adopted.
14022004 Julia is still not in-tree; wiring follows S4 + host E.1 lag,
not a bit-diff of ``sales_step!``.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .fig4_config import PROTECTED_THREE_SCENARIO
from .model import run_agrimate
from .params import wheat_params
from .validation import OUT_DEFAULT
from .wheat_data import prepare_wheat

START_YEAR = 2006
END_YEAR = 2006
ROOT = Path(__file__).resolve().parents[2]
DISPATCH = ROOT / "diagnostics" / "GATE0_REPRO_DISPATCH.md"


def _fmt(x, nd: int = 3) -> str:
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "nan"
    return f"{float(x):.{nd}f}"


def run_x1_pair(start_year: int = START_YEAR, end_year: int = END_YEAR):
    """Default-off vs x1_from_demand on the same 2006 harvest+AMIS WheatData."""
    data = prepare_wheat(start_year=start_year, end_year=end_year,
                         params=wheat_params())
    kwargs = dict(
        data=data, params=wheat_params(),
        use_anomalies=True, use_restrictions=True,
        start_year=start_year, end_year=end_year,
    )
    off = run_agrimate(**kwargs, x1_from_demand=False)
    on = run_agrimate(**kwargs, x1_from_demand=True)
    return off, on


def score_x1_pair(off, on) -> dict:
    dp = np.abs(on.price_index - off.price_index)
    di = np.abs(on.inflow - off.inflow)
    dc = np.abs(on.consumption - off.consumption)
    ds = np.abs(on.S_consumer - off.S_consumer)
    i_ea = off.regions.index("Eastern Africa")
    i_us = off.regions.index("USA")
    return {
        "start_year": int(off.start_year),
        "end_year": int(off.end_year),
        "n_steps": int(off.price_index.size),
        "max_abs_dp_w": float(dp.max()),
        "mean_abs_dp_w": float(dp.mean()),
        "max_abs_dinflow": float(di.max()),
        "sum_inflow_off": float(off.inflow.sum()),
        "sum_inflow_on": float(on.inflow.sum()),
        "sum_inflow_delta": float(on.inflow.sum() - off.inflow.sum()),
        "ea_inflow_off": float(off.inflow[i_ea].sum()),
        "ea_inflow_on": float(on.inflow[i_ea].sum()),
        "usa_inflow_off": float(off.inflow[i_us].sum()),
        "usa_inflow_on": float(on.inflow[i_us].sum()),
        "max_abs_dC": float(dc.max()),
        "max_abs_dSc": float(ds.max()),
        "failed_off": int(off.failed_solves),
        "failed_on": int(on.failed_solves),
        "unconverged_off": int(off.unconverged_solves),
        "unconverged_on": int(on.unconverged_solves),
        "n_solves": int(len(off.regions) * off.price_index.size),
        "runtime_off_s": float(off.runtime_s),
        "runtime_on_s": float(on.runtime_s),
        "x1_from_demand_off": bool(off.x1_from_demand),
        "x1_from_demand_on": bool(on.x1_from_demand),
        "alpha_i": float(wheat_params().alpha_i),
        "zeta_penalty": float(wheat_params().zeta_penalty),
    }


def write_x1_note(score: dict, out_dir: Path) -> Path:
    p = wheat_params()
    pw_silent = float(score["max_abs_dp_w"]) < 1e-12
    lines = [
        "# R5 — S4 x1=demand labelled experiment",
        "",
        "Default **off**. Not adopted. **Not a pin.** Not a CES-rationing",
        "rule (no min(supply, demand)). `wheat_params()` stay",
        f"αI={p.alpha_i:g}, ζ={p.zeta_penalty:g}, N_for={p.n_for_months:g},",
        f"xmin={p.xmin_share:g}. L1–L8 stay rejected. G1/G2 stay blocked.",
        "",
        "14022004 Julia is still **not in-tree**. S4 (2026-09-16 retrieval)",
        "records that author two-market `x1` is *fixed* to D.30/D.30a",
        "requests. This flag copies that assignment: Ndel-lagged foreign",
        "requests replace `dest.T @ XI_lag` as international arrival;",
        "domestic inflow stays `sold_d`. Destination-weight allocation of",
        "XI was **not** copied (that would guess a ration).",
        "",
        f"Window: harvest+AMIS **{score['start_year']}** only",
        f"({int(score['n_steps'])} steps). Default-off recovers today's",
        "path (`test_x1_from_demand_default_off_recovers_path`).",
        "",
        "## Off vs on",
        "",
        "| metric | T*+domestic (off) | x1=demand (on) |",
        "|---|---:|---:|",
        f"| Σ inflow MMT | {_fmt(score['sum_inflow_off'], 2)} | "
        f"{_fmt(score['sum_inflow_on'], 2)} |",
        f"| Eastern Africa inflow | {_fmt(score['ea_inflow_off'], 3)} | "
        f"{_fmt(score['ea_inflow_on'], 3)} |",
        f"| USA inflow | {_fmt(score['usa_inflow_off'], 2)} | "
        f"{_fmt(score['usa_inflow_on'], 2)} |",
        f"| max \\|Δ inflow\\| | — | {_fmt(score['max_abs_dinflow'], 3)} |",
        f"| max \\|Δ C\\| | — | {_fmt(score['max_abs_dC'], 3)} |",
        f"| max \\|Δ S_c\\| | — | {_fmt(score['max_abs_dSc'], 3)} |",
        f"| max \\|Δ p_w\\| | — | {score['max_abs_dp_w']:.3e} |",
        f"| unconverged | {int(score['unconverged_off'])}/{int(score['n_solves'])} | "
        f"{int(score['unconverged_on'])}/{int(score['n_solves'])} |",
        f"| failed | {int(score['failed_off'])} | {int(score['failed_on'])} |",
        "",
        (
            "p_w is **silent** (XI-weighted lagged D.7 mix; B1/R3). "
            if pw_silent else
            "p_w **moved** — unexpected if offers stay on XI; do not pin. "
        )
        + "Who eats / S_c move. εc/σ can now affect inflow; they still do "
        "not enter the supplier plan. Not a reason to retune αI.",
        "",
        "**Next paste: R6.** A1 FAOSTAT FB obtain-or-leave. R5 does not",
        "unlock G1. Item 3 still fails on the live host (x1 default off).",
        "",
    ]
    path = out_dir / "x1_demand.md"
    path.write_text("\n".join(lines))
    return path


def write_r5_dispatch(score: dict, path: Path | None = None) -> Path:
    path = Path(path) if path else DISPATCH
    pw = float(score["max_abs_dp_w"])
    din = float(score["max_abs_dinflow"])
    why = (
        f"x1=demand labelled (default off); max |Δp_w|={pw:.1e}, "
        f"max |Δinflow|={_fmt(din, 3)}; not adopted; do not pin"
    )
    body = "\n".join([
        "# Gate 0 reproduction dispatch",
        "",
        "Living next-paste. Rewrite after every R-session from **that run’s",
        "numbers**. Do not walk R3…R12 in order. Template:",
        "`GATE0_REPRO_PROMPTS.md` (Adaptive rule).",
        "",
        "```",
        "Last completed: R5",
        "Window / scenario: 2006 harvest+AMIS x1=demand vs T*+domestic",
        "hike_2008 (default → knobs → author): ×2.31 → ×2.22 → ×1.62",
        "moy max/min: 26.8× → 13.3× → 1.51×",
        "undisturbed last/first: default 1.630 → qoth_freeze 1.019 → author 1.004",
        f"unconverged / failed: off {int(score['unconverged_off'])}/"
        f"{int(score['n_solves'])} failed={int(score['failed_off'])}",
        "What you could set / could not set: x1_from_demand labelled "
        "(Julia still absent); no CES ration; remaining A7/A1",
        "Next paste: R6",
        f"Why: {why}",
        "Skip: R11; G1/G2; do not adopt x1; do not retune αI",
        "```",
    ])
    path.write_text(body + "\n")
    return path


def run_x1_demand_score(out_dir: Path | None = None) -> dict[str, Path]:
    out_dir = Path(out_dir) if out_dir else OUT_DEFAULT
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in PROTECTED_THREE_SCENARIO:
        assert (out_dir / name).is_file(), name
    before = {name: (out_dir / name).read_bytes() for name in PROTECTED_THREE_SCENARIO}
    off, on = run_x1_pair()
    score = score_x1_pair(off, on)
    csv = out_dir / "score_x1_demand.csv"
    pd.DataFrame([score]).to_csv(csv, index=False)
    note = write_x1_note(score, out_dir)
    dispatch = write_r5_dispatch(score)
    after = {name: (out_dir / name).read_bytes() for name in PROTECTED_THREE_SCENARIO}
    assert before == after, "R5 must not overwrite 2003–11 three-scenario CSVs"
    assert wheat_params().alpha_i == 3.2
    assert wheat_params().zeta_penalty == 0.0
    assert off.x1_from_demand is False
    assert on.x1_from_demand is True
    return {"note": note, "csv": csv, "dispatch": dispatch}
