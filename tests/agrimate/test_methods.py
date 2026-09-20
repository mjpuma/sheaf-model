"""P12: G0-P methods note. Not a retune, not G1/G2, not an acceptance."""
from __future__ import annotations

import ast
from pathlib import Path

from sheaf.agrimate.methods import publication_bar
from sheaf.agrimate.params import wheat_params
from sheaf.agrimate.validation import OUT_DEFAULT


def test_author_params_not_retuned_for_methods():
    p = wheat_params()
    assert p.alpha_i == 3.2
    assert p.p_sto_annual == 0.1
    assert p.xmin_share == 0.2
    assert p.zeta_penalty == 0.0
    assert p.plan_maxiter == 40


def test_g0_p_is_not_accepted():
    bar = publication_bar()
    assert bar["accepted"] is False
    assert bar["item3_undisturbed"] is False
    assert bar["item5_historical"] is False
    assert bar["item4_reproduction"] == "independent_not_replication"
    assert bar["alpha_i"] == 3.2
    assert bar["n_regions"] == 27
    assert bar["failed_harvest_amis"] == 0
    assert bar["unconverged_harvest_amis"] == 2304
    assert bar["hike_2008_host"] > 3.0
    assert 1.5 < bar["hike_2008_author"] < 1.9


def test_methods_note_is_the_market_section_offer():
    text = (OUT_DEFAULT / "methods.md").read_text()
    assert "not accepted" in text.lower() or "Not accepted" in text
    assert "Recommend reject" in text
    assert "independent" in text.lower()
    assert "not" in text.lower() and "replication" in text.lower()
    assert "No substitution" in text or "does **not** implement" in text
    assert "government" in text.lower()
    assert "L1–L8" in text
    assert "α_foreign=10" in text or "Bai" in text
    assert "Do not pin" in text or "not pinned" in text
    assert "αI=3.2" in text or "αI | 3.2" in text
    assert "USDA" in text and "FAOSTAT" in text
    assert "undisturbed" in text.lower()
    assert "harvest_amis" in text or "harvest+AMIS" in text
    assert "1743/5832" in text
    assert "1.63" in text
    assert "1.004" in text
    assert "G1" in text and "blocked" in text.lower()
    assert "dynamic_policy" in text  # named as not implemented
    assert "A1" in text and "A8" in text
    assert "P11" in text or "restriction_pulse" in text


def test_methods_module_does_not_import_g1_g2():
    tree = ast.parse(Path("sheaf/agrimate/methods.py").read_text())
    banned = ("dynamic_policy", "dynamic_coupled", "dynamic_crop")
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(not any(b in a.name for b in banned) for a in node.names)
        if isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            assert not any(b in mod for b in banned)
            assert all(not any(b in a.name for b in banned) for a in node.names)
