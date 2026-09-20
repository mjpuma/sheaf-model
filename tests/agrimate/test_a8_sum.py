"""R7: A8 mean-vs-sum sensitivity. Host unchanged. USDA stocks only."""
from __future__ import annotations

import ast
from pathlib import Path

import pandas as pd

from sheaf.agrimate.a8_sum import a8_mean_vs_sum_table
from sheaf.agrimate.fig4_config import PROTECTED_THREE_SCENARIO
from sheaf.agrimate.params import wheat_params
from sheaf.agrimate.validation import OUT_DEFAULT
from sheaf.agrimate.wheat_data import prepare_wheat


def test_host_still_uses_mean_not_sum():
    p = wheat_params()
    assert p.alpha_i == 3.2
    assert p.p_sto_annual == 0.1
    assert p.xmin_share == 0.2
    d = prepare_wheat(start_year=2006, end_year=2006, params=p)
    assert any("USDA PSD" in n and "not FAOSTAT Food Balances" in n for n in d.notes)
    tab = a8_mean_vs_sum_table()
    ch = tab[tab["region"] == "China"].iloc[0]
    ea = tab[tab["region"] == "Eastern Africa"].iloc[0]
    usa = tab[tab["region"] == "USA"].iloc[0]
    assert abs(ch["host_H"] - ch["H_mean"]) < 1e-6
    assert abs(ea["host_H"] - ea["H_mean"]) < 1e-6
    assert abs(usa["host_H"] - usa["H_sum"]) < 1e-6
    assert 0.45 < ch["H_mean_over_sum"] < 0.55
    assert 0.08 < ea["H_mean_over_sum"] < 0.12
    assert abs(usa["H_mean_over_sum"] - 1.0) < 0.02
    assert ch["stock_source"] == "USDA PSD ending_stocks"
    assert "stock_variation" not in tab.columns


def test_summed_china_and_ea_hcs():
    tab = a8_mean_vs_sum_table()
    ch = tab[tab["region"] == "China"].iloc[0]
    ea = tab[tab["region"] == "Eastern Africa"].iloc[0]
    assert ch["n_psd_members"] == 2
    assert "Hong Kong" in ch["psd_members"]
    assert ea["n_psd_members"] == 10
    assert abs(ch["H_sum"] / ch["H_mean"] - 2.0) < 0.02
    assert abs(ch["C_sum"] / ch["C_mean"] - 2.0) < 0.05
    assert abs(ch["S_sum"] / ch["S_mean"] - 2.0) < 0.02
    assert abs(ea["H_sum"] / ea["H_mean"] - 10.0) < 0.02
    assert abs(ea["C_sum"] / ea["C_mean"] - 10.0) < 0.02
    assert abs(ea["S_sum"] / ea["S_mean"] - 10.0) < 0.02
    assert wheat_params().xmin_share == 0.2
    assert wheat_params().p_sto_annual == 0.1


def test_a8_module_does_not_import_g1g2():
    tree = ast.parse(Path("sheaf/agrimate/a8_sum.py").read_text())
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
    text = Path("sheaf/agrimate/a8_sum.py").read_text()
    assert "ending_stocks" in text
    assert "ΔS" in text or "Stock Variation" in text


def test_r7_note_does_not_rewrite_host():
    note = OUT_DEFAULT / "a8_sum.md"
    csv = OUT_DEFAULT / "score_a8_sum.csv"
    assert note.is_file()
    assert csv.is_file()
    text = note.read_text()
    assert "Host unchanged" in text or "host unchanged" in text.lower()
    assert "Not adopted" in text or "not adopted" in text.lower()
    assert "ending_stocks" in text
    assert "ΔS" in text or "Stock Variation" in text
    assert "L1–L8" in text
    assert "xmin" in text
    assert "Next paste: R8" in text
    assert wheat_params().alpha_i == 3.2
    tab = pd.read_csv(csv)
    ch = tab[tab["region"] == "China"].iloc[0]
    assert 0.45 < float(ch["H_mean_over_sum"]) < 0.55
    for name in PROTECTED_THREE_SCENARIO:
        assert (OUT_DEFAULT / name).is_file(), name
    # Living dispatch moves after the R-queue plan. R7 numbers stay in a8_sum.md.
    text = note.read_text()
    assert "Next paste: R8" in text
    assert "host unchanged" in text.lower() or "Host unchanged" in text
