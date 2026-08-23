#!/usr/bin/env python3
"""Score Level-1 vs Pink Sheet — with Agrimate-style attribution legs.

Gate 0 (VALIDATION.md): reproduce historical / Agrimate crisis targets before
any Level-2 work. Always runs three counterfactuals (no endogenous game):

  full     — PSD anomalies + AMIS τ (Agrimate severity)
  shocks   — PSD anomalies only (τ=0)
  tau      — AMIS τ only (ξ=1)

Default calibration is **crisis-era** (PSD 2004–2006 means + stocks seeded
from 2005 endings). See diagnostics/LEVEL1_INTERROGATION.md.

Example:
  python scripts/score_level1.py
  python scripts/score_level1.py --severity prototype   # legacy mild τ
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from sheaf import SheafModel, build_countries
from sheaf.data_usda import (
    amis_tau_schedule,
    country_production_shocks,
    load_price_series,
    seed_stocks_from_psd,
)

ROOT = Path(__file__).resolve().parents[1]
DIAG = ROOT / "diagnostics"
FIGS = ROOT / "figures"
COL = {"wheat": "#c0392b", "rice": "#2874a6", "maize": "#d68910"}
CRISES = [(2007.5, 2008.5), (2010.5, 2011.5)]
HIKE_WINDOWS = {
    "2007/08": {"base": 2006, "peak": 2008},
    "2010/11": {"base": 2009, "peak": 2011},
}
# Crisis-era baseline (Gate 0) — NOT 2019–21
DEFAULT_BASELINE = (2004, 2005, 2006)


def _build(baseline_years, stock_year: int):
    countries, transport, grains, freight = build_countries(
        substitution=True, quantities="usda", baseline_years=baseline_years)
    seed_stocks_from_psd(countries, stock_year)
    return countries, transport, grains, freight


def run_leg(years, shocks, taus, baseline_years, stock_year):
    countries, transport, grains, freight = _build(baseline_years, stock_year)
    model = SheafModel(countries, transport, grains, freight_mult=freight,
                       play_game=False)
    df = model.run(len(years), shocks=shocks, tau_schedule=taus)
    df["year"] = df["period"].map(lambda t: years[t])
    return (df.groupby(["year", "grain"], as_index=False)["importer_price"]
              .mean()
              .rename(columns={"importer_price": "model_price"}))


def score_vs_obs(model_px: pd.DataFrame, obs: pd.DataFrame, leg: str) -> pd.DataFrame:
    obs_long = (obs.reset_index()
                  .melt(id_vars="year", var_name="grain", value_name="obs_price"))
    m = model_px.merge(obs_long, on=["year", "grain"], how="left")
    m = m.sort_values(["grain", "year"])
    m["leg"] = leg
    m["model_yoy_pct"] = m.groupby("grain")["model_price"].pct_change() * 100
    m["obs_yoy_pct"] = m.groupby("grain")["obs_price"].pct_change() * 100
    return m


def hike_summary(score: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for leg, sleg in score.groupby("leg"):
        for label, w in HIKE_WINDOWS.items():
            for grain in ("wheat", "rice", "maize"):
                sub = sleg[(sleg.grain == grain)
                           & (sleg.year.isin([w["base"], w["peak"]]))]
                if sub.year.nunique() < 2:
                    continue
                mb = float(sub.loc[sub.year == w["base"], "model_price"].iloc[0])
                mp = float(sub.loc[sub.year == w["peak"], "model_price"].iloc[0])
                ob = float(sub.loc[sub.year == w["base"], "obs_price"].iloc[0])
                op = float(sub.loc[sub.year == w["peak"], "obs_price"].iloc[0])
                rows.append(dict(
                    leg=leg, window=label, grain=grain,
                    model_hike_ratio=mp / mb if mb else np.nan,
                    obs_hike_ratio=op / ob if ob else np.nan,
                    sign_match=bool(np.sign(mp - mb) == np.sign(op - ob)),
                ))
    return pd.DataFrame(rows)


def plot_attribution(score: pd.DataFrame, hikes: pd.DataFrame, out: Path):
    grains = ["wheat", "rice", "maize"]
    legs = ["full", "shocks", "tau"]
    styles = {"full": ("o-", "0.15"), "shocks": ("s--", "#6c3483"),
              "tau": ("^-.", "#1e8449")}
    fig, axes = plt.subplots(2, 3, figsize=(13, 7.5))
    for j, grain in enumerate(grains):
        ax = axes[0, j]
        sub_o = score[(score.leg == "full") & (score.grain == grain)].sort_values("year")
        ax.plot(sub_o.year, sub_o.obs_price, "o-", color=COL[grain],
                label="Pink Sheet real", lw=2)
        for leg in legs:
            sub = score[(score.leg == leg) & (score.grain == grain)].sort_values("year")
            fmt, color = styles[leg]
            ax.plot(sub.year, sub.model_price, fmt, color=color, label=f"L1 {leg}",
                    lw=1.2, ms=5)
        for a, b in CRISES:
            ax.axvspan(a, b, color="0.92", zorder=0)
        ax.set_title(f"{grain} $/t")
        if j == 0:
            ax.legend(fontsize=7)
            ax.set_ylabel("$/t")

        ax = axes[1, j]
        width = 0.25
        sub = score[(score.leg == "full") & (score.grain == grain)].sort_values("year")
        x = np.asarray(sub.year, float)
        ax.bar(x - width, sub.obs_yoy_pct, width, color=COL[grain], label="obs", alpha=0.85)
        for k, leg in enumerate(legs):
            s = score[(score.leg == leg) & (score.grain == grain)].sort_values("year")
            ax.bar(x + (k - 0.5) * width * 0.0 + (k) * width * 0.35,
                   s.model_yoy_pct, width * 0.7, label=leg, alpha=0.75,
                   color=styles[leg][1])
        ax.axhline(0, color="0.7", lw=0.7)
        for a, b in CRISES:
            ax.axvspan(a, b, color="0.92", zorder=0)
        ax.set_title(f"{grain} YoY %")
        if j == 0:
            ax.legend(fontsize=7)
            ax.set_ylabel("%")

    # Gate summary from wheat hikes
    bits = []
    for _, r in hikes[(hikes.grain == "wheat")].iterrows():
        bits.append(f"{r.leg} {r.window}: ×{r.model_hike_ratio:.2f}"
                    f"{' OK' if r.sign_match else ' MISS'}")
    fig.suptitle(
        "Level-1 Gate 0 attribution (play_game=False, crisis-era baseline)\n"
        + " | ".join(bits[:6]),
        fontsize=9)
    fig.tight_layout()
    fig.savefig(out, dpi=130)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--years", nargs="+", type=int,
                    default=[2006, 2007, 2008, 2009, 2010, 2011])
    ap.add_argument("--baseline-years", nargs="+", type=int,
                    default=list(DEFAULT_BASELINE))
    ap.add_argument("--stock-year", type=int, default=2005)
    ap.add_argument("--severity", choices=("agrimate", "prototype"),
                    default="agrimate")
    args = ap.parse_args()
    years = list(args.years)
    baseline = tuple(args.baseline_years)

    DIAG.mkdir(parents=True, exist_ok=True)
    FIGS.mkdir(parents=True, exist_ok=True)

    countries, _, grains, _ = _build(baseline, args.stock_year)
    n = len(countries)
    shocks = country_production_shocks(countries, grains, years)
    taus = amis_tau_schedule(countries, grains, years, severity=args.severity)
    ones = {t: np.ones((n, len(grains))) for t in range(len(years))}

    print(f"Gate 0 Level-1 score  years={years}")
    print(f"  baseline_years={baseline}  stock_year={args.stock_year}  "
          f"severity={args.severity}  play_game=False")

    obs = load_price_series(deflated=True)
    pieces = []
    for leg, sh, ta in [
        ("full", shocks, taus),
        ("shocks", shocks, {}),
        ("tau", ones, taus),
    ]:
        print(f"  running leg={leg}…")
        px = run_leg(years, sh, ta, baseline, args.stock_year)
        pieces.append(score_vs_obs(px, obs, leg))
    score = pd.concat(pieces, ignore_index=True)
    hikes = hike_summary(score)

    score_path = DIAG / "level1_price_score.csv"
    hike_path = DIAG / "level1_price_hikes.csv"
    fig_path = FIGS / "fig10_level1_price_score.png"
    score.to_csv(score_path, index=False)
    hikes.to_csv(hike_path, index=False)
    plot_attribution(score, hikes, fig_path)

    print(f"\nwrote {score_path}")
    print(f"wrote {hike_path}")
    print(f"wrote {fig_path}")
    print("\nWheat hike ratios (Gate 0):")
    print(hikes[hikes.grain == "wheat"][
        ["leg", "window", "model_hike_ratio", "obs_hike_ratio", "sign_match"]]
        .to_string(index=False))

    # Acceptance: tau leg must match signs; full may still miss 2007/08 (documented)
    tau_ok = hikes[(hikes.leg == "tau") & (hikes.grain == "wheat")]["sign_match"].all()
    print(f"\nGATE tau-only wheat signs: {'PASS' if tau_ok else 'FAIL'}")
    full_ok = hikes[(hikes.leg == "full") & (hikes.grain == "wheat")]["sign_match"].all()
    print(f"GATE full wheat signs:     {'PASS' if full_ok else 'FAIL (see interrogation)'}")


if __name__ == "__main__":
    main()
