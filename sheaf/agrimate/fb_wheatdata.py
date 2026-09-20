"""R6: labelled parallel WheatData from raw FAOSTAT FBSH. USDA stays default.

Not Agrimate's cleaned ``wheat_food_balance_fao.csv`` (impute / QCL+TCL /
rebalance). Not FoodTradeNetwork 2015–21 averages. Not a ``prepare_wheat``
switch. Stocks cannot be read from FBSH Stock Variation (5074); Psi is
copied from the USDA host and labelled. Anomalies are H_y / H_star − 1
on the 2006–11 extract, not 10-year LOWESS and not author FAO-since-2005.

S3: re-score that parallel against the S1 member-sum USDA host on one
harvest+AMIS window. Historical R6 note/CSVs stay frozen (China 0.50×).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from sheaf.calendar24 import STEPS_PER_YEAR
from sheaf.data_faostat import _mappings, load_trade_matrix
from sheaf.data_usda import load_price_series_monthly
from sheaf.seasonal import load_harvest_calendar

from .faostat_fb import FAOSTAT_FB, inventory
from .fig4_config import PROTECTED_THREE_SCENARIO, _last_first, _moy_maxmin
from .harvest import step_profile_from_months
from .model import run_agrimate
from .params import AgrimateParams, wheat_params
from .regions import D9_ALPHA, D9_NU, REGION_NAMES, iso3_to_region
from .restrictions import restriction_matrix
from .validation import OUT_DEFAULT, _hike, monthly_price
from .wheat_data import WheatData, _income_ac, prepare_wheat

ROOT = Path(__file__).resolve().parents[2]
DISPATCH = ROOT / "diagnostics" / "GATE0_REPRO_DISPATCH.md"
START_YEAR = 2006
END_YEAR = 2008
KT_TO_MMT = 1e-3
BASE_YEARS = (2007, 2008, 2009)

# Territorial totals that duplicate country rows on this extract.
# China 351 == China, mainland 41 (2007 production both 109298).
# Belgium-Luxembourg 15 duplicates Belgium 255. 357 is a China+Taiwan combo.
DROP_AREA_CODES = {15, 351, 357}
ISO_FIX = {"TMP": "TLS"}  # conversion table ISO3 alpha vs Agrimate TLS


def _area_code(val) -> int | None:
    try:
        return int(float(val))
    except (TypeError, ValueError):
        return None


def map_fbsh_row(area_code, area: str) -> tuple[str | None, str | None, str]:
    """FAOSTAT country row → (iso3, Agrimate region, skip_reason)."""
    code = _area_code(area_code)
    if code is None:
        return None, None, "bad_code"
    if code >= 5000:
        return None, None, "aggregate"
    if code in DROP_AREA_CODES:
        return None, None, "duplicate_total"
    fao2iso, name2iso, _valid = _mappings()
    iso = fao2iso.get(code) or name2iso.get(str(area).strip())
    if iso is None:
        return None, None, "unmapped_iso"
    iso = ISO_FIX.get(iso, iso)
    region = iso3_to_region().get(iso)
    if region is None:
        return None, None, "unmapped_region"
    return iso, region, ""


def load_fbsh_wheat() -> pd.DataFrame:
    path = FAOSTAT_FB / "wheat_fbsh_2006_2011.csv"
    if not path.is_file():
        raise FileNotFoundError(
            f"{path} missing — run: PYTHONPATH=. python "
            "scripts/fetch_external_data.py --faostat-fb"
        )
    raw = pd.read_csv(path)
    rows = []
    skip = {}
    for rec in raw.itertuples(index=False):
        iso, region, reason = map_fbsh_row(rec.area_code, rec.area)
        if region is None:
            skip[reason] = skip.get(reason, 0) + 1
            continue
        rows.append({
            "area_code": rec.area_code,
            "area": rec.area,
            "iso": iso,
            "region": region,
            "year": int(rec.year),
            "production": float(rec.production) if pd.notna(rec.production) else 0.0,
            "domestic_supply": float(rec.domestic_supply) if pd.notna(rec.domestic_supply) else 0.0,
            "imports": float(rec.imports) if pd.notna(rec.imports) else 0.0,
            "exports": float(rec.exports) if pd.notna(rec.exports) else 0.0,
            "food": float(rec.food) if pd.notna(rec.food) else 0.0,
            "feed": float(rec.feed) if pd.notna(rec.feed) else 0.0,
            "stock_variation": (
                float(rec.stock_variation) if pd.notna(rec.stock_variation) else 0.0
            ),
        })
    df = pd.DataFrame(rows)
    df.attrs["skip_counts"] = skip
    return df


def fbsh_regional_annual(df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Member-sum, 1000 t → MMT. Not A8 groupby.mean()."""
    df = df if df is not None else load_fbsh_wheat()
    cols = ["production", "domestic_supply", "imports", "exports",
            "food", "feed", "stock_variation"]
    g = df.groupby(["region", "year"], as_index=False)[cols].sum()
    for c in cols:
        g[c] = g[c] * KT_TO_MMT
    return g


def _base_means(annual: pd.DataFrame) -> pd.DataFrame:
    base = annual[annual["year"].between(BASE_YEARS[0], BASE_YEARS[-1])]
    return base.groupby("region")[
        ["production", "domestic_supply", "imports", "exports"]
    ].mean()


def prepare_wheat_fbsh(
    start_year: int = 2003,
    end_year: int = 2011,
    params: AgrimateParams | None = None,
) -> WheatData:
    """Parallel WheatData. Does not replace ``prepare_wheat``."""
    params = params or wheat_params()
    regions = list(REGION_NAMES)
    n_r = len(regions)
    n_y = params.n_year
    usda = prepare_wheat(start_year=start_year, end_year=end_year, params=params)
    fb = load_fbsh_wheat()
    annual = fbsh_regional_annual(fb)
    g = _base_means(annual)
    H_ann = np.array([float(g["production"].get(r, 0.0)) for r in regions])
    C_ann = np.array([float(g["domestic_supply"].get(r, 0.0)) for r in regions])
    X_ann = np.array([float(g["exports"].get(r, 0.0)) for r in regions])
    M_ann = np.array([float(g["imports"].get(r, 0.0)) for r in regions])

    E0 = load_trade_matrix("wheat", window=(2006, 2007))
    m = iso3_to_region()
    T = np.zeros((n_r, n_r))
    ridx = {r: i for i, r in enumerate(regions)}
    for iso_e, row in E0.iterrows():
        er = m.get(str(iso_e), "Rest of World")
        if er not in ridx:
            continue
        for iso_i, val in row.items():
            ir = m.get(str(iso_i), "Rest of World")
            if ir not in ridx:
                continue
            T[ridx[er], ridx[ir]] += float(val)
    T_int = T.copy()
    np.fill_diagonal(T_int, 0.0)
    row_sum = T_int.sum(axis=1)
    fb_x = np.maximum(X_ann, 0.0)
    for i in range(n_r):
        if row_sum[i] > 0 and fb_x[i] > 0:
            T_int[i] *= fb_x[i] / row_sum[i]
        else:
            T_int[i] = 0.0
    world_x = T_int.sum()
    if world_x > 0:
        T_int[T_int < 0.01 * world_x / max(n_r * n_r, 1)] = 0.0
    domestic = np.maximum(H_ann - T_int.sum(axis=1), 0.0)
    T_star = T_int.copy()
    np.fill_diagonal(T_star, domestic)
    C_from_flow = T_star.sum(axis=0)
    use_C = np.where(C_from_flow > 0, C_from_flow, C_ann)
    H_from_flow = T_star.sum(axis=1)
    use_H = np.where(H_from_flow > 0, H_from_flow, H_ann)

    cal = load_harvest_calendar("wheat")
    cal_map = {str(r.country): (int(r.harvest_start_month), int(r.harvest_end_month))
               for r in cal.itertuples()}
    sh = {"Argentina", "Australia", "Brazil", "Rest of Oceania", "Southern Africa",
          "Rest of South America"}
    profile = np.zeros((n_r, n_y))
    for i, r in enumerate(regions):
        if r in cal_map:
            a, b = cal_map[r]
        elif r == "USA":
            a, b = 6, 9
        elif r == "EU-27":
            a, b = 7, 8
        elif r in sh:
            a, b = 11, 1
        else:
            a, b = 6, 8
        profile[i] = step_profile_from_months(a, b, n_y)
    H_star = use_H[:, None] * profile

    XI_ann = T_int.sum(axis=1)
    XD_ann = np.maximum(use_H - XI_ann, 0.0)
    C_star = use_C / n_y
    XI_star = XI_ann / n_y
    XD_star = XD_ann / n_y
    XI_star_path = XI_ann[:, None] * profile
    XD_star_path = XD_ann[:, None] * profile
    XI_world = float(XI_star.sum())

    # FBSH has ΔS, not ending stocks. Copy USDA Psi (labelled remaining A1).
    Psi = np.array(usda.Psi, dtype=float)
    A_c = np.array([_income_ac(r) for r in regions])
    A_d = np.array([
        float(np.clip(0.05 + 0.4 * (M_ann[i] / max(use_C[i], 1e-8)), 0.02, 0.9))
        for i in range(n_r)
    ])
    alpha_d = np.array([
        D9_ALPHA[r] if r in D9_ALPHA else (
            params.alpha_i * XI_star[i] / XI_world if XI_world > 0 else 1.0)
        for i, r in enumerate(regions)
    ])
    nu = np.array([D9_NU.get(r, 1.0) for r in regions])

    years = list(range(start_year, end_year + 1))
    anomaly = np.zeros((n_r, len(years)))
    prod = annual.pivot(index="region", columns="year", values="production")
    for i, r in enumerate(regions):
        star = float(g["production"].get(r, 0.0))
        if star <= 0 or r not in prod.index:
            continue
        for j, y in enumerate(years):
            if y in prod.columns and y >= 2005:
                hy = float(prod.loc[r, y])
                if np.isfinite(hy):
                    anomaly[i, j] = hy / star - 1.0

    delta = restriction_matrix(regions, start_year, end_year, crop="wheat")
    n_bind = int((delta > 0).sum())
    bound = [r for i, r in enumerate(regions) if float(delta[i].max()) > 0]
    skip = fb.attrs.get("skip_counts") or {}
    notes = [
        "PARALLEL WheatData: FAOSTAT FBSH wheat 2006–11, not USDA PSD.",
        "Not author wheat_food_balance_fao.csv (impute/QCL+TCL/rebalance).",
        "Country rows only (area_code<5000); dropped China 351, Belgium-Luxembourg 15.",
        "Members summed (not A8 groupby.mean()). Unit 1000 t → MMT.",
        "C* from domestic_supply then T* inflows. T* E0 2006–07 rescaled to FBSH exports.",
        "Psi copied from USDA prepare_wheat (FBSH Stock Variation is ΔS, not ending stocks).",
        "Anomalies: H_y/H_2007-09 − 1 on the 2006–11 extract, not 10-year LOWESS.",
        f"AMIS wheat Δ: {n_bind} region-steps, max={float(delta.max()):.2f}, "
        f"regions={bound or 'none'}.",
        f"Mapping skip counts: {skip}.",
        "prepare_wheat default is still USDA (A1). This object is not adopted.",
    ]
    pink = load_price_series_monthly()
    p0 = float(pink[(pink["year"] == 2006)]["wheat"].mean())
    return WheatData(
        regions=regions, H_star=H_star, H_annual=use_H, C_star=C_star,
        XI_star=XI_star, XD_star=XD_star,
        XI_star_path=XI_star_path, XD_star_path=XD_star_path,
        XI_world=XI_world, T_star=T_star,
        Psi=Psi, A_c=A_c, A_d=A_d, alpha_d=alpha_d, nu=nu, profile=profile,
        anomaly=anomaly, delta=delta, p0=p0, start_year=start_year,
        end_year=end_year, notes=notes,
    )


def quantity_table(usda: WheatData, fbsh: WheatData) -> pd.DataFrame:
    rows = []
    for i, r in enumerate(usda.regions):
        hu, hf = float(usda.H_annual[i]), float(fbsh.H_annual[i])
        cu, cf = float(usda.C_star[i] * STEPS_PER_YEAR), float(fbsh.C_star[i] * STEPS_PER_YEAR)
        xu, xf = float(usda.XI_star[i] * STEPS_PER_YEAR), float(fbsh.XI_star[i] * STEPS_PER_YEAR)
        rows.append({
            "region": r,
            "H_usda": hu, "H_fbsh": hf,
            "H_ratio": (hf / hu) if hu else float("nan"),
            "C_usda": cu, "C_fbsh": cf,
            "C_ratio": (cf / cu) if cu else float("nan"),
            "XI_usda": xu, "XI_fbsh": xf,
            "XI_ratio": (xf / xu) if xu else float("nan"),
            "Psi_usda": float(usda.Psi[i]),
            "Psi_fbsh": float(fbsh.Psi[i]),
        })
    return pd.DataFrame(rows)


def _fmt(x, nd: int = 2) -> str:
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "nan"
    return f"{float(x):.{nd}f}"


def score_harvest_amis(usda: WheatData, fbsh: WheatData, params: AgrimateParams) -> dict:
    kwargs = dict(
        params=params, use_anomalies=True, use_restrictions=True,
        start_year=START_YEAR, end_year=END_YEAR,
    )
    ru = run_agrimate(data=usda, **kwargs)
    rf = run_agrimate(data=fbsh, **kwargs)
    pu = monthly_price(ru)
    pf = monthly_price(rf)
    n_solves = len(ru.regions) * int(ru.price_index.size)
    i_cn = ru.regions.index("China")
    i_ea = ru.regions.index("Eastern Africa")
    return {
        "hike_usda": _hike(pu, START_YEAR, 2008),
        "hike_fbsh": _hike(pf, START_YEAR, 2008),
        "moy_usda": _moy_maxmin(pu),
        "moy_fbsh": _moy_maxmin(pf),
        "last_first_usda": _last_first(pu),
        "last_first_fbsh": _last_first(pf),
        "mean_2006_usda": float(pu[pu.index.year == 2006].mean()),
        "mean_2006_fbsh": float(pf[pf.index.year == 2006].mean()),
        "pidx_max_usda": float(np.nanmax(ru.price_index)),
        "pidx_max_fbsh": float(np.nanmax(rf.price_index)),
        "failed_usda": int(ru.failed_solves),
        "failed_fbsh": int(rf.failed_solves),
        "unconverged_usda": int(ru.unconverged_solves),
        "unconverged_fbsh": int(rf.unconverged_solves),
        "n_solves": int(n_solves),
        "runtime_usda_s": float(ru.runtime_s),
        "runtime_fbsh_s": float(rf.runtime_s),
        "H_sum_usda": float(usda.H_annual.sum()),
        "H_sum_fbsh": float(fbsh.H_annual.sum()),
        "China_H_usda": float(usda.H_annual[i_cn]),
        "China_H_fbsh": float(fbsh.H_annual[i_cn]),
        "EA_H_usda": float(usda.H_annual[i_ea]),
        "EA_H_fbsh": float(fbsh.H_annual[i_ea]),
        "XI_world_usda": float(usda.XI_world * STEPS_PER_YEAR),
        "XI_world_fbsh": float(fbsh.XI_world * STEPS_PER_YEAR),
        "alpha_i": float(params.alpha_i),
        "zeta_penalty": float(params.zeta_penalty),
        "n_for_months": int(params.n_for_months),
        "p_sto_annual": float(params.p_sto_annual),
        "xmin_share": float(params.xmin_share),
    }


def write_quantity_csv(tab: pd.DataFrame, out_dir: Path) -> Path:
    path = out_dir / "score_fb_wheatdata_quantities.csv"
    tab.to_csv(path, index=False)
    return path


def write_score_csv(score: dict, out_dir: Path) -> Path:
    path = out_dir / "score_fb_wheatdata.csv"
    pd.DataFrame([score]).to_csv(path, index=False)
    return path


def write_fb_wheatdata_note(
    score: dict, tab: pd.DataFrame, out_dir: Path | None = None,
) -> Path:
    out_dir = Path(out_dir) if out_dir else OUT_DEFAULT
    out_dir.mkdir(parents=True, exist_ok=True)
    cn = tab[tab["region"] == "China"].iloc[0]
    ea = tab[tab["region"] == "Eastern Africa"].iloc[0]
    us = tab[tab["region"] == "USA"].iloc[0]
    eu = tab[tab["region"] == "EU-27"].iloc[0]
    inv = inventory()
    lines = [
        "# R6 — Parallel FBSH WheatData vs USDA (one harvest+AMIS window)",
        "",
        "**Not adopted. Leave A1. USDA remains the 2006–11 default.**",
        "`prepare_wheat` is unchanged. `wheat_params()` stay αI=3.2, p_sto=0.1,",
        "xmin=0.2, ζ=0, N_for=3. L1–L8 stay rejected. Bai α_foreign=10 not",
        "adopted. Unforced price is not pinned. G1/G2 stay blocked.",
        "",
        "Raw FAOSTAT **FBSH** wheat 2006–11 (item 2511, 1000 t) maps onto the",
        "27 C.1 nodes. This is **not** author `wheat_food_balance_fao.csv`.",
        "FoodTradeNetwork 2015–21 averages were not copied. FBS 2010+ was",
        "not mixed in.",
        "",
        "## Verification protocol",
        "",
        "1. **Claim.** Agrimate E.1 uses FAOSTAT Food Balances.",
        "2. **Implementation.** `prepare_wheat` still groups USDA PSD 2007–09.",
        "   `prepare_wheat_fbsh` is a labelled parallel.",
        "3. **Match.** Default path does not; A1 stays. Parallel uses raw FBSH,",
        "   not the AgriculturalData impute/QCL+TCL/rebalance pipeline.",
        "4. **Counterexample.** China H USDA "
        f"{_fmt(cn['H_usda'], 1)} vs FBSH {_fmt(cn['H_fbsh'], 1)} "
        f"(ratio {_fmt(cn['H_ratio'])}) is A8 mean-of-members, not a mapping",
        "   failure. USA H matches "
        f"({_fmt(us['H_usda'], 1)} vs {_fmt(us['H_fbsh'], 1)}).",
        "5. **Correctness of not switching.** Stocks are USDA Psi (FBSH 5074 is",
        "   ΔS). Anomalies are H_y/H_star−1 on a 6-year extract, not author",
        "   FAO-since-2005. Intra-region FB exports are not extra-EU PSD.",
        "   Switching the host would retune 2006–11 quantities.",
        "6. **Change.** None to economics. USDA stays default.",
        "",
        "## Mapping (faithful enough to run, labelled)",
        "",
        "- Country rows only (`area_code < 5000`). Aggregates (World, EU-27",
        "  row 5707, Europe, …) dropped. EU-27 **member sum** production",
        "  2007–09 equals the EU-27 aggregate row (122.42 MMT).",
        "- Dropped duplicate totals: China 351 (same 2007 production as",
        "  mainland 41), Belgium-Luxembourg 15.",
        "- ISO3 via `data_faostat._mappings` plus TMP→TLS. Laptop",
        f"  `{inv['laptop_data']['path']}` mounted="
        f"{inv['laptop_data']['exists']}.",
        "- Members **summed** (not A8 `groupby.mean()`).",
        "",
        "## 2007–09 baseline (MMT, after T* rebuild)",
        "",
        "| Region | H USDA | H FBSH | ratio | C USDA | C FBSH |",
        "|---|---:|---:|---:|---:|---:|",
        f"| USA | {_fmt(us['H_usda'], 1)} | {_fmt(us['H_fbsh'], 1)} | "
        f"{_fmt(us['H_ratio'])} | {_fmt(us['C_usda'], 1)} | {_fmt(us['C_fbsh'], 1)} |",
        f"| China | {_fmt(cn['H_usda'], 1)} | {_fmt(cn['H_fbsh'], 1)} | "
        f"{_fmt(cn['H_ratio'])} | {_fmt(cn['C_usda'], 1)} | {_fmt(cn['C_fbsh'], 1)} |",
        f"| EU-27 | {_fmt(eu['H_usda'], 1)} | {_fmt(eu['H_fbsh'], 1)} | "
        f"{_fmt(eu['H_ratio'])} | {_fmt(eu['C_usda'], 1)} | {_fmt(eu['C_fbsh'], 1)} |",
        f"| Eastern Africa | {_fmt(ea['H_usda'], 2)} | {_fmt(ea['H_fbsh'], 2)} | "
        f"{_fmt(ea['H_ratio'])} | {_fmt(ea['C_usda'], 1)} | {_fmt(ea['C_fbsh'], 1)} |",
        f"| World 27-node | {_fmt(score['H_sum_usda'], 1)} | "
        f"{_fmt(score['H_sum_fbsh'], 1)} | "
        f"{_fmt(score['H_sum_fbsh'] / score['H_sum_usda'] if score['H_sum_usda'] else float('nan'))} | — | — |",
        "",
        "Named single-row exporters (USA, Russia, Ukraine, India, Canada, …)",
        "match ~1.00. Multi-country nodes are larger on FBSH because USDA A8",
        "averages sparse PSD members. Next paste **R7** is that sensitivity",
        "on the USDA host, not a reason to adopt FBSH.",
        "",
        "## 2006–08 harvest+AMIS",
        "",
        "| | USDA `prepare_wheat` | FBSH parallel |",
        "|---|---:|---:|",
        f"| hike_2008 | ×{_fmt(score['hike_usda'])} | ×{_fmt(score['hike_fbsh'])} |",
        f"| moy max/min | {_fmt(score['moy_usda'], 1)}× | {_fmt(score['moy_fbsh'], 1)}× |",
        f"| 2006 mean USD/t | {_fmt(score['mean_2006_usda'], 1)} | {_fmt(score['mean_2006_fbsh'], 1)} |",
        f"| unconverged | {int(score['unconverged_usda'])}/{int(score['n_solves'])} | "
        f"{int(score['unconverged_fbsh'])}/{int(score['n_solves'])} |",
        f"| failed | {int(score['failed_usda'])} | {int(score['failed_fbsh'])} |",
        f"| XI* annual | {_fmt(score['XI_world_usda'], 1)} | {_fmt(score['XI_world_fbsh'], 1)} |",
        "",
        f"`wheat_params` αI={score['alpha_i']:g}, ζ={score['zeta_penalty']:g}, "
        f"N_for={int(score['n_for_months'])}. Psi was USDA on both runs.",
        "",
        "## Remaining cannot-set (A1 / A7)",
        "",
        "- Author cleaned FB / QCL+TCL rebalance",
        "- Ending stocks from FAO (Psi stayed USDA)",
        "- FAO-since-2005 LOWESS anomalies; AgrimateEU28+Egypt",
        "- 2015–21 FoodTradeNetwork averages (not used)",
        "",
        "**Next paste: R7.** A8 mean-vs-sum on USDA 2007–09 means (China/EA).",
        "R6 does not unlock G1. Do not retune αI / p_sto / xmin.",
        "",
    ]
    path = out_dir / "fb_wheatdata.md"
    path.write_text("\n".join(lines) + "\n")
    return path


def write_r6_dispatch(score: dict, path: Path | None = None) -> Path:
    """Historical R6 writer. Does not clobber a moved living dispatch."""
    path = Path(path) if path else DISPATCH
    if path.is_file() and "Last completed: R6" not in path.read_text():
        return path
    why = (
        f"FBSH parallel not adopted; China H {_fmt(score['China_H_usda'], 1)}→"
        f"{_fmt(score['China_H_fbsh'], 1)} (A8); hike ×{_fmt(score['hike_usda'])}→"
        f"×{_fmt(score['hike_fbsh'])}; USDA still prepare_wheat default"
    )
    body = "\n".join([
        "# Gate 0 reproduction dispatch",
        "",
        "Living next-paste. Rewrite after every R-session from **that run’s",
        "numbers**. Do not walk R3…R12 in order. Template:",
        "`GATE0_REPRO_PROMPTS.md` (Adaptive rule).",
        "",
        "```",
        "Last completed: R6",
        "Window / scenario: 2006–08 harvest+AMIS USDA vs FBSH parallel WheatData",
        f"hike_2008 (USDA → FBSH → author knobs/series): "
        f"×{_fmt(score['hike_usda'])} → ×{_fmt(score['hike_fbsh'])} → ×1.62",
        f"moy max/min: {_fmt(score['moy_usda'], 1)}× → {_fmt(score['moy_fbsh'], 1)}× → 1.51×",
        "undisturbed last/first: default 1.630 → qoth_freeze 1.019 → author 1.004",
        f"unconverged / failed: USDA {int(score['unconverged_usda'])}/"
        f"{int(score['n_solves'])} failed={int(score['failed_usda'])}; "
        f"FBSH {int(score['unconverged_fbsh'])}/{int(score['n_solves'])} "
        f"failed={int(score['failed_fbsh'])}",
        "What you could set / could not set: raw FBSH H/C/X mapped; Psi USDA; "
        "anomalies H/Hstar−1; author cleaned FB absent",
        "Next paste: R7",
        f"Why: {why}",
        "Skip: R11; G1/G2; do not adopt FBSH; do not retune αI; do not copy "
        "2015–21 averages",
        "```",
        "",
    ])
    path.write_text(body)
    return path


def run_fb_wheatdata_score(out_dir: Path | None = None) -> dict[str, Path]:
    out_dir = Path(out_dir) if out_dir else OUT_DEFAULT
    out_dir.mkdir(parents=True, exist_ok=True)
    params = wheat_params()
    assert params.alpha_i == 3.2
    usda = prepare_wheat(start_year=START_YEAR, end_year=END_YEAR, params=params)
    fbsh = prepare_wheat_fbsh(start_year=START_YEAR, end_year=END_YEAR, params=params)
    tab = quantity_table(usda, fbsh)
    score = score_harvest_amis(usda, fbsh, params)
    # overwrite China_H_fbsh in case the `and` bug — set from arrays
    score["China_H_usda"] = float(usda.H_annual[usda.regions.index("China")])
    score["China_H_fbsh"] = float(fbsh.H_annual[fbsh.regions.index("China")])
    qpath = write_quantity_csv(tab, out_dir)
    spath = write_score_csv(score, out_dir)
    note = write_fb_wheatdata_note(score, tab, out_dir)
    dispatch = write_r6_dispatch(score)
    for name in PROTECTED_THREE_SCENARIO:
        assert (out_dir / name).is_file(), name
    assert wheat_params().alpha_i == 3.2
    return {"note": note, "quantities": qpath, "score": spath, "dispatch": dispatch}


# S1 USDA 2003–11 harvest+AMIS (living host). Not the R6 2006–08-only window.
S1_HOST_HIKE = 3.71
S1_HOST_MOY = 16.8
S1_HOST_LAST_FIRST = 1.444
AUTHOR_HIKE = 1.62
AUTHOR_MOY = 1.45
AUTHOR_LAST_FIRST = 1.004


def s3_adoption_verdict(score: dict) -> dict:
    """Adopt FBSH only if items 1–3 improve and moy does not worsen.

    This run is harvest+AMIS 2006–08. Item 3 is undisturbed 2006–11
    last/first on the USDA host (S2: 1.444) and is not re-measured here.
    Author cleaned FB is still absent. Psi is still USDA (5074 is ΔS).
    """
    moy_usda = float(score["moy_usda"])
    moy_fbsh = float(score["moy_fbsh"])
    moy_worsened = moy_fbsh > moy_usda + 1e-12
    item3_improved = False
    reasons = [
        "item 3 undisturbed last/first still "
        f"{_fmt(S1_HOST_LAST_FIRST, 3)} on the USDA host (author "
        f"{_fmt(AUTHOR_LAST_FIRST, 3)}); FBSH not scored undisturbed",
        "author wheat_food_balance_fao.csv still absent (A7/A1 cannot-set)",
        "Psi still USDA ending_stocks (FBSH 5074 is ΔS, not S)",
    ]
    if moy_worsened:
        reasons.append(
            f"moy worsened {_fmt(moy_usda, 1)}× → {_fmt(moy_fbsh, 1)}× "
            f"on this 2006–08 window (S1 host 2003–11 moy {S1_HOST_MOY:g}×)"
        )
    else:
        reasons.append(
            f"moy {_fmt(moy_usda, 1)}× → {_fmt(moy_fbsh, 1)}× does not "
            "unlock a switch without items 1–3"
        )
    return {
        "adopt": False,
        "item3_improved": item3_improved,
        "moy_worsened": moy_worsened,
        "why": "; ".join(reasons),
    }


def write_s3_fbsh_note(score: dict, tab: pd.DataFrame, verdict: dict,
                       out_dir: Path) -> Path:
    cn = tab[tab["region"] == "China"].iloc[0]
    ea = tab[tab["region"] == "Eastern Africa"].iloc[0]
    us = tab[tab["region"] == "USA"].iloc[0]
    eu = tab[tab["region"] == "EU-27"].iloc[0]
    inv = inventory()
    p = wheat_params()
    lines = [
        "# S3 — FBSH H/C vs S1 member-sum USDA (one harvest+AMIS window)",
        "",
        "**Not adopted. Leave A1. USDA remains the 2006–11 `prepare_wheat`",
        "default.** `wheat_params()` stay "
        f"αI={p.alpha_i:g}, p_sto={p.p_sto_annual:g}, xmin={p.xmin_share:g},",
        f"ζ={p.zeta_penalty:g}, N_for={p.n_for_months:g}. L1–L8 stay rejected.",
        "Bai α_foreign=10 not adopted. Unforced price is not pinned. G1/G2",
        "stay blocked. Historical R6 note (`fb_wheatdata.md`) is frozen.",
        "",
        "Raw FAOSTAT **FBSH** wheat 2006–11 (item 2511, 1000 t) vs USDA",
        "member-sum (S1). This is **not** author `wheat_food_balance_fao.csv`.",
        "FoodTradeNetwork 2015–21 averages were not copied. FBS 2010+ was",
        "not mixed in. FBSH Stock Variation (element **5074**) is not S.",
        "",
        "## Verification protocol (CLAUDE.md)",
        "",
        "1. **Claim.** Agrimate E.1 uses FAOSTAT Food Balances. S3 may switch",
        "`prepare_wheat` to the FBSH parallel only if DEVELOPMENT items 1–3",
        "improve **and** moy does not worsen versus the S1 USDA host.",
        "",
        "2. **Implementation.** `prepare_wheat` is USDA PSD member-sum then",
        "mean (`ending_stocks` is S). `prepare_wheat_fbsh` is a labelled",
        "parallel: FBSH H/C/X, Psi copied from USDA, 5074 unused as a stock",
        "level.",
        "",
        "3. **Match.** Default path is still USDA (A1). After S1, China and",
        "Eastern Africa H sit next to FBSH (not 0.50× / 0.10×). Author",
        "cleaned FB is still absent.",
        "",
        "4. **Counterexample.** China H USDA "
        f"{_fmt(cn['H_usda'], 1)} vs FBSH {_fmt(cn['H_fbsh'], 1)} "
        f"(ratio {_fmt(cn['H_ratio'])}). USA "
        f"{_fmt(us['H_usda'], 1)} vs {_fmt(us['H_fbsh'], 1)}. "
        f"2006–08 harvest+AMIS moy USDA {_fmt(score['moy_usda'], 1)}× vs",
        f"FBSH {_fmt(score['moy_fbsh'], 1)}×; hike ×{_fmt(score['hike_usda'])}",
        f"vs ×{_fmt(score['hike_fbsh'])} (S1 2003–11 host ×{S1_HOST_HIKE:g};",
        f"author ×{AUTHOR_HIKE:g}). Item 3 last/first is still",
        f"{_fmt(S1_HOST_LAST_FIRST, 3)} on the USDA host.",
        "",
        "5. **Correctness of not switching.** "
        f"{verdict['why']}. Switching would retune 2006–11 quantities",
        "without a sourced cleaned FB or an item-3 gain.",
        "",
        "6. **Change.** None to economics. USDA stays default. Do not retune",
        "αI / p_sto / xmin. Do not treat 5074 as stocks.",
        "",
        "## 2007–09 baseline (MMT, after T* rebuild)",
        "",
        "| Region | H USDA | H FBSH | ratio | C USDA | C FBSH |",
        "|---|---:|---:|---:|---:|---:|",
        f"| USA | {_fmt(us['H_usda'], 1)} | {_fmt(us['H_fbsh'], 1)} | "
        f"{_fmt(us['H_ratio'])} | {_fmt(us['C_usda'], 1)} | {_fmt(us['C_fbsh'], 1)} |",
        f"| China | {_fmt(cn['H_usda'], 1)} | {_fmt(cn['H_fbsh'], 1)} | "
        f"{_fmt(cn['H_ratio'])} | {_fmt(cn['C_usda'], 1)} | {_fmt(cn['C_fbsh'], 1)} |",
        f"| EU-27 | {_fmt(eu['H_usda'], 1)} | {_fmt(eu['H_fbsh'], 1)} | "
        f"{_fmt(eu['H_ratio'])} | {_fmt(eu['C_usda'], 1)} | {_fmt(eu['C_fbsh'], 1)} |",
        f"| Eastern Africa | {_fmt(ea['H_usda'], 2)} | {_fmt(ea['H_fbsh'], 2)} | "
        f"{_fmt(ea['H_ratio'])} | {_fmt(ea['C_usda'], 1)} | {_fmt(ea['C_fbsh'], 1)} |",
        f"| World 27-node | {_fmt(score['H_sum_usda'], 1)} | "
        f"{_fmt(score['H_sum_fbsh'], 1)} | "
        f"{_fmt(score['H_sum_fbsh'] / score['H_sum_usda'] if score['H_sum_usda'] else float('nan'))} | — | — |",
        "",
        "China H is comparable after S1 (R6 was 56.4 vs 112.3). Remaining",
        "H/C gaps are EU-27 consumption (USDA ~126 vs FBSH ~84) and other",
        "multi-country C. World 27-node H now matches (~0.99). Psi identical",
        "(USDA) on both objects.",
        f"Laptop `{inv['laptop_data']['path']}` mounted="
        f"{inv['laptop_data']['exists']}. "
        f"Author cleaned FB files: {inv['food_balance_files'] or 'none'}.",
        "",
        "## 2006–08 harvest+AMIS (this window, not the 2003–11 host)",
        "",
        "| | USDA member-sum | FBSH parallel | S1 2003–11 host | author |",
        "|---|---:|---:|---:|---:|",
        f"| hike_2008 | ×{_fmt(score['hike_usda'])} | ×{_fmt(score['hike_fbsh'])} | "
        f"×{S1_HOST_HIKE:g} | ×{AUTHOR_HIKE:g} |",
        f"| moy max/min | {_fmt(score['moy_usda'], 1)}× | {_fmt(score['moy_fbsh'], 1)}× | "
        f"{S1_HOST_MOY:g}× | {AUTHOR_MOY:g}× |",
        f"| 2006 mean USD/t | {_fmt(score['mean_2006_usda'], 1)} | "
        f"{_fmt(score['mean_2006_fbsh'], 1)} | — | — |",
        f"| unconverged | {int(score['unconverged_usda'])}/{int(score['n_solves'])} | "
        f"{int(score['unconverged_fbsh'])}/{int(score['n_solves'])} | 2304 | — |",
        f"| failed | {int(score['failed_usda'])} | {int(score['failed_fbsh'])} | 0 | — |",
        f"| XI* annual | {_fmt(score['XI_world_usda'], 1)} | "
        f"{_fmt(score['XI_world_fbsh'], 1)} | — | — |",
        "",
        f"`wheat_params` αI={score['alpha_i']:g}, ζ={score['zeta_penalty']:g}, "
        f"N_for={int(score['n_for_months'])}. Psi was USDA on both runs.",
        "The 2006–08 last/first columns are **not** item 3 (item 3 is",
        f"undisturbed 2006–11 = {_fmt(S1_HOST_LAST_FIRST, 3)}).",
        "",
        "## Remaining cannot-set (A1 / A7)",
        "",
        "- Author cleaned FB / QCL+TCL rebalance",
        "- Ending stocks from FAO (Psi stayed USDA; 5074 is ΔS)",
        "- FAO-since-2005 LOWESS anomalies; AgrimateEU28+Egypt",
        "- 2015–21 FoodTradeNetwork averages (not used)",
        "",
        f"**Adoption:** not adopted. {verdict['why']}.",
        "",
        "**Next paste: S4.** A7 cannot-set inventory (EU28+Egypt / start-2000",
        "/ cleaned FB). Do not start G1. Do not retune αI / p_sto / xmin.",
        "",
    ]
    path = Path(out_dir) / "s3_fbsh.md"
    path.write_text("\n".join(lines) + "\n")
    return path


def write_s3_dispatch(score: dict, verdict: dict, path: Path | None = None) -> Path:
    """Living S3 writer. Does not clobber a later S-session dispatch."""
    path = Path(path) if path else DISPATCH
    if path.is_file():
        text = path.read_text()
        if "Last completed: S2" not in text and "Last completed: S3" not in text:
            return path
    body = "\n".join([
        "# Gate 0 reproduction dispatch",
        "",
        "Living next-paste. R-science queue exhausted. Template:",
        "`GATE0_NEXT_PROMPTS.md` (S1–S6). Do not walk R8…R12 as science.",
        "",
        "```",
        "Last completed: S3",
        "Window / scenario: 2006–08 harvest+AMIS FBSH vs S1 member-sum USDA",
        f"hike_2008 USDA→FBSH: ×{_fmt(score['hike_usda'])} → ×{_fmt(score['hike_fbsh'])} "
        f"(S1 2003–11 ×{S1_HOST_HIKE:g}; author ×{AUTHOR_HIKE:g})",
        f"moy max/min: {_fmt(score['moy_usda'], 1)}× → {_fmt(score['moy_fbsh'], 1)}× "
        f"(S1 host {S1_HOST_MOY:g}×; author {AUTHOR_MOY:g}×)",
        f"undisturbed last/first: {S1_HOST_LAST_FIRST:g} vs author {AUTHOR_LAST_FIRST:g} (S2; FBSH not scored)",
        f"unconverged / failed: USDA {int(score['unconverged_usda'])}/"
        f"{int(score['n_solves'])} / {int(score['failed_usda'])}; "
        f"FBSH {int(score['unconverged_fbsh'])}/{int(score['n_solves'])} / "
        f"{int(score['failed_fbsh'])}",
        "What you could set / could not set: FBSH H/C re-scored; Psi USDA; 5074 not S; author cleaned FB cannot-set",
        "Next paste: S4",
        "Why: China H ~1.00 vs FBSH after S1; items 1–3 + moy do not justify switch; USDA stays default",
        "Skip: R8-as-science; R11; G1/G2; 2006 pin; Bai 10; L1–L8; FAO ΔS as stocks; FTN 2015–21",
        "```",
    ])
    path.write_text(body + "\n")
    return path


def run_s3_fbsh_score(out_dir: Path | None = None) -> dict[str, Path]:
    """Re-score FBSH vs member-sum USDA. Does not adopt. Does not overwrite R6."""
    out_dir = Path(out_dir) if out_dir else OUT_DEFAULT
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in PROTECTED_THREE_SCENARIO:
        assert (out_dir / name).is_file(), name
    before = {name: (out_dir / name).read_bytes() for name in PROTECTED_THREE_SCENARIO}
    r6_note = (out_dir / "fb_wheatdata.md").read_bytes()
    r6_csv = (out_dir / "score_fb_wheatdata.csv").read_bytes()
    r6_q = (out_dir / "score_fb_wheatdata_quantities.csv").read_bytes()
    params = wheat_params()
    assert params.alpha_i == 3.2
    assert params.zeta_penalty == 0.0
    usda = prepare_wheat(start_year=START_YEAR, end_year=END_YEAR, params=params)
    fbsh = prepare_wheat_fbsh(start_year=START_YEAR, end_year=END_YEAR, params=params)
    assert np.allclose(usda.Psi, fbsh.Psi)
    tab = quantity_table(usda, fbsh)
    score = score_harvest_amis(usda, fbsh, params)
    score["China_H_usda"] = float(usda.H_annual[usda.regions.index("China")])
    score["China_H_fbsh"] = float(fbsh.H_annual[fbsh.regions.index("China")])
    verdict = s3_adoption_verdict(score)
    assert verdict["adopt"] is False
    qpath = out_dir / "score_s3_fbsh_quantities.csv"
    tab.to_csv(qpath, index=False)
    spath = out_dir / "score_s3_fbsh.csv"
    pd.DataFrame([{**score, "adopt": False, "why": verdict["why"]}]).to_csv(
        spath, index=False)
    note = write_s3_fbsh_note(score, tab, verdict, out_dir)
    dispatch = write_s3_dispatch(score, verdict)
    after = {name: (out_dir / name).read_bytes() for name in PROTECTED_THREE_SCENARIO}
    assert before == after, "S3 must not overwrite 2003–11 three-scenario CSVs"
    assert (out_dir / "fb_wheatdata.md").read_bytes() == r6_note
    assert (out_dir / "score_fb_wheatdata.csv").read_bytes() == r6_csv
    assert (out_dir / "score_fb_wheatdata_quantities.csv").read_bytes() == r6_q
    assert wheat_params().alpha_i == 3.2
    assert not any(n.startswith("PARALLEL") for n in usda.notes)
    return {"note": note, "quantities": qpath, "score": spath, "dispatch": dispatch}
