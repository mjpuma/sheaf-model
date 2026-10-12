#!/usr/bin/env python3
"""Score Gate 1 ξ=0 identity: coupled vs single-crop monthly world price.

    python drivers/compare_g1_identity.py agrimate_julia/data_g1prep_identity

Bar: 0.5% (GATE1_DESIGN.md). Wraps ``drivers/compare_g1_identity.jl``.
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
CMP = ROOT / "drivers" / "compare_g1_identity.jl"


def main() -> int:
    out = sys.argv[1] if len(sys.argv) > 1 else str(PROJECT / "data_g1prep_identity")
    exe = Path(os.environ.get("AGRIMATE_JULIA", DEFAULT_JULIA))
    cmd = [str(exe), f"--project={PROJECT.as_posix()}", Path(CMP).as_posix(),
           Path(out).expanduser().resolve().as_posix()]
    if sys.platform != "win32" and platform.machine() == "arm64":
        cmd = ["arch", "-x86_64", *cmd]
    return subprocess.call(cmd, cwd=PROJECT)


if __name__ == "__main__":
    raise SystemExit(main())
