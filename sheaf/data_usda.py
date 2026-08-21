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
_PSD_COUNTRY_DIR = Path(__file__).resolve().parent.parent / "data" / "usda_psd"
_AMIS_DIR = Path(__file__).resolve().parent.parent / "data" / "amis_policies"
_KT_TO_MMT = 1e-3  # 1000 MT -> million tonnes

# PSD bulk Country_Name → SHEAF calibration node name
_PSD_COUNTRY_TO_SHEAF = {
    "United States": "USA",
    "Russia": "Russia",
    "European Union": "EU",
    "Ukraine": "Ukraine",
    "Kazakhstan": "Kazakhstan",
    "Canada": "Canada",
    "Australia": "Australia",
    "Argentina": "Argentina",
    "Brazil": "Brazil",
    "India": "India",
    "Thailand": "Thailand",
    "Vietnam": "Vietnam",
    "China": "China",
    "Egypt": "Egypt",
    "Indonesia": "Indonesia",
    "Mexico": "Mexico",
    "Nigeria": "Nigeria",
}


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


def world_baseline_means(crops=("wheat", "rice", "maize"),
                         years=(2019, 2020, 2021), data_dir=None) -> pd.DataFrame:
    """Mean world production/consumption/stocks (MMT) over `years` from vendored PSD."""
    rows = {}
    for c in crops:
        df = load_crop_world(c, data_dir).loc[list(years)]
        rows[c] = {
            "production": float(df["production"].mean()),
            "consumption": float(df["consumption"].mean()),
            "ending_stocks": float(df["ending_stocks"].mean()),
            "stock_to_use": float((df["ending_stocks"] / df["consumption"]).mean()),
        }
    return pd.DataFrame(rows).T


def shock_matrix_from_world_forcing(n_countries: int, grains: tuple[str, ...],
                                    forcing_row) -> np.ndarray:
    """Broadcast a single year of `crisis_forcing` to an (n, G) shock matrix.

    Every country gets the same grain multiplier. This is the honest maximum
    with *world-aggregate* PSD only — Level-1/2 who-restricts work needs
    per-country PSD (see `load_psd_country`).
    """
    G = len(grains)
    m = np.ones((n_countries, G), float)
    for g, grain in enumerate(grains):
        try:
            m[:, g] = float(forcing_row[grain])
        except (KeyError, TypeError):
            pass
    return m


def shocks_dict_from_crisis_forcing(n_countries: int, grains: tuple[str, ...],
                                    years=range(2007, 2012),
                                    period_of_year: dict[int, int] | None = None,
                                    **forcing_kw) -> dict[int, np.ndarray]:
    """Map crisis years → SheafModel `run(shocks={period: matrix})` entries.

    By default year Y maps to period index (Y - min(years)). Override with
    period_of_year={2007: 0, 2008: 1, ...}.
    """
    years = list(years)
    forcing = crisis_forcing(crops=grains, years=years, **forcing_kw)
    mapping = period_of_year or {y: i for i, y in enumerate(years)}
    out = {}
    for y in years:
        out[mapping[y]] = shock_matrix_from_world_forcing(
            n_countries, grains, forcing.loc[y])
    return out


def load_psd_country(crop: str, country: str | None = None,
                     data_dir: Path | str | None = None) -> pd.DataFrame:
    """Load per-country USDA PSD for one grain (or all grains if crop='all').

    Reads data/usda_psd/psd_grains_country_year.csv (from the official FAS bulk
    ZIP). Values are returned in **MMT**. `country` may be a SHEAF node name
    (e.g. 'USA') or a PSD Country_Name (e.g. 'United States').
    """
    ddir = Path(data_dir) if data_dir else _PSD_COUNTRY_DIR
    path = ddir / "psd_grains_country_year.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} missing — run: python scripts/fetch_external_data.py --psd-only")
    df = pd.read_csv(path)
    if crop != "all":
        crop_l = crop.lower()
        if crop_l not in {"wheat", "rice", "maize"}:
            raise ValueError(f"crop must be wheat|rice|maize|all, got {crop!r}")
        df = df[df["grain"] == crop_l]
    if country is not None:
        # accept SHEAF name or PSD name
        rev = {v: k for k, v in _PSD_COUNTRY_TO_SHEAF.items()}
        psd_name = rev.get(country, country)
        df = df[(df["Country_Name"] == psd_name) | (df["Country_Name"] == country)]
        if df.empty:
            raise KeyError(f"no PSD rows for country={country!r} crop={crop!r}")
    # rename + convert 1000 MT → MMT
    rename = {
        "Production": "production",
        "Domestic Consumption": "consumption",
        "Beginning Stocks": "beginning_stocks",
        "Ending Stocks": "ending_stocks",
        "Imports": "imports",
        "Exports": "exports",
        "Market_Year": "year",
        "Country_Name": "country_psd",
        "Country_Code": "country_code",
    }
    out = df.rename(columns=rename).copy()
    for col in ("production", "consumption", "beginning_stocks", "ending_stocks",
                "imports", "exports"):
        if col in out.columns:
            out[col] = out[col].astype(float) * _KT_TO_MMT
    out["country"] = out["country_psd"].map(
        lambda n: _PSD_COUNTRY_TO_SHEAF.get(n, n))
    return out.sort_values(["country", "grain", "year"]).reset_index(drop=True)


def load_amis_restrictions(path: Path | str | None = None,
                           aggregated: bool = True) -> pd.DataFrame:
    """Load OECD/AMIS export-restriction timelines from data/amis_policies/.

    Default reads the aggregated CSV (one row per country–measure–commodity–
    start/end). Pass aggregated=False for the detailed HS-level table.
    """
    if path is not None:
        p = Path(path)
    else:
        name = ("export_restrictions_aggregated.csv" if aggregated
                else "export_restrictions_detailed.csv")
        p = _AMIS_DIR / name
    if not p.exists():
        raise FileNotFoundError(
            f"{p} missing — see data/amis_policies/PROVENANCE.txt and run "
            "python scripts/fetch_external_data.py --amis-only after placing the "
            "OECD XLSX in data/amis_policies/.")
    df = pd.read_csv(p)
    for col in ("Start_Date", "End_Date"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def load_price_series(path: Path | str | None = None):
    """Observed (deflated) world price series — **external**, not vendored."""
    raise NotImplementedError(
        "Observed price series are not shipped with SHEAF. "
        "See VALIDATION.md remaining inputs. "
        f"Requested path={path!r}."
    )