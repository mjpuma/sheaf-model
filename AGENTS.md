# Agent instructions — Agrimate-SHEAF

Gate 0 drives the **vendored Julia Agrimate code** in
[`agrimate_julia/`](agrimate_julia/). Read
[`diagnostics/GATE0_CONTRACT.md`](diagnostics/GATE0_CONTRACT.md) before
changing that tree, Gate 0 docs, or the default entry point. Gate 1:
[`diagnostics/GATE1_DESIGN.md`](diagnostics/GATE1_DESIGN.md).

- **Default run:** `python drivers/run.py --anomalies --restrictions --t-max 312`
- **Score vs author:** `python drivers/score.py path/to/output.nc`
- **Author inputs:** `python inputs/from_paper.py`
- **Public-data inputs:** `PYTHONPATH=. python inputs/from_data.py [--crop wheat|rice|maize]`
- **Evidence:** [`diagnostics/gate0_julia/`](diagnostics/gate0_julia/)
- **Julia:** 1.6.5 only (Intel / Rosetta). Do **not** `Pkg.update()` or
  `Pkg.resolve()`.
- **Edits to `agrimate_julia/`** must be listed in
  [`agrimate_julia/UPSTREAM.md`](agrimate_julia/UPSTREAM.md).
- Wheat Gate 0 is **accepted** (G0-P). Rice/maize smoke is **met**.
  Gate 1 follows `GATE1_DESIGN.md` (\(\xi\)); coauthor questions §8
  before coding. Do **not** start Gate 2 until Gate 1 is accepted.
