"""Post-R S-queue: S4 A7 inventory done; Next paste S5."""
from __future__ import annotations

from dataclasses import fields
from pathlib import Path

import pandas as pd

from sheaf.agrimate.a8_sum import write_r7_dispatch
from sheaf.agrimate.fb_wheatdata import write_r6_dispatch, write_s3_dispatch
from sheaf.agrimate.s4_a7 import write_s4_dispatch
from sheaf.agrimate.fig4_config import PROTECTED_THREE_SCENARIO
from sheaf.agrimate.methods import publication_bar
from sheaf.agrimate.model import AgrimateSim
from sheaf.agrimate.params import AgrimateParams, wheat_params
from sheaf.agrimate.validation import OUT_DEFAULT
from sheaf.agrimate.wheat_data import prepare_wheat, psd_member_sum_then_mean
from sheaf.agrimate.xi_split import (
    live_host_last_first,
    n_julia_sources,
    write_r4_dispatch,
    write_s2_dispatch,
)

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


def test_dispatch_next_paste_is_s5():
    text = DISPATCH.read_text()
    assert text.count("\n") <= 20
    assert "Last completed: S4" in text
    assert "Next paste: S5" in text
    assert "Next paste: S4" not in text.split("Next paste: S5")[0][-80:]
    assert "R11" in text
    assert "G1/G2" in text
    assert "L1–L8" in text
    assert "FAO ΔS" in text
    assert "2006 pin" in text or "pin" in text
    assert "Bai 10" in text
    assert "USDA stays default" in text or "USDA stays" in text
    assert "invent Egypt" in text or "Egypt not invented" in text


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


def test_s3_prompt_forbids_fao_delta_s():
    text = NEXT.read_text()
    assert "Task S3 only" in text
    assert "Never treat FAO ΔS as stocks" in text
    assert "ending_stocks" in text
    assert "**S3**" in text
    assert "Next paste S4" in text


def test_s4_prompt_does_not_invent_egypt():
    text = NEXT.read_text()
    assert "Task S4 only" in text
    assert "Do not invent an Egypt node" in text
    assert "put Fig. 4 knobs into wheat_params()" in text
    assert "Next paste S5" in text


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
        assert "S4" in body, rel
    repro = (ROOT / "diagnostics" / "GATE0_REPRO_PROMPTS.md").read_text()
    assert "exhausted" in repro.lower()
    dep = (ROOT / "diagnostics" / "GATE0_DEPARTURES.md").read_text()
    assert "S1 implemented" in dep or "implemented**" in dep
    assert "Never FAO ΔS" in dep or "not FAOSTAT FBSH ΔS" in dep
    assert "1.444" in dep
    assert "s3_fbsh.md" in dep
    assert "s4_a7.md" in dep
    assert "approved, not implemented" not in dep


def test_r7_dispatch_writer_does_not_clobber_s5(tmp_path):
    living = tmp_path / "GATE0_REPRO_DISPATCH.md"
    living.write_text(DISPATCH.read_text())
    before = living.read_text()
    assert "Next paste: S5" in before
    from sheaf.agrimate.a8_sum import a8_mean_vs_sum_table

    tab = a8_mean_vs_sum_table()
    write_r7_dispatch(tab, path=living)
    assert living.read_text() == before


def test_r4_dispatch_writer_does_not_clobber_s4(tmp_path):
    living = tmp_path / "GATE0_REPRO_DISPATCH.md"
    living.write_text(DISPATCH.read_text())
    before = living.read_text()
    csv = OUT_DEFAULT / "score_xi_split.csv"
    summary = pd.read_csv(csv)
    write_r4_dispatch(summary, path=living)
    assert living.read_text() == before


def test_r6_dispatch_writer_does_not_clobber_s4(tmp_path):
    living = tmp_path / "GATE0_REPRO_DISPATCH.md"
    living.write_text(DISPATCH.read_text())
    before = living.read_text()
    score = pd.read_csv(OUT_DEFAULT / "score_fb_wheatdata.csv").iloc[0].to_dict()
    write_r6_dispatch(score, path=living)
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


def test_s2_item3_labelled_no_freeze_no_julia():
    note = OUT_DEFAULT / "item3.md"
    csv = OUT_DEFAULT / "score_item3.csv"
    assert note.is_file()
    assert csv.is_file()
    text = note.read_text()
    assert "Not a pin" in text or "not a pin" in text.lower()
    assert "L1–L8" in text
    assert "Next paste: S3" in text
    assert "1.444" in text
    assert "not adopted" in text.lower() or "Not adopted" in text
    assert "0" in text and "*.jl" in text
    tab = pd.read_csv(csv)
    lf = float(tab["last_first"].iloc[0])
    assert lf > 1.1
    assert abs(lf - 1.444) < 0.01
    assert abs(float(tab["last_first_author"].iloc[0]) - 1.004) < 0.005
    assert int(tab["n_julia"].iloc[0]) == 0
    assert not bool(tab["freeze_q_oth_on_params"].iloc[0])
    live = live_host_last_first()
    assert live["last_first"] > 1.1
    assert n_julia_sources() == 0
    assert "freeze_q_oth" not in {f.name for f in fields(AgrimateParams)}
    data = prepare_wheat(start_year=2006, end_year=2006, params=wheat_params())
    sim = AgrimateSim(data, params=wheat_params(),
                      use_anomalies=False, use_restrictions=False)
    assert sim.freeze_q_oth is False
    src = (ROOT / "sheaf" / "agrimate" / "params.py").read_text()
    assert "freeze_q_oth" not in src
    assert "def wheat_params" in src
    for name in PROTECTED_THREE_SCENARIO:
        assert (OUT_DEFAULT / name).is_file(), name


def test_s2_dispatch_writer_does_not_clobber_later(tmp_path):
    living = tmp_path / "GATE0_REPRO_DISPATCH.md"
    living.write_text("Last completed: S3\nNext paste: S4\n")
    metrics = live_host_last_first()
    write_s2_dispatch(metrics, path=living)
    assert living.read_text() == "Last completed: S3\nNext paste: S4\n"


def test_s3_fbsh_not_adopted_usda_default():
    note = OUT_DEFAULT / "s3_fbsh.md"
    csv = OUT_DEFAULT / "score_s3_fbsh.csv"
    q = OUT_DEFAULT / "score_s3_fbsh_quantities.csv"
    assert note.is_file()
    assert csv.is_file()
    assert q.is_file()
    text = note.read_text()
    assert "Not adopted" in text or "not adopted" in text.lower()
    assert "Leave A1" in text
    assert "5074" in text
    assert "L1–L8" in text
    assert "Next paste: S4" in text
    assert "FoodTradeNetwork" in text
    assert wheat_params().alpha_i == 3.2
    tab = pd.read_csv(q)
    cn = tab[tab["region"] == "China"].iloc[0]
    ea = tab[tab["region"] == "Eastern Africa"].iloc[0]
    us = tab[tab["region"] == "USA"].iloc[0]
    assert abs(float(cn["H_ratio"]) - 1.0) < 0.05
    assert abs(float(ea["H_ratio"]) - 1.0) < 0.05
    assert abs(float(us["H_ratio"]) - 1.0) < 0.05
    score = pd.read_csv(csv).iloc[0]
    assert bool(score["adopt"]) is False
    assert float(score["moy_fbsh"]) > float(score["moy_usda"])
    d = prepare_wheat(start_year=2006, end_year=2006, params=wheat_params())
    assert any("USDA PSD" in n and "not FAOSTAT Food Balances" in n for n in d.notes)
    assert not any(n.startswith("PARALLEL") for n in d.notes)
    r6 = pd.read_csv(OUT_DEFAULT / "score_fb_wheatdata_quantities.csv")
    r6_cn = r6[r6["region"] == "China"].iloc[0]
    assert float(r6_cn["H_ratio"]) > 1.5
    for name in PROTECTED_THREE_SCENARIO:
        assert (OUT_DEFAULT / name).is_file(), name


def test_s3_dispatch_writer_does_not_clobber_later(tmp_path):
    living = tmp_path / "GATE0_REPRO_DISPATCH.md"
    living.write_text("Last completed: S4\nNext paste: S5\n")
    score = pd.read_csv(OUT_DEFAULT / "score_s3_fbsh.csv").iloc[0].to_dict()
    from sheaf.agrimate.fb_wheatdata import s3_adoption_verdict
    verdict = s3_adoption_verdict(score)
    write_s3_dispatch(score, verdict, path=living)
    assert living.read_text() == "Last completed: S4\nNext paste: S5\n"


def test_s5_prompt_exists_and_is_not_r11():
    text = NEXT.read_text()
    assert "Task S5 only" in text
    assert "not R11" in text.lower() or "This is not R11" in text
    assert "Do not pin 2006" in text or "Do not pin" in text
    assert "Next paste S6" in text


def test_s4_inventory_does_not_invent_egypt_or_retune():
    from sheaf.agrimate.regions import REGION_NAMES, REGION_ISO3
    from sheaf.agrimate.s4_a7 import (
        FIG4_EU28_EGYPT_NAMES,
        parallel_eu28_egypt_iso3,
    )
    from sheaf.agrimate.params import fig4_experiment_params

    assert "Egypt" not in REGION_NAMES
    assert "EU-28" not in REGION_NAMES
    assert "Brazil" in REGION_NAMES
    assert "EU-27" in REGION_NAMES
    assert "EGY" in REGION_ISO3["Northern Africa"]
    p = wheat_params()
    assert p.alpha_i == 3.2
    assert p.zeta_penalty == 0.0
    assert p.n_for_months == 3
    fig4 = fig4_experiment_params()
    assert fig4.alpha_i == 3.5
    assert fig4.zeta_penalty == 1.0
    assert fig4.n_for_months == 6
    par = parallel_eu28_egypt_iso3()
    assert list(par) == list(FIG4_EU28_EGYPT_NAMES)
    assert par["Egypt"] == ["EGY"]
    assert "GBR" in par["EU-28"]
    assert "BRA" in par["Rest of South America"]
    assert "Brazil" not in par
    note = (OUT_DEFAULT / "s4_a7.md").read_text()
    assert "Do not invent an Egypt node" in note
    assert "wheat_params()" in note
    assert "Next paste: S5" in note
    assert "not C.1" in note or "not** replaced" in note
    assert "L1–L8" in note
    tab = pd.read_csv(OUT_DEFAULT / "score_s4_a7.csv").iloc[0]
    assert bool(tab["host_has_egypt_node"]) is False
    assert bool(tab["reconstruction_adopted"]) is False
    assert bool(tab["usda_is_default"]) is True
    assert float(tab["wheat_params_alpha_i"]) == 3.2
    assert int(tab["n_julia"]) == 0
    d = prepare_wheat(start_year=2006, end_year=2006, params=wheat_params())
    assert any("USDA PSD" in n and "not FAOSTAT Food Balances" in n for n in d.notes)
    for name in PROTECTED_THREE_SCENARIO:
        assert (OUT_DEFAULT / name).is_file(), name


def test_s4_dispatch_writer_does_not_clobber_later(tmp_path):
    living = tmp_path / "GATE0_REPRO_DISPATCH.md"
    living.write_text("Last completed: S5\nNext paste: S6\n")
    inv = pd.read_csv(OUT_DEFAULT / "score_s4_a7.csv").iloc[0].to_dict()
    write_s4_dispatch(inv, path=living)
    assert living.read_text() == "Last completed: S5\nNext paste: S6\n"
