"""P10/R6 obtain: FAOSTAT Food Balance inventory.

Agrimate E.1 uses FAOSTAT Food Balances. This host uses USDA PSD (A1).
Raw FBSH wheat 2006–11 is vendored under data/faostat_fb/. A labelled
host reconstruction of wheat_food_balance_fao.csv lives under
data/food_balances/ (not bit-identical author output; not adopted).
USDA remains prepare_wheat default.
"""
from __future__ import annotations

from pathlib import Path

from .params import wheat_params
from .validation import OUT_DEFAULT
from .wheat_data import prepare_wheat

ROOT = Path(__file__).resolve().parents[2]
FAOSTAT_NETWORK = ROOT / "data" / "faostat_network"
FAOSTAT_FB = ROOT / "data" / "faostat_fb"
DATA_DIR = ROOT / "data"
LAPTOP_DATA = Path("/Users/mjp38/GitHub/sheaf-model/data")

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


def _author_fb_hits() -> list[str]:
    """Agrimate cleaned AgriculturalData names only (not raw FBSH)."""
    found: list[str] = []
    for n in AUTHOR_FB_NAMES:
        hits = [p for p in DATA_DIR.rglob(n) if p.is_file()]
        found.extend(str(p.relative_to(ROOT)) for p in hits)
    return found


def inventory() -> dict:
    """What is on disk. No download. No WheatData rebuild."""
    network = _csv_names(FAOSTAT_NETWORK)
    e0 = [n for n in network if "E0" in n]
    p0 = [n for n in network if any(k in n for k in ("P0", "Production", "R0", "Reserves"))]
    fb_dir_files = [
        n for n in _csv_names(FAOSTAT_FB)
        if not n.endswith(".zip") and "_All_Data" not in n
    ]
    fbsh_wheat = sorted(
        n for n in fb_dir_files
        if n.startswith("wheat_fbsh_") and n.endswith(".csv")
    )
    author_fb = _author_fb_hits()
    laptop = {
        "path": str(LAPTOP_DATA),
        "exists": LAPTOP_DATA.is_dir(),
        "food_balance_hits": [],
    }
    if laptop["exists"]:
        laptop["food_balance_hits"] = sorted(
            str(p) for p in LAPTOP_DATA.rglob("*")
            if p.is_file() and (
                "food_balance" in p.name.lower()
                or "foodbalance" in p.name.lower()
                or p.name.lower().startswith("wheat_fbsh_")
            )
        )
    notes = prepare_wheat(start_year=2006, end_year=2006).notes
    return {
        "network_files": network,
        "e0_files": e0,
        "p0_r0_files": p0,
        # Author-cleaned names (host reconstruction of impute_food_balance_fao).
        # Raw FBSH lives in fbsh_wheat_files. USDA remains prepare_wheat default.
        "food_balance_files": list(author_fb),
        "author_fb_present": [Path(p).name for p in author_fb],
        "author_fb_reconstruction": any(
            Path(p).name == "wheat_food_balance_fao.csv" for p in author_fb
        ),
        "author_fb_bit_identical": False,
        "faostat_fb_dir_files": fb_dir_files,
        "fbsh_wheat_files": fbsh_wheat,
        "laptop_data": laptop,
        "prepare_wheat_notes": notes,
        "alpha_i": float(wheat_params().alpha_i),
        "usda_is_default": any("USDA PSD" in n and "not FAOSTAT" in n for n in notes),
    }


def write_faostat_fb_note(inv: dict | None = None, out_dir: Path | None = None) -> Path:
    inv = inv or inventory()
    out_dir = Path(out_dir) if out_dir else OUT_DEFAULT
    out_dir.mkdir(parents=True, exist_ok=True)
    e0 = ", ".join(inv["e0_files"]) or "none"
    author = ", ".join(inv["food_balance_files"]) or "none"
    fbsh = ", ".join(inv.get("fbsh_wheat_files") or []) or "none"
    laptop = inv.get("laptop_data") or {}
    laptop_exists = bool(laptop.get("exists"))
    laptop_hits = ", ".join(laptop.get("food_balance_hits") or []) or "none"
    lines = [
        "# A1 — FAOSTAT Food Balances: raw FBSH vendored; USDA still default",
        "",
        "**Leave A1. USDA remains the 2006–11 default.** Labelled parallel",
        "`WheatData` is `fb_wheatdata.md` (**not adopted**). No three-scenario",
        "FAO run. `wheat_params()` stay",
        "αI=3.2, p_sto=0.1, xmin=0.2. L1–L8 stay rejected. Bai",
        "α_foreign=10 not adopted. Bai's 2020–24 FAO-anomaly finding is a",
        "different window; it is not a reason to switch this wheat run.",
        "",
        "R6 obtain vendored FAOSTAT **FBSH** (Food Balances −2013, old",
        "methodology) wheat item 2511, years 2006–2011, unit 1000 t.",
        "That extract is **not** bit-identical Agrimate cleaned",
        "`wheat_food_balance_fao.csv`. A labelled host reconstruction of",
        "`impute_food_balance_fao` now lives under `data/food_balances/`",
        "(not adopted as `prepare_wheat`).",
        "Do not mix FBS 2010+ (new methodology) into this vintage.",
        "R6 `prepare_wheat_fbsh` is a labelled parallel vs USDA on one",
        "harvest+AMIS window; **not adopted**.",
        "",
        "## Inventory",
        "",
        "Agrimate E.1.1 baseline quantities are FAOSTAT Food Balances.",
        "This host uses USDA PSD 2007–09 means (labelled A1) plus FAOSTAT",
        "**E0 trade shares** (A2), not FB production/consumption/stocks.",
        "",
        "Checked `data/faostat_network/` (the tree at",
        "`/Users/mjp38/GitHub/sheaf-model/data/faostat_network` on the",
        "laptop; this checkout has the same E0 files). Contents are square",
        "bilateral **E0** matrices (exporter × FAOSTAT area code) plus a",
        "country conversion table. Wheat 2006–07 / 2010–11 / 2019–21 E0",
        "are trade, not production/consumption/stocks.",
        "",
        f"- E0 files: {e0}.",
        f"- P0 / Production / R0 / Reserves in that folder: "
        f"{', '.join(inv.get('p0_r0_files') or []) or 'none'}.",
        f"- Author-cleaned `wheat_food_balance*.csv` under `data/`: {author}.",
        f"- Raw FBSH wheat extract (`data/faostat_fb/`): {fbsh}.",
        f"- Laptop `{laptop.get('path', '/Users/mjp38/GitHub/sheaf-model/data')}` "
        f"mounted: {'yes' if laptop_exists else 'no'} "
        f"(FB hits: {laptop_hits}).",
        "- Author AgriculturalData (Zenodo 14022004) expects cleaned",
        "  `wheat_food_balance_fao.csv` / `wheat_food_balance.csv` /",
        "  `wheat_production.csv`. A labelled host reconstruction of",
        "  `wheat_food_balance_fao.csv` is under `data/food_balances/`",
        "  (not bit-identical; not adopted). The other two names are still",
        "  absent.",
        "- Upstream `mjpuma/FoodTradeNetwork` `inputs_processed/` has",
        "  Wheat P0/Production/Reserves only as **2015–21 window averages**,",
        "  not 2006–11 annual Food Balances. Copying those would not force",
        "  this Agrimate wheat window. Not vendored.",
        "",
        "`data/faostat_network/PROVENANCE.txt` already says production (P0)",
        "and reserves (R0) are **not** taken from FAOSTAT: FAO stocks are",
        "food-balance residuals. `sheaf/data_faostat.py` loads the trade",
        "network only. FBSH Stock Variation is element **5074** (not FBS",
        "5072). It is a residual, not USDA ending stocks.",
        "",
        "## Obtain (this run)",
        "",
        "JSON API `fenixservices.fao.org/.../data/FBSH` returned HTTP 521.",
        "Bulk zip from `bulks-faostat.fao.org` returned 200 (~72.5 MB,",
        "gitignored). Extract: 1259 area-years, 210 areas. Sanity 2007",
        "production (1000 t): United States of America 55820; World 608672;",
        "China, mainland 109298; European Union (27) 107883.",
        "",
        "Refresh: `PYTHONPATH=. python scripts/fetch_external_data.py "
        "--faostat-fb`. Opt-in; not in the default PSD/AMIS/Pink fetch.",
        "Does not change `wheat_params` or `prepare_wheat`.",
        "",
        "## Places that look like FAO but are not Agrimate FB",
        "",
        "1. **Fig. 4 NetCDF** (`production_anomalies=FAOsince-2005`).",
        "   Zenodo 10688435 `data.zip` is model *output* (NetCDF + PDFs).",
        "   No CSV/XLSX Food Balance inputs. The zip is not vendored.",
        "   Those harvest series were scored in P7 on AgrimateEU28+Egypt;",
        "   they are not a 27-node `WheatData` substitute.",
        "2. **Author code** `AgriculturalData` (14022004) has the",
        "   preprocess (`impute_food_balance_fao`, QCL+TCL merge,",
        "   rebalance). The author's local CSV is still unpublished.",
        "   This host reconstructed `impute_food_balance_fao` for 2006–11",
        "   under `data/food_balances/` (labelled; not adopted).",
        "3. This **raw FBSH dump** is official FAOSTAT, not that pipeline.",
        "   Old FBS vs new Food Balances also breaks across ~2010; this",
        "   extract stays on FBSH through 2011.",
        "",
        "## Verification protocol (leave A1)",
        "",
        "1. **Claim.** Agrimate E.1 uses FAOSTAT Food Balances.",
        "2. **Implementation.** `prepare_wheat` (`wheat_data.py`) groups",
        "   USDA PSD 2007–09 and notes \"not FAOSTAT Food Balances (E.1.1).\"",
        "3. **Match.** They do not, by labelled adaptation A1.",
        "4. **Counterexample.** Raw FBSH is on disk. A labelled",
        "   reconstruction of `wheat_food_balance_fao.csv` is also on",
        "   disk (`inventory()[\"food_balance_files\"]`); it is not",
        "   bit-identical author output and is **not adopted**.",
        "   `prepare_wheat` still USDA.",
        "5. **Correctness of stopping.** E0 is present and used. Wiring",
        "   FBSH into the 27-node host needs region maps, stock treatment,",
        "   and a labelled parallel WheatData (`fb_wheatdata.md`, not",
        "   adopted). Switching the host would retune 2006–11 quantities.",
        "6. **Change.** None to economics. USDA stays default until G0-P.",
        "",
        f"`prepare_wheat` default note holds; αI={inv['alpha_i']:g}.",
        "",
        "## Files",
        "",
        "- this note",
        "- `data/faostat_fb/PROVENANCE.txt`",
        "- `data/food_balances/PROVENANCE.txt` (host reconstruction)",
        "- `data/faostat_network/PROVENANCE.txt` (E0 only)",
        "",
        "Next paste: **R7** (A8 mean-vs-sum). Not G1. Do not retune",
        "αI / p_sto / xmin. Do not adopt FBSH as prepare_wheat.",
        "",
    ]
    path = out_dir / "faostat_fb.md"
    path.write_text("\n".join(lines) + "\n")
    return path


def run_faostat_fb_inventory(out_dir: Path | None = None) -> dict[str, Path]:
    inv = inventory()
    note = write_faostat_fb_note(inv, out_dir)
    return {"note": note}
