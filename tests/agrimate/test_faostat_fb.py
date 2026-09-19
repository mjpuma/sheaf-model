"""P10: FAOSTAT Food Balances are not in the repo. Leave A1. USDA stays default."""
from __future__ import annotations

from pathlib import Path

from sheaf.agrimate.faostat_fb import FAOSTAT_NETWORK, inventory
from sheaf.agrimate.params import wheat_params
from sheaf.agrimate.validation import OUT_DEFAULT
from sheaf.agrimate.wheat_data import prepare_wheat


def test_usda_remains_prepare_wheat_default():
    p = wheat_params()
    assert p.alpha_i == 3.2
    assert p.p_sto_annual == 0.1
    assert p.xmin_share == 0.2
    d = prepare_wheat(start_year=2006, end_year=2006)
    assert any("USDA PSD" in n and "not FAOSTAT Food Balances" in n for n in d.notes)


def test_faostat_network_is_e0_not_food_balances():
    names = [p.name for p in FAOSTAT_NETWORK.iterdir() if p.is_file()]
    assert any(n.endswith("E0.csv") and n.startswith("Wheat") for n in names)
    assert "PROVENANCE.txt" in names
    assert not any("food_balance" in n.lower() for n in names)


def test_inventory_finds_no_food_balance_arrays():
    inv = inventory()
    assert inv["e0_files"]
    assert inv["food_balance_files"] == []
    assert inv["author_fb_present"] == []
    assert inv["usda_is_default"] is True
    assert inv["alpha_i"] == 3.2
    assert inv["p0_r0_files"] == []


def test_wheat_2006_e0_is_square_trade_not_a_food_balance():
    import pandas as pd
    path = FAOSTAT_NETWORK / "Wheat_Avg_2006_2007E0.csv"
    df = pd.read_csv(path, index_col=0)
    assert df.shape[0] > 50 and df.shape[1] > 50
    cols = [str(c).lower() for c in df.columns]
    assert "production" not in cols
    assert "consumption" not in cols
    assert "ending_stocks" not in cols
    # FAO area codes or ISO3, not FB element names
    sample = cols[0]
    assert sample in {"arm", "1"} or sample.isupper() or sample.isdigit()


def test_p10_note_leaves_a1():
    text = (OUT_DEFAULT / "faostat_fb.md").read_text()
    assert "Leave A1" in text
    assert "USDA remains" in text
    assert "No parallel" in text
    assert "L1–L8" in text
    assert "α_foreign=10" in text or "Bai" in text
    assert "10688435" in text
    assert "faostat_network" in text
    assert "FoodTradeNetwork" in text or "P0" in text


def test_no_faostat_fb_data_dir_was_added():
    root = Path(__file__).resolve().parents[2]
    assert not (root / "data" / "faostat_fb").exists()
    assert not (root / "data" / "food_balances").exists()
