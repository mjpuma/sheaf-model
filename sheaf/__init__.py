"""SHEAF -- Substitution, Heterogeneous agents, Equilibrium, And Fragility.

Crisis heartbeat: Agrimate-faithful Gate 0 (``sheaf.agrimate``). The pre-rewrite
ask/scarcity spine remains importable from ``sheaf.dynamic_crop`` /
``sheaf.legacy`` and is **not** the documented default.

The annual SPE prototype is parked in ``sheaf.annual`` (not exported here).
"""
from .agrimate import AgrimateResult, run_agrimate, wheat_params
from .calendar24 import STEPS_PER_YEAR
from .calibration import GRAINS

__all__ = [
    "AgrimateResult",
    "GRAINS",
    "STEPS_PER_YEAR",
    "run_agrimate",
    "wheat_params",
]
__version__ = "0.4.0-agrimate-gate0"
