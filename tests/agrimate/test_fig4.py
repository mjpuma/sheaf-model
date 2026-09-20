"""P7: Agrimate Fig. 4 author series vs host. No G1/G2. No retune."""
from __future__ import annotations

import numpy as np
import pandas as pd

from sheaf.agrimate.fig4 import (
    AUTHOR_DIR,
    AUTHOR_SCENARIO_FILES,
    author_undisturbed_drift,
    host_monthly_index,
    score_fig4_prices,
    world_market_price_index,
)
from sheaf.agrimate.params import wheat_params
from sheaf.agrimate.validation import OUT_DEFAULT, SCENARIO_ORDER, _hike


def test_fig4_wm_price_drops_domestic_and_volume_weights():
    q = np.zeros((2, 2, 2))
    p = np.zeros((2, 2, 2))
    q[0, 0, 0] = 100.0  # domestic, ignored
    p[0, 0, 0] = 9.0
    q[0, 1, 0] = 10.0
    p[0, 1, 0] = 2.0
    q[1, 0, 0] = 5.0
    p[1, 0, 0] = 4.0
    q[0, 1, 1] = 1.0
    p[0, 1, 1] = 3.0
    wm = world_market_price_index(q, p)
    assert wm.shape == (2,)
    assert abs(wm[0] - (10 * 2 + 5 * 4) / 15) < 1e-12
    assert abs(wm[1] - 3.0) < 1e-12


def test_author_fig4_csvs_cover_three_scenarios_2006_11():
    monthly = pd.read_csv(AUTHOR_DIR / "monthly_world.csv")
    annual = pd.read_csv(AUTHOR_DIR / "annual_world.csv")
    regional = pd.read_csv(AUTHOR_DIR / "annual_regional.csv")
    assert set(monthly["scenario"]) == set(SCENARIO_ORDER)
    assert set(AUTHOR_SCENARIO_FILES) == set(SCENARIO_ORDER)
    m = monthly[(monthly["year"] >= 2006) & (monthly["year"] <= 2011)]
    assert len(m) == 3 * 6 * 12
    assert m["wm_price_index"].notna().all()
    a = annual[(annual["year"] >= 2006) & (annual["year"] <= 2011)]
    und = a[a["scenario"] == "undisturbed"]
    # Author baseline harvest is repeating (the P2 contrast).
    assert und["production"].max() - und["production"].min() < 1e-6
    assert "Ukraine" in set(regional["region"])
    assert "Egypt" in set(regional["region"])
    assert "EU-28" in set(regional["region"])
    assert "Brazil" not in set(regional["region"])


def test_author_baseline_does_not_drift():
    monthly = pd.read_csv(AUTHOR_DIR / "monthly_world.csv")
    d = author_undisturbed_drift(monthly, 2006, 2011)
    assert d["last_over_first"] < 1.05
    assert d["seasonal_corr_first_last"] > 0.95


def test_fig4_score_identical_series_is_one():
    idx = pd.period_range("2006-01", "2011-12", freq="M")
    rng = np.linspace(1.0, 1.4, len(idx))
    rows = []
    for name in SCENARIO_ORDER:
        for p, v in zip(idx, rng):
            rows.append({
                "year": int(p.year), "month": int(p.month),
                "scenario": name, "host_price_index": float(v),
                "wm_price_index": float(v),
            })
    df = pd.DataFrame(rows)
    sc = score_fig4_prices(df, df, 2006, 2011)
    assert np.allclose(sc["corr_index"], 1.0)
    assert np.allclose(sc["rmse_index"], 0.0)
    assert np.allclose(sc["hike_2008_host"], sc["hike_2008_author"])


def test_host_index_is_usd_over_p0():
    host = host_monthly_index(OUT_DEFAULT / "prices_three_scenarios.csv")
    p0 = float(host["p0"].iloc[0])
    row = host[(host["scenario"] == "harvest_amis")
               & (host["year"] == 2006) & (host["month"] == 1)].iloc[0]
    assert abs(row["host_price_index"] - row["host_usd"] / p0) < 1e-12
    # D.7 index, not a 2006 pin: 2006 mean is not 1.
    m06 = host[(host["scenario"] == "harvest_amis") & (host["year"] == 2006)]
    assert abs(m06["host_price_index"].mean() - 1.0) > 0.2


def test_fig4_report_is_independent_not_replication():
    text = (OUT_DEFAULT / "fig4.md").read_text()
    assert "Do **not** claim replication" in text
    assert "G0-U items 1–3" in text
    assert "1.444" in text or "1.443" in text
    assert "2304/5832" in text
    assert "α_foreign" in text
    assert "not a replication" in text.lower()
    assert "L1–L8" in text
    assert "digitisation" in text.lower()
    prices = pd.read_csv(OUT_DEFAULT / "score_fig4_prices.csv")
    amis = prices[prices["scenario"] == "harvest_amis"].iloc[0]
    # Author hike is the Fig. 4 number; host is larger. Not a retune check.
    assert amis["hike_2008_author"] < 2.5
    assert amis["hike_2008_host"] > amis["hike_2008_author"]
    # Same hike helper as Pink-Sheet scores.
    author_m = pd.read_csv(AUTHOR_DIR / "monthly_world.csv")
    sub = author_m[author_m["scenario"] == "harvest_amis"]
    s = pd.Series(
        sub["wm_price_index"].to_numpy(float),
        index=[pd.Period(year=int(y), month=int(m), freq="M")
               for y, m in zip(sub["year"], sub["month"])],
    )
    s = s[(s.index.year >= 2006) & (s.index.year <= 2011)]
    assert abs(float(amis["hike_2008_author"]) - _hike(s, 2006, 2008)) < 1e-9


def test_p7_does_not_retune_author_params():
    p = wheat_params()
    assert p.alpha_i == 3.2
    assert p.p_sto_annual == 0.1
    assert p.xmin_share == 0.2
    assert p.zeta_penalty == 0.0
    assert p.n_for_months == 3
