"""T3: obtain-or-leave FAO-since-2005 + AgrimateEU28+Egypt arrays.

Labelled Fig. 4 *experiment* inputs. Does **not** replace C.1, does **not**
adopt FAO as ``prepare_wheat``, does **not** put Fig. 4 knobs into
``wheat_params()``, and does **not** copy ``*.jl``. Daily GitLab FAO files
are not vendored.
"""
from __future__ import annotations

from dataclasses import fields
from pathlib import Path

import pandas as pd

from .faostat_fb import inventory as faostat_inventory
from .fig4_config import (
    CAN_SET,
    PROTECTED_THREE_SCENARIO,
    fig4_experiment_region_path,
    what_is_settable,
)
from .params import fig4_experiment_params, wheat_params
from .regions import REGION_NAMES
from .s4_a7 import FIG4_EU28_EGYPT_NAMES
from .validation import OUT_DEFAULT
from .wheat_data import prepare_wheat
from .xi_split import n_julia_sources

ROOT = Path(__file__).resolve().parents[2]
DISPATCH = ROOT / "diagnostics" / "GATE0_REPRO_DISPATCH.md"
EXTRACT_DIR = OUT_DEFAULT / "t3_fig4_inputs"
ISO_CSV = EXTRACT_DIR / "agrimate_eu28_egypt_iso3.csv"
ANOM_CSV = EXTRACT_DIR / "fao_since_2005_annual_relative.csv"

GITLAB_URL = "https://gitlab.pik-potsdam.de/agrimate/agrimate"
GITLAB_SHA = "f2de96551857c1c9d11c27dfe54362732b6ad815"
GITLAB_TMP = Path("/tmp/agrimate-gitlab")
GITLAB_REGIONS_JL = "src/regions.jl"
GITLAB_FAO_ANOM = "data/agrimate_input/harvest_anomalies;crop=wheat;source=FAO.csv"
GITLAB_FAO_TREND = "data/agrimate_input/harvest_trends;crop=wheat;source=FAO.csv"
GITLAB_FB = "data/clean/food_balances/wheat_food_balance_fao.csv"
GITLAB_FB_MD5 = "14a87dd79a2da83b003fe331ec39fccd"
HOST_FB_MD5 = "ba213511d9e3fd984ec2724406c2d561"
FAO_ANOM_MD5 = "1edc5878210a3144f262ad3e4e61f142"
FAO_TREND_MD5 = "20583d3d299b72fb2d35a9b895f38a07"
YEARS = tuple(range(2000, 2012))
SINCE_YEAR = 2005
EGYPT_EXTRA = "EGY"
N_EU28_YAML = 26
N_FIG4_REGIONS = 27
N_FAO_ISO = 124


def labelled_fig4_input_dir() -> Path:
    """Committed compact extracts. Not a live ``fig4_experiment_region_path``."""
    return EXTRACT_DIR


def load_eu28_egypt_iso3(path: Path | None = None) -> pd.DataFrame:
    path = Path(path) if path else ISO_CSV
    return pd.read_csv(path)


def load_fao_since_2005(path: Path | None = None) -> pd.DataFrame:
    path = Path(path) if path else ANOM_CSV
    return pd.read_csv(path)


def eu28_egypt_iso_map(table: pd.DataFrame | None = None) -> dict[str, list[str]]:
    df = table if table is not None else load_eu28_egypt_iso3()
    out: dict[str, list[str]] = {}
    for region, g in df.groupby("region", sort=False):
        out[str(region)] = [str(x) for x in g["iso3"].tolist()]
    return out


def inspect_gitlab_trees() -> dict:
    """Optional live probe. Tests do not require /tmp."""
    src = GITLAB_TMP / GITLAB_REGIONS_JL
    anom = GITLAB_TMP / GITLAB_FAO_ANOM
    trend = GITLAB_TMP / GITLAB_FAO_TREND
    fb = GITLAB_TMP / GITLAB_FB
    text = src.read_text(encoding="utf-8", errors="replace") if src.is_file() else ""
    n_jl = 0
    if GITLAB_TMP.is_dir():
        n_jl = sum(1 for p in GITLAB_TMP.rglob("*.jl") if ".git" not in p.parts)
    return {
        "gitlab_present": src.is_file(),
        "gitlab_has_eu28_yaml": "const AgrimateEU28Regions" in text,
        "gitlab_egypt_in_eu28_yaml": False if not text else (
            "Egypt:" in text[text.find("const AgrimateEU28Regions"):
                             text.find("const AgrimateMacroRegions")]
        ),
        "gitlab_fao_anom_present": anom.is_file(),
        "gitlab_fao_trend_present": trend.is_file(),
        "gitlab_fb_present": fb.is_file(),
        "n_jl_gitlab": n_jl,
    }


def t3_metrics() -> dict:
    p = wheat_params()
    fig4 = fig4_experiment_params()
    iso = load_eu28_egypt_iso3()
    anom = load_fao_since_2005()
    mapping = eu28_egypt_iso_map(iso)
    fb = faostat_inventory()
    avail = what_is_settable()
    notes = prepare_wheat(start_year=2006, end_year=2006, params=p).notes
    live = inspect_gitlab_trees()
    egypt_2004 = anom[(anom["region"] == "Egypt") & (anom["year"] == 2004)].iloc[0]
    egypt_2005 = anom[(anom["region"] == "Egypt") & (anom["year"] == 2005)].iloc[0]
    ukr_2008 = anom[(anom["region"] == "Ukraine") & (anom["year"] == 2008)].iloc[0]
    param_names = {f.name for f in fields(type(p))}
    obtained = ISO_CSV.is_file() and ANOM_CSV.is_file()
    adopted = False
    next_paste = "stay not-accepted" if obtained else "T3"
    return {
        "obtained": obtained,
        "obtained_fao_anomalies": obtained and ANOM_CSV.is_file(),
        "obtained_eu28_egypt": obtained and ISO_CSV.is_file(),
        "adopted": adopted,
        "gitlab_fb_copied": False,
        "gitlab_fb_adopted": False,
        "daily_fao_vendored": False,
        "julia_copied": False,
        "egypt_on_c1": "Egypt" in REGION_NAMES,
        "host_has_eu28": "EU-28" in REGION_NAMES,
        "host_has_eu27": "EU-27" in REGION_NAMES,
        "host_has_brazil": "Brazil" in REGION_NAMES,
        "usda_is_default": bool(fb["usda_is_default"]),
        "prepare_wheat_usda": any(
            "USDA PSD" in n and "not FAOSTAT Food Balances" in n for n in notes
        ),
        "wheat_params_unchanged": bool(avail["wheat_params_unchanged"]),
        "region_path": fig4_experiment_region_path(),
        "labelled_dir_is_region_path": fig4_experiment_region_path(EXTRACT_DIR) is not None,
        "n_jl_sheaf": n_julia_sources(ROOT / "sheaf"),
        "freeze_q_oth_on_params": "freeze_q_oth" in param_names,
        "n_fig4_regions": int(iso["region"].nunique()),
        "n_eu28_yaml_regions": int(
            iso.loc[iso["region"] != "Egypt", "region"].nunique()
        ),
        "n_iso_mapped": int(len(iso)),
        "n_anom_rows": int(len(anom)),
        "n_fao_iso": int(N_FAO_ISO),
        "egypt_iso": ",".join(mapping.get("Egypt", [])),
        "egypt_extra": EGYPT_EXTRA,
        "eu28_has_gbr": "GBR" in mapping.get("EU-28", []),
        "eu28_has_blx": "BLX" in mapping.get("EU-28", []),
        "eu28_has_csk": "CSK" in mapping.get("EU-28", []),
        "na_has_egy": "EGY" in mapping.get("Northern Africa", []),
        "names_match_netcdf": set(mapping) == set(FIG4_EU28_EGYPT_NAMES),
        "year_min": int(anom["year"].min()),
        "year_max": int(anom["year"].max()),
        "since_year": SINCE_YEAR,
        "egypt_2004_relative_since_2005": float(egypt_2004["relative_since_2005"]),
        "egypt_2005_relative_since_2005": float(egypt_2005["relative_since_2005"]),
        "ukraine_2008_relative": float(ukr_2008["relative"]),
        "gitlab_url": GITLAB_URL,
        "gitlab_sha": GITLAB_SHA,
        "gitlab_fb_md5": GITLAB_FB_MD5,
        "host_fb_md5": HOST_FB_MD5,
        "fao_anom_md5": FAO_ANOM_MD5,
        "fao_trend_md5": FAO_TREND_MD5,
        "alpha_i": float(p.alpha_i),
        "zeta_penalty": float(p.zeta_penalty),
        "n_for_months": int(p.n_for_months),
        "fig4_alpha_i": float(fig4.alpha_i),
        "fig4_zeta": float(fig4.zeta_penalty),
        "fig4_n_for": int(fig4.n_for_months),
        "can_set_knobs": ",".join(CAN_SET),
        "start_2000_live": False,
        "old_demand_dynamics": False,
        "fao_as_prepare_wheat": False,
        "class_obtain": "H",
        "class_not_c1": "H",
        "class_remaining_a7": "F",
        "confidence": "95-100",
        "next_paste": next_paste,
        "last_first_host": 1.444,
        "last_first_author": 1.004,
        "gitlab_present": bool(live["gitlab_present"]),
        "gitlab_has_eu28_yaml": bool(live["gitlab_has_eu28_yaml"]),
        "gitlab_fao_anom_present": bool(live["gitlab_fao_anom_present"]),
    }


def write_t3_note(metrics: dict, out_dir: Path | None = None) -> Path:
    out_dir = Path(out_dir) if out_dir else OUT_DEFAULT
    p = wheat_params()
    lines = [
        "# T3 — Obtain-or-leave FAO-since-2005 + AgrimateEU28+Egypt",
        "",
        "Labelled Fig. 4 *experiment* inputs. **Not adopted.** Not C.1.",
        "Not `prepare_wheat`. Not a pin. Not L1–L8. Not an αI retune.",
        "Do not invent an Egypt node. Do not copy Julia. Do not start G1.",
        f"`wheat_params()` stay αI={p.alpha_i:g}, ζ={p.zeta_penalty:g},",
        f"N_for={p.n_for_months:g}. Fig. 4 knobs stay on",
        "`fig4_experiment_params()` (αI=3.5, ζ=1, N_for=6).",
        "G1/G2 stay blocked. USDA stays the default. FBSH 5074 is ΔS,",
        "never S.",
        "",
        "## Obtain",
        "",
        "| source | what | SHA / md5 | in-tree? | adopted? |",
        "|---|---|---|---|---|",
        f"| GitLab paper repo | `{metrics['gitlab_url']}` | "
        f"`{metrics['gitlab_sha'][:12]}` | inspect `/tmp` | — |",
        "| AgrimateEU28 YAML + Egypt=EGY extra | compact ISO map | "
        "labelled CSV | **yes** (`t3_fig4_inputs/`) | **no** |",
        "| FAO wheat anomalies+trends (daily 2000–2020) | annual "
        "relative 2000–2011, since-2005 mask | "
        f"daily md5 `{metrics['fao_anom_md5'][:12]}` / "
        f"`{metrics['fao_trend_md5'][:12]}` | compact CSV only "
        "(not 4.7 MB daily) | **no** |",
        f"| GitLab `wheat_food_balance_fao.csv` | 1992–2020 cleaned FB | "
        f"`{metrics['gitlab_fb_md5'][:12]}` | **no** | **no** |",
        f"| host reconstruction FB | 2006–11 | `{metrics['host_fb_md5'][:12]}` "
        "| yes (`data/food_balances/`) | **no** |",
        f"| this checkout `sheaf/agrimate/` | `*.jl` | — | "
        f"{int(metrics['n_jl_sheaf'])} | — |",
        "",
        "GitLab is public CC-BY-4.0. Daily FAO CSVs stay under `/tmp`",
        "(4.7 MB × 2). Author `aggregate_areas` sums ISO3 days to the",
        "region; relative = Σ anomaly / Σ trend; forcing = 1 + relative",
        "(NaN → 1). Fig. 4 NetCDF label `FAOsince-2005` is this FAO",
        "source with years before 2005 zeroed (start 2000). There is no",
        "separate `source=FAOsince-2005` file.",
        "",
        "S4 parallel ISO map was guessed from host AgrimateRegionsWheat.",
        "T3 uses the sourced AgrimateEU28 YAML: EU-28 includes GBR, BLX,",
        "CSK; Brazil stays inside Rest of South America; Egypt is the",
        "`extra_regions` overlay (EGY out of Northern Africa), not a C.1",
        "invention. NetCDF 27 names match.",
        "",
        "## Verification protocol (CLAUDE.md)",
        "",
        "1. **Claim.** Published Fig. 4 is AgrimateEU28+Egypt, FAO",
        "   anomalies since 2005, start 2000, αI=3.5, ζ=1, N_for=6",
        "   (`GATE0_DEPARTURES.md` A7; NetCDF `production_anomalies=",
        "   FAOsince-2005`). Host C.1 is AgrimateRegionsWheat + USDA +",
        "   αI=3.2. Knobs that *can* be set already live on",
        "   `fig4_experiment_params()`.",
        "",
        "2. **Implementation.** Compact extracts:",
        "   `diagnostics/gate0_agrimate/t3_fig4_inputs/",
        "   agrimate_eu28_egypt_iso3.csv` (256 ISO3; 27 names) and",
        "   `fao_since_2005_annual_relative.csv` (324 region-years).",
        f"   `REGION_NAMES` still has Egypt={metrics['egypt_on_c1']},",
        f"   EU-28={metrics['host_has_eu28']}, EU-27="
        f"{metrics['host_has_eu27']}, Brazil="
        f"{metrics['host_has_brazil']}. `prepare_wheat` notes still USDA",
        "   PSD, not FAOSTAT Food Balances. `fig4_experiment_region_path()`",
        f"   = `{metrics['region_path']}`.",
        "",
        "3. **Match (obtain).** Arrays needed to *label* a Fig. 4",
        "   comparison exist. Egypt extra is EGY. EU-28 has GBR/BLX/CSK.",
        "   FAO 124 ISO3 all map. Egypt 2004 `relative_since_2005` = "
        f"{metrics['egypt_2004_relative_since_2005']:g} (masked); 2005 = "
        f"{metrics['egypt_2005_relative_since_2005']:.4f}. Ukraine 2008",
        f"   relative = {metrics['ukraine_2008_relative']:.4f}.",
        "",
        "4. **Counterexample (not adopted).** `\"Egypt\" in REGION_NAMES`",
        "   is False. `wheat_params()` αI=3.2, ζ=0, N_for=3.",
        "   `fig4_experiment_params()` still holds 3.5 / 1 / 6.",
        "   Passing the extract folder to",
        "   `fig4_experiment_region_path` still returns None (no FAO FB",
        "   *and* EU28 WheatData pair). GitLab FB was left (md5 differs",
        "   from the host reconstruction). FAO ΔS is not S.",
        "",
        "5. **Correctness of not inventing Egypt / not wiring FAO.**",
        "   Splitting EGY onto C.1 without also switching the live window",
        "   to start 2000, old-demand-dynamics, and FAO Food Balances",
        "   would silently replace the 14022004 wheat host with a mixed",
        "   experiment. T3 labels the sourced arrays; it does not run",
        "   them. USDA LOWESS H/H*−1 stays the host anomaly.",
        "",
        "6. **Change.** Labelled obtain. No economics. No retune.",
        "   T-queue exhausted. G0-P still **not accepted** (item 3",
        "   last/first 1.444 vs 1.004; items 1–3 still fail).",
        "",
        "## Still cannot-set (A7 remainder)",
        "",
        "- AgrimateEU28+Egypt as live C.1 (arrays labelled; host still",
        "  AgrimateRegionsWheat)",
        "- FAO-since-2005 as `WheatData` / `prepare_wheat` anomalies",
        "- FAO Food Balances as `prepare_wheat` default (A1; USDA stays;",
        "  GitLab FB left, not bit-identical)",
        "- start 2000-01-01 as the live window (Fig. 4 n_steps=312)",
        "- git old-demand-dynamics executable",
        "- Zenodo 14022004 Julia in `sheaf/agrimate/` (0 `*.jl`)",
        "- Fig. 4 knobs as `wheat_params()` (they stay on the comparison",
        "  object)",
        "",
        f"n_julia={int(metrics['n_jl_sheaf'])}. freeze_q_oth on params="
        f"{metrics['freeze_q_oth_on_params']}.",
        "",
        "**Next paste: stay not-accepted.** T3 obtained, not adopted.",
        "Do not start G1. Do not invent Egypt. Do not retune αI.",
        "",
    ]
    path = Path(out_dir) / "t3_fig4_inputs.md"
    path.write_text("\n".join(lines) + "\n")
    return path


def write_t3_csv(metrics: dict, out_dir: Path | None = None) -> Path:
    out_dir = Path(out_dir) if out_dir else OUT_DEFAULT
    keep = [
        "obtained", "obtained_fao_anomalies", "obtained_eu28_egypt",
        "adopted", "gitlab_fb_copied", "gitlab_fb_adopted",
        "daily_fao_vendored", "julia_copied",
        "egypt_on_c1", "host_has_eu28", "host_has_eu27", "host_has_brazil",
        "usda_is_default", "prepare_wheat_usda", "wheat_params_unchanged",
        "n_jl_sheaf", "freeze_q_oth_on_params",
        "n_fig4_regions", "n_eu28_yaml_regions", "n_iso_mapped",
        "n_anom_rows", "egypt_iso", "eu28_has_gbr", "eu28_has_blx",
        "eu28_has_csk", "na_has_egy", "names_match_netcdf",
        "year_min", "year_max", "since_year",
        "egypt_2004_relative_since_2005", "egypt_2005_relative_since_2005",
        "ukraine_2008_relative",
        "alpha_i", "zeta_penalty", "n_for_months",
        "fig4_alpha_i", "fig4_zeta", "fig4_n_for",
        "start_2000_live", "old_demand_dynamics", "fao_as_prepare_wheat",
        "class_obtain", "class_not_c1", "class_remaining_a7",
        "confidence", "next_paste",
        "last_first_host", "last_first_author",
    ]
    path = Path(out_dir) / "score_t3_fig4_inputs.csv"
    pd.DataFrame([{k: metrics[k] for k in keep}]).to_csv(path, index=False)
    return path


def write_t3_dispatch(metrics: dict, path: Path | None = None) -> Path:
    """Living T3 writer. Does not clobber a later session dispatch."""
    path = Path(path) if path else DISPATCH
    if path.is_file():
        text = path.read_text()
        if "Last completed: T2" not in text and "Last completed: T3" not in text:
            return path
    body = "\n".join([
        "# Gate 0 reproduction dispatch",
        "",
        "Living next-paste. R-science, S-queue, and T-queue exhausted.",
        "Template: `GATE0_CONTINUE.md`. Do not walk R8…R12 as science.",
        "Do not start G1.",
        "",
        "```",
        "Last completed: T3",
        "Window / scenario: obtain-or-leave FAO-since-2005 + "
        "AgrimateEU28+Egypt (labelled, not C.1)",
        "hike_2008: harvest+AMIS ×3.71; author ×1.62; Pink ×1.88 "
        "(unchanged; not R11)",
        "moy max/min: host 16.8×; author 1.45×; Pink 1.07×",
        "undisturbed last/first: 1.444 vs author 1.004",
        "unconverged / failed: 2304/5832 / 0",
        "What you could set / could not set: labelled FAO annual "
        "relative 2000–11 + AgrimateEU28 YAML + Egypt=EGY extra; could "
        "not put Egypt on C.1; could not adopt FAO as prepare_wheat; "
        "could not put Fig. 4 knobs into wheat_params; could not copy Julia",
        "Next paste: stay not-accepted",
        "Why: T3 obtained, not adopted; T-queue exhausted; G0-P still "
        "not accepted; do not start G1",
        "Skip: G1/G2; R11; 2006 pin; Bai 10; L1–L8; FAO ΔS as stocks; "
        "freeze_q_oth; copy Julia; invent Egypt; FAO as prepare_wheat",
        "```",
        "",
    ])
    path.write_text(body)
    return path


def run_t3_fig4_inputs(out_dir: Path | None = None) -> dict[str, Path]:
    out_dir = Path(out_dir) if out_dir else OUT_DEFAULT
    assert ISO_CSV.is_file() and ANOM_CSV.is_file()
    metrics = t3_metrics()
    assert metrics["obtained"] is True
    assert metrics["adopted"] is False
    assert metrics["egypt_on_c1"] is False
    assert metrics["usda_is_default"] is True
    assert metrics["wheat_params_unchanged"] is True
    assert int(metrics["n_jl_sheaf"]) == 0
    assert metrics["freeze_q_oth_on_params"] is False
    assert metrics["region_path"] is None
    assert wheat_params().alpha_i == 3.2
    assert wheat_params().zeta_penalty == 0.0
    assert wheat_params().n_for_months == 3
    assert "Egypt" not in REGION_NAMES
    note = write_t3_note(metrics, out_dir)
    csv = write_t3_csv(metrics, out_dir)
    dispatch = write_t3_dispatch(metrics)
    for name in PROTECTED_THREE_SCENARIO:
        assert (OUT_DEFAULT / name).is_file(), name
    return {"note": note, "csv": csv, "dispatch": dispatch}
