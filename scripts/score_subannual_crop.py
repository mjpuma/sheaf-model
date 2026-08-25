#!/usr/bin/env python3
"""Detailed Gate 0 diagnostics for one crop (wheat / maize / rice).

Runs the ask-dominated single-crop spine alone (no cross-grain substitution).
Writes CSVs, a multi-panel figure, and a markdown report proving:

  - robustness asserts (twin, AMIS price lift, exporter cut, no spring spike)
  - full / shocks / demand / tau monthly prices vs Pink Sheet
  - world stocks path (MY-end, FAO-style with/without China)
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
from sheaf.marketing_years import CROP_MY_END_MONTH
from sheaf.dynamic_crop import (
    _EXPORTER_WINDOWS,
    assert_amis_cuts_exports,
    assert_amis_raises_price,
    assert_no_spring_spike,
    assert_twin_identity,
    result_to_monthly,
    run_crop_dynamics,
)

# Named AMIS episodes scored on the official matched split (full vs shocks).
# Coarse P1 signs, not every AMIS row. Assert window is always included.
_SHIPMENT_WINDOWS = {
    "wheat": (
        ("Russia", 2010, 8, 2010, 12, "assert_AugDec2010"),
        ("Ukraine", 2010, 10, 2011, 6, "quota_2010_11"),
    ),
    "maize": (
        ("Argentina", 2007, 5, 2007, 5, "assert_May2007"),
        ("Argentina", 2007, 5, 2008, 1, "quota_May07_Jan08"),
        ("USA", 2007, 5, 2008, 6, "unrestricted_control"),
        ("Ukraine", 2010, 10, 2011, 6, "quota_2010_11"),
    ),
    "rice": (
        ("Vietnam", 2008, 9, 2008, 11, "assert_tax_SepNov2008"),
        ("Vietnam", 2007, 10, 2007, 12, "ban_harvest_overlap"),
        ("India", 2007, 10, 2007, 12, "ban_harvest_overlap"),
        ("Thailand", 2007, 10, 2007, 12, "unrestricted_control"),
        ("India", 2008, 10, 2011, 9, "lingering_prohibition"),
    ),
}

_PSD_EXPORT_NODES = {
    "wheat": ("Russia", "Ukraine", "USA", "Argentina", "Australia",
              "EU", "Kazakhstan", "India"),
    "maize": ("USA", "Argentina", "Brazil", "Ukraine", "EU"),
    "rice": ("India", "Vietnam", "Thailand", "USA", "China"),
}

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


def _step_slice(res, y0: int, m0: int, y1: int, m1: int) -> tuple[int, int]:
    t0 = (y0 - res.start_year) * STEPS_PER_YEAR + (m0 - 1) * 2
    t1 = (y1 - res.start_year) * STEPS_PER_YEAR + (m1 - 1) * 2 + 2
    return t0, t1


def _ratio(a: float, b: float) -> float:
    if b > 1e-9:
        return a / b
    return float("nan") if a < 1e-9 else float("inf")


def shipment_windows(full, shocks, crop: str) -> pd.DataFrame:
    """Official matched (harvest+AMIS) vs harvest-only offers and shipments.

    FAOSTAT E0 is network structure, not observed crisis trade. PSD exports
    are the observed annual bar (marketing-year label as stored).
    """
    rows = []
    windows = list(_SHIPMENT_WINDOWS.get(crop, ()))
    country, y0, m0, y1, m1 = _EXPORTER_WINDOWS[crop]
    tagged = {(c, a, b, d, e) for c, a, b, d, e, _ in windows}
    if (country, y0, m0, y1, m1) not in tagged:
        windows = [(country, y0, m0, y1, m1, "assert_window")] + windows
    for c, a0, b0, a1, b1, lab in windows:
        if c not in full.countries:
            continue
        i = full.countries.index(c)
        t0, t1 = _step_slice(full, a0, b0, a1, b1)
        off_f = float(np.mean(full.offers[i, t0:t1]))
        off_s = float(np.mean(shocks.offers[i, t0:t1]))
        shp_f = float(np.mean(full.exports[i, t0:t1]))
        shp_s = float(np.mean(shocks.exports[i, t0:t1]))
        rows.append(dict(
            crop=crop, country=c, window=lab,
            y0=a0, m0=b0, y1=a1, m1=b1, n_steps=t1 - t0,
            mean_cut=float(np.mean(full.export_cut[i, t0:t1])),
            offer_full=off_f, offer_shocks=off_s,
            offer_ratio=_ratio(off_f, off_s),
            ship_full=shp_f, ship_shocks=shp_s,
            ship_ratio=_ratio(shp_f, shp_s),
            ship_sum_full=float(np.sum(full.exports[i, t0:t1])),
            ship_sum_shocks=float(np.sum(shocks.exports[i, t0:t1])),
        ))
    return pd.DataFrame(rows)


def _fig_shipment_windows(crop: str, df: pd.DataFrame, path: Path) -> None:
    """Official matched AMIS vs harvest-only offer and shipment ratios."""
    if df is None or df.empty:
        return
    labels = [f"{r.country}\n{r.window}" for _, r in df.iterrows()]
    x = np.arange(len(df))
    w = 0.35
    fig, ax = plt.subplots(figsize=(max(7.2, 1.55 * len(df)), 3.5))
    off = np.clip(df.offer_ratio.to_numpy(float), 0, 3)
    shp = np.clip(df.ship_ratio.to_numpy(float), 0, 3)
    ax.bar(x - w / 2, off, w, color="#1f4e79", label="offer AMIS / no-AMIS")
    ax.bar(x + w / 2, shp, w, color="#e67e22", label="ship AMIS / no-AMIS")
    ax.axhline(1.0, color="0.5", lw=0.8)
    ax.set_xticks(x, labels, fontsize=7)
    ax.set_ylabel("ratio (clipped at 3)")
    ax.set_title(f"{crop.capitalize()}: official matched shipment signs")
    ax.legend(frameon=False, loc="upper right", fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def annual_exports_vs_psd(full, shocks, crop: str) -> pd.DataFrame:
    psd = load_psd_country(crop)
    nodes = [c for c in _PSD_EXPORT_NODES.get(crop, full.countries)
             if c in full.countries]
    rows = []
    for c in nodes:
        i = full.countries.index(c)
        psd_c = psd[psd.country == c].set_index("year")["exports"]
        for y in range(full.start_year, full.end_year + 1):
            t0 = (y - full.start_year) * STEPS_PER_YEAR
            t1 = t0 + STEPS_PER_YEAR
            mf = float(full.exports[i, t0:t1].sum())
            ms = float(shocks.exports[i, t0:t1].sum())
            p = float(psd_c.loc[y]) if y in psd_c.index else float("nan")
            p_prev = float(psd_c.loc[y - 1]) if (y - 1) in psd_c.index else float("nan")
            rows.append(dict(
                crop=crop, country=c, year=y,
                model_full=mf, model_shocks=ms, d_amis=mf - ms,
                psd=p,
                model_over_psd=_ratio(mf, p),
                psd_yoy=_ratio(p, p_prev),
            ))
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
        assert_amis_raises_price(crop)
        print("  PASS AMIS raises price")
        lines.append("- PASS AMIS raises price in primary ban window "
                     "(maize: must not cut world price)")
        assert_amis_cuts_exports(crop)
        country = _EXPORTER_WINDOWS[crop][0]
        print(f"  PASS AMIS cuts {country} exports")
        lines.append(f"- PASS AMIS cuts {country} offers in check window"
                     + (" and shipments" if crop == "wheat" else
                        " (shipments not asserted for maize/rice)"))
        assert_no_spring_spike(crop)
        print("  PASS no fake spring spike")
        lines.append("- PASS no fake spring lean-season spike (climatology path)")
        lines.append("")

    legs = {
        # Official P1 matched: harvest + AMIS + mean flex; USA maize industrial on.
        "full": run_crop_dynamics(
            crop, start_year=args.start, end_year=args.end,
            use_amis=True, use_shocks=True, use_demand=False),
        "shocks": run_crop_dynamics(
            crop, start_year=args.start, end_year=args.end,
            use_amis=False, use_shocks=True, use_demand=False),
        # Year-by-year food/feed (and industrial) — sensitivity, not headline.
        "demand": run_crop_dynamics(
            crop, start_year=args.start, end_year=args.end,
            use_amis=False, use_shocks=False, use_demand=True),
        "tau": run_crop_dynamics(
            crop, start_year=args.start, end_year=args.end,
            use_amis=True, use_shocks=False, use_demand=False,
            use_industrial=False),
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

    ship = shipment_windows(full, legs["shocks"], crop)
    ship_path = DIAG / f"gate0_{crop}_shipments.csv"
    ship.to_csv(ship_path, index=False)
    ann = annual_exports_vs_psd(full, legs["shocks"], crop)
    ann_path = DIAG / f"gate0_{crop}_exports_psd.csv"
    ann.to_csv(ann_path, index=False)
    ship_fig_path = FIGS / f"fig_gate0_{crop}_shipments.png"
    _fig_shipment_windows(crop, ship, ship_fig_path)
    print("AMIS shipment signs (official matched vs harvest-only):")
    for _, r in ship.iterrows():
        print(f"  {r.country} {r.window}: offer ×{r.offer_ratio:.2f}  "
              f"ship ×{r.ship_ratio:.2f}")

    import sys
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    from score_country_balance import _fig as _country_fig
    from score_country_balance import _fig_world_consumption
    from score_country_balance import _fig_world_tightness
    from score_country_balance import _metrics as _country_metrics
    from score_country_balance import consumption_metrics
    from score_country_balance import country_balance
    from score_country_balance import tightness_metrics
    from score_country_balance import world_consumption
    from score_country_balance import world_my_end_stocks

    # Calendar December vs crop marketing-year end (PSD). Rice MY-end is August.
    # Also FAO/AMIS-style world excluding China (rice: China+India).
    my_month = CROP_MY_END_MONTH[crop]
    stock_cmp = world_my_end_stocks(full, crop)
    stock_path = DIAG / f"gate0_{crop}_stocks.csv"
    stock_cmp.to_csv(stock_path, index=False)
    tmet = tightness_metrics(stock_cmp)
    print(f"\nWorld MY-end tightness ({crop}):")
    print(f"  including China ×{tmet['mean_ratio_world']:.2f}")
    print(f"  excluding China ×{tmet['mean_ratio_ex_china']:.2f} "
          f"(China {tmet['china_psd_share']:.0%} of PSD world)")
    if "mean_ratio_ex_china_india" in tmet:
        print(f"  excluding China+India ×{tmet['mean_ratio_ex_china_india']:.2f}")
    tfig_path = FIGS / f"fig_gate0_{crop}_world_exchina.png"
    _fig_world_tightness(crop, stock_cmp, tfig_path)

    cbal = country_balance(full, crop)
    cbal_path = DIAG / f"gate0_{crop}_country_balance.csv"
    cbal.to_csv(cbal_path, index=False)
    cfig_path = FIGS / f"fig_gate0_{crop}_country_stocks.png"
    _country_fig(crop, cbal, cfig_path)
    cmet = _country_metrics(cbal)
    cons_world = world_consumption(cbal)
    cons_path = DIAG / f"gate0_{crop}_consumption.csv"
    cons_world.to_csv(cons_path, index=False)
    cons_met = consumption_metrics(cbal)
    cons_fig_path = FIGS / f"fig_gate0_{crop}_world_consumption.png"
    _fig_world_consumption(crop, cbal, cons_fig_path)
    print(f"World consumption ({crop}): ×{cons_met['mean_cons_ratio']:.2f} "
          f"corr {cons_met['cons_corr']:+.2f} "
          f"Δcons {cons_met['dcons_sign']}/{cons_met['dcons_n']}")

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
        trio = [("production", sh), ("demand", dem), ("restriction", tau)]
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
    lines.append(
        f"## Annual world ending stocks (calendar Dec vs PSD; "
        f"MY-end month={my_month})")
    for _, r in stock_cmp.iterrows():
        lines.append(
            f"- {int(r.year)}: Dec {r.model_ending_stock:.1f} MMT "
            f"(STU {r.model_stu:.2f}); MY-end {r.model_my_end_stock:.1f} MMT "
            f"(STU {r.model_my_stu:.2f}) vs PSD {r.psd_ending_stocks:.1f} MMT "
            f"(STU {r.psd_stu:.2f})")
    ratio_dec = float(
        (stock_cmp.model_ending_stock / stock_cmp.psd_ending_stocks).mean())
    ratio_my = float(
        (stock_cmp.model_my_end_stock / stock_cmp.psd_ending_stocks).mean())
    lines.append(
        f"- Mean model/PSD: Dec ×{ratio_dec:.2f}, MY-end ×{ratio_my:.2f} "
        f"(target ~1; >2 still fat warehouse)")

    lines.append("")
    lines.append(
        "## World MY-end excluding China (FAO/AMIS tightness; China stays a named node)")
    lines.append(
        f"- China share of PSD world stocks: {tmet['china_psd_share']:.0%}")
    lines.append(
        f"- Mean model/PSD MY-end excluding China: "
        f"×{tmet['mean_ratio_ex_china']:.2f} "
        f"(including China ×{tmet['mean_ratio_world']:.2f})")
    if crop == "rice" and "mean_ratio_ex_china_india" in tmet:
        lines.append(
            f"- Mean model/PSD MY-end excluding China+India: "
            f"×{tmet['mean_ratio_ex_china_india']:.2f}")
    lines.append(
        "- China stock *levels* are estimated (state reserves, not a Gate 0 fail). "
        "This series is the traded-market remainder.")
    if crop == "maize":
        lines.append(
            "- China maize USDA MY-end is September; the world bar is August, so "
            "this snapshot under-subtracts China (model China at August is thin). "
            "Local-MY China is separately fat. Not a warehouse retune.")
    for _, r in stock_cmp.iterrows():
        extra = ""
        if crop == "rice":
            extra = (
                f"; ex-CN+IN {r.model_my_end_ex_china_india:.1f} vs "
                f"{r.psd_ending_ex_china_india:.1f} MMT")
        lines.append(
            f"- {int(r.year)}: ex-China {r.model_my_end_ex_china:.1f} vs "
            f"PSD {r.psd_ending_ex_china:.1f} MMT "
            f"(STU {r.model_my_stu_ex_china:.2f} vs {r.psd_stu_ex_china:.2f}; "
            f"China {r.china_psd_share:.0%} of PSD world){extra}")

    lines.append("")
    lines.append(
        "## Annual world consumption vs PSD (calendar year, official matched)")
    lines.append(
        "Country-sum PSD (not `load_crop_world`, which omits the EU). "
        "Mean flex + isoelastic; year-by-year food/feed is a sensitivity. "
        "Not Agrimate Fig. 4 (that figure is supply Δ and stock Δ).")
    lines.append(
        f"- Mean model/PSD: ×{cons_met['mean_cons_ratio']:.2f} "
        f"(unweighted median country-year ×{cmet['median_cons_ratio']:.2f})")
    lines.append(
        f"- Corr(levels) = {cons_met['cons_corr']:+.2f}")
    lines.append(
        f"- Δcons as % of mean PSD use ({cons_met['cons_scale']:.0f} MMT); "
        f"sign {cons_met['dcons_sign']}/{cons_met['dcons_n']}")
    for _, r in cons_world.iterrows():
        d_mod = (f"{r.model_dcons:+.1f}" if np.isfinite(r.model_dcons) else "—")
        d_psd = (f"{r.psd_dcons:+.1f}" if np.isfinite(r.psd_dcons) else "—")
        lines.append(
            f"- {int(r.year)}: model {r.model_cons:.1f} vs PSD {r.psd_cons:.1f} MMT "
            f"(×{r.cons_ratio:.2f}; Δ {d_mod} / {d_psd} pp)")
    y_last = int(cons_world.year.max())
    nodes = (cbal[(cbal.year == y_last) & (cbal.psd_cons > 10)]
             .sort_values("psd_cons", ascending=False).head(6))
    if len(nodes):
        lines.append(f"- {y_last} named-node snapshot (psd_cons>10 MMT):")
        for _, r in nodes.iterrows():
            lines.append(
                f"  - {r.country}: model {r.model_cons:.1f} vs PSD {r.psd_cons:.1f} "
                f"MMT (×{r.cons_ratio:.2f})")

    lines.append("")
    lines.append(
        "## AMIS shipment signs (official matched vs harvest-only)")
    lines.append(
        "Isolated-τ assert ≠ this table. Fig. 3 is model-implied withheld grain, "
        "not FAOSTAT trade. Ratio < 1 means AMIS cut that node.")
    if crop == "wheat":
        lines.append(
            "- Russia 2010: offers fall hard; shipments fall less (Armington fill). "
            "Calendar-year model still well above PSD.")
    elif crop == "maize":
        lines.append(
            "- Argentina May 2007: offers fall, shipments barely move (demand already "
            "the constraint). Isolated τ must not cut the 14-month mean world price.")
    elif crop == "rice":
        lines.append(
            "- Assert window is Vietnam Sep–Nov 2008 **tax**, not the 2007/08 ban. "
            "Clean ban+harvest overlap is Oct–Dec 2007. India lingering can leak.")
    for _, r in ship.iterrows():
        sign = "cut" if r.ship_ratio < 0.98 else (
            "flat" if r.ship_ratio < 1.02 else "up")
        lines.append(
            f"- {r.country} {r.window} {int(r.y0)}-{int(r.m0):02d}→"
            f"{int(r.y1)}-{int(r.m1):02d}: offer ×{r.offer_ratio:.2f}, "
            f"ship ×{r.ship_ratio:.2f} ({sign}; τ̄={r.mean_cut:.2f})")
    # PSD annual for the assert-window country in crisis years
    ac = _EXPORTER_WINDOWS[crop][0]
    sub = ann[(ann.country == ac) & (ann.year.isin([2007, 2008, 2010, 2011]))]
    if len(sub):
        lines.append(f"- {ac} calendar-year exports vs PSD:")
        for _, r in sub.iterrows():
            lines.append(
                f"  - {int(r.year)}: full {r.model_full:.1f} vs no-AMIS "
                f"{r.model_shocks:.1f} vs PSD {r.psd:.1f} MMT "
                f"(model/PSD ×{r.model_over_psd:.2f})")

    lines.append("")
    lines.append(
        "## Country MY-end stocks vs PSD (local marketing year, not groupings)")
    lines.append(
        f"- Median model/PSD stock (psd>1 MMT): ×{cmet['median_stock_ratio']:.2f} "
        f"(mean ×{cmet['mean_stock_ratio']:.2f})")
    lines.append(
        f"- Median model/PSD consumption: ×{cmet['median_cons_ratio']:.2f}")
    lines.append(
        f"- Δstock sign agreement: {cmet['dstock_sign']}/{cmet['dstock_n']}")
    big = cbal[(cbal.psd_stock > 2) & (cbal.year == cbal.year.max())]
    if len(big):
        lines.append(f"- {int(big.year.iloc[0])} snapshot (psd>2 MMT):")
        for _, r in big.sort_values("psd_stock", ascending=False).iterrows():
            lines.append(
                f"  - {r.country} (m={int(r.my_month)}): model {r.model_stock:.1f} "
                f"vs PSD {r.psd_stock:.1f} MMT (×{r.stock_ratio:.2f})")

    lines.append("")
    lines.append(f"## Artifacts")
    lines.append(f"- `{score_path.relative_to(ROOT)}`")
    lines.append(f"- `{exp_path.relative_to(ROOT)}`")
    lines.append(f"- `{ship_path.relative_to(ROOT)}`")
    lines.append(f"- `{ann_path.relative_to(ROOT)}`")
    lines.append(f"- `{ship_fig_path.relative_to(ROOT)}`")
    lines.append(f"- `{stock_path.relative_to(ROOT)}`")
    lines.append(f"- `{cbal_path.relative_to(ROOT)}`")
    lines.append(f"- `{fig_path.relative_to(ROOT)}`")
    lines.append(f"- `{cfig_path.relative_to(ROOT)}`")
    lines.append(f"- `{tfig_path.relative_to(ROOT)}`")
    lines.append(f"- `{cons_path.relative_to(ROOT)}`")
    lines.append(f"- `{cons_fig_path.relative_to(ROOT)}`")

    report_path = DIAG / f"gate0_{crop}_report.md"
    report_path.write_text("\n".join(lines) + "\n")
    print(f"\nwrote {score_path}")
    print(f"wrote {exp_path}")
    print(f"wrote {stock_path}")
    print(f"wrote {fig_path}")
    print(f"wrote {tfig_path}")
    print(f"wrote {report_path}")


if __name__ == "__main__":
    main()
