"""D.22 vector+shift of planned foreign sales. Not a freeze, pin, or solver switch."""
from __future__ import annotations

import ast
from dataclasses import fields
from pathlib import Path

import numpy as np
import pandas as pd

from sheaf.agrimate.d22 import (
    ema_weight,
    init_expected_others_foreign,
    observe_planned_foreign,
    pad_planned_foreign,
    shift_ema_expected_others,
    write_d22_dispatch,
)
from sheaf.agrimate.fig4_config import PROTECTED_THREE_SCENARIO
from sheaf.agrimate.model import AgrimateSim
from sheaf.agrimate.params import AgrimateParams, wheat_params
from sheaf.agrimate.validation import OUT_DEFAULT
from sheaf.agrimate.wheat_data import prepare_wheat
from sheaf.agrimate.xi_split import n_julia_sources

ROOT = Path(__file__).resolve().parents[2]


def test_d22_helpers_match_sourced_lengths():
    n_r, n_y, n_del = 3, 24, 2
    path = np.ones((n_r, n_y))
    path[0] = 2.0
    path[1] = 3.0
    Q = init_expected_others_foreign(path, n_start=0)
    assert Q.shape == (n_r, n_y)
    # Others of region 0 at slot 0: path sum at idx=1 minus own.
    world1 = float(path[:, 1].sum())
    assert abs(Q[0, 0] - (world1 - path[0, 1])) < 1e-12
    plan = np.arange(n_r * 10, dtype=float).reshape(n_r, 10)
    pad = np.array([100.0, 200.0, 300.0])
    padded = pad_planned_foreign(plan, t=0, n_hor=n_y, pad=pad)
    assert padded.shape == (n_r, n_y + 1)
    assert np.allclose(padded[:, n_y], pad)
    obs = observe_planned_foreign(padded, n_del)
    assert obs.shape == (n_r, n_y - 1)
    # Self excluded: obs[0] == padded[1, n_del:] + padded[2, n_del:]
    assert np.allclose(obs[0], padded[1, n_del:] + padded[2, n_del:])
    w = ema_weight(0.5, 24)
    assert abs(w - 1.0 / 12.0) < 1e-12
    new = shift_ema_expected_others(Q, obs, w)
    assert new.shape == Q.shape
    expect = w * obs + (1.0 - w) * Q[:, 1:]
    assert np.allclose(new[:, :-1], expect)
    assert np.allclose(new[:, -1], new[:, :-1].mean(axis=1))
    instant = shift_ema_expected_others(Q, obs, 1.0)
    assert np.allclose(instant[:, :-1], obs)


def test_d22_does_not_copy_julia_or_freeze_or_retune():
    assert n_julia_sources() == 0
    p = wheat_params()
    assert p.alpha_i == 3.2
    assert p.zeta_penalty == 0.0
    assert p.n_for_months == 3
    assert "freeze_q_oth" not in {f.name for f in fields(AgrimateParams)}
    src = (ROOT / "sheaf" / "agrimate" / "params.py").read_text()
    assert "freeze_q_oth" not in src
    model = (ROOT / "sheaf" / "agrimate" / "model.py").read_text()
    assert "expected_others_sales_foreign" not in model
    assert "optimal_sales_foreign" not in model
    assert "shift_ema_expected_others" in model
    assert "init_expected_others_foreign" in model
    data = prepare_wheat(start_year=2006, end_year=2006, params=p)
    sim = AgrimateSim(data, params=p, use_anomalies=False, use_restrictions=False)
    assert sim.freeze_q_oth is False


def test_d22_module_does_not_import_g1g2():
    tree = ast.parse(Path("sheaf/agrimate/d22.py").read_text())
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


def test_d22_dispatch_writer_does_not_clobber_later(tmp_path):
    living = tmp_path / "GATE0_REPRO_DISPATCH.md"
    living.write_text("Last completed: solver\nNext paste: leave labelled\n")
    metrics = {
        "last_first": 1.2,
        "last_first_author": 1.004,
        "item3_pass": False,
        "unconverged": 1,
        "n_solves": 10,
        "failed": 0,
    }
    write_d22_dispatch(metrics, path=living)
    assert living.read_text() == "Last completed: solver\nNext paste: leave labelled\n"


def test_d22_score_locks_when_present():
    note = OUT_DEFAULT / "d22.md"
    csv = OUT_DEFAULT / "score_d22.csv"
    if not note.is_file() or not csv.is_file():
        return
    text = note.read_text()
    assert "Not a freeze" in text or "not a freeze" in text.lower()
    assert "Not a pin" in text or "not a pin" in text.lower()
    assert "L1–L8" in text
    assert "Next paste: solver" in text
    assert "Do not copy Julia" in text
    tab = pd.read_csv(csv).iloc[0]
    assert bool(tab["implemented"]) is True
    assert bool(tab["author_does_freeze"]) is False
    assert bool(tab["freeze_q_oth_on_params"]) is False
    assert int(tab["n_julia"]) == 0
    assert float(tab["alpha_i"]) == 3.2
    assert bool(tab["solver_unchanged"]) is True
    assert bool(tab["item3_pass"]) is False
    assert bool(tab["item3_onesided"]) is True
    assert abs(float(tab["last_first"]) - 0.772) < 0.01
    for name in PROTECTED_THREE_SCENARIO:
        assert (OUT_DEFAULT / name).is_file(), name
