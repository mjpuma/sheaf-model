#!/usr/bin/env python3
"""S3: re-score FBSH H/C vs S1 member-sum USDA. Does not switch the host.

    PYTHONPATH=. python scripts/score_agrimate_s3_fbsh.py
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
    from sheaf.agrimate.fb_wheatdata import run_s3_fbsh_score
    paths = run_s3_fbsh_score(out_dir=args.out)
    print(paths["note"].read_text())


if __name__ == "__main__":
    main()
