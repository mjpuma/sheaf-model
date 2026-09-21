"""Red team of solver last/first 0.812. CSV only. Not a pin, freeze, or G1."""
from __future__ import annotations

import ast
from dataclasses import fields
from pathlib import Path

from sheaf.agrimate.fig4_config import PROTECTED_THREE_SCENARIO
from sheaf.agrimate.params import AgrimateParams, wheat_params
from sheaf.agrimate.rt_solver import write_rt_solver_dispatch
from sheaf.agrimate.validation import OUT_DEFAULT
from sheaf.agrimate.xi_split import n_julia_sources

ROOT = Path(__file__).resolve().parents[2]


def test_rt_solver_does_not_copy_julia_or_freeze_or_retune():
    assert n_julia_sources() == 0
    p = wheat_params()
    assert p.alpha_i == 3.2
    assert p.zeta_penalty == 0.0
    assert p.n_for_months == 3
    assert p.plan_maxiter == 40
    assert "freeze_q_oth" not in {f.name for f in fields(AgrimateParams)}
    src = Path("sheaf/agrimate/rt_solver.py").read_text()
    assert "run_agrimate" not in src
    assert "import nlopt" not in src
    assert "freeze_q_oth" not in (ROOT / "sheaf" / "agrimate" / "params.py").read_text()


def test_rt_solver_module_does_not_import_g1g2():
    tree = ast.parse(Path("sheaf/agrimate/rt_solver.py").read_text())
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


def test_rt_solver_dispatch_writer_does_not_clobber_later(tmp_path):
    living = tmp_path / "GATE0_REPRO_DISPATCH.md"
    living.write_text("Last completed: fig4\nNext paste: never\n")
    metrics = {
        "last_first": 0.812,
        "last_first_author": 1.004,
        "item3_pass": False,
        "moy_host": 2374.0,
        "moy_author": 1.32,
        "unconverged": 1091,
        "n_solves": 5832,
        "failed": 0,
    }
    write_rt_solver_dispatch(metrics, path=living)
    assert living.read_text() == "Last completed: fig4\nNext paste: never\n"


def test_rt_solver_score_locks_when_present():
    import pandas as pd

    note = OUT_DEFAULT / "rt_solver.md"
    csv = OUT_DEFAULT / "score_rt_solver.csv"
    if not note.is_file() or not csv.is_file():
        return
    text = note.read_text()
    assert "Not a freeze" in text or "not a freeze" in text.lower()
    assert "Not a pin" in text or "not a pin" in text.lower()
    assert "L1–L8" in text
    assert "Do not copy Julia" in text
    assert "NLP not re-run" in text or "not an NLP re-run" in text.lower()
    assert "Next paste: leave labelled" in text
    tab = pd.read_csv(csv).iloc[0]
    assert bool(tab["nlp_rerun"]) is False
    assert bool(tab["nlopt_copied"]) is False
    assert bool(tab["implemented"]) is False
    assert abs(float(tab["last_first"]) - 0.812) < 0.01
    assert bool(tab["item3_pass"]) is False
    assert float(tab["moy_host"]) > 100.0
    assert float(tab["alpha_i"]) == 3.2
    assert int(tab["plan_maxiter"]) == 40
    for name in PROTECTED_THREE_SCENARIO:
        assert (OUT_DEFAULT / name).is_file(), name
