"""R5 red-team: is Gate 0 systematically over-amplifying crises?

Recomputes the official hike ratios from the score CSVs written by
`scripts/score_subannual_crop.py` (all three crops, all four legs), forms the
model/observed amplification error in log space, and runs a sign test across
the 3 crops x 2 windows panel. Also summarises how the wheat 2007/08
overshoot moves under the reduced-form ablations already measured in
`diagnostics/gate0_prep/a5/ablation_grid.csv` (reported, not tuned).

Read-only w.r.t. sheaf/ and scripts/*.py.
"""
from __future__ import annotations

from math import comb
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DIAG = ROOT / "diagnostics"
OUT = DIAG / "redteam" / "r5"

WINDOWS = [("2007/08", 2006, 6, 2008, 3), ("2010/11", 2009, 6, 2011, 2)]
CROPS = ("wheat", "maize", "rice")


def _hike(df: pd.DataFrame, col: str, y0: int, m0: int, y1: int, m1: int) -> float:
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


def _corr(a, b) -> float:
    a, b = np.asarray(a, float), np.asarray(b, float)
    m = np.isfinite(a) & np.isfinite(b)
    return float(np.corrcoef(a[m], b[m])[0, 1]) if m.sum() >= 6 else float("nan")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for crop in CROPS:
        sc = pd.read_csv(DIAG / f"gate0_{crop}_score.csv")
        full = sc[sc.leg == "full"]
        for label, y0, m0, y1, m1 in WINDOWS:
            mh = _hike(full, "model_price", y0, m0, y1, m1)
            oh = _hike(full, "obs_price", y0, m0, y1, m1)
            rows.append(dict(
                crop=crop, window=label, model_hike=mh, obs_hike=oh,
                ratio=mh / oh, log_ratio=float(np.log(mh / oh)),
                pct_error=100.0 * (mh / oh - 1.0),
                corr_full=_corr(full.model_price, full.obs_price)))
    df = pd.DataFrame(rows)

    lr = df.log_ratio.values
    n_pos = int((lr > 0).sum())
    n = len(lr)
    # one-sided exact binomial P(X >= n_pos) under p = 0.5
    p_one = sum(comb(n, k) for k in range(n_pos, n + 1)) / 2 ** n
    summary = dict(
        n_cells=n,
        n_overshoot=n_pos,
        mean_log_ratio=float(lr.mean()),
        geometric_mean_amplification=float(np.exp(lr.mean())),
        median_pct_error=float(np.median(df.pct_error)),
        sd_log_ratio=float(lr.std(ddof=1)),
        t_stat=float(lr.mean() / (lr.std(ddof=1) / np.sqrt(n))),
        sign_test_p_one_sided=float(p_one),
        wheat_mean_pct_error=float(df[df.crop == "wheat"].pct_error.mean()),
        maize_mean_pct_error=float(df[df.crop == "maize"].pct_error.mean()),
        rice_mean_pct_error=float(df[df.crop == "rice"].pct_error.mean()),
    )
    df.to_csv(OUT / "hike_bias_panel.csv", index=False)
    pd.DataFrame([summary]).to_csv(OUT / "hike_bias_summary.csv", index=False)
    print(df.round(4).to_string(index=False))
    print()
    for k, v in summary.items():
        print(f"{k:34s} {v}")

    # --- how the wheat overshoot moves under R-class ablations -------------
    abl = pd.read_csv(DIAG / "gate0_prep" / "a5" / "ablation_grid.csv")
    a = abl[abl.leg == "full"].copy()
    a["err_2007_08_pct"] = 100 * (a.hike_2007_08 / a.obs_hike_2007_08 - 1)
    a["err_2010_11_pct"] = 100 * (a.hike_2010_11 / a.obs_hike_2010_11 - 1)
    keep = ["crop", "ablation", "corr", "hike_2007_08", "err_2007_08_pct",
            "hike_2010_11", "err_2010_11_pct"]
    a[keep].to_csv(OUT / "overshoot_vs_ablation.csv", index=False)
    print("\n", a[a.crop == "wheat"][keep].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
