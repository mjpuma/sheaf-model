# Repository reorganization plan (pre-G0 completion)

Agreed after J10 established that the published Julia Agrimate code
reproduces the published wheat results on the authors' own calibration
(`gate0_julia/J10_authorbaseline.md`). J10 is done. The Julia source is
vendored at `agrimate_julia/` (no edits). **Nothing has been deleted.**
**Executed 2026-10-07.** Tag `pre-reorg-20261007` marks the tree before
the cut. Keepers were moved, governance docs rewritten, and the delete
set removed in the following commit.

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
- From `sheaf/`, two **source-data readers** are reused, not the hosts.
  They already have no dependency on the Python model:

  * `data_usda.py` — USDA PSD, AMIS restrictions, LOWESS detrend
    (`load_psd_country`, `load_amis_restrictions`, `detrend_anomalies`)
  * `data_faostat.py` — FAOSTAT bilateral trade (`load_trade_matrix`)

  Those feed `scripts/build_agrimate_paper_inputs.py`, which is the
  adapter that writes Agrimate-format CSVs. The Julia code already ran on
  those CSVs (J2–J4), so they are format-compatible. They do **not**
  reproduce the unpublished author tables — that is the J4/J8/J9 finding,
  not a format problem.

  The J10 builder (`build_agrimate_authorbase_inputs.py`) does **not**
  use these readers at all: it inverts the author NetCDF. Keep both
  adapters: `inputs/from_paper.py` (J10 inverse) and `inputs/from_data.py`
  (reconstruction).

  `calendar24.py`, `marketing_years.py` and `calibration.py` are **not**
  used by any J-series builder. `calibration.py` imports the parked annual
  host and should be deleted with it unless a later pass needs its
  country-name table. Harvest calendars for new scenarios can use
  Agrimate's own `aggregate_harvest_distributions` /
  `generate_baseline_harvests` once the Julia source is vendored.
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

The run and the reorganization are independent. Destructive steps wait
for the J10 finish and for your review of the file list; everything
else can proceed now.

1. Put the J10 figure on the README (done, partial-run series through 2010).
2. Classify every tracked file as keep / migrate / delete, and write the
   list into this document for your review. *(can start now)*
3. Vendor `agrimate_julia/` with `UPSTREAM.md` and a recorded sha256.
   *(can start now; no deletion yet)*
4. Finish the J10 run; score it; record the verdict; refresh the README
   figure if the last two years change anything.
5. Tag the current tree (`pre-reorg-<date>`) and push the tag.
6. Move the keepers into the new layout; run the dependency check; fix
   imports. Confirm a short run from the vendored copy still matches J10.
7. Delete the superseded set in one commit, so it is easy to read and to
   revert.
8. Rewrite `README.md` (model details, parameterization, run instructions,
   detailed Agrimate citations) and the governance docs.
9. Only then open Gate 1 work against the vendored code.

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

## Classification (sign-off needed before deletion)

Tracked files today: ~870. After the cut the working tree should be on
the order of 150 (data + vendored Julia + J-series evidence + drivers).
Git history and the `pre-reorg` tag keep everything else.

### Keep as-is

| Path | Why |
|---|---|
| `data/` (39 files, with PROVENANCE) | raw USDA / FAOSTAT / AMIS / calendars |
| `diagnostics/gate0_julia/` (10 files) | J-series evidence |
| `diagnostics/GATE0_JULIA_PROMPTS.md` | how the verification was run |
| `diagnostics/REORG_PLAN.md` | this document |
| `diagnostics/GAME_CLOCK.md` | Gate 2 timing, still the destination |
| `diagnostics/PAPER_STACK.md` | citations |
| `diagnostics/POTSDAM_RESPONSE.md` | correspondence |
| `diagnostics/GATE1_PLAN.md`, `GATE1_HANDOFF.md`, `GATE2_PLAN.md` | future work |
| `diagnostics/DEVELOPMENT.md` | rewrite in place (stage G0-P) |
| `figures/gate0_j10_vs_author.png` | Gate 0 verification figure |
| `assets/` | logo |
| `LICENSE`, `.gitignore` | ours |
| `agrimate_julia/` | just vendored; no edits yet |
| `requirements.txt` | trim later, keep the file |

### Migrate (new path, same content)

| From | To |
|---|---|
| `sheaf/data_usda.py` | `inputs/pipelines/data_usda.py` |
| `sheaf/data_faostat.py` | `inputs/pipelines/data_faostat.py` |
| `scripts/build_agrimate_paper_inputs.py` | `inputs/from_data.py` |
| `scripts/build_agrimate_authorbase_inputs.py` | `inputs/from_paper.py` |
| `scripts/agrimate_harvest_quadrature.py` | `inputs/harvest_quadrature.py` |
| `scripts/export_agrimate_baseline_arrays.jl` | `inputs/export_baseline_arrays.jl` |
| `scripts/build_agrimate_authorparams_inputs.py` | `inputs/from_paper_params.py` (J8, keep for provenance) |
| `scripts/build_agrimate_authorrestr_inputs.jl` | `inputs/from_paper_restrictions.jl` (J9) |
| `scripts/check_agrimate_*.jl`, `compare_agrimate_julia_runs.jl`, `diagnose_agrimate_j9_gaps.jl`, `export_agrimate_author_params.jl`, `peek_agrimate_partial_run.jl` | `drivers/` |
| `scripts/plot_agrimate_j10.py` | `plots/j10_vs_author.py` |

### Rewrite in place (same path, new content)

`README.md`, `AGENTS.md`, `CLAUDE.md`, `ARCHITECTURE.md`, `VALIDATION.md`,
`.cursor/rules/gate0-agrimate.mdc`, `diagnostics/GATE0_CONTRACT.md`.

### Delete after the `pre-reorg` tag (~720 files)

**Python hosts and their tests**

- `sheaf/` except the two readers above (`agrimate/`, `annual/`, `legacy/`,
  `dynamic_*.py`, `core.py`, `calendar24.py`, `calibration.py`,
  `marketing_years.py`, `maps.py`, `seasonal.py`, `__init__.py`)
- `tests/` (all 8 files: they test the Python hosts)
- `demo.py`

**Scripts that only drive those hosts** (19 files)

`run_agrimate_validation.py`, `run_agrimate_wheat.py`,
`run_subannual_wheat.py`, `score_subannual_*.py`, `score_legacy_crop.py`,
`score_gate1*.py`, `score_gate2_beta.py`, `score_ukraine_war.py`,
`score_country_balance.py`, `score_whitepaper_maps.py`,
`validate_forcing.py`, `build_network.py`, `make_agrimate_comparison.py`,
`render_gate0_flows.py`, `assemble_whitepaper.py`, `fetch_external_data.py`,
`scripts/annual/`

**Python-host diagnostics and figures**

- `diagnostics/redteam/` (118), `diagnostics/gate0_prep/` (98),
  `diagnostics/gate0_agrimate/` (22)
- `diagnostics/gate0_{wheat,rice,maize,ukraine}_*` and the other
  snapshot CSVs / Python-host reports at the diagnostics root
- `diagnostics/GATE0_PROMPTS.md`, `GATE0_VALIDATION.md`,
  `GATE0_PARAMETERIZATION.md`, `GATE0_PER_CROP_PLAN.md`,
  `GATE0_SPEC_MATRIX.md`, `GATE0_FLOWS.md`, `GATE0_DEPARTURES.md`,
  `GATE0_DISCUSSION.md`, `GATE0_EXTENSION_PLAN.md`,
  `GATE0_CHANGE_CHECKLIST.md`, `GATE0_AGRIMATE_BRIEF.md`,
  `LEVEL1_INTERROGATION.md`
- `figures/` except `gate0_j10_vs_author.png` (110 files)
- `overleaf/` entire (203)
- `archive/` entire (88)
- `audit_reports/`, `audit_prompts/`, `SHEAF_AUDIT_STATE.md`
- `grist_results.csv`, `sheaf_results.csv`, `level1_hindcast.csv`

`calendar24.py` / `marketing_years.py` / `calibration.py` are in the
delete set because no J-series builder imports them. Harvest calendars
for new scenarios go through Agrimate's own `preprocess.jl`.

## Path mapping (J-series notes still use old names)

| Old | New |
|---|---|
| `scripts/build_agrimate_paper_inputs.py` | `inputs/from_data.py` |
| `scripts/build_agrimate_authorbase_inputs.py` | `inputs/from_paper.py` |
| `scripts/plot_agrimate_j10.py` | `plots/j10_vs_author.py` |
| `scripts/check_agrimate_*.jl`, `compare_agrimate_julia_runs.jl`, `peek_agrimate_partial_run.jl` | `drivers/` |
| `sheaf/data_usda.py`, `sheaf/data_faostat.py` | `inputs/pipelines/` |
| `sheaf/agrimate/`, `scripts/run_agrimate_*.py` | gone; tag `pre-reorg-20261007` |


