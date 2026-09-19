#!/usr/bin/env python3
"""R10: score R2 Fig. 4 knobs against author_fig4/. Does not retune.

    PYTHONPATH=. python scripts/score_agrimate_fig4_author.py
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
    from sheaf.agrimate.fig4_author_score import run_fig4_author_score
    paths = run_fig4_author_score(out_dir=OUT)
    print(paths["note"].read_text())
    print(paths["dispatch"].read_text())


if __name__ == "__main__":
    main()
