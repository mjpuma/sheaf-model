"""G0-N: always-feasible fraction parameterization of D.11–D.21."""
import numpy as np

from sheaf.agrimate.optimize import (
    _plan_objective_grad,
    fractions_to_sales,
    sales_to_fractions,
    solve_supplier_plan,
)
from sheaf.agrimate.params import AgrimateParams


def test_fractions_always_nonnegative_storage():
    rng = np.random.default_rng(1)
    H = rng.random(24)
    S0 = 1.5
    delta = np.zeros(24)
    delta[0] = 0.5
    for _ in range(20):
        fd = rng.random(24)
        fi = rng.random(24)
        xd, xi, xi_ship, S = fractions_to_sales(fd, fi, S0, H, 0.0, delta)
        assert np.min(S) >= -1e-12
        assert np.min(xd) >= -1e-12
        assert np.min(xi) >= -1e-12
        assert np.min(xi_ship) >= -1e-12
        assert np.max(np.abs(xi_ship - xi * (1.0 - delta))) < 1e-12


def test_sales_fraction_roundtrip_on_feasible_path():
    rng = np.random.default_rng(2)
    H = rng.random(24) + 0.1
    S0 = 0.8
    delta = np.zeros(24)
    fd0 = rng.random(24)
    fi0 = rng.random(24)
    xd, xi, _, S = fractions_to_sales(fd0, fi0, S0, H, 0.0, delta)
    fd1, fi1 = sales_to_fractions(xd, xi, S0, H, 0.0, delta)
    xd2, xi2, _, S2 = fractions_to_sales(fd1, fi1, S0, H, 0.0, delta)
    assert np.allclose(xd, xd2, atol=1e-10)
    assert np.allclose(xi, xi2, atol=1e-10)
    assert np.allclose(S, S2, atol=1e-10)
    assert np.min(S2) >= -1e-12


def test_zero_harvest_plan_stays_feasible():
    p = AgrimateParams(plan_maxiter=15)
    H = np.zeros(24)
    sol = solve_supplier_plan(H, 2.0, np.ones(24), 0.2, 0.3, 3.5, 2.0, p)
    assert sol["success"]
    assert not sol["fallback"]
    assert np.min(sol["S"]) >= -1e-8
    assert np.all(sol["xd"] >= -1e-12)
    assert np.all(sol["xi"] >= -1e-12)


def test_restriction_not_double_applied_in_returned_intended_sales():
    p = AgrimateParams(plan_maxiter=20)
    H = np.ones(24) * 0.5
    dhat = np.zeros(24)
    dhat[0] = 1.0
    sol = solve_supplier_plan(H, 0.0, np.ones(24) * 2.0, 2.0, 0.4, 3.5, 2.0, p,
                              delta_hat=dhat)
    assert sol["success"]
    assert abs(sol["xi_ship"][0]) < 1e-10
    # Intended XI may be positive; shipped is scaled by (1-Δ).
    assert sol["xi_ship"][0] <= sol["xi"][0] + 1e-12


def test_d8_xmin_penalty_is_soft_not_hard():
    """Author x_minimum is a quadratic penalty (ζ=0), not a 1e-6 sales bound."""
    p = AgrimateParams(plan_maxiter=15, xmin_share=0.2, zeta_penalty=0.0)
    H = np.ones(24) * 0.5
    sol = solve_supplier_plan(H, 0.0, np.ones(24) * 2.0, 2.0, 0.4, 3.5, 2.0, p)
    assert sol["success"]
    assert np.min(sol["S"]) >= -1e-8


def test_supplier_plan_analytic_grad_matches_finite_difference():
    p = AgrimateParams(zeta_penalty=1.0, xmin_share=0.0)
    n = 8
    H = np.linspace(0.2, 0.8, n)
    S0 = 0.4
    others = np.full(n, 1.5)
    xi_star = np.full(n, 0.3)
    xd_star = np.full(n, 0.4)
    delta = np.zeros(n)
    delta[1] = 0.4
    rng = np.random.default_rng(3)
    z = rng.random(2 * n) * 0.9 + 0.05
    f0, g0 = _plan_objective_grad(
        z, H, S0, others, xi_star, xd_star, 3.5, 2.0, p, delta)
    eps = 1e-6
    g_fd = np.empty_like(z)
    for i in range(z.size):
        zp, zm = z.copy(), z.copy()
        zp[i] += eps
        zm[i] -= eps
        fp, _ = _plan_objective_grad(
            zp, H, S0, others, xi_star, xd_star, 3.5, 2.0, p, delta)
        fm, _ = _plan_objective_grad(
            zm, H, S0, others, xi_star, xd_star, 3.5, 2.0, p, delta)
        g_fd[i] = (fp - fm) / (2.0 * eps)
    rel = np.abs(g0 - g_fd) / np.maximum(np.abs(g_fd), 1e-6)
    assert float(np.max(rel)) < 2e-4, (g0, g_fd, rel)


def test_nonzero_S0_with_seasonal_harvest_is_feasible():
    """Mid-year stock already holds realised harvest; programme must stay feasible."""
    p = AgrimateParams(plan_maxiter=20)
    profile = np.zeros(24)
    profile[6:10] = 1.0
    profile /= profile.sum()
    H = profile * 12.0
    S0 = float(H[:8].sum())
    sol = solve_supplier_plan(H, S0, np.ones(24), 0.2, 0.3, 3.5, 2.0, p)
    assert sol["success"]
    assert not sol["fallback"]
    assert np.min(sol["S"]) >= -1e-8


def test_international_inverse_demand_uses_world_scale():
    """D.7 argument is (own + others) / XI*_world, so Nash-scale q is O(1)."""
    p = AgrimateParams(plan_maxiter=25)
    H = np.ones(24) * 0.5
    xi_world = 3.0
    others = np.full(24, 2.5)
    own_star = 0.5
    sol = solve_supplier_plan(
        H, 0.0, others, xi_world, own_star, 3.5, 2.0, p,
        x0=np.concatenate([np.full(24, 0.4), np.full(24, 0.1)]),
    )
    assert sol["success"]
    q = (sol["xi_ship"] + others) / xi_world
    assert float(np.max(q)) < 20.0
    from sheaf.agrimate.equations import inverse_demand
    pi = inverse_demand(q, 3.5, 0.0, p.demand_arg_floor)
    assert float(np.max(pi)) < 100.0
    assert float(np.min(pi)) > 1e-6


def test_supplier_plan_counts_floor_and_is_feasible():
    p = AgrimateParams(plan_maxiter=20)
    H = np.ones(24) * 0.5
    sol = solve_supplier_plan(H, 0.0, np.ones(24) * 2.0, 2.0, 0.4, 3.5, 2.0, p)
    assert sol["success"]
    assert np.min(sol["S"]) >= -1e-8
    assert (sol["xd"] + sol["xi_ship"]).sum() <= H.sum() + 1e-6
    assert sol["floor_binds"] >= 0
    assert sol["residual"] < 1e-8


def test_unconverged_stays_feasible_and_is_not_fallback():
    """Low maxiter: scipy success=False is still a feasible accepted point."""
    p = AgrimateParams(plan_maxiter=1)
    H = np.linspace(0.05, 1.2, 24)
    sol = solve_supplier_plan(H, 0.3, np.ones(24) * 2.0, 2.0, 0.4, 3.2, 2.0, p)
    assert sol["success"]
    assert not sol["fallback"]
    assert sol["residual"] < 1e-8
    assert np.min(sol["S"]) >= -1e-8
    assert "converged" in sol
    if not sol["converged"]:
        assert sol["nit"] <= p.plan_maxiter + 1


def test_unconverged_is_counted_separately_from_failed():
    """Host must not treat unconverged as failed or drop the flag."""
    p = AgrimateParams(plan_maxiter=1)
    H = np.linspace(0.05, 1.2, 24)
    sol = solve_supplier_plan(H, 0.3, np.ones(24) * 2.0, 2.0, 0.4, 3.2, 2.0, p)
    assert sol["success"] is True
    assert sol["fallback"] is False
    assert sol["converged"] is False
    assert sol["residual"] < 1e-8
    assert sol["status"] == 1


def test_default_plan_maxiter_is_forty():
    assert AgrimateParams().plan_maxiter == 40


def test_x1_demand_locks_current_sales_and_uses_slsqp():
    """Author x1 is demand, clipped; future only is SLSQP. Not a pin."""
    p = AgrimateParams(plan_maxiter=20)
    H = np.ones(24) * 0.5
    S0 = 0.4
    A0 = S0 + H[0]
    d_dom, d_for = 0.2, 0.15
    sol = solve_supplier_plan(
        H, S0, np.ones(24) * 2.0, 2.0, 0.4, 3.2, 2.0, p,
        x1=(d_dom, d_for),
    )
    assert sol["success"]
    assert sol["x1_fixed"] is True
    assert sol["method"] == "SLSQP"
    assert abs(sol["xd"][0] - d_dom) < 1e-8
    assert abs(sol["xi"][0] - d_for) < 1e-8
    assert sol["xd"][0] + sol["xi"][0] <= A0 + 1e-8
    assert np.min(sol["S"]) >= -1e-8
    # Without x1 the test path stays L-BFGS-B (fraction-map unit tests).
    free = solve_supplier_plan(H, S0, np.ones(24) * 2.0, 2.0, 0.4, 3.2, 2.0, p)
    assert free["method"] == "L-BFGS-B"
    assert free["x1_fixed"] is False


def test_x1_domestic_priority_when_demand_exceeds_availability():
    from sheaf.agrimate.optimize import clip_demand_x1

    xd, xi = clip_demand_x1(5.0, 5.0, S0=0.0, H0=6.0, loss=0.0)
    assert abs(xd - 5.0) < 1e-12
    assert abs(xi - 1.0) < 1e-12
    xd, xi = clip_demand_x1(8.0, 1.0, S0=0.0, H0=6.0, loss=0.0)
    assert abs(xd - 6.0) < 1e-12
    assert abs(xi - 0.0) < 1e-12
