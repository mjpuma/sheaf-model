#!/usr/bin/env python3
"""Copy Gate 0 figures into overleaf/gate0_whitepaper/figures/.

Run from repo root after score_subannual_crop.py, make_agrimate_comparison.py,
and score_ukraine_war.py.
"""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "overleaf" / "gate0_whitepaper" / "figures"
AGR = ROOT / "overleaf" / "gate0_agrimate" / "figures"
FIGS = ROOT / "figures"

# Prefer PDF from the Agrimate companion when both exist.
AGRIMATE = [
    "fig_prices_wheat",
    "fig_prices_maize",
    "fig_prices_rice",
    "fig_forcing_wheat",
    "fig_forcing_maize",
    "fig_forcing_rice",
    "fig_russia_wheat",
    "fig_egypt_wheat",
    "fig_balance_wheat",
    "fig_balance_maize",
    "fig_balance_rice",
]
GATE0 = [
    "fig_gate0_ukraine_prices.png",
    "fig_gate0_wheat_world_consumption.png",
    "fig_gate0_maize_world_consumption.png",
    "fig_gate0_rice_world_consumption.png",
    "fig_gate0_wheat_shipments.png",
    "fig_gate0_maize_shipments.png",
    "fig_gate0_rice_shipments.png",
    "fig_gate0_wheat_world_exchina.png",
    "fig_gate0_maize_world_exchina.png",
    "fig_gate0_rice_world_exchina.png",
    "fig_gate0_wheat_diagnostics.png",
    "fig_gate0_maize_diagnostics.png",
    "fig_gate0_rice_diagnostics.png",
    "fig_gate0_map_wheat_roles_2008.png",
    "fig_gate0_map_wheat_amis_2008.png",
    "fig_gate0_map_rice_amis_2008.png",
    "fig_gate0_map_wheat_harvest_2007.png",
    "fig_gate0_map_wheat_harvest_2010.png",
    "fig_gate0_map_wheat_bite_2010.png",
    "fig_gate0_map_wheat_cons_2008.png",
]


def _copy(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    print(f"  {src.relative_to(ROOT)} -> {dest.relative_to(ROOT)}")


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    for stem in AGRIMATE:
        pdf, png = AGR / f"{stem}.pdf", AGR / f"{stem}.png"
        if pdf.exists():
            _copy(pdf, DEST / f"{stem}.pdf")
        if png.exists():
            _copy(png, DEST / f"{stem}.png")
        if not pdf.exists() and not png.exists():
            print(f"  MISSING {stem}")
    for name in GATE0:
        src = FIGS / name
        if src.exists():
            _copy(src, DEST / name)
        else:
            print(f"  MISSING {name}")
    print(f"figures in {DEST}")


if __name__ == "__main__":
    main()
