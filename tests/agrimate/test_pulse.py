"""P11: prescribed exporter pulse. Not G2, not Bai's 36-run grid."""
from __future__ import annotations

import pandas as pd

from sheaf.agrimate.params import wheat_params
from sheaf.agrimate.pulse import (
    DURATIONS,
    EXPORTERS,
    INTENSITIES,
    grid_is_clean,
    pulse_specs,
)
from sheaf.agrimate.restrictions import restriction_pulse
from sheaf.agrimate.validation import OUT_DEFAULT
from sheaf.agrimate.regions import REGION_NAMES


def test_author_params_not_retuned_for_pulse():
    p = wheat_params()
    assert p.alpha_i == 3.2
    assert p.p_sto_annual == 0.1
    assert p.xmin_share == 0.2


def test_pulse_grid_is_eight_not_thirty_six():
    specs = pulse_specs()
    assert len(specs) == 8
    assert EXPORTERS == ("Ukraine", "Russia")
    assert INTENSITIES == (0.5, 1.0)
    assert DURATIONS == (6, 12)
    labels = {s["label"] for s in specs}
    assert "Ukraine_1_12m" in labels
    assert "Russia_0.5_6m" in labels


def test_pulse_is_prescribed_delta_not_a_game():
    d = restriction_pulse(list(REGION_NAMES), 2008, 2008, "Ukraine",
                          intensity=0.5, duration_months=6, start="2008-01-01")
    i = REGION_NAMES.index("Ukraine")
    j = REGION_NAMES.index("Russia")
    assert d.shape == (27, 24)
    assert d[i, :12].min() == 0.5
    assert d[i, 12:].max() == 0.0
    assert d[j].max() == 0.0
    # no import of the government-game module
    import sys
    assert "sheaf.dynamic_policy" not in sys.modules


def test_pulse_note_is_not_gate2():
    text = (OUT_DEFAULT / "pulse.md").read_text()
    assert "not Gate 2" in text or "Not Gate 2" in text
    assert "36" in text
    assert "L1–L8" in text
    assert "αI=3.2" in text or "α_foreign=10" in text


def test_pulse_csv_cuts_full_year_exports():
    tab = pd.read_csv(OUT_DEFAULT / "score_pulse.csv")
    assert len(tab) == 9
    assert "harvest_only" in set(tab["label"])
    ukr = tab[(tab["label"] == "Ukraine_1_12m")].iloc[0]
    assert ukr["failed"] == 0
    assert ukr["exports_vs_harvest"] < 1.0
    assert abs(ukr["production_vs_harvest"] - 1.0) < 1e-6
    tax = tab[(tab["label"] == "Ukraine_0.5_12m")].iloc[0]
    assert 0.45 < tax["exports_vs_harvest"] < 0.55
    assert grid_is_clean(tab)


def test_pulse_module_does_not_import_dynamic_policy():
    import ast
    from pathlib import Path
    tree = ast.parse(Path("sheaf/agrimate/pulse.py").read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all("dynamic_policy" not in a.name for a in node.names)
        if isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            assert "dynamic_policy" not in mod
            assert all("dynamic_policy" not in a.name for a in node.names)
