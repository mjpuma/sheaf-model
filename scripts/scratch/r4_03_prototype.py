#!/usr/bin/env python3
"""R4 task 2 — prototype an Agrimate-style share-dependent price impact.

Channel (Agrimate Eq. D.7/D.9 + Eq. 5): supplier r's offer price carries the
Cournot markup implied by an isoelastic inverse demand with inverse-elasticity
alpha evaluated at r's share of total international supply.  SHEAF's price law
is already calibrated with the *baseline* markup embedded, so what is grafted
on is the deviation from the calm-twin share:

    log mu_r(t) = alpha * ( s_r(t) - s*_r(t) )          [mp_form="exp"]
    mu_r(t)     = (1 - alpha s*_r) / (1 - alpha s_r)    [mp_form="lerner"]

with s_r = offers_r / sum offers and s*_r the same quantity on the calm twin.
mu == 1 on the twin by construction, so the twin identity is preserved.

THE KEY TEST: with the channel on, can ask_rival go to 0?
"""
from __future__ import annotations

import itertools
from pathlib import Path

import numpy as np
import pandas as pd

import r4_lib as L
from sheaf.dynamic_crop import default_crop_params, prepare_crop_run

OUT = Path(__file__).resolve().parents[2] / "diagnostics" / "redteam" / "r4"
OUT.mkdir(parents=True, exist_ok=True)

ALPHA_I = {"wheat": 3.2, "maize": 2.7, "rice": 2.2}   # Agrimate defaults


def run_case(crop, alloc_mode="shipped", mp_alpha=0.0, mp_form="exp",
             ask_rival=None, with_asserts=False) -> dict:
    ov = {} if ask_rival is None else dict(ask_rival=float(ask_rival))
    prep = prepare_crop_run(crop, use_amis=True, use_shocks=True,
                            use_demand=False, **ov)
    tw = L.retwin(prep, alloc_mode=alloc_mode)
    out = L.run_prep(prep, twin=tw, alloc_mode=alloc_mode,
                     mp_alpha=mp_alpha, mp_form=mp_form)
    s = L.score(out["price"], crop)
    mk = out["markup"]
    off = out["offers"]
    act = off > 1e-9
    row = dict(crop=crop, alloc=alloc_mode, mp_alpha=mp_alpha,
               mp_form=mp_form if mp_alpha > 0 else "-",
               ask_rival=(prep.params.ask_rival), **s,
               obs_h0708=L.OBS_HIKES[crop][0], obs_h1011=L.OBS_HIKES[crop][1],
               markup_p95=float(np.quantile(mk[act], 0.95)) if act.any() else 1.0,
               markup_max=float(mk[act].max()) if act.any() else 1.0,
               markup_min=float(mk[act].min()) if act.any() else 1.0,
               twin_consistent=float(np.max(np.abs(
                   tw["free_twin"] - prep.free_twin))))
    if with_asserts:
        row.update(L.asserts(crop, alloc_mode=alloc_mode, overrides=ov,
                             mp_alpha=mp_alpha, mp_form=mp_form))
    return row


def main():
    cases = []
    # ---- ladder --------------------------------------------------------
    ladder = [
        ("shipped", 0.0, 0.8), ("shipped", 0.0, 0.0),
        ("shipped", None, 0.0), ("shipped", None, 0.8),
        ("source", 0.0, 0.8), ("source", 0.0, 0.0),
        ("source", None, 0.0), ("source", None, 0.8),
        ("agrimate", 0.0, 0.8), ("agrimate", 0.0, 0.0),
        ("agrimate", None, 0.0),
    ]
    for crop in L.CROPS:
        inv_eta = default_crop_params(crop).inv_eta
        for alloc, a, rv in ladder:
            alpha = ALPHA_I[crop] if a is None else a
            cases.append(run_case(crop, alloc, alpha, "exp", rv))
        # existing-parameter variant: alpha = inv_eta (zero new parameters)
        cases.append(run_case(crop, "shipped", inv_eta, "exp", 0.0))
        cases.append(run_case(crop, "source", inv_eta, "exp", 0.0))
    df = pd.DataFrame(cases)
    df.to_csv(OUT / "r4_03_ladder.csv", index=False)
    pd.set_option("display.width", 240)
    cols = ["crop", "alloc", "mp_alpha", "ask_rival", "corr", "h0708",
            "h1011", "obs_h0708", "obs_h1011", "markup_p95", "markup_max",
            "twin_consistent"]
    print("=== prototype ladder ===")
    print(df[cols].to_string(index=False, float_format=lambda x: f"{x:.3f}"))

    # ---- alpha sweep at ask_rival = 0 ---------------------------------
    sweep = []
    for crop in L.CROPS:
        for alloc in ("shipped", "source"):
            for a in (0.0, 0.5, 1.0, 2.0, 3.0, 4.0, 6.0, 8.0, 12.0):
                sweep.append(run_case(crop, alloc, a, "exp", 0.0))
    sw = pd.DataFrame(sweep)
    sw.to_csv(OUT / "r4_03_alpha_sweep.csv", index=False)
    print("\n=== alpha sweep at ask_rival = 0 ===")
    print(sw[cols].to_string(index=False, float_format=lambda x: f"{x:.3f}"))
    print(f"\nwrote CSVs to {OUT}")


if __name__ == "__main__":
    main()
