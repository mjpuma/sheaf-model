#!/usr/bin/env python3
"""Gate 1 E6: 2021–23 Ukraine-war hold-out on the frozen σ band.

Same flags as scripts/score_ukraine_war.py. Do not re-select σ.
See overleaf/gate1_substitution/sections/next.tex.
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
from sheaf.dynamic_coupled import COUPLED_GRAINS, run_coupled_dynamics
from sheaf.dynamic_crop import result_to_monthly, run_crop_dynamics
from score_subannual_crop import _corr, _hike

DIAG = ROOT / "diagnostics"
FIGS = ROOT / "figures"
START, END = 2021, 2023
HIKE = (2021, 6, 2022, 5)
SCALES = (0.0, 0.3, 0.6)
WIN = dict(
    start_year=START, end_year=END,
    stock_seed_year=2020, spin_up_years=2,
    trade_window=(2019, 2021),
)
LEGS = {
    "full": dict(use_amis=True, use_shocks=True, use_demand=False),
    "shocks": dict(use_amis=False, use_shocks=True, use_demand=False),
    "tau": dict(use_amis=True, use_shocks=False, use_demand=False,
                use_industrial=False),
}


def _monthly(coupled, grain: str) -> pd.DataFrame:
    return result_to_monthly(coupled.by_crop[grain])


def main():
    DIAG.mkdir(parents=True, exist_ok=True)
    FIGS.mkdir(parents=True, exist_ok=True)
    pink = load_price_series_monthly(deflated=True)
    pink = pink[(pink.year >= START) & (pink.year <= END)]
    p0 = {g: float(pink[pink.year == 2021][g].mean()) for g in COUPLED_GRAINS}

    print("E6 identity: coupled σ=0 vs Gate 0 Ukraine full...")
    coupled0 = run_coupled_dynamics(subst_scale=0.0, p0=p0, **WIN, **LEGS["full"])
    id_ok = True
    for g in COUPLED_GRAINS:
        solo = run_crop_dynamics(
            g, p0=p0[g], **WIN, use_amis=True, use_shocks=True,
            use_demand=False)
        a = result_to_monthly(coupled0.by_crop[g])["model_price"].to_numpy()
        b = result_to_monthly(solo)["model_price"].to_numpy()
        rel = float(np.max(np.abs(a - b) / np.maximum(np.abs(b), 1.0)))
        flag = "ok" if rel <= 0.005 else "FAIL"
        if flag == "FAIL":
            id_ok = False
        print(f"  {g:5s} max rel |Δp|={rel:.2e}  {flag}")

    runs = {(0.0, "full"): coupled0}
    for s in SCALES:
        for leg, flags in LEGS.items():
            if (s, leg) in runs:
                continue
            print(f"  run σ={s:g}  {leg}...")
            runs[(s, leg)] = run_coupled_dynamics(
                subst_scale=s, p0=p0, **WIN, **flags)

    rows = []
    monthly = []
    fig, axes = plt.subplots(3, 1, figsize=(10.5, 9.2), sharex=True)
    styles = {0.0: ("--", "#6c3483"), 0.3: ("-.", "#1e8449"),
              0.6: ("-", "0.15")}
    for ax, g in zip(axes, COUPLED_GRAINS):
        obs = pink[["year", "month", g]].rename(columns={g: "obs_price"})
        x = None
        for s in SCALES:
            for leg in LEGS:
                m = _monthly(runs[(s, leg)], g).merge(
                    obs, on=["year", "month"], how="left")
                m["grain"] = g
                m["subst_scale"] = s
                m["leg"] = leg
                monthly.append(m)
                rec = dict(grain=g, subst_scale=s, leg=leg, p0=p0[g])
                rec["corr"] = _corr(m.model_price, m.obs_price)
                rec["hike"] = _hike(m, "model_price", *HIKE)
                rec["obs_hike"] = _hike(obs, "obs_price", *HIKE)
                rows.append(rec)
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
        ax.set_title(g.capitalize() + " 2021–23")
        ax.legend(fontsize=7, ncol=4)
        ticks = [i for i, mo in enumerate(m.month) if mo == 1]
        ax.set_xticks(ticks, [str(int(m.year.iloc[i])) for i in ticks])

    fig.suptitle("Gate 1 E6: Ukraine-war window, frozen σ band")
    fig.tight_layout()
    fig.savefig(FIGS / "fig_gate1_e6_ukraine.png", dpi=140)
    plt.close(fig)

    met = pd.DataFrame(rows)
    met.to_csv(DIAG / "gate1_e6_score.csv", index=False)
    pd.concat(monthly, ignore_index=True).to_csv(
        DIAG / "gate1_e6_monthly.csv", index=False)

    full = met[met.leg == "full"]
    print("\nOfficial split (full), Jun-2021 → May-2022 hike:")
    for _, r in full.iterrows():
        print(f"  {r['grain']:5s} σ={r['subst_scale']:g}  "
              f"corr={r['corr']:+.3f}  "
              f"hike ×{r['hike']:.2f} (obs ×{r['obs_hike']:.2f})")

    off = full[full.subst_scale == 0.0].set_index("grain")
    spike_ok = True
    print("\nInvented co-spike? (maize/rice hike vs σ=0 and vs obs):")
    for s in (0.3, 0.6):
        on = full[full.subst_scale == s].set_index("grain")
        for g in ("maize", "rice"):
            h0 = float(off.loc[g, "hike"])
            h = float(on.loc[g, "hike"])
            obs_h = float(off.loc[g, "obs_hike"])
            # Invented if substitution pushes a near-flat grain well above
            # both Gate 0 and the data.
            invented = (h > 1.20) and (h > max(obs_h, h0) + 0.10)
            flag = "FAIL invented" if invented else "ok"
            if invented:
                spike_ok = False
            print(f"  {g:5s} σ={s:g}  ×{h:.3f}  (σ=0 ×{h0:.3f}, obs ×{obs_h:.3f})  {flag}")

    print("\nWheat AMIS-led (tau hike > shocks hike):")
    wheat_ok = True
    for s in SCALES:
        sh = float(met[(met.grain == "wheat") & (met.subst_scale == s)
                       & (met.leg == "shocks")].hike.iloc[0])
        tau = float(met[(met.grain == "wheat") & (met.subst_scale == s)
                        & (met.leg == "tau")].hike.iloc[0])
        flag = "ok" if tau > sh else "FAIL"
        if flag == "FAIL":
            wheat_ok = False
        print(f"  σ={s:g}  tau×{tau:.2f}  shocks×{sh:.2f}  {flag}")

    report = [
        "# Gate 1 E6 — 2021–23 Ukraine-war hold-out",
        "",
        "Frozen band σ ∈ {0, 0.3, 0.6}. Same flags as Gate 0 Ukraine:",
        "2021–23, stock seed 2020, FAOSTAT 2019–21, p0 = 2021 Pink Sheet mean.",
        "No σ* selected.",
        "",
        f"Identity σ=0 vs Gate 0: **{'PASS' if id_ok else 'FAIL'}**.",
        f"Maize/rice invented co-spike: **{'PASS (none)' if spike_ok else 'FAIL'}**.",
        f"Wheat AMIS-led: **{'PASS' if wheat_ok else 'FAIL'}**.",
        "",
        "## Official-split prices (full = harvest + AMIS)",
        "",
        "| Grain | σ | corr | hike model / obs |",
        "|---|---:|---:|---:|",
    ]
    for _, r in full.iterrows():
        report.append(
            f"| {r['grain']} | {r['subst_scale']:g} | {r['corr']:+.3f} | "
            f"×{r['hike']:.2f} / ×{r['obs_hike']:.2f} |"
        )
    report += [
        "",
        "## Soft Δ vs σ=0 (do not select on)",
        "",
    ]
    for s in (0.3, 0.6):
        on = full[full.subst_scale == s].set_index("grain")
        for g in COUPLED_GRAINS:
            dh = float(on.loc[g, "hike"] - off.loc[g, "hike"])
            dc = float(on.loc[g, "corr"] - off.loc[g, "corr"])
            report.append(
                f"- {g} σ={s:g}: Δcorr={dc:+.3f}, Δhike={dh:+.3f}"
            )
    report += [
        "",
        "Figure: `figures/fig_gate1_e6_ukraine.png`.",
        "Table: `diagnostics/gate1_e6_score.csv`.",
    ]
    (DIAG / "gate1_e6_report.md").write_text("\n".join(report) + "\n")
    print(f"\nwrote {FIGS / 'fig_gate1_e6_ukraine.png'}")
    print(f"wrote {DIAG / 'gate1_e6_score.csv'}")
    print(f"wrote {DIAG / 'gate1_e6_report.md'}")


if __name__ == "__main__":
    main()
