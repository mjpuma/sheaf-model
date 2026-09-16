#!/usr/bin/env python3
"""A1: verify overleaf/gate0_discussion equations against _simulate_window.

Resolves four hypotheses seeded in audit_prompts/GATE0_MODEL_PROMPTS.md:

  H1  the scarcity regulariser f is neither small nor constant
  H2  the calm identity p* = p0 is an explicit branch, not algebra
  H3  the unmet anomaly is truncated at zero (one-sided channel)
  H4  p^tr uses this step's asks, not last step's

Read-only with respect to sheaf/*.py: H2 is tested by recompiling the module
source with the calm branch disabled, never by editing it.
"""
from __future__ import annotations

import sys
import types
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from sheaf.calendar24 import STEPS_PER_YEAR  # noqa: E402
from sheaf.dynamic_crop import (  # noqa: E402
    prepare_crop_run,
    run_crop_dynamics,
    simulate_prep,
)

CROPS = ("wheat", "maize", "rice")
SRC = ROOT / "sheaf" / "dynamic_crop.py"

CALM_ORIG = """            calm = (abs(free - twin) < 1e-6 and u_anom < 1e-9
                    and block_frac < 1e-9)
            if calm:
                p_star = p0
            else:"""
CALM_OFF = """            calm = False
            if calm:
                p_star = p0
            else:"""


def load_nocalm():
    """Recompile dynamic_crop with the calm short-circuit disabled."""
    src = SRC.read_text()
    if CALM_ORIG not in src:
        raise SystemExit("calm block not found verbatim; inspect L664-670")
    mod = types.ModuleType("sheaf.dynamic_crop_nocalm")
    mod.__package__ = "sheaf"
    mod.__file__ = str(SRC)
    sys.modules["sheaf.dynamic_crop_nocalm"] = mod
    exec(compile(src.replace(CALM_ORIG, CALM_OFF), mod.__file__, "exec"),
         mod.__dict__)
    return mod


def h1_regulariser(out):
    out("## H1 — the scarcity regulariser\n")
    out("Note eq (14) prints r = (F_twin + f)/(F + f), f 'a small regularising")
    out("constant'. Code L661-663: shift = 0.05*sum(safety) + max(0,-min(free,twin)).\n")
    rows = []
    for crop in CROPS:
        prep = prepare_crop_run(crop, use_amis=True, use_shocks=True,
                                use_demand=False)
        res = simulate_prep(prep)
        safety_w = float(max(prep.safety.sum(), 1.0))
        floor0 = 0.05 * safety_w
        free, twin = res.free_liquid, res.free_twin
        neg = np.maximum(0.0, -np.minimum(free, twin))
        shift = floor0 + neg
        bare = np.where(np.abs(free) > 1e-12, twin / np.where(free == 0, np.nan, free),
                        np.nan)
        code = (twin + shift) / (free + shift)
        tight = int(np.nanargmin(free))
        out(f"### {crop}")
        out(f"- sum(safety) = {safety_w:.1f} MMT, so f = 0.05*sum(safety) = "
            f"**{floor0:.2f} MMT**")
        out(f"- mean free = {np.mean(free):.1f} MMT, so f is "
            f"{100*floor0/max(np.mean(free),1e-9):.1f}% of mean accessible stock")
        out(f"- second term max(0,-min(free,twin)) is nonzero at "
            f"{int((neg > 0).sum())}/{len(neg)} steps"
            + (f", max {neg.max():.1f} MMT" if neg.max() > 0 else ""))
        out(f"- tightest step t={tight}: free={free[tight]:.1f}, "
            f"twin={twin[tight]:.1f} MMT; ratio as coded {code[tight]:.4f} "
            f"vs unregularised {bare[tight]:.4f} "
            f"({100*(code[tight]/bare[tight]-1):+.1f}%)")
        with np.errstate(invalid="ignore"):
            dev = np.abs(code / bare - 1.0)
        out(f"- across all steps: mean |bias| {100*np.nanmean(dev):.1f}%, "
            f"max {100*np.nanmax(dev):.1f}%\n")
        rows.append((crop, floor0, float(np.nanmean(dev)), float(np.nanmax(dev))))
    return rows


def h2_calm(out, nocalm):
    out("## H2 — is the reference identity algebra or a branch?\n")
    out("Note §3.6 calls p* = p0 in a matched run 'an algebraic identity, not a")
    out("calibrated residual'. Code L666-669 sets p_star = p0 outright when")
    out("|free-twin| < 1e-6 and u_anom < 1e-9 and block_frac < 1e-9.\n")
    out("Test: recompile the module with that branch disabled and re-run the")
    out("neither-path configuration that assert_twin_identity uses")
    out("(use_amis=False, use_shocks=False, use_demand=False, use_industrial=False).")
    out("assert_twin_identity tolerates 2% price drift.\n")
    rows = []
    for crop in CROPS:
        kw = dict(use_amis=False, use_shocks=False, use_demand=False,
                  use_industrial=False)
        base = run_crop_dynamics(crop, **kw)
        off = nocalm.run_crop_dynamics(crop, **kw)
        p0 = float(base.price[0])
        d_base = float(np.max(np.abs(base.price[STEPS_PER_YEAR:] - p0)) / p0)
        d_off = float(np.max(np.abs(off.price[STEPS_PER_YEAR:] - p0)) / p0)
        # does the branch actually fire, and how far are asks from p0?
        fe = np.abs(base.free_liquid - base.free_twin)
        fires = int((fe < 1e-6).sum())
        ask_dev = float(np.max(np.abs(base.ask - p0)) / p0)
        out(f"### {crop}")
        out(f"- p0 = {p0:.1f} $/t")
        out(f"- calm condition |free-twin|<1e-6 holds at {fires}/{len(fe)} steps "
            f"(max |free-twin| = {fe.max():.2e} MMT)")
        out(f"- price drift with the branch:    {100*d_base:.3f}%  "
            f"{'PASS' if d_base <= 0.02 else 'FAIL'} at the 2% tolerance")
        out(f"- price drift WITHOUT the branch: {100*d_off:.3f}%  "
            f"{'PASS' if d_off <= 0.02 else 'FAIL'} at the 2% tolerance")
        out(f"- max |ask - p0| / p0 in the matched run: {100*ask_dev:.3f}% "
            f"-- the note's step 'with offer prices at p0' requires this be 0\n")
        rows.append((crop, d_base, d_off, ask_dev, fires, len(fe)))
    return rows


def h3_unmet(out):
    out("## H3 — is the unmet-demand channel one-sided?\n")
    out("Code L664-665: u0 = unmet_twin[t]; u_anom = max(0, unmet_frac - u0).")
    out("So below-twin unmet cannot lower the price. The note writes Delta u as")
    out("'the excess of unmet import demand over its twin value' with no truncation.\n")
    for crop in CROPS:
        prep = prepare_crop_run(crop, use_amis=True, use_shocks=True,
                                use_demand=False)
        res = simulate_prep(prep)
        raw = res.unmet_frac - prep.unmet_twin
        out(f"- {crop}: raw (unmet - twin) is negative at "
            f"{int((raw < -1e-12).sum())}/{len(raw)} steps "
            f"(min {raw.min():+.4f}); truncation is therefore "
            f"{'ACTIVE' if (raw < -1e-12).any() else 'never binding'}")
    out("")


def h4_ptrade(out):
    out("## H4 — does p^tr use this step's asks?\n")
    out("Order in _simulate_window: asks recorded at L599 (pre-update), asks")
    out("updated L632-636, p_trade computed L650-653 from the updated `ask`.")
    out("So p^tr_t is built from q_{i,t}, not q_{i,t-1}. Magnitude of the")
    out("distinction, using recorded pre-update asks against shipments:\n")
    for crop in CROPS:
        res = run_crop_dynamics(crop, use_amis=True, use_shocks=True,
                               use_demand=False)
        shipped = res.exports
        tot = shipped.sum(axis=0)
        ok = tot > 1e-12
        lag = np.full(len(tot), np.nan)
        lag[ok] = (res.ask[:, ok] * shipped[:, ok]).sum(axis=0) / tot[ok]
        # model p_trade is not exported; bound the gap by the ask update size
        dq = np.abs(np.diff(res.ask, axis=1))
        out(f"- {crop}: shipment-weighted mean of PRE-update asks ranges "
            f"{np.nanmin(lag):.1f}-{np.nanmax(lag):.1f} $/t; "
            f"per-step |ask change| median {np.median(dq):.2f}, "
            f"p95 {np.percentile(dq, 95):.2f} $/t")
    out("\nThe gap is one ask update, so it is small in calm periods and largest")
    out("exactly where asks move fastest, i.e. in the crisis windows.\n")


def main():
    lines = []

    def out(s=""):
        print(s)
        lines.append(s)

    out("# A1 — do the note's equations match the code?\n")
    out("Generated by `scripts/scratch/a1_equation_audit.py`. Read-only pass;")
    out("`sheaf/dynamic_crop.py` is not modified. H2 recompiles the module")
    out("source in memory with the calm branch disabled.\n")
    h1_regulariser(out)
    nocalm = load_nocalm()
    h2_calm(out, nocalm)
    h3_unmet(out)
    h4_ptrade(out)

    dest = ROOT / "diagnostics" / "gate0_prep" / "a1"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "A1_HYPOTHESES.md").write_text("\n".join(lines) + "\n")
    print(f"\nwrote {(dest / 'A1_HYPOTHESES.md').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
