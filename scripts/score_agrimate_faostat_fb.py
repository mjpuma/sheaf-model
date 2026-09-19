#!/usr/bin/env python3
"""P10: FAOSTAT Food Balance inventory. Does not switch the USDA host.

    PYTHONPATH=. python scripts/score_agrimate_faostat_fb.py
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
    from sheaf.agrimate.faostat_fb import run_faostat_fb_inventory
    paths = run_faostat_fb_inventory(out_dir=args.out)
    print(paths["note"].read_text())


if __name__ == "__main__":
    main()
