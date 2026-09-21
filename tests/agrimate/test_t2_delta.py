"""T2: sourced D.22/solver delta labelled, not implemented."""
from __future__ import annotations

import ast
from dataclasses import fields
from pathlib import Path

import pandas as pd

from sheaf.agrimate.fig4_config import PROTECTED_THREE_SCENARIO
from sheaf.agrimate.model import AgrimateSim
from sheaf.agrimate.params import AgrimateParams, wheat_params
from sheaf.agrimate.t2_delta import t2_metrics, write_t2_dispatch
from sheaf.agrimate.validation import OUT_DEFAULT
from sheaf.agrimate.wheat_data import prepare_wheat
from sheaf.agrimate.xi_split import n_julia_sources

ROOT = Path(__file__).resolve().parents[2]


def test_t2_does_not_copy_julia_or_freeze():
    assert n_julia_sources() == 0
    p = wheat_params()
    assert p.alpha_i == 3.2
    assert p.zeta_penalty == 0.0
    assert p.n_for_months == 3
    assert "freeze_q_oth" not in {f.name for f in fields(AgrimateParams)}
    src = (ROOT / "sheaf" / "agrimate" / "params.py").read_text()
    assert "freeze_q_oth" not in src
    data = prepare_wheat(start_year=2006, end_year=2006, params=p)
    sim = AgrimateSim(data, params=p, use_anomalies=False, use_restrictions=False)
    assert sim.freeze_q_oth is False
    model = (ROOT / "sheaf" / "agrimate" / "model.py").read_text()
    assert "expected_others_sales_foreign" not in model
    assert "optimal_sales_foreign" not in model


def test_t2_note_cites_file_line_and_does_not_adopt():
    note = OUT_DEFAULT / "t2_delta.md"
    csv = OUT_DEFAULT / "score_t2_delta.csv"
    assert note.is_file()
    assert csv.is_file()
    text = note.read_text()
    assert "Not implemented" in text or "not implemented" in text.lower()
    assert "producer.jl" in text
    assert "452-464" in text or "452–464" in text
    assert "model.py" in text
    assert "347" in text
    assert "optimize.py" in text
    assert "LD_SLSQP" in text
    assert "L-BFGS-B" in text
    assert "Next paste: T3" in text
    assert "L1–L8" in text
    assert "Do not copy Julia" in text
    assert "wheat_params()" in text
    assert "1.444" in text
    tab = pd.read_csv(csv).iloc[0]
    assert bool(tab["t1_obtained"]) is True
    assert bool(tab["d22_differs"]) is True
    assert bool(tab["implemented"]) is False
    assert bool(tab["author_does_freeze"]) is False
    assert bool(tab["freeze_q_oth_on_params"]) is False
    assert int(tab["n_jl_sheaf"]) == 0
    assert str(tab["next_paste"]) == "T3"
    assert float(tab["alpha_i"]) == 3.2
    m = t2_metrics()
    assert m["implemented"] is False
    assert m["class_d22"] == "D"


def test_t2_module_does_not_import_g1g2():
    tree = ast.parse(Path("sheaf/agrimate/t2_delta.py").read_text())
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


def test_t2_did_not_overwrite_three_scenario():
    for name in PROTECTED_THREE_SCENARIO:
        assert (OUT_DEFAULT / name).is_file(), name


def test_t2_dispatch_writer_does_not_clobber_later(tmp_path):
    living = tmp_path / "GATE0_REPRO_DISPATCH.md"
    living.write_text("Last completed: T3\nNext paste: leave labelled\n")
    write_t2_dispatch(t2_metrics(), path=living)
    assert living.read_text() == "Last completed: T3\nNext paste: leave labelled\n"
