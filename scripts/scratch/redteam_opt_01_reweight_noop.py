#!/usr/bin/env python3
"""Red team / optimisation, probe 1.

Claim under test (dynamics.tex eq:reweight): "Preferred destination shares
are reweighted toward low offer prices",
    A~_ij,t  \propto  A_ij (p0 / q_i,t-1)^gamma,   sum_j A~_ij = 1.

Implementation: sheaf/dynamic_crop.py::_ask_reweight_dest (L503-509).

Algebraic prediction: the reweight multiplies ROW i of A by the scalar
rel_i = (p0/q_i)^gamma and then renormalises each row to sum 1. Since A's
rows already sum to 1 (load_trade_shares row-normalises), the scalar
cancels exactly and A_eff == A identically, for every q. If so the
Armington price-competition channel gamma (= CropParams.ask_comp_elast)
has NO effect on anything, and there is no channel by which an exporter's
own offer price changes its own sales.

Tests
  T1  A_eff == A to machine precision for random asks (all three crops).
  T2  Full scored runs are BIT-IDENTICAL across gamma in {0, 0.25, 1.25,
      5.0, 50.0} on price, offers, exports, stocks, asks.
  T3  d X_out_i / d q_i == 0 exactly: perturb one exporter's ask inside a
      hand-rolled single clearing step and measure own-shipment response.

Writes diagnostics/gate0_prep/redteam/optimisation/reweight_noop.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

from sheaf.dynamic_crop import (  # noqa: E402
    _ask_reweight_dest,
    _bilateral_clear,
    default_crop_params,
    load_trade_shares,
    run_crop_dynamics,
)

OUT = ROOT / "diagnostics" / "gate0_prep" / "redteam" / "optimisation"
OUT.mkdir(parents=True, exist_ok=True)

CROPS = ("wheat", "maize", "rice")
GAMMAS = (0.0, 0.25, 1.25, 5.0, 50.0)


def _countries() -> list[str]:
    from sheaf.calibration import DATA
    return [d["name"] for d in DATA] + ["RestOfWorld"]


def t1_identity(rows: list[dict]) -> None:
    print("\n== T1: A_eff vs A ==")
    rng = np.random.default_rng(0)
    countries = _countries()
    for crop in CROPS:
        A, S = load_trade_shares(crop, countries)
        p = default_crop_params(crop)
        worst = 0.0
        for _ in range(200):
            ask = np.exp(rng.uniform(np.log(0.45), np.log(2.8), size=len(countries)))
            ask = ask * 250.0
            for g in GAMMAS:
                A_eff = _ask_reweight_dest(A, ask, 250.0, gamma=g)
                worst = max(worst, float(np.max(np.abs(A_eff - A))))
        rowsum = A.sum(axis=1)
        n_exporters = int((rowsum > 1e-12).sum())
        print(f"  {crop:6s} max|A_eff - A| over 200 asks x 5 gammas = {worst:.3e}"
              f"   (rows summing to 1: {n_exporters}/{len(countries)})")
        rows.append(dict(crop=crop, test="T1_max_abs_dev", value=worst,
                         n_rows_unit_sum=n_exporters, n_nodes=len(countries)))


def t2_score_invariance(rows: list[dict]) -> None:
    print("\n== T2: bit-identical scored runs across gamma ==")
    for crop in CROPS:
        base = run_crop_dynamics(crop, use_amis=True, use_shocks=True,
                                 use_demand=False, ask_comp_elast=1.25)
        for g in GAMMAS:
            r = run_crop_dynamics(crop, use_amis=True, use_shocks=True,
                                  use_demand=False, ask_comp_elast=g)
            d = dict(
                price=float(np.max(np.abs(r.price - base.price))),
                offers=float(np.max(np.abs(r.offers - base.offers))),
                exports=float(np.max(np.abs(r.exports - base.exports))),
                stock=float(np.max(np.abs(r.stock - base.stock))),
                ask=float(np.max(np.abs(r.ask - base.ask))),
                trade=float(np.max(np.abs(r.trade - base.trade))),
            )
            ident = all(v == 0.0 for v in d.values())
            print(f"  {crop:6s} gamma={g:5.2f}  identical={ident}  "
                  f"max|dp|={d['price']:.3e}  max|dtrade|={d['trade']:.3e}")
            rows.append(dict(crop=crop, test="T2_gamma_invariance", gamma=g,
                             identical=ident, **{f"max_abs_d_{k}": v
                                                 for k, v in d.items()}))


def t3_own_price_derivative(rows: list[dict]) -> None:
    """Own-price elasticity of own shipments inside one clearing step."""
    print("\n== T3: d X_out_i / d q_i inside one clearing step ==")
    countries = _countries()
    rng = np.random.default_rng(1)
    for crop in CROPS:
        A, S = load_trade_shares(crop, countries)
        p = default_crop_params(crop)
        n = len(countries)
        # a plausible state: offers on exporters, demand on importers
        offers = np.where(A.sum(axis=1) > 1e-12,
                          rng.uniform(0.5, 5.0, size=n), 0.0)
        demand = np.where(S.sum(axis=0) > 1e-12,
                          rng.uniform(0.5, 5.0, size=n), 0.0)
        ask = np.full(n, 250.0)
        exporters = [i for i in range(n) if offers[i] > 1e-9]
        worst = 0.0
        worst_c = None
        for i in exporters:
            for bump in (0.5, 2.0):
                a2 = ask.copy()
                a2[i] *= bump
                Ae0 = _ask_reweight_dest(A, ask, 250.0, gamma=p.ask_comp_elast)
                Ae1 = _ask_reweight_dest(A, a2, 250.0, gamma=p.ask_comp_elast)
                s0, _, _ = _bilateral_clear(offers, demand, Ae0, S,
                                            subst=p.residual_subst)
                s1, _, _ = _bilateral_clear(offers, demand, Ae1, S,
                                            subst=p.residual_subst)
                d = abs(float(s1[i] - s0[i]))
                if d > worst:
                    worst, worst_c = d, countries[i]
        print(f"  {crop:6s} n_exporters={len(exporters)}  "
              f"max|dX_out_i| over +/-100% own-ask shocks = {worst:.3e} MMT "
              f"({worst_c})")
        rows.append(dict(crop=crop, test="T3_own_price_dXdq", value=worst,
                         n_exporters=len(exporters)))


def main() -> None:
    rows: list[dict] = []
    t1_identity(rows)
    t3_own_price_derivative(rows)
    t2_score_invariance(rows)
    df = pd.DataFrame(rows)
    path = OUT / "reweight_noop.csv"
    df.to_csv(path, index=False)
    print(f"\nwrote {path}")


if __name__ == "__main__":
    main()
