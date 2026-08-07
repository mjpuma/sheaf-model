"""
sheaf.data_faostat
==================
Adapter for the FAOSTAT bilateral trade network, aligned to the processed
matrices in the FoodTradeNetwork repository (mjpuma/FoodTradeNetwork,
inputs_processed/). It loads a crop's bilateral export matrix E0 for a given
year window, keys it to ISO3 via the repo's country conversion table, and
aggregates it to a chosen node set.

IMPORTANT -- what this module deliberately does NOT do:
    It does not read production (P0) or reserves (R0) from FAOSTAT. FAOSTAT does
    not report stocks as a measured variable; in a food-balance pipeline the
    "reserves" are the residual (production + imports - exports - utilisation),
    so they absorb every accounting error in the balance. SHEAF therefore takes
    production and reserves from USDA PSD (see sheaf.data_usda), which reports
    stocks as a genuine series. This module supplies the trade *network* only.

E0 file layout (as in FoodTradeNetwork/inputs_processed):
    rows    = exporter country NAME
    columns = importer FAOSTAT numeric area code
    values  = bilateral flow, exporter -> importer (absolute magnitude is
              treated as unit-agnostic here; use bilateral_shares() for
              structure and rescale_to_total() to pin the scale to a USDA total)

Filenames come in matched windows, e.g. Wheat_Avg_2006_2007E0.csv,
Maize_Avg_2010_2011E0.csv, Wheat_Avg20192021E0.csv, plus Sum_ and
PrimaryEquiv variants. The crisis windows 2006_2007 and 2010_2011 exist for
wheat, rice, and maize.
"""

from __future__ import annotations
from pathlib import Path
import re
import numpy as np
import pandas as pd

# country conversion table + a runnable sample E0 ship under data/faostat_network/
_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "faostat_network"
_CONV_TABLE = _DATA_DIR / "country_conversion_table.csv"

# names in the E0 row index that don't match the conversion table's Country column
_NAME_ALIASES = {
    "China (mainland)": "CHN",
    "Cote dIvoire": "CIV",
    "Taiwan": "TWN",
}
# FAOSTAT codes for the same three (used when they appear as columns)
_CODE_ALIASES = {41: "CHN", 107: "CIV", 214: "TWN"}


def _mappings(conv_table: Path | str | None = None):
    path = Path(conv_table) if conv_table else _CONV_TABLE
    t = pd.read_csv(path, encoding="utf-8-sig").dropna(subset=["FAOSTAT", "ISO3 alpha"])
    fao2iso = {int(r["FAOSTAT"]): str(r["ISO3 alpha"]).strip() for _, r in t.iterrows()}
    name2iso = {str(r["Country"]).strip(): str(r["ISO3 alpha"]).strip() for _, r in t.iterrows()}
    fao2iso.update(_CODE_ALIASES)
    name2iso.update(_NAME_ALIASES)
    valid_iso3 = set(fao2iso.values()) | set(name2iso.values())
    return fao2iso, name2iso, valid_iso3


def _to_iso3(label, fao2iso, name2iso, valid_iso3):
    """Resolve a row/column label to ISO3. Handles the three keyings seen across
    FoodTradeNetwork files: FAOSTAT numeric codes, ISO3 strings, or country names."""
    s = str(label).strip()
    try:                                   # FAOSTAT numeric code
        return fao2iso.get(int(float(s)))
    except (ValueError, TypeError):
        pass
    u = s.upper()
    if u in valid_iso3:                     # already ISO3
        return u
    return name2iso.get(s)                  # country name (with aliases)


# ---------------------------------------------------------------------------
# file resolution across the (inconsistent) window-naming conventions
# ---------------------------------------------------------------------------
def _parse_window(fname: str):
    """Return (crop, agg, primary_equiv, (y0, y1)) parsed from an E0 filename,
    or None if it is not an E0 matrix file."""
    m = re.match(r"([A-Za-z]+)_(Avg|Sum)_?(.*?)(_PrimaryEquiv)?E0\.csv$", fname)
    if not m:
        return None
    crop, agg, yearpart, prim = m.groups()
    yrs = re.findall(r"\d{4}", yearpart)
    if not yrs:
        digits = re.sub(r"\D", "", yearpart)
        if len(digits) == 8:
            yrs = [digits[:4], digits[4:]]
    if not yrs:
        return None
    y0 = int(yrs[0]); y1 = int(yrs[-1])
    return crop.lower(), agg.lower(), bool(prim), (y0, y1)


def list_windows(crop: str, agg: str = "avg", primary_equiv: bool = False,
                 data_dir: Path | str | None = None):
    """List available (y0, y1) windows for a crop, matching agg and equiv flags."""
    ddir = Path(data_dir) if data_dir else _DATA_DIR
    out = []
    for p in sorted(ddir.glob(f"{crop.capitalize()}*E0.csv")):
        parsed = _parse_window(p.name)
        if not parsed:
            continue
        c, a, prim, window = parsed
        if c == crop.lower() and a == agg.lower() and prim == primary_equiv:
            out.append((window, p.name))
    return out


def _resolve_file(crop, year, window, agg, primary_equiv, ddir):
    candidates = list_windows(crop, agg, primary_equiv, ddir)
    if not candidates:
        raise FileNotFoundError(
            f"No E0 files for crop={crop!r} agg={agg!r} in {ddir}")
    if window is not None:
        for (w, name) in candidates:
            if w == tuple(window):
                return ddir / name
        raise FileNotFoundError(f"window {window} not found for {crop}")
    if year is not None:
        for (w, name) in candidates:
            if w[0] <= year <= w[1]:
                return ddir / name
        # nearest window by midpoint
        w, name = min(candidates, key=lambda wn: abs(np.mean(wn[0]) - year))
        return ddir / name
    return ddir / candidates[-1][1]      # latest window by default


# ---------------------------------------------------------------------------
# loading
# ---------------------------------------------------------------------------
def load_trade_matrix(crop: str, year: int | None = None,
                      window: tuple[int, int] | None = None, agg: str = "avg",
                      primary_equiv: bool = False, data_dir=None,
                      conv_table=None, report: bool = False) -> pd.DataFrame:
    """Load a crop's bilateral export matrix as an ISO3 x ISO3 DataFrame
    (index = exporter ISO3, columns = importer ISO3).

    Absolute values are unit-agnostic (see module docstring); use for network
    structure and rescale to a USDA total when magnitudes matter.
    """
    ddir = Path(data_dir) if data_dir else _DATA_DIR
    fao2iso, name2iso, valid_iso3 = _mappings(conv_table)
    path = _resolve_file(crop, year, window, agg, primary_equiv, ddir)

    raw = pd.read_csv(path, index_col=0)
    col_iso = {c: _to_iso3(c, fao2iso, name2iso, valid_iso3) for c in raw.columns}
    row_iso = {r: _to_iso3(r, fao2iso, name2iso, valid_iso3) for r in raw.index}
    n_col_drop = sum(v is None for v in col_iso.values())
    n_row_drop = sum(v is None for v in row_iso.values())

    raw = raw.rename(index=row_iso, columns={c: col_iso[c] for c in raw.columns})
    raw = raw.loc[[i for i in raw.index if i is not None],
                  [c for c in raw.columns if c is not None]]
    # collapse any duplicate ISO3 (e.g. territories mapped together)
    raw = raw.groupby(level=0).sum().T.groupby(level=0).sum().T
    E0 = raw.astype(float)
    E0.index.name = "exporter_iso3"
    E0.columns.name = "importer_iso3"
    if report:
        print(f"[data_faostat] {path.name}: {E0.shape[0]}x{E0.shape[1]} ISO3 nodes "
              f"(dropped {n_row_drop} rows, {n_col_drop} cols unmapped)")
    return E0


# ---------------------------------------------------------------------------
# transforms
# ---------------------------------------------------------------------------
def bilateral_shares(E0: pd.DataFrame, by: str = "destination") -> pd.DataFrame:
    """Normalise the network to shares. by='destination': each exporter's row
    sums to 1 (its export destination mix). by='source': each importer's column
    sums to 1 (its import source mix -- the baseline demand shares a*_rs)."""
    if by == "destination":
        s = E0.sum(axis=1).replace(0, np.nan)
        return E0.div(s, axis=0).fillna(0.0)
    elif by == "source":
        s = E0.sum(axis=0).replace(0, np.nan)
        return E0.div(s, axis=1).fillna(0.0)
    raise ValueError("by must be 'destination' or 'source'")


def rescale_to_total(E0: pd.DataFrame, total: float) -> pd.DataFrame:
    """Rescale the whole matrix so its sum equals `total` (e.g. global traded
    volume in MMT from USDA), pinning the unit-agnostic magnitudes to a real
    total while preserving structure."""
    tot = E0.values.sum()
    return E0 * (total / tot) if tot > 0 else E0


def aggregate_to_nodes(E0: pd.DataFrame, node_map: dict[str, list[str]],
                       rest_label: str = "RestOfWorld") -> pd.DataFrame:
    """Collapse an ISO3 x ISO3 matrix to a node set. node_map maps each node
    name to a list of ISO3 codes; any ISO3 not listed is pooled into
    `rest_label`. Returns a square node x node DataFrame (exporter x importer)."""
    iso_to_node = {}
    for node, isos in node_map.items():
        for iso in isos:
            iso_to_node[iso] = node
    nodes = list(node_map.keys()) + [rest_label]
    ex = E0.index.map(lambda i: iso_to_node.get(i, rest_label))
    im = E0.columns.map(lambda c: iso_to_node.get(c, rest_label))
    agg = (E0.groupby(ex).sum().T.groupby(im).sum().T)
    return agg.reindex(index=nodes, columns=nodes).fillna(0.0)


# a starting node map for SHEAF's prototype country set (EU expanded to members).
EU_ISO3 = ["AUT", "BEL", "BGR", "HRV", "CYP", "CZE", "DNK", "EST", "FIN", "FRA",
           "DEU", "GRC", "HUN", "IRL", "ITA", "LVA", "LTU", "LUX", "MLT", "NLD",
           "POL", "PRT", "ROU", "SVK", "SVN", "ESP", "SWE"]
SHEAF_NODE_MAP = {
    "USA": ["USA"], "Russia": ["RUS"], "EU": EU_ISO3, "Ukraine": ["UKR"],
    "Canada": ["CAN"], "Australia": ["AUS"], "Argentina": ["ARG"],
    "Brazil": ["BRA"], "India": ["IND"], "Thailand": ["THA"], "Vietnam": ["VNM"],
    "China": ["CHN"], "Egypt": ["EGY"], "Indonesia": ["IDN"], "Mexico": ["MEX"],
    "Nigeria": ["NGA"],
}
