#!/usr/bin/env python3
"""Red-team Gate 1 substitution. Print classified probes; exit 0 always.

Does not retune CropParams / ρ. Does not run the export game.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sheaf.calibration import GRAINS, RHO
from sheaf.dynamic_coupled import (
    COUPLED_GRAINS,
    cross_price_eta,
    run_coupled_dynamics,
)
from sheaf.dynamic_crop import default_crop_params, run_crop_dynamics


def _maxrel(a, b):
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    return float(np.max(np.abs(a - b) / np.maximum(np.abs(b), 1.0)))


def _maxabs(a, b):
    return float(np.max(np.abs(np.asarray(a) - np.asarray(b))))


def probe_eta():
    print("\n=== 1. η construction ===")
    eta = cross_price_eta(0.6)
    elast = np.array([default_crop_params(g).elast for g in COUPLED_GRAINS])
    print("GRAINS", GRAINS, "COUPLED", COUPLED_GRAINS)
    print("elast", elast)
    print("RHO\n", RHO)
    print("eta σ=0.6\n", eta)
    hand = np.diag(elast)
    idx = {g: i for i, g in enumerate(GRAINS)}
    for a, ga in enumerate(COUPLED_GRAINS):
        for b, gb in enumerate(COUPLED_GRAINS):
            if a == b:
                continue
            hand[a, b] = 0.6 * RHO[idx[ga], idx[gb]] * abs(elast[a])
    print("hand-minus-code maxabs", _maxabs(eta, hand))
    print("maize←wheat", eta[2, 0], "wheat←maize", eta[0, 2],
          "maize_answers_more", eta[2, 0] > eta[0, 2])
    print("row sums (not 0 => not homogeneous)", eta.sum(axis=1))
    eta0 = cross_price_eta(0.0)
    print("σ=0 off-diag maxabs", float(np.max(np.abs(eta0 - np.diag(np.diag(eta0))))))


def probe_identity():
    print("\n=== 2. σ=0 identity vs solo (step-level) ===")
    coupled = run_coupled_dynamics(subst_scale=0.0, use_demand=False)
    fields = ("price", "stock", "consumption", "offers", "purchase_demand",
              "ask", "free_liquid", "exports")
    for g in COUPLED_GRAINS:
        solo = run_crop_dynamics(g, use_amis=True, use_shocks=True,
                                 use_demand=False)
        c = coupled.by_crop[g]
        print(f"  {g} countries match", c.countries == solo.countries)
        for f in fields:
            a, b = getattr(c, f), getattr(solo, f)
            print(f"    {f:16s} maxabs={_maxabs(a, b):.3e}  maxrel={_maxrel(a, b):.3e}")


def probe_calm():
    print("\n=== 3. calm twin at σ=0.6 (no AMIS, no shocks, no industrial) ===")
    for s in (0.0, 0.6):
        run = run_coupled_dynamics(
            subst_scale=s, use_amis=False, use_shocks=False,
            use_demand=False, use_industrial=False)
        for g in COUPLED_GRAINS:
            p = run.by_crop[g].price
            p0 = float(run.by_crop[g].params and run.by_crop[g].price[0])
            # p0 is the first-step price if calm; compare to prep via mean
            rel = np.max(np.abs(p - p[0]) / max(abs(p[0]), 1.0))
            print(f"  σ={s:g} {g:5s} max |p-p[0]|/p[0]={rel:.3e}  "
                  f"p[0]={p[0]:.4f} p.min={p.min():.4f} p.max={p.max():.4f}")


def probe_quantities():
    print("\n=== 4. quantity signs: freeze wheat at 1.5 p0 ===")
    base = run_coupled_dynamics(subst_scale=0.0, use_demand=False,
                                use_amis=False, use_shocks=False,
                                use_industrial=True)
    T = len(base.by_crop["wheat"].price)
    p0w = float(base.by_crop["wheat"].price[0])
    freeze = {"wheat": np.full(T, 1.5 * p0w)}
    for s in (0.0, 0.6):
        run = run_coupled_dynamics(
            subst_scale=s, use_demand=False, use_amis=False,
            use_shocks=False, use_industrial=True, freeze_price=freeze)
        print(f"  σ={s:g}")
        for g in COUPLED_GRAINS:
            c0 = base.by_crop[g]
            c = run.by_crop[g]
            # skip t=0 (lag: freeze applies after step 0 demand)
            d0 = c0.consumption[:, 1:].sum()
            d1 = c.consumption[:, 1:].sum()
            ratio = d1 / d0 if d0 else float("nan")
            print(f"    {g:5s} cons t>=1 ×{ratio:.5f}  "
                  f"price mean {c.price[1:].mean():.2f} "
                  f"(base {c0.price[1:].mean():.2f})")
            if g == "maize" and c.industrial is not None:
                print(f"    maize industrial identical",
                      np.allclose(c.industrial, c0.industrial))


def probe_fac_formula():
    print("\n=== 5. fac vs (p/p0)**η at synthetic prices ===")
    eta = cross_price_eta(0.6)
    p0 = np.array([200.0, 400.0, 180.0])
    p = np.array([300.0, 400.0, 180.0])  # wheat +50%
    rel = np.maximum(p / p0, 1e-6)
    fac = np.exp(eta @ np.log(rel))
    # own-only at σ=0
    eta0 = cross_price_eta(0.0)
    fac0 = np.exp(eta0 @ np.log(rel))
    print("  fac σ=0.6", fac)
    print("  fac σ=0  ", fac0, "wheat own-only", (p[0] / p0[0]) ** eta0[0, 0])
    print("  rice fac>1", fac[1] > 1, "maize fac>1", fac[2] > 1,
          "wheat fac<1", fac[0] < 1)
    # Gate 0 unfloored vs 1e-6 floor at normal prices
    print("  floor binds?", np.any(p / p0 < 1e-6))


def probe_scarcity_split():
    print("\n=== 6. 2008 rice: consumption vs free vs price (σ=0 vs 0.6) ===")
    # Official split, compare a crisis window of steps. 2008 starts at
    # year index 2 of 2006–11, 24 steps/year, plus 2-year spin is inside prep
    # not in result length — result is start_year..end_year only.
    r0 = run_coupled_dynamics(subst_scale=0.0, use_demand=False)
    r1 = run_coupled_dynamics(subst_scale=0.6, use_demand=False)
    # March 2008 ≈ year 2008 month 3 → step (2008-2006)*24 + (3-1)*2 = 52
    sl = slice(48, 72)  # calendar 2008
    for g in COUPLED_GRAINS:
        a, b = r0.by_crop[g], r1.by_crop[g]
        print(f"  {g}")
        print(f"    price 08 mean σ0={a.price[sl].mean():.2f} σ6={b.price[sl].mean():.2f} "
              f"Δ%={(b.price[sl].mean()/a.price[sl].mean()-1)*100:.2f}")
        print(f"    cons  08 sum  σ0={a.consumption[:, sl].sum():.3f} "
              f"σ6={b.consumption[:, sl].sum():.3f} "
              f"Δ%={(b.consumption[:, sl].sum()/a.consumption[:, sl].sum()-1)*100:.2f}")
        print(f"    free  08 mean σ0={a.free_liquid[sl].mean():.3f} "
              f"σ6={b.free_liquid[sl].mean():.3f}")
        print(f"    offers 08 sum σ0={a.offers[:, sl].sum():.3f} "
              f"σ6={b.offers[:, sl].sum():.3f}")


def main():
    probe_eta()
    probe_fac_formula()
    probe_identity()
    probe_calm()
    probe_quantities()
    probe_scarcity_split()
    print("\nDONE")


if __name__ == "__main__":
    main()
