#!/usr/bin/env python3
"""Shared scoring harness for the red-team census experiments.

Read-only with respect to `sheaf/`: every variant is a keyword override
through `run_crop_dynamics`, or a post-hoc edit of a `CropPrep` field that
`prepare_crop_run` has already finished building.

`_corr` and `_hike` are imported from `scripts/score_subannual_crop.py`
rather than reimplemented, so the numbers here are the official metric.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from sheaf.data_usda import load_price_series_monthly  # noqa: E402
from sheaf.dynamic_crop import (  # noqa: E402
    prepare_crop_run,
    result_to_monthly,
    run_crop_dynamics,
    simulate_prep,
)
from score_subannual_crop import _corr, _hike  # noqa: E402

CROPS = ("wheat", "maize", "rice")

# (label, base_year, base_month, peak_year, peak_month)
WINDOWS = (
    ("h0708", 2006, 6, 2008, 3),
    ("h1011", 2009, 6, 2011, 2),
)

# Observed targets, from diagnostics/gate0_*_report.md.
OBSERVED = {
    "wheat": {"h0708": 1.82, "h1011": 1.16},
    "maize": {"h0708": 1.84, "h1011": 1.44},
    "rice": {"h0708": 1.84, "h1011": 0.79},
}

# Official snapshot scores (diagnostics/gate0_*_report.md, A5_REPORT.md).
OFFICIAL = {
    "wheat": (0.720, 2.27, 1.45),
    "maize": (0.712, 1.97, 1.70),
    "rice": (0.678, 1.72, 0.82),
}

_OBS_CACHE: dict[str, object] = {}


def observed(crop: str):
    if "m" not in _OBS_CACHE:
        _OBS_CACHE["m"] = load_price_series_monthly(deflated=True)
    m = _OBS_CACHE["m"]
    sub = m[(m.year >= 2006) & (m.year <= 2011)][["year", "month", crop]]
    return sub.rename(columns={crop: "obs_price"})


def score_monthly(crop: str, monthly) -> dict[str, float]:
    """corr against the deflated Pink Sheet, plus the two hike ratios."""
    obs = observed(crop)
    merged = monthly.merge(obs, on=["year", "month"], how="left")
    out = {"corr": _corr(merged.model_price, merged.obs_price)}
    for label, y0, m0, y1, m1 in WINDOWS:
        out[label] = _hike(merged, "model_price", y0, m0, y1, m1)
    return out


def score_full_leg(crop: str, **overrides) -> dict[str, float]:
    """Official P1 matched leg: harvest + AMIS + mean flex (+ maize RFS)."""
    res = run_crop_dynamics(
        crop, start_year=2006, end_year=2011,
        use_amis=True, use_shocks=True, use_demand=False, **overrides)
    return score_monthly(crop, result_to_monthly(res))


def score_prep(crop: str, mutate=None, **overrides) -> dict[str, float]:
    """Same leg, but with a hook that may edit the built `CropPrep`.

    `mutate(prep)` runs after `prepare_crop_run` has produced the twin, so
    edits to `prep.H_seas` change only the treatment path's expectation
    (`H_seasonal` in `_simulate_window`), not the calm twin.
    """
    prep = prepare_crop_run(
        crop, start_year=2006, end_year=2011,
        use_amis=True, use_shocks=True, use_demand=False, **overrides)
    if mutate is not None:
        mutate(prep)
    return score_monthly(crop, result_to_monthly(simulate_prep(prep)))


def metric_vector(scores: dict[str, dict[str, float]]) -> np.ndarray:
    """Flatten {crop: {metric: value}} into a fixed-order 9-vector."""
    return np.array([scores[c][k] for c in CROPS
                     for k in ("corr", "h0708", "h1011")], float)


METRIC_NAMES = tuple(f"{c}.{k}" for c in CROPS
                     for k in ("corr", "h0708", "h1011"))


def baseline_scores() -> dict[str, dict[str, float]]:
    return {c: score_full_leg(c) for c in CROPS}


def check_baseline(verbose: bool = True) -> bool:
    """Assert the harness reproduces the published per-crop reports."""
    ok = True
    base = baseline_scores()
    for crop in CROPS:
        got = (base[crop]["corr"], base[crop]["h0708"], base[crop]["h1011"])
        want = OFFICIAL[crop]
        hit = all(abs(g - w) < 5e-3 for g, w in zip(got, want))
        ok &= hit
        if verbose:
            print(f"  {crop:6s} corr {got[0]:+.3f} (want {want[0]:+.3f})  "
                  f"07/08 x{got[1]:.2f} (want x{want[1]:.2f})  "
                  f"10/11 x{got[2]:.2f} (want x{want[2]:.2f})  "
                  f"{'OK' if hit else 'MISMATCH'}")
    return bool(ok)


if __name__ == "__main__":
    print("Baseline reproduction check (official P1 matched leg):")
    print("PASS" if check_baseline() else "FAIL")
