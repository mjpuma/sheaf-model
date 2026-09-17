"""Accounting identities on a tiny Nash year."""
import numpy as np

from sheaf.agrimate.optimize import nash_ibr
from sheaf.agrimate.params import AgrimateParams


def test_nash_sales_finite_and_nonnegative():
    p = AgrimateParams(plan_maxiter=15, nash_max_iters=2)
    H = np.ones((2, 24))
    nash = nash_ibr(H, np.array([2.0, 2.0]), np.array([0.2, 0.2]), np.array([0.3, 0.3]), p)
    assert np.all(nash["xd"] >= -1e-10)
    assert np.all(nash["xi"] >= -1e-10)
    assert np.all(np.isfinite(nash["sales"]))
