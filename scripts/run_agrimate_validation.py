#!/usr/bin/env python3
"""Gate 0 three-scenario validation (G0-U / G0-H workflow).

    PYTHONPATH=. python scripts/run_agrimate_validation.py

Runs undisturbed / harvest-only / harvest+AMIS on wheat 2003–11 (score 2006–11).
Writes diagnostics/gate0_agrimate/{validation.md, figures/, score_*.csv}.

Single-scenario solver smoke remains:

    python scripts/run_agrimate_wheat.py

OAT diagnostic (does not retune author defaults):

    python scripts/run_agrimate_validation.py --sensitivity
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "diagnostics" / "gate0_agrimate"


def main():
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    os.environ.setdefault("MKL_NUM_THREADS", "1")

    ap = argparse.ArgumentParser()
    ap.add_argument("--start-year", type=int, default=2003)
    ap.add_argument("--end-year", type=int, default=2011)
    ap.add_argument("--score-start", type=int, default=2006)
    ap.add_argument("--score-end", type=int, default=2011)
    ap.add_argument("--sensitivity", action="store_true",
                    help="OAT diagnostic on harvest+AMIS; does not change defaults")
    ap.add_argument("--sensitivity-extended", action="store_true")
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    from sheaf.agrimate.validation import (
        run_sensitivity,
        run_three_scenarios,
        write_figures,
        write_report,
        write_tables,
    )

    data, results = run_three_scenarios(
        start_year=args.start_year, end_year=args.end_year)
    tables = write_tables(
        data, results, out,
        score_start=args.score_start, score_end=args.score_end)
    figures = write_figures(
        data, results, out,
        score_start=args.score_start, score_end=args.score_end)

    sensitivity = None
    if args.sensitivity or args.sensitivity_extended:
        # Short window: OAT is a diagnostic, not the hindcast.
        sens_start = max(args.start_year, 2006)
        sens_end = min(args.end_year, 2008)
        sensitivity = run_sensitivity(
            data, start_year=sens_start, end_year=sens_end,
            extended=bool(args.sensitivity_extended),
        )
        sensitivity.to_csv(out / "score_sensitivity.csv", index=False)

    path = write_report(
        data, results, tables, figures, out,
        start_year=args.start_year, end_year=args.end_year,
        score_start=args.score_start, score_end=args.score_end,
        sensitivity=sensitivity,
    )
    notes = []
    for name, res in results.items():
        notes.append(f"## {name}")
        notes.extend(res.notes)
        notes.append("")
    (out / "notes.txt").write_text("\n".join(notes) + "\n")
    print(path.read_text())


if __name__ == "__main__":
    main()
