#!/usr/bin/env python3
"""Launch the vendored Agrimate Julia host.

    python drivers/run.py --anomalies --restrictions --t-max 312

Julia 1.6.5 only (Intel build; on Apple Silicon this wraps ``arch -x86_64``).
Do not run ``Pkg.update()`` or ``Pkg.resolve()``. Package versions are pinned
in ``agrimate_julia/Manifest.toml``.

Environment:
    AGRIMATE_JULIA   path to julia 1.6.5 (default: the local 2025 install)
    AGRIMATE_INPUT   input directory of the seven CSVs
    AGRIMATE_OUTPUT  NetCDF output root
"""
from __future__ import annotations

import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "agrimate_julia"
DEFAULT_JULIA = Path("/Users/mjp38/GitHub/agrimate-2025/julia/julia-1.6.5/bin/julia")
DEFAULT_INPUT = ROOT / "inputs" / "generated" / "agrimate_input"
DEFAULT_OUTPUT = ROOT / "agrimate_julia" / "data"


def julia_cmd() -> list[str]:
    exe = Path(os.environ.get("AGRIMATE_JULIA", DEFAULT_JULIA))
    cmd = [str(exe), f"--project={PROJECT}"]
    if platform.machine() == "arm64":
        cmd = ["arch", "-x86_64", *cmd]
    return cmd


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--t-max", type=int, default=312)
    p.add_argument("--anomalies", action="store_true", help='production_anomalies="FAOsince-2005"')
    p.add_argument("--restrictions", action="store_true", help='export_restrictions="2007-2011"')
    p.add_argument("--inputroot", type=Path, default=Path(os.environ.get("AGRIMATE_INPUT", DEFAULT_INPUT)))
    p.add_argument("--outputroot", type=Path, default=Path(os.environ.get("AGRIMATE_OUTPUT", DEFAULT_OUTPUT)))
    p.add_argument("--verbose", action="store_true", default=True)
    args = p.parse_args()

    anomalies = 'production_anomalies = "FAOsince-2005",' if args.anomalies else ""
    restrictions = 'export_restrictions = "2007-2011",' if args.restrictions else ""
    wrapper = f"""
using DrWatson
@quickactivate "Agrimate"
using Dates
include(srcdir("simulation.jl"))
params = Params(
    crops = "wheat",
    baseline = "2007-2009",
    regions = "AgrimateEU28",
    extra_regions = Dict{{String,Any}}("Egypt" => "EGY"),
    start = Date(2000, 1, 1),
    {anomalies}
    {restrictions}
)
simulate(params; t_max = {args.t_max},
         inputroot = "{args.inputroot}",
         outputroot = "{args.outputroot}",
         verbose = {str(args.verbose).lower()})
"""
    cmd = julia_cmd() + ["-e", wrapper]
    print(" ".join(cmd[:4]), "...", file=sys.stderr)
    return subprocess.call(cmd, cwd=PROJECT)


if __name__ == "__main__":
    raise SystemExit(main())
