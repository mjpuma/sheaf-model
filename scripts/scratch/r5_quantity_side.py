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

FAO_BLUE = (86, 180, 233)
MODEL_ORANGE = (230, 126, 34)
TOL = 60.0

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


def panel_frame(arr, box):
    x0, y0, x1, y1 = box
    dark = arr[y0:y1, x0:x1].sum(axis=2) < 260
    rows = np.where(dark.sum(axis=1) > 0.6 * dark.shape[1])[0]
    cols = np.where(dark.sum(axis=0) > 0.6 * dark.shape[0])[0]
    return (cols.min() + x0, cols.max() + x0, rows.min() + y0, rows.max() + y0)


def y_ticks(arr, left, top, bot):
    g = arr.mean(axis=2)
    strip = g[top:bot + 1, left + 8:left + 20] < 120
    rows = np.where(strip.all(axis=1))[0]
    out = [int(round(np.mean(r))) + top for r in _group(rows)]
    return [r for r in out if top + 20 < r < bot - 20]


def bars(arr, rgb, left, right, top, bot, zero_row, scale):
    d = np.linalg.norm(arr - np.array(rgb, float), axis=2)
    m = d < TOL
    m[:top, :] = False
    m[bot + 1:, :] = False
    m[:, :left] = False
    m[:, right + 1:] = False
    cols = np.where(m.sum(axis=0) > 5)[0]
    out = []
    for c0, c1 in _group(cols, gap=6):
        if c1 - c0 < 8:          # legend swatches / stray marks
            continue
        sub = m[:, c0:c1 + 1]
        rows = np.where(sub.any(axis=1))[0]
        lo, hi = rows.min(), rows.max()
        # the bar runs from the zero line to its far end
        val = (zero_row - lo) * scale if abs(zero_row - lo) > abs(zero_row - hi) \
            else (zero_row - hi) * scale
        out.append(dict(x0=int(c0), x1=int(c1), value=float(val)))
    return out


def digitise_panel(arr, box, gridvals):
    left, right, top, bot = panel_frame(arr, box)
    ticks = y_ticks(arr, left, top, bot)
    assert len(ticks) == len(gridvals), (ticks, gridvals)
    fit = np.polyfit(ticks, gridvals, 1)          # value = a*row + b
    scale = -fit[0]                                # value units per pixel up
    zero_row = float((0.0 - fit[1]) / fit[0])
    fao = bars(arr, FAO_BLUE, left, right, top, bot, zero_row, scale)
    mod = bars(arr, MODEL_ORANGE, left, right, top, bot, zero_row, scale)
    return left, right, top, bot, fao, mod


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    arr = render()

    # panel (b): y ticks are -4,-3,-2,-1,0,1  (top tick is +1)
    supply = digitise_panel(arr, PANELS["supply_change"]["box"],
                            [1.0, 0.0, -1.0, -2.0, -3.0, -4.0])
    # panel (e): y ticks are 6,3,0,-3
    stock = digitise_panel(arr, PANELS["stock_change"]["box"],
                           [6.0, 3.0, 0.0, -3.0])

    rows = []
    for name, (left, right, top, bot, fao, mod) in [
            ("supply_change", supply), ("stock_change", stock)]:
        fao = sorted(fao, key=lambda r: r["x0"])
        mod = sorted(mod, key=lambda r: r["x0"])
        print(f"{name}: {len(fao)} FAO bars, {len(mod)} model bars")
        for i, (f, m) in enumerate(zip(fao, mod)):
            rows.append(dict(panel=name, year=2006 + i,
                             fao=round(f["value"], 2),
                             full_model=round(m["value"], 2),
                             sign_agree=int(np.sign(f["value"]) ==
                                            np.sign(m["value"]))))
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
