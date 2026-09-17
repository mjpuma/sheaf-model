"""Author-param defaults and wheat-path wiring locks."""
from pathlib import Path

import numpy as np

from sheaf.agrimate.optimize import solve_supplier_plan
from sheaf.agrimate.params import AgrimateParams


def test_author_beta_and_tau_p_defaults():
    p = AgrimateParams()
    assert p.beta_loc == 0.05
    assert p.tau_p == 0.2


def test_beta_loc_and_tau_p_are_not_read_outside_params():
    """Wheat two_markets path does not use β/τ_P; do not invent a rule."""
    root = Path(__file__).resolve().parents[2] / "sheaf" / "agrimate"
    hits = []
    for path in sorted(root.glob("*.py")):
        if path.name == "params.py":
            continue
        text = path.read_text()
        if "beta_loc" in text or "tau_p" in text:
            hits.append(path.name)
    assert hits == []


def test_beta_loc_does_not_enter_supplier_plan():
    H = np.ones(24) * 0.5
    others = np.ones(24) * 2.0
    p0 = AgrimateParams(plan_maxiter=15, beta_loc=0.05, tau_p=0.2)
    p1 = AgrimateParams(plan_maxiter=15, beta_loc=10.0, tau_p=100.0)
    sol0 = solve_supplier_plan(H, 0.0, others, 2.0, 0.4, 3.5, 2.0, p0)
    sol1 = solve_supplier_plan(H, 0.0, others, 2.0, 0.4, 3.5, 2.0, p1)
    assert sol0["success"] and sol1["success"]
    assert np.allclose(sol0["xd"], sol1["xd"])
    assert np.allclose(sol0["xi"], sol1["xi"])
    assert np.allclose(sol0["S"], sol1["S"])
