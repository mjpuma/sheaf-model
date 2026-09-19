#!/usr/bin/env python3
"""R4: characterise undisturbed xd/xi. Does not pin. Does not retune.

    PYTHONPATH=. python scripts/score_agrimate_xi_split.py
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
    from sheaf.agrimate.xi_split import run_xi_split_score
    paths = run_xi_split_score(out_dir=OUT)
    print(paths["note"].read_text())
    print(paths["dispatch"].read_text())


if __name__ == "__main__":
    main()
