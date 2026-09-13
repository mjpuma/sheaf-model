#!/usr/bin/env python3
"""A5 — channel ablation of the Gate 0 crisis spine (read-only measurement).

For each crop in (wheat, maize, rice) and each single-parameter ablation,
re-score the official `full` and `shocks` legs against the deflated Pink
Sheet, and re-run the four robustness assertions of `sheaf/dynamic_crop.py`
(L900-1013) with the same override applied.

Nothing here proposes new defaults. `default_crop_params` is untouched;
every ablation is a keyword override passed through `run_crop_dynamics`.

Metric helpers (`_corr`, `_hike`) are imported from
`scripts/score_subannual_crop.py` so the numbers are directly comparable to
`diagnostics/gate0_*_report.md`.

Outputs
-------
diagnostics/gate0_prep/a5/ablation_grid.csv
diagnostics/gate0_prep/a5/assert_detail.csv
"""
from __future__ import annotations

import sys
import traceback
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from sheaf.calendar24 import STEPS_PER_YEAR  # noqa: E402
from sheaf.data_usda import load_price_series_monthly  # noqa: E402
from sheaf.dynamic_crop import (  # noqa: E402
    _EXPORTER_WINDOWS,
    result_to_monthly,
    run_crop_dynamics,
)
from score_subannual_crop import _corr, _hike  # noqa: E402

OUT = ROOT / "diagnostics" / "gate0_prep" / "a5"

CROPS = ("wheat", "maize", "rice")
START, END = 2006, 2011

# Ablations: (label, override dict). Field names verified against
# CropParams (sheaf/dynamic_crop.py L77-138).
ABLATIONS = (
    ("baseline", {}),
    ("trade_w=1.0", dict(trade_w=1.0)),
    ("trade_w=0.0", dict(trade_w=0.0)),
    ("ask_rival=0.0", dict(ask_rival=0.0)),
    ("block_kappa=0.0", dict(block_kappa=0.0)),
    ("unmet_kappa=0.0", dict(unmet_kappa=0.0)),
    ("foresight_phi=0.0", dict(foresight_phi=0.0)),
    ("foresight_phi=1.0", dict(foresight_phi=1.0)),
    ("ask_alpha=0.0", dict(ask_alpha=0.0)),
    ("rebuild_lambda=0.0", dict(rebuild_lambda=0.0)),
)

WINDOWS = (
    ("hike_2007_08", 2006, 6, 2008, 3),
    ("hike_2010_11", 2009, 6, 2011, 2),
)


# ---------------------------------------------------------------------------
# Assertion re-implementations.
#
# The library assertions call run_crop_dynamics() with no override hook, so
# they cannot be parameterised. These are transcriptions of
# sheaf/dynamic_crop.py L900-1013 with (a) the identical windows, floors and
# tolerances and (b) a `**ov` pass-through, returning a bool + the underlying
# statistic instead of raising. The two shock-free runs each assertion needs
# ("tau" = AMIS only, "base" = nothing on, both use_industrial=False) are
# built once per (crop, ablation) and shared, which is what the library does
# too, just without the caching.
# ---------------------------------------------------------------------------

def _assert_runs(crop: str, ov: dict):
    tau = run_crop_dynamics(crop, start_year=START, end_year=END,
                            use_amis=True, use_shocks=False,
                            use_demand=False, use_industrial=False, **ov)
    base = run_crop_dynamics(crop, start_year=START, end_year=END,
                             use_amis=False, use_shocks=False,
                             use_demand=False, use_industrial=False, **ov)
    return tau, base


def a_twin_identity(base, tol_price=0.02, tol_free=1.0):
    p0 = float(base.price[0])
    tail = base.price[STEPS_PER_YEAR:]
    rel = float(np.max(np.abs(tail - p0)) / max(p0, 1.0))
    free_err = float(np.max(np.abs(base.free_liquid - base.free_twin)))
    ok = (rel <= tol_price) and (free_err <= tol_free)
    return ok, dict(twin_price_drift=rel, twin_free_err=free_err)


def a_amis_raises_price(crop, tau, base):
    if crop == "wheat":
        y0, m0, y1, m1, floor = 2010, 8, 2010, 12, 0.05
    elif crop == "rice":
        y0, m0, y1, m1, floor = 2008, 1, 2008, 6, 0.05
    elif crop == "maize":
        y0, m0, y1, m1, floor = 2007, 5, 2008, 6, 0.0
    else:
        return True, {}
    t0 = (y0 - tau.start_year) * STEPS_PER_YEAR + (m0 - 1) * 2
    t1 = (y1 - tau.start_year) * STEPS_PER_YEAR + (m1 - 1) * 2 + 2
    p_tau = float(np.mean(tau.price[t0:t1]))
    p_base = float(np.mean(base.price[t0:t1]))
    lift = p_tau / max(p_base, 1e-9) - 1.0
    return lift >= floor, dict(amis_lift=lift, amis_lift_floor=floor,
                               p_tau=p_tau, p_base=p_base)


def a_no_spring_spike(base, max_ratio=1.25):
    m = result_to_monthly(base)
    spring = float(m[m.month.isin([3, 4])]["model_price"].mean())
    autumn = float(m[m.month.isin([9, 10])]["model_price"].mean())
    ratio = spring / max(autumn, 1e-9)
    return ratio <= max_ratio, dict(spring_autumn=ratio)


def a_amis_cuts_exports(crop, tau, base):
    max_offer_ratio = 0.20 if crop == "wheat" else 0.70
    max_ship_ratio = 0.85 if crop == "wheat" else 0.95
    country, y0, m0, y1, m1 = _EXPORTER_WINDOWS[crop]
    i = tau.countries.index(country)
    t0 = (y0 - tau.start_year) * STEPS_PER_YEAR + (m0 - 1) * 2
    t1 = (y1 - tau.start_year) * STEPS_PER_YEAR + (m1 - 1) * 2 + 2
    off_tau = float(np.mean(tau.offers[i, t0:t1]))
    off_base = float(np.mean(base.offers[i, t0:t1]))
    det = dict(offer_ratio=float("nan"), ship_ratio=float("nan"),
               offer_base=off_base)
    if off_base < 1e-6:
        return False, det  # library raises "pick a different window"
    off_ratio = off_tau / off_base
    det["offer_ratio"] = off_ratio
    ok = off_ratio <= max_offer_ratio
    exp_tau = float(np.mean(tau.exports[i, t0:t1]))
    exp_base = float(np.mean(base.exports[i, t0:t1]))
    ship_ratio = exp_tau / max(exp_base, 1e-9)
    det["ship_ratio"] = ship_ratio
    if crop == "wheat":
        ok = ok and (ship_ratio <= max_ship_ratio)
    return ok, det


# ---------------------------------------------------------------------------

def score_leg(res, obs, crop):
    m = result_to_monthly(res).merge(obs, on=["year", "month"], how="left")
    out = dict(corr=_corr(m.model_price, m.obs_price))
    for label, y0, mo0, y1, mo1 in WINDOWS:
        out[label] = _hike(m, "model_price", y0, mo0, y1, mo1)
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows, adet = [], []

    for crop in CROPS:
        obs_all = load_price_series_monthly(deflated=True)
        obs = obs_all[(obs_all.year >= START) & (obs_all.year <= END)][
            ["year", "month", crop]].rename(columns={crop: "obs_price"})
        obs_h = {lab: _hike(obs, "obs_price", y0, mo0, y1, mo1)
                 for lab, y0, mo0, y1, mo1 in WINDOWS}
        print(f"\n=== {crop} (observed: "
              + "  ".join(f"{k}×{v:.2f}" for k, v in obs_h.items()) + ") ===")

        for lab, ov in ABLATIONS:
            legs = {
                "full": run_crop_dynamics(
                    crop, start_year=START, end_year=END, use_amis=True,
                    use_shocks=True, use_demand=False, **ov),
                "shocks": run_crop_dynamics(
                    crop, start_year=START, end_year=END, use_amis=False,
                    use_shocks=True, use_demand=False, **ov),
            }
            tau, base = _assert_runs(crop, ov)
            ok_t, d_t = a_twin_identity(base)
            ok_p, d_p = a_amis_raises_price(crop, tau, base)
            ok_s, d_s = a_no_spring_spike(base)
            ok_e, d_e = a_amis_cuts_exports(crop, tau, base)
            det = dict(crop=crop, ablation=lab, **d_t, **d_p, **d_s, **d_e)
            adet.append(det)

            for leg, res in legs.items():
                sc = score_leg(res, obs, crop)
                rows.append(dict(
                    crop=crop, leg=leg, ablation=lab,
                    override=";".join(f"{k}={v}" for k, v in ov.items()) or "-",
                    **sc,
                    obs_hike_2007_08=obs_h["hike_2007_08"],
                    obs_hike_2010_11=obs_h["hike_2010_11"],
                    assert_twin_identity="PASS" if ok_t else "FAIL",
                    assert_amis_raises_price="PASS" if ok_p else "FAIL",
                    assert_no_spring_spike="PASS" if ok_s else "FAIL",
                    assert_amis_cuts_exports="PASS" if ok_e else "FAIL",
                    amis_lift=d_p.get("amis_lift", float("nan")),
                    offer_ratio=d_e.get("offer_ratio", float("nan")),
                    ship_ratio=d_e.get("ship_ratio", float("nan")),
                    spring_autumn=d_s.get("spring_autumn", float("nan")),
                    twin_price_drift=d_t.get("twin_price_drift", float("nan")),
                    twin_free_err=d_t.get("twin_free_err", float("nan")),
                ))
                print(f"  {lab:20s} {leg:6s} corr={sc['corr']:+.3f} "
                      f"h07={sc['hike_2007_08']:.2f} "
                      f"h10={sc['hike_2010_11']:.2f}  "
                      f"asserts={''.join('T' if o else 'F' for o in (ok_t, ok_p, ok_s, ok_e))}"
                      f" lift={d_p.get('amis_lift', float('nan')):+.4f}")

    grid = pd.DataFrame(rows)
    grid.to_csv(OUT / "ablation_grid.csv", index=False)
    pd.DataFrame(adet).to_csv(OUT / "assert_detail.csv", index=False)
    print(f"\nwrote {OUT / 'ablation_grid.csv'}")

    # ---- inert-parameter scan -------------------------------------------
    print("\n=== inert scan (max |Δ| vs baseline across all crops/legs) ===")
    keys = ["corr", "hike_2007_08", "hike_2010_11", "amis_lift",
            "offer_ratio", "ship_ratio", "spring_autumn", "twin_price_drift",
            "twin_free_err"]
    aflags = ["assert_twin_identity", "assert_amis_raises_price",
              "assert_no_spring_spike", "assert_amis_cuts_exports"]
    base_idx = grid[grid.ablation == "baseline"].set_index(["crop", "leg"])
    for lab, _ in ABLATIONS:
        if lab == "baseline":
            continue
        sub = grid[grid.ablation == lab].set_index(["crop", "leg"])
        worst, worst_k = 0.0, ""
        for k in keys:
            d = (sub[k] - base_idx[k]).abs().max()
            d = 0.0 if not np.isfinite(d) else float(d)
            if d > worst:
                worst, worst_k = d, k
        flag_diff = sum(int((sub[a] != base_idx[a]).any()) for a in aflags)
        print(f"  {lab:20s} max|Δ|={worst:.3e} on {worst_k or '(none)':16s} "
              f"assert_flips={flag_diff}")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
