"""Gate 0 J8: reconstructed Agrimate inputs with the author's region parameters.

Input-alignment experiment, not a retune. Nothing is fitted. The region
values of psi (STU), A_d_star and A_c_star are copied from the author's
Zenodo data v3 wheat NetCDF output (all three scenario files agree).

Steps
1. Run ``drivers/export_agrimate_author_params.jl`` under the paper
   project. It writes ``author_region_params.csv`` and ``area_region_map.csv``
   (the AgrimateEU28 + Egypt map that ``simulate()`` builds) to
   ``agrimate-2025/j8_author_params/``.
2. Run this script. It copies the six other reconstructed CSVs from
   ``data/agrimate_input/`` unchanged and writes a new parameters file in
   which every country carries its region's author value for STU, A_d and
   A_c.

``generate_empirical_params`` (src/preprocess.jl) fills missing cells with
regional medians and then takes the consumption-weighted mean over each
region's countries, rounded to 4 digits. If every country in a region has
the same value v, that mean is v whatever the consumption weights (zero
weights included), as long as the region's total consumption is positive.
The author values are already 4-digit, so the rounding returns them
exactly. Areas not in the region map keep their original cells; the paper
code drops them.

The source directory ``data/agrimate_input/`` is only read.
"""

from __future__ import annotations

import csv
import shutil
from pathlib import Path

ROOT = Path("/Users/mjp38/GitHub/agrimate-2025")
PAPER = ROOT / "agrimate-equal-sales-penalty"
SRC = PAPER / "data" / "agrimate_input"
DST = PAPER / "data" / "agrimate_input_authorparams"
AUTHOR = ROOT / "j8_author_params"
PARAMS = "parameters_baseline=2007-2009_crop=wheat_source=empirical.csv"
FOOD = "food-balance_baseline=2007-2009_crop=wheat.csv"


def main() -> None:
    if DST.resolve() == SRC.resolve():
        raise SystemExit("refusing to write into the source input dir")
    DST.mkdir(parents=True, exist_ok=True)

    csvs = sorted(p for p in SRC.glob("*.csv") if p.name != PARAMS)
    assert len(csvs) == 6, [p.name for p in csvs]
    for p in csvs:
        shutil.copy2(p, DST / p.name)

    with open(AUTHOR / "author_region_params.csv", newline="") as f:
        author = {r["Region"]: r for r in csv.DictReader(f)}
    with open(AUTHOR / "area_region_map.csv", newline="") as f:
        region_of = {r["Area"]: r["Region"] for r in csv.DictReader(f)}

    with open(SRC / FOOD, newline="") as f:
        consumption = {r["Area"]: float(r["Consumption"]) for r in csv.DictReader(f)}
    totals: dict[str, float] = {}
    for area, region in region_of.items():
        totals[region] = totals.get(region, 0.0) + consumption.get(area, 0.0)
    for region in author:
        if totals.get(region, 0.0) <= 0:
            raise SystemExit(f"region {region} has zero consumption; weighted mean undefined")

    with open(SRC / PARAMS, newline="") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        rows = list(reader)
    assert fields == ["Area", "STU", "A_d", "A_c"], fields

    unmapped = []
    for r in rows:
        region = region_of.get(r["Area"])
        if region is None:
            unmapped.append(r["Area"])
            continue
        a = author[region]
        r["STU"], r["A_d"], r["A_c"] = a["psi"], a["A_d_star"], a["A_c_star"]
        if r["Area"] not in consumption:
            raise SystemExit(f"{r['Area']} missing from food balance; its weight would be missing")

    covered = {region_of[r["Area"]] for r in rows if r["Area"] in region_of}
    missing = set(author) - covered
    if missing:
        raise SystemExit(f"author regions with no country row: {sorted(missing)}")

    with open(DST / PARAMS, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    (DST / "README.txt").write_text(
        "SHEAF reconstruction of the CSVs simulate() reads. Not author input.\n"
        "Six CSVs are byte copies of data/agrimate_input/. The parameters file\n"
        "carries the author's region psi, A_d_star, A_c_star (Zenodo data v3\n"
        "NetCDF) on every country of the region. See\n"
        "diagnostics/gate0_julia/J8_authorparams.md in the sheaf-model repo.\n"
    )
    print(f"wrote {DST}")
    print(f"rows {len(rows)}, regions {len(covered)}, unmapped areas kept as-is: {unmapped}")


if __name__ == "__main__":
    main()
