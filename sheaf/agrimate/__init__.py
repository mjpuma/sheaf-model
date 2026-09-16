"""Agrimate-faithful Gate 0 host (Kuhla, Kubiczek & Otto 2025).

Independent implementation of the published specification (Ecological
Economics 231:108546, ODD supplement §D; wheat application §E). Author
code https://doi.org/10.5281/zenodo.14022004 was not retrieved here.

Legacy SHEAF Gate 0 remains in ``sheaf.legacy`` and must not be imported
from this package.
"""
from .params import AgrimateParams, wheat_params
from .model import AgrimateResult, AgrimateSim, run_agrimate
from .wheat_data import prepare_wheat

__all__ = [
    "AgrimateParams",
    "AgrimateResult",
    "AgrimateSim",
    "prepare_wheat",
    "run_agrimate",
    "wheat_params",
]
