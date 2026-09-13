"""SHEAF -- Substitution, Heterogeneous agents, Equilibrium, And Fragility.

Crisis heartbeat: 24-step Gate 0 spine (``dynamic_crop``), optional
substitution (``dynamic_coupled``), Headey-clock actions
(``dynamic_policy``).

The annual SPE prototype is parked in ``sheaf.annual`` (not exported here).
Import it explicitly when you want a year-scale outer loop or the old QP.
"""
from .calendar24 import STEPS_PER_YEAR
from .calibration import GRAINS
from .dynamic_crop import CropParams, default_crop_params, run_crop_dynamics

__all__ = [
    "CropParams",
    "GRAINS",
    "STEPS_PER_YEAR",
    "default_crop_params",
    "run_crop_dynamics",
]
__version__ = "0.3.0-subannual"
