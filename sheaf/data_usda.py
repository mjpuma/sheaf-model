"""
sheaf.data_usda
===============
Adapter for USDA PSD (Production, Supply & Distribution) data, aligned to the
schema used in the AgRichter Scale repository (mjpuma/AgRichterScale). It loads
the per-crop world-aggregate series that ship with SHEAF under data/usda_world/,
and is structured to accept a local per-country PSD export in the same shape.

The per-crop CSV layout (as in AgRichterScale/USDAdata) is three header rows
followed by annual data:

    Commodity , <crop> , <crop> , <crop> , <crop>
    Attribute , Beginning Stocks TY , Domestic Consumption TY , Ending Stocks TY , Production TY
    Country   , World , World , World , World
    <year>    , <begstocks> , <consumption> , <endstocks> , <production>     (units: 1000 MT)

This module provides:
  * load_crop_world(crop)        -> tidy DataFrame (year, production, consumption,
                                     beginning_stocks, ending_stocks) in MMT
  * detrend_anomalies(series)    -> relative production anomalies vs a LOWESS trend
                                     (the detrending Agrimate uses to force its hindcast)
  * stock_to_use(df)             -> ending stocks / consumption (for storage calibration)
  * crisis_forcing(...)          -> production-anomaly multipliers for a year range,
                                     ready to hand to Grist/SheafModel as a shock.
"""

from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

# world-aggregate CSVs vendored with SHEAF (see data/usda_world/PROVENANCE.txt)
_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "usda_world"
_KT_TO_MMT = 1e-3  # 1000 MT -> million tonnes


def load_crop_world(crop: str, data_dir: Path | str | None = None) -> pd.DataFrame:
    """Load a per-crop world PSD series. crop in {'wheat','rice','maize'}.

    Returns a tidy DataFrame indexed by integer marketing year with columns
    production, consumption, beginning_stocks, ending_stocks (all in MMT).
    Mirrors AgRichterScale's USDADataLoader.load_crop_data column positions.
    """
    ddir = Path(data_dir) if data_dir else _DATA_DIR
    path = ddir / f"usda_psd_1961to2025_{crop}.csv"
    if not path.exists():
        raise FileNotFoundError(f"{path} not found (crop={crop!r})")
    raw = pd.read_csv(path, skiprows=3, header=None)
    df = pd.DataFrame({
        "year": pd.to_numeric(raw.iloc[:, 0], errors="coerce"),
        "beginning_stocks": pd.to_numeric(raw.iloc[:, 1], errors="coerce") * _KT_TO_MMT,
        "consumption": pd.to_numeric(raw.iloc[:, 2], errors="coerce") * _KT_TO_MMT,
        "ending_stocks": pd.to_numeric(raw.iloc[:, 3], errors="coerce") * _KT_TO_MMT,
        "production": pd.to_numeric(raw.iloc[:, 4], errors="coerce") * _KT_TO_MMT,
    }).dropna(subset=["year"]).astype({"year": int}).set_index("year").sort_index()
    return df.dropna(how="all")


def _lowess(y: np.ndarray, x: np.ndarray, frac: float) -> np.ndarray:
    """Compact LOWESS (local linear, tricube weights). frac in (0,1] sets the
    window as a fraction of the sample -- e.g. a ~10-year window over 65 years
    of data is frac ~ 0.16, matching Agrimate's detrending choice."""
    n = len(x)
    k = max(3, int(np.ceil(frac * n)))
    out = np.empty(n)
    for i in range(n):
        d = np.abs(x - x[i])
        idx = np.argsort(d)[:k]
        dmax = d[idx].max() or 1.0
        w = (1 - (d[idx] / dmax) ** 3) ** 3          # tricube weights
        X = np.vstack([np.ones(k), x[idx] - x[i]]).T
        W = np.diag(w)
        try:
            beta = np.linalg.solve(X.T @ W @ X, X.T @ W @ y[idx])
            out[i] = beta[0]
        except np.linalg.LinAlgError:
            out[i] = np.average(y[idx], weights=w)
    return out


def detrend_anomalies(series: pd.Series, window_years: int = 10) -> pd.DataFrame:
    """Relative production anomalies vs a LOWESS trend, per Agrimate's method:
    anomaly = (value - trend) / trend. Returns columns trend, anomaly."""
    s = series.dropna()
    x = s.index.values.astype(float)
    y = s.values.astype(float)
    frac = min(1.0, max(0.1, window_years / max(len(x), 1)))
    trend = _lowess(y, x, frac)
    return pd.DataFrame({"trend": trend, "anomaly": (y - trend) / trend}, index=s.index)


def stock_to_use(df: pd.DataFrame) -> pd.Series:
    """Stock-to-use ratio (ending stocks / consumption) -- a natural calibration
    target for SHEAF's storage rules; low SUR marks tight, spike-prone markets."""
    return (df["ending_stocks"] / df["consumption"]).rename("stock_to_use")


def crisis_forcing(crops=("wheat", "rice", "maize"), years=range(2005, 2013),
                   window_years: int = 10, data_dir=None) -> pd.DataFrame:
    """Production-anomaly multipliers (1 + anomaly) per crop per year, ready to
    drive a hindcast. Row index = year, columns = crops. A value of 0.95 means
    production 5% below its detrended trend that year."""
    cols = {}
    for c in crops:
        df = load_crop_world(c, data_dir)
        an = detrend_anomalies(df["production"], window_years)["anomaly"]
        cols[c] = 1.0 + an.reindex(years)
    return pd.DataFrame(cols, index=list(years))
