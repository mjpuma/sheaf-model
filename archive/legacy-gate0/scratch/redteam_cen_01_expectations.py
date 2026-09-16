#!/usr/bin/env python3
"""Red-team census, experiment 1: what expectation does Gate 0 actually form?

Three questions, in order.

1. Structure. Gate 0 forms H^exp = phi*H + (1-phi)*H_seas ONCE, as a single
   time-indexed array, before the loop (`_simulate_window` L576-586). The
   cover target then reads it forward with `rolling_ahead_variable`. So the
   belief held about the harvest at date t' does not depend on the date t at
   which it is held: there is no belief state and no revision. Agrimate's
   kernel (Suppl. Eq. D.1) is w_n over LEAD TIME n, so its beliefs do revise.
   We quantify the lead times Gate 0 actually reads, which is what decides
   whether the difference can matter.

2. Agrimate equivalence. Agrimate uses an accurate forecast to N_for = 6
   steps decaying to climatology by ~9 (w_n = 5% at n = N_for + tau_for/2).
   Over the lead times Gate 0 reads, that kernel is nearly w_n = 1, i.e.
   phi = 1. We score phi in {0, 0.55/0.50, 1} plus the exact w_n-weighted
   effective phi.

3. Adaptive alternative. The Potsdam instruction was backward-looking:
   stay near the previous belief unless new information arrives. We
   implement that literally as an EWMA over realised harvest anomalies and
   score it against the current forward-looking blend.

Read-only on sheaf/: the adaptive variant is injected by rewriting
`prep.H_seas` AFTER `prepare_crop_run` has built the calm twin, using the
identity H_seas' = (H_target - phi*H)/(1 - phi). `_simulate_window` uses
`H_seasonal` for nothing except the blend (verified below by an exact
round-trip), and the twin is already built, so nothing else moves.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from redteam_cen_00_harness import (
    CROPS,
    ROOT,
    baseline_scores,
    prepare_crop_run,
    score_prep,
)
from sheaf.calendar24 import STEPS_PER_YEAR
from sheaf.dynamic_crop import MAX_LEAN_STEPS, default_crop_params
from sheaf.seasonal import steps_to_harvest_pulse

OUT = ROOT / "diagnostics" / "gate0_prep" / "redteam" / "census"

# Agrimate Suppl. Tbl. D.1 defaults, at N_year = 24.
AGRIMATE_NFOR = 6.0
AGRIMATE_TAUFOR = 0.2 * 24.0


def agrimate_wn(n: np.ndarray) -> np.ndarray:
    """Agrimate Suppl. Eq. (D.1a): weight on the accurate forecast at lead n."""
    return 1.0 / (1.0 + np.exp((n - AGRIMATE_NFOR) / (0.17 * AGRIMATE_TAUFOR)))


def lead_time_profile(prep) -> dict:
    """Which lead times does the Gate 0 cover target actually read?"""
    p = prep.params
    H_exp = p.foresight_phi * prep.H + (1.0 - p.foresight_phi) * prep.H_seas
    lean_h = steps_to_harvest_pulse(
        H_exp, frac=p.harvest_pulse_frac, max_horizon=MAX_LEAN_STEPS)
    world = H_exp.sum(axis=0)
    T = world.shape[0]
    # Mass-weighted distribution of lead time n over the read window.
    mass = np.zeros(MAX_LEAN_STEPS + 1)
    for t in range(T):
        for n in range(1, int(lean_h[t]) + 1):
            if t + n < T:
                mass[n] += world[t + n]
    tot = float(mass.sum())
    share = mass / max(tot, 1e-12)
    n_idx = np.arange(MAX_LEAN_STEPS + 1, dtype=float)
    w = agrimate_wn(n_idx)
    return dict(
        lean_mean=float(lean_h.mean()),
        lean_median=float(np.median(lean_h)),
        lean_max=int(lean_h.max()),
        lean_p90=float(np.percentile(lean_h, 90)),
        share_lead_le6=float(share[1:7].sum()),
        share_lead_gt9=float(share[10:].sum()),
        # Effective Agrimate weight over the lead times Gate 0 reads.
        phi_agrimate_equiv=float((share[1:] * w[1:]).sum()
                                 / max(share[1:].sum(), 1e-12)),
    )


def adaptive_hexp(prep, theta: float) -> np.ndarray:
    """Backward-looking belief: EWMA over realised trailing-year anomalies.

    r_{i,t} = trailing 24-step realised harvest / trailing 24-step
    climatology; a_{i,t} = (1-theta) a_{i,t-1} + theta r_{i,t}, a_{i,0} = 1.
    Expected harvest is climatology scaled by that belief. Uses only
    information dated t or earlier, unlike the current blend.
    """
    H, H_seas = prep.H, prep.H_seas
    n, T = H.shape
    cH = np.concatenate([np.zeros((n, 1)), np.cumsum(H, axis=1)], axis=1)
    cS = np.concatenate([np.zeros((n, 1)), np.cumsum(H_seas, axis=1)], axis=1)
    out = np.zeros_like(H)
    a = np.ones(n)
    for t in range(T):
        t0 = max(0, t + 1 - STEPS_PER_YEAR)
        num = cH[:, t + 1] - cH[:, t0]
        den = cS[:, t + 1] - cS[:, t0]
        r = np.where(den > 1e-9, num / np.maximum(den, 1e-9), 1.0)
        a = (1.0 - theta) * a + theta * r
        out[:, t] = H_seas[:, t] * a
    return out


def _inject(prep, H_target: np.ndarray) -> None:
    """Set prep.H_seas so that the blend reproduces H_target exactly."""
    phi = prep.params.foresight_phi
    if abs(1.0 - phi) < 1e-12:
        raise ValueError("cannot invert the blend at phi = 1")
    prep.H_seas = (H_target - phi * prep.H) / (1.0 - phi)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    base = baseline_scores()
    rows, profile_rows = [], []

    for crop in CROPS:
        p = default_crop_params(crop)
        prep0 = prepare_crop_run(
            crop, start_year=2006, end_year=2011,
            use_amis=True, use_shocks=True, use_demand=False)
        prof = lead_time_profile(prep0)
        prof["crop"] = crop
        prof["phi_default"] = p.foresight_phi
        profile_rows.append(prof)

        b = base[crop]
        rows.append(dict(crop=crop, variant="baseline (phi blend)",
                         detail=f"phi={p.foresight_phi}", **b))

        # --- harness validation: the injection must be an exact no-op ------
        H_id = p.foresight_phi * prep0.H + (1.0 - p.foresight_phi) * prep0.H_seas
        s_id = score_prep(crop, mutate=lambda pr: _inject(pr, H_id))
        rows.append(dict(crop=crop, variant="injection round-trip",
                         detail="must equal baseline", **s_id))

        # --- lead-time variants -------------------------------------------
        for phi in (0.0, 0.25, 0.75, 1.0):
            s = {}
            s.update(score_prep(crop, foresight_phi=phi))
            rows.append(dict(crop=crop, variant="static blend",
                             detail=f"phi={phi:.2f}", **s))

        # Agrimate-equivalent phi over the lead times actually read.
        phi_ag = min(1.0, prof["phi_agrimate_equiv"])
        s = score_prep(crop, foresight_phi=phi_ag)
        rows.append(dict(crop=crop, variant="Agrimate w_n equivalent",
                         detail=f"phi={phi_ag:.3f}", **s))

        # --- adaptive, backward-looking ------------------------------------
        for theta in (0.05, 0.15, 0.35, 1.0):
            H_ad = adaptive_hexp(prep0, theta)
            s = score_prep(crop, mutate=lambda pr, H=H_ad: _inject(pr, H))
            rows.append(dict(crop=crop, variant="adaptive EWMA (backward)",
                             detail=f"theta={theta:.2f}", **s))

        # Perfect climatology belief = no information at all.
        s = score_prep(crop, mutate=lambda pr: _inject(pr, pr.H_seas))
        rows.append(dict(crop=crop, variant="climatology belief",
                         detail="H_exp = H_seas", **s))

    df = pd.DataFrame(rows)
    prof_df = pd.DataFrame(profile_rows)

    # Spread of each variant family away from baseline, per crop.
    base_v = df[df.variant == "baseline (phi blend)"].set_index("crop")
    df["d_corr"] = df.apply(
        lambda r: r["corr"] - base_v.loc[r.crop, "corr"], axis=1)
    df["d_h0708"] = df.apply(
        lambda r: r["h0708"] - base_v.loc[r.crop, "h0708"], axis=1)
    df["d_h1011"] = df.apply(
        lambda r: r["h1011"] - base_v.loc[r.crop, "h1011"], axis=1)
    df["max_abs_d"] = df[["d_corr", "d_h0708", "d_h1011"]].abs().max(axis=1)

    df.to_csv(OUT / "cen01_expectations.csv", index=False)
    prof_df.to_csv(OUT / "cen01_lead_profile.csv", index=False)

    pd.set_option("display.width", 200)
    print("\n=== Lead-time profile of the Gate 0 cover target ===")
    print(prof_df[["crop", "phi_default", "lean_mean", "lean_median",
                   "lean_p90", "lean_max", "share_lead_le6", "share_lead_gt9",
                   "phi_agrimate_equiv"]].to_string(index=False,
                                                    float_format="%.3f"))

    print("\n=== Scores by expectation variant ===")
    for crop in CROPS:
        sub = df[df.crop == crop]
        print(f"\n-- {crop} --")
        print(sub[["variant", "detail", "corr", "h0708", "h1011",
                   "max_abs_d"]].to_string(index=False, float_format="%.4f"))

    rt = df[df.variant == "injection round-trip"]
    print(f"\nInjection round-trip max |delta| = {rt.max_abs_d.max():.3e} "
          f"(must be ~0 for the harness to be valid)")

    fam = (df[df.variant != "injection round-trip"]
           .groupby("variant")["max_abs_d"].max())
    print("\n=== Worst-case move away from baseline, by variant family ===")
    print(fam.to_string(float_format="%.4f"))

    (OUT / "cen01_summary.json").write_text(json.dumps(dict(
        round_trip_max_abs=float(rt.max_abs_d.max()),
        worst_by_family={k: float(v) for k, v in fam.items()},
        lead_profile=prof_df.to_dict("records"),
    ), indent=2))
    print(f"\nwrote {OUT / 'cen01_expectations.csv'}")


if __name__ == "__main__":
    main()
