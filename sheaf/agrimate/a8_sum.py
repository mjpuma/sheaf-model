"""R7: labelled A8 mean-vs-sum sensitivity. Does not rewrite the host.

``prepare_wheat`` uses ``groupby(region).mean()`` on USDA PSD country-year
rows (2007–09). ``psd_regional_annual()`` sums members within a year.
This module reports what China / Eastern Africa H, C, and **USDA ending
stocks** become if members are summed. It does not change
``prepare_wheat``, does not fit xmin/p_sto, and does not treat FAOSTAT
FBSH Stock Variation (ΔS) as a stock level.
"""
from __future__ import annotations

from pathlib import Path

import math

import pandas as pd

from sheaf.calendar24 import STEPS_PER_YEAR
from sheaf.data_usda import load_psd_country

from .fig4_config import PROTECTED_THREE_SCENARIO
from .params import wheat_params
from .validation import OUT_DEFAULT
from .wheat_data import _psd_to_region, prepare_wheat

ROOT = Path(__file__).resolve().parents[2]
DISPATCH = ROOT / "diagnostics" / "GATE0_REPRO_DISPATCH.md"
YEAR0, YEAR1 = 2007, 2009
FOCUS = ("USA", "EU-27", "China", "Eastern Africa")
COLS = ("production", "consumption", "ending_stocks")


def _fmt(x, nd: int = 2) -> str:
    if x is None or (isinstance(x, float) and not math.isfinite(x)):
        return "nan"
    return f"{float(x):.{nd}f}"


def a8_mean_vs_sum_table(year0: int = YEAR0, year1: int = YEAR1) -> pd.DataFrame:
    """USDA PSD 2007–09: pooled mean of country-year rows vs year-sum then mean.

    Stocks are USDA ``ending_stocks`` (MMT). FAO ΔS is not used.
    """
    params = wheat_params()
    data = prepare_wheat(start_year=year0, end_year=year1, params=params)
    raw = load_psd_country("wheat").copy()
    raw["region"] = [
        _psd_to_region(c, n) for c, n in zip(raw["country_code"], raw["country_psd"])
    ]
    base = raw[(raw["year"] >= year0) & (raw["year"] <= year1)].dropna(subset=["region"])
    rows = []
    for r in FOCUS:
        sub = base[base["region"] == r]
        names = sorted(sub["country_psd"].dropna().unique().tolist())
        n = len(names)
        mean = {c: float(sub[c].mean()) if len(sub) else float("nan") for c in COLS}
        if len(sub):
            byy = sub.groupby("year")[list(COLS)].sum()
            summed = {c: float(byy[c].mean()) for c in COLS}
        else:
            summed = {c: float("nan") for c in COLS}
        i = data.regions.index(r)
        host_h = float(data.H_annual[i])
        host_c = float(data.C_star[i] * STEPS_PER_YEAR)
        host_s = float(data.Psi[i] * data.C_star[i] * STEPS_PER_YEAR)
        rows.append({
            "region": r,
            "n_psd_members": n,
            "psd_members": "|".join(names),
            "H_mean": mean["production"],
            "H_sum": summed["production"],
            "H_mean_over_sum": (
                mean["production"] / summed["production"]
                if summed["production"] else float("nan")
            ),
            "C_mean": mean["consumption"],
            "C_sum": summed["consumption"],
            "C_mean_over_sum": (
                mean["consumption"] / summed["consumption"]
                if summed["consumption"] else float("nan")
            ),
            "S_mean": mean["ending_stocks"],
            "S_sum": summed["ending_stocks"],
            "S_mean_over_sum": (
                mean["ending_stocks"] / summed["ending_stocks"]
                if summed["ending_stocks"] else float("nan")
            ),
            "host_H": host_h,
            "host_C_after_Tstar": host_c,
            "host_S_usda": host_s,
            "stock_source": "USDA PSD ending_stocks",
            "construction": (
                "single_psd_row" if n == 1 else
                "groupby_mean_of_members" if n > 1 else
                "unmapped"
            ),
            "alpha_i": float(params.alpha_i),
            "p_sto_annual": float(params.p_sto_annual),
            "xmin_share": float(params.xmin_share),
        })
    return pd.DataFrame(rows)


def write_a8_csv(tab: pd.DataFrame, out_dir: Path) -> Path:
    path = out_dir / "score_a8_sum.csv"
    tab.to_csv(path, index=False)
    return path


def _row(tab: pd.DataFrame, region: str) -> pd.Series:
    return tab[tab["region"] == region].iloc[0]


def write_a8_note(tab: pd.DataFrame, out_dir: Path | None = None) -> Path:
    out_dir = Path(out_dir) if out_dir else OUT_DEFAULT
    out_dir.mkdir(parents=True, exist_ok=True)
    usa, eu, ch, ea = (_row(tab, r) for r in FOCUS)
    lines = [
        "# R7 — A8 mean-vs-sum sensitivity (2007–09 USDA only)",
        "",
        "**Host unchanged. Not adopted.** `prepare_wheat` still uses",
        "`groupby(region).mean()` on USDA PSD country-year rows.",
        "`wheat_params()` stay αI=3.2, p_sto=0.1, xmin=0.2, ζ=0, N_for=3.",
        "No xmin/p_sto fit. L1–L8 stay rejected. Bai α_foreign=10 not",
        "adopted. G1/G2 stay blocked. 2003–11 three-scenario CSVs are",
        "not rewritten.",
        "",
        "**Stocks are USDA PSD `ending_stocks`.** FAOSTAT FBSH Stock",
        "Variation (element 5074) is ΔS, a food-balance residual, not a",
        "stock level. R6 copied USDA Psi onto the FBSH parallel for that",
        "reason. This table does not use FAO ΔS.",
        "",
        "## Verification protocol",
        "",
        "1. **Claim.** A8: multi-country PSD baseline uses mean, not sum;",
        "   China 0.50× and Eastern Africa 0.10× on harvest.",
        "2. **Implementation.** `prepare_wheat` (`wheat_data.py`) ",
        "   `groupby(\"region\").mean()`; `psd_regional_annual()` sums.",
        "3. **Match.** They match. This note reports C and S on the same",
        "   construction, still USDA.",
        "4. **Counterexample.** China 2007–09 H mean "
        f"{_fmt(ch['H_mean'], 1)} vs sum {_fmt(ch['H_sum'], 1)} "
        f"(ratio {_fmt(ch['H_mean_over_sum'], 2)}); EA "
        f"{_fmt(ea['H_mean'], 2)} vs {_fmt(ea['H_sum'], 2)} "
        f"(ratio {_fmt(ea['H_mean_over_sum'], 2)}). USA is 1.00.",
        "5. **Correctness of not rewriting.** Summing would rescale China",
        "   H/C/S ×2 and Eastern Africa ×10 and rewrite the 2003–11 host.",
        "   That is a data-adapter change, not a parameter fit. Host C",
        "   after T* is already not the PSD mean (inflows).",
        "6. **Change.** None to economics. Mean stays the default.",
        "",
        "## 2007–09 USDA PSD (MMT)",
        "",
        "Mean = pooled country-year rows (what `prepare_wheat` uses for",
        "H and for S_ann). Sum = members summed within each year, then",
        "averaged over 2007–09 (what `psd_regional_annual()` uses).",
        "",
        "| region | members | H mean | H sum | C mean | C sum | S mean | S sum | mean/sum |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
        f"| USA | 1 ({usa['psd_members']}) | {_fmt(usa['H_mean'], 1)} | "
        f"{_fmt(usa['H_sum'], 1)} | {_fmt(usa['C_mean'], 1)} | {_fmt(usa['C_sum'], 1)} | "
        f"{_fmt(usa['S_mean'], 1)} | {_fmt(usa['S_sum'], 1)} | "
        f"{_fmt(usa['H_mean_over_sum'], 2)} |",
        f"| EU-27 | 1 ({eu['psd_members']}) | {_fmt(eu['H_mean'], 1)} | "
        f"{_fmt(eu['H_sum'], 1)} | {_fmt(eu['C_mean'], 1)} | {_fmt(eu['C_sum'], 1)} | "
        f"{_fmt(eu['S_mean'], 1)} | {_fmt(eu['S_sum'], 1)} | "
        f"{_fmt(eu['H_mean_over_sum'], 2)} |",
        f"| China | {int(ch['n_psd_members'])} ({ch['psd_members']}) | "
        f"{_fmt(ch['H_mean'], 1)} | {_fmt(ch['H_sum'], 1)} | "
        f"{_fmt(ch['C_mean'], 1)} | {_fmt(ch['C_sum'], 1)} | "
        f"{_fmt(ch['S_mean'], 1)} | {_fmt(ch['S_sum'], 1)} | "
        f"{_fmt(ch['H_mean_over_sum'], 2)} |",
        f"| Eastern Africa | {int(ea['n_psd_members'])} countries | "
        f"{_fmt(ea['H_mean'], 2)} | {_fmt(ea['H_sum'], 2)} | "
        f"{_fmt(ea['C_mean'], 2)} | {_fmt(ea['C_sum'], 2)} | "
        f"{_fmt(ea['S_mean'], 3)} | {_fmt(ea['S_sum'], 2)} | "
        f"{_fmt(ea['H_mean_over_sum'], 2)} |",
        "",
        "If members are **summed**, China H/C/S become "
        f"{_fmt(ch['H_sum'], 1)} / {_fmt(ch['C_sum'], 1)} / {_fmt(ch['S_sum'], 1)} "
        f"(now {_fmt(ch['H_mean'], 1)} / {_fmt(ch['C_mean'], 1)} / "
        f"{_fmt(ch['S_mean'], 1)}). Eastern Africa becomes "
        f"{_fmt(ea['H_sum'], 2)} / {_fmt(ea['C_sum'], 2)} / {_fmt(ea['S_sum'], 2)} "
        f"(now {_fmt(ea['H_mean'], 2)} / {_fmt(ea['C_mean'], 2)} / "
        f"{_fmt(ea['S_mean'], 3)}). Hong Kong wheat production and stocks",
        "are ~0, so China mean is ½ of China mainland. Eastern Africa is",
        f"the mean of {int(ea['n_psd_members'])} mapped PSD rows",
        f"({ea['psd_members']}).",
        "",
        "## Host after T* (unchanged)",
        "",
        "`prepare_wheat` H follows the **mean** for these nodes. S_ann is",
        "the mean of USDA ending stocks; host S = Ψ C* = S_ann. C* is",
        "rebuilt from T* inflows, so host C is not the PSD mean.",
        "",
        "| region | host H | PSD H mean | host C (T*) | PSD C mean | host S | PSD S mean |",
        "|---|---:|---:|---:|---:|---:|---:|",
        f"| China | {_fmt(ch['host_H'], 1)} | {_fmt(ch['H_mean'], 1)} | "
        f"{_fmt(ch['host_C_after_Tstar'], 1)} | {_fmt(ch['C_mean'], 1)} | "
        f"{_fmt(ch['host_S_usda'], 1)} | {_fmt(ch['S_mean'], 1)} |",
        f"| Eastern Africa | {_fmt(ea['host_H'], 2)} | {_fmt(ea['H_mean'], 2)} | "
        f"{_fmt(ea['host_C_after_Tstar'], 2)} | {_fmt(ea['C_mean'], 2)} | "
        f"{_fmt(ea['host_S_usda'], 3)} | {_fmt(ea['S_mean'], 3)} |",
        f"| USA | {_fmt(usa['host_H'], 1)} | {_fmt(usa['H_mean'], 1)} | "
        f"{_fmt(usa['host_C_after_Tstar'], 1)} | {_fmt(usa['C_mean'], 1)} | "
        f"{_fmt(usa['host_S_usda'], 1)} | {_fmt(usa['S_mean'], 1)} |",
        "",
        "Eastern Africa host C is already 3.61 vs PSD mean 0.66 because",
        "T* inflows fill the node. Summing members would still ×10 H and",
        "S. That is why this stays a labelled sensitivity, not a silent",
        "host rewrite.",
        "",
        f"`wheat_params` αI={float(usa['alpha_i']):g}, "
        f"p_sto={float(usa['p_sto_annual']):g}, "
        f"xmin={float(usa['xmin_share']):g}.",
        "",
        "**Next paste: R8.** Honest Fig. 4 score tests. R7 does not unlock",
        "G1. Do not rewrite the 2003–11 host. Do not retune αI.",
        "",
    ]
    path = out_dir / "a8_sum.md"
    path.write_text("\n".join(lines) + "\n")
    return path


def write_r7_dispatch(tab: pd.DataFrame, path: Path | None = None) -> Path:
    """Historical R7 writer. Does not clobber a moved living dispatch."""
    path = Path(path) if path else DISPATCH
    if path.is_file() and "Last completed: R7" not in path.read_text():
        return path
    ch, ea = _row(tab, "China"), _row(tab, "Eastern Africa")
    why = (
        f"A8 labelled; China H {_fmt(ch['H_mean'], 1)}→{_fmt(ch['H_sum'], 1)}, "
        f"S {_fmt(ch['S_mean'], 1)}→{_fmt(ch['S_sum'], 1)}; EA H "
        f"{_fmt(ea['H_mean'], 2)}→{_fmt(ea['H_sum'], 2)}; USDA ending_stocks "
        "only (not FAO ΔS); host unchanged"
    )
    body = "\n".join([
        "# Gate 0 reproduction dispatch",
        "",
        "Living next-paste. Rewrite after every R-session from **that run’s",
        "numbers**. Do not walk R3…R12 in order. Template:",
        "`GATE0_REPRO_PROMPTS.md` (Adaptive rule).",
        "",
        "```",
        "Last completed: R7",
        "Window / scenario: 2007–09 USDA A8 mean vs sum (China/EA H,C,S)",
        "hike_2008 (default → knobs → author): ×2.31 → ×2.22 → ×1.62",
        "moy max/min: 26.8× → 13.3× → 1.51×",
        "undisturbed last/first: default 1.630 → qoth_freeze 1.019 → author 1.004",
        "unconverged / failed: host not re-run",
        "What you could set / could not set: mean vs sum table only; "
        "FAO ΔS is not stocks; 2003–11 host not rewritten",
        "Next paste: R8",
        f"Why: {why}",
        "Skip: R11; G1/G2; do not rewrite host; do not retune αI/xmin/p_sto; "
        "do not adopt FBSH",
        "```",
        "",
    ])
    path.write_text(body)
    return path


def run_a8_sum_score(out_dir: Path | None = None) -> dict[str, Path]:
    out_dir = Path(out_dir) if out_dir else OUT_DEFAULT
    out_dir.mkdir(parents=True, exist_ok=True)
    assert wheat_params().alpha_i == 3.2
    tab = a8_mean_vs_sum_table()
    csv = write_a8_csv(tab, out_dir)
    note = write_a8_note(tab, out_dir)
    # Living dispatch moved off R7 (S-queue). Do not rewrite it.
    for name in PROTECTED_THREE_SCENARIO:
        assert (out_dir / name).is_file(), name
    assert wheat_params().alpha_i == 3.2
    assert wheat_params().p_sto_annual == 0.1
    assert wheat_params().xmin_share == 0.2
    return {"note": note, "csv": csv}
