#!/usr/bin/env python3
"""Task 2 — glut vs shortfall asymmetry, measured off the calm pin.

Controlled experiment. Baseline is the twin-matched configuration (no AMIS,
no harvest anomaly, mean flex demand, no industrial) with harvest scaled by
(1 - 1e-6) so the run leaves the calm regime and shares a price law with the
treatments -- the repository's own `assert_amis_raises_price` trick. All
treatments are harvest * (1 + s); the s>0 and s<0 legs are therefore
symmetric perturbations of the *same* unpinned baseline, which isolates the
genuine asymmetry from the pinning artifact catalogued in
diagnostics/gate0_prep/a2/A2C_MONOTONICITY.md.

Writes clr_glut_permanent.csv, clr_glut_transient.csv, clr_glut_channels.csv.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import redteam_clr_lib as L  # noqa: E402

from sheaf.calendar24 import STEPS_PER_YEAR  # noqa: E402
from sheaf.dynamic_crop import prepare_crop_run  # noqa: E402

OUT = Path(__file__).resolve().parents[2] / "diagnostics/gate0_prep/redteam/clearing"
OUT.mkdir(parents=True, exist_ok=True)

SHOCKS = (0.005, 0.01, 0.02, 0.05, 0.10, 0.20)
TAIL = slice(2 * STEPS_PER_YEAR, None)   # last 4 years of the 6-year window


def run_leg(prep, mult, **variant):
    return L.simulate_instrumented(prep, harvest=prep.H * mult, **variant)


def main() -> None:
    perm, trans, chan = [], [], []
    for crop in L.CROPS:
        prep = prepare_crop_run(crop, use_amis=False, use_shocks=False,
                                use_demand=False, use_industrial=False)
        for mode in ("onesided", "twosided"):
            var = dict(unmet_mode=mode)
            base = run_leg(prep, 1.0 - 1e-6, **var)
            lp0 = float(np.mean(np.log(base["price"][TAIL])))
            chan.append(dict(crop=crop, mode=mode, s=0.0, log_p=lp0,
                             mean_p=float(np.mean(base["price"][TAIL])),
                             mean_drawdown=float(np.mean(base["drawdown"][TAIL])),
                             mean_u_anom=float(np.mean(base["u_anom"][TAIL])),
                             mean_ratio=float(np.mean(base["ratio"][TAIL])),
                             mean_p_trade=float(np.mean(base["p_trade"][TAIL])),
                             mean_free=float(np.mean(base["free"][TAIL])),
                             mean_excess_cap=float(np.mean(base["excess_above_cap"][TAIL])),
                             ))
            legs = {}
            for s in SHOCKS:
                for sgn in (+1, -1):
                    r = run_leg(prep, 1.0 + sgn * s, **var)
                    legs[sgn * s] = r
                    chan.append(dict(
                        crop=crop, mode=mode, s=sgn * s,
                        log_p=float(np.mean(np.log(r["price"][TAIL]))),
                        mean_p=float(np.mean(r["price"][TAIL])),
                        mean_drawdown=float(np.mean(r["drawdown"][TAIL])),
                        mean_u_anom=float(np.mean(r["u_anom"][TAIL])),
                        mean_ratio=float(np.mean(r["ratio"][TAIL])),
                        mean_p_trade=float(np.mean(r["p_trade"][TAIL])),
                        mean_free=float(np.mean(r["free"][TAIL])),
                        mean_excess_cap=float(np.mean(r["excess_above_cap"][TAIL])),
                    ))
            for s in SHOCKS:
                lp_dn = float(np.mean(np.log(legs[-s]["price"][TAIL])))  # shortfall
                lp_up = float(np.mean(np.log(legs[+s]["price"][TAIL])))  # surplus
                # price flexibility dlog p / dlog H, one-sided each way
                flex_short = (lp_dn - lp0) / np.log(1.0 - s)   # >0 if p up on cut
                flex_surp = (lp_up - lp0) / np.log(1.0 + s)
                perm.append(dict(
                    crop=crop, mode=mode, s=s,
                    logp_base=lp0, logp_shortfall=lp_dn, logp_surplus=lp_up,
                    resp_shortfall_pct=100 * (np.exp(lp_dn - lp0) - 1),
                    resp_surplus_pct=100 * (np.exp(lp_up - lp0) - 1),
                    flex_shortfall=flex_short, flex_surplus=flex_surp,
                    asym_ratio=abs(lp_dn - lp0) / max(abs(lp_up - lp0), 1e-12),
                    surplus_lowers_price=bool(lp_up < lp0),
                ))

        # ---- transient: shock year 2 only (closer to a real anomaly) ----
        var = dict(unmet_mode="onesided")
        H0 = prep.H * (1.0 - 1e-6)
        base = L.simulate_instrumented(prep, harvest=H0, **var)
        w = slice(1 * STEPS_PER_YEAR, 2 * STEPS_PER_YEAR + 12)
        for mode in ("onesided", "twosided"):
            var = dict(unmet_mode=mode)
            base = L.simulate_instrumented(prep, harvest=H0, **var)
            for s in SHOCKS:
                out = {}
                for sgn in (+1, -1):
                    Hs = prep.H.copy() * (1.0 - 1e-6)
                    Hs[:, STEPS_PER_YEAR:2 * STEPS_PER_YEAR] *= (1.0 + sgn * s)
                    out[sgn] = L.simulate_instrumented(prep, harvest=Hs, **var)
                trans.append(dict(
                    crop=crop, mode=mode, s=s,
                    peak_base=float(base["price"][w].max()),
                    peak_shortfall_ratio=float(out[-1]["price"][w].max()
                                               / base["price"][w].max()),
                    trough_surplus_ratio=float(out[+1]["price"][w].min()
                                               / base["price"][w].min()),
                    mean_shortfall_ratio=float(out[-1]["price"][w].mean()
                                               / base["price"][w].mean()),
                    mean_surplus_ratio=float(out[+1]["price"][w].mean()
                                             / base["price"][w].mean()),
                ))
        print(f"  {crop}: done")

    for name, rows in (("clr_glut_permanent", perm),
                       ("clr_glut_transient", trans),
                       ("clr_glut_channels", chan)):
        df = pd.DataFrame(rows)
        df.to_csv(OUT / f"{name}.csv", index=False)

    p = pd.read_csv(OUT / "clr_glut_permanent.csv")
    print("\n=== permanent uniform shock, mean price over last 4 years ===")
    print(p[["crop", "mode", "s", "resp_shortfall_pct", "resp_surplus_pct",
             "flex_shortfall", "flex_surplus", "asym_ratio",
             "surplus_lowers_price"]].to_string(index=False))
    t = pd.read_csv(OUT / "clr_glut_transient.csv")
    print("\n=== transient (year-2) shock ===")
    print(t.to_string(index=False))


if __name__ == "__main__":
    main()
