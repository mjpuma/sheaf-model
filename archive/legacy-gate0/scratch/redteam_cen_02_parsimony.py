#!/usr/bin/env python3
"""Red-team census, experiment 2: test the Potsdam parameter criticism.

Two claims were made at the sitting, and they are different claims.

(a) "Too many parameters." Testable as: can the crop-specific reduced-form
    values be replaced by one shared round number per parameter without
    materially moving the scored output? That removes degrees of freedom
    without changing any equation. We run a nested ladder from the current
    parameterisation down to a maximally pooled one and record the cost.

(b) "Hard bounds would give similar behaviour." Testable literally: the
    three partial-adjustment gains (rebuild lambda, warehouse lambda,
    price smoothing rho) each interpolate between "no response" and a hard
    bound. Setting lambda = 1, lambda_W = 1, rho = 0 replaces the smooth
    rule with the corresponding hard bound. We score each, and all four
    robustness assertions, at those corners.

Material change is declared in advance: |d corr| > 0.05 or |d hike| > 10%
of the baseline hike. Anything inside that is "the data cannot tell".
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from redteam_cen_00_harness import CROPS, OFFICIAL, ROOT, baseline_scores, score_full_leg
from sheaf.dynamic_crop import (
    assert_amis_cuts_exports,
    assert_amis_raises_price,
    assert_no_spring_spike,
    assert_twin_identity,
    default_crop_params,
)

OUT = ROOT / "diagnostics" / "gate0_prep" / "redteam" / "census"

CORR_TOL = 0.05
HIKE_REL_TOL = 0.10

# --- (a) the pooling ladder ------------------------------------------------
# Each rung adds restrictions to the rung above. `n_freed` counts distinct
# numeric values removed from the three-crop parameter set.
LADDER = [
    ("R0 current", {}, 0),
    # kappa_b is 4.0/4.0/4.5 and phi 0.55/0.50/0.55: two near-degenerate splits.
    ("R1 pool kappa_b, phi",
     dict(block_kappa=4.0, foresight_phi=0.55), 2),
    # eta 1.00/0.85/0.95 -> the unit-elastic structural value.
    ("R2 + eta = 1 (unit elastic)",
     dict(block_kappa=4.0, foresight_phi=0.55, inv_eta=1.0), 4),
    # omega 0.70/0.80/0.72 -> one shared weight.
    ("R3 + omega = 0.75 shared",
     dict(block_kappa=4.0, foresight_phi=0.55, inv_eta=1.0, trade_w=0.75), 6),
    # Capacity ceiling to one shared stock-to-use rather than 0.28/0.18/0.22.
    ("R4 + sigma_max = 0.22 shared",
     dict(block_kappa=4.0, foresight_phi=0.55, inv_eta=1.0, trade_w=0.75,
          max_stu=0.22), 8),
    # Safety stock to one shared stock-to-use rather than 0.20/0.16/0.18.
    ("R5 + sigma_stu = 0.18 shared",
     dict(block_kappa=4.0, foresight_phi=0.55, inv_eta=1.0, trade_w=0.75,
          max_stu=0.22, stu_target=0.18), 10),
    # Demand elasticity to one shared literature value, -0.20.
    ("R6 + epsilon = -0.20 shared",
     dict(block_kappa=4.0, foresight_phi=0.55, inv_eta=1.0, trade_w=0.75,
          max_stu=0.22, stu_target=0.18, elast=-0.20), 12),
]

# --- (b) smooth rule replaced by the corresponding hard bound --------------
HARD_BOUNDS = [
    ("lambda = 1 (import demand jumps to target)", dict(rebuild_lambda=1.0)),
    ("lambda_W = 1 (stock hard-clipped at capacity)", dict(warehouse_lambda=1.0)),
    ("rho = 0 (no price smoothing)", dict(smooth=0.0)),
    ("all three hard bounds together",
     dict(rebuild_lambda=1.0, warehouse_lambda=1.0, smooth=0.0)),
    # For contrast, the opposite corner of the same gains.
    ("lambda = 0 (no stock rebuilding)", dict(rebuild_lambda=0.0)),
    ("lambda_W = 0 (no capacity limit at all)", dict(warehouse_lambda=0.0)),
]

ASSERTS = (
    ("twin", assert_twin_identity),
    ("tau_up", assert_amis_raises_price),
    ("spring", assert_no_spring_spike),
    ("cut", assert_amis_cuts_exports),
)


def run_asserts(crop: str, **ov) -> tuple[str, str]:
    """Return (compact PASS/FAIL string, first failure message)."""
    bits, first = [], ""
    for name, fn in ASSERTS:
        try:
            fn(crop, **ov)
            bits.append(f"{name}:P")
        except AssertionError as exc:
            bits.append(f"{name}:F")
            if not first:
                first = f"{name}: {exc}"
    return " ".join(bits), first


def material(crop: str, base: dict, got: dict) -> bool:
    if abs(got["corr"] - base["corr"]) > CORR_TOL:
        return True
    for k in ("h0708", "h1011"):
        if abs(got[k] - base[k]) > HIKE_REL_TOL * abs(base[k]):
            return True
    return False


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    base = baseline_scores()

    print("=== Distinct numeric values in the three-crop parameter set ===")
    counts = {}
    for f in ("elast", "stu_target", "max_stu", "pipeline_max_steps",
              "rebuild_lambda", "warehouse_lambda", "inv_eta", "smooth",
              "trade_w", "unmet_kappa", "block_kappa", "ask_alpha",
              "ask_target_fill", "ask_comp_elast", "ask_beta", "ask_rival",
              "foresight_phi", "harvest_pulse_frac", "residual_subst",
              "seasonal_buffer_steps"):
        vals = tuple(getattr(default_crop_params(c), f) for c in CROPS)
        counts[f] = dict(values=vals, distinct=len(set(vals)))
    n_rows = len(counts)
    n_vals = sum(v["distinct"] for v in counts.values())
    for f, v in counts.items():
        flag = "  <- crop-specific" if v["distinct"] > 1 else ""
        print(f"  {f:22s} {str(v['values']):28s} distinct={v['distinct']}{flag}")
    print(f"  TOTAL: {n_rows} parameter rows, {n_vals} distinct numeric values")

    rows = []
    # ---------------- (a) pooling ladder ----------------------------------
    print("\n=== (a) Pooling ladder: can crop-specific values be shared? ===")
    for label, ov, freed in LADDER:
        for crop in CROPS:
            s = score_full_leg(crop, **ov) if ov else dict(base[crop])
            a_str, a_msg = run_asserts(crop, **ov) if ov else ("all:P", "")
            rows.append(dict(
                arm="pooling", variant=label, crop=crop, n_freed=freed,
                **s,
                d_corr=s["corr"] - base[crop]["corr"],
                d_h0708=s["h0708"] - base[crop]["h0708"],
                d_h1011=s["h1011"] - base[crop]["h1011"],
                material=material(crop, base[crop], s),
                asserts=a_str, assert_msg=a_msg))

    lad = pd.DataFrame([r for r in rows if r["arm"] == "pooling"])
    for label, _, freed in LADDER:
        sub = lad[lad.variant == label]
        worst = sub[["d_corr", "d_h0708", "d_h1011"]].abs().max().max()
        n_mat = int(sub.material.sum())
        n_fail = int(sub.asserts.str.contains("F").sum())
        print(f"  {label:32s} freed={freed:2d}  worst|d|={worst:.3f}  "
              f"material {n_mat}/3  assert-fail {n_fail}/3")

    # ---------------- (b) hard bounds -------------------------------------
    print("\n=== (b) Hard bounds in place of the partial-adjustment gains ===")
    for label, ov in HARD_BOUNDS:
        for crop in CROPS:
            try:
                s = score_full_leg(crop, **ov)
            except Exception as exc:                       # noqa: BLE001
                s = {"corr": float("nan"), "h0708": float("nan"),
                     "h1011": float("nan")}
                a_str, a_msg = "run:ERROR", str(exc)
            else:
                a_str, a_msg = run_asserts(crop, **ov)
            rows.append(dict(
                arm="hard_bound", variant=label, crop=crop, n_freed=1, **s,
                d_corr=s["corr"] - base[crop]["corr"],
                d_h0708=s["h0708"] - base[crop]["h0708"],
                d_h1011=s["h1011"] - base[crop]["h1011"],
                material=material(crop, base[crop], s),
                asserts=a_str, assert_msg=a_msg))
        sub = pd.DataFrame([r for r in rows
                            if r["arm"] == "hard_bound" and r["variant"] == label])
        worst = sub[["d_corr", "d_h0708", "d_h1011"]].abs().max().max()
        n_fail = int(sub.asserts.str.contains("F").sum())
        print(f"  {label:46s} worst|d|={worst:.3f}  "
              f"material {int(sub.material.sum())}/3  assert-fail {n_fail}/3")
        for _, r in sub.iterrows():
            print(f"      {r.crop:6s} corr {r['corr']:+.3f} "
                  f"07/08 x{r.h0708:.2f} 10/11 x{r.h1011:.2f}  [{r.asserts}]")

    df = pd.DataFrame(rows)
    df.to_csv(OUT / "cen02_parsimony.csv", index=False)

    deepest_ok = None
    for label, _, freed in LADDER:
        sub = lad[lad.variant == label]
        if not sub.material.any() and not sub.asserts.str.contains("F").any():
            deepest_ok = (label, freed)
    print("\n=== Verdict ===")
    if deepest_ok:
        print(f"  Deepest pooling rung with NO material score change and no "
              f"assertion failure: {deepest_ok[0]} "
              f"({deepest_ok[1]} of {n_vals} numeric values removed)")
    hb = df[df.arm == "hard_bound"]
    print(f"  Hard-bound corners that materially change the score: "
          f"{int(hb.material.sum())} of {len(hb)} crop-variant cells")

    (OUT / "cen02_summary.json").write_text(json.dumps(dict(
        n_param_rows=n_rows, n_distinct_values=n_vals,
        crop_specific=[f for f, v in counts.items() if v["distinct"] > 1],
        deepest_free_rung=deepest_ok,
        hard_bound_material_cells=int(hb.material.sum()),
        official=OFFICIAL,
    ), indent=2, default=str))
    print(f"\nwrote {OUT / 'cen02_parsimony.csv'}")


if __name__ == "__main__":
    main()
