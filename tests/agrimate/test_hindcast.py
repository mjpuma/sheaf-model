"""P8: G0-H hindcast note. No retune, no L1–L8, no Bai αI=10."""
from __future__ import annotations

import numpy as np

from sheaf.agrimate.fig4 import load_author_fig4
from sheaf.agrimate.hindcast import (
    harvest_vs_amis_attribution,
    load_host_prices,
    month_of_year_profile,
    score_quantity_anomalies,
    score_seasonal_paths,
)
from sheaf.agrimate.params import wheat_params
from sheaf.agrimate.validation import OUT_DEFAULT, SCENARIO_ORDER, _hike


def test_hindcast_note_is_a_sourced_shortfall():
    text = (OUT_DEFAULT / "hindcast.md").read_text()
    assert "Explicit sourced shortfall" in text
    assert "not a replication" in text.lower()
    assert "L1–L8" in text
    assert "α_foreign=10" in text
    assert "not adopted" in text
    assert "1.444" in text or "1.443" in text
    assert "2304/5832" in text
    assert "not pin" in text.lower() or "Do not pin" in text
    assert "81.5" in text or "$81" in text
    assert "213.5" in text or "$213" in text
    # Pre-P2 3× stocks must not be repeated as current.
    assert "not 3×" in text


def test_hindcast_does_not_retune_author_params():
    p = wheat_params()
    assert p.alpha_i == 3.2
    assert p.p_sto_annual == 0.1
    assert p.xmin_share == 0.2
    assert p.zeta_penalty == 0.0


def test_seasonal_path_is_inverted_vs_pink_not_just_low_corr():
    prices = load_host_prices(OUT_DEFAULT)
    author = load_author_fig4()
    sc = score_seasonal_paths(prices, author["monthly"])
    ha = sc[sc["scenario"] == "harvest_amis"].iloc[0]
    assert list(sc["scenario"]) == list(SCENARIO_ORDER)
    # S1 member-sum moved full-window corr through zero; shape is still inverted.
    assert ha["corr_vs_pink"] < 0.2
    assert ha["moy_corr_vs_pink"] < -0.4
    assert ha["moy_maxmin_host"] > 10
    assert ha["moy_maxmin_pink"] < 1.2
    assert ha["moy_maxmin_author"] < 2.0
    assert ha["hike_2008_host"] > ha["hike_2008_author"]
    assert ha["hike_2008_host"] > 3.0
    assert 1.5 < ha["hike_2008_pink"] < 2.2
    assert 1.4 < ha["hike_2008_author"] < 1.9
    assert abs(ha["mean_2006_host_usd"] - 81.5) < 1.5
    assert abs(ha["mean_2006_pink_usd"] - 213.5) < 1.0
    s = prices["harvest_amis"]
    s = s[(s.index.year >= 2006) & (s.index.year <= 2011)]
    assert abs(float(ha["hike_2008_host"]) - _hike(s, 2006, 2008)) < 1e-9


def test_stock_level_bias_is_not_three_times_usda():
    qty = score_quantity_anomalies(OUT_DEFAULT)
    stk = qty[(qty["scenario"] == "harvest_amis")
              & (qty["field"] == "ending_stocks")].iloc[0]
    prod = qty[(qty["scenario"] == "harvest_amis")
               & (qty["field"] == "production")].iloc[0]
    assert 1.2 < stk["level_ratio"] < 2.0  # ~1.58× after P2, not ~3×
    assert abs(prod["corr_level"] - 0.803) < 0.02
    assert abs(stk["corr_anomaly"] - stk["corr_level"]) < 1e-9


def test_amis_still_differs_from_harvest_only():
    prices = load_host_prices(OUT_DEFAULT)
    a = harvest_vs_amis_attribution(prices)
    # S1: max |AMIS−harvest| moved to 2011-07; May 2008 lift is small.
    assert a["max_abs_delta_at"] == "2011-07"
    assert a["max_abs_delta_usd"] > 50
    assert abs(a["jun2007_amis"] - a["jun2007_harvest"]) < 10
    assert 0 < a["may2008_amis"] - a["may2008_harvest"] < 50


def test_month_of_year_profile_length():
    prices = load_host_prices(OUT_DEFAULT)
    moy = month_of_year_profile(prices["pink_usd"])
    assert list(moy.index) == list(range(1, 13))
    assert np.isfinite(moy).all()
