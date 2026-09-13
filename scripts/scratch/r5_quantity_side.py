"""R5 red-team: quantity-side validation, Agrimate Fig. 4b/4e vs SHEAF Gate 0.

Part 1 digitises the two global bar panels of Agrimate Fig. 4 (supply change
and stock change, % of baseline supply, FAO blue vs full-model orange) and
scores sign agreement year by year.

Part 2 builds the closest SHEAF analogue from the Gate 0 report artifacts:
world annual stock change and world annual consumption change, model vs USDA
PSD, expressed the same way (% of mean annual PSD use), plus the country-level
stock-sign tallies already in the reports.

Read-only w.r.t. sheaf/ and scripts/*.py.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
DIAG = ROOT / "diagnostics"
OUT = DIAG / "redteam" / "r5"
TMP = Path("/tmp/r5fig")

FAO_BLUE = (0, 159, 218)
MODEL_ORANGE = (227, 114, 34)
TOL = 45.0

# Panel bounding boxes in the 600 dpi page-9 render, found by inspection of
# the axes frames (see r5_digitise_agrimate_fig4a.py for the same technique).
# Axes frames (left, right, top, bottom) of Fig. 4b and 4e in the 600 dpi
# page-9 render, located by long-black-line detection (see r5 notebook trace).
PANELS = {
    "supply_change": dict(frame=(919, 1936, 1578, 2236),
                          tick_values=[1.0, 0.0, -1.0, -2.0, -3.0, -4.0]),
    "stock_change":  dict(frame=(919, 1936, 2246, 2904),
                          tick_values=[6.0, 3.0, 0.0, -3.0]),
}


def render() -> np.ndarray:
    TMP.mkdir(exist_ok=True)
    png = TMP / "hi-09.png"
    if not png.exists():
        subprocess.run(["pdftoppm", "-r", "600", "-f", "9", "-l", "9", "-png",
                        str(ROOT / "agrimate" / "Kuhla_2025_Agrimate.pdf"),
                        str(TMP / "hi")], check=True)
    return np.asarray(Image.open(png).convert("RGB")).astype(float)


def _group(idx, gap=4):
    groups, cur = [], [idx[0]]
    for v in idx[1:]:
        if v - cur[-1] <= gap:
            cur.append(v)
        else:
            groups.append((cur[0], cur[-1]))
            cur = [v]
    groups.append((cur[0], cur[-1]))
    return groups


def y_ticks(arr, left, top, bot, n_expected):
    """Inward tick marks on the left spine; drop the spines themselves."""
    g = arr.mean(axis=2)
    strip = g[top:bot + 1, left + 8:left + 20] < 120
    rows = np.where(strip.all(axis=1))[0]
    out = [int(round(np.mean(range(a, b + 1)))) + top for a, b in _group(rows)]
    out = [r for r in out if r > top + 20]
    if len(out) > n_expected:                  # bottom spine doubles as a tick
        out = out[:n_expected]
    return out


def bar_value(arr, rgb, band, top, bot, zero_row, scale):
    """Height of the coloured run that touches the zero line inside `band`.

    Walking out from the zero line (rather than taking the colour's extreme
    row in the column) keeps the in-panel legend swatch, which shares the
    horizontal extent of the 2009 bars, out of the measurement. The model
    bars are dotted, so a row counts as filled if a quarter of the band is
    coloured.
    """
    c0, c1 = band
    d = np.linalg.norm(arr[top:bot + 1, c0:c1 + 1] -
                       np.array(rgb, float), axis=2)
    on = (d < TOL).mean(axis=1) > 0.25
    z = int(round(zero_row)) - top
    idx = np.where(on)[0]
    if idx.size == 0:
        return 0.0
    # contiguous runs, tolerating the grey zero gridline drawn over the bars
    best = None
    for lo, hi in _group(idx, gap=8):
        dist = 0 if lo <= z <= hi else min(abs(lo - z), abs(hi - z))
        if dist <= 15 and (best is None or dist < best[0]):
            best = (dist, lo, hi)
    if best is None:
        return 0.0
    _, lo, hi = best
    return float((z - lo) * scale) if (z - lo) >= (hi - z) \
        else float(-(hi - z) * scale)


YEAR_CENTRES = (1016, 1180, 1345, 1509, 1674, 1839)   # x ticks 2006..2011


def digitise_panel(arr, frame, gridvals):
    left, right, top, bot = frame
    ticks = y_ticks(arr, left, top, bot, len(gridvals))
    assert len(ticks) == len(gridvals), (ticks, gridvals)
    fit = np.polyfit(ticks, gridvals, 1)          # value = a*row + b
    scale = -fit[0]                                # value units per pixel up
    zero_row = float((0.0 - fit[1]) / fit[0])
    out = []
    for i, xc in enumerate(YEAR_CENTRES):
        out.append(dict(
            year=2006 + i,
            fao=bar_value(arr, FAO_BLUE, (xc - 45, xc - 5),
                          top, bot, zero_row, scale),
            full_model=bar_value(arr, MODEL_ORANGE, (xc + 5, xc + 45),
                                 top, bot, zero_row, scale)))
    return out


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    arr = render()

    supply = digitise_panel(arr, PANELS["supply_change"]["frame"],
                            PANELS["supply_change"]["tick_values"])
    stock = digitise_panel(arr, PANELS["stock_change"]["frame"],
                           PANELS["stock_change"]["tick_values"])

    rows = []
    for name, recs in [("supply_change", supply), ("stock_change", stock)]:
        for r in recs:
            rows.append(dict(panel=name, year=r["year"],
                             fao=round(r["fao"], 2),
                             full_model=round(r["full_model"], 2),
                             sign_agree=int(np.sign(r["fao"]) ==
                                            np.sign(r["full_model"]))))
    ag = pd.DataFrame(rows)
    ag.to_csv(OUT / "agrimate_fig4be_digitised.csv", index=False)
    print(ag.to_string(index=False))
    print("\nAgrimate global sign agreement:")
    print(ag.groupby("panel").sign_agree.agg(["sum", "count"]))

    # ---------------- SHEAF world quantity side --------------------------
    srows = []
    for crop in ("wheat", "maize", "rice"):
        st = pd.read_csv(DIAG / f"gate0_{crop}_stocks.csv")
        cons = pd.read_csv(DIAG / f"gate0_{crop}_consumption.csv")
        base = float(cons.psd_cons.mean())     # "baseline supply" proxy
        st = st.sort_values("year")
        dm = st.model_my_end_stock.diff()
        dp = st.psd_ending_stocks.diff()
        for y, a, b in zip(st.year[1:], dm[1:], dp[1:]):
            srows.append(dict(crop=crop, panel="stock_change", year=int(y),
                              psd_pct=100 * b / base, model_pct=100 * a / base,
                              sign_agree=int(np.sign(a) == np.sign(b))))
        cons = cons.sort_values("year")
        for _, r in cons.dropna(subset=["model_dcons"]).iterrows():
            srows.append(dict(crop=crop, panel="consumption_change",
                              year=int(r.year),
                              psd_pct=100 * r.psd_dcons / base,
                              model_pct=100 * r.model_dcons / base,
                              sign_agree=int(np.sign(r.model_dcons) ==
                                             np.sign(r.psd_dcons))))
    sh = pd.DataFrame(srows)
    sh.to_csv(OUT / "sheaf_world_quantity_signs.csv", index=False)
    print("\nSHEAF world sign agreement (model vs USDA PSD):")
    print(sh.groupby(["panel", "crop"]).sign_agree.agg(["sum", "count"]))
    print("\n", sh.round(2).to_string(index=False))

    # levels ratios and correlations already in the reports, gathered
    lev = []
    for crop in ("wheat", "maize", "rice"):
        st = pd.read_csv(DIAG / f"gate0_{crop}_stocks.csv")
        cons = pd.read_csv(DIAG / f"gate0_{crop}_consumption.csv")
        cb = pd.read_csv(DIAG / f"gate0_{crop}_country_balance.csv")
        big = cb[cb.psd_stock > 1]
        lev.append(dict(
            crop=crop,
            world_my_end_stock_ratio=float(
                (st.model_my_end_stock / st.psd_ending_stocks).mean()),
            world_my_end_stock_corr=float(np.corrcoef(
                st.model_my_end_stock, st.psd_ending_stocks)[0, 1]),
            world_dec_stock_ratio=float(
                (st.model_ending_stock / st.psd_ending_stocks).mean()),
            world_cons_ratio=float(cons.cons_ratio.mean()),
            world_cons_corr=float(np.corrcoef(cons.model_cons,
                                              cons.psd_cons)[0, 1]),
            country_stock_ratio_median=float(big.stock_ratio.median()),
            country_dstock_sign_agree=int(
                (np.sign(cb.model_dstock) == np.sign(cb.psd_dstock)).sum()),
            country_dstock_n=int(cb.dropna(subset=["psd_dstock"]).shape[0]),
        ))
    lv = pd.DataFrame(lev)
    lv.to_csv(OUT / "sheaf_quantity_levels.csv", index=False)
    print("\n", lv.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
