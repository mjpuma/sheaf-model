"""SHEAF -- Substitution, Heterogeneous agents, Equilibrium, And Fragility.

A multi-commodity, game-theoretic network model of global grain trade.
"""
from .core import (
    DemandSystem, build_demand_system, Country,
    SpatialEquilibrium, SpatialEquilibriumError, ExportRestrictionGame, SheafModel,
    market_responsive_storage, strategic_storage, MarketResult,
)
from .calibration import build_countries, GRAINS
from .calendar24 import STEPS_PER_YEAR

__all__ = [
    "DemandSystem", "build_demand_system", "Country",
    "SpatialEquilibrium", "SpatialEquilibriumError",
    "ExportRestrictionGame", "SheafModel",
    "market_responsive_storage", "strategic_storage", "MarketResult",
    "build_countries", "GRAINS", "STEPS_PER_YEAR",
]
__version__ = "0.2.0-subannual"
