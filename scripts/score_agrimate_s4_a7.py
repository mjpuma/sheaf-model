#!/usr/bin/env python3
"""S4: A7 cannot-set inventory. Does not invent Egypt or retune wheat_params.

    PYTHONPATH=. python scripts/score_agrimate_s4_a7.py
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
    from sheaf.agrimate.s4_a7 import run_s4_a7_inventory
    from sheaf.agrimate.params import wheat_params
    from sheaf.agrimate.regions import REGION_NAMES

    assert wheat_params().alpha_i == 3.2
    assert "Egypt" not in REGION_NAMES
    paths = run_s4_a7_inventory(out_dir=args.out)
    print(paths["note"].read_text())
    print("wrote", {k: str(v) for k, v in paths.items()})


if __name__ == "__main__":
    main()
