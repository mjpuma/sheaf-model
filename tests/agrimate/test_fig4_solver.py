"""R9: N5 on Fig. 4 knobs. plan_maxiter stays 40. wheat_params unchanged."""
from __future__ import annotations

import ast
import json
from pathlib import Path

from sheaf.agrimate.fig4_config import PROTECTED_THREE_SCENARIO
from sheaf.agrimate.fig4_solver import _bucket
from sheaf.agrimate.params import fig4_experiment_params, wheat_params
from sheaf.agrimate.validation import OUT_DEFAULT

ROOT = Path(__file__).resolve().parents[2]


def test_plan_maxiter_not_raised_on_defaults_or_fig4_object():
    assert wheat_params().plan_maxiter == 40
    assert fig4_experiment_params().plan_maxiter == 40
    assert wheat_params().alpha_i == 3.2
    assert fig4_experiment_params().alpha_i == 3.5
    assert fig4_experiment_params().zeta_penalty == 1.0


def test_bucket_splits_maxiter_from_abnormal():
    assert _bucket("STOP: TOTAL NO. OF ITERATIONS REACHED LIMIT") == "maxiter"
    assert _bucket("ABNORMAL: ") == "abnormal"
    assert _bucket("CONVERGENCE: RELATIVE REDUCTION OF F") == "other"


def test_r9_note_and_json_count_failed_vs_unconverged():
    note = OUT_DEFAULT / "solver_fig4.md"
    js = OUT_DEFAULT / "solver_fig4.json"
    assert note.is_file()
    assert js.is_file()
    text = note.read_text()
    assert "Leave `plan_maxiter=40`" in text
    assert "L1–L8" in text
    assert "not adopted" in text.lower() or "not a retune" in text.lower()
    assert "wheat_params" in text
    assert "Next paste: R4" in text
    report = json.loads(js.read_text())
    assert report["default_plan_maxiter"] == 40
    assert report["fig4_plan_maxiter"] == 40
    assert report["decision"] == "leave plan_maxiter=40"
    assert report["adopted_fig4_knobs"] is False
    k40 = report["runs"]["knobs_40"]
    d40 = report["runs"]["default_40"]
    assert k40["failed"] == 0
    assert d40["failed"] == 0
    assert k40["unconverged"] > 0
    assert k40["unconverged"] == k40["n_snaps"]
    assert k40["unconverged"] == (
        k40["buckets"]["maxiter"] + k40["buckets"]["abnormal"]
        + k40["buckets"]["other"]
    )
    assert wheat_params().plan_maxiter == 40


def test_r9_module_does_not_import_g1g2():
    tree = ast.parse(Path("sheaf/agrimate/fig4_solver.py").read_text())
    banned = ("dynamic_policy", "dynamic_coupled", "legacy")
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""]
        else:
            continue
        for name in names:
            assert all(b not in name for b in banned), name


def test_r9_did_not_overwrite_p5_or_three_scenario():
    assert (OUT_DEFAULT / "solver.md").is_file()
    assert (OUT_DEFAULT / "solver_probe.json").is_file()
    p5 = (OUT_DEFAULT / "solver.md").read_text()
    assert "1743/5832" in p5
    for name in PROTECTED_THREE_SCENARIO:
        assert (OUT_DEFAULT / name).is_file(), name
    dispatch = (ROOT / "diagnostics" / "GATE0_REPRO_DISPATCH.md").read_text()
    assert "Last completed: R9" in dispatch
    assert "Next paste: R4" in dispatch
    assert "plan_maxiter stays 40" in dispatch
