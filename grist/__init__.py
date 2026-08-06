"""GRIST -- Grain Restriction, Interdependence & Strategic Trade.

A multi-commodity, game-theoretic network model of global grain trade.
"""
from .core import (
    DemandSystem, build_demand_system, Country,
    SpatialEquilibrium, ExportRestrictionGame, GristModel,
    market_responsive_storage, strategic_storage, MarketResult,
)
from .calibration import build_countries, GRAINS

__all__ = [
    "DemandSystem", "build_demand_system", "Country",
    "SpatialEquilibrium", "ExportRestrictionGame", "GristModel",
    "market_responsive_storage", "strategic_storage", "MarketResult",
    "build_countries", "GRAINS",
]
__version__ = "0.1.0"
