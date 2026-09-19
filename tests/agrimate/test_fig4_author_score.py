"""R10: Fig. 4 knobs scored vs author_fig4. wheat_params() stay 14022004."""
from __future__ import annotations

import ast
from pathlib import Path

import pandas as pd

from sheaf.agrimate.fig4_author_score import (
    knobs_are_not_a_fig4_match,
    score_r2_against_author,
)
from sheaf.agrimate.fig4_config import CANNOT_SET, PROTECTED_THREE_SCENARIO
from sheaf.agrimate.params import wheat_params
from sheaf.agrimate.validation import OUT_DEFAULT

ROOT = Path(__file__).resolve().parents[2]


def test_wheat_params_not_adopted_after_r10():
    p = wheat_params()
    assert p.alpha_i == 3.2
    assert p.zeta_penalty == 0.0
    assert p.n_for_months == 3
    assert p.p_sto_annual == 0.1
    assert p.xmin_share == 0.2


def test_r10_scores_knobs_not_defaults_against_author():
    csv = OUT_DEFAULT / "score_fig4_config_author.csv"
    note = OUT_DEFAULT / "fig4_config_score.md"
    assert csv.is_file()
    assert note.is_file()
    tab = pd.read_csv(csv)
    c = tab[(tab["label"] == "fig4_knobs") & (tab["scenario"] == "harvest_amis")].iloc[0]
    d = tab[(tab["label"] == "default") & (tab["scenario"] == "harvest_amis")].iloc[0]
    u = tab[(tab["label"] == "fig4_knobs") & (tab["scenario"] == "undisturbed")].iloc[0]
    assert c["alpha_i"] == 3.5
    assert d["alpha_i"] == 3.2
    assert not bool(c["adopted"])
    assert c["hike_2008"] > c["hike_2008_author"]
    assert c["moy_maxmin"] > 3.0 * c["moy_maxmin_author"]
    # Quiet year: knobs moved away from author, not a 2006 pin.
    assert abs(c["mean_2006_index"] - 1.0) > 0.2
    assert abs(c["mean_2006_index"] - c["mean_2006_author_index"]) + 1e-9 >= abs(
        d["mean_2006_index"] - d["mean_2006_author_index"]
    )
    assert u["last_first_author"] < 1.05
    v = knobs_are_not_a_fig4_match(tab)
    assert v["match"] is False
    assert v["adopted"] is False


def test_r10_note_lists_remaining_a7_and_does_not_adopt():
    text = (OUT_DEFAULT / "fig4_config_score.md").read_text()
    assert "Remaining A7" in text
    assert "FAOSTAT Food Balances" in text
    assert "Egypt" in text
    assert "old-demand-dynamics" in text
    assert "not a retune" in text.lower()
    assert "wheat_params" in text
    assert "adopted=False" in text
    assert "Pink" in text
    assert "L1–L8" in text
    assert "Next paste: R9" in text
    assert "spin-up" in text
    joined = " ".join(CANNOT_SET)
    assert "FAOSTAT Food Balances" in joined


def test_r10_module_does_not_import_g1g2():
    tree = ast.parse(Path("sheaf/agrimate/fig4_author_score.py").read_text())
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


def test_r10_did_not_overwrite_three_scenario_or_adopt():
    for name in PROTECTED_THREE_SCENARIO:
        assert (OUT_DEFAULT / name).is_file(), name
    assert wheat_params().alpha_i == 3.2
    dispatch = (ROOT / "diagnostics" / "GATE0_REPRO_DISPATCH.md").read_text()
    assert "Last completed: R10" in dispatch
    assert "Next paste: R9" in dispatch


def test_score_r2_against_author_is_pure_csv():
    """R10 reads the R2 CSV; it does not need a new host run."""
    scored = score_r2_against_author()
    assert set(scored["label"]) == {"default", "fig4_knobs"}
    assert "mean_2006_index" in scored.columns
    assert "mean_2006_author_index" in scored.columns
    assert scored["adopted"].eq(False).all()
