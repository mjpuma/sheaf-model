"""Post-R S-queue: S1 member-sum shipped; Next paste S2."""
from __future__ import annotations

from pathlib import Path

from sheaf.agrimate.a8_sum import write_r7_dispatch
from sheaf.agrimate.methods import publication_bar
from sheaf.agrimate.params import wheat_params
from sheaf.agrimate.wheat_data import prepare_wheat, psd_member_sum_then_mean

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


def test_s1_implements_member_sum():
    d = prepare_wheat(start_year=2006, end_year=2006, params=wheat_params())
    assert any("USDA PSD" in n and "not FAOSTAT Food Balances" in n for n in d.notes)
    src = (ROOT / "sheaf" / "agrimate" / "wheat_data.py").read_text()
    assert "psd_member_sum_then_mean" in src
    assert "groupby(region).mean()" not in src
    i_cn = d.regions.index("China")
    i_ea = d.regions.index("Eastern Africa")
    i_us = d.regions.index("USA")
    assert abs(d.H_annual[i_cn] - 112.7) < 0.2
    assert abs(d.H_annual[i_ea] - 3.31) < 0.05
    assert abs(d.H_annual[i_us] - 61.4) < 0.2
    assert any("5074" in n for n in d.notes)


def test_dispatch_next_paste_is_s2():
    text = DISPATCH.read_text()
    assert text.count("\n") <= 20
    assert "Last completed: S1" in text
    assert "Next paste: S2" in text
    assert "Next paste: S1" not in text.split("Next paste: S2")[0][-80:]
    assert "R11" in text
    assert "G1/G2" in text
    assert "L1–L8" in text
    assert "FAO ΔS" in text
    assert "2006 pin" in text or "pin" in text
    assert "Bai 10" in text
    assert "item-3" in text or "item 3" in text.lower() or "last/first" in text


def test_s2_prompt_forbids_pin_and_l1l8():
    text = NEXT.read_text()
    assert "Task S2 only" in text
    assert "Do not pin" in text
    assert "L1–L8" in text
    assert "Do not write freeze_q_oth into" in text
    assert "G1 / G2" in text or "G1/G2" in text
    assert "blocked until G0-P accepted" in text
    assert "**S1**" in text
    assert "member-sum" in text
    assert "ending_stocks" in text


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
        assert "S2" in body or "S1" in body, rel
    repro = (ROOT / "diagnostics" / "GATE0_REPRO_PROMPTS.md").read_text()
    assert "exhausted" in repro.lower()
    dep = (ROOT / "diagnostics" / "GATE0_DEPARTURES.md").read_text()
    assert "S1 implemented" in dep or "implemented**" in dep
    assert "Never FAO ΔS" in dep
    assert "approved, not implemented" not in dep


def test_r7_dispatch_writer_does_not_clobber_s2(tmp_path):
    living = tmp_path / "GATE0_REPRO_DISPATCH.md"
    living.write_text(DISPATCH.read_text())
    before = living.read_text()
    assert "Next paste: S2" in before
    from sheaf.agrimate.a8_sum import a8_mean_vs_sum_table

    tab = a8_mean_vs_sum_table()
    write_r7_dispatch(tab, path=living)
    assert living.read_text() == before


def test_member_sum_helper_matches_psd_regional_annual():
    from sheaf.data_usda import load_psd_country
    from sheaf.agrimate.wheat_data import _psd_to_region, psd_regional_annual

    raw = load_psd_country("wheat").copy()
    raw["region"] = [
        _psd_to_region(c, n) for c, n in zip(raw["country_code"], raw["country_psd"])
    ]
    g = psd_member_sum_then_mean(raw.dropna(subset=["region"]))
    ann = psd_regional_annual()
    base = ann[(ann["year"] >= 2007) & (ann["year"] <= 2009)]
    byr = base.groupby("region")[["production", "consumption", "ending_stocks"]].mean()
    for region in ("China", "Eastern Africa", "USA"):
        assert abs(float(g.loc[region, "production"]) - float(byr.loc[region, "production"])) < 1e-9
        assert abs(float(g.loc[region, "ending_stocks"]) - float(byr.loc[region, "ending_stocks"])) < 1e-9
