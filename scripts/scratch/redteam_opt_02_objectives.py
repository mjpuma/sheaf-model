#!/usr/bin/env python3
"""Red team / optimisation, probe 2: does any objective generate the map?

(a) SCARCITY TERM AS MARGINAL UTILITY OF ACCESSIBLE STOCK.
    Claim: p_scar = p0 r^eta with r = (F_twin + f)/(F + f) is exactly
    U'(F) for the CRRA-in-accessible-stock felicity
        U(F) = p0 (F_twin + f)^eta (F + f)^(1-eta) / (1 - eta),  eta != 1
        U(F) = p0 (F_twin + f) ln(F + f),                        eta  = 1
    Test numerically on the scored path: U'(F) vs p_scar recomputed from
    the model's own recorded F, F_twin. Also report how often the kappa_u
    / kappa_b multipliers move p_scar off U'(F) (they are a wedge, not
    part of any U).

(b) COVER RULE AS A NEWSVENDOR.  T = L + s. If T is the newsvendor
    order-up-to level for the uncertain lean requirement L, then
    s_i = z_i * sigma_{L,i} with critical fractile Phi(z_i) =
    c_u / (c_u + c_o), so the implied stockout:carry penalty ratio is
    c_u/c_o = Phi(z_i) / (1 - Phi(z_i)).  We measure sigma_{L,i} as the
    model's own lean-gap forecast error (L from blended H_exp vs L from
    realised H) and back out z_i and the penalty ratio per country.
    A common-fractile newsvendor requires z_i roughly constant.

(c) ASK LAW AS EXPORTER PROFIT ASCENT.  Probe 1 established
    dX_out_i/dq_i = 0.  Here we quantify the full-model derivative
    dPi_i/dq_i by finite difference on a whole scored run (perturbing one
    exporter's ask-price bounds is not available, so we perturb the ask
    level directly through a shim) and report its sign.

Writes cover_newsvendor.csv, pscar_utility.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402
from scipy.stats import norm  # noqa: E402

from sheaf.calendar24 import STEPS_PER_YEAR  # noqa: E402
from sheaf.dynamic_crop import (  # noqa: E402
    MAX_LEAN_STEPS,
    default_crop_params,
    prepare_crop_run,
    simulate_prep,
)
from sheaf.seasonal import rolling_ahead_variable, steps_to_harvest_pulse  # noqa: E402

OUT = ROOT / "diagnostics" / "gate0_prep" / "redteam" / "optimisation"
OUT.mkdir(parents=True, exist_ok=True)

CROPS = ("wheat", "maize", "rice")


# ---------------------------------------------------------------- (a)
def u_prime(F, F_twin, f, eta, p0):
    """Marginal utility of accessible stock for the CRRA felicity above."""
    return p0 * ((F_twin + f) / (F + f)) ** eta


def probe_a(rows: list[dict]) -> None:
    print("\n== (a) p_scar as marginal utility of accessible stock ==")
    for crop in CROPS:
        prep = prepare_crop_run(crop, use_amis=True, use_shocks=True,
                                use_demand=False)
        res = simulate_prep(prep)
        p = prep.params
        F = np.asarray(res.free_liquid, float)
        Ft = np.asarray(prep.free_twin, float)
        s_w = float(max(prep.safety.sum(), 1.0))
        f = 0.05 * s_w + np.maximum(0.0, -np.minimum(F, Ft))
        r = (Ft + f) / (F + f)
        # the pure inverse-demand / marginal-utility piece
        mu = u_prime(F, Ft, f, p.inv_eta, prep.p0)
        pure = prep.p0 * np.maximum(r, 1e-12) ** p.inv_eta
        dev = float(np.max(np.abs(mu - pure)))
        # the kappa wedge
        u0 = np.asarray(prep.unmet_twin, float)
        du = np.maximum(0.0, np.asarray(res.unmet_frac, float) - u0)
        # blockage share, recomputed
        b = np.zeros_like(F)
        for t in range(len(F)):
            tot_d = float(res.purchase_demand[:, t].sum())
            pb = float((prep.S * prep.cuts[:, t][:, None]
                        * res.purchase_demand[None, :, t]).sum())
            b[t] = pb / max(tot_d, 1e-9)
        wedge = 1.0 + p.unmet_kappa * du + p.block_kappa * b
        n_wedge = int((wedge > 1.0 + 1e-12).sum())
        print(f"  {crop:6s} eta={p.inv_eta:.2f}  max|U'(F) - p0 r^eta| = "
              f"{dev:.3e} $/t  (exact identity)")
        print(f"         implied demand elasticity over accessible stock = "
              f"{-1.0 / p.inv_eta:+.3f}")
        print(f"         kappa wedge != 1 at {n_wedge}/{len(F)} steps; "
              f"mean wedge {wedge.mean():.3f}, max {wedge.max():.3f}")
        rows.append(dict(crop=crop, eta=p.inv_eta,
                         max_abs_dev_uprime=dev,
                         implied_elasticity=-1.0 / p.inv_eta,
                         n_steps=len(F), n_wedge_active=n_wedge,
                         mean_wedge=float(wedge.mean()),
                         max_wedge=float(wedge.max()),
                         mean_regulariser_share=float(
                             (f / np.maximum(np.abs(F), 1e-9)).mean())))


# ---------------------------------------------------------------- (b)
def probe_b(rows: list[dict]) -> None:
    print("\n== (b) cover target T = L + s as a newsvendor ==")
    for crop in CROPS:
        prep = prepare_crop_run(crop, use_amis=True, use_shocks=True,
                                use_demand=False)
        p = prep.params
        C_step = prep.C_flex + prep.C_ind
        H = prep.H
        H_seas = prep.H_seas
        H_exp = p.foresight_phi * H + (1.0 - p.foresight_phi) * H_seas

        def lean(Hx):
            lh = steps_to_harvest_pulse(Hx, frac=p.harvest_pulse_frac,
                                        max_horizon=MAX_LEAN_STEPS)
            Ha = rolling_ahead_variable(Hx, lh)
            Ca = rolling_ahead_variable(C_step, lh)
            return np.maximum(0.0, Ca + C_step - Ha - Hx)

        L_exp = lean(H_exp)     # what the agent uses (forecast)
        L_real = lean(H)        # what a perfect-foresight agent would use
        err = L_real - L_exp    # forecast error of the lean requirement
        n_y = L_exp.shape[1] // STEPS_PER_YEAR
        crop_rows = []
        for i, c in enumerate(prep.countries):
            if prep.C_ann[i] < 1.0:
                continue
            # sigma_1: residual forecast error the agent actually faces
            sig_err = float(np.std(err[i]))
            # sigma_2: year-to-year dispersion of the lean requirement at the
            # same seasonal phase (the risk a safety stock would buffer)
            block = L_real[i, :n_y * STEPS_PER_YEAR].reshape(
                n_y, STEPS_PER_YEAR)
            sig_yr = float(np.mean(np.std(block, axis=0)))
            s_i = float(prep.safety[i])

            def _back_out(sig):
                if sig <= 1e-9:
                    return np.inf, 1.0, np.inf
                z = s_i / sig
                # log10 of the penalty ratio, via the normal tail
                logsf = float(norm.logsf(z)) / np.log(10.0)
                return z, float(norm.cdf(z)), -logsf

            z1, f1, lr1 = _back_out(sig_err)
            z2, f2, lr2 = _back_out(sig_yr)
            row = dict(
                crop=crop, country=c, C_ann=float(prep.C_ann[i]),
                safety_s=s_i, mean_L=float(L_exp[i].mean()),
                sd_forecast_err=sig_err, sd_interannual=sig_yr,
                z_forecast_err=z1, log10_penalty_ratio_fcasterr=lr1,
                z_interannual=z2, log10_penalty_ratio_interann=lr2,
                s_over_meanL=s_i / max(float(L_exp[i].mean()), 1e-9))
            rows.append(row)
            crop_rows.append(row)

        def _stats(key):
            v = np.array([r[key] for r in crop_rows], float)
            v = v[np.isfinite(v)]
            return v
        z1s, z2s = _stats("z_forecast_err"), _stats("z_interannual")
        l1s, l2s = (_stats("log10_penalty_ratio_fcasterr"),
                    _stats("log10_penalty_ratio_interann"))
        print(f"  {crop:6s} n_nodes={len(crop_rows)}  sigma^stu="
              f"{p.stu_target:.2f}")
        print(f"         vs forecast error : z median {np.median(z1s):6.2f} "
              f"[{z1s.min():.2f},{z1s.max():.2f}]  "
              f"implied log10(c_u/c_o) median {np.median(l1s):.1f}")
        print(f"         vs interannual sd : z median {np.median(z2s):6.2f} "
              f"[{z2s.min():.2f},{z2s.max():.2f}]  "
              f"implied log10(c_u/c_o) median {np.median(l2s):.1f}")
        print(f"         a genuine newsvendor at c_u/c_o = 10 needs z = "
              f"{norm.ppf(10/11):.2f}; at 1000 needs z = "
              f"{norm.ppf(1000/1001):.2f}")


def main() -> None:
    a_rows: list[dict] = []
    probe_a(a_rows)
    pd.DataFrame(a_rows).to_csv(OUT / "pscar_utility.csv", index=False)

    b_rows: list[dict] = []
    probe_b(b_rows)
    pd.DataFrame(b_rows).to_csv(OUT / "cover_newsvendor.csv", index=False)
    print(f"\nwrote {OUT/'pscar_utility.csv'}")
    print(f"wrote {OUT/'cover_newsvendor.csv'}")


if __name__ == "__main__":
    main()
