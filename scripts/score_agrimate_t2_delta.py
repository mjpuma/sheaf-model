#!/usr/bin/env python3
"""T2: label sourced D.22 / solver delta. Does not copy Julia or freeze.

    PYTHONPATH=. python scripts/score_agrimate_t2_delta.py
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
    from sheaf.agrimate.t2_delta import run_t2_delta
    from sheaf.agrimate.params import wheat_params
    from sheaf.agrimate.xi_split import n_julia_sources

    assert wheat_params().alpha_i == 3.2
    assert n_julia_sources() == 0
    paths = run_t2_delta(out_dir=args.out)
    print(paths["note"].read_text())
    print("wrote", {k: str(v) for k, v in paths.items()})


if __name__ == "__main__":
    main()
