"""Step accounting identities for Agrimate Gate 0 (G0-U / P1).

Reconstructs producer and consumer stock updates from stored paths and
checks them against Eq. D.6 / the consumer clip in ``model.py``. Does not
change the economic model.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .equations import fulfill_sales, update_producer_storage
from .model import AgrimateResult
from .params import AgrimateParams
from .wheat_data import WheatData

ATOL = 1e-8
RTOL = 1e-8


@dataclass
class Violation:
    identity: str
    region: str
    step: int
    expected: float
    got: float
    detail: str = ""


@dataclass
class AccountingReport:
    n_steps: int
    n_regions: int
    n_checked: int
    violations: list[Violation] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.violations) == 0


def _arr(x, name: str) -> np.ndarray:
    if x is None:
        raise ValueError(f"AgrimateResult.{name} is required for accounting")
    return np.asarray(x, float)


def check_fulfill_sales_identities(planned_d, planned_i, available, delta,
                                   atol: float = ATOL) -> list[str]:
    """D.3: domestic first; international scaled by (1−Δ); nonnegative."""
    sd, si = fulfill_sales(planned_d, planned_i, available, delta)
    errs = []
    if sd < -atol or si < -atol:
        errs.append(f"negative sales sd={sd} si={si}")
    if sd + si > max(available, 0.0) + atol:
        errs.append(f"sold {sd+si} > available {available}")
    rest = max(max(available, 0.0) - sd, 0.0)
    cap = rest * (1.0 - float(np.clip(delta, 0.0, 1.0)))
    if si > cap + atol:
        errs.append(f"international {si} exceeds (1-Δ)·rest {cap}")
    return errs


def check_result(
    result: AgrimateResult,
    data: WheatData,
    params: AgrimateParams | None = None,
    atol: float = ATOL,
) -> AccountingReport:
    """Replay D.6 / consumer clip on a stored path."""
    params = params or AgrimateParams()
    H = _arr(result.harvest, "harvest")
    sold_d = _arr(result.sold_domestic, "sold_domestic")
    sold_i = _arr(result.xi_ship, "xi_ship")
    inflow = _arr(result.inflow, "inflow")
    cons = _arr(result.consumption, "consumption")
    Sp = _arr(result.S_producer, "S_producer")
    Sc = _arr(result.S_consumer, "S_consumer")
    price = np.asarray(result.price_index, float)
    n_r, T = H.shape
    report = AccountingReport(n_steps=T, n_regions=n_r, n_checked=0)
    report.notes.append(
        "In-transit international shipments (Ndel queue) sit in neither "
        "S_p nor S_c; that is Agrimate delivery lag, not a stock identity."
    )
    report.notes.append(
        f"Producer S_p starts at 0. Consumer S_c starts at Ψ·Nyear·C*. "
        f"δ_loss={params.delta_loss}."
    )

    finite_names = {
        "price_index": price,
        "harvest": H,
        "sold_domestic": sold_d,
        "xi_ship": sold_i,
        "inflow": inflow,
        "consumption": cons,
        "S_producer": Sp,
        "S_consumer": Sc,
    }
    for name, arr in finite_names.items():
        if not np.all(np.isfinite(arr)):
            bad = int(np.size(arr) - np.isfinite(arr).sum())
            report.violations.append(Violation(
                identity="finite", region="*", step=-1,
                expected=0.0, got=float(bad),
                detail=f"{name} has {bad} non-finite entries",
            ))

    S_p_begin = np.zeros(n_r)
    S_c_begin = np.maximum(data.Psi * params.n_year * data.C_star, 0.0)
    delta = data.delta
    if delta.shape[1] < T:
        pad = np.zeros((n_r, T - delta.shape[1]))
        delta = np.concatenate([delta, pad], axis=1)

    for t in range(T):
        dlt = delta[:, t] if t < delta.shape[1] else np.zeros(n_r)
        for r in range(n_r):
            report.n_checked += 4
            region = result.regions[r]
            avail = S_p_begin[r] + H[r, t]
            sd, si = float(sold_d[r, t]), float(sold_i[r, t])
            if sd < -atol or si < -atol:
                report.violations.append(Violation(
                    "sales_nonneg", region, t, 0.0, min(sd, si),
                    f"sd={sd} si={si}",
                ))
            if sd + si > avail + atol:
                report.violations.append(Violation(
                    "sales_le_available", region, t, avail, sd + si,
                    f"H={H[r, t]} S_begin={S_p_begin[r]}",
                ))
            rest = max(avail - sd, 0.0)
            cap = rest * (1.0 - float(np.clip(dlt[r], 0.0, 1.0)))
            if si > cap + atol:
                report.violations.append(Violation(
                    "sales_respect_delta", region, t, cap, si,
                    f"Δ={dlt[r]} rest={rest}",
                ))
            sp_exp = update_producer_storage(
                float(S_p_begin[r]), float(H[r, t]), sd, si, params.delta_loss)
            if abs(sp_exp - Sp[r, t]) > atol + RTOL * max(abs(sp_exp), 1.0):
                report.violations.append(Violation(
                    "producer_D6", region, t, sp_exp, float(Sp[r, t]),
                    f"S_begin={S_p_begin[r]} H={H[r, t]} sd={sd} si={si}",
                ))
            room = S_c_begin[r] + inflow[r, t]
            if cons[r, t] > room + atol:
                report.violations.append(Violation(
                    "consumption_le_stock_plus_inflow", region, t,
                    room, float(cons[r, t]),
                ))
            sc_exp = max(S_c_begin[r] + inflow[r, t] - cons[r, t], 0.0)
            if abs(sc_exp - Sc[r, t]) > atol + RTOL * max(abs(sc_exp), 1.0):
                report.violations.append(Violation(
                    "consumer_clip", region, t, sc_exp, float(Sc[r, t]),
                    f"S_begin={S_c_begin[r]} inflow={inflow[r, t]} C={cons[r, t]}",
                ))
        S_p_begin = Sp[:, t].copy()
        S_c_begin = Sc[:, t].copy()
    return report


def report_markdown(report: AccountingReport, heading: str) -> str:
    lines = [
        heading,
        "",
        f"- regions: {report.n_regions}",
        f"- steps: {report.n_steps}",
        f"- identity checks: {report.n_checked}",
        f"- violations: {len(report.violations)}",
        "",
    ]
    for n in report.notes:
        lines.append(f"- {n}")
    lines.append("")
    if report.ok:
        lines += [
            "All four P1 identities hold on this path (atol 1e-8):",
            "",
            "1. Producer D.6: `S_p' = max((1-δ)S_p + H - sold_d - sold_i, 0)`.",
            "2. Consumer: `S_c' = max(S_c + inflow - C, 0)` and `C ≤ S_c + inflow`.",
            "3. Sales: `sold_d, sold_i ≥ 0`; `sold_d + sold_i ≤ S_p + H`;",
            "   `sold_i ≤ (1-Δ)(S_p + H - sold_d)` (D.3).",
            "4. `price_index`, stocks, harvest, consumption, sales, inflow finite.",
            "",
            "Classification: **H** (not an issue) for this 2006 path.",
            "No economic change. Next prompt is P2 (undisturbed drift).",
            "",
        ]
        return "\n".join(lines)
    lines += ["## Violations (first 20)", ""]
    for v in report.violations[:20]:
        lines.append(
            f"- `{v.identity}` {v.region} t={v.step}: "
            f"expected {v.expected:.8g} got {v.got:.8g} {v.detail}"
        )
    lines += [
        "",
        "Do not retune L1–L8 to clear these. Classify in GATE0_DEPARTURES.md",
        "after a counterexample + correctness argument.",
        "",
    ]
    return "\n".join(lines)
