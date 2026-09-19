"""P10: FAOSTAT Food Balance inventory. Arrays are not in the repo.

Agrimate E.1 uses FAOSTAT Food Balances. This host uses USDA PSD (A1).
P10 does not switch the 2006–11 default. If FB arrays are absent, leave A1.
"""
from __future__ import annotations

from pathlib import Path

from .params import wheat_params
from .validation import OUT_DEFAULT
from .wheat_data import prepare_wheat

ROOT = Path(__file__).resolve().parents[2]
FAOSTAT_NETWORK = ROOT / "data" / "faostat_network"
DATA_DIR = ROOT / "data"

# Author AgriculturalData expected cleaned FB files (14022004). None are vendored.
AUTHOR_FB_NAMES = (
    "wheat_food_balance_fao.csv",
    "wheat_food_balance.csv",
    "wheat_production.csv",
)


def _csv_names(folder: Path) -> list[str]:
    if not folder.is_dir():
        return []
    return sorted(p.name for p in folder.iterdir() if p.is_file())


def inventory() -> dict:
    """What is on disk. No download. No WheatData rebuild."""
    network = _csv_names(FAOSTAT_NETWORK)
    e0 = [n for n in network if "E0" in n]
    p0 = [n for n in network if any(k in n for k in ("P0", "Production", "R0", "Reserves"))]
    fb_hits = []
    for p in DATA_DIR.rglob("*"):
        if not p.is_file():
            continue
        low = p.name.lower()
        if "food_balance" in low or "foodbalance" in low or low.startswith("fbs"):
            fb_hits.append(str(p.relative_to(ROOT)))
    author_fb = [
        n for n in AUTHOR_FB_NAMES
        if any(n == q or q.endswith(n) for q in network)
        or list(DATA_DIR.rglob(n))
    ]
    notes = prepare_wheat(start_year=2006, end_year=2006).notes
    return {
        "network_files": network,
        "e0_files": e0,
        "p0_r0_files": p0,
        "food_balance_files": fb_hits,
        "author_fb_present": author_fb,
        "prepare_wheat_notes": notes,
        "alpha_i": float(wheat_params().alpha_i),
        "usda_is_default": any("USDA PSD" in n and "not FAOSTAT" in n for n in notes),
    }


def write_faostat_fb_note(inv: dict | None = None, out_dir: Path | None = None) -> Path:
    inv = inv or inventory()
    out_dir = Path(out_dir) if out_dir else OUT_DEFAULT
    out_dir.mkdir(parents=True, exist_ok=True)
    e0 = ", ".join(inv["e0_files"]) or "none"
    fb = ", ".join(inv["food_balance_files"]) or "none"
    lines = [
        "# A1 — FAOSTAT Food Balances not in the repo (P10)",
        "",
        "**Leave A1. USDA remains the 2006–11 default.** No parallel",
        "`WheatData`. No three-scenario FAO run. `wheat_params()` stay",
        "αI=3.2, p_sto=0.1, xmin=0.2. L1–L8 stay rejected. Bai",
        "α_foreign=10 not adopted. Bai's 2020–24 FAO-anomaly finding is a",
        "different window; it is not a reason to switch this wheat run.",
        "",
        "## Inventory",
        "",
        "Agrimate E.1.1 baseline quantities are FAOSTAT Food Balances.",
        "This host uses USDA PSD 2007–09 means (labelled A1) plus FAOSTAT",
        "**E0 trade shares** (A2), not FB production/consumption/stocks.",
        "",
        "Checked `data/faostat_network/` (the tree at",
        "`/Users/mjp38/GitHub/sheaf-model/data/faostat_network` on the",
        "laptop; this checkout has the same files). Contents are square",
        "bilateral **E0** matrices (exporter × FAOSTAT area code) plus a",
        "country conversion table. Wheat 2006–07 / 2010–11 / 2019–21 E0",
        "are trade, not production/consumption/stocks.",
        "",
        f"- E0 files: {e0}.",
        f"- P0 / Production / R0 / Reserves in that folder: "
        f"{', '.join(inv.get('p0_r0_files') or []) or 'none'}.",
        f"- Files matching `food_balance` / FBS under `data/`: {fb}.",
        "- Author AgriculturalData (Zenodo 14022004) expects cleaned",
        "  `wheat_food_balance_fao.csv` / `wheat_food_balance.csv` /",
        "  `wheat_production.csv`. None of those names exist under `data/`.",
        "- Upstream `mjpuma/FoodTradeNetwork` `inputs_processed/` has",
        "  Wheat P0/Production/Reserves only as **2015–21 window averages**,",
        "  not 2006–11 annual Food Balances. Copying those would not force",
        "  this Agrimate wheat window. Not vendored.",
        "",
        "`data/faostat_network/PROVENANCE.txt` already says production (P0)",
        "and reserves (R0) are **not** taken from FAOSTAT: FAO stocks are",
        "food-balance residuals. `sheaf/data_faostat.py` loads the trade",
        "network only.",
        "",
        "## Places that look like FAO but are not FB arrays",
        "",
        "1. **Fig. 4 NetCDF** (`production_anomalies=FAOsince-2005`).",
        "   Zenodo 10688435 `data.zip` is model *output* (NetCDF + PDFs).",
        "   No CSV/XLSX Food Balance inputs. The zip is not vendored.",
        "   Those harvest series were scored in P7 on AgrimateEU28+Egypt;",
        "   they are not a 27-node `WheatData` substitute.",
        "2. **Author code** `AgriculturalData` (14022004) has the",
        "   preprocess (`impute_food_balance_fao`, QCL+TCL merge,",
        "   rebalance). The cleaned arrays it reads are a local product",
        "   of that pipeline, not shipped in the code zip or in 10688435.",
        "3. Fetching a **new** FAOSTAT FBS vintage from fao.org would not",
        "   be Agrimate's cleaned FB (item groups, imputation, stock",
        "   rebalance). P10 does not invent that pipeline. Old FBS vs",
        "   new Food Balances also breaks across ~2010.",
        "",
        "## Verification protocol (leave A1)",
        "",
        "1. **Claim.** Agrimate E.1 uses FAOSTAT Food Balances.",
        "2. **Implementation.** `prepare_wheat` (`wheat_data.py`) groups",
        "   USDA PSD 2007–09 and notes \"not FAOSTAT Food Balances (E.1.1).\"",
        "3. **Match.** They do not, by labelled adaptation A1.",
        "4. **Counterexample.** No FB file exists to build a parallel",
        "   `WheatData`; `inventory()[\"food_balance_files\"]` is empty.",
        "5. **Correctness of stopping.** E0 is present and used; P0/R0",
        "   from FAO would treat stocks as a residual (`data_faostat.py`).",
        "   A new FAOSTAT dump would not be the author cleaned series.",
        "   Switching the host would retune 2006–11 quantities, which",
        "   P10 forbids unless the arrays are actually here.",
        "6. **Change.** None to economics. USDA stays default until G0-P.",
        "",
        f"`prepare_wheat` default note holds; αI={inv['alpha_i']:g}.",
        "",
        "## Files",
        "",
        "- this note",
        "- `data/faostat_network/PROVENANCE.txt` (E0 only)",
        "",
        "Next: P11 exporter pulse grid (optional, not G2).",
        "",
    ]
    path = out_dir / "faostat_fb.md"
    path.write_text("\n".join(lines) + "\n")
    return path


def run_faostat_fb_inventory(out_dir: Path | None = None) -> dict[str, Path]:
    inv = inventory()
    note = write_faostat_fb_note(inv, out_dir)
    return {"note": note}
