"""P9: regional USDA vs 27-node host. No retune, no L1–L8, coverage labelled."""
from __future__ import annotations

import numpy as np
import pandas as pd

from sheaf.agrimate.params import wheat_params
from sheaf.agrimate.regional import (
    NAMED_REGIONS,
    model_production_annual,
    psd_construction_table,
)
from sheaf.agrimate.validation import OUT_DEFAULT
from sheaf.agrimate.wheat_data import prepare_wheat


def test_author_params_not_retuned_for_regional_gap():
    p = wheat_params()
    assert p.alpha_i == 3.2
    assert p.p_sto_annual == 0.1
    assert p.xmin_share == 0.2
    assert p.zeta_penalty == 0.0


def test_named_regions_match_prompt():
    assert "USA" in NAMED_REGIONS
    assert "EU-27" in NAMED_REGIONS
    assert "Eastern Africa" in NAMED_REGIONS
    assert "China" in NAMED_REGIONS
    assert "Egypt" not in NAMED_REGIONS


def test_psd_construction_mean_vs_sum_counterexample():
    """A8: groupby.mean is not a regional total for multi-member nodes."""
    tab = psd_construction_table()
    usa = tab[tab["region"] == "USA"].iloc[0]
    ch = tab[tab["region"] == "China"].iloc[0]
    ea = tab[tab["region"] == "Eastern Africa"].iloc[0]
    eu = tab[tab["region"] == "EU-27"].iloc[0]
    assert usa["construction"] == "single_psd_row"
    assert abs(usa["host_over_psd_sum"] - 1.0) < 0.02
    assert eu["construction"] == "single_psd_row"
    assert eu["psd_members"] == "European Union"
    assert ch["construction"] == "groupby_mean_of_members"
    assert ch["n_psd_members"] == 2
    assert 0.45 < ch["host_over_psd_sum"] < 0.55
    assert ea["construction"] == "groupby_mean_of_members"
    assert ea["n_psd_members"] == 10
    assert 0.08 < ea["host_over_psd_sum"] < 0.12
    # Host H follows the mean, not the sum, for those two.
    assert abs(ch["model_H_annual"] - ch["psd_mean_production"]) < 1e-6
    assert abs(ea["model_H_annual"] - ea["psd_mean_production"]) < 1e-6


def test_harvest_reconstruction_matches_saved_ukraine():
    data = prepare_wheat(start_year=2003, end_year=2011)
    prod = model_production_annual(data, use_anomalies=True, start=2003, end=2011)
    ukr = prod[prod["region"] == "Ukraine"].set_index("year")["production"]
    saved = pd.read_csv(OUT_DEFAULT / "ukraine_harvest_amis.csv").set_index("year")
    for y in range(2003, 2012):
        assert abs(float(ukr.loc[y]) - float(saved.loc[y, "production"])) < 1e-9


def test_amis_moves_ukraine_2007_consumption_not_production():
    long = pd.read_csv(OUT_DEFAULT / "score_regional.csv")
    def val(sc, field, year=2007):
        q = long[(long["scenario"] == sc) & (long["region"] == "Ukraine")
                 & (long["field"] == field) & (long["year"] == year)]
        return float(q.iloc[0]["model"])
    assert abs(val("harvest", "production") - val("harvest_amis", "production")) < 1e-9
    assert val("harvest", "consumption") < 3.0
    assert val("harvest_amis", "consumption") > 8.0


def test_regional_note_labels_coverage_not_a_fit():
    text = (OUT_DEFAULT / "regional.md").read_text()
    assert "A8" in text
    assert "not fixed" in text.lower() or "Not fixed" in text
    assert "xmin" in text or "p_sto" in text
    assert "China" in text
    assert "Eastern Africa" in text
    assert "L1–L8" in text
    assert "α_foreign=10" in text or "alpha_foreign=10" in text or "Bai" in text


def test_regional_csv_china_half_eastern_africa_tenth():
    summ = pd.read_csv(OUT_DEFAULT / "score_regional_summary.csv")
    ha = summ[summ["scenario"] == "harvest_amis"]
    ch = ha[(ha["region"] == "China") & (ha["field"] == "production")].iloc[0]
    ea = ha[(ha["region"] == "Eastern Africa") & (ha["field"] == "production")].iloc[0]
    usa = ha[(ha["region"] == "USA") & (ha["field"] == "production")].iloc[0]
    assert 0.45 < ch["level_ratio"] < 0.55
    assert 0.08 < ea["level_ratio"] < 0.12
    assert 0.8 < usa["level_ratio"] < 1.3
    # Stocks are reported, not fitted.
    stk = ha[ha["field"] == "ending_stocks"]
    assert len(stk) == len(NAMED_REGIONS)
    assert np.isfinite(stk["mean_model"]).all()
