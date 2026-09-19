"""R3: host p_w is the XI-weighted lagged D.7 offer mix. Not a 2006 pin."""
from __future__ import annotations

from pathlib import Path

import numpy as np

from sheaf.agrimate.equations import inverse_demand
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


def test_reported_pw_equals_lagged_xi_weighted_offers_not_world_d7():
    params = wheat_params()
    data = prepare_wheat(start_year=2006, end_year=2006, params=params)
    res = run_agrimate(
        data=data, params=params,
        use_anomalies=True, use_restrictions=True,
        start_year=2006, end_year=2006,
    )
    assert res.offer is not None and res.xi_ship is not None
    replay = lagged_offer_index(res.xi_ship, res.offer, params.n_del)
    assert np.allclose(res.price_index, replay, rtol=0.0, atol=1e-12)
    assert np.allclose(res.price_usd, res.price_index * data.p0)

    n_r, T = res.xi_ship.shape
    q_i = [np.zeros(n_r) for _ in range(params.n_del)]
    single = np.empty(T)
    prev = 1.0
    star = max(float(data.XI_world), 1e-8)
    for t in range(T):
        q_i.append(res.xi_ship[:, t].copy())
        xi_lag = q_i.pop(0)
        vol = float(np.sum(xi_lag))
        if vol > 1e-12:
            single[t] = float(inverse_demand(
                vol / star, params.alpha_i, params.lam_demand,
                params.demand_arg_floor))
        else:
            single[t] = prev if t else 1.0
        prev = single[t]
    assert np.max(np.abs(res.price_index - single)) > 0.05
    # Not a 2006 pin: year-mean index is not reset to 1.
    assert abs(float(res.price_index.mean()) - 1.0) > 0.05


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
    dispatch = (ROOT / "diagnostics" / "GATE0_REPRO_DISPATCH.md").read_text()
    assert "Last completed: R3" in dispatch
    assert "Next paste: R10" in dispatch
