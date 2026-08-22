#!/usr/bin/env python3
"""Level-1 hindcast smoke run: USDA PSD shocks + AMIS exogenous tau.

VALIDATION.md Level 1 — market + storage core with historical restrictions
imposed (Agrimate-style), not the endogenous game.

Example:
  python scripts/run_level1_hindcast.py --years 2007 2008 2009 2010 2011
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from sheaf import SheafModel, build_countries
from sheaf.data_usda import amis_tau_schedule, country_production_shocks


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int,
                    default=[2007, 2008, 2009, 2010, 2011])
    ap.add_argument("--out", type=Path, default=Path("level1_hindcast.csv"))
    ap.add_argument("--no-amis", action="store_true",
                    help="PSD shocks only (tau=0)")
    args = ap.parse_args()
    years = list(args.years)

    countries, transport, grains, freight = build_countries(
        substitution=True, quantities="usda")
    shocks = country_production_shocks(countries, grains, years)
    taus = ({} if args.no_amis
            else amis_tau_schedule(countries, grains, years))

    model = SheafModel(countries, transport, grains, freight_mult=freight,
                       play_game=False)  # Level 1: exogenous tau, no game
    df = model.run(len(years), shocks=shocks, tau_schedule=taus)
    df["year"] = df["period"].map(lambda t: years[t])
    df.to_csv(args.out, index=False)

    # Headline diagnostics
    print(f"Level-1 hindcast years={years}  nodes={len(countries)}  "
          f"wrote {args.out}")
    for y, t in zip(years, range(len(years))):
        sub = df[(df.period == t) & (df.grain == "wheat")]
        nrest = int((sub.export_tax > 1.0).sum())
        who = sorted(sub.loc[sub.export_tax > 1.0, "country"].unique())
        px = float(sub.groupby("period")["importer_price"].first().iloc[0])
        print(f"  {y}: wheat importer_price={px:.1f}  "
              f"n_restricting={nrest}  {who}")


if __name__ == "__main__":
    main()
