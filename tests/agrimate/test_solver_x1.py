"""Solver: x1 from demand + SLSQP. Not a freeze, pin, or Julia copy."""
from __future__ import annotations

import ast
from dataclasses import fields
from pathlib import Path

import numpy as np

from sheaf.agrimate.fig4_config import PROTECTED_THREE_SCENARIO
from sheaf.agrimate.model import AgrimateSim
from sheaf.agrimate.optimize import (
    clip_demand_x1,
    demand_x1_from_ask,
)
from sheaf.agrimate.params import AgrimateParams, wheat_params
from sheaf.agrimate.solver_x1 import write_solver_dispatch
from sheaf.agrimate.validation import OUT_DEFAULT
from sheaf.agrimate.wheat_data import prepare_wheat
from sheaf.agrimate.xi_split import n_julia_sources

ROOT = Path(__file__).resolve().parents[2]


def test_solver_does_not_copy_julia_or_freeze_or_retune():
    assert n_julia_sources() == 0
    p = wheat_params()
    assert p.alpha_i == 3.2
    assert p.zeta_penalty == 0.0
    assert p.n_for_months == 3
    assert p.plan_maxiter == 40
    assert "freeze_q_oth" not in {f.name for f in fields(AgrimateParams)}
    opt = (ROOT / "sheaf" / "agrimate" / "optimize.py").read_text()
    assert "SLSQP" in opt
    assert "x1" in opt
    assert "nlopt" not in opt.lower()
    model = (ROOT / "sheaf" / "agrimate" / "model.py").read_text()
    assert "demand_x1_from_ask" in model
    assert "expected_others_sales_foreign" not in model
    # Author X_avg is per-step mean harvest, not annual.
    assert "XD_star[r]) + float(d.XI_star[r])) * n_y" not in model
    src = (ROOT / "sheaf" / "agrimate" / "params.py").read_text()
    assert "freeze_q_oth" not in src
    data = prepare_wheat(start_year=2006, end_year=2006, params=p)
    sim = AgrimateSim(data, params=p, use_anomalies=False, use_restrictions=False)
    assert sim.freeze_q_oth is False
    assert sim.x1_from_demand is False


def test_solver_module_does_not_import_g1g2():
    tree = ast.parse(Path("sheaf/agrimate/solver_x1.py").read_text())
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


def test_solver_dispatch_writer_does_not_clobber_later(tmp_path):
    living = tmp_path / "GATE0_REPRO_DISPATCH.md"
    living.write_text("Last completed: fig4\nNext paste: never\n")
    metrics = {
        "last_first": 1.0,
        "last_first_author": 1.004,
        "item3_pass": True,
        "unconverged": 0,
        "n_solves": 10,
        "failed": 0,
    }
    write_solver_dispatch(metrics, path=living)
    assert living.read_text() == "Last completed: fig4\nNext paste: never\n"


def test_solver_score_locks_when_present():
    import pandas as pd

    note = OUT_DEFAULT / "solver_x1.md"
    csv = OUT_DEFAULT / "score_solver_x1.csv"
    if not note.is_file() or not csv.is_file():
        return
    text = note.read_text()
    assert "SLSQP" in text
    assert "Not a freeze" in text or "not a freeze" in text.lower()
    assert "Not a pin" in text or "not a pin" in text.lower()
    assert "L1–L8" in text
    assert "Do not copy Julia" in text
    assert "plan_maxiter" in text
    tab = pd.read_csv(csv).iloc[0]
    assert bool(tab["implemented"]) is True
    assert str(tab["method"]) == "SLSQP"
    assert bool(tab["x1_fixed"]) is True
    assert bool(tab["nlopt_copied"]) is False
    assert int(tab["plan_maxiter"]) == 40
    assert float(tab["alpha_i"]) == 3.2
    for name in PROTECTED_THREE_SCENARIO:
        assert (OUT_DEFAULT / name).is_file(), name


def test_demand_x1_from_ask_iota_and_clip():
    ask = np.array([[0.5, 0.1], [0.2, 0.4]])
    xd, xi = demand_x1_from_ask(ask, 0, S0=0.0, H0=10.0, iota=0.001, x_avg=1.0)
    assert abs(xd - 0.5) < 1e-12
    assert abs(xi - 0.1) < 1e-12
    tiny = np.array([[1e-9, 1e-9], [1e-9, 1e-9]])
    xd, xi = demand_x1_from_ask(tiny, 0, S0=0.0, H0=10.0, iota=0.001, x_avg=100.0)
    assert xd == 0.0 and xi == 0.0
    assert clip_demand_x1(1.0, 1.0, 0.0, 1.0) == (1.0, 0.0)
