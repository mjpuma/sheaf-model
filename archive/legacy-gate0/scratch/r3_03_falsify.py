#!/usr/bin/env python3
"""R3-03: falsification battery for the R3 findings.

1. Is V1 a tuned knob? Re-run it across Agrimate's OWN sensitivity range for
   N_for (3 / 6 / 9, supplement Tbl. F.1) and tau_for (0.1 / 0.2 / 0.4 N_year).
   Agrimate reports that changing N_for "does not change the model dynamics";
   if SHEAF's scores swing wildly across that range, V1 is a fitted knob and
   the parity argument does not carry it.
2. Does V1 double-count against `foresight_phi`? Under V1 the parameter should
   be exactly inert. Verified by running V1 at phi in {0.0, 0.55, 1.0}.
3. How big is the within-step ask double-update actually? Measure
   |ask_post - ask_pre| and the resulting p^tr gap directly.
4. How long are the AMIS restriction phases SHEAF actually sees? This sizes
   question (b) - duration knowledge can only matter where duration varies.
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

from score_subannual_crop import _corr, _hike  # noqa: E402
from sheaf.calendar24 import STEPS_PER_YEAR  # noqa: E402
from sheaf.data_usda import load_price_series_monthly  # noqa: E402
from sheaf.dynamic_crop import amis_export_cuts  # noqa: E402
from sheaf.calibration import DATA  # noqa: E402

CROPS = ("wheat", "maize", "rice")
SRC = ROOT / "sheaf" / "dynamic_crop.py"
OUT = ROOT / "diagnostics" / "redteam" / "r3"
P1 = dict(use_amis=True, use_shocks=True, use_demand=False)

sys.path.insert(0, str(ROOT / "scripts" / "scratch"))
from r3_02_prototypes import EXP_AGRI, EXP_ORIG, LEAN_LAG0, LEAN_ORIG  # noqa: E402

PROBE_AT = "        lean_need = float(lean_gap.sum())"
PROBE = """        _ASKD.append((float(np.dot(ask_path[:, t], shipped)),
                      float(np.dot(ask, shipped)),
                      float(shipped.sum()),
                      float(np.max(np.abs(ask - ask_path[:, t])))))
        lean_need = float(lean_gap.sum())"""


def build(name: str, *, agri=False, nfor=6.0, taufor=4.8, probe=False):
    src = SRC.read_text()
    if agri:
        body = EXP_AGRI.replace("_NFOR, _TAUFOR = 6.0, 4.8",
                                f"_NFOR, _TAUFOR = {nfor}, {taufor}")
        src = src.replace(EXP_ORIG, body).replace(LEAN_ORIG, LEAN_LAG0)
    if probe:
        assert src.count(PROBE_AT) == 1
        src = src.replace(PROBE_AT, PROBE)
    mod = types.ModuleType(f"sheaf.{name}")
    mod.__package__ = "sheaf"
    mod.__file__ = str(SRC)
    mod.__dict__["_ASKD"] = []
    sys.modules[f"sheaf.{name}"] = mod
    exec(compile(src, mod.__file__, "exec"), mod.__dict__)
    return mod


def score(mod, crop, obs_all, **kw):
    obs = obs_all[(obs_all.year >= 2006) & (obs_all.year <= 2011)][
        ["year", "month", crop]].rename(columns={crop: "obs_price"})
    res = mod.run_crop_dynamics(crop, **P1, **kw)
    m = mod.result_to_monthly(res).merge(obs, on=["year", "month"], how="left")
    return (_corr(m.model_price, m.obs_price),
            _hike(m, "model_price", 2006, 6, 2008, 3),
            _hike(m, "model_price", 2009, 6, 2011, 2))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    obs_all = load_price_series_monthly(deflated=True)
    lines: list[str] = []
    rows_sens, rows_phi, rows_ask, rows_dur = [], [], [], []

    def out(s: str = "") -> None:
        print(s)
        lines.append(s)

    out("# R3-03 - falsification battery\n")

    # ---- 1. is V1 a fitted knob? --------------------------------------
    out("## 1. V1 across Agrimate's own N_for / tau_for sensitivity range\n")
    out("Agrimate Tbl. F.1 explores N_for in {3, 6, 9} and tau_for in "
        "{0.1, 0.2, 0.4} x N_year and reports no change in model dynamics. "
        "If SHEAF's scores swing across that range, V1 is a knob.\n")
    out("| N_for | tau_for | crop | corr | 2007/08 | 2010/11 |")
    out("|---|---|---|---|---|---|")
    grid = [(3.0, 4.8), (6.0, 4.8), (9.0, 4.8),
            (6.0, 2.4), (6.0, 9.6)]
    for nf, tf in grid:
        mod = build(f"dc_r3_s{int(nf)}_{int(tf*10)}", agri=True,
                    nfor=nf, taufor=tf)
        for crop in CROPS:
            c, h07, h10 = score(mod, crop, obs_all)
            out(f"| {nf:.0f} | {tf:.1f} | {crop} | {c:+.3f} | x{h07:.2f} | "
                f"x{h10:.2f} |")
            rows_sens.append(dict(n_for=nf, tau_for=tf, crop=crop, corr=c,
                                  hike_0708=h07, hike_1011=h10))
    out("")
    s = pd.DataFrame(rows_sens)
    out("Spread across the whole Agrimate range:\n")
    out("| crop | corr min | corr max | corr spread | 07/08 spread | "
        "10/11 spread |")
    out("|---|---|---|---|---|---|")
    for crop in CROPS:
        g = s[s.crop == crop]
        out(f"| {crop} | {g['corr'].min():+.3f} | {g['corr'].max():+.3f} | "
            f"{g['corr'].max() - g['corr'].min():.3f} | "
            f"{g.hike_0708.max() - g.hike_0708.min():.2f} | "
            f"{g.hike_1011.max() - g.hike_1011.min():.2f} |")
    out("")

    # ---- 2. does V1 double-count against phi? -------------------------
    out("## 2. Is `foresight_phi` inert under V1 (no double-counting)?\n")
    mod1 = build("dc_r3_v1phi", agri=True)
    out("| crop | phi | corr | 2007/08 | 2010/11 |")
    out("|---|---|---|---|---|")
    for crop in CROPS:
        for phi in (0.0, 0.55, 1.0):
            c, h07, h10 = score(mod1, crop, obs_all, foresight_phi=phi)
            out(f"| {crop} | {phi:.2f} | {c:+.3f} | x{h07:.2f} | x{h10:.2f} |")
            rows_phi.append(dict(crop=crop, phi=phi, corr=c,
                                 hike_0708=h07, hike_1011=h10))
    p = pd.DataFrame(rows_phi)
    exact = all(len(g["corr"].round(12).unique()) == 1
                for _, g in p.groupby("crop"))
    out("")
    out(f"phi exactly inert under V1: **{exact}** "
        "(so V1 replaces the parameter rather than stacking on it).\n")
    out("For contrast, phi in the SHIPPED model:\n")
    mod0 = build("dc_r3_v0phi")
    out("| crop | phi | corr | 2007/08 | 2010/11 |")
    out("|---|---|---|---|---|")
    for crop in CROPS:
        for phi in (0.0, 0.55, 1.0):
            c, h07, h10 = score(mod0, crop, obs_all, foresight_phi=phi)
            out(f"| {crop} | {phi:.2f} | {c:+.3f} | x{h07:.2f} | x{h10:.2f} |")
    out("")

    # ---- 3. size of the within-step ask double-update -----------------
    out("## 3. Size of the within-step ask double-update\n")
    out("`_simulate_window` allocates shipments with the inherited ask "
        "(`A_eff` at L616 uses `ask_path[:, t]`), then updates `ask` at "
        "L646-651, then values the SAME shipments at the updated ask "
        "(L667). README section 8 writes p^tr with q_{i,t} while step 5 of "
        "Method of solution produces q_{i,t+1}.\n")
    out("| crop | mean |p^tr(post) - p^tr(pre)| $/t | mean rel gap | "
        "max rel gap | mean max_i |dask| $/t |")
    out("|---|---|---|---|---|")
    modp = build("dc_r3_probe3", probe=True)
    for crop in CROPS:
        modp.__dict__["_ASKD"].clear()
        res = modp.run_crop_dynamics(crop, **P1)
        d = np.array(modp.__dict__["_ASKD"], float)[-len(res.price):]
        num_pre, num_post, shp, dask = d.T
        ok = shp > 1e-12
        pre = num_pre[ok] / shp[ok]
        post = num_post[ok] / shp[ok]
        gap = np.abs(post - pre)
        rel = gap / np.maximum(pre, 1e-9)
        out(f"| {crop} | {gap.mean():.2f} | {rel.mean():.4%} | "
            f"{rel.max():.4%} | {dask.mean():.2f} |")
        rows_ask.append(dict(crop=crop, mean_abs_gap=float(gap.mean()),
                             mean_rel_gap=float(rel.mean()),
                             max_rel_gap=float(rel.max()),
                             mean_max_dask=float(dask.mean())))
    out("")

    # ---- 4. AMIS restriction phase lengths ----------------------------
    out("## 4. How long are the AMIS restriction phases SHEAF sees?\n")
    out("Duration knowledge can only matter where duration varies and is "
        "informative. Phase = maximal run of a constant nonzero cut.\n")
    countries = [d["name"] for d in DATA] + ["RestOfWorld"]
    out("| crop | n phases | median len (steps) | mean | max | "
        "share of cut-steps in phases >= 6 steps |")
    out("|---|---|---|---|---|---|")
    for crop in CROPS:
        cuts = amis_export_cuts(crop, countries, 2006, 2011)
        lens, long_steps, tot_steps = [], 0, 0
        for i in range(cuts.shape[0]):
            t = 0
            T = cuts.shape[1]
            while t < T:
                if cuts[i, t] <= 0:
                    t += 1
                    continue
                c = cuts[i, t]
                m = t
                while m + 1 < T and cuts[i, m + 1] == c:
                    m += 1
                L = m - t + 1
                lens.append(L)
                tot_steps += L
                if L >= 6:
                    long_steps += L
                t = m + 1
        lens_a = np.array(lens, float)
        share = long_steps / max(tot_steps, 1)
        out(f"| {crop} | {len(lens)} | {np.median(lens_a):.0f} | "
            f"{lens_a.mean():.1f} | {lens_a.max():.0f} | {share:.1%} |")
        rows_dur.append(dict(crop=crop, n_phases=len(lens),
                             median_len=float(np.median(lens_a)),
                             mean_len=float(lens_a.mean()),
                             max_len=float(lens_a.max()),
                             share_steps_in_long_phases=float(share)))
        # Russia wheat 2010 detail
        if crop == "wheat" and "Russia" in countries:
            i = countries.index("Russia")
            nz = np.flatnonzero(cuts[i] > 0)
            if len(nz):
                out(f"    - Russia wheat cut steps: {len(nz)}, levels "
                    f"{sorted(set(np.round(cuts[i, nz], 2)))}, "
                    f"first step {nz.min()} "
                    f"({2006 + nz.min() // STEPS_PER_YEAR}), last {nz.max()} "
                    f"({2006 + nz.max() // STEPS_PER_YEAR})")
    out("")

    pd.DataFrame(rows_sens).to_csv(OUT / "r3_v1_nfor_sensitivity.csv",
                                   index=False)
    pd.DataFrame(rows_phi).to_csv(OUT / "r3_v1_phi_inert.csv", index=False)
    pd.DataFrame(rows_ask).to_csv(OUT / "r3_ask_double_update.csv",
                                  index=False)
    pd.DataFrame(rows_dur).to_csv(OUT / "r3_amis_phase_lengths.csv",
                                  index=False)
    (OUT / "R3_03_FALSIFY.md").write_text("\n".join(lines) + "\n")
    print(f"\nwrote {OUT / 'R3_03_FALSIFY.md'}")


if __name__ == "__main__":
    main()
