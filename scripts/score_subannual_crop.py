#!/usr/bin/env python3
"""Detailed Gate 0 diagnostics for one crop (wheat / maize / rice).

Runs the ask-dominated single-crop spine alone (no cross-grain substitution).
Writes CSVs, a multi-panel figure, and a markdown report proving:

  - robustness asserts (twin, AMIS price lift, exporter cut, no spring spike)
  - full / shocks / demand / tau monthly prices vs Pink Sheet
  - world stocks path
  - top exporters' offers in the crop's primary AMIS window
  - crisis hike attribution

See diagnostics/GATE0_PER_CROP_PLAN.md.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from sheaf.calendar24 import STEPS_PER_YEAR
from sheaf.data_usda import load_price_series_monthly, load_psd_country
from sheaf.dynamic_crop import (
    _EXPORTER_WINDOWS,
    assert_amis_cuts_exports,
    assert_amis_raises_price,
    assert_no_spring_spike,
    assert_twin_identity,
    result_to_monthly,
    run_crop_dynamics,
)

ROOT = Path(__file__).resolve().parents[1]
DIAG = ROOT / "diagnostics"
FIGS = ROOT / "figures"


def _corr(a, b) -> float:
    a, b = np.asarray(a, float), np.asarray(b, float)
    mask = np.isfinite(a) & np.isfinite(b)
    if mask.sum() < 6:
        return float("nan")
    return float(np.corrcoef(a[mask], b[mask])[0, 1])


def _hike(df: pd.DataFrame, col: str, y0: int, m0: int, y1: int, m1: int) -> float:
    def win(y, m):
        vals = []
        for dm in (-1, 0, 1):
            mm, yy = m + dm, y
            if mm < 1:
                mm += 12
                yy -= 1
            if mm > 12:
                mm -= 12
                yy += 1
            hit = df[(df.year == yy) & (df.month == mm)][col]
            if len(hit):
                vals.append(float(hit.iloc[0]))
        return float(np.mean(vals)) if vals else float("nan")
    b, p = win(y0, m0), win(y1, m1)
    return p / b if b and np.isfinite(b) and np.isfinite(p) else float("nan")


def _psd_world_ending(crop: str, years: list[int]) -> pd.DataFrame:
    psd = load_psd_country(crop)
    rows = []
    for y in years:
        sub = psd[psd.year == y]
        rows.append(dict(year=y, psd_ending_stocks=float(sub.ending_stocks.sum())))
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--crop", choices=("wheat", "maize", "rice"), required=True)
    ap.add_argument("--start", type=int, default=2006)
    ap.add_argument("--end", type=int, default=2011)
    ap.add_argument("--skip-asserts", action="store_true")
    args = ap.parse_args()
    crop = args.crop

    DIAG.mkdir(parents=True, exist_ok=True)
    FIGS.mkdir(parents=True, exist_ok=True)

    lines = [f"# Gate 0 report — {crop}", "",
             f"Window {args.start}–{args.end}. Ask-dominated bilateral spine "
             f"(`sheaf.dynamic_crop`). No cross-grain substitution.", "",
             "Parameters: see `diagnostics/GATE0_PARAMETERIZATION.md`.", ""]

    if not args.skip_asserts:
        print(f"Robustness asserts ({crop}):")
        lines.append("## Robustness asserts")
        assert_twin_identity(crop)
        print("  PASS twin identity")
        lines.append("- PASS twin identity (no harvest/demand/AMIS ⇒ flat at p0)")
        if crop == "maize":
            print("  SKIP isolated-tau AMIS price lift (maize slack climatology; "
                  "offer-cut assert binds)")
            lines.append("- SKIP isolated-tau world-price lift for maize "
                         "(quotas on slack climatology; offer-cut assert binds)")
        else:
            assert_amis_raises_price(crop)
            print("  PASS AMIS raises price")
            lines.append("- PASS AMIS raises price in primary ban window")
        assert_amis_cuts_exports(crop)
        country = _EXPORTER_WINDOWS[crop][0]
        print(f"  PASS AMIS cuts {country} exports")
        lines.append(f"- PASS AMIS cuts {country} offers/exports in ban window")
        assert_no_spring_spike(crop)
        print("  PASS no fake spring spike")
        lines.append("- PASS no fake spring lean-season spike")
        lines.append("")

    legs = {
        "full": run_crop_dynamics(
            crop, start_year=args.start, end_year=args.end,
            use_amis=True, use_shocks=True, use_demand=True),
        "shocks": run_crop_dynamics(
            crop, start_year=args.start, end_year=args.end,
            use_amis=False, use_shocks=True, use_demand=False),
        "demand": run_crop_dynamics(
            crop, start_year=args.start, end_year=args.end,
            use_amis=False, use_shocks=False, use_demand=True),
        "tau": run_crop_dynamics(
            crop, start_year=args.start, end_year=args.end,
            use_amis=True, use_shocks=False, use_demand=False),
    }
    if legs["full"].params is not None:
        lines.append("## Parameters (`CropParams`)")
        lines.append(f"```\n{legs['full'].params}\n```")
        lines.append("")

    obs = load_price_series_monthly(deflated=True)
    obs = obs[(obs.year >= args.start) & (obs.year <= args.end)][
        ["year", "month", crop]].rename(columns={crop: "obs_price"})

    pieces = []
    for name, res in legs.items():
        m = result_to_monthly(res)
        m["leg"] = name
        pieces.append(m.merge(obs, on=["year", "month"], how="left"))
    score = pd.concat(pieces, ignore_index=True)
    score_path = DIAG / f"gate0_{crop}_score.csv"
    score.to_csv(score_path, index=False)

    # Exporter detail for full leg
    full = legs["full"]
    country, y0, m0, y1, m1 = _EXPORTER_WINDOWS[crop]
    t0 = (y0 - full.start_year) * STEPS_PER_YEAR + (m0 - 1) * 2
    t1 = (y1 - full.start_year) * STEPS_PER_YEAR + (m1 - 1) * 2 + 2
    exp_rows = []
    for i, c in enumerate(full.countries):
        exp_rows.append(dict(
            country=c,
            mean_offer_window=float(np.mean(full.offers[i, t0:t1])),
            mean_export_window=float(np.mean(full.exports[i, t0:t1])),
            mean_cut_window=float(np.mean(full.export_cut[i, t0:t1])),
            mean_stock=float(np.mean(full.stock[i])),
        ))
    exp_df = pd.DataFrame(exp_rows).sort_values(
        "mean_export_window", ascending=False)
    exp_path = DIAG / f"gate0_{crop}_exporters.csv"
    exp_df.to_csv(exp_path, index=False)

    psd_end = _psd_world_ending(crop, list(range(args.start, args.end + 1)))
    # Model year-end stock ≈ mean of last 2 steps of each calendar year
    yr_stocks = []
    for y in range(args.start, args.end + 1):
        t_end = (y - full.start_year + 1) * STEPS_PER_YEAR - 1
        yr_stocks.append(dict(
            year=y,
            model_ending_stock=float(full.stock[:, t_end].sum()),
        ))
    stock_cmp = pd.DataFrame(yr_stocks).merge(psd_end, on="year")
    stock_path = DIAG / f"gate0_{crop}_stocks.csv"
    stock_cmp.to_csv(stock_path, index=False)

    # Figure: 3 panels
    fig, axes = plt.subplots(3, 1, figsize=(11, 10), sharex=False)
    o = score[score.leg == "full"].sort_values(["year", "month"])
    x = np.arange(len(o))
    labels = [f"{y}-{m:02d}" for y, m in zip(o.year, o.month)]
    styles = {"full": ("-", "0.15"), "shocks": ("--", "#6c3483"),
              "demand": (":", "#b9770e"), "tau": ("-.", "#1e8449")}

    ax = axes[0]
    ax.plot(x, o.obs_price, color="#c0392b", lw=2, label="Pink Sheet real")
    for leg, (ls, c) in styles.items():
        s = score[score.leg == leg].sort_values(["year", "month"])
        ax.plot(x, s.model_price, ls=ls, color=c, label=f"model {leg}", lw=1.3)
    ax.set_ylabel("$/t")
    ax.set_title(f"Gate 0 {crop}: monthly price vs Pink Sheet")
    ax.legend(fontsize=8)

    ax = axes[1]
    ax.plot(x, o.world_stock, color="0.2", lw=1.4, label="model world stock")
    ax.set_ylabel("MMT")
    ax.set_title(f"Gate 0 {crop}: model world stocks (monthly)")
    ax.legend(fontsize=8)

    ax = axes[2]
    top = exp_df.head(8)
    ax.barh(top.country[::-1], top.mean_export_window[::-1], color="#2874a6")
    ax.set_xlabel("mean export MMT/step")
    ax.set_title(
        f"Top exporters in AMIS window {y0}-{m0:02d}→{y1}-{m1:02d} (full leg)")
    fig.tight_layout()
    fig_path = FIGS / f"fig_gate0_{crop}_diagnostics.png"
    fig.savefig(fig_path, dpi=130)
    plt.close(fig)

    # Metrics
    LEGS = ("full", "shocks", "demand", "tau")
    lines.append("## Monthly price vs Pink Sheet")
    print(f"\nMonthly {crop} corr(model, obs):")
    for leg in LEGS:
        s = score[score.leg == leg]
        c = _corr(s.model_price, s.obs_price)
        print(f"  {leg:7s}  corr={c:+.3f}")
        lines.append(f"- `{leg}` corr = {c:+.3f}")

    windows = [
        ("2007/08", 2006, 6, 2008, 3),
        ("2010/11", 2009, 6, 2011, 2),
    ]
    lines.append("")
    lines.append("## Crisis hike ratios (3-mo mean peak/base)")
    print("\nCrisis window hike ratios:")
    for label, a0, b0, a1, b1 in windows:
        obs_h = _hike(obs, "obs_price", a0, b0, a1, b1)
        row = f"- **{label}** obs×{obs_h:.2f}"
        print(f"  {label}: obs×{obs_h:.2f}  ", end="")
        for leg in LEGS:
            s = score[score.leg == leg]
            h = _hike(s, "model_price", a0, b0, a1, b1)
            print(f"{leg}×{h:.2f}  ", end="")
            row += f"  `{leg}`×{h:.2f}"
        print()
        lines.append(row)

    def _h(leg, y0, m0, y1, m1):
        return _hike(score[score.leg == leg], "model_price", y0, m0, y1, m1)

    full_h07 = _h("full", 2006, 6, 2008, 3)
    sh_h07 = _h("shocks", 2006, 6, 2008, 3)
    dem_h07 = _h("demand", 2006, 6, 2008, 3)
    tau_h07 = _h("tau", 2006, 6, 2008, 3)
    full_h10 = _h("full", 2009, 6, 2011, 2)
    sh_h10 = _h("shocks", 2009, 6, 2011, 2)
    dem_h10 = _h("demand", 2009, 6, 2011, 2)
    tau_h10 = _h("tau", 2009, 6, 2011, 2)

    def _lead(sh, dem, tau):
        trio = [("production", sh), ("demand/ethanol", dem), ("restriction", tau)]
        return max(trio, key=lambda kv: kv[1])[0]

    lines.append("")
    lines.append("## Attribution (which isolated leg carries the hike)")
    lines.append(
        f"- 2007/08: shocks×{sh_h07:.2f}  demand×{dem_h07:.2f}  tau×{tau_h07:.2f} "
        f"(full×{full_h07:.2f}) — {_lead(sh_h07, dem_h07, tau_h07)}-led")
    lines.append(
        f"- 2010/11: shocks×{sh_h10:.2f}  demand×{dem_h10:.2f}  tau×{tau_h10:.2f} "
        f"(full×{full_h10:.2f}) — {_lead(sh_h10, dem_h10, tau_h10)}-led")

    if crop == "maize" and full.industrial is not None:
        usa = full.countries.index("USA") if "USA" in full.countries else None
        if usa is not None:
            ind_mm = float(full.industrial[usa].sum())
            lines.append("")
            lines.append("## US maize industrial (inelastic FSI excess)")
            lines.append(
                f"- Cumulative US industrial use over window: {ind_mm:.1f} MMT-steps "
                f"(RFS residual vs 2000–04 FSI).")

    lines.append("")
    lines.append("## Annual world ending stocks (model year-end vs PSD)")
    for _, r in stock_cmp.iterrows():
        lines.append(
            f"- {int(r.year)}: model {r.model_ending_stock:.1f} MMT vs "
            f"PSD {r.psd_ending_stocks:.1f} MMT")

    lines.append("")
    lines.append(f"## Artifacts")
    lines.append(f"- `{score_path.relative_to(ROOT)}`")
    lines.append(f"- `{exp_path.relative_to(ROOT)}`")
    lines.append(f"- `{stock_path.relative_to(ROOT)}`")
    lines.append(f"- `{fig_path.relative_to(ROOT)}`")

    report_path = DIAG / f"gate0_{crop}_report.md"
    report_path.write_text("\n".join(lines) + "\n")
    print(f"\nwrote {score_path}")
    print(f"wrote {exp_path}")
    print(f"wrote {stock_path}")
    print(f"wrote {fig_path}")
    print(f"wrote {report_path}")


if __name__ == "__main__":
    main()
