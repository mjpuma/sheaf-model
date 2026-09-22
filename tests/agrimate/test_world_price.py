"""World price is the off-diagonal transaction index. Not a 2006 pin."""
from __future__ import annotations

from pathlib import Path

import numpy as np

from sheaf.agrimate.equations import foreign_transaction_index, inverse_demand
from sheaf.agrimate.fig4 import world_market_price_index
from sheaf.agrimate.model import (
    lagged_offer_index,
    run_agrimate,
    volume_weighted_offer_index,
)
from sheaf.agrimate.params import wheat_params
from sheaf.agrimate.wheat_data import prepare_wheat

ROOT = Path(__file__).resolve().parents[2]


def test_wheat_params_unchanged_by_world_price_recipe():
    p = wheat_params()
    assert p.alpha_i == 3.2
    assert p.p_sto_annual == 0.1
    assert p.xmin_share == 0.2
    assert p.zeta_penalty == 0.0
    assert p.n_for_months == 3
    assert p.n_del == 2
    assert p.lam_demand == 0.0


def test_volume_weighted_offer_index_is_xi_mix_not_single_d7():
    xi = np.array([8.0, 2.0])
    q_oth = np.array([1.0, 1.0])
    star = 10.0
    offers = np.array([
        float(inverse_demand((xi[r] + q_oth[r]) / star, 3.2, 0.0))
        for r in range(2)
    ])
    mix = volume_weighted_offer_index(xi, offers)
    expected = float(np.dot(xi, offers) / xi.sum())
    assert abs(mix - expected) < 1e-12
    single = float(inverse_demand(float(xi.sum()) / star, 3.2, 0.0))
    assert abs(single - 1.0) < 1e-12
    assert abs(mix - single) > 1.0
    assert volume_weighted_offer_index([0.0, 0.0], [2.0, 4.0], empty=1.5) == 1.5


def test_author_extractor_is_bilateral_off_diagonal_not_host_mix():
    """fig4.world_market_price_index drops the domestic diagonal of q·p.

    Host p_w mixes exporter-level D.7 offers with exporter XI. The two
    coincide only if every destination pays that offer and XI is already
    international. Destination-specific transaction prices diverge.
    """
    q = np.zeros((2, 2, 1))
    p = np.zeros((2, 2, 1))
    q[0, 0, 0] = 100.0  # domestic, dropped by the author extractor
    p[0, 0, 0] = 9.0
    q[0, 1, 0] = 10.0
    p[0, 1, 0] = 2.0
    q[1, 0, 0] = 5.0
    p[1, 0, 0] = 4.0
    wm = world_market_price_index(q, p)
    assert abs(wm[0] - (10 * 2 + 5 * 4) / 15) < 1e-12
    xi = np.array([10.0, 5.0])
    same_offer = volume_weighted_offer_index(xi, np.array([2.0, 4.0]))
    assert abs(same_offer - wm[0]) < 1e-12
    other_offer = volume_weighted_offer_index(xi, np.array([3.0, 4.0]))
    assert abs(other_offer - wm[0]) > 0.1


def test_reported_pw_equals_foreign_transactions_not_lagged_offers():
    params = wheat_params()
    data = prepare_wheat(start_year=2006, end_year=2006, params=params)
    res = run_agrimate(
        data=data, params=params,
        use_anomalies=True, use_restrictions=True,
        start_year=2006, end_year=2006,
    )
    assert res.tx_quantity is not None and res.tx_price is not None
    wm = world_market_price_index(res.tx_quantity, res.tx_price)
    prev = 1.0
    expect = np.empty_like(res.price_index)
    for t in range(expect.size):
        if np.isfinite(wm[t]):
            step = foreign_transaction_index(
                res.tx_quantity[:, :, t], res.tx_price[:, :, t], prev)
            assert abs(step - float(wm[t])) < 1e-8
            expect[t] = step
        else:
            expect[t] = prev if t else 1.0
        prev = expect[t]
    assert np.allclose(res.price_index, expect, rtol=0.0, atol=1e-12)
    assert np.allclose(res.price_usd, res.price_index * data.p0)
    replay = lagged_offer_index(res.xi_ship, res.offer, params.n_del)
    assert np.max(np.abs(res.price_index - replay)) > 0.05
    # Not a 2006 pin: year-mean index is not reset to 1.
    assert abs(float(res.price_index.mean()) - 1.0) > 0.05
    vw = res.to_monthly_price()
    eq = res.to_monthly_price_equal()
    assert vw.shape == eq.shape
    # Live months are the transaction basket, not the equal-weight mean.
    assert np.max(np.abs(vw - eq)) > 1.0
    from sheaf.agrimate.equations import monthly_transaction_index
    expect = monthly_transaction_index(res.tx_quantity, res.tx_price) * data.p0
    assert np.allclose(vw, expect, rtol=0.0, atol=1e-8)


def test_author_plot_wm_price_timeseries_not_in_tree():
    jl = []
    for base in (ROOT, Path("/opt"), Path("/workspace")):
        for rel in ("agrimate", "vendor/agrimate", "src/agrimate"):
            d = base / rel
            if d.is_dir():
                jl.extend(d.rglob("*.jl"))
    jl.extend((ROOT / "sheaf" / "agrimate").glob("*.jl"))
    assert not any(p.name == "plot.jl" for p in jl)
    assert not any(
        "plot_wm_price_timeseries" in p.read_text(errors="ignore") for p in jl)
    note = (ROOT / "diagnostics" / "gate0_agrimate" / "world_price.md").read_text()
    assert "14022004" in note
    assert "plot_wm_price_timeseries" in note
    assert "not in" in note.lower() or "absent" in note.lower()
    assert "Do not pin" in note or "not pinned" in note.lower()
    assert "wheat_params()" in note
