#!/usr/bin/env python3
"""R0k: adjudicating R3's p_trade double-update finding on current code.

R3 reports that _simulate_window allocates shipments using the inherited
ask and then values those same shipments at the freshly updated ask. Read
directly:

  L643  ask_path[:, t] = ask            <- records q_t as step t's ask
  L645-648  A_eff/S_eff from `ask`      <- allocation uses q_t
  L678-681  ask = ...                   <- ask updated in place to q_{t+1}
  L697  p_trade = dot(ask, shipped)/... <- valuation uses q_{t+1}

So the model's own output array says step t's offer price is the pre-update
value, the allocation agrees, and only the valuation disagrees. Agrimate
Eq. D.4 is explicit that the transaction price is the offer price the
demand request responded to.

R3's numbers were measured before the R0f scarcity fix, so maize's are
stale. This re-measures on current code and also checks the direction of
the bias, which determines whether it flatters the crisis.

Read-only; in-memory recompilation.
"""
from __future__ import annotations

import sys
import types
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from sheaf.data_usda import load_price_series_monthly  # noqa: E402
from sheaf.dynamic_crop import (  # noqa: E402
    result_to_monthly,
    run_crop_dynamics,
)
from score_subannual_crop import _corr, _hike  # noqa: E402

SRC = ROOT / "sheaf" / "dynamic_crop.py"
CROPS = ("wheat", "maize", "rice")
FULL = dict(use_amis=True, use_shocks=True, use_demand=False)
ASSERTS = ("assert_twin_identity", "assert_amis_raises_price",
           "assert_no_spring_spike", "assert_amis_cuts_exports")

ORIG = """        shipped_sum = float(shipped.sum())
        if shipped_sum > 1e-12:
            p_trade = float(np.dot(ask, shipped) / shipped_sum)"""
FIXED = """        shipped_sum = float(shipped.sum())
        if shipped_sum > 1e-12:
            p_trade = float(np.dot(ask_path[:, t], shipped) / shipped_sum)"""


def build():
    src = SRC.read_text()
    if ORIG not in src:
        raise SystemExit("p_trade block not found verbatim")
    mod = types.ModuleType("sheaf.dc_ptrade")
    mod.__package__ = "sheaf"
    mod.__file__ = str(SRC)
    sys.modules["sheaf.dc_ptrade"] = mod
    exec(compile(src.replace(ORIG, FIXED), mod.__file__, "exec"), mod.__dict__)
    return mod


def main():
    lines = []

    def out(s=""):
        print(s)
        lines.append(s)

    obs_all = load_price_series_monthly(deflated=True)
    fix = build()
    rows = []

    out("# R0k — adjudicating the p_trade double-update, on current code\n")

    out("## 1. Size and direction of the valuation gap\n")
    out("The gap is (updated ask − allocating ask) weighted by shipments,")
    out("as a share of the allocating value. A positive gap through a rally")
    out("means the shipped-weighted price is systematically flattered.\n")
    out("| crop | mean gap, all steps | mean gap, 2007/08 rally | mean gap, 2010/11 |")
    out("|---|---|---|---|")
    for crop in CROPS:
        r = run_crop_dynamics(crop, **FULL)
        # ask_path[:, t] is the allocating ask; reconstruct the updated ask
        # as the one used at t, which is ask_path[:, t+1] up to the clip.
        q_alloc, ship = r.ask, r.exports
        gap = np.zeros(q_alloc.shape[1] - 1)
        for t in range(q_alloc.shape[1] - 1):
            s = ship[:, t]
            tot = s.sum()
            if tot > 1e-12:
                va = float(np.dot(q_alloc[:, t], s) / tot)
                vb = float(np.dot(q_alloc[:, t + 1], s) / tot)
                gap[t] = vb / va - 1.0
        # 2006-06..2008-03 is steps 10..51; 2009-06..2011-02 is steps 82..122
        out(f"| {crop} | {100*gap.mean():+.2f}% "
            f"| {100*gap[10:52].mean():+.2f}% | {100*gap[82:123].mean():+.2f}% |")
        rows.append(dict(crop=crop, kind="gap", all=float(gap.mean()),
                         w0708=float(gap[10:52].mean()),
                         w1011=float(gap[82:123].mean())))
    out("")

    out("## 2. Score impact of valuing shipments at the allocating ask\n")
    out("| crop | metric | current | fixed | Δ | observed |")
    out("|---|---|---|---|---|---|")
    for crop in CROPS:
        obs = obs_all[(obs_all.year >= 2006) & (obs_all.year <= 2011)][
            ["year", "month", crop]].rename(columns={crop: "obs_price"})
        o07 = _hike(obs, "obs_price", 2006, 6, 2008, 3)
        o10 = _hike(obs, "obs_price", 2009, 6, 2011, 2)
        v = {}
        for lab, runner, conv in (
                ("cur", run_crop_dynamics, result_to_monthly),
                ("fix", fix.run_crop_dynamics, fix.result_to_monthly)):
            m = conv(runner(crop, **FULL))
            mm = m.merge(obs, on=["year", "month"], how="left")
            v[lab] = (_corr(mm.model_price, mm.obs_price),
                      _hike(m, "model_price", 2006, 6, 2008, 3),
                      _hike(m, "model_price", 2009, 6, 2011, 2))
        out(f"| {crop} | corr | {v['cur'][0]:+.3f} | {v['fix'][0]:+.3f} "
            f"| {v['fix'][0]-v['cur'][0]:+.3f} | — |")
        out(f"| {crop} | 2007/08 | x{v['cur'][1]:.2f} | x{v['fix'][1]:.2f} "
            f"| {v['fix'][1]-v['cur'][1]:+.3f} | x{o07:.2f} |")
        out(f"| {crop} | 2010/11 | x{v['cur'][2]:.2f} | x{v['fix'][2]:.2f} "
            f"| {v['fix'][2]-v['cur'][2]:+.3f} | x{o10:.2f} |")
        rows.append(dict(crop=crop, kind="score", corr_cur=v['cur'][0],
                         corr_fix=v['fix'][0], h07_cur=v['cur'][1],
                         h07_fix=v['fix'][1], h10_cur=v['cur'][2],
                         h10_fix=v['fix'][2], obs07=o07, obs10=o10))
    out("")
    out("## 3. Absolute error in the hike ratios, before and after\n")
    out("Whether the fix moves the model toward or away from the observed")
    out("ratios, summed over both windows and all three crops.\n")
    tot_c = tot_f = 0.0
    out("| crop | window | |error| current | |error| fixed |")
    out("|---|---|---|---|")
    for crop in CROPS:
        rec = [r for r in rows if r.get("kind") == "score"
               and r["crop"] == crop][0]
        for w, cur, fx, ob in (("2007/08", rec["h07_cur"], rec["h07_fix"],
                                rec["obs07"]),
                               ("2010/11", rec["h10_cur"], rec["h10_fix"],
                                rec["obs10"])):
            ec, ef = abs(cur - ob), abs(fx - ob)
            tot_c += ec
            tot_f += ef
            out(f"| {crop} | {w} | {ec:.3f} | {ef:.3f} |")
    out(f"| **total** | | **{tot_c:.3f}** | **{tot_f:.3f}** |")
    out("")

    out("## 4. Assertions under the fix\n")
    for crop in CROPS:
        st = []
        for name in ASSERTS:
            try:
                getattr(fix, name)(crop)
                st.append("PASS")
            except AssertionError as e:
                st.append(f"FAIL({str(e)[:40]})")
        out(f"- {crop}: {st}")
    out("")

    dest = ROOT / "diagnostics" / "redteam" / "r0"
    dest.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(dest / "ptrade_adjudication.csv", index=False)
    (dest / "R0K_PTRADE_ADJUDICATION.md").write_text("\n".join(lines) + "\n")
    print(f"\nwrote {(dest / 'R0K_PTRADE_ADJUDICATION.md').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
