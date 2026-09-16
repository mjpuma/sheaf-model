"""Wheat data adaptations that must stay labelled."""
from sheaf.agrimate.wheat_data import prepare_wheat
from sheaf.agrimate.regions import REGION_NAMES


def test_c1_wheat_nodes_match_author_list():
    d = prepare_wheat(start_year=2006, end_year=2006)
    assert len(d.regions) == 27
    assert d.regions == REGION_NAMES
    assert "Pakistan" in d.regions
    assert "Turkey" in d.regions
    assert "EU-27" in d.regions
    assert "Egypt" not in d.regions
    assert "Mexico" not in d.regions
    assert d.XI_world < 20.0
    assert d.C_star.sum() < 80.0
    assert d.H_annual.sum() > 400.0
    assert d.delta.shape[1] == 24
