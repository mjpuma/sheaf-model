# Repository reorganization plan (pre-G0 completion)

Agreed after J10 established that the published Julia Agrimate code
reproduces the published wheat results on the authors' own calibration
(`gate0_julia/J10_authorbaseline.md`). Not yet executed — awaiting the end
of the J10 run and your sign-off on this plan.

## Decisions taken

1. **The Julia Agrimate code is driven directly** and becomes the model we
   modify for Gate 1. Python is reduced to drivers, input generation,
   scoring and plotting.
2. **`sheaf/agrimate/` (the Python rewrite) becomes legacy**, along with the
   other Python hosts (`dynamic_crop.py`, `legacy/`, `annual/`).
3. **Superseded material is deleted from the working tree after tagging**,
   not carried along. Git history and the tag keep it reachable.
4. **Governance docs are rewritten** to match reality: `AGENTS.md`,
   `CLAUDE.md`, `.cursor/rules/gate0-agrimate.mdc`,
   `diagnostics/GATE0_CONTRACT.md`.

## Licensing — vendoring is permitted

The paper code is **CC-BY 4.0** (`agrimate-equal-sales-penalty/LICENSE`),
so we may copy it into this repo, modify it, and redistribute, provided we
(a) keep their licence text, (b) attribute Kuhla et al. 2025 and Zenodo
14022004, and (c) state clearly what we changed. The code is ~600 KB
(`src/` 512 KB plus manifests), so it belongs in-tree rather than as an
external path. Every Gate 1 edit must be marked as ours; an untouched
upstream copy stays at the tagged commit for diffing.

## Target layout

```
README.md               model description, Agrimate citations, how to
                        parameterize and run
LICENSE                 ours
CITATION.cff            SHEAF + upstream Agrimate
agrimate_julia/         VENDORED paper code (CC-BY)
  LICENSE               their text, verbatim
  UPSTREAM.md           Zenodo DOI, sha256 of the zip, our change log
  src/, Project.toml, Manifest.toml
drivers/                our Python entry points
  run.py                scenario -> Julia invocation, logging, progress
  score.py              a run vs the author NetCDF (J4/J8/J9/J10 metrics)
inputs/                 input generation and parameterization
  from_paper.py         author-derived inputs (the J10 inverse)
  from_data.py          reconstruction from USDA/FAOSTAT/AMIS (J-series)
  parameterize.py       Agrimate's own routines where available, else ours
  pipelines/            the data readers kept from sheaf/ (see below)
  generated/            produced input sets, gitignored; manifests tracked
plots/                  every figure script
data/                   raw source data, unchanged
diagnostics/gate0_julia/  the J-series evidence, kept in full
tests/
```

## What is kept, and why

- `diagnostics/gate0_julia/` — the Gate 0 evidence base (J0–J10). Keep all.
- `data/` — raw USDA/FAOSTAT/AMIS/calendar inputs with their PROVENANCE
  files. Keep as is.
- From `sheaf/`, the **data pipelines are still used** by the input
  builders and must survive the deletion, repackaged under
  `inputs/pipelines/`: `data_usda.py` (12 importers), `data_faostat.py`,
  `calendar24.py`, `marketing_years.py`, `calibration.py`. A dependency
  check runs before anything is deleted; nothing goes until its importers
  are either migrated or deleted too.
- `scripts/` that belong to the J-series: the input builders, the
  verification scripts, the comparison scripts and the partial-run scorer.
  These move to `inputs/`, `drivers/` and `plots/`.

## What is deleted after tagging

- The Python hosts: `sheaf/agrimate/`, `sheaf/dynamic_*.py`,
  `sheaf/legacy/`, `sheaf/annual/`, `sheaf/core.py`, `demo.py`.
- The scripts that only drive those hosts: `score_subannual_*.py`,
  `score_legacy_crop.py`, `score_gate1_*.py`, `score_gate2_beta.py`,
  `run_subannual_wheat.py`, `score_ukraine_war.py` and the rest of that
  family (19 scripts import `sheaf.*` today; each is classified as migrate
  or delete before the cut).
- Superseded reports and figures: most of the 321 tracked files under
  `diagnostics/` outside `gate0_julia/`, the 110 under `figures/`, the 203
  under `overleaf/`, and `archive/legacy-gate0/`.
- Stray root outputs: `grist_results.csv`, `sheaf_results.csv`,
  `level1_hindcast.csv`.
- `audit_reports/`, `audit_prompts/`, `SHEAF_AUDIT_STATE.md` — the audit
  constitution describes a repository that will no longer exist; the parts
  worth keeping are folded into the rewritten governance docs.

## Order of operations

1. Finish the J10 run; score it; record the verdict.
2. Classify every tracked file as keep / migrate / delete, and write the
   list into this document for your review.
3. Tag the current tree (`pre-reorg-<date>`) and push the tag.
4. Vendor `agrimate_julia/` with `UPSTREAM.md` and a recorded sha256; a
   clean run from the vendored copy must reproduce J10 before anything is
   deleted.
5. Move the keepers into the new layout; run the dependency check; fix
   imports.
6. Delete the superseded set in one commit, so it is easy to read and to
   revert.
7. Rewrite `README.md` (model details, parameterization, run instructions,
   detailed Agrimate citations) and the governance docs.
8. Only then open Gate 1 work against the vendored code.

## Risks

- **Deleting something still load-bearing.** Mitigated by the
  classification pass in step 2 and the dependency check in step 5, and by
  the tag.
- **The vendored copy not reproducing J10.** Step 4 is a gate: the input
  set and a short run must match before deletions begin. The `Manifest.toml`
  pins the package versions, and Julia 1.6.5 stays the interpreter.
- **Losing the provenance of the J-series numbers.** The reports in
  `diagnostics/gate0_julia/` cite paths that the reorganization changes;
  step 7 adds a path-mapping note rather than rewriting the reports.
