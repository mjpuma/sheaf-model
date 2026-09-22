"""Equation-level checks against supplement §D."""
import numpy as np

from sheaf.agrimate.equations import (
    alpha_domestic_adjusted,
    alpha_domestic_d10,
    author_inverse_demand,
    ces_price_index,
    consumption_ces,
    crop_budget_share,
    expected_harvest,
    expected_restriction,
    expected_two_market_sales,
    foreign_transaction_index,
    fulfill_sales,
    harvest_weights,
    inverse_demand,
    iota_floor,
    prorate_two_market_sales,
    purchaser_commodity_quantity,
    purchaser_demand,
    foreign_request_quantity,
    scale_baseline_shares,
)
from sheaf.agrimate.harvest import step_profile_from_months
from sheaf.agrimate.optimize import nash_ibr, solve_supplier_plan
from sheaf.agrimate.params import AgrimateParams


def test_harvest_weights_d1a():
    w = harvest_weights(24)
    assert w.shape == (24,)
    assert w[0] > w[-1]  # near-term realised (author expected_harvests.jl)
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


def test_alpha_adj_matches_both_markets_and_caps_at_one():
    # α_f * C * XI / (XI_world * XD) = 3.2 * 2 * 5 / (10 * 4) = 0.8
    assert abs(alpha_domestic_adjusted(3.2, 2.0, 5.0, 4.0, 10.0) - 0.8) < 1e-12
    assert alpha_domestic_adjusted(3.2, 10.0, 5.0, 1.0, 10.0) == 1.0
    assert alpha_domestic_adjusted(3.2, 2.0, 0.0, 4.0, 10.0) == 1.0
    assert alpha_domestic_adjusted(3.2, 2.0, 5.0, 0.0, 10.0) == 1.0


def test_purchaser_demand_sums_when_prices_equal():
    p = np.ones(4)
    s = np.array([0.1, 0.2, 0.3, 0.4])
    q = purchaser_demand(p, budget=10.0, sigma=6.0, shares=s)
    assert abs(float(np.dot(p, q)) - 10.0) < 1e-8


def test_d30a_budget_exhaustion_on_commodity_share():
    """Commodity spend equals D.30a value share of B, not the whole budget."""
    prices = np.array([0.8, 1.1, 1.4, 0.9])
    shares = np.array([0.1, 0.2, 0.3, 0.4])
    B, A, e, sigma = 12.0, 0.25, 1.0 / 3.0, 2.0
    q = purchaser_demand(prices, B, sigma, shares, A_d=A, eps_d=e)
    P = ces_price_index(prices, shares, sigma)
    spend = float(np.dot(prices, q))
    value_share = A * P ** (1.0 - e) / (1.0 + A * (P ** (1.0 - e) - 1.0))
    assert abs(spend - value_share * B) < 1e-8
    D = purchaser_commodity_quantity(P, A, e, B)
    assert abs(spend - P * D) < 1e-8
    assert spend < B - 1e-6


def test_d30a_off_recovers_lower_tier_when_A_d_is_one():
    prices = np.array([0.7, 1.2, 0.9])
    shares = np.array([0.2, 0.5, 0.3])
    B, sigma = 8.0, 2.0
    q_off = purchaser_demand(prices, B, sigma, shares)
    q_on = purchaser_demand(prices, B, sigma, shares, A_d=1.0, eps_d=1.0 / 3.0)
    assert np.allclose(q_off, q_on, atol=1e-10)
    assert abs(float(np.dot(prices, q_off)) - B) < 1e-8


def test_d30a_at_unit_price_is_A_d_times_budget():
    D = purchaser_commodity_quantity(1.0, 0.3, 1.0 / 3.0, 10.0)
    assert abs(D - 3.0) < 1e-12


def test_d30a_quantity_falls_when_price_index_rises():
    D1 = purchaser_commodity_quantity(1.0, 0.2, 1.0 / 3.0, 5.0)
    D2 = purchaser_commodity_quantity(1.5, 0.2, 1.0 / 3.0, 5.0)
    assert D2 < D1


def test_foreign_request_quantity_drops_own_origin():
    q = np.array([1.0, 2.0, 3.0])
    assert abs(foreign_request_quantity(q, 1) - 4.0) < 1e-12
    assert abs(foreign_request_quantity(q, 0) - 5.0) < 1e-12
    assert foreign_request_quantity(np.zeros(3), 0) == 0.0


def test_crop_budget_share_clips_and_adds_extra_demand():
    assert abs(crop_budget_share(0.2, 1.0, 0.0, 10.0) - 0.2) < 1e-12
    A = crop_budget_share(0.2, 2.0, 1.0, 10.0)
    assert abs(A - 0.4) < 1e-12
    assert crop_budget_share(0.9, 1.0, 50.0, 10.0) == 1.0
    assert crop_budget_share(0.1, 1.0, -50.0, 10.0) == 0.0


def test_consumption_capped_and_price_response():
    c1 = consumption_ces(1.0, 0.34, 0.15, 1.0)
    c2 = consumption_ces(2.0, 0.34, 0.15, 1.0)
    assert c2 < c1
    assert c1 > 0


def test_supplier_plan_respects_availability():
    p = AgrimateParams(plan_maxiter=20, nash_max_iters=2)
    H = np.ones(24) * 0.5
    sol = solve_supplier_plan(H, 0.0, np.ones(24) * 2.0, 2.0, 0.4, 3.5, 2.0, p)
    sold = sol["xd"] + sol["xi_ship"]
    assert sold.sum() <= H.sum() + 1e-6
    assert np.min(sol["S"]) >= -1e-8
    assert sol["success"]
    assert not sol["fallback"]


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


def test_prorate_caps_ratios_and_scales_foreign_by_one_minus_delta():
    ask = np.array([2.0, 4.0, 6.0])
    q, price, sd, si = prorate_two_market_sales(
        ask, seller=0, sales_d=2.0, sales_i=10.0, available=100.0,
        delta=0.5, p_dom=1.2, p_for=1.5,
    )
    assert abs(sd - 2.0) < 1e-12
    assert abs(si - 5.0) < 1e-12
    assert np.allclose(q, [2.0, 2.0, 3.0])
    assert np.allclose(price, [1.2, 1.5, 1.5])
    q2, _, sd2, si2 = prorate_two_market_sales(
        ask, 0, sales_d=100.0, sales_i=100.0, available=3.0,
        delta=0.5, p_dom=1.0, p_for=1.0,
    )
    assert abs(sd2 - 2.0) < 1e-12
    assert si2 <= 0.5 * (3.0 - sd2) + 1e-12
    assert abs(q2.sum() - sd2 - si2) < 1e-12


def test_expected_sales_do_not_redirect_a_sub_iota_foreign_plan():
    exp_d, exp_f = expected_two_market_sales(
        raw_d=np.array([1.0, 1.0]),
        raw_f=np.array([0.0001, 2.0]),
        delta=np.array([0.5, 0.5]),
        iota=0.001,
        x_avg=np.array([1.0, 1.0]),
    )
    assert exp_f[0] == 0.0
    assert abs(exp_d[0] - 1.0) < 1e-12
    assert abs(exp_f[1] - 1.0) < 1e-12
    assert abs(exp_d[1] - 2.0) < 1e-12
    z = iota_floor(np.array([0.01, 0.0001]), 0.001, np.array([1.0, 100.0]))
    assert z[0] == 0.01 and z[1] == 0.0


def test_author_inverse_demand_caps_at_1000():
    assert abs(author_inverse_demand(1.0, 3.2, 0.0) - 1.0) < 1e-12
    assert author_inverse_demand(0.0, 3.2, 0.0) == 1000.0
    assert author_inverse_demand(1e-6, 3.2, 0.0) == 1000.0


def test_scale_baseline_shares_uses_expected_over_star_then_renormalizes():
    a = np.array([[0.5, 0.0], [0.5, 1.0]])
    out = scale_baseline_shares(
        a, exp_d=np.array([2.0, 1.0]), exp_f=np.array([1.0, 3.0]),
        xd_star=np.array([1.0, 1.0]), xi_star=np.array([1.0, 1.0]),
    )
    assert np.allclose(out.sum(axis=0), 1.0)
    assert abs(out[0, 0] - 1.0 / 2.5) < 1e-12
    assert abs(out[1, 0] - 1.5 / 2.5) < 1e-12
    zero = scale_baseline_shares(
        np.zeros((2, 2)), np.zeros(2), np.zeros(2), np.ones(2), np.ones(2),
    )
    assert np.allclose(zero, 0.5)


def test_foreign_transaction_index_drops_the_diagonal():
    q = np.array([[100.0, 10.0], [5.0, 80.0]])
    p = np.array([[9.0, 2.0], [4.0, 7.0]])
    got = foreign_transaction_index(q, p, empty=1.0)
    assert abs(got - (10 * 2 + 5 * 4) / 15) < 1e-12
    assert foreign_transaction_index(np.eye(2), np.eye(2), empty=1.25) == 1.25
