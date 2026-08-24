"""Wheat Gate 0 entry point — thin wrap around ``sheaf.dynamic_crop``.

Prefer ``run_crop_dynamics(crop="wheat")`` / ``scripts/score_subannual_crop.py``
for new work. This module keeps the previous wheat-named API for existing
scripts and README §8 cross-references.
"""
from __future__ import annotations

from .dynamic_crop import (
    CropSimResult as WheatSimResult,
    assert_amis_cuts_exports as _assert_cuts,
    assert_amis_raises_price as _assert_lift,
    assert_no_spring_spike as _assert_spring,
    assert_twin_identity as _assert_twin,
    result_to_monthly,
    run_crop_dynamics,
)

__all__ = [
    "WheatSimResult",
    "run_wheat_dynamics",
    "result_to_monthly",
    "assert_twin_identity",
    "assert_amis_raises_price",
    "assert_no_spring_spike",
    "assert_amis_cuts_exports",
]


def run_wheat_dynamics(**kwargs) -> WheatSimResult:
    return run_crop_dynamics(crop="wheat", **kwargs)


def assert_twin_identity(**kwargs) -> None:
    _assert_twin("wheat", **kwargs)


def assert_amis_raises_price(**kwargs) -> None:
    _assert_lift("wheat", **kwargs)


def assert_no_spring_spike(**kwargs) -> None:
    _assert_spring("wheat", **kwargs)


def assert_amis_cuts_exports(**kwargs) -> None:
    # Wheat Russia ban: keep the stricter legacy offer ratio.
    kwargs.setdefault("max_offer_ratio", 0.20)
    kwargs.setdefault("max_ship_ratio", 0.85)
    _assert_cuts("wheat", **kwargs)
