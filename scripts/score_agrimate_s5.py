#!/usr/bin/env python3
"""S5: re-score Fig. 4 / hindcast from existing three-scenario CSVs.

Does not re-run the NLP runner. Does not retune AgrimateParams.

    PYTHONPATH=. python scripts/score_agrimate_s5.py
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
    from sheaf.agrimate.s5_score import run_s5_rescore
    paths = run_s5_rescore(out_dir=args.out)
    print(paths["note"].read_text())


if __name__ == "__main__":
    main()
