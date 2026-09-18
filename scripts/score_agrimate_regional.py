#!/usr/bin/env python3
"""G0-H regional USDA table (P9).

Scores named exporters + Eastern Africa against psd_regional_annual().
Does not retune AgrimateParams. Does not overwrite the three-scenario
price CSVs. Re-runs the host only for regional consumption/stocks.

    PYTHONPATH=. python scripts/score_agrimate_regional.py
    PYTHONPATH=. python scripts/score_agrimate_regional.py --harvest-only
"""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "diagnostics" / "gate0_agrimate"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument(
        "--harvest-only", action="store_true",
        help="Skip the three-scenario NLP; production + construction only.",
    )
    args = ap.parse_args()
    from sheaf.agrimate.regional import run_regional_score
    paths = run_regional_score(out_dir=args.out, run_model=not args.harvest_only)
    print(paths["note"].read_text())


if __name__ == "__main__":
    main()
