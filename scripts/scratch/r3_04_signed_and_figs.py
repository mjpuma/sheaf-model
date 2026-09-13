#!/usr/bin/env python3
"""R3-04: signed size of the within-step ask double-update, plus figures.

R3-03 measured |p^tr(post) - p^tr(pre)|. The sign is what matters: if the
post-update ask is systematically ABOVE the pre-update ask during a rally,
the double-update front-runs the world price by one adaptation step.
"""
from __future__ import annotations

import sys
import types
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "scratch"))

from sheaf.calendar24 import STEPS_PER_YEAR  # noqa: E402
from sheaf.dynamic_crop import default_crop_params  # noqa: E402
from sheaf.data_usda import load_price_series_monthly  # noqa: E402
from r3_01_lookahead import agri_w, build_probe  # noqa: E402
from r3_02_prototypes import build as build_variant  # noqa: E402
from r3_03_falsify import PROBE, PROBE_AT  # noqa: E402

CROPS = ("wheat", "maize", "rice")
SRC = ROOT / "sheaf" / "dynamic_crop.py"
OUT = ROOT / "diagnostics" / "redteam" / "r3"
FIGS = ROOT / "figures" / "scratch" / "r3"
P1 = dict(use_amis=True, use_shocks=True, use_demand=False)


def build_askprobe(name: str):
    src = SRC.read_text().replace(PROBE_AT, PROBE)
    mod = types.ModuleType(f"sheaf.{name}")
    mod.__package__ = "sheaf"
    mod.__file__ = str(SRC)
    mod.__dict__["_ASKD"] = []
    sys.modules[f"sheaf.{name}"] = mod
    exec(compile(src, mod.__file__, "exec"), mod.__dict__)
    return mod


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    FIGS.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    rows = []

    def out(s: str = "") -> None:
        print(s)
        lines.append(s)

    out("# R3-04 - signed ask double-update and figures\n")
    out("| crop | mean signed gap $/t | mean signed rel | rally-window "
        "signed rel (2007/08) | share of steps post > pre |")
    out("|---|---|---|---|---|")
    mod = build_askprobe("dc_r3_signed")
    price_paths = {}
    for crop in CROPS:
        mod.__dict__["_ASKD"].clear()
        res = mod.run_crop_dynamics(crop, **P1)
        T = len(res.price)
        d = np.array(mod.__dict__["_ASKD"], float)[-T:]
        num_pre, num_post, shp, _ = d.T
        ok = shp > 1e-12
        pre = np.where(ok, num_pre / np.maximum(shp, 1e-12), np.nan)
        post = np.where(ok, num_post / np.maximum(shp, 1e-12), np.nan)
        rel = (post - pre) / np.maximum(pre, 1e-9)
        # 2007/08 rally: Jun-2006 .. Mar-2008
        t0 = (2006 - res.start_year) * STEPS_PER_YEAR + 5 * 2
        t1 = (2008 - res.start_year) * STEPS_PER_YEAR + 2 * 2 + 2
        rally = np.nanmean(rel[t0:t1])
        share = float(np.nanmean((post - pre) > 0))
        out(f"| {crop} | {np.nanmean(post - pre):+.2f} | "
            f"{np.nanmean(rel):+.4%} | {rally:+.4%} | {share:.1%} |")
        rows.append(dict(crop=crop, mean_signed_gap=float(np.nanmean(post - pre)),
                         mean_signed_rel=float(np.nanmean(rel)),
                         rally_signed_rel=float(rally),
                         share_post_gt_pre=share))
        price_paths[crop] = {"V0": res.price.copy()}
    out("")
    pd.DataFrame(rows).to_csv(OUT / "r3_ask_double_update_signed.csv",
                              index=False)

    # variant price paths for the figure
    m1 = build_variant("dc_r3f_v1", agri_exp=True)
    m3 = build_variant("dc_r3f_v3", pre_ask=True)
    for crop in CROPS:
        price_paths[crop]["V1"] = m1.run_crop_dynamics(crop, **P1).price.copy()
        price_paths[crop]["V3"] = m3.run_crop_dynamics(crop, **P1).price.copy()

    # ---- figure 1: lag-weight profiles + h_t histogram ----------------
    probe = build_probe()
    hs = {}
    for crop in CROPS:
        probe.__dict__["_DIAG"].clear()
        probe.run_crop_dynamics(crop, **P1)
        hs[crop] = probe.__dict__["_DIAG"][-1]["lean_h"]

    fig, axes = plt.subplots(1, 2, figsize=(11, 3.9))
    ax = axes[0]
    ks = np.arange(0, 25)
    ax.plot(ks, agri_w(ks), "o-", color="#1f4e79", lw=1.8, ms=3.5,
            label=r"Agrimate $w_k$ (Eq. D.1a, $N_{for}$=6, $\tau_{for}$=4.8)")
    for crop, c in zip(CROPS, ("#c0392b", "#e67e22", "#148f77")):
        phi = default_crop_params(crop).foresight_phi
        ax.axhline(phi, ls="--", lw=1.2, color=c,
                   label=rf"SHEAF $\phi$ = {phi:.2f} ({crop}), flat in lag")
    ax.set_xlabel("forward lag $k$ (steps ahead)")
    ax.set_ylabel("weight on REALISED harvest")
    ax.set_title("Weight on realised future harvest by lag")
    ax.set_ylim(-0.03, 1.05)
    ax.legend(fontsize=7, frameon=False)

    ax = axes[1]
    for crop, c in zip(CROPS, ("#c0392b", "#e67e22", "#148f77")):
        ax.hist(hs[crop], bins=np.arange(0.5, 21.5), alpha=0.45, color=c,
                label=f"{crop} (median {int(np.median(hs[crop]))})")
    ax.axvline(6, color="#1f4e79", lw=1.6,
               label=r"Agrimate $N_{for}$ = 6")
    ax.set_xlabel("lean horizon $h_t$ (steps)")
    ax.set_ylabel("steps")
    ax.set_title("Realised Gate 0 forward-window length")
    ax.legend(fontsize=7, frameon=False)
    fig.tight_layout()
    f1 = FIGS / "r3_fig1_lag_weights.png"
    fig.savefig(f1, dpi=140)
    plt.close(fig)

    # ---- figure 2: price paths ----------------------------------------
    obs_all = load_price_series_monthly(deflated=True)
    fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    for ax, crop in zip(axes, CROPS):
        o = obs_all[(obs_all.year >= 2006) & (obs_all.year <= 2011)]
        xo = np.arange(len(o)) * 2 + 1
        ax.plot(xo, o[crop], color="#c0392b", lw=2, label="Pink Sheet real")
        for lab, ls, c in (("V0", "-", "0.15"), ("V1", "--", "#1f4e79"),
                           ("V3", ":", "#148f77")):
            p = price_paths[crop][lab]
            ax.plot(np.arange(len(p)), p, ls=ls, color=c, lw=1.3, label=lab)
        ax.set_ylabel(f"{crop}  $/t")
        ax.legend(fontsize=7, frameon=False, ncol=4)
    axes[-1].set_xlabel("step (24/yr from Jan 2006)")
    axes[0].set_title("R3 prototypes: V0 baseline, V1 Agrimate D.1 "
                      "expectation, V3 pre-update ask")
    fig.tight_layout()
    f2 = FIGS / "r3_fig2_price_paths.png"
    fig.savefig(f2, dpi=140)
    plt.close(fig)

    out(f"Figures: `{f1.relative_to(ROOT)}`, `{f2.relative_to(ROOT)}`\n")
    (OUT / "R3_04_SIGNED.md").write_text("\n".join(lines) + "\n")
    print(f"wrote {OUT / 'R3_04_SIGNED.md'}")


if __name__ == "__main__":
    main()
