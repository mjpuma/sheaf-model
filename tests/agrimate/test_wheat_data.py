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


def test_amis_wheat_delta_nonempty_in_2008():
    """OECD columns are PolicyMeasure_Name / CommodityClass_Name, not Measure."""
    from sheaf.agrimate.restrictions import restriction_matrix
    d = restriction_matrix(list(REGION_NAMES), 2007, 2008, crop="wheat")
    assert d.max() >= 0.5
    assert d.sum() > 0
    # named 2007/08 exporters in the OECD wheat slice
    for name in ("Argentina", "Ukraine", "Russia", "India"):
        i = REGION_NAMES.index(name)
        assert d[i].max() > 0, name
