"""B3: supplier harvest horizon N_year+1. Not a Julia copy, pin, or G1."""
from __future__ import annotations

from pathlib import Path

from sheaf.agrimate.fig4_config import PROTECTED_THREE_SCENARIO
from sheaf.agrimate.params import wheat_params
from sheaf.agrimate.validation import OUT_DEFAULT
from sheaf.agrimate.xi_split import n_julia_sources

ROOT = Path(__file__).resolve().parents[2]
DISPATCH = ROOT / "diagnostics" / "GATE0_REPRO_DISPATCH.md"


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


def test_horizon_files_and_dispatch():
    out = OUT_DEFAULT
    for name in (
        "prices_undisturbed_horizon.csv",
        "score_horizon.csv",
        "horizon.md",
    ):
        assert (out / name).is_file(), name
    for name in PROTECTED_THREE_SCENARIO:
        assert (out / name).is_file(), name
    for name in (
        "prices_undisturbed_xoth.csv",
        "score_xoth.csv",
        "xoth.md",
    ):
        assert (out / name).is_file(), name
    text = DISPATCH.read_text()
    assert text.count("\n") <= 20
    assert "Last completed: B3" in text
    assert "Next paste: B4" in text
    assert "G1/G2" in text
    assert "copy Julia" in text
    assert "Do not start G1" in text
    note = (out / "horizon.md").read_text()
    assert "Jan1" in note and "Jan2" in note
    assert "plan_maxiter" in note
    assert "Do not start G1" in note
    score = (out / "score_horizon.csv").read_text()
    assert "5125" in score
    assert "jan1_xi" in score
