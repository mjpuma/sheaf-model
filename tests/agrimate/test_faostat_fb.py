"""R6 obtain: raw FAOSTAT FBSH is vendored; author cleaned FB absent; USDA default."""
from __future__ import annotations

from pathlib import Path

from sheaf.agrimate.faostat_fb import FAOSTAT_FB, FAOSTAT_NETWORK, inventory
from sheaf.agrimate.params import wheat_params
from sheaf.agrimate.validation import OUT_DEFAULT
from sheaf.agrimate.wheat_data import prepare_wheat

ROOT = Path(__file__).resolve().parents[2]


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


def test_inventory_separates_raw_fbsh_from_author_cleaned():
    inv = inventory()
    assert inv["e0_files"]
    assert inv["food_balance_files"] == []
    assert inv["author_fb_present"] == []
    assert inv["fbsh_wheat_files"]
    assert "wheat_fbsh_2006_2011.csv" in inv["fbsh_wheat_files"]
    assert inv["usda_is_default"] is True
    assert inv["alpha_i"] == 3.2
    assert inv["p0_r0_files"] == []
    assert inv["laptop_data"]["exists"] is False


def test_wheat_2006_e0_is_square_trade_not_a_food_balance():
    import pandas as pd
    path = FAOSTAT_NETWORK / "Wheat_Avg_2006_2007E0.csv"
    df = pd.read_csv(path, index_col=0)
    assert df.shape[0] > 50 and df.shape[1] > 50
    cols = [str(c).lower() for c in df.columns]
    assert "production" not in cols
    assert "consumption" not in cols
    assert "ending_stocks" not in cols
    sample = cols[0]
    assert sample in {"arm", "1"} or sample.isupper() or sample.isdigit()


def test_fbsh_wheat_extract_is_2006_2011_thousand_tonnes():
    import pandas as pd
    path = FAOSTAT_FB / "wheat_fbsh_2006_2011.csv"
    assert path.is_file()
    df = pd.read_csv(path)
    assert set(df["year"].unique()) == {2006, 2007, 2008, 2009, 2010, 2011}
    assert set(df["unit"].unique()) == {"1000 t"}
    usa = df[(df["area"] == "United States of America") & (df["year"] == 2007)]
    assert abs(float(usa["production"].iloc[0]) - 55820.0) < 1.0
    world = df[(df["area"] == "World") & (df["year"] == 2007)]
    assert abs(float(world["production"].iloc[0]) - 608672.0) < 1.0
    assert "stock_variation" in df.columns
    assert usa["stock_variation"].notna().iloc[0]


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
    assert "FBSH" in text
    assert "--faostat-fb" in text
    assert "wheat_food_balance_fao.csv" in text


def test_bulk_zip_is_gitignored():
    gi = (ROOT / ".gitignore").read_text()
    assert "data/faostat_fb/*.zip" in gi
    assert "data/faostat_fb/*_All_Data*" in gi


def test_dispatch_obtain_then_parallel_wheatdata():
    text = (ROOT / "diagnostics" / "GATE0_REPRO_DISPATCH.md").read_text()
    assert "Last completed: R6 obtain" in text
    assert "Next paste: R6" in text
    assert "do not switch prepare_wheat" in text.lower() or "USDA still" in text


def test_faostat_fb_dir_has_provenance_and_not_author_cleaned():
    assert FAOSTAT_FB.is_dir()
    assert (FAOSTAT_FB / "PROVENANCE.txt").is_file()
    assert (FAOSTAT_FB / "wheat_fbsh_2006_2011.csv").is_file()
    assert not (FAOSTAT_FB / "wheat_food_balance_fao.csv").exists()
    assert not (ROOT / "data" / "food_balances").exists()
    prov = (FAOSTAT_FB / "PROVENANCE.txt").read_text()
    assert "5074" in prov
    assert "prepare_wheat" in prov or "USDA" in prov
    assert "14022004" not in (ROOT / "scripts" / "fetch_external_data.py").read_text()
