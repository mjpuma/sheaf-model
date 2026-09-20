"""Host reconstruction of wheat_food_balance_fao.csv. USDA stays default."""
from __future__ import annotations

import ast
from pathlib import Path

import pandas as pd

from sheaf.agrimate.author_fb import (
    FOOD_BALANCES,
    OUT_CSV,
    impute_food_balance_fao,
    remove_aggregate_areas,
)
from sheaf.agrimate.faostat_fb import FAOSTAT_FB, inventory
from sheaf.agrimate.fig4_config import fig4_experiment_region_path, what_is_settable
from sheaf.agrimate.params import wheat_params
from sheaf.agrimate.regions import REGION_NAMES
from sheaf.agrimate.validation import OUT_DEFAULT
from sheaf.agrimate.wheat_data import prepare_wheat

ROOT = Path(__file__).resolve().parents[2]


def test_reconstructed_csv_matches_author_schema_and_fbsh_production():
    assert OUT_CSV.is_file()
    df = pd.read_csv(OUT_CSV)
    assert list(df.columns) == [
        "ISO3 Code", "Area", "Area Code", "Year",
        "Production", "Domestic supply quantity",
        "Import Quantity", "Export Quantity", "Stock Variation", "Source",
    ]
    assert set(df["Year"].unique()) == {2006, 2007, 2008, 2009, 2010, 2011}
    assert set(df["Source"].unique()) <= {"FBS", "QCL+TCL"}
    assert (df["Area Code"] < 350).all()
    assert not ((df["Area Code"] > 260) & (df["Area Code"] < 270)).any()
    usa = df[(df["Area"] == "United States of America") & (df["Year"] == 2007)]
    chn = df[(df["Area"] == "China, mainland") & (df["Year"] == 2007)]
    assert abs(float(usa["Production"].iloc[0]) - 55820.0) < 1.0
    assert abs(float(chn["Production"].iloc[0]) - 109298.0) < 1.0
    assert str(chn["ISO3 Code"].iloc[0]) == "CHN"
    assert str(usa["Source"].iloc[0]) == "FBS"
    # Sourced reverse_stock_variation_sign: FBSH AFG 2006 5074=+150 → −150.
    afg = df[(df["Area"] == "Afghanistan") & (df["Year"] == 2006)]
    assert abs(float(afg["Stock Variation"].iloc[0]) - (-150.0)) < 1e-9
    # Identity after the sign flip: DS = P + I − X − SV.
    p, i, x, sv, ds = (
        float(afg["Production"].iloc[0]),
        float(afg["Import Quantity"].iloc[0]),
        float(afg["Export Quantity"].iloc[0]),
        float(afg["Stock Variation"].iloc[0]),
        float(afg["Domestic supply quantity"].iloc[0]),
    )
    assert abs((p + i - x - sv) - ds) < 1.0
    assert (df["Source"] == "QCL+TCL").any()
    assert df["ISO3 Code"].notna().all()
    # FAOSTAT Egypt is an area row, not a C.1 node.
    assert "Egypt" not in REGION_NAMES
    assert (df["ISO3 Code"] == "EGY").any()


def test_usda_still_prepare_wheat_default_after_reconstruction():
    p = wheat_params()
    assert p.alpha_i == 3.2
    assert p.p_sto_annual == 0.1
    assert p.xmin_share == 0.2
    assert p.zeta_penalty == 0.0
    assert p.n_for_months == 3
    d = prepare_wheat(start_year=2006, end_year=2006, params=p)
    assert any("USDA PSD" in n and "not FAOSTAT Food Balances" in n for n in d.notes)
    inv = inventory()
    assert inv["usda_is_default"] is True
    assert "wheat_food_balance_fao.csv" in inv["author_fb_present"]
    assert any(p.endswith("wheat_food_balance_fao.csv") for p in inv["food_balance_files"])
    assert inv["author_fb_bit_identical"] is False
    assert inv["author_fb_reconstruction"] is True
    assert "wheat_fbsh_2006_2011.csv" in inv["fbsh_wheat_files"]
    # Raw FBSH folder is not the cleaned output.
    assert not (FAOSTAT_FB / "wheat_food_balance_fao.csv").exists()


def test_impute_is_deterministic_and_drops_aggregates():
    a = impute_food_balance_fao()
    b = impute_food_balance_fao()
    pd.testing.assert_frame_equal(a, b)
    raw = pd.DataFrame({"Area Code": [41, 351, 265, 5000, 231]})
    kept = remove_aggregate_areas(raw)["Area Code"].tolist()
    assert kept == [41, 231]


def test_reconstruction_does_not_invent_egypt_or_switch_fig4():
    avail = what_is_settable()
    assert avail["host_has_egypt_node"] is False
    assert avail["host_has_eu28"] is False
    assert avail["region_path"] is None
    assert fig4_experiment_region_path() is None
    assert avail["usda_is_default"] is True
    assert avail["wheat_params_unchanged"] is True
    assert any("wheat_food_balance_fao.csv" in p for p in avail["faostat_fb_files"])


def test_author_fb_note_leaves_a1():
    text = (OUT_DEFAULT / "author_fb.md").read_text()
    assert "Leave A1" in text
    assert "USDA remains" in text
    assert "not bit-identical" in text.lower() or "not Kuhla" in text
    assert "L1–L8" in text
    assert "5074" in text
    assert "Do not invent an Egypt node" in text
    assert "fig4_experiment_params" in text
    assert "Next paste: **S4**" in text
    assert "not adopted" in text.lower()
    prov = (FOOD_BALANCES / "PROVENANCE.txt").read_text()
    assert "5074" in prov
    assert "prepare_wheat" in prov or "USDA" in prov
    assert "14022004" in prov
    assert "not bit-identical" in prov.lower() or "Not Kuhla" in prov


def test_fetch_script_still_has_no_zenodo_and_no_param_fit():
    text = (ROOT / "scripts" / "fetch_external_data.py").read_text()
    assert "zenodo" not in text.lower()
    assert "14022004" not in text
    assert "10688435" not in text
    assert "alpha_i" not in text
    assert "--faostat-qcl-tcl" in text
    assert "wheat_params" in text
    assert "prepare_wheat" in text


def test_author_fb_module_does_not_import_g1g2():
    tree = ast.parse(Path("sheaf/agrimate/author_fb.py").read_text())
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
