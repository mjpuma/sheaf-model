"""A-queue: inspect-only inventory next. Not a Julia copy, pin, or G1."""
from __future__ import annotations

from pathlib import Path

from sheaf.agrimate.params import wheat_params
from sheaf.agrimate.validation import OUT_DEFAULT
from sheaf.agrimate.xi_split import n_julia_sources

ROOT = Path(__file__).resolve().parents[2]
ALIGN = ROOT / "diagnostics" / "GATE0_ALIGN.md"
PROMPTS = ROOT / "diagnostics" / "GATE0_ALIGN_PROMPTS.md"
BRIEF = ROOT / "diagnostics" / "GATE0_AGRIMATE_BRIEF.md"
DISPATCH = ROOT / "diagnostics" / "GATE0_REPRO_DISPATCH.md"


def test_align_does_not_copy_julia_or_retune_or_open_g1():
    assert n_julia_sources() == 0
    p = wheat_params()
    assert p.alpha_i == 3.2
    assert p.zeta_penalty == 0.0
    assert p.n_for_months == 3
    assert p.plan_maxiter == 40
    text = ALIGN.read_text()
    assert "Do not copy" in text or "not a Julia" in text.lower()
    assert "G1" in text
    assert "Bar A" in text and "Bar B" in text
    assert "A1" in text
    prompts = PROMPTS.read_text()
    assert "Task A1 only" in prompts
    assert "Do not implement" in prompts
    assert "Do not copy author Julia into sheaf/agrimate" in prompts
    assert "Do not start G1" in prompts
    assert "dynamic_coupled" not in prompts
    assert "dynamic_policy" not in prompts


def test_align_a1_is_inspect_only_not_transcription():
    prompts = PROMPTS.read_text()
    assert "inspect-only" in prompts.lower() or "Inspect-only" in prompts
    assert "not a transcription" in prompts.lower()
    assert "align_inventory.md" in prompts
    assert "producer.jl" in prompts
    assert "consumer.jl" in prompts
    a1 = prompts.split("## A1")[1].split("## A3")[0]
    assert "Do not implement" in a1
    assert "Do not copy Julia" in a1 or "Do not copy author Julia" in prompts


def test_brief_has_open_team_questions():
    text = BRIEF.read_text()
    assert "Open (2026-09-21)" in text
    assert "14022004" in text
    assert "Fig. 4d" in text
    assert "world price" in text.lower()
    assert "α_foreign=10" in text or "Bai" in text
    assert "Do not need from the team" in text


def test_dispatch_next_paste_is_b4_after_b3():
    text = DISPATCH.read_text()
    assert text.count("\n") <= 20
    assert "Last completed: B3" in text
    assert "Next paste: B4" in text
    assert "4.81" in text
    assert "G1/G2" in text
    assert "copy Julia" in text
    assert "Do not start G1" in text
    assert "copy Julia" in text
    assert "Do not start G1" in text
    assert (OUT_DEFAULT / "rt_solver.md").is_file()
    inv = (OUT_DEFAULT / "align_inventory.md").read_text()
    assert "implement-now" in inv
    assert "yes (1)" in inv and "yes (2)" in inv
    assert inv.count("**yes") == 2
    assert "Do not start G1" in inv
    assert "determine_transactions_two_markets" in inv
    bq = ROOT / "diagnostics" / "GATE0_B_PROMPTS.md"
    btxt = bq.read_text()
    assert "Task B1 only" in btxt
    assert "Task B2 only" in btxt
    assert "Task B3 only" in btxt
    assert "Task B4 only" in btxt
    assert "Do not copy Julia" in btxt
    assert "Do not start G1" in btxt
    assert "plan_maxiter" in btxt
    assert "dynamic_coupled" not in btxt
    assert "dynamic_policy" not in btxt
