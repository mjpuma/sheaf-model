#!/usr/bin/env python3
"""Fetch / refresh external validation inputs into data/.

USDA PSD (per-country bulk) downloads directly from FAS (no API key).
AMIS/OECD export-restrictions: converts a browser-downloaded XLSX into CSVs
(oecd.org blocks unattended bots via Cloudflare).
"""
from __future__ import annotations

import argparse
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
PSD_DIR = ROOT / "data" / "usda_psd"
AMIS_DIR = ROOT / "data" / "amis_policies"
PSD_URL = "https://apps.fas.usda.gov/psdonline/downloads/psd_alldata_csv.zip"

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
        "amis_page": "https://www.amis-outlook.org/policy-database/introduction",
        "n_aggregated_rows": int(len(agg)),
        "n_detailed_rows": int(len(det)),
    }
    (AMIS_DIR / "DOWNLOAD_META.json").write_text(json.dumps(meta, indent=2))
    print(f"AMIS CSVs refreshed from {xlsx.name} "
          f"(agg={len(agg)}, detail={len(det)}).")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--psd-only", action="store_true")
    ap.add_argument("--amis-only", action="store_true")
    ap.add_argument("--amis-xlsx", type=Path, default=None,
                    help="Path to a browser-downloaded OECD/AMIS XLSX")
    args = ap.parse_args()
    if args.amis_only:
        refresh_amis_csvs(args.amis_xlsx)
    elif args.psd_only:
        fetch_psd()
    else:
        fetch_psd()
        refresh_amis_csvs(args.amis_xlsx)


if __name__ == "__main__":
    main()
