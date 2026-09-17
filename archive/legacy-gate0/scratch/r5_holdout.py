"""R5 red-team, resumed: the out-of-window (2021-23) test at the CURRENT
baseline, and the global sign-agreement head-to-head against Agrimate Fig. 4b/e.

The diagnostics/gate0_ukraine_*.csv artifacts are dated 2026-08-25 and so
predate all three model changes that have landed since (R0f scarcity bound,
CES origin restore, R3 ask-valuation). The 2021-23 configuration is
replicated here from scripts/score_ukraine_war.py L33-59 rather than by
running that script, which writes into diagnostics/.

Read-only w.r.t. sheaf/ and scripts/*.py (imports only).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from sheaf.data_usda import load_price_series_monthly  # noqa: E402
from sheaf.dynamic_crop import result_to_monthly, run_crop_dynamics  # noqa: E402

DIAG = ROOT / "diagnostics"
OUT = DIAG / "redteam" / "r5"
CROPS = ("wheat", "maize", "rice")
START, END = 2021, 2023
HIKE = (2021, 6, 2022, 5)   # 3-mo mean Jun-2021 base vs May-2022 peak


def _corr(a, b) -> float:
    a, b = np.asarray(a, float), np.asarray(b, float)
    m = np.isfinite(a) & np.isfinite(b)
    return float(np.corrcoef(a[m], b[m])[0, 1]) if m.sum() >= 6 else float("nan")


def _hike(df, col, y0, m0, y1, m1) -> float:
    def win(y, m):
        vals = []
        for dm in (-1, 0, 1):
            mm, yy = m + dm, y
            if mm < 1:
                mm, yy = mm + 12, yy - 1
            if mm > 12:
                mm, yy = mm - 12, yy + 1
            hit = df[(df.year == yy) & (df.month == mm)][col]
            if len(hit):
                vals.append(float(hit.iloc[0]))
        return float(np.mean(vals)) if vals else float("nan")
    b, p = win(y0, m0), win(y1, m1)
    return p / b if b and np.isfinite(b) and np.isfinite(p) else float("nan")


def holdout() -> pd.DataFrame:
    pink = load_price_series_monthly(deflated=True)
    obs_w = pink[pink.year.between(START, END)]
    rows = []
    for crop in CROPS:
        p0 = float(pink[pink.year == 2021][crop].mean())
        o = obs_w[["year", "month", crop]].rename(columns={crop: "obs_price"})
        legs = {
            "full":   dict(use_amis=True,  use_shocks=True,  use_demand=False),
            "shocks": dict(use_amis=False, use_shocks=True,  use_demand=False),
            "tau":    dict(use_amis=True,  use_shocks=False, use_demand=False,
                           use_industrial=False),
        }
        rec = dict(crop=crop, p0_2021=p0)
        rec["obs_hike"] = _hike(o, "obs_price", *HIKE)
        for name, kw in legs.items():
            res = run_crop_dynamics(
                crop, start_year=START, end_year=END, p0=p0,
                stock_seed_year=2020, spin_up_years=2,
                trade_window=(2019, 2021), **kw)
            m = result_to_monthly(res).merge(o, on=["year", "month"],
                                             how="left")
            rec[f"{name}_hike"] = _hike(m, "model_price", *HIKE)
            rec[f"{name}_corr"] = _corr(m.model_price, m.obs_price)
            rec[f"{name}_mean_usd"] = float(m.model_price.mean())
        rec["obs_mean_usd"] = float(o.obs_price.mean())
        rec["full_over_obs_level"] = rec["full_mean_usd"] / rec["obs_mean_usd"]
        rec["amp_err_pct"] = 100 * (rec["full_hike"] / rec["obs_hike"] - 1)
        rows.append(rec)
    return pd.DataFrame(rows)


def sign_head_to_head() -> pd.DataFrame:
    """Global annual change-sign agreement: Agrimate Fig. 4b/e vs SHEAF."""
    ag = pd.read_csv(OUT / "agrimate_fig4be_digitised.csv")
    sh = pd.read_csv(OUT / "sheaf_world_quantity_signs_v2.csv")
    rows = []
    for panel, g in ag.groupby("panel"):
        rows.append(dict(model="Agrimate (wheat, digitised Fig. 4b/e)",
                         panel=panel, source="FAOSTAT",
                         n_agree=int(g.sign_agree.sum()), n=len(g),
                         frac=float(g.sign_agree.mean())))
    for (panel, crop), g in sh.groupby(["panel", "crop"]):
        rows.append(dict(model=f"SHEAF Gate 0 ({crop})", panel=panel,
                         source="USDA PSD", n_agree=int(g.sign_agree.sum()),
                         n=len(g), frac=float(g.sign_agree.mean())))
    df = pd.DataFrame(rows)
    tot = sh.sign_agree.groupby(sh.panel).agg(["sum", "count"])
    print("\nSHEAF pooled across crops:\n", tot.to_string())
    return df


def main() -> None:
    sha = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short",
                          "HEAD"], capture_output=True, text=True).stdout.strip()
    print(f"HEAD = {sha}")
    h = holdout()
    h.to_csv(OUT / "holdout_2021_23.csv", index=False)
    print("\n=== 2021-23 Ukraine-war window, current baseline ===")
    print(h.round(3).to_string(index=False))

    s = sign_head_to_head()
    s.to_csv(OUT / "sign_head_to_head.csv", index=False)
    print("\n=== global change-sign agreement ===")
    print(s.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
