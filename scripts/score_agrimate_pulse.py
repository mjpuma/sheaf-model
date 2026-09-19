#!/usr/bin/env python3
"""P11: 8-run 2008 prescribed-Δ pulse grid. Not Gate 2.

    PYTHONPATH=. python scripts/score_agrimate_pulse.py
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
    from sheaf.agrimate.pulse import run_pulse_score
    paths = run_pulse_score(out_dir=args.out)
    print(paths["note"].read_text())


if __name__ == "__main__":
    main()
