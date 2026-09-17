"""P1: accounting identities (D.6, consumer clip, D.3 sales, finite)."""
from __future__ import annotations

import numpy as np

from sheaf.agrimate.accounting import (
    check_fulfill_sales_identities,
    check_result,
)
from sheaf.agrimate.equations import fulfill_sales, update_producer_storage
from sheaf.agrimate.model import run_agrimate
from sheaf.agrimate.params import wheat_params
from sheaf.agrimate.wheat_data import prepare_wheat


def test_fulfill_sales_never_exceeds_available_or_delta():
    rng = np.random.default_rng(3)
    for _ in range(200):
        planned_d, planned_i = rng.random() * 5, rng.random() * 5
        available = rng.random() * 4 - 0.5
        delta = rng.random()
        errs = check_fulfill_sales_identities(planned_d, planned_i, available, delta)
        assert not errs, errs
        sd, si = fulfill_sales(planned_d, planned_i, available, delta)
        assert sd >= -1e-12 and si >= -1e-12
        assert sd + si <= max(available, 0.0) + 1e-12


def test_producer_storage_matches_d6_clip():
    S = 1.2
    H, sd, si = 0.4, 0.3, 0.2
    got = update_producer_storage(S, H, sd, si, 0.0)
    assert abs(got - (S + H - sd - si)) < 1e-12
    # clip at 0
    assert update_producer_storage(0.0, 0.1, 0.4, 0.0, 0.0) == 0.0
    # δ>0: selling all of S+H can clip
    s1 = update_producer_storage(1.0, 0.0, 1.0, 0.0, 0.1)
    assert s1 == 0.0


def test_consumer_clip_identity_synthetic():
    S, inflow, want = 0.5, 0.2, 0.9
    cons = min(want, S + inflow)
    S2 = max(S + inflow - cons, 0.0)
    assert cons <= S + inflow + 1e-12
    assert abs(S2 - (S + inflow - cons)) < 1e-12


def test_2006_harvest_amis_path_identities():
    params = wheat_params()
    data = prepare_wheat(start_year=2006, end_year=2006, params=params)
    res = run_agrimate(
        data=data, params=params,
        use_anomalies=True, use_restrictions=True,
        start_year=2006, end_year=2006,
    )
    report = check_result(res, data, params)
    assert report.n_regions == 27
    assert report.n_steps == 24
    assert np.all(np.isfinite(res.price_index))
    assert res.harvest is not None and res.sold_domestic is not None
    assert report.ok, report_markdown_head(report)


def test_international_sales_are_not_echoed_to_the_exporter():
    """P2: arrive used to be own lagged XI. T* must send grain to importers."""
    from sheaf.agrimate.wheat_data import international_destination_shares
    params = wheat_params()
    data = prepare_wheat(start_year=2006, end_year=2006, params=params)
    dest = international_destination_shares(data.T_star)
    assert dest.shape == (27, 27)
    assert np.allclose(dest.sum(axis=1), 1.0)
    res = run_agrimate(
        data=data, params=params,
        use_anomalies=False, use_restrictions=False,
        start_year=2006, end_year=2006,
    )
    i_us = data.regions.index("USA")
    i_ea = data.regions.index("Eastern Africa")
    xi, sd, inf = res.xi_ship, res.sold_domestic, res.inflow
    echo = np.max(np.abs(inf[i_us, 2:] - sd[i_us, 2:] - xi[i_us, :-2]))
    assert echo > 0.1, "USA inflow still equals sold_d + own lagged XI"
    assert float(inf[i_ea].sum()) > float(sd[i_ea].sum()) + 0.5
    report = check_result(res, data, params)
    assert report.ok, report_markdown_head(report)


def report_markdown_head(report) -> str:
    if not report.violations:
        return "ok"
    v = report.violations[0]
    return (
        f"{len(report.violations)} violations; first {v.identity} "
        f"{v.region} t={v.step} expected={v.expected} got={v.got} {v.detail}"
    )


def test_existing_nash_smoke_still_there():
    from sheaf.agrimate.optimize import nash_ibr
    from sheaf.agrimate.params import AgrimateParams
    p = AgrimateParams(plan_maxiter=15, nash_max_iters=2)
    H = np.ones((2, 24))
    nash = nash_ibr(H, np.array([2.0, 2.0]), np.array([0.2, 0.2]), np.array([0.3, 0.3]), p)
    assert np.all(nash["xd"] >= -1e-10)
    assert np.all(np.isfinite(nash["sales"]))
