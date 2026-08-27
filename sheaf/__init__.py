"""SHEAF -- Substitution, Heterogeneous agents, Equilibrium, And Fragility.

Crisis heartbeat: 24-step Gate 0 spine (``dynamic_crop``), optional
substitution (``dynamic_coupled``), Headey-clock actions
(``dynamic_policy``). ``core`` is the leftover annual SPE prototype.
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
