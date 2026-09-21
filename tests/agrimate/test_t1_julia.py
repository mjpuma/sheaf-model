"""T1: author Julia inspect-only. No copy, no freeze, no wheat_params retune."""
from __future__ import annotations

import ast
from dataclasses import fields
from pathlib import Path

import pandas as pd

from sheaf.agrimate.fig4_config import PROTECTED_THREE_SCENARIO
from sheaf.agrimate.model import AgrimateSim
from sheaf.agrimate.params import AgrimateParams, wheat_params
from sheaf.agrimate.t1_julia import (
    inspect_tmp_trees,
    t1_metrics,
    write_t1_dispatch,
)
from sheaf.agrimate.validation import OUT_DEFAULT
from sheaf.agrimate.wheat_data import prepare_wheat
from sheaf.agrimate.xi_split import n_julia_sources

ROOT = Path(__file__).resolve().parents[2]
DISPATCH = ROOT / "diagnostics" / "GATE0_REPRO_DISPATCH.md"


def test_no_julia_copied_into_sheaf():
    sheaf = ROOT / "sheaf"
    jl = [p for p in sheaf.rglob("*.jl") if ".git" not in p.parts]
    assert jl == []
    assert n_julia_sources() == 0
    assert n_julia_sources(sheaf) == 0


def test_freeze_not_adopted_and_wheat_params_stay():
    p = wheat_params()
    assert p.alpha_i == 3.2
    assert p.zeta_penalty == 0.0
    assert p.n_for_months == 3
    assert p.p_sto_annual == 0.1
    assert p.xmin_share == 0.2
    assert p.tau_exp == 0.5
    assert "freeze_q_oth" not in {f.name for f in fields(AgrimateParams)}
    src = (ROOT / "sheaf" / "agrimate" / "params.py").read_text()
    assert "freeze_q_oth" not in src
    data = prepare_wheat(start_year=2006, end_year=2006, params=p)
    sim = AgrimateSim(data, params=p, use_anomalies=False, use_restrictions=False)
    assert sim.freeze_q_oth is False


def test_t1_note_and_csv_lock_obtain_and_deltas():
    note = OUT_DEFAULT / "t1_julia.md"
    csv = OUT_DEFAULT / "score_t1_julia.csv"
    assert note.is_file()
    assert csv.is_file()
    text = note.read_text()
    assert "Inspect-only" in text
    assert "Not copied" in text or "not copied" in text.lower()
    assert "Not a freeze" in text or "not a freeze" in text.lower()
    assert "L1–L8" in text
    assert "Next paste: T2" in text
    assert "LD_SLSQP" in text
    assert "L-BFGS-B" in text
    assert "optimal_sales_foreign[3:end]" in text
    assert "scalar" in text.lower()
    assert "Do not copy Julia" in text
    assert "wheat_params()" in text
    assert "1.444" in text
    tab = pd.read_csv(csv).iloc[0]
    assert bool(tab["obtained"]) is True
    assert bool(tab["d22_differs"]) is True
    assert bool(tab["solver_differs"]) is True
    assert bool(tab["freeze_in_author"]) is False
    assert bool(tab["freeze_q_oth_on_params"]) is False
    assert bool(tab["ema_weight_match"]) is True
    assert int(tab["n_jl_sheaf"]) == 0
    assert float(tab["alpha_i"]) == 3.2
    assert str(tab["next_paste"]) == "T2"
    m = t1_metrics()
    assert m["d22_differs"] is True
    assert m["n_jl_sheaf"] == 0


def test_t1_module_does_not_import_g1g2():
    tree = ast.parse(Path("sheaf/agrimate/t1_julia.py").read_text())
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


def test_t1_did_not_overwrite_three_scenario():
    for name in PROTECTED_THREE_SCENARIO:
        assert (OUT_DEFAULT / name).is_file(), name


def test_t1_dispatch_writer_does_not_clobber_later(tmp_path):
    living = tmp_path / "GATE0_REPRO_DISPATCH.md"
    living.write_text("Last completed: T2\nNext paste: T3\n")
    write_t1_dispatch(t1_metrics(), path=living)
    assert living.read_text() == "Last completed: T2\nNext paste: T3\n"


def test_live_tmp_probe_agrees_when_present():
    live = inspect_tmp_trees()
    if live["z14_present"]:
        assert live["z14_has_two_markets"] is True
        assert live["z14_has_foreign_vector"] is True
        assert live["z14_has_horizon_shift"] is True
        assert live["z14_has_freeze"] is False
        assert live["z14_nlopt"] is True
        assert live["z14_alpha_foreign_32"] is True
        assert live["n_jl_14022004"] > 0
    if live["gitlab_present"]:
        assert live["gitlab_has_expected_others"] is True
        assert live["gitlab_has_two_markets"] is False
        assert live["n_jl_gitlab"] > 0
