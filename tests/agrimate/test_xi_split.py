"""R4: undisturbed xd/xi characterisation. No pin. wheat_params unchanged."""
from __future__ import annotations

import ast
from pathlib import Path

import pandas as pd

from sheaf.agrimate.fig4_config import PROTECTED_THREE_SCENARIO
from sheaf.agrimate.model import AgrimateSim
from sheaf.agrimate.params import wheat_params
from sheaf.agrimate.validation import OUT_DEFAULT
from sheaf.agrimate.wheat_data import prepare_wheat

ROOT = Path(__file__).resolve().parents[2]


def test_diagnostic_hooks_default_off():
    data = prepare_wheat(start_year=2006, end_year=2006, params=wheat_params())
    sim = AgrimateSim(data, params=wheat_params(),
                      use_anomalies=False, use_restrictions=False)
    assert sim.replan_stride == 1
    assert sim.freeze_q_oth is False
    p = wheat_params()
    assert p.alpha_i == 3.2
    assert p.zeta_penalty == 0.0
    assert p.xmin_share == 0.2
    assert p.n_for_months == 3


def test_r4_note_does_not_pin_or_adopt():
    note = OUT_DEFAULT / "xi_split.md"
    csv = OUT_DEFAULT / "score_xi_split.csv"
    assert note.is_file()
    assert csv.is_file()
    text = note.read_text()
    assert "Not a pin" in text or "not a pin" in text.lower()
    assert "decay" in text.lower()
    assert "L1–L8" in text
    assert "wheat_params" in text
    assert "Next paste: R5" in text
    assert "xmin_off" in text and "qoth_freeze" in text and "calendar_replan" in text
    tab = pd.read_csv(csv)
    assert set(tab["label"]) >= {"default", "xmin_off", "qoth_freeze", "calendar_replan"}
    d = tab[tab["label"] == "default"].iloc[0]
    assert d["last_first"] > 1.1
    assert abs(d["last_first_author"] - 1.0) < 0.05
    assert wheat_params().zeta_penalty == 0.0
    assert wheat_params().alpha_i == 3.2
    assert wheat_params().n_for_months == 3
    # A probe near 1 would be a finding, not an adoption.
    if (tab["last_first"] - 1.0).abs().min() < 0.05:
        assert "not adopted" in text.lower() or "Not adopted" in text
    cal = tab[tab["label"] == "calendar_replan"].iloc[0]
    assert cal["n_solves"] < d["n_solves"]
    assert cal["replan_stride"] == 24


def test_r4_module_does_not_import_g1g2():
    tree = ast.parse(Path("sheaf/agrimate/xi_split.py").read_text())
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


def test_r4_did_not_overwrite_three_scenario():
    for name in PROTECTED_THREE_SCENARIO:
        assert (OUT_DEFAULT / name).is_file(), name
    dispatch = (ROOT / "diagnostics" / "GATE0_REPRO_DISPATCH.md").read_text()
    assert "Last completed: R4" in dispatch
    assert "Next paste: R5" in dispatch
    assert "do not pin" in dispatch.lower() or "do not add a decay" in dispatch.lower()
