# Agent instructions — SHEAF

Gate 0 drives the **vendored Julia Agrimate code** in
[`agrimate_julia/`](agrimate_julia/). Read
[`diagnostics/GATE0_CONTRACT.md`](diagnostics/GATE0_CONTRACT.md) before
changing that tree, Gate 0 docs, or the default entry point.

- **Default run:** `python drivers/run.py --anomalies --restrictions --t-max 312`
- **Score vs author:** `python drivers/score.py path/to/output.nc`
- **Author inputs:** `python inputs/from_paper.py`
- **Public-data inputs:** `PYTHONPATH=. python inputs/from_data.py [--crop wheat|rice|maize]`
- **Evidence:** [`diagnostics/gate0_julia/`](diagnostics/gate0_julia/)
- **Julia:** 1.6.5 only (Intel / Rosetta). Do **not** `Pkg.update()` or
  `Pkg.resolve()`.
- **Edits to `agrimate_julia/`** must be listed in
  [`agrimate_julia/UPSTREAM.md`](agrimate_julia/UPSTREAM.md).
- Wheat Gate 0 is **accepted** (G0-P). Do **not** implement substitution
  until rice and maize smoke. Do **not** start Gate 2 until Gate 1 is
  accepted.
