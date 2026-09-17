#!/usr/bin/env python3
"""LEGACY Gate 0 scorer — labelled pre-rewrite benchmark.

    python scripts/score_legacy_crop.py --crop wheat

This is not the Agrimate-faithful default
(``python scripts/run_agrimate_wheat.py``).
"""
from __future__ import annotations

import argparse

from sheaf.legacy.dynamic_crop import run_crop_dynamics, result_to_monthly


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--crop", default="wheat")
    ap.add_argument("--start-year", type=int, default=2006)
    ap.add_argument("--end-year", type=int, default=2011)
    args = ap.parse_args()
    res = run_crop_dynamics(crop=args.crop, start_year=args.start_year,
                            end_year=args.end_year)
    monthly = result_to_monthly(res)
    print(monthly.head())
    print("legacy run ok", args.crop, "rows", len(monthly))


if __name__ == "__main__":
    main()
