"""B3: supplier harvest horizon N_year+1. Not a Julia copy, pin, or G1."""
from __future__ import annotations

from pathlib import Path

from sheaf.agrimate.params import wheat_params
from sheaf.agrimate.xi_split import n_julia_sources

ROOT = Path(__file__).resolve().parents[2]


def test_horizon_does_not_copy_julia_or_retune_or_open_g1():
    assert n_julia_sources() == 0
    p = wheat_params()
    assert p.alpha_i == 3.2
    assert p.zeta_penalty == 0.0
    assert p.n_for_months == 3
    assert p.plan_maxiter == 40
    eq = (ROOT / "sheaf" / "agrimate" / "equations.py").read_text()
    assert "def harvest_weights" in eq
    assert "def supplier_harvest_horizon" in eq
    assert "n_for = 3 * (n_year // 12)" in eq
    model = (ROOT / "sheaf" / "agrimate" / "model.py").read_text()
    assert "supplier_harvest_horizon" in model
    assert "n_h = n_y + 1" in model
    assert "expected_others_sales_foreign" not in model
    src = (ROOT / "sheaf" / "agrimate" / "params.py").read_text()
    assert "freeze_q_oth" not in src
    opt = (ROOT / "sheaf" / "agrimate" / "optimize.py").read_text()
    assert "nlopt" not in opt.lower()
    assert "revenue_curve" not in opt
