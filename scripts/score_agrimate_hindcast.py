#!/usr/bin/env python3
"""G0-H hindcast note from existing three-scenario CSVs (P8).

Does not re-run the host. Does not retune AgrimateParams.

    PYTHONPATH=. python scripts/score_agrimate_hindcast.py
"""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "diagnostics" / "gate0_agrimate"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()
    from sheaf.agrimate.hindcast import run_hindcast_score
    paths = run_hindcast_score(out_dir=args.out)
    print(paths["note"].read_text())


if __name__ == "__main__":
    main()
