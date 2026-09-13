"""R5 red-team: like-for-like scoring of Agrimate Fig. 4a vs SHEAF Gate 0.

Applies SHEAF's own price metrics (monthly Pearson corr over 2006-2011, and
the 3-month-mean peak / 3-month-mean base hike ratio over 2006-06 -> 2008-03
and 2009-06 -> 2011-02, exactly as `scripts/score_subannual_crop.py::_hike`)
to four series:

  * SHEAF Gate 0 wheat model price      (diagnostics/gate0_wheat_score.csv)
  * SHEAF's observed target             (Pink Sheet US HRW, MUV-deflated)
  * Agrimate full-model price           (digitised Fig. 4a, orange)
  * Agrimate's observed target          (digitised Fig. 4a, blue: US HRW,
                                         US-CPI-deflated)

Also validates the digitisation by correlating the digitised blue curve
against the repository's own Pink Sheet US HRW series.

Read-only w.r.t. sheaf/ and scripts/*.py.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DIAG = ROOT / "diagnostics"
OUT = DIAG / "redteam" / "r5"

WINDOWS = [("2007/08", 2006, 6, 2008, 3), ("2010/11", 2009, 6, 2011, 2)]


def _corr(a, b) -> float:
    a, b = np.asarray(a, float), np.asarray(b, float)
    m = np.isfinite(a) & np.isfinite(b)
    return float(np.corrcoef(a[m], b[m])[0, 1]) if m.sum() >= 6 else float("nan")


def _hike(df: pd.DataFrame, col: str, y0: int, m0: int, y1: int, m1: int) -> float:
    """Byte-for-byte the metric in scripts/score_subannual_crop.py."""
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


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    ag = pd.read_csv(OUT / "agrimate_fig4a_digitised.csv")

    rows = []

    # --- digitisation sanity check against the repo's own Pink Sheet HRW ----
    ps = pd.read_csv(ROOT / "data" / "world_prices" / "pink_sheet_grains_monthly.csv")
    ps = ps[(ps.grain == "wheat") & ps.year.between(2006, 2011)]
    merged = ag.merge(ps, on=["year", "month"], how="inner")
    check = dict(
        n_months=len(merged),
        corr_digitised_vs_pinksheet_nominal=_corr(
            merged.observed, merged.price_nominal_usd_mt),
        corr_digitised_vs_pinksheet_muv_real=_corr(
            merged.observed, merged.price_real_2010_usd_mt),
    )
    pd.DataFrame([check]).to_csv(OUT / "digitisation_check.csv", index=False)
    print("digitisation check:", check)

    # --- metrics on all four series ----------------------------------------
    sheaf = pd.read_csv(DIAG / "gate0_wheat_score.csv")
    sheaf_full = sheaf[sheaf.leg == "full"].copy()

    series = {
        ("SHEAF Gate 0 wheat", "model"): (sheaf_full, "model_price"),
        ("Pink Sheet HRW (MUV-real)", "observed"): (sheaf_full, "obs_price"),
        ("Agrimate full model", "model"): (ag, "full_model"),
        ("Agrimate prod-anomalies only", "model"): (ag, "prod_anom"),
        ("Agrimate unperturbed baseline", "model"): (ag, "baseline"),
        ("HRW US-CPI-real (Agrimate Fig4a)", "observed"): (ag, "observed"),
    }
    for (name, kind), (df, col) in series.items():
        rec = dict(series=name, kind=kind)
        for label, y0, m0, y1, m1 in WINDOWS:
            rec[f"hike_{label}"] = _hike(df, col, y0, m0, y1, m1)
        rows.append(rec)

    # correlations, each model against its OWN paper's observed target
    corr_rows = [
        dict(model="SHEAF Gate 0 wheat (full leg)",
             target="Pink Sheet US HRW, MUV-deflated",
             corr=_corr(sheaf_full.model_price, sheaf_full.obs_price),
             n=len(sheaf_full)),
        dict(model="Agrimate full model (digitised)",
             target="US HRW, US-CPI-deflated (digitised)",
             corr=_corr(ag.full_model, ag.observed), n=len(ag)),
        dict(model="Agrimate prod-anomalies only (digitised)",
             target="US HRW, US-CPI-deflated (digitised)",
             corr=_corr(ag.prod_anom, ag.observed), n=len(ag)),
        dict(model="Agrimate unperturbed baseline (digitised)",
             target="US HRW, US-CPI-deflated (digitised)",
             corr=_corr(ag.baseline, ag.observed), n=len(ag)),
        # cross-target robustness: Agrimate model vs SHEAF's own target
        dict(model="Agrimate full model (digitised)",
             target="Pink Sheet US HRW, MUV-deflated",
             corr=_corr(merged.full_model, merged.price_real_2010_usd_mt),
             n=len(merged)),
        dict(model="SHEAF Gate 0 wheat (full leg)",
             target="US HRW, US-CPI-deflated (digitised)",
             corr=_corr(sheaf_full.sort_values(["year", "month"]).model_price.values,
                        ag.observed.values), n=len(ag)),
    ]

    # normalised error metrics on the crisis window, each vs its own target
    def nrmse(m, o):
        m, o = np.asarray(m, float), np.asarray(o, float)
        m = m / np.nanmean(m)
        o = o / np.nanmean(o)
        return float(np.sqrt(np.nanmean((m - o) ** 2)))

    err_rows = [
        dict(model="SHEAF Gate 0 wheat", target="Pink Sheet HRW MUV-real",
             nrmse_meanscaled=nrmse(sheaf_full.model_price, sheaf_full.obs_price)),
        dict(model="Agrimate full model", target="HRW US-CPI-real (digitised)",
             nrmse_meanscaled=nrmse(ag.full_model, ag.observed)),
        dict(model="Agrimate prod-anomalies only",
             target="HRW US-CPI-real (digitised)",
             nrmse_meanscaled=nrmse(ag.prod_anom, ag.observed)),
        dict(model="Agrimate unperturbed baseline",
             target="HRW US-CPI-real (digitised)",
             nrmse_meanscaled=nrmse(ag.baseline, ag.observed)),
    ]

    hk = pd.DataFrame(rows)
    cr = pd.DataFrame(corr_rows)
    er = pd.DataFrame(err_rows)
    hk.to_csv(OUT / "like_for_like_hikes.csv", index=False)
    cr.to_csv(OUT / "like_for_like_corr.csv", index=False)
    er.to_csv(OUT / "like_for_like_nrmse.csv", index=False)
    print("\n", hk.to_string(index=False))
    print("\n", cr.to_string(index=False))
    print("\n", er.to_string(index=False))

    # --- annual mean price uplift vs unperturbed baseline (Agrimate S5.4) ---
    ann = ag.groupby("year")[["baseline", "prod_anom", "full_model",
                              "observed"]].mean()
    ann["full_over_baseline"] = ann.full_model / ann.baseline
    ann["prod_over_baseline"] = ann.prod_anom / ann.baseline
    ann["full_minus_baseline_usd"] = ann.full_model - ann.baseline
    ann.to_csv(OUT / "agrimate_annual_uplift.csv")
    print("\n", ann.round(2).to_string())


if __name__ == "__main__":
    main()
