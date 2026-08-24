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


def load_psd_use_split(crop: str, data_dir: Path | str | None = None) -> pd.DataFrame:
    """Per-country PSD use split: consumption, feed, FSI (MMT).

    Source: ``psd_grains_use_split.csv`` (Feed Dom. Consumption + FSI Consumption
    from the FAS bulk). Rice has no FSI/feed attributes in PSD — those columns
    are zero and all use is treated as food. Values in **MMT**.
    """
    ddir = Path(data_dir) if data_dir else _PSD_COUNTRY_DIR
    path = ddir / "psd_grains_use_split.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} missing — rebuild from psd_alldata.csv (Feed/FSI attributes).")
    df = pd.read_csv(path)
    crop_l = crop.lower()
    if crop_l not in {"wheat", "rice", "maize"}:
        raise ValueError(f"crop must be wheat|rice|maize, got {crop!r}")
    df = df[df["grain"] == crop_l].copy()
    df = df.rename(columns={
        "Country_Name": "country_psd",
        "Country_Code": "country_code",
    })
    for col in ("consumption", "feed", "fsi"):
        if col not in df.columns:
            df[col] = 0.0
        df[col] = df[col].astype(float) * _KT_TO_MMT
    df["country"] = df["country_psd"].map(
        lambda n: _PSD_COUNTRY_TO_SHEAF.get(n, n))
    return df.sort_values(["country", "year"]).reset_index(drop=True)


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


_PRICE_DIR = Path(__file__).resolve().parents[1] / "data" / "world_prices"


def load_price_series(path: Path | str | None = None,
                      deflated: bool = True) -> pd.DataFrame:
    """Observed **annual** world grain prices (Pink Sheet).

    Returns a DataFrame indexed by year with columns wheat / rice / maize
    ($/mt). Default `deflated=True` uses constant-2010 USD (MUV-deflated).
    For Gate 0 monthly targets use `load_price_series_monthly`.
    """
    p = Path(path) if path else (_PRICE_DIR / "pink_sheet_grains_annual.csv")
    if not p.exists():
        raise FileNotFoundError(
            f"{p} missing — run: python scripts/fetch_external_data.py --prices-only")
    df = pd.read_csv(p)
    col = "price_real_2010_usd_mt" if deflated else "price_nominal_usd_mt"
    if col not in df.columns:
        raise ValueError(f"{p} missing column {col!r}")
    wide = (df.pivot(index="year", columns="grain", values=col)
              .sort_index())
    for g in ("wheat", "rice", "maize"):
        if g not in wide.columns:
            wide[g] = np.nan
    return wide[["wheat", "rice", "maize"]]


def load_price_series_monthly(path: Path | str | None = None,
                              deflated: bool = True) -> pd.DataFrame:
    """Observed **monthly** world grain prices (Pink Sheet) — Gate 0 target.

    Returns DataFrame with columns year, month, wheat, rice, maize ($/mt).
    """
    p = Path(path) if path else (_PRICE_DIR / "pink_sheet_grains_monthly.csv")
    if not p.exists():
        raise FileNotFoundError(
            f"{p} missing — run: python scripts/fetch_external_data.py --prices-only")
    df = pd.read_csv(p)
    col = "price_real_2010_usd_mt" if deflated else "price_nominal_usd_mt"
    wide = (df.pivot(index=["year", "month"], columns="grain", values=col)
              .reset_index()
              .sort_values(["year", "month"]))
    for g in ("wheat", "rice", "maize"):
        if g not in wide.columns:
            wide[g] = np.nan
    return wide[["year", "month", "wheat", "rice", "maize"]]

# AMIS Country_Name → SHEAF node
_AMIS_COUNTRY_TO_SHEAF = {
    "Argentina": "Argentina",
    "Australia": "Australia",
    "China": "China",
    "Egypt": "Egypt",
    "India": "India",
    "Indonesia": "Indonesia",
    "Kazakhstan": "Kazakhstan",
    "Mexico": "Mexico",
    "Russian Federation": "Russia",
    "Ukraine": "Ukraine",
    "Viet Nam": "Vietnam",
}

# Prototype $/t mapping (legacy). Too weak to move world prices much.
_AMIS_TAU_PROTOTYPE = {
    "Export prohibition": 120.0,
    "Export quota": 72.0,
    "Export tax": 60.0,
    "Minimum export price": 48.0,
    "Licensing requirement": 36.0,
    "Restriction on customs clearance point for exports": 24.0,
}

# Agrimate-aligned severity: bans ≈ shut export edges; taxes ≈ large wedge.
# Calibrated so *restrictions-only* Level-1 recovers crisis price SIGNS vs Pink Sheet
# (see diagnostics/LEVEL1_INTERROGATION.md). Quantity-cut mapping still TODO.
_AMIS_TAU_AGRIMATE = {
    "Export prohibition": 500.0,
    "Export quota": 250.0,
    "Export tax": 150.0,
    "Minimum export price": 100.0,
    "Licensing requirement": 80.0,
    "Restriction on customs clearance point for exports": 50.0,
}

_AMIS_TAU = _AMIS_TAU_AGRIMATE  # default for Level-1

_AMIS_GRAIN = {
    "Wheat": "wheat",
    "Maize": "maize",
    "Rice": "rice",
}


def country_production_shocks(countries: list, grains: tuple[str, ...],
                              years: list[int],
                              window_years: int = 10) -> dict[int, np.ndarray]:
    """Per-country PSD production anomalies → SheafModel shock matrices.

    Named nodes: ξ = 1 + LOWESS anomaly on that country's production.
    RestOfWorld: ξ = 1 + LOWESS anomaly on the **world residual**
    (world production − sum of named nodes), so RoW is not frozen at 1.0.

    Returns {period_index: (n,G) multipliers} with period 0 = years[0].
    Missing country–grain series default to 1.0 (no shock).
    """
    n, G = len(countries), len(grains)
    name_to_i = {c.name: i for i, c in enumerate(countries)}
    named = [c.name for c in countries if c.name != "RestOfWorld"]
    out = {t: np.ones((n, G)) for t in range(len(years))}
    for g, grain in enumerate(grains):
        try:
            psd = load_psd_country(grain)
        except FileNotFoundError:
            continue
        for cname, i in name_to_i.items():
            if cname == "RestOfWorld":
                continue
            sub = psd[psd["country"] == cname].set_index("year")["production"]
            if sub.empty or len(sub.dropna()) < 5:
                continue
            an = detrend_anomalies(sub, window_years=window_years)["anomaly"]
            for t, y in enumerate(years):
                if y in an.index and np.isfinite(an.loc[y]):
                    out[t][i, g] = float(1.0 + an.loc[y])
        # RoW residual anomaly
        if "RestOfWorld" in name_to_i:
            world = psd.groupby("year")["production"].sum()
            named_sum = (psd[psd["country"].isin(named)]
                         .groupby("year")["production"].sum())
            resid = (world - named_sum).dropna()
            if len(resid) >= 5:
                an = detrend_anomalies(resid, window_years=window_years)["anomaly"]
                i = name_to_i["RestOfWorld"]
                for t, y in enumerate(years):
                    if y in an.index and np.isfinite(an.loc[y]):
                        out[t][i, g] = float(1.0 + an.loc[y])
    return out


def amis_tau_schedule(countries: list, grains: tuple[str, ...],
                      years: list[int],
                      tau_max: float | None = None,
                      severity: str = "agrimate") -> dict[int, np.ndarray]:
    """Map OECD/AMIS restriction episodes to annual (n,G) tau matrices.

    severity:
      "agrimate" — strong wedges (default); bans effectively shut exports.
      "prototype" — legacy mild $/t ladder (max 120).

    If several measures overlap in a year for the same country–grain, the
    **strongest** (highest tau) is kept. Unmapped AMIS countries are ignored.
    """
    if severity == "agrimate":
        table = dict(_AMIS_TAU_AGRIMATE)
    elif severity == "prototype":
        table = dict(_AMIS_TAU_PROTOTYPE)
    else:
        raise ValueError(f"unknown severity={severity!r}")
    if tau_max is not None:
        scale = tau_max / max(table.values())
        table = {k: v * scale for k, v in table.items()}

    n, G = len(countries), len(grains)
    name_to_i = {c.name: i for i, c in enumerate(countries)}
    gi = {g: k for k, g in enumerate(grains)}
    schedule = {t: np.zeros((n, G)) for t in range(len(years))}

    amis = load_amis_restrictions(aggregated=True)
    for _, row in amis.iterrows():
        sheaf = _AMIS_COUNTRY_TO_SHEAF.get(row["Country_Name"])
        if sheaf is None or sheaf not in name_to_i:
            continue
        grain = _AMIS_GRAIN.get(str(row["CommodityClass_Name"]))
        if grain is None or grain not in gi:
            continue
        tau = table.get(str(row["PolicyMeasure_Name"]), 0.0)
        if tau <= 0:
            continue
        start = row["Start_Date"]
        end = row["End_Date"]
        if pd.isna(start):
            continue
        y0 = int(start.year)
        y1 = int(end.year) if pd.notna(end) else y0
        i, g = name_to_i[sheaf], gi[grain]
        for t, y in enumerate(years):
            if y0 <= y <= y1:
                schedule[t][i, g] = max(schedule[t][i, g], tau)
    return schedule


def seed_stocks_from_psd(countries: list, year: int) -> None:
    """Overwrite private/gov opening stocks from PSD ending stocks in `year`."""
    try:
        psd = load_psd_country("all")
    except FileNotFoundError:
        return
    grains = ("wheat", "rice", "maize")
    named = [c.name for c in countries if c.name != "RestOfWorld"]
    for c in countries:
        if c.name == "RestOfWorld":
            continue
        for gi, g in enumerate(grains):
            hit = psd[(psd["country"] == c.name) & (psd["grain"] == g)
                      & (psd["year"] == year)]
            if hit.empty:
                continue
            es = float(max(hit["ending_stocks"].iloc[0], 0.0))
            if c.mkt_stock is not None:
                c.mkt_stock[gi] = 0.7 * es
                if c.mkt_capacity is not None:
                    c.mkt_capacity[gi] = max(
                        float(c.mkt_capacity[gi]), c.mkt_stock[gi] * 1.5, 1.0)
            if c.gov_stock is not None:
                c.gov_stock[gi] = 0.3 * es
    # RoW residual stocks
    row = next((c for c in countries if c.name == "RestOfWorld"), None)
    if row is None:
        return
    for gi, g in enumerate(grains):
        world_s = float(psd[psd["grain"] == g].groupby("year")["ending_stocks"]
                        .sum().loc[year])
        named_s = 0.0
        for c in countries:
            if c.name == "RestOfWorld":
                continue
            if c.mkt_stock is not None:
                named_s += float(c.mkt_stock[gi])
            if c.gov_stock is not None:
                named_s += float(c.gov_stock[gi])
        rem = max(world_s - named_s, 0.0)
        if row.mkt_stock is None:
            row.mkt_stock = np.zeros(len(grains))
            row.mkt_gamma = np.full(len(grains), 0.05)
            row.mkt_capacity = np.full(len(grains), max(rem, 1.0) * 2.0)
            row.mkt_cost = 5.0
        row.mkt_stock[gi] = rem
        if row.mkt_capacity is not None:
            row.mkt_capacity[gi] = max(float(row.mkt_capacity[gi]), rem * 1.5, 1.0)
