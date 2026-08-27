#!/usr/bin/env python3
"""Choropleths for the Gate 0 and Gate 1 Overleaf notes.

Does not retune CropParams, densify σ, or re-run official Gate 0 / Gate 1
score tables. Gate 0 maps are built from locked CSVs plus AMIS/LOWESS
arrays. Gate 1 maps need two coupled official-split runs (σ=0 and 0.6)
for country Δconsumption — that is a map diagnostic, not a new score.

See sheaf/maps.py. Score scripts should keep emitting who/what-state maps.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sheaf.calendar24 import STEPS_PER_YEAR
from sheaf.dynamic_crop import (
    _harvest_anomaly_scalars,
    amis_export_cuts,
    prepare_crop_run,
)
from sheaf.dynamic_coupled import run_coupled_dynamics
from sheaf.maps import plot_categories, plot_choropleth

DIAG = ROOT / "diagnostics"
FIGS = ROOT / "figures"
G0_FIGS = ROOT / "overleaf" / "gate0_whitepaper" / "figures"
G1_FIGS = ROOT / "overleaf" / "gate1_whitepaper" / "figures"


def _named(countries: list[str], values) -> dict[str, float]:
    out = {}
    for i, c in enumerate(countries):
        if c == "RestOfWorld":
            continue
        v = values[i]
        if v is None or (isinstance(v, float) and not np.isfinite(v)):
            continue
        out[c] = float(v)
    return out


def _year_slice(start_year: int, year: int) -> slice:
    t0 = (year - start_year) * STEPS_PER_YEAR
    return slice(t0, t0 + STEPS_PER_YEAR)


def _max_cut(cuts: np.ndarray, countries: list[str], start: int,
             years: tuple[int, ...]) -> dict[str, float]:
    acc = np.zeros(len(countries))
    for y in years:
        acc = np.maximum(acc, np.asarray(cuts[:, _year_slice(start, y)], float).max(axis=1))
    return _named(countries, acc)


def _copy(name: str, *dests: Path) -> None:
    src = FIGS / name
    for d in dests:
        d.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, d / name)


def gate0_maps() -> None:
    FIGS.mkdir(parents=True, exist_ok=True)
    wheat = prepare_crop_run(
        "wheat", start_year=2006, end_year=2011,
        use_amis=True, use_shocks=True, use_demand=False)
    rice = prepare_crop_run(
        "rice", start_year=2006, end_year=2011,
        use_amis=True, use_shocks=True, use_demand=False)
    years = list(range(2006, 2012))
    w_anom = _harvest_anomaly_scalars("wheat", wheat.countries, years)
    yi = {y: i for i, y in enumerate(years)}
    w_cuts = amis_export_cuts("wheat", wheat.countries, 2006, 2011)
    r_cuts = amis_export_cuts("rice", rice.countries, 2006, 2011)

    plot_choropleth(
        _max_cut(w_cuts, wheat.countries, 2006, (2007, 2008)),
        FIGS / "fig_gate0_map_wheat_amis_2008.png",
        title="Wheat AMIS intensity, 2007–08 (max τ on the diary)",
        label="max AMIS cut τ", cmap="YlOrRd", vmin=0, vmax=0.95)
    plot_choropleth(
        _max_cut(r_cuts, rice.countries, 2006, (2007, 2008)),
        FIGS / "fig_gate0_map_rice_amis_2008.png",
        title="Rice AMIS intensity, 2007–08 (max τ on the diary)",
        label="max AMIS cut τ", cmap="YlOrRd", vmin=0, vmax=0.95)
    plot_choropleth(
        _named(wheat.countries, w_anom[:, yi[2007]] - 1.0),
        FIGS / "fig_gate0_map_wheat_harvest_2007.png",
        title="Wheat LOWESS harvest anomaly, 2007",
        label="(1+a) − 1", cmap="RdBu", vmin=-0.45, vmax=0.45, vcenter=0.0)
    plot_choropleth(
        _named(wheat.countries, w_anom[:, yi[2010]] - 1.0),
        FIGS / "fig_gate0_map_wheat_harvest_2010.png",
        title="Wheat LOWESS harvest anomaly, 2010",
        label="(1+a) − 1", cmap="RdBu", vmin=-0.45, vmax=0.45, vcenter=0.0)

    bite = pd.read_csv(DIAG / "gate0_wheat_exports_psd.csv")
    bite10 = bite[bite.year == 2010]
    d_amis = {str(r.country): float(r.d_amis) for r in bite10.itertuples(index=False)
              if r.country != "RestOfWorld"}
    plot_choropleth(
        d_amis, FIGS / "fig_gate0_map_wheat_bite_2010.png",
        title="Wheat AMIS shipment bite, 2010 (full − harvest-only, MMT)",
        label="Δ shipments from AMIS (MMT)", cmap="RdBu", vcenter=0.0)

    bal = pd.read_csv(DIAG / "gate0_wheat_country_balance.csv")
    cons08 = bal[(bal.year == 2008) & (bal.country != "RestOfWorld")]
    plot_choropleth(
        {str(r.country): float(r.cons_ratio) for r in cons08.itertuples(index=False)},
        FIGS / "fig_gate0_map_wheat_cons_2008.png",
        title="Wheat 2008 calendar-year use: model / PSD",
        label="model / PSD", cmap="RdYlBu", vmin=0.70, vmax=1.15, vcenter=1.0)

    roles = {}
    w08 = _max_cut(w_cuts, wheat.countries, 2006, (2007, 2008))
    a07 = _named(wheat.countries, w_anom[:, yi[2007]] - 1.0)
    for c in wheat.countries:
        if c == "RestOfWorld":
            continue
        banned = w08.get(c, 0.0) >= 0.25
        short = a07.get(c, 0.0) <= -0.08
        if banned and short:
            roles[c] = "ban and short harvest"
        elif banned:
            roles[c] = "AMIS ban / tax"
        elif short:
            roles[c] = "harvest shortfall"
        else:
            roles[c] = "named node, neither"
    plot_categories(
        roles, FIGS / "fig_gate0_map_wheat_roles_2008.png",
        title="Wheat 2007–08: who banned vs who lost harvest (AMIS + LOWESS)",
        palette={
            "AMIS ban / tax": "#c0392b",
            "harvest shortfall": "#2471a3",
            "ban and short harvest": "#6c3483",
            "named node, neither": "#d5dbdb",
        })

    names = (
        "fig_gate0_map_wheat_amis_2008.png",
        "fig_gate0_map_rice_amis_2008.png",
        "fig_gate0_map_wheat_harvest_2007.png",
        "fig_gate0_map_wheat_harvest_2010.png",
        "fig_gate0_map_wheat_bite_2010.png",
        "fig_gate0_map_wheat_cons_2008.png",
        "fig_gate0_map_wheat_roles_2008.png",
    )
    for name in names:
        _copy(name, G0_FIGS)
        print(f"wrote {FIGS / name}")


def gate1_maps() -> None:
    """Country Δconsumption, official split, σ=0.6 vs σ=0. Not a new score."""
    print("Gate 1 map diagnostic: coupled σ=0 and σ=0.6 official split...")
    z = run_coupled_dynamics(subst_scale=0.0, use_amis=True, use_shocks=True,
                             use_demand=False)
    s = run_coupled_dynamics(subst_scale=0.6, use_amis=True, use_shocks=True,
                             use_demand=False)
    countries = z.by_crop["wheat"].countries
    sl = _year_slice(z.by_crop["wheat"].start_year, 2008)
    for grain, fname, title in (
            ("wheat", "fig_gate1_map_dc_wheat_2008.png",
             "Wheat 2008 use: σ=0.6 vs σ=0 (% of σ=0)"),
            ("rice", "fig_gate1_map_dc_rice_2008.png",
             "Rice 2008 use: σ=0.6 vs σ=0 (% of σ=0)"),
            ("maize", "fig_gate1_map_dc_maize_2008.png",
             "Maize 2008 use: σ=0.6 vs σ=0 (% of σ=0)"),
    ):
        c0 = np.asarray(z.by_crop[grain].consumption[:, sl], float).sum(axis=1)
        c1 = np.asarray(s.by_crop[grain].consumption[:, sl], float).sum(axis=1)
        pct = 100.0 * (c1 - c0) / np.maximum(c0, 1e-9)
        plot_choropleth(
            _named(countries, pct), FIGS / fname,
            title=title, label="% Δ consumption",
            cmap="RdBu", vcenter=0.0, vmin=-8.0, vmax=8.0)
        _copy(fname, G1_FIGS)
        print(f"wrote {FIGS / fname}")
        top = sorted(
            ((countries[i], float(pct[i])) for i in range(len(countries))
             if countries[i] != "RestOfWorld"),
            key=lambda kv: abs(kv[1]), reverse=True)[:6]
        print(f"  {grain} largest |Δ%|: " +
              ", ".join(f"{n} {v:+.2f}%" for n, v in top))


def main() -> None:
    gate0_maps()
    gate1_maps()


if __name__ == "__main__":
    main()
