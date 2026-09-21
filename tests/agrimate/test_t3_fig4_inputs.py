"""T3: FAO-since-2005 + AgrimateEU28+Egypt labelled, not adopted, not C.1."""
from __future__ import annotations

import ast
from dataclasses import fields
from pathlib import Path

import pandas as pd

from sheaf.agrimate.fig4_config import (
    PROTECTED_THREE_SCENARIO,
    fig4_experiment_region_path,
)
from sheaf.agrimate.model import AgrimateSim
from sheaf.agrimate.params import AgrimateParams, fig4_experiment_params, wheat_params
from sheaf.agrimate.regions import REGION_NAMES
from sheaf.agrimate.s4_a7 import FIG4_EU28_EGYPT_NAMES
from sheaf.agrimate.t3_fig4_inputs import (
    ANOM_CSV,
    EXTRACT_DIR,
    ISO_CSV,
    inspect_gitlab_trees,
    load_eu28_egypt_iso3,
    load_fao_since_2005,
    t3_metrics,
    write_t3_dispatch,
)
from sheaf.agrimate.validation import OUT_DEFAULT
from sheaf.agrimate.wheat_data import prepare_wheat
from sheaf.agrimate.xi_split import n_julia_sources

ROOT = Path(__file__).resolve().parents[2]


def test_t3_does_not_invent_egypt_or_retune():
    assert "Egypt" not in REGION_NAMES
    assert "EU-28" not in REGION_NAMES
    assert "EU-27" in REGION_NAMES
    assert "Brazil" in REGION_NAMES
    p = wheat_params()
    assert p.alpha_i == 3.2
    assert p.zeta_penalty == 0.0
    assert p.n_for_months == 3
    assert p.p_sto_annual == 0.1
    assert p.xmin_share == 0.2
    fig4 = fig4_experiment_params()
    assert fig4.alpha_i == 3.5
    assert fig4.zeta_penalty == 1.0
    assert fig4.n_for_months == 6
    assert "freeze_q_oth" not in {f.name for f in fields(AgrimateParams)}
    src = (ROOT / "sheaf" / "agrimate" / "params.py").read_text()
    assert "freeze_q_oth" not in src
    data = prepare_wheat(start_year=2006, end_year=2006, params=p)
    assert any("USDA PSD" in n and "not FAOSTAT Food Balances" in n for n in data.notes)
    assert "Egypt" not in data.regions
    sim = AgrimateSim(data, params=p, use_anomalies=False, use_restrictions=False)
    assert sim.freeze_q_oth is False
    assert n_julia_sources() == 0
    assert n_julia_sources(ROOT / "sheaf") == 0


def test_t3_extracts_are_labelled_not_region_path():
    assert ISO_CSV.is_file()
    assert ANOM_CSV.is_file()
    iso = load_eu28_egypt_iso3()
    anom = load_fao_since_2005()
    assert set(iso["region"]) == set(FIG4_EU28_EGYPT_NAMES)
    assert iso["region"].nunique() == 27
    egypt = iso[iso["region"] == "Egypt"]
    assert list(egypt["iso3"]) == ["EGY"]
    na = set(iso.loc[iso["region"] == "Northern Africa", "iso3"])
    assert "EGY" not in na
    eu28 = set(iso.loc[iso["region"] == "EU-28", "iso3"])
    assert {"GBR", "BLX", "CSK"} <= eu28
    assert "Brazil" not in set(iso["region"])
    assert set(anom["region"]) == set(FIG4_EU28_EGYPT_NAMES)
    assert set(anom["year"]) == set(range(2000, 2012))
    e2004 = anom[(anom["region"] == "Egypt") & (anom["year"] == 2004)].iloc[0]
    e2005 = anom[(anom["region"] == "Egypt") & (anom["year"] == 2005)].iloc[0]
    assert float(e2004["relative_since_2005"]) == 0.0
    assert abs(float(e2004["relative"])) > 0
    assert abs(float(e2005["relative_since_2005"]) - float(e2005["relative"])) < 1e-12
    assert float(e2005["relative_since_2005"]) > 0
    ukr = anom[(anom["region"] == "Ukraine") & (anom["year"] == 2008)].iloc[0]
    assert float(ukr["relative"]) > 0.3
    assert fig4_experiment_region_path() is None
    assert fig4_experiment_region_path(EXTRACT_DIR) is None
    assert fig4_experiment_region_path(ROOT / "data" / "faostat_network") is None
    daily = list(EXTRACT_DIR.glob("harvest_anomalies*")) + list(
        EXTRACT_DIR.glob("harvest_trends*")
    )
    assert daily == []
    assert not (EXTRACT_DIR / "wheat_food_balance_fao.csv").exists()
    jl = [p for p in (ROOT / "sheaf").rglob("*.jl") if ".git" not in p.parts]
    assert jl == []


def test_t3_note_and_csv_lock_obtain_not_adopt():
    note = OUT_DEFAULT / "t3_fig4_inputs.md"
    csv = OUT_DEFAULT / "score_t3_fig4_inputs.csv"
    assert note.is_file()
    assert csv.is_file()
    text = note.read_text()
    assert "Not adopted" in text or "not adopted" in text.lower()
    assert "Do not invent an Egypt node" in text
    assert "Do not copy Julia" in text
    assert "Do not start G1" in text
    assert "L1–L8" in text
    assert "wheat_params()" in text
    assert "3.2" in text
    assert "fig4_experiment_params()" in text
    assert "AgrimateEU28" in text
    assert "FAOsince-2005" in text or "since-2005" in text
    assert "USDA" in text
    assert "Next paste: stay not-accepted" in text
    assert "1.444" in text
    tab = pd.read_csv(csv).iloc[0]
    assert bool(tab["obtained"]) is True
    assert bool(tab["adopted"]) is False
    assert bool(tab["egypt_on_c1"]) is False
    assert bool(tab["usda_is_default"]) is True
    assert bool(tab["wheat_params_unchanged"]) is True
    assert bool(tab["gitlab_fb_copied"]) is False
    assert bool(tab["daily_fao_vendored"]) is False
    assert int(tab["n_jl_sheaf"]) == 0
    assert bool(tab["freeze_q_oth_on_params"]) is False
    assert float(tab["alpha_i"]) == 3.2
    assert float(tab["fig4_alpha_i"]) == 3.5
    assert str(tab["next_paste"]) == "stay not-accepted"
    m = t3_metrics()
    assert m["obtained"] is True
    assert m["adopted"] is False
    assert m["egypt_on_c1"] is False
    assert m["names_match_netcdf"] is True
    assert m["na_has_egy"] is False
    assert m["class_obtain"] == "H"


def test_t3_module_does_not_import_g1g2():
    tree = ast.parse(Path("sheaf/agrimate/t3_fig4_inputs.py").read_text())
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


def test_t3_did_not_overwrite_three_scenario():
    for name in PROTECTED_THREE_SCENARIO:
        assert (OUT_DEFAULT / name).is_file(), name


def test_t3_dispatch_writer_does_not_clobber_later(tmp_path):
    living = tmp_path / "GATE0_REPRO_DISPATCH.md"
    living.write_text("Last completed: G1\nNext paste: never\n")
    write_t3_dispatch(t3_metrics(), path=living)
    assert living.read_text() == "Last completed: G1\nNext paste: never\n"


def test_live_gitlab_probe_agrees_when_present():
    live = inspect_gitlab_trees()
    if live["gitlab_present"]:
        assert live["gitlab_has_eu28_yaml"] is True
        assert live["gitlab_egypt_in_eu28_yaml"] is False
        assert live["n_jl_gitlab"] > 0
    if live["gitlab_fao_anom_present"]:
        assert live["gitlab_fao_trend_present"] is True
