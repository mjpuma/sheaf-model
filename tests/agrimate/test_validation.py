"""Three-scenario validation workflow (G0-U). No G1/G2."""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import numpy as np

from sheaf.agrimate.model import AgrimateResult, AgrimateSim
from sheaf.agrimate.params import wheat_params
from sheaf.agrimate.restrictions import EXPORTER_PULSE_REGIONS, restriction_pulse
from sheaf.agrimate.validation import (
    G1G2_DIFFERENTIATORS,
    SCENARIO_ORDER,
    SCENARIOS,
    annual_model_totals,
    load_usda_world_wheat,
    oat_settings,
    scenario_specs,
    score_prices,
    score_supply_stocks,
    undisturbed_diagnostics,
    write_figures,
    write_report,
    write_tables,
)
from sheaf.agrimate.wheat_data import prepare_wheat
from sheaf.agrimate.regions import REGION_NAMES


def _toy_result(name: str, n_r: int = 3, n_y: int = 24, n_years: int = 2,
                start: int = 2006) -> AgrimateResult:
    T = n_y * n_years
    rng = np.random.default_rng(abs(hash(name)) % 2**31)
    pidx = 1.0 + 0.1 * np.sin(np.linspace(0, 4 * np.pi, T))
    if name == "harvest":
        pidx = pidx * np.linspace(1.0, 1.2, T)
    if name == "harvest_amis":
        pidx = pidx * np.linspace(1.0, 1.5, T)
    H = rng.random((n_r, T)) * 0.5 + 0.2
    C = rng.random((n_r, T)) * 0.4 + 0.2
    xi = rng.random((n_r, T)) * 0.1
    Sp = np.cumsum(rng.random((n_r, T)) * 0.01, axis=1)
    Sc = np.cumsum(rng.random((n_r, T)) * 0.01, axis=1) + 0.1
    return AgrimateResult(
        start_year=start, end_year=start + n_years - 1,
        regions=list(REGION_NAMES[:n_r]),
        price_index=pidx, price_usd=pidx * 200.0,
        S_producer=Sp, S_consumer=Sc, failed_solves=0, fallback_solves=0,
        nash={"iterations": 1, "err": 0.0, "success": True},
        consumption=C, xi_ship=xi, harvest=H, sold_domestic=C * 0.5,
        p_consumer=np.ones((n_r, T)), inflow=C,
        use_anomalies=SCENARIOS[name]["use_anomalies"],
        use_restrictions=SCENARIOS[name]["use_restrictions"],
    )


def test_scenario_flags_toggle_harvest_and_delta():
    data = prepare_wheat(start_year=2006, end_year=2006)
    u = AgrimateSim(data, use_anomalies=False, use_restrictions=False)
    h = AgrimateSim(data, use_anomalies=True, use_restrictions=False)
    a = AgrimateSim(data, use_anomalies=True, use_restrictions=True)
    assert np.allclose(u.delta_at(0), 0.0)
    assert np.allclose(h.delta_at(0), 0.0)
    assert a.delta_at(0).shape == (len(data.regions),)
    # anomalies are applied when the year column is nonzero
    if np.any(np.abs(data.anomaly[:, 0]) > 1e-12):
        assert not np.allclose(u.harvest_at(0), h.harvest_at(0))
    else:
        assert np.allclose(u.harvest_at(0), h.harvest_at(0))
    assert np.allclose(h.harvest_at(0), a.harvest_at(0))


def test_three_scenarios_are_agrimate_not_g1g2():
    specs = {s.name: s for s in scenario_specs()}
    assert tuple(specs) == SCENARIO_ORDER
    assert specs["undisturbed"].use_anomalies is False
    assert specs["undisturbed"].use_restrictions is False
    assert specs["harvest"].use_anomalies is True
    assert specs["harvest"].use_restrictions is False
    assert specs["harvest_amis"].use_anomalies is True
    assert specs["harvest_amis"].use_restrictions is True
    assert "G1" in G1G2_DIFFERENTIATORS and "G2" in G1G2_DIFFERENTIATORS
    # disabled G1/G2 recover this host — recorded, not implemented
    assert "Disabled G1" in G1G2_DIFFERENTIATORS["G1"]
    assert "Disabled G2" in G1G2_DIFFERENTIATORS["G2"]


def test_oat_keeps_author_alpha_and_lists_bai_ten():
    base = wheat_params()
    assert base.alpha_i == 3.2
    alphas = [v for n, v, _ in oat_settings() if n == "alpha_i"]
    assert 3.2 in alphas
    assert 10.0 in alphas  # Bai fit as alternative, not default
    for n, v, p in oat_settings():
        if n == "alpha_i" and v == 3.2:
            assert p.alpha_i == 3.2
        if n != "alpha_i":
            assert p.alpha_i == 3.2


def test_restriction_pulse_is_prescribed_not_a_game():
    regions = list(REGION_NAMES)
    d = restriction_pulse(regions, 2007, 2008, "Ukraine", intensity=1.0,
                          duration_months=12, start="2008-01-01")
    i = regions.index("Ukraine")
    assert d.shape == (27, 48)
    assert d[i].max() == 1.0
    assert d[i, :24].sum() == 0.0  # 2007
    assert d[i, 24:].min() == 1.0  # all of 2008
    assert "Ukraine" in EXPORTER_PULSE_REGIONS
    assert "EU-27" in EXPORTER_PULSE_REGIONS


def test_usda_world_units_are_mmt():
    w = load_usda_world_wheat()
    row = w[w["year"] == 2008].iloc[0]
    # world wheat production ~ 600–700 MMT in 2008, not 1000 MT units
    assert 400 < row["production"] < 900
    assert 0.1 < row["stock_to_use"] < 0.6


def test_scoring_on_toy_paths(tmp_path: Path):
    results = {n: _toy_result(n) for n in SCENARIO_ORDER}
    data = prepare_wheat(start_year=2006, end_year=2007)
    # trim toy regions to match helper that indexes by name
    # annual_model_totals only needs arrays
    ann = annual_model_totals(results["harvest_amis"])
    assert set(ann["year"]) == {2006, 2007}
    assert (ann["production"] > 0).all()
    und = undisturbed_diagnostics(results["undisturbed"], spinup_end=2005)
    assert und["n_steps"] > 0
    assert und["S_p_min"] >= 0
    prices = score_prices(results, score_start=2006, score_end=2007)
    assert list(prices["scenario"]) == list(SCENARIO_ORDER)
    qty = score_supply_stocks(results, score_start=2006, score_end=2007)
    assert {"production", "ending_stocks"} <= set(qty["field"])
    # figures + report on toy (Fig 4/5 skipped: toy regions are first 3 names)
    tables = write_tables(data, {
        n: replace_regions(results[n], data.regions) for n in SCENARIO_ORDER
    }, tmp_path, score_start=2006, score_end=2007)
    figs = write_figures(data, {
        n: replace_regions(results[n], data.regions) for n in SCENARIO_ORDER
    }, tmp_path, score_start=2006, score_end=2007)
    assert (tmp_path / "score_prices.csv").exists()
    assert any(p.name == "fig1_coverage_trade.png" for p in figs)
    assert any(p.name == "fig2_prices.png" for p in figs)
    path = write_report(
        data,
        {n: replace_regions(results[n], data.regions) for n in SCENARIO_ORDER},
        tables, figs, tmp_path, 2006, 2007, 2006, 2007,
    )
    text = path.read_text()
    assert "G1" in text and "G2" in text
    assert "αI=3.2" in text or "alpha" in text.lower()
    assert "L1–L8" in text


def replace_regions(res: AgrimateResult, regions: list[str]) -> AgrimateResult:
    n_r, T = res.harvest.shape
    H = np.zeros((len(regions), T))
    H[:n_r] = res.harvest
    def pad(a):
        out = np.zeros((len(regions), T))
        out[:n_r] = a
        return out
    return AgrimateResult(
        start_year=res.start_year, end_year=res.end_year, regions=list(regions),
        price_index=res.price_index, price_usd=res.price_usd,
        S_producer=pad(res.S_producer), S_consumer=pad(res.S_consumer),
        failed_solves=0, fallback_solves=0, nash=res.nash,
        consumption=pad(res.consumption), xi_ship=pad(res.xi_ship),
        harvest=H, sold_domestic=pad(res.sold_domestic),
        p_consumer=pad(res.p_consumer), inflow=pad(res.inflow),
        use_anomalies=res.use_anomalies, use_restrictions=res.use_restrictions,
    )


def test_oat_short_window_is_three_years():
    d = prepare_wheat(2006, 2008)
    assert d.start_year == 2006 and d.end_year == 2008
    assert d.delta.shape == (27, 72)


def test_oat_hike_summary_classifies_movers():
    import pandas as pd
    from sheaf.agrimate.validation import _oat_hike_summary
    df = pd.DataFrame([
        {"param": "alpha_i", "value": 3.2, "hike_2008_model": 4.50},
        {"param": "alpha_i", "value": 10.0, "hike_2008_model": 2.00},
        {"param": "sigma_ces", "value": 2.0, "hike_2008_model": 4.50},
        {"param": "sigma_ces", "value": 2.5, "hike_2008_model": 4.51},
    ])
    text = "\n".join(_oat_hike_summary(df))
    assert "Moves 2008 hike:" in text and "`alpha_i`=10" in text
    assert "does not:" in text and "`sigma_ces`=2.5" in text
    assert "No parameter was adopted" in text


def test_author_defaults_not_replaced_by_replace():
    p = wheat_params()
    q = replace(p, alpha_i=10.0)
    assert p.alpha_i == 3.2
    assert q.alpha_i == 10.0
