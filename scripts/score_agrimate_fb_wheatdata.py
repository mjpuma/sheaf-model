#!/usr/bin/env python3
"""R6: labelled FBSH parallel WheatData vs USDA. Does not switch the host.

    PYTHONPATH=. python scripts/score_agrimate_fb_wheatdata.py
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
    from sheaf.agrimate.fb_wheatdata import run_fb_wheatdata_score
    paths = run_fb_wheatdata_score(out_dir=args.out)
    print(paths["note"].read_text())


if __name__ == "__main__":
    main()
