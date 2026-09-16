#!/usr/bin/env python3
"""Red team / optimisation, probe 7: how big is the scarcity signal itself?

Probe 6 REJECTED the hypothesis that the regulariser suppresses the
amplitude (shrinking it 25-fold moves the wheat 2007/08 hike from x1.22 to
x1.21). So the missing amplitude is not a regularisation artefact.

The remaining candidate: the scarcity ratio r_t that Gate 0 constructs is
simply too small to explain the observed price move at any elasticity a
referee would accept. This probe measures that directly.

For each crop, on the official matched leg:
  * the realised scarcity ratio r_t over the crisis peak window,
  * the pure inverse-demand price p0 r_t^eta it implies,
  * the eta that WOULD be required to reproduce the observed peak/base
    ratio from the model's own r_t, i.e.
        eta_req = log(observed hike) / log(r_peak / r_base),
  * and how much of the shipped model's realised hike comes from p^tr
    rather than p^scar, by decomposing p^star = omega p^tr + (1-omega) p^scar
    over the peak and base windows.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402

from sheaf.calendar24 import STEPS_PER_YEAR  # noqa: E402
from sheaf.data_usda import load_price_series_monthly  # noqa: E402

sys.path.insert(0, str(ROOT / "scripts" / "scratch"))
from redteam_opt_03_exporter_foc import _hike  # noqa: E402
import redteam_opt_04_foc_diagnosis as m4  # noqa: E402

OUT = ROOT / "diagnostics" / "gate0_prep" / "redteam" / "optimisation"
OUT.mkdir(parents=True, exist_ok=True)
CROPS = ("wheat", "maize", "rice")
WINDOWS = {"2007/08": (2006, 6, 2008, 3), "2010/11": (2009, 6, 2011, 2)}


def _steps(prep, y, m, half=1):
    """steps covering month m of year y, +/- `half` months (as _hike does)."""
    out = []
    for dm in range(-half, half + 1):
        mm, yy = m + dm, y
        if mm < 1:
            mm, yy = mm + 12, yy - 1
        if mm > 12:
            mm, yy = mm - 12, yy + 1
        t0 = (yy - prep.start_year) * STEPS_PER_YEAR + (mm - 1) * 2
        out += [t0, t0 + 1]
    return [t for t in out if 0 <= t < prep.H.shape[1]]


def main():
    obs_all = load_price_series_monthly(deflated=True)
    rows = []
    for crop in CROPS:
        obs = obs_all[(obs_all.year >= 2006) & (obs_all.year <= 2011)][
            ["year", "month", crop]].rename(columns={crop: "obs_price"})
        prep, tw, cfg = m4.build(crop, use_amis=True, use_shocks=True,
                                 use_demand=False, law="ask")
        out = m4.go(prep, tw, cfg)
        eta = prep.params.inv_eta
        w = prep.params.trade_w
        # reconstruct r_t from the recorded p_scar (strip the kappa wedge is
        # not possible post hoc, so recompute r from F and F_twin directly)
        F = out["free"]
        Ft = np.asarray(prep.free_twin, float)
        sw = float(max(prep.safety.sum(), 1.0))
        f = 0.05 * sw + np.maximum(0.0, -np.minimum(F, Ft))
        r = (Ft + f) / (F + f)
        print(f"\n=== {crop} (eta={eta:.2f}, omega={w:.2f}, "
              f"p0={prep.p0:.1f} $/t) ===")
        print(f"  r_t over the whole scored window: mean {r.mean():.3f}  "
              f"min {r.min():.3f}  max {r.max():.3f}")
        print(f"  implied pure inverse-demand price p0 r^eta: "
              f"max {prep.p0 * r.max()**eta:.1f} $/t "
              f"(= {r.max()**eta:.2f} x p0)")
        for lab, (y0, m0, y1, m1) in WINDOWS.items():
            b = _steps(prep, y0, m0)
            k = _steps(prep, y1, m1)
            r_b, r_k = float(r[b].mean()), float(r[k].mean())
            obs_h = _hike(obs, "obs_price", y0, m0, y1, m1)
            scar_h = (r_k / r_b) ** eta
            # eta needed to get the observed hike from the model's own r
            eta_req = (np.log(obs_h) / np.log(r_k / r_b)
                       if r_k / r_b > 1.0001 else np.inf)
            ps_b = float(np.mean(out["p_scar"][b]))
            ps_k = float(np.mean(out["p_scar"][k]))
            pt_b = float(np.mean(out["p_trade"][b]))
            pt_k = float(np.mean(out["p_trade"][k]))
            mod_h = _hike(
                pd.DataFrame(dict(
                    year=[0], month=[0])), "x", 0, 0, 0, 0) if False else None
            # contribution decomposition of the change in p_star
            d_star = (w * (pt_k - pt_b) + (1 - w) * (ps_k - ps_b))
            share_tr = (w * (pt_k - pt_b) / d_star) if abs(d_star) > 1e-9 else np.nan
            print(f"  {lab}: observed x{obs_h:.2f}")
            print(f"      r  base {r_b:.3f} -> peak {r_k:.3f}  "
                  f"(x{r_k/r_b:.3f});  scarcity-only price x{scar_h:.3f}")
            print(f"      eta required to match observed from this r: "
                  f"{eta_req:.2f}   (shipped eta = {eta:.2f})")
            print(f"      p^scar {ps_b:.0f} -> {ps_k:.0f} $/t ;  "
                  f"p^tr {pt_b:.0f} -> {pt_k:.0f} $/t")
            print(f"      share of the move in p* carried by p^tr: "
                  f"{share_tr:.0%}  (omega = {w:.0%})")
            rows.append(dict(
                crop=crop, window=lab, eta=eta, omega=w, p0=prep.p0,
                obs_hike=obs_h, r_base=r_b, r_peak=r_k,
                r_ratio=r_k / r_b, scarcity_only_hike=scar_h,
                eta_required=eta_req, pscar_base=ps_b, pscar_peak=ps_k,
                ptrade_base=pt_b, ptrade_peak=pt_k,
                share_of_move_from_ptrade=share_tr))
    pd.DataFrame(rows).to_csv(OUT / "scarcity_signal.csv", index=False)
    print(f"\nwrote {OUT/'scarcity_signal.csv'}")


if __name__ == "__main__":
    main()
