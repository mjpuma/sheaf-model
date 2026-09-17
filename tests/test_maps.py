"""Choropleth helper: SHEAF nodes on Natural Earth 110m."""
from __future__ import annotations

from pathlib import Path

from sheaf.data_faostat import SHEAF_NODE_MAP, EU_ISO3
from sheaf.maps import (
    GEOJSON,
    feature_iso3,
    node_for_iso3,
    plot_categories,
    plot_choropleth,
    safe_min_ratio,
    world_features,
)


def test_geojson_is_vendored():
    assert GEOJSON.is_file()
    assert GEOJSON.stat().st_size > 10_000


def test_france_maps_to_eu():
    # Natural Earth ISO_A3 is -99 for France; ISO_A3_EH / ADM0_A3 must win.
    feats = {iso: True for iso, _rings in world_features()}
    assert "FRA" in feats
    assert node_for_iso3("FRA") == "EU"
    assert "FRA" in EU_ISO3
    assert node_for_iso3("RUS") == "Russia"
    assert node_for_iso3("KAZ") == "Kazakhstan"
    assert node_for_iso3("UKR") == "Ukraine"
    assert node_for_iso3("ZZZ") == "RestOfWorld"


def test_every_named_node_has_geometry():
    present = {node_for_iso3(iso) for iso, _ in world_features()}
    for name in SHEAF_NODE_MAP:
        assert name in present, f"{name} has no 110m polygon"


def test_plot_choropleth_and_categories(tmp_path: Path):
    p1 = plot_categories(
        {"Russia": "harvest shock", "Kazakhstan": "player (no harvest cut)",
         "Ukraine": "on market, not playing"},
        tmp_path / "roles.png",
        title="test roles")
    p2 = plot_choropleth(
        {"Russia": 0.45, "Kazakhstan": 0.76, "Ukraine": 0.86},
        tmp_path / "ratio.png",
        title="test ratio", label="min S/S_calm",
        cmap="RdYlBu", vmin=0.4, vmax=1.05, vcenter=0.85)
    assert p1.is_file() and p1.stat().st_size > 1000
    assert p2.is_file() and p2.stat().st_size > 1000
    assert safe_min_ratio([1.0, 2.0], [1.0, 2.0]) == 1.0
    assert safe_min_ratio([0.0, 1.0], [0.0, 1.0]) is None
