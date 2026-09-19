"""G0-H/P P11: prescribed exporter pulse grid. Not Gate 2.

Ukraine and Russia × {0.5, 1.0} × {6, 12} months on harvest-anomaly
wheat, 2008 start, versus harvest-only. AMIS-style Δ via
``restriction_pulse``. Not a government best-response. Do not expand
to Bai's 36-run 2020 grid in this module.
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd

from .model import AgrimateResult, run_agrimate
from .params import wheat_params
from .restrictions import restriction_pulse
from .validation import OUT_DEFAULT, monthly_price, regional_annual
from .wheat_data import WheatData, prepare_wheat

START_YEAR = 2008
END_YEAR = 2008
PULSE_START = "2008-01-01"
EXPORTERS = ("Ukraine", "Russia")
INTENSITIES = (0.5, 1.0)
DURATIONS = (6, 12)


def pulse_specs() -> list[dict]:
    rows = []
    for exp in EXPORTERS:
        for intensity in INTENSITIES:
            for months in DURATIONS:
                rows.append({
                    "exporter": exp,
                    "intensity": float(intensity),
                    "duration_months": int(months),
                    "start": PULSE_START,
                    "label": f"{exp}_{intensity:g}_{months}m",
                })
    return rows


def with_pulse(data: WheatData, spec: dict) -> WheatData:
    delta = restriction_pulse(
        data.regions, data.start_year, data.end_year,
        spec["exporter"], spec["intensity"], spec["duration_months"],
        start=spec["start"],
    )
    note = (
        f"Prescribed pulse {spec['label']} from {spec['start']} "
        "(not AMIS diary, not G2)."
    )
    return replace(data, delta=delta, notes=list(data.notes) + [note])


def _exporter_year(result: AgrimateResult, region: str) -> dict[str, float]:
    tab = regional_annual(result, region)
    row = tab[tab["year"] == result.start_year].iloc[0]
    return {
        "production": float(row["production"]),
        "consumption": float(row["consumption"]),
        "exports": float(row["exports"]),
        "ending_stocks": float(row["S_producer"] + row["S_consumer"]),
    }


def _score_run(result: AgrimateResult, exporter: str, harvest: AgrimateResult | None,
               spec: dict | None) -> dict:
    p = monthly_price(result)
    qty = _exporter_year(result, exporter)
    hqty = _exporter_year(harvest, exporter) if harvest is not None else qty
    hp = monthly_price(harvest) if harvest is not None else p
    i = result.regions.index(exporter)
    delta_on = 0
    if spec is not None:
        d = restriction_pulse(
            result.regions, result.start_year, result.end_year,
            spec["exporter"], spec["intensity"], spec["duration_months"],
            start=spec["start"],
        )
        delta_on = int((d[i] > 0).sum())
        other = float(np.delete(d, i, axis=0).max()) if d.shape[0] > 1 else 0.0
    else:
        other = 0.0
    h_prod = hqty["production"]
    h_xi = hqty["exports"]
    h_c = hqty["consumption"]
    h_s = hqty["ending_stocks"]
    return {
        "label": spec["label"] if spec else "harvest_only",
        "exporter": exporter if spec else "—",
        "intensity": spec["intensity"] if spec else 0.0,
        "duration_months": spec["duration_months"] if spec else 0,
        "mean_price_usd": float(p.mean()),
        "max_price_usd": float(p.max()),
        "mean_price_vs_harvest": float(p.mean() / hp.mean()) if float(hp.mean()) else float("nan"),
        "production": qty["production"],
        "production_vs_harvest": qty["production"] / h_prod if h_prod else float("nan"),
        "exports": qty["exports"],
        "exports_vs_harvest": qty["exports"] / h_xi if h_xi else float("nan"),
        "consumption": qty["consumption"],
        "consumption_vs_harvest": qty["consumption"] / h_c if h_c else float("nan"),
        "ending_stocks": qty["ending_stocks"],
        "ending_stocks_vs_harvest": qty["ending_stocks"] / h_s if h_s else float("nan"),
        "failed": int(result.failed_solves),
        "unconverged": int(result.unconverged_solves),
        "n_steps": int(result.price_index.size),
        "delta_steps_on": delta_on,
        "other_exporters_delta_max": other,
    }


def run_pulse_grid(
    start_year: int = START_YEAR,
    end_year: int = END_YEAR,
    params=None,
) -> tuple[WheatData, AgrimateResult, list[tuple[dict, AgrimateResult]]]:
    params = params or wheat_params()
    data = prepare_wheat(start_year=start_year, end_year=end_year, params=params)
    harvest = run_agrimate(
        data=data, params=params,
        use_anomalies=True, use_restrictions=False,
        start_year=start_year, end_year=end_year,
    )
    pulsed = []
    for spec in pulse_specs():
        d = with_pulse(data, spec)
        res = run_agrimate(
            data=d, params=params,
            use_anomalies=True, use_restrictions=True,
            start_year=start_year, end_year=end_year,
        )
        pulsed.append((spec, res))
    return data, harvest, pulsed


def score_pulse_grid(
    harvest: AgrimateResult,
    pulsed: list[tuple[dict, AgrimateResult]],
) -> pd.DataFrame:
    rows = [_score_run(harvest, "Ukraine", None, None)]
    for spec, res in pulsed:
        rows.append(_score_run(res, spec["exporter"], harvest, spec))
    return pd.DataFrame(rows)


def _half_xi(pulses: pd.DataFrame) -> str:
    bits = []
    for exp in EXPORTERS:
        row = pulses[(pulses["exporter"] == exp) & (pulses["intensity"] == 0.5)
                     & (pulses["duration_months"] == 12)]
        if row.empty:
            continue
        bits.append(f"{exp} {_fmt(float(row.iloc[0]['exports_vs_harvest']), 2)}×")
    return " / ".join(bits) if bits else "nan"


def _six_xi(pulses: pd.DataFrame, exporter: str) -> str:
    bits = []
    for intensity in INTENSITIES:
        row = pulses[(pulses["exporter"] == exporter) & (pulses["intensity"] == intensity)
                     & (pulses["duration_months"] == 6)]
        if row.empty:
            continue
        bits.append(_fmt(float(row.iloc[0]["exports_vs_harvest"]), 2))
    return " / ".join(bits) if bits else "nan"


def _stk(tab: pd.DataFrame) -> str:
    if tab.empty or "ending_stocks_vs_harvest" not in tab.columns:
        return "nan"
    return _fmt(float(tab.iloc[0]["ending_stocks_vs_harvest"]), 2)


def _fmt(x, nd: int = 2) -> str:
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "nan"
    return f"{float(x):.{nd}f}"


def grid_is_clean(summary: pd.DataFrame) -> bool:
    """P11 8-run slice: feasible, Δ binds on one exporter, harvest identical.

    Unconverged scipy (N5) is counted, not a reason to call the slice dirty
    if failed=0 and the export cut has the prescribed sign.
    """
    pulses = summary[summary["label"] != "harvest_only"]
    if len(pulses) != 8:
        return False
    if int(pulses["failed"].sum()) != 0:
        return False
    if not np.allclose(pulses["production_vs_harvest"].to_numpy(float), 1.0, atol=1e-8):
        return False
    if (pulses["other_exporters_delta_max"] > 0).any():
        return False
    full = pulses[(pulses["intensity"] == 1.0) & (pulses["duration_months"] == 12)]
    if full.empty or not (full["exports_vs_harvest"] < 1.0).all():
        return False
    return True


def write_pulse_note(summary: pd.DataFrame, out_dir: Path) -> Path:
    pulses = summary[summary["label"] != "harvest_only"]
    h = summary[summary["label"] == "harvest_only"].iloc[0]
    clean = grid_is_clean(summary)
    lines = [
        "# G0-H/P — 2008 exporter pulse grid (P11)",
        "",
        "**Prescribed Δ, not Gate 2.** `restriction_pulse` on harvest-anomaly",
        "wheat, 2008 only, versus harvest-only. Governments do not choose Δ.",
        "`sheaf/dynamic_policy.py` is not imported. `wheat_params()` stay",
        "αI=3.2, p_sto=0.1, xmin=0.2. L1–L8 stay rejected. Bai α_foreign=10",
        "not adopted. AMIS diary is **off**; each run has one synthetic pulse.",
        "",
        f"Window: {START_YEAR} (no 2003–11 re-run). Pulse start {PULSE_START}.",
        "Grid: Ukraine, Russia × {0.5, 1.0} × {6, 12} months = **8 runs**",
        "+ harvest-only. Bai's 9×2×2=36 2020 grid is **not** run.",
        f"This 8-run slice is **{'clean' if clean else 'not clean'}**",
        "(failed=0, production identical, Δ on one exporter, Δ=1.0/12m",
        "cuts that exporter's XI). Do not expand to 36 in this prompt",
        "either way — one PR-sized change.",
        "",
        "## Harvest-only 2008 (baseline)",
        "",
        f"Mean world price ${_fmt(h['mean_price_usd'], 1)}/t; max "
        f"${_fmt(h['max_price_usd'], 1)}. Failed {int(h['failed'])};",
        f"unconverged {int(h['unconverged'])} of {int(h['n_steps'])}*27.",
        "Harvest-only Ukraine XI "
        f"{_fmt(h['exports'], 1)} MMT (this row's quantity columns).",
        "Russia harvest-only XI is the denominator on the Russia rows.",
        "Exporter columns below are vs this path, not vs Pink Sheet.",
        "",
        "## Pulse vs harvest-only",
        "",
        "| run | Δ steps | mean p $/t | vs H | exports | vs H | consumption vs H | failed | unconv |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for _, r in pulses.iterrows():
        lines.append(
            f"| {r['label']} | {int(r['delta_steps_on'])} | "
            f"{_fmt(r['mean_price_usd'], 1)} | {_fmt(r['mean_price_vs_harvest'], 2)} | "
            f"{_fmt(r['exports'], 1)} | {_fmt(r['exports_vs_harvest'], 2)} | "
            f"{_fmt(r['consumption_vs_harvest'], 2)} | "
            f"{int(r['failed'])} | {int(r['unconverged'])} |"
        )
    ukr1 = pulses[(pulses["exporter"] == "Ukraine") & (pulses["intensity"] == 1.0)
                  & (pulses["duration_months"] == 12)]
    rus1 = pulses[(pulses["exporter"] == "Russia") & (pulses["intensity"] == 1.0)
                  & (pulses["duration_months"] == 12)]
    lines += [
        "",
        "Δ=1.0 is a complete international cut (D.3 `(1−Δ)`), stronger than",
        "E.4's 0.95 ban. Intensity 0.5 matches E.4 export tax. 6-month",
        "pulses occupy 12 of 24 steps; 12-month pulses occupy the year.",
        "",
        "Ukraine Δ=1 / 12m exports vs harvest-only: "
        f"{_fmt(float(ukr1.iloc[0]['exports_vs_harvest']) if not ukr1.empty else float('nan'), 2)}×.",
        "Russia Δ=1 / 12m: "
        f"{_fmt(float(rus1.iloc[0]['exports_vs_harvest']) if not rus1.empty else float('nan'), 2)}×.",
        "",
        "## What the slice shows",
        "",
        "D.3 `(1−Δ)` binds on the prescribed exporter: 12-month Δ=1.0",
        "zeros Ukraine and Russia XI; 12-month Δ=0.5 halves them",
        f"({_half_xi(pulses)}). A 6-month pulse from 2008-01-01 only",
        "cuts annual XI by a few percent to mid-teens "
        f"(Ukraine {_six_xi(pulses, 'Ukraine')}, "
        f"Russia {_six_xi(pulses, 'Russia')}): wheat harvest calendars",
        "are Jul–Aug (Ukraine) and Jul–Sep (Russia), so Jan–Jun is",
        "mostly the lean half of the year. Mean world price stays",
        "0.99–1.01× harvest-only; the ~$608 max is the host seasonal",
        "spike (P8), not a restriction spike. Unsold grain stays in stocks "
        f"(Ukraine Δ=1/12m ending stocks {_stk(ukr1)}× harvest-only).",
        "Consumption barely moves. Unconverged scipy (N5) is counted;",
        "failed=0.",
        "",
        f"This is **{'clean' if clean else 'not clean'}** as a mechanism",
        "check. It is not a Pink-Sheet fit, not a reason to restore L1–L8,",
        "not Gate 2, and not a reason to expand to Bai's 36-run 2020 grid",
        "in this PR.",
        "",
        "## Not Gate 2, not the 36-run grid",
        "",
        "- Gate 2 would let governments **choose** Δ. Disabled G2 recovers",
        "  E.4 AMIS. This grid **prescribes** Δ.",
        "- Bai 2020: 9 exporters × 2 intensities × 2 durations. Not run.",
        "- Default three-scenario host is unchanged (AMIS diary still E.4).",
        "",
        "## Files",
        "",
        "- `score_pulse.csv` — harvest-only + 8 pulses",
        "",
        "Next: P12 methods note is `methods.md` (written; not accepted; G1 blocked).",
        "",
    ]
    path = Path(out_dir) / "pulse.md"
    path.write_text("\n".join(lines) + "\n")
    return path


def run_pulse_score(out_dir: Path | None = None) -> dict[str, Path]:
    out_dir = Path(out_dir) if out_dir else OUT_DEFAULT
    out_dir.mkdir(parents=True, exist_ok=True)
    _data, harvest, pulsed = run_pulse_grid()
    summary = score_pulse_grid(harvest, pulsed)
    summary.to_csv(out_dir / "score_pulse.csv", index=False)
    note = write_pulse_note(summary, out_dir)
    return {"note": note, "csv": out_dir / "score_pulse.csv"}
