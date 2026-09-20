"""S5: re-score Fig. 4 / hindcast on the S1 member-sum host.

Allowed because S1 changed the data adapter, not ``wheat_params()``.
Reads existing 2003–11 three-scenario CSVs. Does **not** re-run the
NLP runner (that would be R11). Does not adopt Bai αI=10, restore
L1–L8, pin 2006, or start G1.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from .fig4 import run_fig4_score
from .fig4_config import PROTECTED_THREE_SCENARIO
from .hindcast import run_hindcast_score
from .methods import publication_bar
from .params import wheat_params
from .regional import rewrite_regional_note_from_csvs
from .validation import OUT_DEFAULT

ROOT = Path(__file__).resolve().parents[2]
DISPATCH = ROOT / "diagnostics" / "GATE0_REPRO_DISPATCH.md"


def live_s5_metrics(out_dir: Path | None = None) -> dict:
    out_dir = Path(out_dir) if out_dir else OUT_DEFAULT
    prices = pd.read_csv(out_dir / "score_prices.csv")
    ha = prices[prices["scenario"] == "harvest_amis"].iloc[0]
    seasonal = pd.read_csv(out_dir / "score_hindcast_seasonal.csv")
    sha = seasonal[seasonal["scenario"] == "harvest_amis"].iloc[0]
    item3 = pd.read_csv(out_dir / "score_item3.csv").iloc[0]
    fig4 = pd.read_csv(out_dir / "score_fig4_prices.csv")
    fha = fig4[fig4["scenario"] == "harvest_amis"].iloc[0]
    last_first = float(item3["last_first"])
    last_first_author = float(item3["last_first_author"])
    item3_pass = last_first <= 1.1
    item2_pass = int(ha["unconverged"]) == 0 and int(ha["failed"]) == 0
    items_13_changed = item3_pass or item2_pass
    return {
        "hike_host": float(sha["hike_2008_host"]),
        "hike_author": float(sha["hike_2008_author"]),
        "hike_pink": float(sha["hike_2008_pink"]),
        "moy_host": float(sha["moy_maxmin_host"]),
        "moy_author": float(sha["moy_maxmin_author"]),
        "moy_pink": float(sha["moy_maxmin_pink"]),
        "mean_2006_host_usd": float(sha["mean_2006_host_usd"]),
        "mean_2006_pink_usd": float(sha["mean_2006_pink_usd"]),
        "quiet_index_host": float(sha["level_vs_pink"]),
        "quiet_index_author": float(sha["mean_2006_author_index"]),
        "last_first": last_first,
        "last_first_author": last_first_author,
        "unconverged": int(ha["unconverged"]),
        "failed": int(ha["failed"]),
        "fig4_hike_host": float(fha["hike_2008_host"]),
        "fig4_hike_author": float(fha["hike_2008_author"]),
        "fig4_mean_2006_host": float(fha["mean_2006_host"]),
        "alpha_i": float(wheat_params().alpha_i),
        "item2_pass": item2_pass,
        "item3_pass": item3_pass,
        "items_13_changed": items_13_changed,
        "accepted": False,
    }


def write_s5_note(metrics: dict, out_dir: Path | None = None) -> Path:
    out_dir = Path(out_dir) if out_dir else OUT_DEFAULT
    next_paste = "S6" if metrics["items_13_changed"] else "stay not-accepted"
    lines = [
        "# S5 — re-score Fig. 4 / hindcast on the member-sum host",
        "",
        "Allowed because S1 changed the **data adapter**, not",
        "`wheat_params()`. This is **not R11**. The 2003–11 three-scenario",
        "NLP runner was not re-run. Bai αI=10 not adopted. L1–L8 stay",
        "rejected. 2006 not pinned. G1/G2 stay blocked.",
        "",
        "## Live scores (S1 CSVs vs author_fig4 / Pink Sheet)",
        "",
        "| metric | host | author Fig. 4 | Pink Sheet |",
        "|---|---:|---:|---:|",
        f"| 2006–08 hike (harvest+AMIS) | ×{metrics['hike_host']:.2f} | "
        f"×{metrics['hike_author']:.2f} | ×{metrics['hike_pink']:.2f} |",
        f"| 2006 quiet-year mean | ${metrics['mean_2006_host_usd']:.1f}/t "
        f"(index {metrics['quiet_index_host']:.3f}) | "
        f"index {metrics['quiet_index_author']:.3f} | "
        f"${metrics['mean_2006_pink_usd']:.1f}/t |",
        f"| moy max/min | {metrics['moy_host']:.1f}× | "
        f"{metrics['moy_author']:.2f}× | {metrics['moy_pink']:.2f}× |",
        f"| undisturbed last/first | {metrics['last_first']:.3f} | "
        f"{metrics['last_first_author']:.3f} | — |",
        f"| unconverged / failed | {metrics['unconverged']}/5832 / "
        f"{metrics['failed']} | — | — |",
        "",
        f"`wheat_params()` αI={metrics['alpha_i']}, ζ=0, N_for=3.",
        "Fig. 4 knobs stay on `fig4_experiment_params()`.",
        "",
        "## Items 1–3 (pass rule)",
        "",
        "1. Source fidelity: still met for retrieved 14022004 with labelled",
        "   S3/S4/A1–A6/N5. Unchanged.",
        "2. Numerical reliability: still feasible, **not** first-order",
        f"   stationary (unconverged {metrics['unconverged']}/5832). Still fails.",
        "3. Undisturbed: last/first "
        f"{metrics['last_first']:.3f} vs author "
        f"{metrics['last_first_author']:.3f} (still >1.1). Still fails.",
        "",
        "Items 1–3 evidence did **not** newly pass. Item 5 is still a",
        "sourced shortfall (hike and moy still several times Agrimate).",
        "G0-P stays **not accepted**. S6 is not next. Do not start G1.",
        "",
        "## What this session did not do",
        "",
        "- Did not re-run `scripts/run_agrimate_validation.py` (R11).",
        "- Did not retune αI / p_sto / xmin / λ.",
        "- Did not restore L1–L8 or pin 2006.",
        "- Did not adopt Bai α_foreign=10.",
        "- Did not adopt FBSH. Did not invent Egypt.",
        "- Did not start G1/G2.",
        "",
        f"**Next paste: {next_paste}.** Do not start G1.",
        "",
    ]
    path = out_dir / "s5_score.md"
    path.write_text("\n".join(lines) + "\n")
    return path


def write_s5_dispatch(metrics: dict, path: Path | None = None) -> Path:
    """Living S5 writer. Does not clobber a later S-session dispatch."""
    path = Path(path) if path else DISPATCH
    if path.is_file():
        text = path.read_text()
        if "Last completed: S4" not in text and "Last completed: S5" not in text:
            return path
    next_paste = "S6" if metrics["items_13_changed"] else "stay not-accepted"
    why = (
        "items 1–3 still fail (unconverged "
        f"{metrics['unconverged']}/5832; last/first "
        f"{metrics['last_first']:.3f}>1.1); G0-P not accepted; do not start G1"
        if not metrics["items_13_changed"]
        else "items 1–3 evidence moved; G0-P methods v2"
    )
    body = "\n".join([
        "# Gate 0 reproduction dispatch",
        "",
        "Living next-paste. R-science queue exhausted. Template:",
        "`GATE0_NEXT_PROMPTS.md` (S1–S6). Do not walk R8…R12 as science.",
        "",
        "```",
        "Last completed: S5",
        "Window / scenario: S1 member-sum 2003–11 three scenarios (CSV re-score, not R11)",
        f"hike_2008: harvest+AMIS ×{metrics['hike_host']:.2f}; "
        f"author ×{metrics['hike_author']:.2f}; Pink ×{metrics['hike_pink']:.2f}",
        f"moy max/min: host {metrics['moy_host']:.1f}×; "
        f"author {metrics['moy_author']:.2f}×; Pink {metrics['moy_pink']:.2f}×",
        f"undisturbed last/first: {metrics['last_first']:.3f} vs author "
        f"{metrics['last_first_author']:.3f} (S2)",
        f"unconverged / failed: {metrics['unconverged']}/5832 / {metrics['failed']}",
        "What you could set / could not set: notes from existing CSVs; "
        "could not retune wheat_params; could not re-run NLP (R11)",
        f"Next paste: {next_paste}",
        f"Why: {why}",
        "Skip: S6; G1/G2; R11; 2006 pin; Bai 10; L1–L8; FAO ΔS as stocks",
        "```",
        "",
    ])
    path.write_text(body)
    return path


def write_score_csv(metrics: dict, out_dir: Path) -> Path:
    path = Path(out_dir) / "score_s5.csv"
    pd.DataFrame([metrics]).to_csv(path, index=False)
    return path


def run_s5_rescore(out_dir: Path | None = None) -> dict[str, Path]:
    out_dir = Path(out_dir) if out_dir else OUT_DEFAULT
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in PROTECTED_THREE_SCENARIO:
        assert (out_dir / name).is_file(), name
    before = {name: (out_dir / name).read_bytes() for name in PROTECTED_THREE_SCENARIO}
    p = wheat_params()
    assert p.alpha_i == 3.2
    assert p.zeta_penalty == 0.0
    assert p.n_for_months == 3
    fig4 = run_fig4_score(out_dir=out_dir)
    hind = run_hindcast_score(out_dir=out_dir)
    regional = rewrite_regional_note_from_csvs(out_dir)
    metrics = live_s5_metrics(out_dir)
    assert metrics["items_13_changed"] is False
    assert metrics["alpha_i"] == 3.2
    csv = write_score_csv(metrics, out_dir)
    note = write_s5_note(metrics, out_dir)
    dispatch = write_s5_dispatch(metrics)
    after = {name: (out_dir / name).read_bytes() for name in PROTECTED_THREE_SCENARIO}
    assert before == after, "S5 must not overwrite 2003–11 three-scenario CSVs"
    bar = publication_bar(out_dir)
    assert bar["accepted"] is False
    return {
        "note": note,
        "score": csv,
        "fig4": fig4["report"],
        "hindcast": hind["note"],
        "regional": regional,
        "dispatch": dispatch,
    }
