#!/usr/bin/env python3
"""D.22: implement sourced vector+shift. Does not freeze, pin, or switch solver.

    PYTHONPATH=. python scripts/score_agrimate_d22.py
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
    from sheaf.agrimate.d22 import run_d22_undisturbed
    from sheaf.agrimate.params import wheat_params
    from sheaf.agrimate.xi_split import n_julia_sources

    assert wheat_params().alpha_i == 3.2
    assert n_julia_sources(ROOT / "sheaf") == 0
    paths = run_d22_undisturbed(out_dir=args.out)
    print(paths["note"].read_text())
    print("wrote", {k: str(v) for k, v in paths.items()})


if __name__ == "__main__":
    main()
