#!/usr/bin/env python3
"""Fetch / refresh external validation inputs into data/.

USDA PSD (per-country bulk) downloads directly from FAS (no API key).
AMIS/OECD export-restrictions: converts a browser-downloaded XLSX into CSVs
(oecd.org blocks unattended bots via Cloudflare).
World Bank Pink Sheet annual prices: discovered from the Commodity Markets page
(download URL hash changes monthly).
"""
from __future__ import annotations

import argparse
import json
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import urllib.request
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PSD_DIR = ROOT / "data" / "usda_psd"
AMIS_DIR = ROOT / "data" / "amis_policies"
PRICE_DIR = ROOT / "data" / "world_prices"
PSD_URL = "https://apps.fas.usda.gov/psdonline/downloads/psd_alldata_csv.zip"
WB_COMMODITY_PAGE = "https://www.worldbank.org/en/research/commodity-markets"

# Pink Sheet commodity column → SHEAF grain
_PINK_SERIES = {
    "wheat": "Wheat, US HRW",
    "maize": "Maize",
    "rice": "Rice, Thai 5% ",
}

GRAIN_MAP = {
    "Wheat": "wheat",
    "Rice, Milled": "rice",
    "Corn": "maize",
}
ATTRS = {
    "Beginning Stocks", "Domestic Consumption", "Ending Stocks", "Production",
    "Imports", "Exports", "Total Supply", "Total Distribution",
}


def fetch_psd() -> None:
    PSD_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = PSD_DIR / "psd_alldata_csv.zip"
    print(f"Downloading {PSD_URL} ...")
    urllib.request.urlretrieve(PSD_URL, zip_path)
    print(f"  wrote {zip_path} ({zip_path.stat().st_size / 1e6:.1f} MB)")
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(PSD_DIR)
    csv_path = PSD_DIR / "psd_alldata.csv"
    _build_grain_extracts(csv_path)
    meta = {
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_url": PSD_URL,
        "source": "USDA FAS PSD Online Downloadable Data Sets",
    }
    (PSD_DIR / "DOWNLOAD_META.json").write_text(json.dumps(meta, indent=2))
    print("PSD refresh complete.")


def _build_grain_extracts(csv_path: Path) -> None:
    chunks = []
    for chunk in pd.read_csv(csv_path, chunksize=200_000):
        m = (chunk["Commodity_Description"].isin(GRAIN_MAP)
             & chunk["Attribute_Description"].isin(ATTRS))
        if m.any():
            chunks.append(chunk.loc[m])
    sub = pd.concat(chunks, ignore_index=True)
    sub["grain"] = sub["Commodity_Description"].map(GRAIN_MAP)
    sub.to_csv(PSD_DIR / "psd_grains_long.csv", index=False)
    piv = (sub.pivot_table(
        index=["Country_Code", "Country_Name", "Market_Year", "grain"],
        columns="Attribute_Description", values="Value", aggfunc="sum")
        .reset_index())
    piv.columns.name = None
    piv.to_csv(PSD_DIR / "psd_grains_country_year.csv", index=False)
    print(f"  grains extract: {len(sub)} rows, "
          f"{sub.Country_Name.nunique()} countries, "
          f"{int(sub.Market_Year.min())}-{int(sub.Market_Year.max())}")


def refresh_amis_csvs(xlsx: Path | None = None) -> None:
    AMIS_DIR.mkdir(parents=True, exist_ok=True)
    xlsx = xlsx or (AMIS_DIR / "oecd_export_restrictions_staple_crops.xlsx")
    if not xlsx.exists():
        raise SystemExit(
            f"Missing {xlsx}. Download the XLSX from\n"
            "  https://www.oecd.org/en/topics/sub-issues/agro-food-trade/"
            "export-restrictions-on-staple-crops.html\n"
            "and save it to that path, then re-run with --amis-only."
        )
    agg = pd.read_excel(xlsx, sheet_name="AggregatedDatabase")
    det = pd.read_excel(xlsx, sheet_name="DetailedDatabase")
    agg.to_csv(AMIS_DIR / "export_restrictions_aggregated.csv", index=False)
    det.to_csv(AMIS_DIR / "export_restrictions_detailed.csv", index=False)
    meta = {
        "refreshed_at_utc": datetime.now(timezone.utc).isoformat(),
        "workbook": str(xlsx.relative_to(ROOT)),
        "official_oecd_page":
            "https://www.oecd.org/en/topics/sub-issues/agro-food-trade/"
            "export-restrictions-on-staple-crops.html",
        "amis_page": "https://amis-outlook.org/policy-database/introduction",
        "n_aggregated_rows": int(len(agg)),
        "n_detailed_rows": int(len(det)),
    }
    (AMIS_DIR / "DOWNLOAD_META.json").write_text(json.dumps(meta, indent=2))
    print(f"AMIS CSVs refreshed from {xlsx.name} "
          f"(agg={len(agg)}, detail={len(det)}).")


def _discover_pink_sheet_url(kind: str = "Annual") -> str:
    """Parse the Commodity Markets page for Annual or Monthly XLSX URL."""
    req = urllib.request.Request(
        WB_COMMODITY_PAGE, headers={"User-Agent": "sheaf-model/0.1"})
    html = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
    label = "Annual" if kind.lower().startswith("a") else "Monthly"
    for pat in (rf'https://[^"\'\s>]+CMO-Historical-Data-{label}\.xlsx',
                rf'https://[^"\'\s>]+CMO-Historical-Data-{label}\.xls'):
        m = re.search(pat, html, flags=re.I)
        if m:
            return m.group(0)
    raise RuntimeError(
        f"Could not find CMO-Historical-Data-{label} link on {WB_COMMODITY_PAGE}")


def _discover_pink_sheet_annual_url() -> str:
    return _discover_pink_sheet_url("Annual")


def _pink_sheet_to_grains_csv(xlsx: Path, out_csv: Path) -> pd.DataFrame:
    def _clean(sheet: str) -> pd.DataFrame:
        df = pd.read_excel(xlsx, sheet_name=sheet, header=6)
        df = df.rename(columns={df.columns[0]: "year"})
        df = df[pd.to_numeric(df["year"], errors="coerce").notna()].copy()
        df["year"] = df["year"].astype(int)
        return df

    nom = _clean("Annual Prices (Nominal)")
    real = _clean("Annual Prices (Real)")
    rows = []
    for grain, col in _PINK_SERIES.items():
        if col not in nom.columns or col not in real.columns:
            cand = [c for c in nom.columns
                    if isinstance(c, str) and c.strip() == col.strip()]
            if not cand:
                raise KeyError(f"Pink Sheet missing series {col!r}")
            col = cand[0]
        for y in sorted(set(nom.year) & set(real.year)):
            def _f(v):
                try:
                    return float(v)
                except (TypeError, ValueError):
                    return float("nan")
            rows.append(dict(
                year=int(y), grain=grain,
                price_nominal_usd_mt=_f(nom.loc[nom.year == y, col].iloc[0]),
                price_real_2010_usd_mt=_f(real.loc[real.year == y, col].iloc[0]),
                source_series=str(col).strip(),
            ))
    out = pd.DataFrame(rows).sort_values(["grain", "year"])
    out.to_csv(out_csv, index=False)
    return out


def _pink_sheet_monthly_to_grains_csv(xlsx: Path, out_csv: Path,
                                      annual_csv: Path | None = None) -> pd.DataFrame:
    """Extract monthly grains (nominal only in Pink Sheet) and MUV-deflate.

    Monthly workbook has no Real sheet. We deflate each month by that year's
    annual real/nominal ratio for the same series (constant within year).
    """
    raw = pd.read_excel(xlsx, sheet_name="Monthly Prices", header=4)
    raw = raw.rename(columns={raw.columns[0]: "ym"})
    raw = raw[raw["ym"].astype(str).str.match(r"^\d{4}M\d{2}$", na=False)].copy()
    raw["year"] = raw["ym"].astype(str).str.slice(0, 4).astype(int)
    raw["month"] = raw["ym"].astype(str).str.slice(5, 7).astype(int)

    # Annual real/nominal ratios for deflation
    annual_csv = annual_csv or (PRICE_DIR / "pink_sheet_grains_annual.csv")
    if not Path(annual_csv).exists():
        raise FileNotFoundError(
            f"{annual_csv} required to deflate monthly prices — fetch annual first")
    ann = pd.read_csv(annual_csv)
    ann["deflator"] = (ann["price_real_2010_usd_mt"]
                       / ann["price_nominal_usd_mt"])

    rows = []
    for grain, col in _PINK_SERIES.items():
        if col not in raw.columns:
            cand = [c for c in raw.columns
                    if isinstance(c, str) and c.strip() == col.strip()]
            if not cand:
                raise KeyError(f"Pink Sheet monthly missing {col!r}")
            col = cand[0]

        def _f(v):
            try:
                return float(v)
            except (TypeError, ValueError):
                return float("nan")

        for _, row in raw.iterrows():
            nom = _f(row[col])
            dsub = ann[(ann.grain == grain) & (ann.year == int(row["year"]))]
            defl = float(dsub["deflator"].iloc[0]) if len(dsub) and np.isfinite(
                dsub["deflator"].iloc[0]) else float("nan")
            rows.append(dict(
                year=int(row["year"]), month=int(row["month"]), grain=grain,
                price_nominal_usd_mt=nom,
                price_real_2010_usd_mt=(nom * defl) if np.isfinite(nom) and np.isfinite(defl)
                else float("nan"),
                source_series=str(col).strip(),
            ))
    out = pd.DataFrame(rows).sort_values(["grain", "year", "month"])
    out.to_csv(out_csv, index=False)
    return out


def fetch_prices() -> None:
    PRICE_DIR.mkdir(parents=True, exist_ok=True)
    # Annual
    url_a = _discover_pink_sheet_url("Annual")
    xlsx_a = PRICE_DIR / "CMO-Historical-Data-Annual.xlsx"
    print(f"Downloading {url_a} ...")
    urllib.request.urlretrieve(url_a, xlsx_a)
    print(f"  wrote {xlsx_a} ({xlsx_a.stat().st_size / 1e3:.0f} KB)")
    out_a = PRICE_DIR / "pink_sheet_grains_annual.csv"
    grains_a = _pink_sheet_to_grains_csv(xlsx_a, out_a)
    print(f"  annual grains extract: {len(grains_a)} rows")

    # Monthly (Gate 0 target)
    url_m = _discover_pink_sheet_url("Monthly")
    xlsx_m = PRICE_DIR / "CMO-Historical-Data-Monthly.xlsx"
    print(f"Downloading {url_m} ...")
    urllib.request.urlretrieve(url_m, xlsx_m)
    print(f"  wrote {xlsx_m} ({xlsx_m.stat().st_size / 1e3:.0f} KB)")
    out_m = PRICE_DIR / "pink_sheet_grains_monthly.csv"
    grains_m = _pink_sheet_monthly_to_grains_csv(xlsx_m, out_m)
    print(f"  monthly grains extract: {len(grains_m)} rows")

    meta = {
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_page": WB_COMMODITY_PAGE,
        "source_url_annual": url_a,
        "source_url_monthly": url_m,
        "real_deflator": "World Bank MUV, constant 2010 USD",
        "series": {k: v.strip() for k, v in _PINK_SERIES.items()},
        "n_rows_annual": int(len(grains_a)),
        "n_rows_monthly": int(len(grains_m)),
    }
    (PRICE_DIR / "DOWNLOAD_META.json").write_text(json.dumps(meta, indent=2))
    print("Pink Sheet price refresh complete (annual + monthly).")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--psd-only", action="store_true")
    ap.add_argument("--amis-only", action="store_true")
    ap.add_argument("--prices-only", action="store_true")
    ap.add_argument("--amis-xlsx", type=Path, default=None,
                    help="Path to a browser-downloaded OECD/AMIS XLSX")
    args = ap.parse_args()
    if args.amis_only:
        refresh_amis_csvs(args.amis_xlsx)
    elif args.psd_only:
        fetch_psd()
    elif args.prices_only:
        fetch_prices()
    else:
        fetch_psd()
        refresh_amis_csvs(args.amis_xlsx)
        fetch_prices()


if __name__ == "__main__":
    main()
