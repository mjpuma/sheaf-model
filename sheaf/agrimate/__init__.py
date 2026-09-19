"""Agrimate-faithful Gate 0 host (Kuhla, Kubiczek & Otto 2025).

Independent implementation of the published specification (Ecological
Economics 231:108546, ODD supplement §D; wheat application §E). Author
code https://doi.org/10.5281/zenodo.14022004 was retrieved 2026-09-16
and used as the executable specification; it is not copied into this
package.

Legacy SHEAF Gate 0 remains in ``sheaf.legacy`` and must not be imported
from this package.
"""
from .params import AgrimateParams, fig4_experiment_params, wheat_params
from .model import AgrimateResult, AgrimateSim, run_agrimate
from .wheat_data import prepare_wheat
from .validation import SCENARIOS, run_three_scenarios
from .accounting import check_result

__all__ = [
    "AgrimateParams",
    "AgrimateResult",
    "AgrimateSim",
    "SCENARIOS",
    "check_result",
    "fig4_experiment_params",
    "prepare_wheat",
    "run_agrimate",
    "run_three_scenarios",
    "wheat_params",
]
