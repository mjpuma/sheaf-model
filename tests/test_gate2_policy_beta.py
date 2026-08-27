"""Hard bars for the Gate 2 policy beta. See diagnostics/GATE2_PLAN.md."""
from __future__ import annotations

import inspect

import numpy as np
import pytest

from sheaf.dynamic_crop import run_crop_dynamics
from sheaf.dynamic_policy import (
    PolicyKnobs,
    apply_year_tau,
    gov_buffer,
    grid_best_response,
    prepare_beta,
    shock_year_harvest,
    simulate_headey,
    year_slice,
)


@pytest.fixture(scope="module")
def knobs() -> PolicyKnobs:
    return PolicyKnobs()


@pytest.fixture(scope="module")
def prep(knobs):
    return prepare_beta(knobs)


@pytest.fixture(scope="module")
def calm_br(prep, knobs):
    return grid_best_response(prep, prep.H, knobs)


@pytest.fixture(scope="module")
def shock_harvest(prep, knobs):
    return shock_year_harvest(
        prep, knobs.exporter, knobs.shock_year, knobs.harvest_mult)


@pytest.fixture(scope="module")
def shock_br(prep, knobs, shock_harvest):
    return grid_best_response(prep, shock_harvest, knobs)


@pytest.fixture(scope="module")
def headey_calm(prep, knobs):
    return simulate_headey(prep, prep.H, knobs)


@pytest.fixture(scope="module")
def headey_shock(prep, knobs, shock_harvest):
    return simulate_headey(prep, shock_harvest, knobs)


def test_run_crop_dynamics_still_defaults_amis_on():
    # Hard bar 4: this module must not change P1's exogenous-AMIS default.
    sig = inspect.signature(run_crop_dynamics)
    assert sig.parameters["use_amis"].default is True
    assert sig.parameters["use_shocks"].default is True


def test_apply_year_tau_only_shock_year(prep, knobs):
    cuts = apply_year_tau(prep, knobs.exporter, knobs.shock_year, 0.6)
    i = prep.countries.index(knobs.exporter)
    sl = year_slice(prep, knobs.shock_year)
    assert np.allclose(cuts[i, sl], 0.6)
    mask = np.ones(cuts.shape[1], dtype=bool)
    mask[sl] = False
    assert np.allclose(cuts[i, mask], 0.0)
    for j, name in enumerate(prep.countries):
        if name != knobs.exporter:
            assert np.allclose(cuts[j], 0.0)


def test_shock_harvest_only_shock_year(prep, knobs, shock_harvest):
    i = prep.countries.index(knobs.exporter)
    sl = year_slice(prep, knobs.shock_year)
    assert np.allclose(shock_harvest[i, sl], prep.H[i, sl] * knobs.harvest_mult)
    mask = np.ones(prep.H.shape[1], dtype=bool)
    mask[sl] = False
    assert np.allclose(shock_harvest[i, mask], prep.H[i, mask])


def test_calm_tau_star_is_zero(calm_br):
    tau, rows = calm_br
    assert tau == 0.0
    by_tau = {r["tau"]: r for r in rows}
    assert by_tau[0.0]["W"] == max(r["W"] for r in rows)
    # Year-mean buffer does not bind on climatology.
    assert by_tau[0.0]["penalty"] == 0.0
    assert by_tau[0.0]["mean_stock"] > by_tau[0.0]["s_gov"]


def test_shock_tau_star_positive(shock_br):
    tau, rows = shock_br
    assert tau > 0.0
    by_tau = {r["tau"]: r for r in rows}
    assert by_tau[tau]["W"] == max(r["W"] for r in rows)
    # Food-security term binds on the open-trade shocked path.
    assert by_tau[0.0]["penalty"] > 0.0
    assert by_tau[0.0]["mean_stock"] < by_tau[0.0]["s_gov"]


def test_tau_cuts_shock_shipments(shock_br):
    tau, rows = shock_br
    by_tau = {r["tau"]: r for r in rows}
    assert by_tau[tau]["sum_exports"] < by_tau[0.0]["sum_exports"]


def test_gov_buffer_is_not_gate0_safety(prep, knobs):
    i = prep.countries.index(knobs.exporter)
    s_gov = gov_buffer(prep, knobs)
    assert s_gov == pytest.approx(knobs.gov_stu * float(prep.C_ann[i]))
    assert s_gov > float(prep.safety[i])


def test_headey_calm_is_open(prep, knobs, headey_calm):
    _res, cuts, meta = headey_calm
    i = prep.countries.index(knobs.exporter)
    sl = year_slice(prep, knobs.shock_year)
    assert float(cuts[i, sl].max()) == 0.0
    assert meta["n_year"] == 0
    assert np.allclose(cuts[i], 0.0)


def test_headey_shock_turns_on_inside_the_year(prep, knobs, headey_shock):
    _res, cuts, meta = headey_shock
    i = prep.countries.index(knobs.exporter)
    sl = year_slice(prep, knobs.shock_year)
    assert meta["max_tau"] > 0.0
    assert 0 < meta["n_year"] <= 24
    assert np.allclose(cuts[i, sl][cuts[i, sl] > 0], knobs.tau_on)
    mask = np.ones(cuts.shape[1], dtype=bool)
    mask[sl] = False
    assert np.allclose(cuts[i, mask], 0.0)


def test_headey_cuts_shock_shipments(headey_shock):
    _res, _cuts, meta = headey_shock
    assert meta["closed_exports"] < meta["open_exports"]
