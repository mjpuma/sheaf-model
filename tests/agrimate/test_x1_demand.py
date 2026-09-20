"""R5: x1=demand labelled experiment. Default off recovers today's path."""
from __future__ import annotations

import ast
from pathlib import Path

import numpy as np
import pandas as pd

from sheaf.agrimate.fig4_config import PROTECTED_THREE_SCENARIO
from sheaf.agrimate.model import AgrimateSim, run_agrimate
from sheaf.agrimate.params import wheat_params
from sheaf.agrimate.validation import OUT_DEFAULT
from sheaf.agrimate.wheat_data import prepare_wheat

ROOT = Path(__file__).resolve().parents[2]


def test_x1_from_demand_default_off():
    data = prepare_wheat(start_year=2006, end_year=2006, params=wheat_params())
    sim = AgrimateSim(data, params=wheat_params(),
                      use_anomalies=False, use_restrictions=False)
    assert sim.x1_from_demand is False
    p = wheat_params()
    assert p.alpha_i == 3.2
    assert p.zeta_penalty == 0.0
    assert p.xmin_share == 0.2
    assert p.n_for_months == 3


def test_x1_from_demand_default_off_recovers_path():
    data = prepare_wheat(start_year=2006, end_year=2006, params=wheat_params())
    kwargs = dict(
        data=data, params=wheat_params(),
        use_anomalies=False, use_restrictions=False,
        start_year=2006, end_year=2006,
    )
    a = run_agrimate(**kwargs)
    b = run_agrimate(**kwargs, x1_from_demand=False)
    assert a.x1_from_demand is False
    assert b.x1_from_demand is False
    assert np.allclose(a.price_index, b.price_index)
    assert np.allclose(a.inflow, b.inflow)
    assert np.allclose(a.S_consumer, b.S_consumer)
    assert np.allclose(a.consumption, b.consumption)
    assert np.allclose(a.xi_ship, b.xi_ship)


def test_x1_from_demand_on_moves_inflow():
    data = prepare_wheat(start_year=2006, end_year=2006, params=wheat_params())
    kwargs = dict(
        data=data, params=wheat_params(),
        use_anomalies=False, use_restrictions=False,
        start_year=2006, end_year=2006,
    )
    off = run_agrimate(**kwargs, x1_from_demand=False)
    on = run_agrimate(**kwargs, x1_from_demand=True)
    assert on.x1_from_demand is True
    assert not np.allclose(on.inflow, off.inflow)
    # p_w is XI-weighted offers; x1 does not enter D.7.
    assert np.allclose(on.price_index, off.price_index)
    assert wheat_params().alpha_i == 3.2


def test_r5_note_does_not_adopt_or_ration():
    note = OUT_DEFAULT / "x1_demand.md"
    csv = OUT_DEFAULT / "score_x1_demand.csv"
    assert note.is_file()
    assert csv.is_file()
    text = note.read_text()
    assert "Not adopted" in text or "not adopted" in text.lower()
    assert "min(supply, demand)" in text
    assert "L1–L8" in text
    assert "wheat_params" in text
    assert "Next paste: R6" in text
    assert "x1_from_demand" in text or "x1=demand" in text
    tab = pd.read_csv(csv)
    assert bool(tab["x1_from_demand_off"].iloc[0]) is False
    assert bool(tab["x1_from_demand_on"].iloc[0]) is True
    assert float(tab["max_abs_dinflow"].iloc[0]) > 0.0
    assert wheat_params().alpha_i == 3.2
    assert wheat_params().zeta_penalty == 0.0


def test_r5_module_does_not_import_g1g2():
    tree = ast.parse(Path("sheaf/agrimate/x1_demand.py").read_text())
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


def test_r5_did_not_overwrite_three_scenario():
    for name in PROTECTED_THREE_SCENARIO:
        assert (OUT_DEFAULT / name).is_file(), name
    dispatch = (ROOT / "diagnostics" / "GATE0_REPRO_DISPATCH.md").read_text()
    assert "Last completed: R5" in dispatch
    assert "Next paste: R6" in dispatch
    assert "not adopted" in dispatch.lower() or "do not adopt" in dispatch.lower()
