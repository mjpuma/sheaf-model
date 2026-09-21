"""Stay not-accepted: G0-P still rejected after T1–T3. Do not start G1."""
from __future__ import annotations

import ast
from dataclasses import fields
from pathlib import Path

import pandas as pd

from sheaf.agrimate.fig4_config import PROTECTED_THREE_SCENARIO
from sheaf.agrimate.methods import publication_bar
from sheaf.agrimate.params import AgrimateParams, wheat_params
from sheaf.agrimate.regions import REGION_NAMES
from sheaf.agrimate.stay_not_accepted import sna_metrics, write_sna_dispatch
from sheaf.agrimate.validation import OUT_DEFAULT
from sheaf.agrimate.wheat_data import prepare_wheat
from sheaf.agrimate.xi_split import n_julia_sources

ROOT = Path(__file__).resolve().parents[2]


def test_sna_does_not_accept_or_start_g1():
    bar = publication_bar()
    assert bar["accepted"] is False
    assert bar["item3_undisturbed"] is False
    assert bar["item5_historical"] is False
    p = wheat_params()
    assert p.alpha_i == 3.2
    assert p.zeta_penalty == 0.0
    assert p.n_for_months == 3
    assert "Egypt" not in REGION_NAMES
    assert "freeze_q_oth" not in {f.name for f in fields(AgrimateParams)}
    assert n_julia_sources() == 0
    data = prepare_wheat(start_year=2006, end_year=2006, params=p)
    assert any("USDA PSD" in n and "not FAOSTAT Food Balances" in n for n in data.notes)
    src = (ROOT / "sheaf" / "agrimate" / "stay_not_accepted.py").read_text()
    assert "dynamic_coupled" not in src
    assert "dynamic_policy" not in src


def test_sna_note_and_csv_lock_stop():
    note = OUT_DEFAULT / "stay_not_accepted.md"
    csv = OUT_DEFAULT / "score_stay_not_accepted.csv"
    assert note.is_file()
    assert csv.is_file()
    text = note.read_text()
    assert "Do not start G1" in text
    assert "not accepted" in text.lower()
    assert "T-queue exhausted" in text or "T-queue is exhausted" in text
    assert "L1–L8" in text
    assert "wheat_params()" in text
    assert "3.2" in text
    assert "Egypt" in text
    assert "Next paste: stay not-accepted" in text
    assert "1.444" in text
    tab = pd.read_csv(csv).iloc[0]
    assert bool(tab["accepted"]) is False
    assert bool(tab["t2_implemented"]) is False
    assert bool(tab["t3_adopted"]) is False
    assert bool(tab["egypt_on_c1"]) is False
    assert bool(tab["usda_is_default"]) is True
    assert int(tab["n_jl_sheaf"]) == 0
    assert bool(tab["g1_started"]) is False
    assert bool(tab["t_queue_exhausted"]) is True
    assert str(tab["next_paste"]) == "stay not-accepted"
    assert float(tab["alpha_i"]) == 3.2
    m = sna_metrics()
    assert m["accepted"] is False
    assert m["g1_started"] is False


def test_sna_module_does_not_import_g1g2():
    tree = ast.parse(Path("sheaf/agrimate/stay_not_accepted.py").read_text())
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


def test_sna_did_not_overwrite_three_scenario():
    for name in PROTECTED_THREE_SCENARIO:
        assert (OUT_DEFAULT / name).is_file(), name


def test_sna_dispatch_writer_does_not_clobber_later(tmp_path):
    living = tmp_path / "GATE0_REPRO_DISPATCH.md"
    living.write_text("Last completed: G1\nNext paste: never\n")
    write_sna_dispatch(sna_metrics(), path=living)
    assert living.read_text() == "Last completed: G1\nNext paste: never\n"
