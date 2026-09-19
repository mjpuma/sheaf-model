"""G0-P wheat methods note. Not a retune. Not G1/G2.

Compiles ``diagnostics/gate0_agrimate/methods.md`` from existing
three-scenario and G0-H CSVs. Does not run the host. Does not change
``wheat_params()``. Acceptance of this note as the SHEAF market section
is a human decision; the evidence recorded here does **not** meet the
DEVELOPMENT publication bar.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .params import wheat_params
from .regions import REGION_NAMES
from .validation import OUT_DEFAULT


def _fmt(x, nd: int = 2) -> str:
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "nan"
    return f"{float(x):.{nd}f}"


def publication_bar(out_dir: Path | None = None) -> dict:
    """DEVELOPMENT items 1–5. ``accepted`` is False until a human overrides.

    This function does not unlock G1. Item 3 (undisturbed) and item 5
    (historical performance) fail on the recorded scores.
    """
    out_dir = Path(out_dir) if out_dir else OUT_DEFAULT
    p = wheat_params()
    prices = pd.read_csv(out_dir / "score_prices.csv")
    ha = prices[prices["scenario"] == "harvest_amis"].iloc[0]
    seasonal = pd.read_csv(out_dir / "score_hindcast_seasonal.csv")
    sha = seasonal[seasonal["scenario"] == "harvest_amis"].iloc[0]
    return {
        "n_regions": len(REGION_NAMES),
        "alpha_i": float(p.alpha_i),
        "p_sto_annual": float(p.p_sto_annual),
        "xmin_share": float(p.xmin_share),
        "zeta_penalty": float(p.zeta_penalty),
        "plan_maxiter": int(p.plan_maxiter),
        "item1_source_fidelity": "met_for_retrieved_code",
        "item2_numerical": "feasible_not_stationary",
        "item3_undisturbed": False,
        "item4_reproduction": "independent_not_replication",
        "item5_historical": False,
        "failed_harvest_amis": int(ha["failed"]),
        "unconverged_harvest_amis": int(ha["unconverged"]),
        "hike_2008_host": float(sha["hike_2008_host"]),
        "hike_2008_author": float(sha["hike_2008_author"]),
        "hike_2008_pink": float(sha["hike_2008_pink"]),
        "drift_undisturbed": 1.63,
        "accepted": False,
    }


def _row(tab: pd.DataFrame, scenario: str) -> pd.Series:
    return tab[tab["scenario"] == scenario].iloc[0]


def _qty(tab: pd.DataFrame, scenario: str, field: str) -> pd.Series:
    return tab[(tab["scenario"] == scenario) & (tab["field"] == field)].iloc[0]


def write_methods_note(out_dir: Path | None = None) -> Path:
    out_dir = Path(out_dir) if out_dir else OUT_DEFAULT
    bar = publication_bar(out_dir)
    p = wheat_params()
    prices = pd.read_csv(out_dir / "score_prices.csv")
    seasonal = pd.read_csv(out_dir / "score_hindcast_seasonal.csv")
    qty = pd.read_csv(out_dir / "score_hindcast_quantities.csv")
    ha = _row(prices, "harvest_amis")
    hv = _row(prices, "harvest")
    un = _row(prices, "undisturbed")
    sha = _row(seasonal, "harvest_amis")
    prod = _qty(qty, "harvest_amis", "production")
    stk = _qty(qty, "harvest_amis", "ending_stocks")
    cons = _qty(qty, "harvest_amis", "consumption")
    pulse_path = out_dir / "score_pulse.csv"
    pulse = pd.read_csv(pulse_path) if pulse_path.exists() else None

    lines = [
        "# SHEAF Gate 0 wheat — methods note (G0-P)",
        "",
        "**This is the market section offered for acceptance or rejection.**",
        "It is an independent Agrimate copy (Kuhla, Kubiczek & Otto 2025,",
        "*Ecol. Econ.* 231:108546; ODD §D; wheat §E). It is **not** a",
        "replication of Agrimate Fig. 4. It does **not** implement",
        "cross-crop substitution (G1) or a government restriction game (G2).",
        "",
        f"**Verdict. Not accepted.** DEVELOPMENT items 3 and 5 fail",
        f"(undisturbed last/first **{bar['drift_undisturbed']}** vs author",
        f"1.004; harvest+AMIS 2008 hike ×{_fmt(bar['hike_2008_host'], 2)} vs",
        f"Agrimate ×{_fmt(bar['hike_2008_author'], 2)} vs Pink",
        f"×{_fmt(bar['hike_2008_pink'], 2)}). G1 and G2 stay blocked.",
        "Do not start them from this note. `wheat_params()` stay",
        f"αI={p.alpha_i:g}, p_sto={p.p_sto_annual:g}, xmin={p.xmin_share:g}.",
        "L1–L8 stay rejected. Bai α_foreign=10 is not adopted. The unforced",
        "world price is not pinned to the 2006 mean.",
        "",
        "Numbers are from existing `diagnostics/gate0_agrimate/` CSVs",
        "(spin-up 2003–05, score 2006–11). The three-scenario runner was",
        "not re-run for this note.",
        "",
        "## 1. What we implemented",
        "",
        "Host: `sheaf/agrimate/`. Executable specification: Zenodo 14022004",
        "retrieved 2026-09-16 (**not copied**). Fig. 4 author series:",
        "Zenodo 10688435 `main_output` NetCDF (P7). Paper text and author",
        "code disagree in labelled places (paper 28 regions vs code 27;",
        "Tbl. D.8 αI=3.5 vs code 3.2); the host follows the retrieved wheat",
        "executable, not a guessed blend.",
        "",
        "Lineage is TWIST (Schewe et al. 2017) → Agrimate (Kuhla et al. 2025)",
        "→ this Gate 0 copy. The only planned SHEAF differentiators versus",
        "an Agrimate copy are **later**: G1 substitution and G2 government",
        "games (`GATE0_EXTENSION_PLAN.md`). Disabled G1 must recover this",
        "single-crop run; disabled G2 must recover E.4 AMIS. Those tests",
        "are not this note.",
        "",
        "| piece | source | host |",
        "|---|---|---|",
        f"| regions | Zenodo `AgrimateRegionsWheat` | {len(REGION_NAMES)} names (S1) |",
        "| clock | 24-step year | `STEPS_PER_YEAR` |",
        "| harvest expectation | Eq. D.1 | `expected_harvest` |",
        "| restriction expectation | Eq. D.2 | `expected_restriction` |",
        "| sales | Eq. D.3 | `fulfill_sales`; XI × (1−Δ) |",
        "| supplier plan | D.11–D.21 | fraction map; p_sto; xmin penalty ζ=0 |",
        "| inverse demand | D.7 | world XI* scale; αI=3.2 |",
        "| rivals' XI | D.22 | Jacobi IBR; τ_exp=0.5 |",
        "| purchaser | D.30 + D.30a | nested CES; A_d=1 recovers D.30 |",
        "| consumer | D.35 | εc=0.1 |",
        "| harvest shape | E.27 | author raised-cosine |",
        "| restrictions | Tbl. E.4 / AMIS OECD | prescribed Δ; not a game |",
        "| world price | §5.2 international tx | D.7 × p0; not a calm pin |",
        "| Nash init | §D.5 | not the dynamic baseline |",
        "",
        "Units: quantities million tonnes (MMT); prices a $/t index on D.7.",
        "Process order follows §D.3. Step identities (producer, consumer,",
        "sales, (1−Δ)) hold on the 2006 harvest+AMIS path (P1).",
        "",
        "## 2. Parameters (author defaults, not a fit)",
        "",
        "Zenodo 14022004 `AgrimateParams`. Tbl. D.8 (αI=3.5, τ=0.2) is",
        "`wheat_table_d8_defaults()`, unused. Bai's fitted α_foreign=10 is",
        "an OAT alternative (P6), not ours.",
        "",
        "| knob | value | note |",
        "|---|---:|---|",
        f"| αI | {p.alpha_i:g} | code, not Tbl. D.8 3.5 |",
        f"| α_nash | {p.alpha_nash:g} | §D.5 init |",
        f"| σ | {p.sigma_ces:g} | origin CES |",
        f"| εc | {p.eps_c:g} | D.35 |",
        f"| p_sto | {p.p_sto_annual:g} / Nyear | Tbl. D.8 storage cost |",
        f"| xmin | {p.xmin_share:g} | even-spread penalty; ζ={p.zeta_penalty:g} on |",
        f"| N_for | {p.n_for_months:g} months | D.1; Fig. 4 used 6 |",
        f"| τ | {p.tau_storage:g} yr | F.1 / code |",
        "| β, τ_P | 0.05, 0.2 yr | unused on wheat path (S3) |",
        f"| plan_maxiter | {p.plan_maxiter:g} | left at 40 (N5 / P5) |",
        "",
        "## 3. Data vintage",
        "",
        "- **Baseline quantities:** USDA PSD 2007–09 mean, not FAOSTAT Food",
        "  Balances E.1 (A1). P10: `data/faostat_network/` is E0 trade only;",
        "  author `wheat_food_balance_fao.csv` is not shipped; USDA stays",
        "  the default (`faostat_fb.md`).",
        "- **Trade pattern:** FAOSTAT E0 2006–07, rescaled to USDA exports (A2).",
        "- **Anomalies:** USDA PSD, LOWESS residual, applied to the 2007–09",
        "  mean harvest.",
        "- **Restrictions:** OECD/AMIS aggregated wheat measures,",
        "  `PolicyMeasure_Name` / `CommodityClass_Name` (E.4). Bans 0.95,",
        "  taxes 0.50. 491 region-steps bind on 2003–11 wheat.",
        "- **Harvest calendars:** `data/crop_calendars/wheat_harvest_months.csv`.",
        "- **Pink Sheet:** scoring only. Not a calibration target.",
        "- **Window:** simulate 2003–11; spin-up 2003–05; score 2006–11.",
        "",
        "A_d is not E.30 (A3; F.1 Egypt 0.17 unused because Egypt is inside",
        "Northern Africa). A_c uses income-group proxies (A4). Multi-country",
        "PSD nodes use `groupby.mean()` not sum (A8): China 0.50× and Eastern",
        "Africa 0.10× mapped PSD production; single-row exporters match.",
        "Labelled, not fixed — summing would rewrite the 2003–11 host.",
        "",
        "## 4. Three scenarios (G0-U)",
        "",
        "Same design as Agrimate’s published wheat experiments.",
        "",
        "| name | harvest anomalies | export restrictions |",
        "|---|---|---|",
        "| `undisturbed` | off | off |",
        "| `harvest` | USDA PSD, on | off |",
        "| `harvest_amis` | on | AMIS / Tbl. E.4 |",
        "",
        "Command: `PYTHONPATH=. python scripts/run_agrimate_validation.py`.",
        "World price is the international transaction price already in",
        "`model.py` (D.7 × p0). Not a calm pin. Harvest vs harvest+AMIS",
        "differ when AMIS binds (they were identical before the OECD column",
        "fix).",
        "",
        "## 5. Numerical representation",
        "",
        "N1 fraction parameterization of D.11–D.21 (equivalent feasible set).",
        "N2 rolling forthcoming-year plan. N3 Jacobi IBR inside the step.",
        "N4 D.7 scaled by world XI*. N5: feasible L-BFGS-B with",
        f"`success=False` — harvest+AMIS unconverged",
        f"**{int(ha['unconverged'])}/5832** (maxiter 1033 + ABNORMAL 710).",
        f"Failed {int(ha['failed'])}; fallback {int(ha['fallback'])}; residual 0.",
        "`plan_maxiter=40` kept: 200 vs 400 iters disagree by as much as",
        "40 vs 400, so there is no unique stationary point to adopt",
        "(`solver.md`). Inverse-demand offer floor binds 0 times on the",
        "reference path.",
        "",
        "B1 (P2): international delivery now follows E.1 T* to importers.",
        "Pre-fix, lagged XI was credited to the exporter as consumer inflow.",
        "That ballooned exporter stocks; it did **not** cause the 1.63",
        "undisturbed drift (p_w is on XI, not on who receives it).",
        "",
        "## 6. What this market section does not do",
        "",
        "- Restore L1–L8 (fill-target 0.70, calm pin, scarcity blend,",
        "  ask_rival, prescribed buffer, scarcity-ratio floor, residual ν,",
        "  AR(1) smoother).",
        "- Pin the unforced world price to the 2006 Pink Sheet mean.",
        "- Retune αI, p_sto, xmin, or λ to Pink Sheet or to Bai α_foreign=10.",
        "- Split-calibrate 2008 vs 2022.",
        "- Treat maize or rice as an acceptance target.",
        "- Implement G1 (`sheaf/dynamic_coupled.py`) or G2",
        "  (`sheaf/dynamic_policy.py`). Leftover files on the legacy spine",
        "  are not this host.",
        "- Treat the P11 prescribed-Δ grid as Gate 2. Gate 2 would let",
        "  governments **choose** Δ. This host **prescribes** it.",
        "",
        "## 7. Hindcast versus Agrimate Fig. 4 and Pink Sheet",
        "",
        "Pass rule: items 1–3 before judging item 5. Item 1 is met for",
        "retrieved code with labelled S3/S4/A1–A8/N5. Item 2 is feasible",
        "but not first-order stationary. Item 3 fails. Item 5 is reported",
        "as an explicit sourced shortfall (`hindcast.md`, `fig4.md`).",
        "",
        "### Quiet-year level and 2008 hike",
        "",
        "| series | 2006 mean | 2008 hike | crisis peak |",
        "|---|---:|---:|---|",
        f"| host harvest+AMIS | ${_fmt(sha['mean_2006_host_usd'], 1)}/t | "
        f"×{_fmt(sha['hike_2008_host'], 2)} | {sha['crisis_peak_host']} |",
        f"| host harvest-only | ${_fmt(hv['mean_2006_model'], 1)}/t | "
        f"×{_fmt(hv['hike_2008_model'], 2)} | — |",
        f"| host undisturbed | ${_fmt(un['mean_2006_model'], 1)}/t | "
        f"×{_fmt(un['hike_2008_model'], 2)} | — |",
        f"| Pink Sheet | ${_fmt(sha['mean_2006_pink_usd'], 1)}/t | "
        f"×{_fmt(sha['hike_2008_pink'], 2)} | {sha['crisis_peak_pink']} |",
        f"| Agrimate Fig. 4d harvest+AMIS | index {_fmt(sha['mean_2006_author_index'], 3)} | "
        f"×{_fmt(sha['hike_2008_author'], 2)} | {sha['crisis_peak_author']} |",
        "",
        f"Quiet-year host is ~31% of Pink (${_fmt(sha['mean_2006_host_usd'], 1)} vs",
        f"${_fmt(sha['mean_2006_pink_usd'], 1)}) and ~0.31 vs author ~1.18 on",
        "the index. Host hike overshoots Pink **and** Agrimate. Agrimate is",
        "the closer of the two models to Pink on this metric. Peak timing is",
        f"wrong: host **{sha['crisis_peak_host']}** (harvest-calendar spike);",
        f"Pink **{sha['crisis_peak_pink']}**; author **{sha['crisis_peak_author']}**.",
        "Bai αI=10 is the wrong direction (P6 short-window hike ×2.31 → ×3.58,",
        "pidx_max 473). Not adopted. Do not pin 2006 to close the level gap.",
        "",
        "### Path, not only correlation",
        "",
        f"Harvest+AMIS corr vs Pink is **{_fmt(ha['corr'], 3)}** (negative).",
        f"Month-of-year max/min is **{_fmt(sha['moy_maxmin_host'], 1)}×** vs Pink",
        f"**{_fmt(sha['moy_maxmin_pink'], 2)}×** vs Agrimate Fig. 4d",
        f"**{_fmt(sha['moy_maxmin_author'], 2)}×**. The host shares Agrimate's",
        f"northern-harvest calendar (moy corr vs author {_fmt(sha['moy_corr_vs_author'], 2)})",
        f"and inverts Pink (moy corr {_fmt(sha['moy_corr_vs_pink'], 2)}).",
        f"September 2007: host **${_fmt(sha['sep2007_host_usd'], 1)}/t** vs Pink",
        f"**${_fmt(sha['sep2007_pink_usd'], 0)}/t**. Correlation alone would hide",
        "this. Figure: `figures/fig6_hindcast_seasonal.png`.",
        "",
        "### Undisturbed (item 3)",
        "",
        "Seasonal *shape* repeats (year-to-year corr ≈ 0.98). Annual-mean",
        "world-price ratio 2011/2006 is **1.63**. Author Fig. 4 baseline on",
        "the same window is **1.004**. Remaining candidate: non-periodic",
        "xd/xi split under constant H (`undisturbed.md`). Not a price pin.",
        "",
        "### Production, stocks, consumption",
        "",
        f"Harvest+AMIS production vs USDA world: corr **{_fmt(prod['corr_level'], 3)}**,",
        f"level {_fmt(prod['mean_host'], 1)} vs {_fmt(prod['mean_usda'], 1)} MMT",
        f"(ratio {_fmt(prod['level_ratio'], 3)}). Ending stocks",
        f"**{_fmt(stk['level_ratio'], 2)}×** USDA after B1 (not the pre-P2 3×",
        f"echo). Consumption corr {_fmt(cons['corr_level'], 3)}; level ratio",
        f"{_fmt(cons['level_ratio'], 3)}. Vs Agrimate Fig. 4, production corr",
        "is 0.986 at different levels (USDA vs FAO; region lists differ).",
        "Do not fit xmin or p_sto to the stock gap (`regional.md`).",
        "",
        "### Harvest-only vs harvest+AMIS",
        "",
        "Production is identical by construction. AMIS wheat Δ binds 491",
        "region-steps (Argentina, China, India, Kazakhstan, Russia, Ukraine,",
        "Northern Africa; max 0.95). The 2007 spike is harvest-driven; AMIS",
        "adds a May 2008 spike on top of an already-too-large 2007 harvest",
        "spike. Ukraine 2007 exports 15.0 → 6.0 MMT with AMIS; consumption",
        "1.93 → 10.3 MMT. E.4 does what it says on the exporter. It does",
        "not repair world-price path or level.",
        "",
        "Fig. 4 NetCDF is a **different experiment** (A7): AgrimateEU28+Egypt,",
        "FAO anomalies, α_foreign=3.5, ζ=1, N_for=6, git `old-demand-dynamics`.",
        "Labelling that mismatch does not make ×4.54 a success.",
        "",
        "## 8. Prescribed-Δ pulse (P11, not G2)",
        "",
        "Eight 2008 harvest-anomaly runs versus harvest-only: Ukraine and",
        "Russia × {0.5, 1.0} × {6, 12} months (`pulse.md`). AMIS diary off;",
        "`restriction_pulse` overlays one synthetic exporter. Not a",
        "government best-response. Not Bai's 36-run 2020 grid.",
    ]
    if pulse is not None:
        ukr = pulse[pulse["label"] == "Ukraine_1_12m"]
        rus = pulse[pulse["label"] == "Russia_1_12m"]
        tax = pulse[pulse["label"] == "Ukraine_0.5_12m"]
        if not ukr.empty and not rus.empty:
            lines += [
                "",
                "Slice is **clean**: failed=0, production identical, Δ on one",
                "exporter. 12-month Δ=1.0 zeros Ukraine and Russia XI",
                f"({_fmt(float(ukr.iloc[0]['exports_vs_harvest']), 2)}× / "
                f"{_fmt(float(rus.iloc[0]['exports_vs_harvest']), 2)}×).",
                "12-month Δ=0.5 halves it"
                + (f" ({_fmt(float(tax.iloc[0]['exports_vs_harvest']), 2)}×)." if not tax.empty else "."),
                "A January–June 6-month pulse misses NH harvest (Jul–Sep).",
                "Mean world price stays 0.99–1.01× harvest-only. D.3 binds;",
                "it is not a Pink-Sheet lever and not Gate 2.",
            ]
    lines += [
        "",
        "## 9. Labelled departures",
        "",
        "Full register: `diagnostics/GATE0_DEPARTURES.md`. Compact:",
        "",
        "| id | what | status |",
        "|---|---|---|",
        "| L1–L8 | legacy ask/scarcity devices | **rejected** |",
        "| A1 | USDA PSD not FAOSTAT FB | labelled; P10 left |",
        "| A2 | E0 shares rescaled to USDA XI | labelled |",
        "| A3 | A_d not E.30 | labelled |",
        "| A7 | Fig. 4 executable ≠ 14022004 wheat | labelled; not a retune |",
        "| A8 | `groupby.mean()` vs PSD sum | labelled, not fixed |",
        "| N1–N4 | fraction map, rolling year, Jacobi, XI* scale | numerical, not economics |",
        "| N5 | unconverged L-BFGS-B 1743/5832 | counted; maxiter 40 kept |",
        "| S1 | 27 not 28 | follows executable |",
        "| S2 | αI=3.2 not D.8 3.5 | follows executable |",
        "| S3 | β/τ_P unused | matches wheat `two_markets` path |",
        "| S4 | D.30a formula wired; x1 still from plan | formula H; x1 gap D |",
        "| B1 | T* delivery, not own-XI echo | coding fix |",
        "| E1/E2 | G1 substitution / G2 game | **not implemented** |",
        "",
        "## 10. Limits",
        "",
        "1. Undisturbed annual-mean drift 1.63 is unexplained after B1.",
        "2. ~30% of harvest+AMIS plans are unconverged feasible iterates (N5).",
        "3. Off-season world price collapses (~18× moy max/min vs Agrimate 1.45×).",
        "4. Quiet-year level is not on Agrimate's or Pink's scale.",
        "5. Baseline quantities are USDA, not FAOSTAT FB (A1); A8 mean-of-members",
        "   rescales China and Eastern Africa.",
        "6. Physical inflow remains T* + domestic; author two-market x1=demand",
        "   is labelled, not copied (S4). εc and σ are silent on world price",
        "   in the P6 OAT, as expected under that gap.",
        "7. This is an independent implementation, not a bit-reproduction of",
        "   Fig. 4 (different region list, FAO vs USDA, αI 3.5 vs 3.2, ζ, N_for).",
        "",
        "Open G0-H questions that are **not** retunes of this run: FAO vs USDA",
        "on a window that actually has FB arrays; whether one parameter set",
        "can fit 2008 and 2022 (Bai). Neither is a reason to restore L1–L8.",
        "",
        "## 11. Verdict (accept or reject)",
        "",
        "Offer this note as the SHEAF wheat market section.",
        "",
        "| DEVELOPMENT item | result |",
        "|---|---|",
        "| 1. Source fidelity | Met for retrieved 14022004 code, with labelled gaps |",
        "| 2. Numerical reliability | Feasible (failed=0, residual=0); not first-order stationary (N5) |",
        "| 3. Undisturbed dynamics | **Fail** — last/first 1.63 vs author 1.004 |",
        "| 4. Reference reproduction | Independent implementation, **not** a replication |",
        "| 5. Historical performance | **Fail** — level, hike, path vs Agrimate Fig. 4 and Pink |",
        "| 6. Controlled experiments | Three scenarios + P11 pulse run; AMIS moves the exporter |",
        "",
        "**Recommend reject** as the publishable SHEAF market section.",
        "Items 1–3 do not all hold; item 5 is a sourced shortfall. G1 and",
        "G2 stay blocked until a later G0-P acceptance. Do not start G1 in",
        "the same session as this note. `wheat_params()` unchanged.",
        "",
        "## Files",
        "",
        "- this note (`methods.md`)",
        "- `hindcast.md`, `fig4.md`, `regional.md`, `faostat_fb.md`, `pulse.md`,",
        "  `undisturbed.md`, `solver.md`, `validation.md`",
        "- `GATE0_DEPARTURES.md`, `GATE0_SPEC_MATRIX.md`, `GATE0_CONTRACT.md`",
        "- `GATE0_REDTEAM.md`, `GATE0_DATA.md` — post-P12 inventory; not a retune",
        "",
        "G1/G2 remain the blocked pair in `GATE0_EXTENSION_PLAN.md`.",
        "",
    ]
    path = Path(out_dir) / "methods.md"
    path.write_text("\n".join(lines) + "\n")
    return path


def run_methods_note(out_dir: Path | None = None) -> dict[str, Path]:
    out_dir = Path(out_dir) if out_dir else OUT_DEFAULT
    note = write_methods_note(out_dir)
    return {"note": note}
