#!/usr/bin/env python3
"""Reference Agrimate-faithful Gate 0 wheat run.

    python scripts/run_agrimate_wheat.py

Writes diagnostics/gate0_agrimate/{prices.csv,validation.md,notes.txt}.
Legacy comparison: python scripts/score_legacy_crop.py --crop wheat
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from sheaf.agrimate.model import run_wheat
from sheaf.agrimate.wheat_data import prepare_wheat
from sheaf.data_usda import load_price_series_monthly

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "diagnostics" / "gate0_agrimate"


def _corr(a, b) -> float:
    a, b = np.asarray(a, float), np.asarray(b, float)
    m = np.isfinite(a) & np.isfinite(b)
    if m.sum() < 6:
        return float("nan")
    return float(np.corrcoef(a[m], b[m])[0, 1])


def _hike(series, year0, year1) -> float:
    s = series[(series.index.year >= year0) & (series.index.year <= year1)]
    if s.empty:
        return float("nan")
    peak = float(s.rolling(3, min_periods=2).mean().max())
    ref = float(series[series.index.year == year0].mean())
    return peak / ref if ref and np.isfinite(ref) and ref > 0 else float("nan")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start-year", type=int, default=2003)
    ap.add_argument("--end-year", type=int, default=2011)
    ap.add_argument("--no-restrictions", action="store_true")
    ap.add_argument("--no-anomalies", action="store_true")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    data = prepare_wheat(start_year=args.start_year, end_year=args.end_year)
    res = run_wheat(
        data=data,
        use_restrictions=not args.no_restrictions,
        use_anomalies=not args.no_anomalies,
        start_year=args.start_year,
        end_year=args.end_year,
    )
    monthly = res.to_monthly_price()
    idx = pd.period_range(f"{res.start_year}-01", periods=monthly.size, freq="M")
    model = pd.Series(monthly, index=idx, name="model_usd")
    pink = load_price_series_monthly()
    pink["stamp"] = [pd.Period(year=int(y), month=int(m), freq="M")
                     for y, m in zip(pink["year"], pink["month"])]
    obs = pink.set_index("stamp")["wheat"].rename("pink_usd")
    both = pd.concat([model, obs], axis=1).dropna()
    both = both[(both.index.year >= 2006) & (both.index.year <= 2011)]
    corr = _corr(both["model_usd"], both["pink_usd"])
    h08_m = _hike(both["model_usd"], 2006, 2008)
    h08_o = _hike(both["pink_usd"], 2006, 2008)
    OUT.mkdir(parents=True, exist_ok=True)
    both.to_csv(OUT / "prices_2006_11.csv")
    (OUT / "notes.txt").write_text("\n".join(res.notes) + "\n")
    md = f"""# Agrimate Gate 0 wheat — validation snapshot

Command: `python scripts/run_agrimate_wheat.py --start-year {args.start_year} --end-year {args.end_year}`

Independent implementation of Kuhla et al. (2025) §D; not a bit-reproduction
of Zenodo 14022004 (code not retrieved).

- regions: {len(res.regions)}
- failed supplier solves: {res.failed_solves}
- fallback: {res.fallback_solves}
- unconverged (feasible but scipy not success): {res.unconverged_solves}
- inverse-demand floor binds (offers): {res.floor_binds}
- max plan residual: {res.plan_residual:.3e}
- runtime: {res.runtime_s:.1f}s
- Nash IBR: {res.nash['iterations']} err={res.nash['err']} success={res.nash['success']}
- min S_p / S_c: {res.S_producer.min():.4f} / {res.S_consumer.min():.4f}
- price index min/max: {res.price_index.min():.4f} / {res.price_index.max():.4f}
- 2006–11 Pink Sheet corr: {corr:+.3f}
- 2007/08 hike model/obs: ×{h08_m:.2f} / ×{h08_o:.2f}

A worse Pink-Sheet fit than the legacy host is not a reason to restore
fill-target, calm pin, scarcity blend, or rival markup.

## G0-N (supplier programme)

Always-feasible `(fd, fi) ∈ [0, 1]` map of D.11–D.21; rolling forthcoming
year `[t, t+Nyear)`; Jacobi IBR against D.22 expected rivals; D.7 argument
`(XI_r + Q_{{-r}}) / XI*_world`. Not L1–L8. Success = finite and `S ≥ 0`.
Unconverged counts scipy `success=False` on a still-feasible point.
Plan-path floor hits are mostly off-season `XD = 0` when `H = S = 0`
(domestic `q` at the numerical floor with zero sales). Offer-floor binds
are the market-relevant count.

2006-only smoke (same host): failed=0, fallback=0, offer-floor=0,
price index ≈ 0.010–2.95, runtime ≈ 1.5 s. Pre-G0-N host: failed 344,
fallback 417 of 672, price index ≈ 0.0006–1.00 because failed plans kept
Nash offers.
"""
    (OUT / "validation.md").write_text(md)
    print(md)


if __name__ == "__main__":
    main()
