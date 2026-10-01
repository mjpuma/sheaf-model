# Gate 0 prompts — get the published Agrimate code running

Paste **exactly one** prompt per session. Each block below already includes
the preamble. Copy the whole fenced block. Do not skip. Do not open G1 or G2.

**Now:** wait for the J3 rerun to finish (`gate0_julia/J3.md`), then paste
**J4**. J2 baseline done (`gate0_julia/J2.md`).

## Where this stands

Julia 1.6.5 is installed. The 2025 code is unpacked. Author **outputs** are
on disk. Author **input** CSVs were not in the Zenodo data zip. SHEAF
already rebuilt those seven files from USDA / FAOSTAT / AMIS /
calendars. `AgrimateModel` now loads from the unpacked source. The wheat
baseline finished (`t_max = 312`, exit 0, 11 h 40 m). The first J3 attempt
failed on blank cells in the rebuilt harvest-anomaly CSV. The input builder
was fixed (zeros for non-producers, AMIS overlaps merged at the daily max
cut; see `gate0_julia/INPUTS.md`). The other four inputs were byte-identical,
so J2 stands. Both J3 runs were relaunched and are still running. Nothing
has been scored against the author NetCDF yet.

Gate 0 is finished only when a wheat run of this Julia code can be
compared with the author NetCDF. A mismatch is allowed and must be
reported. Do not retune to hide it. GitHub cleanup is **J7**, later.

## Paths (do not move these)

| What | Path |
|---|---|
| Julia 1.6.5 | `/Users/mjp38/GitHub/agrimate-2025/julia/julia-1.6.5/bin/julia` |
| Paper code | `/Users/mjp38/GitHub/agrimate-2025/agrimate-equal-sales-penalty/` |
| Local model source | `…/src/AgrimateModel/` (same UUID as the missing path) |
| Reconstructed inputs | `…/data/agrimate_input/` |
| Author output NetCDF | `/Users/mjp38/GitHub/agrimate-2025/data-v3/data/hindcasting_analysis/raw_data/` |

Invoke Julia as `arch -x86_64 <julia> --project=.`. Do not `brew install julia`.

## Wheat settings (every science run)

- `crops = "wheat"`
- `baseline = "2007-2009"`
- `regions = "AgrimateEU28"`
- `extra_regions = Dict("Egypt" => "EGY")`
- `start = Date(2000, 1, 1)`
- `t_max` must **not** be 0. `simulate()` returns after Nash init if `t_max == 0`.
  Default: `12 * 24 = 288` (2000 through 2011). If the author NetCDF has a
  different time length, use that.
- Harvest shock adds `production_anomalies = "FAOsince-2005"`
- Harvest + restrictions also adds `export_restrictions = "2007-2011"`

## Status

| ID | Prompt | Status |
|---|---|---|
| J0 | Install Julia 1.6.5 and instantiate | **done / stopped** — packages installed; model path is wrong (`gate0_julia/J0.md`) |
| J1 | Inventory author data zip | **done / stopped** — outputs present, inputs absent (`gate0_julia/J1.md`) |
| — | Rebuild input CSVs from SHEAF data | **done** — `scripts/build_agrimate_paper_inputs.py`, `gate0_julia/INPUTS.md` |
| J0b | Point `AgrimateModel` at the unpacked source and load it | **done** — loaded; `Pkg.develop` also resolved versions (`gate0_julia/J0b.md`) |
| J2 | One wheat baseline `simulate()` | **done** — `t_max = 312`, exit 0, 11 h 40 m (`gate0_julia/J2.md`) |
| **J3** | Harvest, then harvest + restrictions | **running** — first attempt failed on input blanks; inputs fixed, both runs relaunched (`gate0_julia/J3.md`) |
| J4 | Compare the three runs with the author NetCDF | **next**, after J3 finishes; this is the Gate 0 score |
| J5 | Python script that only launches that Julia run | after J3 has three files |
| J6 | Point the Gate 0 docs at this host | only if you accept J4 |
| J7 | GitHub cleanup | only after J6, and only when you ask |

---

## J0b — Load AgrimateModel (next)

```
You are running SHEAF Gate 0 from the published Agrimate code, not from
the Python rewrite in sheaf/agrimate/.

Read diagnostics/GATE0_JULIA_PROMPTS.md and diagnostics/gate0_julia/J0.md
before editing. Obey this prompt only.

Hard stops:
- Do not implement Gate 1 substitution or Gate 2 government games.
- Do not change Agrimate economics or parameters. Do not run
  Pkg.resolve() or Pkg.update().
- Do not brew-install a current Julia. Use Julia 1.6.5 under Rosetta.
- Do not clone GitLab main or develop-consumers.
- Do not retune anything to the Pink Sheet or to Bai's alpha_foreign=10.
- Do not delete, move, or rewrite sheaf/ Python, diagnostics contracts,
  or git history. Cleanup is J7 and is not this prompt.
- Do not commit the Agrimate zip, the data zip, or generated output.
- If the paper code fails, report the failure and stop. Do not fall back
  to sheaf/agrimate/ or sheaf/dynamic_crop.py.

One prompt, one session. Write a short note under
diagnostics/gate0_julia/ with what you ran and what happened.

Task J0b only. Make AgrimateModel load. Do not call simulate().

Read diagnostics/gate0_julia/J0.md. The paper Manifest.toml still has

  path = "/home/kikuhla/research/code/agrimate/src/AgrimateModel"

That directory is not on this Mac. The same package (uuid
4da19ca3-7b67-453c-a8f9-78404829864f) is already unpacked at

  /Users/mjp38/GitHub/agrimate-2025/agrimate-equal-sales-penalty/src/AgrimateModel

From that project directory, using Julia 1.6.5 under Rosetta, run only

  Pkg.develop(path="src/AgrimateModel")

That may rewrite the path line in Manifest.toml. Do not change versions.
Do not Pkg.resolve() or Pkg.update(). Then confirm

  using AgrimateModel
  println(pathof(AgrimateModel))

prints the local src/AgrimateModel path.

Write diagnostics/gate0_julia/J0b.md: the command, whether it loaded,
pathof(AgrimateModel), and the exact error if it failed. If it failed,
stop. Do not edit Julia source to get past it.
```

---

## J2 — Wheat baseline run

```
You are running SHEAF Gate 0 from the published Agrimate code, not from
the Python rewrite in sheaf/agrimate/.

Read diagnostics/GATE0_JULIA_PROMPTS.md and diagnostics/gate0_julia/J0b.md
before editing. Obey this prompt only.

Hard stops:
- Do not implement Gate 1 substitution or Gate 2 government games.
- Do not change Agrimate economics or parameters. Do not run
  Pkg.resolve() or Pkg.update().
- Do not brew-install a current Julia. Use Julia 1.6.5 under Rosetta.
- Do not clone GitLab main or develop-consumers.
- Do not retune anything to the Pink Sheet or to Bai's alpha_foreign=10.
- Do not delete, move, or rewrite sheaf/ Python, diagnostics contracts,
  or git history. Cleanup is J7 and is not this prompt.
- Do not commit the Agrimate zip, the data zip, or generated output.
- If the paper code fails, report the failure and stop. Do not fall back
  to sheaf/agrimate/ or sheaf/dynamic_crop.py.

One prompt, one session. Write a short note under
diagnostics/gate0_julia/ with what you ran and what happened.

Task J2 only. Read J0b.md first. If AgrimateModel did not load, write
that in J2.md and stop.

Call simulate() once, baseline only, from
/Users/mjp38/GitHub/agrimate-2025/agrimate-equal-sales-penalty/ using
Julia 1.6.5 under Rosetta. Inputs are already in data/agrimate_input/
(see diagnostics/gate0_julia/INPUTS.md). They are a SHEAF reconstruction,
not the author tables. Use them. Do not rebuild them.

Settings:
- crops = "wheat"
- baseline = "2007-2009"
- regions = "AgrimateEU28"
- extra_regions = Dict("Egypt" => "EGY")
- start = Date(2000, 1, 1)
- production_anomalies empty
- export_restrictions empty
- t_max = 288 unless the author baseline NetCDF in
  /Users/mjp38/GitHub/agrimate-2025/data-v3/data/hindcasting_analysis/raw_data/
  has a different step count; then use that count
- leave every other parameter at the code default

Write diagnostics/gate0_julia/J2.md: whether it finished, runtime, output
path, t_max used, and any error. If it fails, quote the error and stop.
Do not edit the Julia source to get past it.
```

---

## J3 — Harvest, then harvest plus restrictions

```
You are running SHEAF Gate 0 from the published Agrimate code, not from
the Python rewrite in sheaf/agrimate/.

Read diagnostics/GATE0_JULIA_PROMPTS.md and diagnostics/gate0_julia/J2.md
before editing. Obey this prompt only.

Hard stops:
- Do not implement Gate 1 substitution or Gate 2 government games.
- Do not change Agrimate economics or parameters. Do not run
  Pkg.resolve() or Pkg.update().
- Do not brew-install a current Julia. Use Julia 1.6.5 under Rosetta.
- Do not clone GitLab main or develop-consumers.
- Do not retune anything to the Pink Sheet or to Bai's alpha_foreign=10.
- Do not delete, move, or rewrite sheaf/ Python, diagnostics contracts,
  or git history. Cleanup is J7 and is not this prompt.
- Do not commit the Agrimate zip, the data zip, or generated output.
- If the paper code fails, report the failure and stop. Do not fall back
  to sheaf/agrimate/ or sheaf/dynamic_crop.py.

One prompt, one session. Write a short note under
diagnostics/gate0_julia/ with what you ran and what happened.

Task J3 only. Read J2.md first. If J2 did not finish, stop.

Run two more simulate() calls with the same Julia, project, inputs,
crops, baseline, regions, Egypt extra region, start, and t_max as J2.
Change only:

1. production_anomalies = "FAOsince-2005"
2. that anomaly plus export_restrictions = "2007-2011"

Keep the J2 baseline file. Do not rerun it unless J2 produced no file.

Write diagnostics/gate0_julia/J3.md with the three output paths, runtimes,
and whether each run finished. Do not score them yet. Do not change
parameters between runs.
```

---

## J4 — Compare with the author NetCDF (Gate 0 score)

```
You are running SHEAF Gate 0 from the published Agrimate code, not from
the Python rewrite in sheaf/agrimate/.

Read diagnostics/GATE0_JULIA_PROMPTS.md, diagnostics/gate0_julia/J1.md,
diagnostics/gate0_julia/INPUTS.md, and diagnostics/gate0_julia/J3.md
before editing. Obey this prompt only.

Hard stops:
- Do not implement Gate 1 substitution or Gate 2 government games.
- Do not change Agrimate economics or parameters. Do not run
  Pkg.resolve() or Pkg.update().
- Do not brew-install a current Julia. Use Julia 1.6.5 under Rosetta.
- Do not clone GitLab main or develop-consumers.
- Do not retune anything to the Pink Sheet or to Bai's alpha_foreign=10.
- Do not delete, move, or rewrite sheaf/ Python, diagnostics contracts,
  or git history. Cleanup is J7 and is not this prompt.
- Do not commit the Agrimate zip, the data zip, or generated output.
- If the paper code fails, report the failure and stop. Do not fall back
  to sheaf/agrimate/ or sheaf/dynamic_crop.py.

One prompt, one session. Write a short note under
diagnostics/gate0_julia/ with what you ran and what happened.

Task J4 only. This is the Gate 0 score. Read J3.md first. If the three
local files are missing, stop.

Compare the three local runs with the three author NetCDF files in

  /Users/mjp38/GitHub/agrimate-2025/data-v3/data/hindcasting_analysis/raw_data/

baseline, production failure, and production failure plus export
restrictions. Use the same years, regions, and variables the author
files contain. Report prices, production, consumption, and stocks.

The local inputs are a SHEAF reconstruction (INPUTS.md), not the author
tables. A gap is expected. Do not retune to shrink it. Do not compare
with sheaf/agrimate/ except to label that host as a different program.

Write diagnostics/gate0_julia/J4.md:
- what matches
- what does not, with the size of the gap
- whether this is a reproduction of the published wheat run, or only
  a run of the published code on reconstructed inputs
A failed match stays a failed match.
```

---

## J5 — Python caller

```
You are running SHEAF Gate 0 from the published Agrimate code, not from
the Python rewrite in sheaf/agrimate/.

Read diagnostics/GATE0_JULIA_PROMPTS.md and diagnostics/gate0_julia/J4.md
before editing. Obey this prompt only.

Hard stops:
- Do not implement Gate 1 substitution or Gate 2 government games.
- Do not change Agrimate economics or parameters. Do not run
  Pkg.resolve() or Pkg.update().
- Do not brew-install a current Julia. Use Julia 1.6.5 under Rosetta.
- Do not clone GitLab main or develop-consumers.
- Do not retune anything to the Pink Sheet or to Bai's alpha_foreign=10.
- Do not delete, move, or rewrite sheaf/ Python, diagnostics contracts,
  or git history. Cleanup is J7 and is not this prompt.
- Do not commit the Agrimate zip, the data zip, or generated output.
- If the paper code fails, report the failure and stop. Do not fall back
  to sheaf/agrimate/ or sheaf/dynamic_crop.py.

One prompt, one session. Write a short note under
diagnostics/gate0_julia/ with what you ran and what happened.

Task J5 only. Read J3.md and J4.md first. If J3 never produced three
output files, stop.

Add one Python script, scripts/run_agrimate_paper.py, that:
- calls the Julia 1.6.5 binary under Rosetta
- uses the unpacked paper project and data/agrimate_input
- runs one named scenario: baseline, harvest, or harvest_restrictions
- prints the output path and does not reimplement the market

Document the command at the top of the script. Run the baseline through
the script once and confirm it launches the same Julia project.

Do not change Julia source. Do not import sheaf.agrimate or
sheaf.dynamic_crop. Write diagnostics/gate0_julia/J5.md with the command
and the check.
```

---

## J6 — Point the docs at this host

```
You are running SHEAF Gate 0 from the published Agrimate code, not from
the Python rewrite in sheaf/agrimate/.

Read diagnostics/GATE0_JULIA_PROMPTS.md and diagnostics/gate0_julia/J4.md
before editing. Obey this prompt only.

Hard stops:
- Do not implement Gate 1 substitution or Gate 2 government games.
- Do not change Agrimate economics or parameters. Do not run
  Pkg.resolve() or Pkg.update().
- Do not brew-install a current Julia. Use Julia 1.6.5 under Rosetta.
- Do not clone GitLab main or develop-consumers.
- Do not retune anything to the Pink Sheet or to Bai's alpha_foreign=10.
- Do not delete, move, or rewrite sheaf/ Python, diagnostics contracts,
  or git history. Cleanup is J7 and is not this prompt.
- Do not commit the Agrimate zip, the data zip, or generated output.
- If the paper code fails, report the failure and stop. Do not fall back
  to sheaf/agrimate/ or sheaf/dynamic_crop.py.

One prompt, one session. Write a short note under
diagnostics/gate0_julia/ with what you ran and what happened.

Task J6 only. Do this only if J4.md is written and you have been told
to accept that score. If J4 did not run, stop and leave the docs alone.

Update diagnostics/GATE0_CONTRACT.md, diagnostics/DEVELOPMENT.md,
AGENTS.md, and .cursor/rules/gate0-agrimate.mdc so Gate 0 means: the
published Agrimate Julia code, Julia 1.6.5, Zenodo 14022004, invoked by
scripts/run_agrimate_paper.py, with inputs labelled as author or
reconstructed.

State plainly that sheaf/agrimate/ is the paused Python rewrite and is
not the host. Leave G1 and G2 blocked. Do not describe them as started.
Do not delete code in this prompt.
```

---

## J7 — GitHub cleanup

```
You are running SHEAF Gate 0 from the published Agrimate code, not from
the Python rewrite in sheaf/agrimate/.

Read diagnostics/GATE0_JULIA_PROMPTS.md before editing. Obey this prompt
only.

Hard stops:
- Do not implement Gate 1 substitution or Gate 2 government games.
- Do not change Agrimate economics or parameters. Do not run
  Pkg.resolve() or Pkg.update().
- Do not brew-install a current Julia. Use Julia 1.6.5 under Rosetta.
- Do not clone GitLab main or develop-consumers.
- Do not retune anything to the Pink Sheet or to Bai's alpha_foreign=10.
- Do not delete, move, or rewrite sheaf/ Python, diagnostics contracts,
  or git history except as this prompt lists. Do not push.
- Do not commit the Agrimate zip, the data zip, or generated output.
- If the paper code fails, report the failure and stop. Do not fall back
  to sheaf/agrimate/ or sheaf/dynamic_crop.py.

One prompt, one session. Write a short note under
diagnostics/gate0_julia/ with what you ran and what happened.

Task J7 only. Do this only after J6 has landed and you have been asked
to clean the repo. Do not push.

Goal: the repo's default path is the published Agrimate run. History
stays. The Python rewrite and the older crisis map stop looking like
the current model.

1. Bring the paper code in as a vendored tree or submodule with its
   LICENSE files intact (repo CC-BY-4.0, AgrimateModel MIT). Do not
   commit data.zip, NetCDF outputs, or the Julia binary.
2. Move sheaf/agrimate/, sheaf/legacy/, sheaf/dynamic_crop.py,
   sheaf/dynamic_coupled.py, sheaf/dynamic_policy.py, and sheaf/annual/
   under archive/ and fix imports so the default entry point is
   scripts/run_agrimate_paper.py. Keep sheaf/data_usda.py and
   sheaf/data_faostat.py where they are, labelled as SHEAF data tools,
   not as Agrimate inputs.
3. Point README, AGENTS.md, and the Gate 0 docs at the Julia host.
4. Leave G1 and G2 unimplemented.

Show the file moves in the J7 note before committing. Commit only if
asked. Do not force-push.
```
