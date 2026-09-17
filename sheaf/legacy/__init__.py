"""Legacy Gate 0 host, frozen at the Agrimate rewrite snapshot.

This package is the labelled pre-rewrite benchmark. It is not the default
Gate 0 path. Run it with ``python scripts/score_legacy_crop.py --crop wheat``.
"""
from .dynamic_crop import (
    CropParams,
    CropSimResult,
    default_crop_params,
    prepare_crop_run,
    result_to_monthly,
    run_crop_dynamics,
    simulate_prep,
)

__all__ = [
    "CropParams",
    "CropSimResult",
    "default_crop_params",
    "prepare_crop_run",
    "result_to_monthly",
    "run_crop_dynamics",
    "simulate_prep",
]
