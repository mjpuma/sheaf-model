"""Host reconstruction of AgriculturalData.impute_food_balance_fao("wheat").

Sourced algorithm (Zenodo 14022004 AgriculturalData, CC-BY-4.0):
``data_processing.impute_food_balance_fao``, ``item_groups_fao["wheat"]``,
``reverse_stock_variation_sign``, ``remove_aggregate_areas``.

This is **not** Kuhla's unpublished local CSV (not bit-identical). The
window is the vendored FBSH 2006–11 extract, not the author's full
history. Rebalance / trade-harmonization are later pipeline steps and
are **not** applied (timeseries reads this imputed file). USDA remains
``prepare_wheat`` default. FBSH element 5074 is ΔS after the sourced
sign flip; it is never a stock *level*.
"""
from __future__ import annotations

import csv
import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from sheaf.data_faostat import _mappings

from .faostat_fb import FAOSTAT_FB, inventory
from .params import wheat_params
from .validation import OUT_DEFAULT
from .wheat_data import prepare_wheat

ROOT = Path(__file__).resolve().parents[2]
QCL_TCL_DIR = ROOT / "data" / "faostat_qcl_tcl"
FOOD_BALANCES = ROOT / "data" / "food_balances"
OUT_CSV = FOOD_BALANCES / "wheat_food_balance_fao.csv"

YEARS = tuple(range(2006, 2012))
# AgriculturalData.item_groups_fao["wheat"] — Item Code: conversion to primary.
WHEAT_ITEM_FACTORS = {
    15: 1,      # wheat
    16: 1,      # flour
    17: 1,      # bran
    18: 1,      # macaroni
    20: 1.15,   # bread
    22: 1.15,   # pastry
    41: 0.9,    # cereals
    110: 1,     # wafers
    114: 0.9,   # mixes
    115: 0.9,   # preparations
    21: 0.95,   # bulgur
    19: 1,      # germ (no FAO trade data)
    23: 1,      # starch (no FAO trade data)
    24: 1,      # gluten (no FAO trade data)
}
WHEAT_ITEM_CODES = frozenset(WHEAT_ITEM_FACTORS)
# FBSH (old methodology) element names already match AgriculturalData FBS.
FBS_ELEMENTS = (
    "Production",
    "Domestic supply quantity",
    "Import Quantity",
    "Export Quantity",
    "Stock Variation",
)
QCL_URL = (
    "https://bulks-faostat.fao.org/production/"
    "Production_Crops_Livestock_E_All_Data_(Normalized).zip"
)
TCL_URL = (
    "https://bulks-faostat.fao.org/production/"
    "Trade_CropsLivestock_E_All_Data_(Normalized).zip"
)
ELEMENT_CANON = {
    "Production": "Production",
    "Import quantity": "Import Quantity",
    "Export quantity": "Export Quantity",
    "Import Quantity": "Import Quantity",
    "Export Quantity": "Export Quantity",
}
ISO_FIX = {"TMP": "TLS"}  # conversion-table ISO3 alpha vs Agrimate TLS
# China, mainland 41 is CHN; conversion table ISO3 alpha is NULL on that row.
# 351 China total is dropped by remove_aggregate_areas (code >= 350).
KEEP_COLS = [
    "ISO3 Code", "Area", "Area Code", "Year",
    "Production", "Domestic supply quantity",
    "Import Quantity", "Export Quantity", "Stock Variation", "Source",
]


def remove_aggregate_areas(df: pd.DataFrame) -> pd.DataFrame:
    """AgriculturalData.data_cleaning.remove_aggregate_areas."""
    code = df["Area Code"]
    return df[(code < 350) & ~((260 < code) & (code < 270))].copy()


def reverse_stock_variation_sign(df: pd.DataFrame) -> pd.DataFrame:
    """AgriculturalData.data_cleaning.reverse_stock_variation_sign."""
    out = df.copy()
    out["Value"] = out["Value"].astype(float)
    out.loc[out["Element"] == "Stock Variation", "Value"] *= -1
    return out


def convert_to_primary_equivalent(df: pd.DataFrame) -> pd.DataFrame:
    """AgriculturalData.data_processing.convert_to_primary_equivalent(wheat).

    The sourced ``impute_food_balance_fao`` converts a local ``df_trade``
    then divides ``dfs["trade"]`` by 1000. Those are distinct objects, so
    the conversion would be dropped. This reconstruction applies the
    conversion to the frame that is pivoted (the intended pipeline).
    """
    factors = pd.Series(WHEAT_ITEM_FACTORS, name="Conversion Factor")
    out = df.join(factors, on="Item Code")
    missing = out["Conversion Factor"].isna()
    out = out.loc[~missing].copy()
    out["Value"] = out["Value"].astype(float) / out["Conversion Factor"]
    return out.drop(columns="Conversion Factor")


def _area_codes_table(frames: list[pd.DataFrame]) -> pd.DataFrame:
    """Area Code → Area name + ISO3. Names from FAOSTAT rows; ISO3 from A2 table."""
    parts = []
    for df in frames:
        if df.empty:
            continue
        parts.append(df[["Area Code", "Area"]].drop_duplicates())
    names = pd.concat(parts, ignore_index=True).drop_duplicates("Area Code")
    fao2iso, _name2iso, _valid = _mappings()
    iso = names["Area Code"].map(lambda c: fao2iso.get(int(c)))
    iso = iso.map(lambda s: ISO_FIX.get(s, s) if isinstance(s, str) else s)
    return pd.DataFrame({
        "Area": names["Area"].to_numpy(),
        "Area Code": names["Area Code"].to_numpy(),
        "ISO3 Code": iso.to_numpy(),
    })


def load_fbsh_as_fbs() -> pd.DataFrame:
    """Map vendored FBSH long extract onto AgriculturalData FBS element names."""
    path = FAOSTAT_FB / "wheat_fbsh_2006_2011_long.csv"
    if not path.is_file():
        raise FileNotFoundError(
            f"{path} missing — run: PYTHONPATH=. python "
            "scripts/fetch_external_data.py --faostat-fb"
        )
    raw = pd.read_csv(path)
    raw["Element"] = raw["element"].astype(str)
    keep = raw["Element"].isin(FBS_ELEMENTS)
    df = raw.loc[keep, ["area_code", "area", "year", "Element", "value"]].copy()
    df = df.rename(columns={
        "area_code": "Area Code",
        "area": "Area",
        "year": "Year",
        "value": "Value",
    })
    df["Area Code"] = df["Area Code"].astype(int)
    df["Year"] = df["Year"].astype(int)
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce")
    df = reverse_stock_variation_sign(df)
    df = remove_aggregate_areas(df)
    return df


def load_qcl_production() -> pd.DataFrame:
    path = QCL_TCL_DIR / "wheat_qcl_2006_2011.csv"
    if not path.is_file():
        raise FileNotFoundError(
            f"{path} missing — run: PYTHONPATH=. python "
            "scripts/fetch_external_data.py --faostat-qcl-tcl"
        )
    df = pd.read_csv(path)
    df["Element"] = df["Element"].map(lambda s: ELEMENT_CANON.get(str(s), str(s)))
    df = df[df["Element"] == "Production"].copy()
    df["Area Code"] = df["Area Code"].astype(int)
    df["Item Code"] = df["Item Code"].astype(int)
    df["Year"] = df["Year"].astype(int)
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce")
    df = df[df["Item Code"].isin(WHEAT_ITEM_CODES)]
    df = df[df["Year"].isin(YEARS)]
    df = remove_aggregate_areas(df)
    return df


def load_tcl_trade() -> pd.DataFrame:
    path = QCL_TCL_DIR / "wheat_tcl_2006_2011.csv"
    if not path.is_file():
        raise FileNotFoundError(
            f"{path} missing — run: PYTHONPATH=. python "
            "scripts/fetch_external_data.py --faostat-qcl-tcl"
        )
    df = pd.read_csv(path)
    df["Element"] = df["Element"].map(lambda s: ELEMENT_CANON.get(str(s), str(s)))
    df = df[df["Element"].isin(("Import Quantity", "Export Quantity"))].copy()
    df["Area Code"] = df["Area Code"].astype(int)
    df["Item Code"] = df["Item Code"].astype(int)
    df["Year"] = df["Year"].astype(int)
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce")
    df = df[df["Item Code"].isin(WHEAT_ITEM_CODES)]
    df = df[df["Year"].isin(YEARS)]
    df = remove_aggregate_areas(df)
    return df


def impute_food_balance_fao() -> pd.DataFrame:
    """Sourced AgriculturalData.impute_food_balance_fao for wheat, 2006–11."""
    df_fbs = load_fbsh_as_fbs()
    df_prod = load_qcl_production()
    df_trade = load_tcl_trade()
    area_codes = _area_codes_table([df_fbs, df_prod, df_trade])

    df_trade = convert_to_primary_equivalent(df_trade)
    dfs = {"fbs": df_fbs, "prod": df_prod, "trade": df_trade}
    # QCL/TCL are tonnes; FBS is already 1000 t.
    for key in ("prod", "trade"):
        dfs[key] = dfs[key].copy()
        dfs[key]["Value"] = dfs[key]["Value"].astype(float) / 1000.0

    for key in dfs:
        dfs[key] = dfs[key].pivot_table(
            index=["Area Code", "Year"],
            columns="Element",
            values="Value",
            aggfunc="sum",
            fill_value=0,
        )

    df_prod_trade = pd.merge(
        dfs["prod"], dfs["trade"], left_index=True, right_index=True, how="outer",
    )
    df_prod_trade = df_prod_trade.fillna(0)
    df_prod_trade = df_prod_trade[(df_prod_trade > 0.0).any(axis=1)]
    net = (
        df_prod_trade["Production"]
        + df_prod_trade["Import Quantity"]
        - df_prod_trade["Export Quantity"]
    )
    df_prod_trade["Domestic supply quantity"] = np.maximum(net, 0)
    df_prod_trade["Stock Variation"] = np.minimum(net, 0)
    df_prod_trade = df_prod_trade.round(3)

    dfs["fbs"]["Source"] = "FBS"
    df_prod_trade["Source"] = "QCL+TCL"

    df = pd.merge(
        dfs["fbs"], df_prod_trade,
        left_index=True, right_index=True, how="outer",
        suffixes=("", " QCL+TCL"),
    )
    columns = [
        "Production", "Domestic supply quantity",
        "Import Quantity", "Export Quantity", "Stock Variation", "Source",
    ]
    no_fbs = df[columns].isna().any(axis=1)
    for col in columns:
        df.loc[no_fbs, col] = df.loc[no_fbs, f"{col} QCL+TCL"]
    df = df.reset_index()
    df = pd.merge(df, area_codes, on="Area Code", how="left")
    df = df[KEEP_COLS].sort_values(by=["ISO3 Code", "Year"])
    return df.reset_index(drop=True)


def write_wheat_food_balance_fao(df: pd.DataFrame | None = None) -> Path:
    FOOD_BALANCES.mkdir(parents=True, exist_ok=True)
    df = df if df is not None else impute_food_balance_fao()
    df.to_csv(OUT_CSV, index=False)
    return OUT_CSV


def write_provenance(df: pd.DataFrame) -> Path:
    FOOD_BALANCES.mkdir(parents=True, exist_ok=True)
    n_fbs = int((df["Source"] == "FBS").sum())
    n_qcl = int((df["Source"] == "QCL+TCL").sum())
    usa = df[(df["Area"] == "United States of America") & (df["Year"] == 2007)]
    chn = df[(df["Area"] == "China, mainland") & (df["Year"] == 2007)]
    usa_p = float(usa["Production"].iloc[0]) if len(usa) else float("nan")
    chn_p = float(chn["Production"].iloc[0]) if len(chn) else float("nan")
    text = "\n".join([
        "Host reconstruction of AgriculturalData.impute_food_balance_fao(\"wheat\").",
        "",
        "What this file is",
        "  wheat_food_balance_fao.csv  — imputed FAO food-balance table for",
        "  wheat, years 2006–2011, unit 1000 t. Columns match the sourced",
        "  AgriculturalData output: ISO3 Code, Area, Area Code, Year,",
        "  Production, Domestic supply quantity, Import Quantity,",
        "  Export Quantity, Stock Variation, Source (FBS or QCL+TCL).",
        "",
        "What this file is not",
        "  Not Kuhla's unpublished local CSV (not bit-identical).",
        "  Not a prepare_wheat switch. USDA PSD remains the 2006–11 default (A1).",
        "  Not FoodTradeNetwork 2015–21 P0/R0 averages.",
        "  Not FBS 2010+ (new methodology) mixed into FBSH.",
        "  Not rebalanced / trade-harmonized (those are later pipeline steps;",
        "  Agrimate timeseries.py reads this imputed file).",
        "  Stock Variation is ΔS (FBSH 5074, sign-flipped per sourced",
        "  reverse_stock_variation_sign). It is not USDA ending stocks.",
        "  Do not treat 5074 as a stock level.",
        "",
        "Algorithm (Zenodo 14022004 AgriculturalData, CC-BY-4.0)",
        "  1. FBS = vendored FBSH wheat item 2511, 2006–11, unit 1000 t.",
        "     reverse_stock_variation_sign (Stock Variation × −1).",
        "     remove_aggregate_areas (Area Code < 350, drop 260–270).",
        "  2. QCL Production (item 15 Wheat, tonnes / 1000).",
        "  3. TCL Import/Export Quantity for item_groups_fao wheat codes,",
        "     converted to primary equivalent, tonnes / 1000.",
        "  4. For area-years missing FBS: Domestic supply = max(P+I−X, 0);",
        "     Stock Variation = min(P+I−X, 0); Source = QCL+TCL.",
        "  5. ISO3 from data/faostat_network/country_conversion_table.csv",
        "     plus data_faostat aliases (41→CHN, 107→CIV, 214→TWN) and TMP→TLS.",
        "",
        "Labelled adaptations vs the unpublished author product",
        "  Window 2006–11 only (vendored FBSH), not the author's longer span.",
        "  Current FAOSTAT QCL/TCL vintages (downloaded this reconstruction),",
        "  not whatever dump Kuhla cleaned locally.",
        "  Sourced impute converted a copy of df_trade then divided the",
        "  unconverted dfs['trade']; reconstruction applies conversion to the",
        "  pivoted frame (intended pipeline).",
        "  Belgium-Luxembourg (15) is kept (author remove_aggregate_areas);",
        "  the FBSH WheatData parallel still drops it as a duplicate total.",
        "",
        "Sanity (2007 Production, 1000 t, Source=FBS)",
        f"  United States of America {usa_p:.3f} (FBSH 55820).",
        f"  China, mainland {chn_p:.3f} (FBSH 109298).",
        f"  Rows: {len(df)} (FBS {n_fbs}; QCL+TCL imputed {n_qcl}).",
        "",
        "Refresh",
        "  PYTHONPATH=. python scripts/fetch_external_data.py --faostat-qcl-tcl",
        "  PYTHONPATH=. python scripts/build_author_fb_fao.py",
        "  Does not change wheat_params or prepare_wheat. Not G0-P acceptance.",
        "",
    ]) + "\n"
    path = FOOD_BALANCES / "PROVENANCE.txt"
    path.write_text(text)
    return path


def write_author_fb_note(df: pd.DataFrame | None = None,
                         out_dir: Path | None = None) -> Path:
    df = df if df is not None else pd.read_csv(OUT_CSV)
    out_dir = Path(out_dir) if out_dir else OUT_DEFAULT
    out_dir.mkdir(parents=True, exist_ok=True)
    inv = inventory()
    n_fbs = int((df["Source"] == "FBS").sum())
    n_qcl = int((df["Source"] == "QCL+TCL").sum())
    usa = df[(df["Area"] == "United States of America") & (df["Year"] == 2007)]
    chn = df[(df["Area"] == "China, mainland") & (df["Year"] == 2007)]
    egypt = df[df["Area"].astype(str).str.contains("Egypt", case=False, na=False)]
    notes = prepare_wheat(start_year=2006, end_year=2006).notes
    lines = [
        "# Author cleaned wheat_food_balance_fao.csv — host reconstruction",
        "",
        "**Leave A1. USDA remains the 2006–11 `prepare_wheat` default.**",
        "This file is a labelled reconstruction of AgriculturalData",
        "`impute_food_balance_fao(\"wheat\")` (Zenodo 14022004), not Kuhla's",
        "unpublished local CSV, and **not adopted** as the host. Do not",
        "silently replace C.1. Do not invent an Egypt node. Fig. 4 knobs",
        "stay on `fig4_experiment_params()`. `wheat_params()` stay αI=3.2,",
        "p_sto=0.1, xmin=0.2, ζ=0, N_for=3. L1–L8 stay rejected. Bai",
        "α_foreign=10 not adopted. FBSH 5074 is ΔS, never S.",
        "",
        "## What was created",
        "",
        f"- `{OUT_CSV.relative_to(ROOT)}` ({len(df)} rows;",
        f"  FBS {n_fbs}; QCL+TCL imputed {n_qcl}).",
        "- Columns: ISO3 Code, Area, Area Code, Year, Production,",
        "  Domestic supply quantity, Import Quantity, Export Quantity,",
        "  Stock Variation, Source.",
        "- Years 2006–2011. Unit 1000 t.",
        f"- 2007 Production: USA {float(usa['Production'].iloc[0]):.3f};",
        f"  China, mainland {float(chn['Production'].iloc[0]):.3f}.",
        f"- Egypt rows in this table: {len(egypt)} (ISO3 EGY if mapped;",
        "  **not** added to the 27-node C.1 list).",
        f"- inventory()[\"food_balance_files\"]: {inv['food_balance_files']}.",
        f"- USDA is default: {inv['usda_is_default']}; αI={inv['alpha_i']:g}.",
        "",
        "## Verification protocol",
        "",
        "1. **Claim.** Agrimate E.1 uses cleaned FAOSTAT Food Balances",
        "   (`wheat_food_balance_fao.csv` from `impute_food_balance_fao`).",
        "2. **Implementation.** `prepare_wheat` still groups USDA PSD",
        "   2007–09 and notes \"not FAOSTAT Food Balances (E.1.1).\"",
        "3. **Match.** File now exists as a **host reconstruction**, not a",
        "   bit-identical author dump. Host quantities are still USDA (A1).",
        "4. **Counterexample.** `prepare_wheat` notes still say USDA PSD,",
        f"   not FAOSTAT: {any('USDA PSD' in n and 'not FAOSTAT' in n for n in notes)}.",
        "   Stock Variation here is sign-flipped FBSH 5074 (ΔS), not",
        "   USDA `ending_stocks`.",
        "5. **Correctness of not switching.** S3 already scored raw FBSH",
        "   H/C vs member-sum USDA: moy worsened 20.1×→33.0×; items 1–3",
        "   did not improve. This reconstruction does not add EU28+Egypt",
        "   or start-2000. Switching would retune 2006–11 quantities.",
        "6. **Change.** Write the labelled CSV. Do not change economics.",
        "",
        "## Remaining A7 cannot-set",
        "",
        "- AgrimateEU28 + Egypt extra node (host is AgrimateRegionsWheat).",
        "- start 2000-01-01.",
        "- FAO production anomalies since 2005.",
        "- Bit-identical author local `wheat_food_balance_fao.csv`.",
        "- Zenodo 14022004 Julia (not vendored).",
        "",
        "Next paste: **S4** (A7 cannot-set inventory). Not G1. Do not",
        "retune αI / p_sto / xmin. Do not adopt this file as prepare_wheat.",
        "",
    ]
    path = out_dir / "author_fb.md"
    path.write_text("\n".join(lines) + "\n")
    return path


def extract_wheat_from_zip(zip_path: Path, domain: str, out_path: Path) -> int:
    """Filter a FAOSTAT QCL/TCL normalized zip to wheat 2006–11 quantity rows."""
    if domain == "QCL":
        member = "Production_Crops_Livestock_E_All_Data_(Normalized).csv"
        keep = {"Production"}
    elif domain == "TCL":
        member = "Trade_CropsLivestock_E_All_Data_(Normalized).csv"
        keep = {"Import quantity", "Export quantity", "Import Quantity", "Export Quantity"}
    else:
        raise ValueError(domain)
    cols = ["Area Code", "Area", "Item Code", "Item", "Element", "Year", "Unit", "Value", "Flag"]
    rows = []
    with zipfile.ZipFile(zip_path) as zf:
        with zf.open(member) as raw:
            text = io.TextIOWrapper(raw, encoding="utf-8-sig", errors="replace", newline="")
            reader = csv.DictReader(text)
            for rec in reader:
                try:
                    item = int(float(rec["Item Code"]))
                    year = int(float(rec["Year"]))
                except (TypeError, ValueError):
                    continue
                if item not in WHEAT_ITEM_CODES or year not in YEARS:
                    continue
                el = rec["Element"].strip()
                if el not in keep:
                    continue
                rows.append({
                    "Area Code": rec["Area Code"],
                    "Area": rec["Area"],
                    "Item Code": item,
                    "Item": rec["Item"],
                    "Element": ELEMENT_CANON[el],
                    "Year": year,
                    "Unit": rec["Unit"],
                    "Value": rec["Value"],
                    "Flag": rec.get("Flag", ""),
                })
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def write_qcl_tcl_meta(n_qcl: int, n_tcl: int, extra: dict | None = None) -> Path:
    QCL_TCL_DIR.mkdir(parents=True, exist_ok=True)
    meta = {
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "qcl_source_url": QCL_URL,
        "tcl_source_url": TCL_URL,
        "years": list(YEARS),
        "wheat_item_codes": sorted(WHEAT_ITEM_CODES),
        "n_qcl_rows": int(n_qcl),
        "n_tcl_rows": int(n_tcl),
        "note": (
            "FAOSTAT QCL Production + TCL trade quantity extracts for wheat "
            "2006-11. Intermediate inputs to the host reconstruction of "
            "impute_food_balance_fao. Not a prepare_wheat switch. Not FBS 2010+."
        ),
    }
    if extra:
        meta.update(extra)
    path = QCL_TCL_DIR / "DOWNLOAD_META.json"
    path.write_text(json.dumps(meta, indent=2) + "\n")
    return path


def run_author_fb(out_dir: Path | None = None) -> dict[str, Path]:
    df = impute_food_balance_fao()
    csv_path = write_wheat_food_balance_fao(df)
    prov = write_provenance(df)
    note = write_author_fb_note(df, out_dir)
    assert wheat_params().alpha_i == 3.2
    return {"csv": csv_path, "provenance": prov, "note": note}
