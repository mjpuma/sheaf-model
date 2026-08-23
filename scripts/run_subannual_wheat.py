#!/usr/bin/env python3
"""Run Gate 0 sub-annual wheat spine (24 steps/yr).

Example:
  python scripts/run_subannual_wheat.py
  python scripts/run_subannual_wheat.py --no-amis
"""
from __future__ import annotations

import argparse
from pathlib import Path

from sheaf.dynamic_wheat import result_to_monthly, run_wheat_dynamics


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--start", type=int, default=2006)
    ap.add_argument("--end", type=int, default=2011)
    ap.add_argument("--no-amis", action="store_true")
    ap.add_argument("--out", type=Path,
                    default=Path("diagnostics/subannual_wheat_monthly.csv"))
    args = ap.parse_args()

    res = run_wheat_dynamics(
        start_year=args.start, end_year=args.end,
        use_amis=not args.no_amis)
    monthly = result_to_monthly(res)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    monthly.to_csv(args.out, index=False)

    print(f"sub-annual wheat  {args.start}-{args.end}  "
          f"steps={len(res.price)}  amis={not args.no_amis}")
    print(f"wrote {args.out}  ({len(monthly)} months)")
    # Headline: annual mean price
    for y in range(args.start, args.end + 1):
        sub = monthly[monthly.year == y]
        print(f"  {y}: mean p={sub.model_price.mean():.1f}  "
              f"min={sub.model_price.min():.1f}  max={sub.model_price.max():.1f}")


if __name__ == "__main__":
    main()
