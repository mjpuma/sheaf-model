#!/usr/bin/env python3
"""R9: P5 unconverged count on Fig. 4 knobs. Does not raise plan_maxiter.

    PYTHONPATH=. python scripts/characterize_agrimate_fig4_solver.py
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
    from sheaf.agrimate.fig4_solver import run_fig4_solver_score
    paths = run_fig4_solver_score(out_dir=OUT)
    print(paths["note"].read_text())
    print(paths["dispatch"].read_text())


if __name__ == "__main__":
    main()
