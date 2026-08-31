"""Annual SPE prototype — parked, not the crisis host.

Import explicitly::

    from sheaf.annual import SheafModel, build_countries

Crisis market: ``sheaf.dynamic_crop`` (24 steps/year).
Equations: ``sheaf/annual/README.md``. Demo: ``scripts/annual/demo.py``.
"""
from sheaf.calibration import build_countries, GRAINS
from .core import (
    Country,
    DemandSystem,
    ExportRestrictionGame,
    MarketResult,
    SheafModel,
    SpatialEquilibrium,
    SpatialEquilibriumError,
    build_demand_system,
    market_responsive_storage,
    strategic_storage,
)

__all__ = [
    "Country",
    "DemandSystem",
    "ExportRestrictionGame",
    "GRAINS",
    "MarketResult",
    "SheafModel",
    "SpatialEquilibrium",
    "SpatialEquilibriumError",
    "build_countries",
    "build_demand_system",
    "market_responsive_storage",
    "strategic_storage",
]
