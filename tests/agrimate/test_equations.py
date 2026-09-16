"""Equation-level checks against supplement §D."""
import numpy as np

from sheaf.agrimate.equations import (
    alpha_domestic_d10,
    consumption_ces,
    expected_harvest,
    expected_restriction,
    fulfill_sales,
    harvest_weights,
    inverse_demand,
    purchaser_demand,
)
from sheaf.agrimate.harvest import step_profile_from_months
from sheaf.agrimate.optimize import nash_ibr, solve_supplier_plan
from sheaf.agrimate.params import AgrimateParams


def test_harvest_weights_d1a():
    w = harvest_weights(24)
    assert w.shape == (24,)
    assert w[0] < w[-1]
    assert np.all(w >= 0) and np.all(w <= 1)


def test_harvest_profile_normalised():
    p = step_profile_from_months(6, 8)
    assert abs(p.sum() - 1.0) < 1e-12
    assert np.all(p >= 0)


def test_restriction_expectation_d2():
    h = expected_restriction(0.95, 24)
    assert abs(h[0] - 0.95) < 1e-12
    assert float(np.max(np.abs(h[1:]))) == 0.0


def test_sales_domestic_priority_and_restriction():
    d, i = fulfill_sales(planned_d=5, planned_i=5, available=6, delta=0.5)
    assert abs(d - 5) < 1e-12
    assert abs(i - 0.5) < 1e-12  # 1 remaining * (1-0.5)


def test_inverse_demand_normalised():
    assert abs(float(inverse_demand(1.0, 3.5, 0.0)) - 1.0) < 1e-12
    assert float(inverse_demand(0.5, 3.5, 0.0)) > 1.0


def test_alpha_d10_matches_export_share():
    assert abs(alpha_domestic_d10(3.5, 2.0, 10.0) - 0.7) < 1e-12


def test_purchaser_demand_sums_when_prices_equal():
    p = np.ones(4)
    s = np.array([0.1, 0.2, 0.3, 0.4])
    q = purchaser_demand(p, budget=10.0, sigma=6.0, shares=s)
    assert abs(float(np.dot(p, q)) - 10.0) < 1e-8


def test_consumption_capped_and_price_response():
    c1 = consumption_ces(1.0, 0.34, 0.15, 1.0)
    c2 = consumption_ces(2.0, 0.34, 0.15, 1.0)
    assert c2 < c1
    assert c1 > 0


def test_supplier_plan_respects_availability():
    p = AgrimateParams(plan_maxiter=20, nash_max_iters=2)
    H = np.ones(24) * 0.5
    sol = solve_supplier_plan(H, 0.0, np.ones(24) * 2.0, 2.0, 0.4, 3.5, 2.0, p)
    sold = sol["xd"] + sol["xi"]
    assert sold.sum() <= H.sum() + 1e-6 + 1e-6
    assert np.min(sol["S"]) >= -1e-6


def test_nash_periodic_and_clears_harvest():
    p = AgrimateParams(plan_maxiter=15, nash_max_iters=3)
    rng = np.random.default_rng(0)
    H = rng.random((3, 24))
    H = H / H.sum(axis=1, keepdims=True) * 12.0
    alpha_d = np.array([2.0, 2.5, 3.0])
    xi_s = np.full(3, 0.2)
    xd_s = np.full(3, 0.3)
    nash = nash_ibr(H, alpha_d, xi_s, xd_s, p)
    sales = nash["sales"].sum(axis=1)
    rel = np.abs(sales - H.sum(axis=1)) / np.maximum(H.sum(axis=1), 1e-12)
    assert float(np.max(rel)) < 1e-12
    assert nash["success"]
