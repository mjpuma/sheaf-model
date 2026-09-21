"""Stay not-accepted: reaffirm G0-P rejection after the T-queue.

T1–T3 are labelled and not adopted. This module does **not** start G1,
does **not** retune ``wheat_params()``, does **not** pin 2006, and does
**not** invent an Egypt node. USDA stays ``prepare_wheat`` default.
"""
from __future__ import annotations

from dataclasses import fields
from pathlib import Path

import pandas as pd

from .fig4_config import PROTECTED_THREE_SCENARIO, fig4_experiment_region_path
from .methods import publication_bar
from .params import AgrimateParams, fig4_experiment_params, wheat_params
from .regions import REGION_NAMES
from .t1_julia import t1_metrics
from .t2_delta import t2_metrics
from .t3_fig4_inputs import t3_metrics
from .validation import OUT_DEFAULT
from .wheat_data import prepare_wheat
from .xi_split import n_julia_sources

ROOT = Path(__file__).resolve().parents[2]
DISPATCH = ROOT / "diagnostics" / "GATE0_REPRO_DISPATCH.md"


def sna_metrics() -> dict:
    bar = publication_bar()
    t1 = t1_metrics()
    t2 = t2_metrics()
    t3 = t3_metrics()
    p = wheat_params()
    fig4 = fig4_experiment_params()
    notes = prepare_wheat(start_year=2006, end_year=2006, params=p).notes
    param_names = {f.name for f in fields(AgrimateParams)}
    return {
        "accepted": bool(bar["accepted"]),
        "item3_undisturbed": bool(bar["item3_undisturbed"]),
        "item5_historical": bool(bar["item5_historical"]),
        "t1_obtained": bool(t1["obtained"]),
        "t2_implemented": bool(t2["implemented"]),
        "t3_obtained": bool(t3["obtained"]),
        "t3_adopted": bool(t3["adopted"]),
        "egypt_on_c1": "Egypt" in REGION_NAMES,
        "usda_is_default": any(
            "USDA PSD" in n and "not FAOSTAT Food Balances" in n for n in notes
        ),
        "region_path": fig4_experiment_region_path(),
        "n_jl_sheaf": n_julia_sources(ROOT / "sheaf"),
        "freeze_q_oth_on_params": "freeze_q_oth" in param_names,
        "alpha_i": float(p.alpha_i),
        "zeta_penalty": float(p.zeta_penalty),
        "n_for_months": int(p.n_for_months),
        "fig4_alpha_i": float(fig4.alpha_i),
        "hike_2008_host": float(bar["hike_2008_host"]),
        "hike_2008_author": float(bar["hike_2008_author"]),
        "hike_2008_pink": float(bar["hike_2008_pink"]),
        "last_first_host": float(bar["drift_undisturbed"]),
        "last_first_author": 1.004,
        "unconverged": int(bar["unconverged_harvest_amis"]),
        "failed": int(bar["failed_harvest_amis"]),
        "t_queue_exhausted": True,
        "g1_started": False,
        "next_paste": "stay not-accepted",
        "class_g0p": "F",
        "confidence": "95-100",
    }


def write_sna_note(metrics: dict, out_dir: Path | None = None) -> Path:
    out_dir = Path(out_dir) if out_dir else OUT_DEFAULT
    p = wheat_params()
    lines = [
        "# Stay not-accepted — G0-P after T1–T3",
        "",
        "**Do not start G1.** T-queue exhausted. G0-P stays **not accepted.**",
        "Not a pin. Not L1–L8. Not an αI retune. Do not copy Julia.",
        "Do not invent an Egypt node. USDA stays `prepare_wheat`.",
        f"`wheat_params()` stay αI={p.alpha_i:g}, ζ={p.zeta_penalty:g},",
        f"N_for={p.n_for_months:g}. Fig. 4 knobs stay on",
        "`fig4_experiment_params()`. FBSH 5074 is ΔS, never S.",
        "",
        "## Why this is not G1",
        "",
        "DEVELOPMENT pass rule: items 1–3 before judging 5, and before G1.",
        f"Item 3 still fails (last/first **{metrics['last_first_host']:.3f}** vs",
        f"author {metrics['last_first_author']:.3f}). Item 2 is still",
        f"unconverged L-BFGS-B **{int(metrics['unconverged'])}/5832**",
        f"(failed={int(metrics['failed'])}). Item 5 still fails (hike",
        f"×{metrics['hike_2008_host']:.2f} vs author",
        f"×{metrics['hike_2008_author']:.2f} vs Pink",
        f"×{metrics['hike_2008_pink']:.2f}). T1–T3 labelled those gaps;",
        "they did not close them. Opening substitution on this host would",
        "repeat the last-cycle mistake.",
        "",
        "## T-queue (labelled, not adopted)",
        "",
        "| ID | what | adopted? |",
        "|---|---|---|",
        "| T1 | GitLab + 14022004 Julia inspect (D.22 vector+shift; NLopt) | **no** "
        f"(0 `*.jl` in sheaf; n_jl={int(metrics['n_jl_sheaf'])}) |",
        "| T2 | sourced D.22 / solver delta (file:line) | **no** "
        f"(implemented={metrics['t2_implemented']}; freeze not a params field) |",
        "| T3 | FAO-since-2005 annual relative + AgrimateEU28+Egypt ISO | **no** "
        f"(Egypt on C.1={metrics['egypt_on_c1']}; region_path="
        f"`{metrics['region_path']}`) |",
        "",
        "`publication_bar()[\"accepted\"]` is **False**. This function does",
        "not unlock G1.",
        "",
        "## Verification protocol (CLAUDE.md)",
        "",
        "1. **Claim.** Gate 0 is publishable only if DEVELOPMENT items 1–3",
        "   hold (`DEVELOPMENT.md`). G1/G2 stay blocked until G0-P is accepted.",
        "2. **Implementation.** `publication_bar()` reads live CSVs.",
        f"   accepted={metrics['accepted']}; item3={metrics['item3_undisturbed']};",
        f"   item5={metrics['item5_historical']}.",
        "3. **Match.** T-queue did not move hike, last/first, or N5",
        "   (not R11). Scores remain S5/S6 numbers.",
        "4. **Counterexample (do not start G1).** Items 2 and 3 fail on",
        "   the recorded host. `wheat_params()` αI=3.2. Egypt is not a",
        "   C.1 node. FAO is not `prepare_wheat`.",
        "5. **Correctness of staying not-accepted.** T1–T3 were",
        "   obtain-or-leave / label-only. Adopting D.22 vector+shift,",
        "   FAO WheatData, or an Egypt node would be a new session with",
        "   a sourced prompt, not this stop. Do not invent a U-queue.",
        "6. **Change.** Record the stop. Update `methods.md` so it no",
        "   longer points at T1 as next. No economics.",
        "",
        f"n_julia={int(metrics['n_jl_sheaf'])}. freeze_q_oth on params="
        f"{metrics['freeze_q_oth_on_params']}.",
        "",
        "**Next paste: stay not-accepted.** If this note already exists",
        "and `accepted` is False, do not start G1 and do not open a new",
        "science queue. Human acceptance of G0-P is still required.",
        "",
    ]
    path = Path(out_dir) / "stay_not_accepted.md"
    path.write_text("\n".join(lines) + "\n")
    return path


def write_sna_csv(metrics: dict, out_dir: Path | None = None) -> Path:
    out_dir = Path(out_dir) if out_dir else OUT_DEFAULT
    keep = [
        "accepted", "item3_undisturbed", "item5_historical",
        "t1_obtained", "t2_implemented", "t3_obtained", "t3_adopted",
        "egypt_on_c1", "usda_is_default", "n_jl_sheaf",
        "freeze_q_oth_on_params", "alpha_i", "zeta_penalty", "n_for_months",
        "fig4_alpha_i", "hike_2008_host", "hike_2008_author", "hike_2008_pink",
        "last_first_host", "last_first_author", "unconverged", "failed",
        "t_queue_exhausted", "g1_started", "next_paste",
        "class_g0p", "confidence",
    ]
    path = Path(out_dir) / "score_stay_not_accepted.csv"
    pd.DataFrame([{k: metrics[k] for k in keep}]).to_csv(path, index=False)
    return path


def write_sna_dispatch(metrics: dict, path: Path | None = None) -> Path:
    """Living SNA writer. Does not clobber a later session that is not SNA/T3."""
    path = Path(path) if path else DISPATCH
    if path.is_file():
        text = path.read_text()
        if (
            "Last completed: T3" not in text
            and "Last completed: stay-not-accepted" not in text
        ):
            return path
    body = "\n".join([
        "# Gate 0 reproduction dispatch",
        "",
        "Living next-paste. R-science, S-queue, and T-queue exhausted.",
        "Template: `GATE0_CONTINUE.md`. Do not walk R8…R12 as science.",
        "Do not start G1.",
        "",
        "```",
        "Last completed: stay-not-accepted",
        "Window / scenario: G0-P reaffirmation after T1–T3 (not R11)",
        f"hike_2008: harvest+AMIS ×{metrics['hike_2008_host']:.2f}; "
        f"author ×{metrics['hike_2008_author']:.2f}; Pink "
        f"×{metrics['hike_2008_pink']:.2f} (unchanged; not R11)",
        "moy max/min: host 16.8×; author 1.45×; Pink 1.07×",
        f"undisturbed last/first: {metrics['last_first_host']:.3f} vs author "
        f"{metrics['last_first_author']:.3f}",
        f"unconverged / failed: {int(metrics['unconverged'])}/5832 / "
        f"{int(metrics['failed'])}",
        "What you could set / could not set: recorded T1–T3 labelled not "
        "adopted; could not accept G0-P; could not start G1; could not "
        "retune wheat_params; could not invent Egypt",
        "Next paste: stay not-accepted",
        "Why: T-queue exhausted; items 2 and 3 still fail; G0-P still not "
        "accepted; do not start G1",
        "Skip: G1/G2; R11; 2006 pin; Bai 10; L1–L8; FAO ΔS as stocks; "
        "freeze_q_oth; copy Julia; invent Egypt; FAO as prepare_wheat",
        "```",
        "",
    ])
    path.write_text(body)
    return path


def run_stay_not_accepted(out_dir: Path | None = None) -> dict[str, Path]:
    out_dir = Path(out_dir) if out_dir else OUT_DEFAULT
    metrics = sna_metrics()
    assert metrics["accepted"] is False
    assert metrics["item3_undisturbed"] is False
    assert metrics["t2_implemented"] is False
    assert metrics["t3_adopted"] is False
    assert metrics["egypt_on_c1"] is False
    assert metrics["usda_is_default"] is True
    assert int(metrics["n_jl_sheaf"]) == 0
    assert metrics["freeze_q_oth_on_params"] is False
    assert metrics["g1_started"] is False
    assert wheat_params().alpha_i == 3.2
    assert "Egypt" not in REGION_NAMES
    from .methods import write_methods_note
    note = write_sna_note(metrics, out_dir)
    csv = write_sna_csv(metrics, out_dir)
    methods = write_methods_note(out_dir)
    dispatch = write_sna_dispatch(metrics)
    for name in PROTECTED_THREE_SCENARIO:
        assert (OUT_DEFAULT / name).is_file(), name
    bar = publication_bar(out_dir)
    assert bar["accepted"] is False
    return {
        "note": note, "csv": csv, "methods": methods, "dispatch": dispatch,
    }
