"""R1: live host is not silently tuned; data path is documented."""
from __future__ import annotations

import ast
from pathlib import Path

import pandas as pd

from sheaf.agrimate.fig4 import AUTHOR_DIR, author_undisturbed_drift
from sheaf.agrimate.methods import publication_bar
from sheaf.agrimate.params import wheat_params
from sheaf.agrimate.validation import OUT_DEFAULT

ROOT = Path(__file__).resolve().parents[2]
AGRIMATE = ROOT / "sheaf" / "agrimate"
BANNED = (
    "sheaf.legacy",
    "sheaf.dynamic_crop",
    "sheaf.dynamic_coupled",
    "sheaf.dynamic_policy",
    "sheaf.dynamic_wheat",
    "sheaf.dynamic_grains",
)


def test_g0_p_still_not_accepted_after_redteam():
    bar = publication_bar()
    assert bar["accepted"] is False
    assert bar["item3_undisturbed"] is False
    assert bar["item5_historical"] is False


def test_author_params_not_fig4_knobs():
    p = wheat_params()
    assert p.alpha_i == 3.2
    assert p.zeta_penalty == 0.0
    assert p.n_for_months == 3
    assert p.p_sto_annual == 0.1
    assert p.xmin_share == 0.2


def test_agrimate_package_does_not_import_legacy_or_g1g2():
    for path in sorted(AGRIMATE.glob("*.py")):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            for name in names:
                assert all(b not in name for b in BANNED), f"{path.name} imports {name}"


def test_fetch_script_does_not_download_zenodo_or_fit_params():
    text = (ROOT / "scripts" / "fetch_external_data.py").read_text()
    assert "zenodo" not in text.lower()
    assert "14022004" not in text
    assert "10688435" not in text
    assert "alpha_i" not in text
    assert "p_sto" not in text
    assert "xmin" not in text
    assert "--faostat-fb" in text
    assert "wheat_params" in text
    assert "prepare_wheat" in text


def test_provenance_and_cookbook_exist():
    for rel in (
        "data/usda_psd/PROVENANCE.txt",
        "data/usda_world/PROVENANCE.txt",
        "data/faostat_network/PROVENANCE.txt",
        "data/faostat_fb/PROVENANCE.txt",
        "data/amis_policies/PROVENANCE.txt",
        "data/world_prices/PROVENANCE.txt",
        "data/crop_calendars/PROVENANCE.txt",
        "diagnostics/gate0_agrimate/author_fig4/PROVENANCE.txt",
        "diagnostics/GATE0_DATA.md",
        "diagnostics/GATE0_REDTEAM.md",
        "diagnostics/GATE0_REPRO_PROMPTS.md",
        "diagnostics/GATE0_REPRO_DISPATCH.md",
        "diagnostics/GATE0_NEXT_PROMPTS.md",
        "diagnostics/gate0_agrimate/world_price.md",
        "archive/README.md",
    ):
        assert (ROOT / rel).is_file(), rel


def test_author_fig4_csvs_are_vendored():
    for name in ("monthly_world.csv", "annual_world.csv", "annual_regional.csv"):
        assert (AUTHOR_DIR / name).is_file()
    monthly = pd.read_csv(AUTHOR_DIR / "monthly_world.csv")
    d = author_undisturbed_drift(monthly, 2006, 2011)
    assert d["last_over_first"] < 1.05
    assert set(monthly["scenario"]) >= {"undisturbed"}


def test_calendar_provenance_labels_live_e27():
    text = (ROOT / "data" / "crop_calendars" / "PROVENANCE.txt").read_text()
    assert "E.27" in text
    assert "sheaf.agrimate.harvest" in text
    assert "legacy" in text.lower()
    text = (ROOT / "archive" / "README.md").read_text()
    assert "not on the live Gate 0 path" in text
    assert "sheaf/agrimate/" in text


def test_redteam_note_does_not_claim_replication():
    text = (ROOT / "diagnostics" / "GATE0_REDTEAM.md").read_text()
    assert "**not** reproduce Agrimate Fig. 4" in text
    assert "Do not start G1" in text
    assert "L1–L8" in text
    assert "α_foreign=10" in text or "Bai" in text
    assert "adaptive" in (ROOT / "diagnostics" / "GATE0_REPRO_PROMPTS.md").read_text().lower()
    dispatch = (ROOT / "diagnostics" / "GATE0_REPRO_DISPATCH.md").read_text()
    assert "Last completed:" in dispatch
    assert "Next paste:" in dispatch
    assert "R11" in dispatch
    data = (ROOT / "diagnostics" / "GATE0_DATA.md").read_text()
    assert "--psd-only" in data
    assert "--faostat-fb" in data
    assert "Food Balances" in data
    assert OUT_DEFAULT.exists()
