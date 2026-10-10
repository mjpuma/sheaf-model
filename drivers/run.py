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
    cmd = [str(exe), f"--project={PROJECT.as_posix()}"]
    # Apple Silicon only: the pinned interpreter is the Intel 1.6.5 build.
    if sys.platform != "win32" and platform.machine() == "arm64":
        cmd = ["arch", "-x86_64", *cmd]
    return cmd


def julia_path(p: Path) -> str:
    """Absolute path with forward slashes so Julia on Windows can open it."""
    return p.expanduser().resolve().as_posix()


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--t-max", type=int, default=312)
    p.add_argument("--crop", choices=("wheat", "rice", "maize"), default="wheat")
    p.add_argument("--anomalies", action="store_true", help='production_anomalies="FAOsince-2005"')
    p.add_argument("--restrictions", action="store_true", help='export_restrictions="2007-2011"')
    p.add_argument("--inputroot", type=Path, default=Path(os.environ.get("AGRIMATE_INPUT", DEFAULT_INPUT)))
    p.add_argument("--outputroot", type=Path, default=Path(os.environ.get("AGRIMATE_OUTPUT", DEFAULT_OUTPUT)))
    p.add_argument("--verbose", action="store_true", default=True)
    p.add_argument("--coupled", action="store_true", help="Gate 1: wheat+rice+maize (GATE1_DESIGN.md)")
    p.add_argument("--xi", type=float, default=0.0, help="Gate 1 substitution scale ξ (0, 0.3, 0.6)")
    args = p.parse_args()

    anomalies = 'production_anomalies = "FAOsince-2005",' if args.anomalies else ""
    restrictions = 'export_restrictions = "2007-2011",' if args.restrictions else ""
    inputroot = julia_path(args.inputroot)
    outputroot = julia_path(args.outputroot)
    call = (
        f'simulate_coupled(params; crops = ("wheat", "rice", "maize"), ξ = {args.xi}, '
        f't_max = {args.t_max}, inputroot = "{inputroot}", outputroot = "{outputroot}", '
        f'verbose = {str(args.verbose).lower()})'
        if args.coupled
        else (
            f"simulate(params; t_max = {args.t_max}, "
            f'inputroot = "{inputroot}", outputroot = "{outputroot}", '
            f"verbose = {str(args.verbose).lower()})"
        )
    )
    wrapper = f"""
using DrWatson
@quickactivate "Agrimate"
using Dates
include(srcdir("simulation.jl"))
params = Params(
    crops = "{args.crop}",
    baseline = "2007-2009",
    regions = "AgrimateEU28",
    extra_regions = Dict{{String,Any}}("Egypt" => "EGY"),
    start = Date(2000, 1, 1),
    ξ = {args.xi},
    {anomalies}
    {restrictions}
)
{call}
"""
    cmd = julia_cmd() + ["-e", wrapper]
    print(" ".join(cmd[:4]), "...", file=sys.stderr)
    return subprocess.call(cmd, cwd=PROJECT)


if __name__ == "__main__":
    raise SystemExit(main())
