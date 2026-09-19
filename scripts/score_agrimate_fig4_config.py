#!/usr/bin/env python3
"""R2: labelled Fig. 4-config comparison. Does not retune wheat_params().

    PYTHONPATH=. python scripts/score_agrimate_fig4_config.py
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "diagnostics" / "gate0_agrimate"


def main() -> None:
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    os.environ.setdefault("MKL_NUM_THREADS", "1")
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()
    from sheaf.agrimate.fig4_config import run_fig4_config_score
    paths = run_fig4_config_score(out_dir=args.out)
    print(paths["note"].read_text())
    print(paths["dispatch"].read_text())


if __name__ == "__main__":
    main()
