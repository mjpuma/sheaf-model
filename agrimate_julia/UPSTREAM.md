# Upstream Agrimate (vendored)

This directory is a copy of the published Agrimate source from Kuhla,
Kubiczek, Puma, and Otto (2025).

## Attribution

- Kuhla, K., Kubiczek, P., Puma, M. J., & Otto, C. (2025).
  *Agrimate: a process-based model of global annual and intra-annual
  agricultural market dynamics*.
- Source snapshot: Zenodo **10.5281/zenodo.14022004**, folder
  `agrimate-equal-sales-penalty`.
- SHA-256 of `agrimate-model.zip`:
  `4853153bb216a39451a1d7d1b3de1865de8d5fbe758e63c074a1d8c4c8372088`
- Licence: **CC-BY 4.0** (see `LICENSE` in this directory).
- Authors of the Julia code: Patryk Kubiczek and co-authors as listed
  in `Project.toml`.

## What was copied

`src/`, `Project.toml`, `Manifest.toml`, `LICENSE`, and the upstream
README (as `README.upstream.md`). Run outputs and reconstructed input
CSVs were not copied. Package versions are pinned by `Manifest.toml`;
the interpreter is Julia 1.6.5 (Intel build, Rosetta on Apple Silicon).
Do not run `Pkg.update()` or `Pkg.resolve()`.

`AgrimateModel` is the local package at `src/AgrimateModel` (path pin in
the Manifest). Gate 0 verification: this tree, with the authors'
calibrated inputs inverted from their NetCDF, reproduces the published
wheat run (`diagnostics/gate0_julia/J10_authorbaseline.md`).

## Our changes

- `src/preprocess.jl` `generate_baseline_harvest_timeseries` /
  `generate_baseline_harvests`: if the harvest calendar has no mass
  (0/0 after aggregating a region with zero food-balance production),
  return zeros and **do not create that producer**. Wheat never hits
  this; rice Canada and Rest of Oceania have production 0, which made
  `X_star` NaN and Nash spin for 12 h. Not a substitution change.
