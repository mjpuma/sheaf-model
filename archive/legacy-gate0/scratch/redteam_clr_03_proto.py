#!/usr/bin/env python3
"""Tasks 2/4 — decompose the glut asymmetry, then prototype and score the
two candidate cheap upgrades.

Part A. Asymmetry decomposition at s = +/-10%: switch off, one at a time,
        (i) the one-sided truncation of the unmet-demand channel and
        (ii) the physical capacity drawdown. Also counts how often the
        offer-price lower clip 0.45*p0 binds on the surplus leg, which is
        the third candidate cause.
Part B. Official-P1 rescore (harvest + AMIS + mean flex) of
        (a) the two-sided unmet channel and
        (b) an explicit excess-demand (tatonnement) term added to p*.

Writes clr_asym_decomp.csv, clr_proto_scores.csv, clr_askclip.csv.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import redteam_clr_lib as L  # noqa: E402

from sheaf.calendar24 import STEPS_PER_YEAR  # noqa: E402
from sheaf.dynamic_crop import prepare_crop_run  # noqa: E402

OUT = Path(__file__).resolve().parents[2] / "diagnostics/gate0_prep/redteam/clearing"
OUT.mkdir(parents=True, exist_ok=True)

TAIL = slice(2 * STEPS_PER_YEAR, None)
S = 0.10

VARIANTS = {
    "shipped":            dict(unmet_mode="onesided"),
    "unmet_twosided":     dict(unmet_mode="twosided"),
    "no_drawdown":        dict(unmet_mode="onesided", drawdown_lambda=0.0),
    "twosided+no_drawdn": dict(unmet_mode="twosided", drawdown_lambda=0.0),
}


def main() -> None:
    dec, clip = [], []
    for crop in L.CROPS:
        prep = prepare_crop_run(crop, use_amis=False, use_shocks=False,
                                use_demand=False, use_industrial=False)
        for vname, var in VARIANTS.items():
            base = L.simulate_instrumented(prep, harvest=prep.H * (1 - 1e-6), **var)
            up = L.simulate_instrumented(prep, harvest=prep.H * (1 + S), **var)
            dn = L.simulate_instrumented(prep, harvest=prep.H * (1 - S), **var)
            lp0 = float(np.mean(np.log(base["price"][TAIL])))
            lpu = float(np.mean(np.log(up["price"][TAIL])))
            lpd = float(np.mean(np.log(dn["price"][TAIL])))
            dec.append(dict(
                crop=crop, variant=vname, s=S,
                resp_shortfall_pct=100 * (np.exp(lpd - lp0) - 1),
                resp_surplus_pct=100 * (np.exp(lpu - lp0) - 1),
                asym_ratio=abs(lpd - lp0) / max(abs(lpu - lp0), 1e-12),
                drawdown_base=float(np.mean(base["drawdown"][TAIL])),
                drawdown_surplus=float(np.mean(up["drawdown"][TAIL])),
                drawdown_shortfall=float(np.mean(dn["drawdown"][TAIL])),
                free_surplus=float(np.mean(up["free"][TAIL])),
                free_base=float(np.mean(base["free"][TAIL])),
                free_shortfall=float(np.mean(dn["free"][TAIL])),
                ratio_surplus=float(np.mean(up["ratio"][TAIL])),
                ratio_shortfall=float(np.mean(dn["ratio"][TAIL])),
                p_trade_surplus=float(np.mean(up["p_trade"][TAIL])),
                p_trade_shortfall=float(np.mean(dn["p_trade"][TAIL])),
            ))
            if vname == "shipped":
                lo = 0.45 * prep.p0
                for leg, r in (("surplus", up), ("base", base), ("shortfall", dn)):
                    a = r["mat"]["ask"]
                    clip.append(dict(
                        crop=crop, leg=leg, p0=prep.p0, ask_floor=lo,
                        frac_exporter_steps_at_floor=float(
                            np.mean(np.isclose(a, lo, rtol=1e-9))),
                        mean_ask=float(a.mean()),
                        mean_p_trade=float(np.mean(r["p_trade"][TAIL])),
                    ))
        print(f"  decomp {crop}: done")

    pd.DataFrame(dec).to_csv(OUT / "clr_asym_decomp.csv", index=False)
    pd.DataFrame(clip).to_csv(OUT / "clr_askclip.csv", index=False)
    print("\n=== asymmetry decomposition, s = +/-10% ===")
    print(pd.DataFrame(dec)[[
        "crop", "variant", "resp_shortfall_pct", "resp_surplus_pct",
        "asym_ratio", "drawdown_surplus", "drawdown_shortfall",
        "free_surplus", "free_base"]].to_string(index=False))
    print("\n=== offer-price floor incidence ===")
    print(pd.DataFrame(clip).to_string(index=False))

    # ---------------- Part B: official-P1 rescore ----------------
    rows = []
    for crop in L.CROPS:
        prep = prepare_crop_run(crop, use_amis=True, use_shocks=True,
                                use_demand=False)
        obs07, obs10 = L.OBS_HIKES[crop]
        cases = [("shipped", dict()),
                 ("unmet_twosided", dict(unmet_mode="twosided")),
                 ("no_drawdown", dict(drawdown_lambda=0.0))]
        for k in (0.25, 0.5, 1.0, 2.0, 5.0):
            cases.append((f"tatonnement_k{k}", dict(tat_kappa=k)))
        for k in (0.5, 2.0):
            cases.append((f"twosided+tat_k{k}",
                          dict(unmet_mode="twosided", tat_kappa=k)))
        for name, var in cases:
            t0 = time.perf_counter()
            r = L.simulate_instrumented(prep, record_trade=False, **var)
            dt = time.perf_counter() - t0
            sc = L.score_price(r["price"], crop)
            rows.append(dict(
                crop=crop, variant=name, corr=sc["corr"],
                h0708=sc["h0708"], h1011=sc["h1011"],
                obs_h0708=obs07, obs_h1011=obs10,
                err0708=abs(sc["h0708"] - obs07), err1011=abs(sc["h1011"] - obs10),
                mean_price=float(r["price"].mean()), runtime_s=dt,
            ))
        print(f"  score {crop}: done")

    df = pd.DataFrame(rows)
    df.to_csv(OUT / "clr_proto_scores.csv", index=False)
    print("\n=== official P1 rescore (harvest + AMIS + mean flex) ===")
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
