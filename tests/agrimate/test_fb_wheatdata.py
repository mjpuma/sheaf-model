"""R6: FBSH parallel WheatData. USDA stays prepare_wheat default. Not adopted."""
from __future__ import annotations

import ast
from pathlib import Path

import numpy as np
import pandas as pd

from sheaf.agrimate.faostat_fb import inventory
from sheaf.agrimate.fb_wheatdata import (
    DROP_AREA_CODES,
    map_fbsh_row,
    prepare_wheat_fbsh,
    quantity_table,
)
from sheaf.agrimate.fig4_config import PROTECTED_THREE_SCENARIO
from sheaf.agrimate.params import wheat_params
from sheaf.agrimate.validation import OUT_DEFAULT
from sheaf.agrimate.wheat_data import prepare_wheat


def test_usda_prepare_wheat_still_default():
    p = wheat_params()
    assert p.alpha_i == 3.2
    assert p.p_sto_annual == 0.1
    assert p.xmin_share == 0.2
    assert p.zeta_penalty == 0.0
    assert p.n_for_months == 3
    d = prepare_wheat(start_year=2006, end_year=2006, params=p)
    assert any("USDA PSD" in n and "not FAOSTAT Food Balances" in n for n in d.notes)
    assert not any(n.startswith("PARALLEL") for n in d.notes)


def test_map_drops_china_total_and_aggregates():
    iso, region, reason = map_fbsh_row(351, "China")
    assert region is None and reason == "duplicate_total"
    iso, region, reason = map_fbsh_row(5707, "European Union (27)")
    assert region is None and reason == "aggregate"
    iso, region, reason = map_fbsh_row(41, "China, mainland")
    assert iso == "CHN" and region == "China"
    iso, region, reason = map_fbsh_row(231, "United States of America")
    assert iso == "USA" and region == "USA"
    assert 351 in DROP_AREA_CODES
    assert inventory()["usda_is_default"] is True
    assert "wheat_food_balance_fao.csv" in inventory()["author_fb_present"]
    assert inventory()["fbsh_wheat_files"]


def test_fbsh_parallel_china_is_sum_matching_s1_usda():
    usda = prepare_wheat(start_year=2006, end_year=2008, params=wheat_params())
    fbsh = prepare_wheat_fbsh(start_year=2006, end_year=2008, params=wheat_params())
    assert usda.regions == fbsh.regions
    i_cn = usda.regions.index("China")
    i_us = usda.regions.index("USA")
    i_ea = usda.regions.index("Eastern Africa")
    assert abs(usda.H_annual[i_us] - fbsh.H_annual[i_us]) < 0.5
    # S1: USDA China/EA are member-sum, so they sit next to FBSH H (not 0.50× / 0.10×).
    assert abs(usda.H_annual[i_cn] / fbsh.H_annual[i_cn] - 1.0) < 0.15
    assert usda.H_annual[i_cn] > 100.0
    assert usda.H_annual[i_ea] > 2.0
    assert np.allclose(usda.Psi, fbsh.Psi)
    assert any("PARALLEL" in n for n in fbsh.notes)
    assert wheat_params().alpha_i == 3.2
    tab = quantity_table(usda, fbsh)
    assert set(tab["region"]) == set(usda.regions)
    # USDA stays default. FBSH is not adopted.
    assert any("USDA PSD" in n and "not FAOSTAT Food Balances" in n for n in usda.notes)


def test_fbsh_module_does_not_import_g1g2():
    tree = ast.parse(Path("sheaf/agrimate/fb_wheatdata.py").read_text())
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


def test_r6_note_does_not_adopt():
    note = OUT_DEFAULT / "fb_wheatdata.md"
    csv = OUT_DEFAULT / "score_fb_wheatdata.csv"
    q = OUT_DEFAULT / "score_fb_wheatdata_quantities.csv"
    assert note.is_file()
    assert csv.is_file()
    assert q.is_file()
    text = note.read_text()
    assert "Not adopted" in text or "not adopted" in text.lower()
    assert "Leave A1" in text
    assert "L1–L8" in text
    assert "wheat_params" in text
    assert "Next paste: R7" in text
    assert wheat_params().alpha_i == 3.2
    tab = pd.read_csv(q)
    cn = tab[tab["region"] == "China"].iloc[0]
    assert float(cn["H_ratio"]) > 1.5
    for name in PROTECTED_THREE_SCENARIO:
        assert (OUT_DEFAULT / name).is_file(), name
    # Living dispatch moves after R7. R6 numbers stay in fb_wheatdata.md.
    text = (OUT_DEFAULT / "fb_wheatdata.md").read_text()
    assert "Next paste: R7" in text
    assert "not adopted" in text.lower() or "Not adopted" in text
