"""R5 red-team: digitise Agrimate (Kuhla et al. 2025) Fig. 4a.

Fig. 4a plots four monthly series over 2006-2012 on a US$/t axis:
  baseline (grey dash-dot), production anomalies (green dotted),
  full model (orange solid), empirical deflated Wheat US HRW (blue dashed).

We recover them by colour segmentation of a 600 dpi render of PDF page 9,
calibrate pixel -> data with the plot frame + tick positions, and resample
to monthly. Output: diagnostics/redteam/r5/agrimate_fig4a_digitised.csv

Read-only w.r.t. sheaf/ and scripts/*.py.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
PDF = ROOT / "agrimate" / "Kuhla_2025_Agrimate.pdf"
OUTDIR = ROOT / "diagnostics" / "redteam" / "r5"
TMP = Path("/tmp/r5fig")

# Reference colours sampled from the render (RGB).
SERIES = {
    "baseline":    (150, 150, 150),
    "prod_anom":   (106, 168, 79),
    "full_model":  (244, 154, 100),
    "observed":    (86, 180, 233),
}
TOL = 46.0

# Axis calibration, in the coordinate frame of the 600 dpi page render.
# Frame corners and tick anchors are located automatically below.
Y_TICKS = (80.0, 200.0)     # first and last labelled y ticks
X_TICKS = (2006.0, 2012.0)  # first and last labelled x ticks


def render() -> Image.Image:
    TMP.mkdir(exist_ok=True)
    png = TMP / "hi-09.png"
    if not png.exists():
        subprocess.run(
            ["pdftoppm", "-r", "600", "-f", "9", "-l", "9", "-png",
             str(PDF), str(TMP / "hi")], check=True)
    return Image.open(png).convert("RGB")


def find_frame(arr: np.ndarray) -> tuple[int, int, int, int]:
    """Locate the black axes rectangle of panel (a)."""
    dark = arr.sum(axis=2) < 260
    # Panel (a) lives in the upper-left quadrant of the page.
    sub = dark[400:1500, 700:2800]
    rows = sub.sum(axis=1)
    cols = sub.sum(axis=0)
    long_rows = np.where(rows > 0.6 * sub.shape[1])[0]
    long_cols = np.where(cols > 0.6 * sub.shape[0])[0]
    top, bot = long_rows.min() + 400, long_rows.max() + 400
    left, right = long_cols.min() + 700, long_cols.max() + 700
    return left, right, top, bot


def _group(idx: np.ndarray, gap: int = 4) -> list[int]:
    groups, cur = [], [idx[0]]
    for v in idx[1:]:
        if v - cur[-1] <= gap:
            cur.append(v)
        else:
            groups.append(int(round(np.mean(cur))))
            cur = [v]
    groups.append(int(round(np.mean(cur))))
    return groups


def y_tick_pixels(arr: np.ndarray, left: int, top: int, bot: int) -> list[int]:
    """Ticks point inward; read the strip just inside the left spine."""
    g = arr.mean(axis=2)
    strip = g[top:bot + 1, left + 8:left + 20] < 120
    rows = np.where(strip.all(axis=1))[0]
    return [r + top for r in _group(rows)]


def x_tick_pixels(arr: np.ndarray, left: int, right: int, bot: int) -> list[int]:
    g = arr.mean(axis=2)
    strip = g[bot - 20:bot - 8, left:right + 1] < 120
    cols = np.where(strip.all(axis=0))[0]
    return [c + left for c in _group(cols)]


def main() -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    im = render()
    arr = np.asarray(im).astype(float)

    left, right, top, bot = find_frame(arr)
    # The topmost y tick (220) has a clipped label; keep only the 7 labelled
    # ticks 200..80.
    yticks = [r for r in y_tick_pixels(arr, left, top, bot)
              if top + 20 < r < bot - 20]
    xticks = x_tick_pixels(arr, left, right, bot)
    print(f"frame x[{left},{right}] y[{top},{bot}]")
    print(f"y ticks (px rows): {yticks}")
    print(f"x ticks (px cols): {xticks}")
    assert len(yticks) == 7, yticks
    assert len(xticks) == 7, xticks

    # y ticks run 200 (top) down to 80 (bottom) in steps of 20 -> 7 ticks
    yvals = np.linspace(200.0, 80.0, len(yticks))
    # x ticks 2006..2012 -> 7 ticks
    xvals = np.linspace(2006.0, 2012.0, len(xticks))
    py = np.polyfit(yticks, yvals, 1)
    px = np.polyfit(xticks, xvals, 1)

    recs = []
    for name, rgb in SERIES.items():
        d = np.linalg.norm(arr - np.array(rgb, dtype=float), axis=2)
        mask = d < TOL
        mask[:top, :] = False
        mask[bot + 1:, :] = False
        mask[:, :left] = False
        mask[:, right + 1:] = False
        for col in range(left, right + 1):
            rows = np.where(mask[:, col])[0]
            if rows.size == 0:
                continue
            recs.append(dict(series=name, col=col,
                             row=float(rows.mean()),
                             n=int(rows.size)))
    raw = pd.DataFrame(recs)
    raw["year_frac"] = np.polyval(px, raw["col"])
    raw["price"] = np.polyval(py, raw["row"])

    # Resample each series onto month centres.
    months = np.arange(2006.0, 2012.0 + 1e-9, 1.0 / 12.0) + 1.0 / 24.0
    out = {"year_frac": months[:-1]}
    for name in SERIES:
        s = raw[raw.series == name].sort_values("year_frac")
        # dashed/dotted lines have gaps: interpolate over them
        out[name] = np.interp(months[:-1], s.year_frac.values, s.price.values)
    df = pd.DataFrame(out)
    k = np.arange(len(df))
    df["year"] = 2006 + k // 12
    df["month"] = k % 12 + 1
    df = df[["year", "month", "year_frac"] + list(SERIES)]
    df.to_csv(OUTDIR / "agrimate_fig4a_digitised.csv", index=False)
    print(df.describe())
    print(f"wrote {OUTDIR / 'agrimate_fig4a_digitised.csv'}")


if __name__ == "__main__":
    main()
