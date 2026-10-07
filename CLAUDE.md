# CLAUDE.md

Constitution for work on SHEAF after the Gate 0 host cut. This does not
override [`diagnostics/GATE0_CONTRACT.md`](diagnostics/GATE0_CONTRACT.md).

## What SHEAF is

SHEAF is a country-level, multi-commodity, game-theoretic network model of
global grain trade, in the TWIST → Agrimate lineage. The Gate 0 host is the
**published Julia Agrimate code** vendored at `agrimate_julia/` (Kuhla et
al. 2025; Zenodo 14022004; CC-BY 4.0). Python is drivers, input builders,
scoring, and plots.

Gate 1 substitution and Gate 2 endogenous restrictions are **blocked**
until stage G0-P is accepted. Do not implement them.

## Gate 0 evidence

J10 established that this Julia tree, given the authors’ own calibration,
reproduces their published wheat run
(`diagnostics/gate0_julia/J10_authorbaseline.md`). Reconstructing the
unpublished input tables from USDA / FAOSTAT / AMIS does **not**
reproduce those magnitudes (J4/J8/J9). A failed public-data match stays a
failed match; do not retune to shrink it.

## Rules

- **Correctness over polish.** Every claim needs evidence. Do not
  optimize for criticism or praise.
- **Do not edit Agrimate economics or `Params` defaults** unless there is
  an approved departure and an `UPSTREAM.md` entry.
- **Do not run `Pkg.update()` or `Pkg.resolve()`.** Julia 1.6.5, Manifest
  pinned.
- **Do not clone GitLab main or `develop-consumers`.**
- **Units:** quantities in the paper code are 1000 t; world-price index is
  dimensionless around 1. Flag inconsistencies rather than silently converting.
- **Classification** of findings, when you are auditing: A mathematical
  error, B coding bug, C numerical issue, D economic simplification, E
  modeling philosophy, F empirical limitation, G documentation, H not an
  issue. Confidence 95–100 / 80–95 / 60–80 / 40–60 / below 40. Do not
  recommend complexity on findings below 60 %.

## Layout

`agrimate_julia/` host · `drivers/` launch and score · `inputs/` builders
and USDA/FAOSTAT readers · `plots/` · `data/` · `diagnostics/gate0_julia/`.
