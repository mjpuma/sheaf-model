#!/usr/bin/env python3
"""Red team solver last/first 0.812 from committed CSVs. No NLP re-run.

    PYTHONPATH=. python scripts/score_agrimate_rt_solver.py
"""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "diagnostics" / "gate0_agrimate"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()
    from sheaf.agrimate.params import wheat_params
    from sheaf.agrimate.rt_solver import run_rt_solver
    from sheaf.agrimate.xi_split import n_julia_sources

    assert wheat_params().alpha_i == 3.2
    assert wheat_params().plan_maxiter == 40
    assert n_julia_sources(ROOT / "sheaf") == 0
    paths = run_rt_solver(out_dir=args.out)
    print(paths["note"].read_text())
    print("wrote", {k: str(v) for k, v in paths.items()})


if __name__ == "__main__":
    main()
