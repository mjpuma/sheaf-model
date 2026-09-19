"""R2: labelled Fig. 4 knobs. wheat_params() stay 14022004 defaults."""
from __future__ import annotations

import ast
from pathlib import Path

import pandas as pd
import pytest

from sheaf.agrimate.fig4_config import (
    CAN_SET,
    CANNOT_SET,
    PROTECTED_THREE_SCENARIO,
    apply_alpha_i,
    fig4_experiment_region_path,
    what_is_settable,
)
from sheaf.agrimate.params import fig4_experiment_params, wheat_params
from sheaf.agrimate.regions import D9_ALPHA, REGION_NAMES
from sheaf.agrimate.validation import OUT_DEFAULT
from sheaf.agrimate.wheat_data import prepare_wheat

ROOT = Path(__file__).resolve().parents[2]


def test_wheat_params_stay_14022004_not_fig4():
    p = wheat_params()
    assert p.alpha_i == 3.2
    assert p.alpha_nash == 3.0
    assert p.zeta_penalty == 0.0
    assert p.n_for_months == 3
    assert p.p_sto_annual == 0.1
    assert p.xmin_share == 0.2


def test_fig4_experiment_params_are_netcdf_knobs():
    p = fig4_experiment_params()
    assert p.alpha_i == 3.5
    assert p.alpha_nash == 3.0
    assert p.zeta_penalty == 1.0
    assert p.n_for_months == 6
    assert p.p_sto_annual == 0.1
    assert p.xmin_share == 0.2
    assert p.sigma_ces == 2.0
    assert p.eps_c == 0.1
    w = wheat_params()
    assert w.alpha_i != p.alpha_i
    assert w.zeta_penalty != p.zeta_penalty
    assert w.n_for_months != p.n_for_months


def test_cannot_set_is_labelled_and_region_path_is_none():
    avail = what_is_settable()
    assert avail["region_path"] is None
    assert fig4_experiment_region_path() is None
    assert fig4_experiment_region_path(ROOT / "data" / "faostat_network") is None
    joined = " ".join(avail["cannot_set"])
    assert "FAOSTAT Food Balances" in joined
    assert "Egypt" in joined
    assert "EU28" in joined or "AgrimateEU28" in joined
    assert "2000" in joined
    assert "old-demand-dynamics" in joined
    assert "14022004" in joined
    assert avail["faostat_fb_files"] == []
    assert avail["usda_is_default"] is True
    assert avail["host_has_egypt_node"] is False
    assert avail["host_has_eu28"] is False
    assert avail["wheat_params_unchanged"] is True
    assert any("alpha_i=3.5" in s for s in CAN_SET)
    assert any("zeta_penalty=1.0" in s for s in CAN_SET)
    assert any("n_for_months=6" in s for s in CAN_SET)
    assert any("FAOSTAT" in s for s in CANNOT_SET)


def test_apply_alpha_i_keeps_usda_quantities_and_d9():
    d0 = prepare_wheat(start_year=2006, end_year=2006, params=wheat_params())
    d1 = apply_alpha_i(d0, fig4_experiment_params().alpha_i)
    assert d0.regions == d1.regions == list(REGION_NAMES)
    assert (d0.H_annual == d1.H_annual).all()
    assert (d0.anomaly == d1.anomaly).all()
    assert (d0.delta == d1.delta).all()
    for i, r in enumerate(d0.regions):
        if r in D9_ALPHA:
            assert d1.alpha_d[i] == D9_ALPHA[r]
            assert d0.alpha_d[i] == D9_ALPHA[r]


def test_fig4_config_module_does_not_import_g1g2():
    tree = ast.parse(Path("sheaf/agrimate/fig4_config.py").read_text())
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


def test_fig4_config_note_labels_cannot_set_and_does_not_adopt():
    note = OUT_DEFAULT / "fig4_config.md"
    csv = OUT_DEFAULT / "score_fig4_config.csv"
    if not note.is_file() or not csv.is_file():
        pytest.skip("run scripts/score_agrimate_fig4_config.py first")
    text = note.read_text()
    assert "Cannot set" in text or "cannot set" in text
    assert "FAOSTAT Food Balances" in text
    assert "Egypt" in text
    assert "old-demand-dynamics" in text
    assert "not a retune" in text.lower()
    assert "wheat_params" in text
    assert "3.2" in text
    assert "L1–L8" in text
    assert "α_foreign=10" in text or "Bai" in text
    assert "G1" in text
    tab = pd.read_csv(OUT_DEFAULT / "score_fig4_config.csv")
    assert set(tab["label"]) == {"default", "fig4_knobs"}
    assert set(tab["scenario"]) == {"harvest_amis", "undisturbed"}
    d = tab[(tab["label"] == "default") & (tab["scenario"] == "harvest_amis")].iloc[0]
    c = tab[(tab["label"] == "fig4_knobs") & (tab["scenario"] == "harvest_amis")].iloc[0]
    assert d["alpha_i"] == 3.2
    assert d["zeta_penalty"] == 0.0
    assert d["n_for_months"] == 3
    assert c["alpha_i"] == 3.5
    assert c["zeta_penalty"] == 1.0
    assert c["n_for_months"] == 6
    assert d["failed"] == 0
    assert c["failed"] == 0
    assert wheat_params().alpha_i == 3.2
    # R2 numbers stay in the living dispatch until a later session
    # replaces them. Do not freeze "Last completed: R2".
    dispatch = (ROOT / "diagnostics" / "GATE0_REPRO_DISPATCH.md").read_text()
    assert "Next paste: R10" in dispatch
    assert "26.8" in dispatch and "13.3" in dispatch


def test_r2_did_not_overwrite_three_scenario_csvs():
    for name in PROTECTED_THREE_SCENARIO:
        assert (OUT_DEFAULT / name).is_file(), name
    prices = pd.read_csv(OUT_DEFAULT / "prices_three_scenarios.csv")
    years = {int(str(p).split("-")[0]) for p in prices.iloc[:, 0]}
    assert min(years) <= 2006 and max(years) >= 2011
