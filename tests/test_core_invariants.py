"""Minimal invariant tests for adjudicated SHEAF core behaviour."""
from __future__ import annotations

import numpy as np
import pytest

from sheaf.calibration import build_countries, DATA
from sheaf.core import (
    build_demand_system, SpatialEquilibrium, SpatialEquilibriumError,
    strategic_storage, SheafModel,
)
from sheaf.data_faostat import SHEAF_NODE_MAP
from sheaf.data_usda import crisis_forcing, shock_matrix_from_world_forcing


def test_kazakhstan_is_named_node():
    names = {d["name"] for d in DATA}
    assert "Kazakhstan" in names
    assert "Kazakhstan" in SHEAF_NODE_MAP
    assert SHEAF_NODE_MAP["Kazakhstan"] == ["KAZ"]
    countries, *_ = build_countries()
    assert any(c.name == "Kazakhstan" for c in countries)
    assert any(c.name == "RestOfWorld" for c in countries)


def test_demand_pd_at_former_cliff():
    grains = ("wheat", "rice", "maize")
    D0 = np.array([1000.0, 519.0, 666.7])
    p0 = np.array([250.0, 400.0, 200.0])
    own = np.array([-0.25, -0.20, -0.30])
    rho = np.full((3, 3), 0.999)
    np.fill_diagonal(rho, 0.0)
    ds = build_demand_system(grains, D0, p0, own, rho, subst_scale=0.63)
    assert np.linalg.eigvalsh(ds.M).min() > 0


def test_solver_raises_on_global_infeasibility():
    grains = ("wheat", "rice", "maize")
    rho0 = np.zeros((3, 3))
    ds = build_demand_system(grains, [50, 20, 30], [250, 400, 200],
                             [-0.25, -0.2, -0.3], rho0, 0.0)
    se = SpatialEquilibrium(np.array([[0.0, 10.0], [10.0, 0.0]]), grains)
    with pytest.raises(SpatialEquilibriumError):
        se.solve([ds, ds], np.array([[-10.0, 5.0, 5.0], [-10.0, 5.0, 5.0]]),
                 np.zeros((2, 3)), np.zeros((2, 3)))


def test_g2_importer_calm_rebuild():
    countries, *_ = build_countries()
    china = next(c for c in countries if c.name == "China")
    china.gov_stock = china.gov_stock.copy()
    china.gov_stock[0] = 40.0  # below target
    dg = strategic_storage(
        china, 0, 200.0, china.demand.D0[0], china.production[0],
        production0=china.production[0])
    assert dg > 0


def test_material_balance_one_period():
    countries, transport, grains, fm = build_countries()
    model = SheafModel(countries, transport, grains, freight_mult=fm,
                       play_game=False, game_grid=5)
    model.step(0)
    df = model.results_frame()
    for grain in grains:
        sub = df[df.grain == grain]
        # availability - consumption ≈ net_export; world nets ≈ 0
        assert abs(sub["net_export"].sum()) < 1e-6


def test_world_forcing_broadcast():
    forcing = crisis_forcing(years=[2007])
    m = shock_matrix_from_world_forcing(5, ("wheat", "rice", "maize"), forcing.loc[2007])
    assert m.shape == (5, 3)
    assert np.allclose(m[:, 0], m[0, 0])


def test_policy_archetype_pool():
    c_hand, *_ = build_countries(policy_pool=None)
    c_arch, *_ = build_countries(policy_pool="archetype")
    # fewer unique fs_weight rows under pooling
    hand = {tuple(np.round(c.fs_weight, 6)) for c in c_hand if c.name != "RestOfWorld"}
    arch = {tuple(np.round(c.fs_weight, 6)) for c in c_arch if c.name != "RestOfWorld"}
    assert len(arch) <= len(hand)
    assert len(arch) <= 4
