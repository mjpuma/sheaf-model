"""Post-R S-queue: R-science exhausted; Next paste S1; this PR does not rewrite the host."""
from __future__ import annotations

from pathlib import Path

from sheaf.agrimate.a8_sum import write_r7_dispatch
from sheaf.agrimate.methods import publication_bar
from sheaf.agrimate.params import wheat_params
from sheaf.agrimate.wheat_data import prepare_wheat

ROOT = Path(__file__).resolve().parents[2]
NEXT = ROOT / "diagnostics" / "GATE0_NEXT_PROMPTS.md"
DISPATCH = ROOT / "diagnostics" / "GATE0_REPRO_DISPATCH.md"


def test_g0_p_still_not_accepted():
    bar = publication_bar()
    assert bar["accepted"] is False
    assert bar["item3_undisturbed"] is False
    p = wheat_params()
    assert p.alpha_i == 3.2
    assert p.zeta_penalty == 0.0
    assert p.n_for_months == 3
    assert p.p_sto_annual == 0.1
    assert p.xmin_share == 0.2


def test_this_pr_does_not_implement_s1():
    d = prepare_wheat(start_year=2006, end_year=2006, params=wheat_params())
    assert any("USDA PSD" in n and "not FAOSTAT Food Balances" in n for n in d.notes)
    src = (ROOT / "sheaf" / "agrimate" / "wheat_data.py").read_text()
    assert 'base.groupby("region")' in src
    assert ".mean()" in src.split('base.groupby("region")', 1)[1][:200]


def test_dispatch_next_paste_is_s1():
    text = DISPATCH.read_text()
    assert text.count("\n") <= 20
    assert "Last completed: R-queue plan" in text
    assert "Next paste: S1" in text
    assert "Next paste: R8" not in text
    assert "R11" in text
    assert "G1/G2" in text
    assert "L1–L8" in text
    assert "FAO ΔS" in text
    assert "2006 pin" in text or "pin" in text
    assert "Bai 10" in text
    assert "item-3" in text
    assert "A8" in text and "A7" in text and "A1" in text


def test_s1_prompt_forbids_delta_s_pin_and_l1l8():
    text = NEXT.read_text()
    assert "Task S1 only" in text
    assert "Never FAOSTAT FBSH ΔS" in text or "Never FAO ΔS" in text
    assert "Do not pin" in text
    assert "L1–L8" in text
    assert "Do not retune αI" in text
    assert "wheat_params()" in text
    assert "member-sum" in text
    assert "ending_stocks" in text
    assert "Do not write freeze_q_oth into" in text
    assert "G1 / G2" in text or "G1/G2" in text
    assert "blocked until G0-P accepted" in text
    assert "**S1**" in text
    assert "**next**" in text
    assert "S1 —" in text


def test_pointers_name_s_queue():
    for rel in (
        "diagnostics/DEVELOPMENT.md",
        "diagnostics/GATE0_CONTRACT.md",
        "diagnostics/GATE0_PROMPTS.md",
        "diagnostics/GATE0_REPRO_PROMPTS.md",
        "diagnostics/GATE0_VALIDATION.md",
        "AGENTS.md",
    ):
        body = (ROOT / rel).read_text()
        assert "GATE0_NEXT_PROMPTS.md" in body, rel
        assert "S1" in body, rel
    repro = (ROOT / "diagnostics" / "GATE0_REPRO_PROMPTS.md").read_text()
    assert "exhausted" in repro.lower()
    dep = (ROOT / "diagnostics" / "GATE0_DEPARTURES.md").read_text()
    assert "S1 (approved, not implemented)" in dep
    assert "Never FAO ΔS" in dep


def test_r7_dispatch_writer_does_not_clobber_s1(tmp_path):
    living = tmp_path / "GATE0_REPRO_DISPATCH.md"
    living.write_text(DISPATCH.read_text())
    before = living.read_text()
    assert "Next paste: S1" in before
    from sheaf.agrimate.a8_sum import a8_mean_vs_sum_table

    tab = a8_mean_vs_sum_table()
    write_r7_dispatch(tab, path=living)
    assert living.read_text() == before
