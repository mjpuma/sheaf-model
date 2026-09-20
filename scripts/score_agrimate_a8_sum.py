#!/usr/bin/env python3
"""R7: A8 mean-vs-sum sensitivity. Does not rewrite prepare_wheat.

    PYTHONPATH=. python scripts/score_agrimate_a8_sum.py
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
    from sheaf.agrimate.a8_sum import run_a8_sum_score
    paths = run_a8_sum_score(out_dir=args.out)
    print(paths["note"].read_text())


if __name__ == "__main__":
    main()
