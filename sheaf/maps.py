"""Choropleths of SHEAF nodes on Natural Earth 110m.

Score scripts should emit at least one map of *who* moved and one of the
*state* that moved them. Named nodes follow ``SHEAF_NODE_MAP`` (EU is
dissolved). ``RestOfWorld`` is the residual fill. Antarctica is omitted.

Matplotlib only — no geopandas. Geometry: ``data/maps/ne_110m_admin_0_countries.geojson``.
"""
from __future__ import annotations

from pathlib import Path

import json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.collections import PatchCollection
from matplotlib.colors import Normalize, TwoSlopeNorm
from matplotlib.cm import ScalarMappable
from matplotlib.patches import Polygon
import numpy as np

from .data_faostat import SHEAF_NODE_MAP

_ROOT = Path(__file__).resolve().parents[1]
GEOJSON = _ROOT / "data" / "maps" / "ne_110m_admin_0_countries.geojson"
SKIP_ISO3 = {"ATA"}  # Antarctica: crops the frame

_ISO3_TO_NODE = {
    iso: node for node, isos in SHEAF_NODE_MAP.items() for iso in isos
}


def feature_iso3(props: dict) -> str | None:
    """Prefer ISO_A3_EH: Natural Earth sets ISO_A3='-99' for France/Norway."""
    for key in ("ISO_A3_EH", "ADM0_A3", "ISO_A3"):
        val = props.get(key)
        if val and str(val).strip() not in ("", "-99", "None"):
            return str(val).strip()
    return None


def node_for_iso3(iso: str, rest_label: str = "RestOfWorld") -> str:
    return _ISO3_TO_NODE.get(iso, rest_label)


def _exteriors(geom: dict):
    if geom is None:
        return
    gtype = geom.get("type")
    coords = geom.get("coordinates") or []
    if gtype == "Polygon":
        if coords:
            yield coords[0]
    elif gtype == "MultiPolygon":
        for poly in coords:
            if poly:
                yield poly[0]


def _load_features() -> list[tuple[str, list[np.ndarray]]]:
    data = json.loads(GEOJSON.read_text())
    out: list[tuple[str, list[np.ndarray]]] = []
    for feat in data["features"]:
        iso = feature_iso3(feat.get("properties") or {})
        if iso is None or iso in SKIP_ISO3:
            continue
        rings = []
        for ring in _exteriors(feat.get("geometry") or {}):
            arr = np.asarray(ring, float)
            if arr.ndim == 2 and arr.shape[0] >= 3:
                rings.append(arr[:, :2])
        if rings:
            out.append((iso, rings))
    return out


_FEATURES: list[tuple[str, list[np.ndarray]]] | None = None


def world_features() -> list[tuple[str, list[np.ndarray]]]:
    global _FEATURES
    if _FEATURES is None:
        if not GEOJSON.is_file():
            raise FileNotFoundError(
                f"Missing {GEOJSON}; see data/maps/PROVENANCE.txt")
        _FEATURES = _load_features()
    return _FEATURES


def safe_min_ratio(s_open, s_calm, floor: float = 0.05) -> float | None:
    """Min S_open/S_calm, or None if climatology stocks out (ratio undefined)."""
    c = np.asarray(s_calm, float)
    s = np.asarray(s_open, float)
    if c.size == 0 or float(np.min(c)) < float(floor):
        return None
    return float(np.min(s / np.maximum(c, 1e-9)))


def _style_axes(ax) -> None:
    ax.set_xlim(-170, 188)
    ax.set_ylim(-58, 84)
    ax.set_aspect("equal")
    ax.axis("off")


def plot_choropleth(
    values: dict[str, float],
    path: str | Path,
    *,
    title: str,
    label: str = "",
    cmap: str = "YlOrRd",
    vmin: float | None = None,
    vmax: float | None = None,
    vcenter: float | None = None,
    rest_label: str = "RestOfWorld",
    missing_color: str = "#f0f0f0",
    rest_color: str = "#d9d9d9",
    edgecolor: str = "0.35",
    figsize: tuple[float, float] = (10.6, 5.0),
) -> Path:
    """Fill named SHEAF nodes from ``values``. Unlisted named nodes and RoW
    take ``missing_color`` / ``rest_color``. ``vcenter`` makes a diverging
    scale (e.g. stock ratio around the trigger)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    nums = [float(v) for v in values.values() if v is not None]
    if not nums:
        raise ValueError("plot_choropleth: no values")
    if vmin is None:
        vmin = min(nums)
    if vmax is None:
        vmax = max(nums)
    if vmax <= vmin:
        vmax = vmin + 1e-9
    if vcenter is not None:
        norm = TwoSlopeNorm(vcenter=vcenter, vmin=vmin, vmax=vmax)
    else:
        norm = Normalize(vmin=vmin, vmax=vmax)
    cm = plt.get_cmap(cmap)

    patches, colors = [], []
    for iso, rings in world_features():
        node = node_for_iso3(iso, rest_label=rest_label)
        if node == rest_label:
            facecolor = rest_color
        elif node in values and values[node] is not None:
            facecolor = cm(norm(float(values[node])))
        else:
            facecolor = missing_color
        for ring in rings:
            patches.append(Polygon(ring, closed=True))
            colors.append(facecolor)

    fig, ax = plt.subplots(figsize=figsize)
    coll = PatchCollection(
        patches, facecolors=colors, edgecolors=edgecolor, linewidths=0.25)
    ax.add_collection(coll)
    _style_axes(ax)
    sm = ScalarMappable(norm=norm, cmap=cm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, fraction=0.03, pad=0.02)
    if label:
        cbar.set_label(label)
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_categories(
    categories: dict[str, str],
    path: str | Path,
    *,
    title: str,
    palette: dict[str, str] | None = None,
    rest_label: str = "RestOfWorld",
    rest_category: str = "Rest of world",
    figsize: tuple[float, float] = (10.6, 5.0),
) -> Path:
    """Categorical choropleth (who plays, who was shocked, …)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    cats = sorted({c for c in categories.values()} | {rest_category})
    default = {
        "harvest shock": "#c0392b",
        "player (no harvest cut)": "#2471a3",
        "on market, not playing": "#bb8fce",
        "named node": "#aab7b8",
        "Rest of world": "#ececec",
    }
    palette = {**default, **(palette or {})}
    fallback = ["#1b9e77", "#d95f02", "#7570b3", "#e7298a", "#66a61e",
                "#e6ab02"]
    for i, c in enumerate(cats):
        palette.setdefault(c, fallback[i % len(fallback)])

    patches, colors = [], []
    for iso, rings in world_features():
        node = node_for_iso3(iso, rest_label=rest_label)
        if node == rest_label:
            cat = rest_category
        else:
            cat = categories.get(node, "named node")
        facecolor = palette.get(cat, "#dddddd")
        for ring in rings:
            patches.append(Polygon(ring, closed=True))
            colors.append(facecolor)

    fig, ax = plt.subplots(figsize=figsize)
    coll = PatchCollection(
        patches, facecolors=colors, edgecolors="0.35", linewidths=0.25)
    ax.add_collection(coll)
    _style_axes(ax)
    handles = []
    seen = []
    for cat in cats:
        if cat not in seen:
            seen.append(cat)
            handles.append(mpatches.Patch(facecolor=palette[cat],
                                          edgecolor="0.35", label=cat))
    ax.legend(handles=handles, loc="lower left", frameon=True, fontsize=8,
              framealpha=0.92)
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path
