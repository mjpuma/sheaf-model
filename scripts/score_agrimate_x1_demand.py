#!/usr/bin/env python3
"""R5: labelled x1=demand vs T*+domestic. Does not adopt. Does not retune.

    PYTHONPATH=. python scripts/score_agrimate_x1_demand.py
"""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "diagnostics" / "gate0_agrimate"


def main() -> None:
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    os.environ.setdefault("MKL_NUM_THREADS", "1")
    from sheaf.agrimate.x1_demand import run_x1_demand_score
    paths = run_x1_demand_score(out_dir=OUT)
    print(paths["note"].read_text())
    print(paths["dispatch"].read_text())


if __name__ == "__main__":
    main()
