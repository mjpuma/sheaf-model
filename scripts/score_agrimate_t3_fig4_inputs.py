#!/usr/bin/env python3
"""T3: obtain-or-leave FAO-since-2005 + AgrimateEU28+Egypt. Label only.

    PYTHONPATH=. python scripts/score_agrimate_t3_fig4_inputs.py
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
    from sheaf.agrimate.t3_fig4_inputs import run_t3_fig4_inputs
    from sheaf.agrimate.params import wheat_params
    from sheaf.agrimate.regions import REGION_NAMES
    from sheaf.agrimate.xi_split import n_julia_sources

    assert wheat_params().alpha_i == 3.2
    assert "Egypt" not in REGION_NAMES
    assert n_julia_sources() == 0
    paths = run_t3_fig4_inputs(out_dir=args.out)
    print(paths["note"].read_text())
    print("wrote", {k: str(v) for k, v in paths.items()})


if __name__ == "__main__":
    main()
