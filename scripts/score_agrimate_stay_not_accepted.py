#!/usr/bin/env python3
"""Stay not-accepted: reaffirm G0-P after T1–T3. Do not start G1.

    PYTHONPATH=. python scripts/score_agrimate_stay_not_accepted.py
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
    from sheaf.agrimate.stay_not_accepted import run_stay_not_accepted
    from sheaf.agrimate.methods import publication_bar
    from sheaf.agrimate.params import wheat_params

    assert wheat_params().alpha_i == 3.2
    assert publication_bar()["accepted"] is False
    paths = run_stay_not_accepted(out_dir=args.out)
    print(paths["note"].read_text())
    print("wrote", {k: str(v) for k, v in paths.items()})


if __name__ == "__main__":
    main()
