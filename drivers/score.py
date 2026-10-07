#!/usr/bin/env python3
"""Score a local Agrimate NetCDF against the author wheat run.

Wraps ``drivers/peek_agrimate_partial_run.jl`` (same world-price and stock
definitions as the J4/J8/J9/J10 notes).

    python drivers/score.py path/to/local.nc
"""
from __future__ import annotations

import os
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "agrimate_julia"
DEFAULT_JULIA = Path("/Users/mjp38/GitHub/agrimate-2025/julia/julia-1.6.5/bin/julia")
PEEK = ROOT / "drivers" / "peek_agrimate_partial_run.jl"


def main() -> int:
    nc = sys.argv[1] if len(sys.argv) > 1 else ""
    exe = Path(os.environ.get("AGRIMATE_JULIA", DEFAULT_JULIA))
    cmd = [str(exe), f"--project={PROJECT}", str(PEEK)]
    if platform.machine() == "arm64":
        cmd = ["arch", "-x86_64", *cmd]
    if nc:
        cmd.append(nc)
    env = os.environ.copy()
    if "J10_CSV" not in env:
        env["J10_CSV"] = str(ROOT / "inputs" / "generated" / "price_monthly.csv")
    if "J10_STOCK_CSV" not in env:
        env["J10_STOCK_CSV"] = str(ROOT / "inputs" / "generated" / "stocks_annual.csv")
    return subprocess.call(cmd, cwd=PROJECT, env=env)


if __name__ == "__main__":
    raise SystemExit(main())
