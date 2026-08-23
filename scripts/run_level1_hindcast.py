#!/usr/bin/env python3
"""Level-1 hindcast: crisis-era baseline + PSD shocks + exogenous AMIS τ.

No endogenous export-restriction game (play_game=False). This is the
Agrimate-matched reproduction path (VALIDATION.md Gate 0).

Defaults:
  --baseline-years 2004 2005 2006
  --stock-year 2005
  --severity agrimate

Example:
  python scripts/run_level1_hindcast.py
  python scripts/run_level1_hindcast.py --no-amis
  python scripts/run_level1_hindcast.py --tau-only
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from sheaf import SheafModel, build_countries
from sheaf.data_usda import (
    amis_tau_schedule,
    country_production_shocks,
    seed_stocks_from_psd,
)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int,
                    default=[2006, 2007, 2008, 2009, 2010, 2011])
    ap.add_argument("--baseline-years", nargs="+", type=int,
                    default=[2004, 2005, 2006])
    ap.add_argument("--stock-year", type=int, default=2005)
    ap.add_argument("--severity", choices=("agrimate", "prototype"),
                    default="agrimate")
    ap.add_argument("--out", type=Path, default=Path("level1_hindcast.csv"))
    ap.add_argument("--no-amis", action="store_true",
                    help="PSD shocks only (tau=0)")
    ap.add_argument("--tau-only", action="store_true",
                    help="AMIS tau only (xi=1); attribution leg")
    args = ap.parse_args()
    years = list(args.years)
    baseline = tuple(args.baseline_years)

    countries, transport, grains, freight = build_countries(
        substitution=True, quantities="usda", baseline_years=baseline)
    seed_stocks_from_psd(countries, args.stock_year)

    n = len(countries)
    if args.tau_only:
        shocks = {t: np.ones((n, len(grains))) for t in range(len(years))}
    else:
        shocks = country_production_shocks(countries, grains, years)
    taus = ({} if args.no_amis
            else amis_tau_schedule(countries, grains, years,
                                   severity=args.severity))

    model = SheafModel(countries, transport, grains, freight_mult=freight,
                       play_game=False)
    df = model.run(len(years), shocks=shocks, tau_schedule=taus)
    df["year"] = df["period"].map(lambda t: years[t])
    df.to_csv(args.out, index=False)

    mode = ("tau-only" if args.tau_only
            else "shocks-only" if args.no_amis else "full")
    print(f"Level-1 [{mode}] years={years} nodes={n} "
          f"baseline={baseline} severity={args.severity}  wrote {args.out}")
    for y, t in zip(years, range(len(years))):
        sub = df[(df.period == t) & (df.grain == "wheat")]
        nrest = int((sub.export_tax > 1.0).sum())
        who = sorted(sub.loc[sub.export_tax > 1.0, "country"].unique())
        px = float(sub.groupby("period")["importer_price"].first().iloc[0])
        print(f"  {y}: wheat importer_price={px:.1f}  "
              f"n_restricting={nrest}  {who}")


if __name__ == "__main__":
    main()
