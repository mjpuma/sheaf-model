"""S4: A7 cannot-set inventory. Does not replace C.1 or wheat_params().

Fig. 4 NetCDF (10688435) is AgrimateEU28 + extra Egypt=EGY, FAO anomalies,
start 2000. Host remains AgrimateRegionsWheat + USDA + αI=3.2.
``fig4_experiment_params()`` already holds the knobs that can be set.

A labelled host reconstruction of ``wheat_food_balance_fao.csv`` appeared
before this session. S4 labels a **parallel** AgrimateEU28+Egypt region
list from the sourced NetCDF ``region_list`` plus extra_regions Egypt=EGY.
It does **not** invent an Egypt node on C.1, does not adopt the
reconstruction as ``prepare_wheat``, and does not retune.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .author_fb import OUT_CSV
from .faostat_fb import inventory as faostat_inventory
from .fig4 import AUTHOR_DIR
from .fig4_config import CAN_SET, CANNOT_SET, PROTECTED_THREE_SCENARIO, what_is_settable
from .params import fig4_experiment_params, wheat_params
from .regions import REGION_ISO3, REGION_NAMES
from .validation import OUT_DEFAULT
from .wheat_data import prepare_wheat
from .xi_split import n_julia_sources

ROOT = Path(__file__).resolve().parents[2]
DISPATCH = ROOT / "diagnostics" / "GATE0_REPRO_DISPATCH.md"
ATTRS = AUTHOR_DIR / "netcdf_attrs.json"

# Sourced from author_fig4/netcdf_attrs.json region_list (all three NetCDFs).
FIG4_EU28_EGYPT_NAMES: tuple[str, ...] = (
    "USA", "Ukraine", "Argentina", "Eastern Africa", "Central America",
    "Middle Africa", "Rest of Eastern Asia", "Rest of South America",
    "Northern Africa", "Rest of Southern Asia", "Kazakhstan",
    "South-Eastern Asia", "India", "EU-28", "Canada", "Rest of Europe",
    "Rest of Western Asia", "Pakistan", "Russia", "Western Africa",
    "Rest of Central Asia", "Egypt", "Southern Africa", "China",
    "Australia", "Turkey", "Rest of Oceania",
)
assert len(FIG4_EU28_EGYPT_NAMES) == 27

S1_HOST_HIKE = 3.71
S1_HOST_MOY = 16.8
S2_LAST_FIRST = 1.444
AUTHOR_HIKE = 1.62
AUTHOR_MOY = 1.45
AUTHOR_LAST_FIRST = 1.004
S3_HIKE_FBSH = 2.18
S3_MOY_FBSH = 33.0


def sourced_fig4_region_list() -> tuple[str, ...]:
    """NetCDF region_list; extra_regions Egypt=EGY. Not a C.1 replacement."""
    rows = json.loads(ATTRS.read_text())
    lists = {tuple(r["region_list"].split("|")) for r in rows}
    assert lists == {FIG4_EU28_EGYPT_NAMES}, lists
    extras = {r.get("extra_regions", "") for r in rows}
    assert all("Egypt" in e and "EGY" in e for e in extras)
    starts = {r.get("start") for r in rows}
    assert starts == {"2000-01-01"}
    n_steps = {int(r["n_steps"]) for r in rows}
    assert n_steps == {312}
    return FIG4_EU28_EGYPT_NAMES


def parallel_eu28_egypt_iso3() -> dict[str, list[str]]:
    """Labelled ISO3 map for AgrimateEU28+Egypt.

    Derived from host AgrimateRegionsWheat plus the sourced NetCDF names:
    Egypt=EGY split out of Northern Africa; EU-28 = host EU-27 + GBR;
    Brazil folded into Rest of South America; Southeast Asia renamed
    South-Eastern Asia. Julia ``regions.jl`` is not in-tree — this is a
    labelled parallel, not a bit-copy of AgrimateEU28.
    """
    base = {k: list(v) for k, v in REGION_ISO3.items()}
    egypt = ["EGY"]
    northern_africa = [i for i in base["Northern Africa"] if i != "EGY"]
    eu28 = list(base["EU-27"]) + ["GBR"]
    rest_europe = [i for i in base["Rest of Europe"] if i != "GBR"]
    rosa = list(base["Rest of South America"]) + list(base["Brazil"])
    sea = list(base["Southeast Asia"])
    out: dict[str, list[str]] = {}
    for name in FIG4_EU28_EGYPT_NAMES:
        if name == "Egypt":
            out[name] = egypt
        elif name == "EU-28":
            out[name] = eu28
        elif name == "Northern Africa":
            out[name] = northern_africa
        elif name == "Rest of Europe":
            out[name] = rest_europe
        elif name == "Rest of South America":
            out[name] = rosa
        elif name == "South-Eastern Asia":
            out[name] = sea
        else:
            out[name] = list(base[name])
    return out


def parallel_region_table() -> pd.DataFrame:
    rows = []
    for region, isos in parallel_eu28_egypt_iso3().items():
        for iso in isos:
            rows.append({
                "region": region, "iso3": iso, "source": "parallel_eu28_egypt",
            })
    return pd.DataFrame(rows)


def host_c1_still_wheat() -> dict:
    return {
        "n_host": len(REGION_NAMES),
        "host_has_egypt": "Egypt" in REGION_NAMES,
        "host_has_eu28": "EU-28" in REGION_NAMES,
        "host_has_eu27": "EU-27" in REGION_NAMES,
        "host_has_brazil": "Brazil" in REGION_NAMES,
        "egypt_in_northern_africa": "EGY" in REGION_ISO3["Northern Africa"],
        "gbr_in_rest_of_europe": "GBR" in REGION_ISO3["Rest of Europe"],
        "bra_named": "BRA" in REGION_ISO3["Brazil"],
    }


def inventory_a7() -> dict:
    """What Fig. 4 still cannot set. No WheatData rebuild."""
    names = sourced_fig4_region_list()
    parallel = parallel_eu28_egypt_iso3()
    fb = faostat_inventory()
    avail = what_is_settable()
    p = wheat_params()
    fig4 = fig4_experiment_params()
    host = host_c1_still_wheat()
    notes = prepare_wheat(start_year=2006, end_year=2006, params=p).notes
    return {
        "can_set": list(CAN_SET),
        "cannot_set": list(CANNOT_SET),
        "fig4_region_names": list(names),
        "n_fig4_regions": len(names),
        "parallel_has_egypt": "Egypt" in parallel and parallel["Egypt"] == ["EGY"],
        "parallel_has_eu28": "EU-28" in parallel and "GBR" in parallel["EU-28"],
        "parallel_has_brazil_node": "Brazil" in parallel,
        "parallel_n": len(parallel),
        "reconstruction_present": OUT_CSV.is_file(),
        "reconstruction_adopted": False,
        "usda_is_default": bool(fb["usda_is_default"]),
        "author_fb_bit_identical": bool(fb.get("author_fb_bit_identical", False)),
        "region_path": avail["region_path"],
        "host_has_egypt_node": host["host_has_egypt"],
        "host_has_eu28": host["host_has_eu28"],
        "host_has_eu27": host["host_has_eu27"],
        "host_has_brazil": host["host_has_brazil"],
        "wheat_params_alpha_i": float(p.alpha_i),
        "wheat_params_zeta": float(p.zeta_penalty),
        "wheat_params_n_for": int(p.n_for_months),
        "fig4_params_alpha_i": float(fig4.alpha_i),
        "fig4_params_zeta": float(fig4.zeta_penalty),
        "fig4_params_n_for": int(fig4.n_for_months),
        "start_2000_arrays": False,
        "fao_anomalies_since_2005_inputs": False,
        "author_julia_in_repo": n_julia_sources() > 0,
        "n_julia": int(n_julia_sources()),
        "n_steps_fig4": 312,
        "prepare_wheat_usda": any(
            "USDA PSD" in n and "not FAOSTAT Food Balances" in n for n in notes
        ),
        "wheat_params_unchanged": bool(avail["wheat_params_unchanged"]),
    }


def write_parallel_csv(out_dir: Path | None = None) -> Path:
    out_dir = Path(out_dir) if out_dir else OUT_DEFAULT
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "s4_parallel_eu28_egypt.csv"
    parallel_region_table().to_csv(path, index=False)
    return path


def write_score_csv(inv: dict, out_dir: Path | None = None) -> Path:
    out_dir = Path(out_dir) if out_dir else OUT_DEFAULT
    out_dir.mkdir(parents=True, exist_ok=True)
    skip = {"can_set", "cannot_set", "fig4_region_names"}
    row = {k: v for k, v in inv.items() if k not in skip}
    path = out_dir / "score_s4_a7.csv"
    pd.DataFrame([row]).to_csv(path, index=False)
    return path


def write_s4_note(inv: dict, out_dir: Path | None = None) -> Path:
    out_dir = Path(out_dir) if out_dir else OUT_DEFAULT
    out_dir.mkdir(parents=True, exist_ok=True)
    host = host_c1_still_wheat()
    missing = [
        "Bit-identical author local wheat_food_balance_fao.csv "
        "(reconstruction is labelled, 2006–11, not rebalanced)",
        "AgrimateEU28+Egypt as live C.1 (parallel list labelled; host "
        "still AgrimateRegionsWheat)",
        "start 2000-01-01 (Fig. 4 n_steps=312; host window 2003–11 / 2006–08)",
        "FAO production anomalies since 2005 as WheatData inputs "
        "(author_fig4/ is model *output*)",
        "git old-demand-dynamics executable",
        "Zenodo 14022004 Julia (not vendored)",
        "FAO Food Balances as prepare_wheat default (A1; USDA stays)",
    ]
    lines = [
        "# S4 — A7 cannot-set inventory",
        "",
        "**Do not invent an Egypt node. Do not put Fig. 4 knobs into",
        "`wheat_params()`.** Host remains AgrimateRegionsWheat + USDA +",
        "αI=3.2. L1–L8 stay rejected. Bai α_foreign=10 not adopted.",
        "Unforced price is not pinned. G1/G2 stay blocked. FBSH 5074 is",
        "ΔS, never S. C.1 is **not** replaced.",
        "",
        "## What can be set (already on the comparison object)",
        "",
        ", ".join(inv["can_set"]) + ".",
        f"`fig4_experiment_params()` αI={inv['fig4_params_alpha_i']:g},",
        f"ζ={inv['fig4_params_zeta']:g}, N_for={inv['fig4_params_n_for']}.",
        f"`wheat_params()` still αI={inv['wheat_params_alpha_i']:g},",
        f"ζ={inv['wheat_params_zeta']:g}, N_for={inv['wheat_params_n_for']}.",
        "",
        "## Files that appeared (labelled; not adopted)",
        "",
        "- Host reconstruction `data/food_balances/wheat_food_balance_fao.csv`",
        f"  present={inv['reconstruction_present']}; adopted="
        f"{inv['reconstruction_adopted']}; bit-identical="
        f"{inv['author_fb_bit_identical']}. USDA default="
        f"{inv['usda_is_default']}.",
        "- Parallel AgrimateEU28+Egypt **name list** from NetCDF",
        "  `region_list` + extra_regions Egypt=EGY (27 names). ISO3 map is",
        "  derived from host AgrimateRegionsWheat (EGY split; GBR into",
        "  EU-28; Brazil folded into Rest of South America). Not",
        "  `regions.jl` (0 `*.jl` in tree). CSV:",
        "  `s4_parallel_eu28_egypt.csv`.",
        "",
        "## Parallel vs C.1 (not a replacement)",
        "",
        f"- C.1 host: {host['n_host']} names; Egypt node="
        f"{host['host_has_egypt']}; EU-28={host['host_has_eu28']};",
        f"  EU-27={host['host_has_eu27']}; Brazil named="
        f"{host['host_has_brazil']}. EGY in Northern Africa="
        f"{host['egypt_in_northern_africa']}; GBR in Rest of Europe="
        f"{host['gbr_in_rest_of_europe']}.",
        f"- Parallel: n={inv['parallel_n']}; Egypt node="
        f"{inv['parallel_has_egypt']}; EU-28+GBR="
        f"{inv['parallel_has_eu28']}; Brazil node="
        f"{inv['parallel_has_brazil_node']}.",
        f"- `fig4_experiment_region_path()` = `{inv['region_path']}`",
        "  (still None: no AgrimateEU28 data directory with both FAO FB",
        "  *and* an EU28 WheatData).",
        "",
        "## Still cannot-set",
        "",
    ]
    for item in missing:
        lines.append(f"- {item}")
    lines += [
        "",
        "Fig. 4 NetCDF also cannot copy: start 2000-01-01, FAO-since-2005",
        "input anomalies, old-demand-dynamics git, author Julia.",
        "",
        "## Verification protocol",
        "",
        "1. **Claim.** Fig. 4 is AgrimateEU28+Egypt, FAO anomalies, start 2000;",
        "   knobs αI=3.5, ζ=1, N_for=6 live on a named comparison object.",
        "2. **Implementation.** `REGION_NAMES` is AgrimateRegionsWheat (27).",
        "   `wheat_params()` αI=3.2, ζ=0, N_for=3.",
        "   `fig4_experiment_params()` holds the NetCDF knobs.",
        "3. **Match.** Knobs that *can* be set already are. Region list,",
        "   start year, and FAO-anomaly *inputs* do not match Fig. 4.",
        "4. **Counterexample.** `\"Egypt\" in REGION_NAMES` is False; host",
        "   has EU-27 and named Brazil. Reconstruction CSV exists but",
        "   `prepare_wheat` notes still say USDA PSD, not FAOSTAT.",
        "5. **Correctness of not inventing Egypt.** Splitting EGY out of",
        "   Northern Africa without the author's AgrimateEU28 ISO map and",
        "   FAO-since-2005 anomalies would silently replace C.1 with a",
        "   guessed 27-node list. The parallel CSV labels the NetCDF names",
        "   without wiring them into `prepare_wheat`.",
        "6. **Change.** Inventory + labelled parallel list. No economics.",
        "",
        f"n_julia={inv['n_julia']}. Fig. 4 n_steps={inv['n_steps_fig4']}.",
        "",
        "**Next paste: S5.** Re-score Fig. 4 / hindcast on the S1 host.",
        "Do not start G1. Do not retune αI. Do not invent Egypt.",
        "",
    ]
    path = out_dir / "s4_a7.md"
    path.write_text("\n".join(lines) + "\n")
    return path


def write_s4_dispatch(inv: dict, path: Path | None = None) -> Path:
    """Living S4 writer. Does not clobber a later S-session dispatch."""
    path = Path(path) if path else DISPATCH
    if path.is_file():
        text = path.read_text()
        if "Last completed: S3" not in text and "Last completed: S4" not in text:
            return path
    body = "\n".join([
        "# Gate 0 reproduction dispatch",
        "",
        "Living next-paste. R-science queue exhausted. Template:",
        "`GATE0_NEXT_PROMPTS.md` (S1–S6). Do not walk R8…R12 as science.",
        "",
        "```",
        "Last completed: S4",
        "Window / scenario: A7 cannot-set inventory (AgrimateEU28+Egypt vs C.1)",
        f"hike_2008: S1 2003–11 ×{S1_HOST_HIKE:g}; S3 FBSH ×{S3_HIKE_FBSH:g}; "
        f"author ×{AUTHOR_HIKE:g} (not re-run)",
        f"moy max/min: S1 {S1_HOST_MOY:g}×; S3 FBSH {S3_MOY_FBSH:g}×; "
        f"author {AUTHOR_MOY:g}× (not re-run)",
        f"undisturbed last/first: {S2_LAST_FIRST:g} vs author "
        f"{AUTHOR_LAST_FIRST:g} (S2)",
        "unconverged / failed: S3 USDA 823/1944 / 0 (not re-run)",
        "What you could set / could not set: knobs on fig4_experiment_params; "
        "FB reconstruction labelled not adopted; EU28+Egypt parallel list "
        "labelled not C.1; start-2000 / FAO-since-2005 / Julia cannot-set",
        "Next paste: S5",
        "Why: Egypt not invented; wheat_params αI=3.2; C.1 still "
        "AgrimateRegionsWheat 27; USDA stays default",
        "Skip: R8-as-science; R11; G1/G2; 2006 pin; Bai 10; L1–L8; "
        "FAO ΔS as stocks; invent Egypt",
        "```",
        "",
    ])
    path.write_text(body)
    return path


def run_s4_a7_inventory(out_dir: Path | None = None) -> dict[str, Path]:
    out_dir = Path(out_dir) if out_dir else OUT_DEFAULT
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in PROTECTED_THREE_SCENARIO:
        assert (out_dir / name).is_file(), name
    before = {name: (out_dir / name).read_bytes() for name in PROTECTED_THREE_SCENARIO}
    inv = inventory_a7()
    assert inv["host_has_egypt_node"] is False
    assert inv["wheat_params_alpha_i"] == 3.2
    assert inv["reconstruction_adopted"] is False
    assert inv["region_path"] is None
    csv = write_score_csv(inv, out_dir)
    parallel = write_parallel_csv(out_dir)
    note = write_s4_note(inv, out_dir)
    dispatch = write_s4_dispatch(inv)
    after = {name: (out_dir / name).read_bytes() for name in PROTECTED_THREE_SCENARIO}
    assert before == after, "S4 must not overwrite 2003–11 three-scenario CSVs"
    assert wheat_params().alpha_i == 3.2
    assert "Egypt" not in REGION_NAMES
    return {"note": note, "score": csv, "parallel": parallel, "dispatch": dispatch}
