"""B2: domestic others in supplier D.7. Not a Julia copy, pin, or G1."""
from __future__ import annotations

from pathlib import Path

import numpy as np

from sheaf.agrimate.params import wheat_params
from sheaf.agrimate.wheat_data import prepare_wheat
from sheaf.agrimate.xi_split import n_julia_sources

ROOT = Path(__file__).resolve().parents[2]


def test_xoth_does_not_copy_julia_or_retune_or_open_g1():
    assert n_julia_sources() == 0
    p = wheat_params()
    assert p.alpha_i == 3.2
    assert p.zeta_penalty == 0.0
    assert p.n_for_months == 3
    assert p.plan_maxiter == 40
    opt = (ROOT / "sheaf" / "agrimate" / "optimize.py").read_text()
    assert "xd_others" in opt
    assert "(xd + xd_others) / xd_star" in opt
    assert "nlopt" not in opt.lower()
    assert "revenue_curve" not in opt
    model = (ROOT / "sheaf" / "agrimate" / "model.py").read_text()
    assert "expected_others_sales_foreign" not in model
    assert "share_imp[r] * others" in model
    assert "d.C_star[r]" in model
    src = (ROOT / "sheaf" / "agrimate" / "params.py").read_text()
    assert "freeze_q_oth" not in src


def test_c_star_is_not_xd_star():
    """X_star_domestic is baseline consumption, not residual domestic sales."""
    d = prepare_wheat(start_year=2006, end_year=2006, params=wheat_params())
    assert float(np.max(np.abs(d.C_star - d.XD_star))) > 0.01
