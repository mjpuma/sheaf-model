#!/usr/bin/env python3
"""Score Gate 0 wheat against Agrimate Fig. 4 author series (P7).

Does not re-run the three-scenario host. Reads diagnostics/gate0_agrimate/
host CSVs and author_fig4/ (extracted from Zenodo 10688435). Optional
``--from-nc DIR`` rebuilds those CSVs from main_output NetCDF.

    PYTHONPATH=. python scripts/score_agrimate_fig4.py
    PYTHONPATH=. python scripts/score_agrimate_fig4.py \\
        --from-nc /tmp/zenodo10688435/main_output/data
"""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "diagnostics" / "gate0_agrimate"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-nc", type=Path, default=None,
                    help="Directory with the three main_output NetCDF files")
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--score-start", type=int, default=2006)
    ap.add_argument("--score-end", type=int, default=2011)
    args = ap.parse_args()

    from sheaf.agrimate.fig4 import extract_author_fig4, run_fig4_score

    if args.from_nc is not None:
        extract_author_fig4(args.from_nc, args.out / "author_fig4")
    paths = run_fig4_score(
        out_dir=args.out,
        author_dir=args.out / "author_fig4",
        score_start=args.score_start,
        score_end=args.score_end,
    )
    print(paths["report"].read_text())


if __name__ == "__main__":
    main()
