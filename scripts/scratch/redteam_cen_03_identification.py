#!/usr/bin/env python3
"""Red-team census, experiment 3: are any two Gate 0 parameters unidentified?

The question the sitting really posed is not "how many knobs are there" but
"how many can the scored data tell apart". We answer it directly.

Method. Build the Jacobian J of the nine official metrics (3 crops x
{corr, 2007/08 hike, 2010/11 hike}) with respect to eighteen continuous
CropParams fields, by central differences at a relative step h. Metrics are
scaled by the same "material change" thresholds used in experiment 2
(0.05 for a correlation, 10% of the baseline value for a hike ratio) so the
nine rows are commensurate. Then:

  * ||J_k||       - how much parameter k moves the scored output at all;
  * |cos(J_j,J_k)|- whether two parameters move it in the SAME direction,
                    in which case only their combination is identified;
  * SVD of J      - how many independent directions the nine metrics can
                    actually resolve.

A high |cos| between two parameters with non-negligible norms is a genuine
identification failure: the data cannot distinguish them, and the honest
response is to fix one. Robustness to the step size is checked by running
the whole thing at two values of h.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from redteam_cen_00_harness import (
    CROPS,
    METRIC_NAMES,
    ROOT,
    baseline_scores,
    metric_vector,
    score_full_leg,
)
from sheaf.dynamic_crop import default_crop_params

OUT = ROOT / "diagnostics" / "gate0_prep" / "redteam" / "census"

PARAMS = (
    "elast", "stu_target", "max_stu", "rebuild_lambda", "warehouse_lambda",
    "inv_eta", "smooth", "trade_w", "unmet_kappa", "block_kappa",
    "ask_alpha", "ask_target_fill", "ask_comp_elast", "ask_beta",
    "ask_rival", "foresight_phi", "harvest_pulse_frac", "residual_subst",
)

# Fields that must stay inside [0, 1] for the map to make sense.
UNIT_INTERVAL = {"smooth", "trade_w", "foresight_phi", "ask_target_fill",
                 "residual_subst", "rebuild_lambda", "warehouse_lambda",
                 "harvest_pulse_frac", "stu_target", "max_stu"}

COLLINEAR_TOL = 0.95
NEGLIGIBLE = 0.10          # scaled-metric norm below this = no real effect


def metric_scale(base: dict) -> np.ndarray:
    """Per-metric 'material change' unit, matching experiment 2."""
    s = []
    for c in CROPS:
        s.append(0.05)                      # correlation
        s.append(0.10 * abs(base[c]["h0708"]))
        s.append(0.10 * abs(base[c]["h1011"]))
    return np.asarray(s, float)


def perturbed_value(field: str, crop: str, h: float, sign: int) -> float:
    v = float(getattr(default_crop_params(crop), field))
    out = v * (1.0 + sign * h)
    if field in UNIT_INTERVAL:
        out = float(np.clip(out, 1e-4, 0.999))
    return out


def jacobian(h: float, base: dict, scale: np.ndarray):
    """Scaled central-difference Jacobian, shape (9 metrics, n params)."""
    cols, steps = [], []
    for field in PARAMS:
        plus, minus = {}, {}
        for crop in CROPS:
            plus[crop] = score_full_leg(
                crop, **{field: perturbed_value(field, crop, h, +1)})
            minus[crop] = score_full_leg(
                crop, **{field: perturbed_value(field, crop, h, -1)})
        d = (metric_vector(plus) - metric_vector(minus)) / scale
        cols.append(d)
        steps.append(h)
        print(f"    {field:20s} ||dJ|| = {np.linalg.norm(d):7.3f}")
    return np.column_stack(cols), np.asarray(steps)


def analyse(J: np.ndarray, h: float) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    norms = np.linalg.norm(J, axis=0)
    U = J / np.where(norms > 1e-12, norms, 1.0)
    C = np.abs(U.T @ U)

    pairs = []
    for i in range(len(PARAMS)):
        for j in range(i + 1, len(PARAMS)):
            pairs.append(dict(
                h=h, a=PARAMS[i], b=PARAMS[j], abs_cos=float(C[i, j]),
                norm_a=float(norms[i]), norm_b=float(norms[j]),
                both_active=bool(norms[i] > NEGLIGIBLE
                                 and norms[j] > NEGLIGIBLE),
                sign=int(np.sign((U[:, i] @ U[:, j]) or 1.0)),
            ))
    pair_df = pd.DataFrame(pairs)

    sv = np.linalg.svd(J, compute_uv=False)
    frac = np.cumsum(sv ** 2) / np.sum(sv ** 2)
    info = dict(
        h=h,
        singular_values=[float(s) for s in sv],
        cond_number=float(sv[0] / sv[-1]) if sv[-1] > 0 else float("inf"),
        n_dirs_99pct=int(np.searchsorted(frac, 0.99) + 1),
        n_dirs_above_1pct_of_top=int((sv > 0.01 * sv[0]).sum()),
        n_params=len(PARAMS),
        n_metrics=J.shape[0],
    )
    norm_df = pd.DataFrame(dict(h=h, param=list(PARAMS), norm=norms))
    return pair_df, norm_df, info


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    base = baseline_scores()
    scale = metric_scale(base)
    print("Metric scaling (one unit = one 'material' change):")
    for nm, s in zip(METRIC_NAMES, scale):
        print(f"  {nm:14s} {s:.4f}")

    all_pairs, all_norms, infos, jacs = [], [], [], {}
    for h in (0.10, 0.20):
        print(f"\n=== Jacobian at relative step h = {h:.2f} ===")
        J, _ = jacobian(h, base, scale)
        jacs[h] = J
        p, n, info = analyse(J, h)
        all_pairs.append(p)
        all_norms.append(n)
        infos.append(info)
        print(f"  singular values: "
              f"{', '.join(f'{s:.2f}' for s in info['singular_values'][:8])} ...")
        print(f"  condition number {info['cond_number']:.3g}; "
              f"{info['n_dirs_99pct']} of {len(PARAMS)} directions carry 99% "
              f"of the response")

    pair_df = pd.concat(all_pairs, ignore_index=True)
    norm_df = pd.concat(all_norms, ignore_index=True)
    pair_df.to_csv(OUT / "cen03_pairs.csv", index=False)
    norm_df.to_csv(OUT / "cen03_norms.csv", index=False)
    np.savetxt(OUT / "cen03_jacobian_h010.csv", jacs[0.10], delimiter=",")

    print("\n=== Sensitivity magnitude (scaled), h = 0.10 ===")
    n0 = norm_df[norm_df.h == 0.10].sort_values("norm", ascending=False)
    for _, r in n0.iterrows():
        tag = "  <- negligible" if r.norm < NEGLIGIBLE else ""
        print(f"  {r.param:20s} {r.norm:8.3f}{tag}")

    print(f"\n=== Near-collinear pairs (|cos| >= {COLLINEAR_TOL}, both active) ===")
    hits = {}
    for h in (0.10, 0.20):
        sub = pair_df[(pair_df.h == h) & pair_df.both_active
                      & (pair_df.abs_cos >= COLLINEAR_TOL)]
        hits[h] = {(r.a, r.b): float(r.abs_cos) for _, r in sub.iterrows()}
    stable = sorted(set(hits[0.10]) & set(hits[0.20]))
    if not stable:
        print("  none at either step size")
    for a, b in stable:
        i, j = PARAMS.index(a), PARAMS.index(b)
        sgn = "+" if float(jacs[0.10][:, i] @ jacs[0.10][:, j]) > 0 else "-"
        print(f"  {a:20s} ~ {b:20s} |cos| = {hits[0.10][(a, b)]:.4f} "
              f"(h=0.10), {hits[0.20][(a, b)]:.4f} (h=0.20), same sign: {sgn}")

    print("\n=== Highest |cos| overall among active pairs, h = 0.10 ===")
    top = (pair_df[(pair_df.h == 0.10) & pair_df.both_active]
           .sort_values("abs_cos", ascending=False).head(12))
    for _, r in top.iterrows():
        print(f"  {r.a:20s} ~ {r.b:20s} |cos| = {r.abs_cos:.4f}  "
              f"(norms {r.norm_a:.2f} / {r.norm_b:.2f})")

    (OUT / "cen03_summary.json").write_text(json.dumps(dict(
        params=list(PARAMS), metrics=list(METRIC_NAMES),
        collinear_tol=COLLINEAR_TOL, negligible_norm=NEGLIGIBLE,
        stable_collinear_pairs=[
            dict(a=a, b=b, abs_cos_h010=hits[0.10][(a, b)],
                 abs_cos_h020=hits[0.20][(a, b)]) for a, b in stable],
        svd=infos,
        norms_h010={r.param: float(r.norm) for _, r in n0.iterrows()},
    ), indent=2))
    print(f"\nwrote {OUT / 'cen03_pairs.csv'}")


if __name__ == "__main__":
    main()
