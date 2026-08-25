#!/usr/bin/env python3
"""Gate 1 scoring: substitution on the locked Gate 0 spine.

Hard: coupled subst_scale=0 matches independent Gate 0 prices; spillover
sign; wheat attribution signs survive; rice AMIS still dominates 2008 rice.
Soft: σ grid {0, 0.3, 0.6} as a pre-declared band — do not pick σ* on 2008.

See diagnostics/GATE1_PLAN.md.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from sheaf.data_usda import load_price_series_monthly
from sheaf.dynamic_coupled import (
    COUPLED_GRAINS,
    assert_subst0_matches_gate0,
    run_coupled_dynamics,
)
from sheaf.dynamic_crop import result_to_monthly
from score_subannual_crop import _corr, _hike

DIAG = ROOT / "diagnostics"
FIGS = ROOT / "figures"
HIKE_08 = (2006, 6, 2008, 3)
HIKE_10 = (2009, 6, 2011, 2)
SCALES = (0.0, 0.3, 0.6)
LEGS = {
    "full": dict(use_amis=True, use_shocks=True, use_demand=False),
    "shocks": dict(use_amis=False, use_shocks=True, use_demand=False),
    "tau": dict(use_amis=True, use_shocks=False, use_demand=False,
                use_industrial=False),
}


def _monthly(coupled, grain: str) -> pd.DataFrame:
    return result_to_monthly(coupled.by_crop[grain])


def _metrics(m: pd.DataFrame, obs: pd.DataFrame, grain: str, scale: float,
             leg: str) -> dict:
    rec = dict(grain=grain, subst_scale=scale, leg=leg)
    rec["corr"] = _corr(m.model_price, m.obs_price)
    rec["hike_2008"] = _hike(m, "model_price", *HIKE_08)
    rec["hike_2010"] = _hike(m, "model_price", *HIKE_10)
    rec["obs_2008"] = _hike(obs, "obs_price", *HIKE_08)
    rec["obs_2010"] = _hike(obs, "obs_price", *HIKE_10)
    return rec


def main():
    DIAG.mkdir(parents=True, exist_ok=True)
    FIGS.mkdir(parents=True, exist_ok=True)

    print("Gate 1 identity (σ=0 vs independent Gate 0)...")
    assert_subst0_matches_gate0()
    print("  PASS")

    pink = load_price_series_monthly(deflated=True)
    pink = pink[(pink.year >= 2006) & (pink.year <= 2011)]

    rows = []
    monthly = []
    runs = {}
    for s in SCALES:
        for leg, flags in LEGS.items():
            print(f"  run σ={s:g}  {leg}...")
            runs[(s, leg)] = run_coupled_dynamics(subst_scale=s, **flags)

    for s in SCALES:
        for leg in LEGS:
            for g in COUPLED_GRAINS:
                obs = pink[["year", "month", g]].rename(columns={g: "obs_price"})
                m = _monthly(runs[(s, leg)], g).merge(
                    obs, on=["year", "month"], how="left")
                m["grain"] = g
                m["subst_scale"] = s
                m["leg"] = leg
                monthly.append(m)
                rows.append(_metrics(m, obs, g, s, leg))

    fig, axes = plt.subplots(3, 1, figsize=(11, 9.2), sharex=True)
    styles = {0.0: ("--", "#6c3483"), 0.3: ("-.", "#1e8449"),
              0.6: ("-", "0.15")}
    for ax, g in zip(axes, COUPLED_GRAINS):
        obs = pink[["year", "month", g]].rename(columns={g: "obs_price"})
        x = None
        for s in SCALES:
            m = _monthly(runs[(s, "full")], g).merge(
                obs, on=["year", "month"], how="left")
            if x is None:
                x = np.arange(len(m))
                ax.plot(x, m.obs_price, color="#c0392b", lw=2,
                        label="Pink Sheet")
            ls, c = styles[s]
            ax.plot(x, m.model_price, ls=ls, color=c, lw=1.3,
                    label=f"σ={s:g}")
        ax.set_ylabel("$/t")
        ax.set_title(g.capitalize())
        ax.legend(fontsize=7, ncol=4)
        ticks = [i for i, (y, mo) in enumerate(zip(m.year, m.month)) if mo == 1]
        ax.set_xticks(ticks, [str(int(m.year.iloc[i])) for i in ticks])

    fig.suptitle("Gate 1: Gate 0 spine with substitution σ (official P1 split)")
    fig.tight_layout()
    fig.savefig(FIGS / "fig_gate1_substitution.png", dpi=140)
    plt.close(fig)

    met = pd.DataFrame(rows)
    met.to_csv(DIAG / "gate1_score.csv", index=False)
    pd.concat(monthly, ignore_index=True).to_csv(
        DIAG / "gate1_monthly.csv", index=False)

    full = met[met.leg == "full"]
    print("\nHike / corr (official split, full leg):")
    for _, r in full.iterrows():
        print(f"  {r['grain']:5s} σ={r['subst_scale']:g}  "
              f"corr={r['corr']:+.3f}  "
              f"2008 ×{r['hike_2008']:.2f} (obs ×{r['obs_2008']:.2f})  "
              f"2010 ×{r['hike_2010']:.2f} (obs ×{r['obs_2010']:.2f})")

    report = [
        "# Gate 1 report",
        "",
        "Sensitivity band σ ∈ {0, 0.3, 0.6}, not a 2008 fit. "
        "See `diagnostics/GATE1_PLAN.md`.",
        "",
        "## Identity",
        "",
        "Coupled σ=0 vs independent Gate 0: **PASS**.",
        "",
        "## Official-split prices (full = harvest + AMIS)",
        "",
        "| Grain | σ | corr | 2008 model / obs | 2010 model / obs |",
        "|---|---:|---:|---:|---:|",
    ]
    for _, r in full.iterrows():
        report.append(
            f"| {r['grain']} | {r['subst_scale']:g} | {r['corr']:+.3f} | "
            f"×{r['hike_2008']:.2f} / ×{r['obs_2008']:.2f} | "
            f"×{r['hike_2010']:.2f} / ×{r['obs_2010']:.2f} |"
        )

    print("\nSpillover sign 2007/08 (σ>0 hike / σ=0 hike, full leg):")
    report += ["", "## Hard bar: spillover sign (2007/08 full hike vs σ=0)", ""]
    off = full[full.subst_scale == 0.0].set_index("grain")
    sign_ok = True
    for s in (0.3, 0.6):
        on = full[full.subst_scale == s].set_index("grain")
        for g in COUPLED_GRAINS:
            ratio = float(on.loc[g, "hike_2008"] / off.loc[g, "hike_2008"])
            if g == "wheat":
                flag = "—"
            elif ratio >= 0.995:
                flag = "ok"
            else:
                flag = "FAIL sign"
                sign_ok = False
            print(f"  {g:5s} σ={s:g}  ×{ratio:.3f}  {flag}")
            report.append(f"- {g} σ={s:g}: ×{ratio:.3f}  {flag}")
    report.append("")
    report.append("**Spillover sign:** " + ("PASS" if sign_ok else "FAIL"))

    print("\nWheat attribution (isolated shocks vs tau):")
    report += ["", "## Hard bar: wheat Gate 0 attribution signs", ""]
    wheat_ok = True
    for s in SCALES:
        sh = float(met[(met.grain == "wheat") & (met.subst_scale == s)
                       & (met.leg == "shocks")].hike_2008.iloc[0])
        tau = float(met[(met.grain == "wheat") & (met.subst_scale == s)
                        & (met.leg == "tau")].hike_2008.iloc[0])
        sh10 = float(met[(met.grain == "wheat") & (met.subst_scale == s)
                         & (met.leg == "shocks")].hike_2010.iloc[0])
        tau10 = float(met[(met.grain == "wheat") & (met.subst_scale == s)
                          & (met.leg == "tau")].hike_2010.iloc[0])
        lead08 = "restriction" if tau > sh else "production"
        lead10 = "production" if sh10 > tau10 else "restriction"
        ok08 = lead08 == "restriction"
        ok10 = lead10 == "production"
        flag = "ok" if (ok08 and ok10) else "FAIL"
        if flag == "FAIL":
            wheat_ok = False
        print(f"  σ={s:g}  2008 {lead08}-led (tau×{tau:.2f} shocks×{sh:.2f})  "
              f"2010 {lead10}-led (shocks×{sh10:.2f} tau×{tau10:.2f})  {flag}")
        report.append(
            f"- σ={s:g}: 2008 {lead08}-led (tau×{tau:.2f}, shocks×{sh:.2f}); "
            f"2010 {lead10}-led (shocks×{sh10:.2f}, tau×{tau10:.2f})  {flag}"
        )
    report.append("")
    report.append("**Wheat attribution:** " + ("PASS" if wheat_ok else "FAIL"))

    print("\nRice AMIS share of 2008 hike ((tau−1)/(full−1)):")
    report += ["", "## Hard bar: rice AMIS still carries most of 2008 rice hike",
               ""]
    rice_ok = True
    for s in SCALES:
        full_h = float(met[(met.grain == "rice") & (met.subst_scale == s)
                           & (met.leg == "full")].hike_2008.iloc[0])
        tau_h = float(met[(met.grain == "rice") & (met.subst_scale == s)
                          & (met.leg == "tau")].hike_2008.iloc[0])
        sh_h = float(met[(met.grain == "rice") & (met.subst_scale == s)
                         & (met.leg == "shocks")].hike_2008.iloc[0])
        share = (tau_h - 1.0) / (full_h - 1.0) if full_h != 1.0 else float("nan")
        flag = "ok" if (share >= 0.5 and tau_h >= sh_h) else "FAIL"
        if flag == "FAIL":
            rice_ok = False
        print(f"  σ={s:g}  tau×{tau_h:.2f}  shocks×{sh_h:.2f}  full×{full_h:.2f}  "
              f"AMIS share {share:.0%}  {flag}")
        report.append(
            f"- σ={s:g}: tau×{tau_h:.2f}, shocks×{sh_h:.2f}, full×{full_h:.2f}, "
            f"AMIS share {share:.0%}  {flag}"
        )
    report.append("")
    report.append("**Rice AMIS dominance:** " + ("PASS" if rice_ok else "FAIL"))

    print("\nSoft: Δhike vs σ=0 (full). Maize = least-confounded; "
          "rice 2008 = hold-out / own-ban; rice 2010 must not invent a co-spike.")
    report += ["", "## Soft (do not select σ* on these)", ""]
    for s in (0.3, 0.6):
        on = full[full.subst_scale == s].set_index("grain")
        for g in COUPLED_GRAINS:
            d08 = float(on.loc[g, "hike_2008"] - off.loc[g, "hike_2008"])
            d10 = float(on.loc[g, "hike_2010"] - off.loc[g, "hike_2010"])
            dc = float(on.loc[g, "corr"] - off.loc[g, "corr"])
            print(f"  {g:5s} σ={s:g}  Δcorr={dc:+.3f}  "
                  f"Δ2008={d08:+.3f}  Δ2010={d10:+.3f}")
            report.append(
                f"- {g} σ={s:g}: Δcorr={dc:+.3f}, Δ2008={d08:+.3f}, "
                f"Δ2010={d10:+.3f}"
            )
    rice10_06 = float(full[(full.grain == "rice") & (full.subst_scale == 0.6)
                           ].hike_2010.iloc[0])
    rice10_0 = float(off.loc["rice", "hike_2010"])
    rice10_obs = float(off.loc["rice", "obs_2010"])
    report.append("")
    report.append(
        f"Rice 2010 observed ×{rice10_obs:.2f} (<1). Model σ=0 ×{rice10_0:.2f}, "
        f"σ=0.6 ×{rice10_06:.2f}. A large σ-driven rice co-spike in 2010/11 "
        "would be a miss against the data, not a substitution win."
    )
    report += [
        "",
        "No σ* selected. Band is the result.",
        "",
        f"Figure: `{FIGS / 'fig_gate1_substitution.png'}`.",
        f"Table: `{DIAG / 'gate1_score.csv'}`.",
    ]
    (DIAG / "gate1_report.md").write_text("\n".join(report) + "\n")
    print(f"\nwrote {FIGS / 'fig_gate1_substitution.png'}")
    print(f"wrote {DIAG / 'gate1_score.csv'}")
    print(f"wrote {DIAG / 'gate1_report.md'}")


if __name__ == "__main__":
    main()
