"""Wheat data adaptations that must stay labelled."""
from sheaf.agrimate.wheat_data import prepare_wheat


def test_egypt_f1_pins_and_per_step_starred_units():
    d = prepare_wheat(start_year=2006, end_year=2006)
    i = d.regions.index("Egypt")
    assert abs(d.A_c[i] - 0.34) < 1e-12
    assert abs(d.A_d[i] - 0.17) < 1e-12
    assert d.XI_world < 20.0
    assert d.C_star.sum() < 80.0
    assert d.H_annual.sum() > 400.0
    assert d.delta.shape[1] == 24
    assert len(d.regions) == 28
