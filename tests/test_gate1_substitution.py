"""Gate 1 substitution invariants. Official split; no σ* selection."""
from __future__ import annotations

import numpy as np
import pytest

from sheaf.calibration import GRAINS, RHO
from sheaf.dynamic_coupled import (
    COUPLED_GRAINS,
    assert_subst0_matches_gate0,
    cross_price_eta,
    run_coupled_dynamics,
)
from sheaf.dynamic_crop import default_crop_params


def test_eta_matches_hand_and_own_elast():
    eta = cross_price_eta(0.6)
    elast = np.array([default_crop_params(g).elast for g in COUPLED_GRAINS])
    assert COUPLED_GRAINS == GRAINS
    hand = np.diag(elast)
    idx = {g: i for i, g in enumerate(GRAINS)}
    for a, ga in enumerate(COUPLED_GRAINS):
        for b, gb in enumerate(COUPLED_GRAINS):
            if a == b:
                continue
            hand[a, b] = 0.6 * RHO[idx[ga], idx[gb]] * abs(elast[a])
    np.testing.assert_allclose(eta, hand, atol=0.0, rtol=0.0)
    # Maize answers wheat more than wheat answers maize (|ε| larger).
    assert eta[2, 0] > eta[0, 2]
    off = cross_price_eta(0.0)
    np.testing.assert_allclose(off, np.diag(elast), atol=0.0, rtol=0.0)


def test_fac_signs_wheat_hike():
    eta = cross_price_eta(0.6)
    p0 = np.array([200.0, 400.0, 180.0])
    p = np.array([300.0, 400.0, 180.0])
    fac = np.exp(eta @ np.log(p / p0))
    fac0 = np.exp(cross_price_eta(0.0) @ np.log(p / p0))
    assert fac[0] < 1.0 and fac[1] > 1.0 and fac[2] > 1.0
    np.testing.assert_allclose(fac0[0], (p[0] / p0[0]) ** eta[0, 0])
    np.testing.assert_allclose(fac0[1:], 1.0)


def test_sigma0_identity_official_split():
    assert_subst0_matches_gate0()


def test_calm_stays_at_p0_with_substitution_on():
    run = run_coupled_dynamics(
        subst_scale=0.6, use_amis=False, use_shocks=False,
        use_demand=False, use_industrial=False)
    for g in COUPLED_GRAINS:
        p = run.by_crop[g].price
        rel = float(np.max(np.abs(p - p[0]) / max(abs(p[0]), 1.0)))
        assert rel < 1e-12, f"{g} calm drifted {rel:.3e}"


def test_wheat_hike_spills_into_rice_maize_not_ethanol():
    base = run_coupled_dynamics(
        subst_scale=0.0, use_demand=False, use_amis=False,
        use_shocks=False, use_industrial=True)
    T = len(base.by_crop["wheat"].price)
    p0w = float(base.by_crop["wheat"].price[0])
    freeze = {"wheat": np.full(T, 1.5 * p0w)}
    off = run_coupled_dynamics(
        subst_scale=0.0, use_demand=False, use_amis=False,
        use_shocks=False, use_industrial=True, freeze_price=freeze)
    on = run_coupled_dynamics(
        subst_scale=0.6, use_demand=False, use_amis=False,
        use_shocks=False, use_industrial=True, freeze_price=freeze)
    # σ=0: rice/maize use unchanged; ethanol block identical.
    np.testing.assert_allclose(
        off.by_crop["rice"].consumption[:, 1:],
        base.by_crop["rice"].consumption[:, 1:], rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(
        off.by_crop["maize"].industrial,
        base.by_crop["maize"].industrial)
    # σ>0: substitute grains' use rises vs σ=0 freeze (t>=1; Jacobi lag).
    rice_ratio = (on.by_crop["rice"].consumption[:, 1:].sum()
                  / off.by_crop["rice"].consumption[:, 1:].sum())
    maize_ratio = (on.by_crop["maize"].consumption[:, 1:].sum()
                   / off.by_crop["maize"].consumption[:, 1:].sum())
    assert rice_ratio > 1.0, rice_ratio
    assert maize_ratio > 1.0, maize_ratio
    np.testing.assert_allclose(
        on.by_crop["maize"].industrial,
        off.by_crop["maize"].industrial)
