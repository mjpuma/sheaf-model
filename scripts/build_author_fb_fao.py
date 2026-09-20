#!/usr/bin/env python3
"""Build the labelled host reconstruction of wheat_food_balance_fao.csv.

Does not switch prepare_wheat. USDA stays default. wheat_params unchanged.

    PYTHONPATH=. python scripts/build_author_fb_fao.py
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
    from sheaf.agrimate.author_fb import run_author_fb
    from sheaf.agrimate.wheat_data import prepare_wheat

    paths = run_author_fb(out_dir=args.out)
    d = prepare_wheat(start_year=2006, end_year=2006)
    assert any("USDA PSD" in n and "not FAOSTAT Food Balances" in n for n in d.notes)
    print(paths["note"].read_text())
    print("wrote", {k: str(v) for k, v in paths.items()})


if __name__ == "__main__":
    main()
