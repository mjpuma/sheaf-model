# Gate 0 prompts — published Agrimate code

Paste **exactly one** prompt per session. Do not skip. Do not open G1 or G2.
The Python rewrite queue in [`GATE0_PROMPTS.md`](GATE0_PROMPTS.md) is paused.

**Now:** J0 is still blocked (`AgrimateModel` does not load;
[`gate0_julia/J0.md`](gate0_julia/J0.md)). Author inputs were absent
([`gate0_julia/J1.md`](gate0_julia/J1.md)). A SHEAF reconstruction of
those CSVs is in [`gate0_julia/INPUTS.md`](gate0_julia/INPUTS.md). Do not
paste J2 until `AgrimateModel` loads.

Gate 0 is finished only when a wheat run of the published code matches the
author output. GitHub cleanup is **J7**, and only after that match.

## What this track uses

- Paper: Kuhla, Kubiczek, and Otto, *Ecological Economics* 231 (2025) 108546.
- Code: Zenodo [10.5281/zenodo.14022004](https://doi.org/10.5281/zenodo.14022004)
  (`agrimate-model.zip`, 165 KB, 1 Nov 2024). Inside, the folder is
  `agrimate-equal-sales-penalty/`. The packed git commit is `79951111`.
  `Manifest.toml` pins **Julia 1.6.5**. There is no `scripts/` directory.
  The run function is `simulate()` in `src/simulation.jl`.
- Author results: Zenodo
  [10.5281/zenodo.14870541](https://doi.org/10.5281/zenodo.14870541)
  (data v3, 14 Feb 2025, `data.zip`, about 1.55 GB). This is the latest
  data record. The older 150 MB record `10688435` is v1 and is not the
  comparison target. The v3 description lists **output** NetCDF and
  figures. It may not contain the input CSVs `simulate()` needs. J1
  checks that before any science run.
- Do not clone GitLab `main` or `develop-consumers`. Those are not this
  archive.
- This Mac is Apple Silicon (`arm64`). Julia 1.6.5 has an Intel Mac
  build only. Run that build under Rosetta. Do not `brew install julia`.
  A current Julia will not match the paper manifest.
- Keep the code and the data zip **outside** this git repo until J7:
  `/Users/mjp38/GitHub/agrimate-2025/`. Do not unpack into
  `sheaf-model/agrimate/` (that path is reserved for local paper PDFs and
  is gitignored).

Paper wheat scenarios, read off the author output filenames:

| Scenario | `simulate` settings |
|---|---|
| Baseline | `crops="wheat"`, `baseline="2007-2009"`, `regions="AgrimateEU28"`, `extra_regions` Egypt = EGY, `start=2000-01-01`, no production anomalies, no export restrictions |
| Harvest shock | same, plus `production_anomalies="FAOsince-2005"` |
| Harvest + restrictions | same, plus `export_restrictions="2007-2011"` |

`simulate()` reads CSVs from an input root (default `data/agrimate_input`
under the Agrimate project, or `AGRIMATE_INPUT_ROOT`). Expected names
include `food-balance_baseline=2007-2009_crop=wheat.csv`,
`trade-flows_baseline=2007-2009_crop=wheat.csv`, and
`harvest-distributions_crop=wheat.csv`, plus anomaly, trend, parameter,
and export-restriction files when those scenarios are turned on.

## Status

| ID | Prompt | Status |
|---|---|---|
| **J0** | Install Julia 1.6.5 and instantiate the paper code | **stopped** — see `gate0_julia/J0.md` |
| J1 | Download data v3 and separate inputs from author outputs | **stopped** — inputs absent; see `gate0_julia/J1.md` |
| J2 | One wheat baseline `simulate()` | queued; stop if J1 found no inputs |
| J3 | The three paper scenarios | queued |
| J4 | Compare the run with the author NetCDF | queued; this is the Gate 0 test |
| J5 | Python script that calls that Julia run | after J4 runs, even if the match is imperfect |
| J6 | Point the Gate 0 docs at this host | only if you accept the J4 match |
| J7 | GitHub cleanup | only after J6, and only when you ask |

## Shared preamble (prepend to every prompt)

```
You are running SHEAF Gate 0 from the published Agrimate code, not from
the Python rewrite in sheaf/agrimate/.

Read diagnostics/GATE0_JULIA_PROMPTS.md before editing. Obey this prompt
only.

Hard stops:
- Do not implement Gate 1 substitution or Gate 2 government games.
- Do not edit Agrimate economics, parameters, or Manifest.toml to make a
  run succeed. Do not run Pkg.resolve() or Pkg.update().
- Do not brew-install a current Julia. Use Julia 1.6.5.
- Do not clone GitLab main or develop-consumers.
- Do not retune anything to the Pink Sheet or to Bai's alpha_foreign=10.
- Do not delete, move, or rewrite sheaf/ Python, diagnostics contracts,
  or git history. Cleanup is J7 and is not this prompt.
- Do not commit the Agrimate zip, the data zip, or generated output.
- If the paper code fails, report the failure and stop. Do not fall back
  to sheaf/agrimate/ or sheaf/dynamic_crop.py.

One prompt, one session. Write a short note under
diagnostics/gate0_julia/ with what you ran and what happened.
```

---

## J0 — Install Julia 1.6.5 and instantiate

```
[SHARED PREAMBLE]

Task J0 only. Get the published code to instantiate. Do not run a
wheat scenario.

1. Confirm the machine is arm64. Install Rosetta if `arch -x86_64 uname -m`
   fails.
2. Download the Intel Mac tarball of Julia 1.6.5 (the aarch64 1.6.5 URL
   404s) and unpack it under /Users/mjp38/GitHub/agrimate-2025/julia/.
   Invoke it as `arch -x86_64 <julia> --version` and confirm 1.6.5.
3. Download https://doi.org/10.5281/zenodo.14022004
   (file agrimate-model.zip) into that same parent folder and unzip it.
   Confirm the tree is agrimate-equal-sales-penalty/ and that
   Manifest.toml contains julia_version = "1.6.5".
4. From that project directory, run:
   arch -x86_64 <julia> --project=. -e 'using Pkg; Pkg.instantiate()'
   Let it finish. First instantiate can take a long time.
5. Confirm `using AgrimateModel` loads. Do not call simulate().

Write diagnostics/gate0_julia/J0.md: Julia path, version, instantiate
success or the exact error, and the path of the unpacked project.
If instantiate fails, stop. Do not upgrade packages.
```

---

## J1 — Inventory the author data

```
[SHARED PREAMBLE]

Task J1 only. Do not call simulate().

Download data v3, doi 10.5281/zenodo.14870541 (data.zip, about 1.55 GB),
to /Users/mjp38/GitHub/agrimate-2025/data-v3/. Unzip it outside the
SHEAF repo. Do not download the older 150 MB record 10688435 unless v3
is missing the files below.

Read src/simulation.jl in the unpacked paper code and list every input
filename simulate() will request for the three paper scenarios in
diagnostics/GATE0_JULIA_PROMPTS.md (wheat, baseline 2007-2009,
AgrimateEU28, Egypt as EGY, start 2000-01-01, FAOsince-2005,
export restrictions 2007-2011).

Then classify the zip:
- author output NetCDF (the three scenario files named in the Zenodo
  description, plus any hindcast figures)
- input CSVs that match those simulate() names
- anything else

Write diagnostics/gate0_julia/J1.md with that classification and the
exact paths. If the input CSVs are absent, say so in the first line and
stop. Do not build substitute inputs from USDA or FAOSTAT. Do not unpack
the zip into the SHEAF repo.
```

---

## J2 — One wheat baseline run

```
[SHARED PREAMBLE]

Task J2 only. Read diagnostics/gate0_julia/J0.md and J1.md first.

If J1 found no input CSVs, write that in J2.md and stop. Do not invent
inputs.

If the inputs exist, point AGRIMATE_INPUT_ROOT at them and call
simulate() once, for the baseline row only:

- crops = wheat
- baseline = 2007-2009
- regions = AgrimateEU28
- extra_regions = Egypt as EGY
- start = 2000-01-01
- production_anomalies empty
- export_restrictions empty

Use Julia 1.6.5 under Rosetta and the paper project. Leave every other
parameter at the code default. Save the log and the output path.

Write diagnostics/gate0_julia/J2.md: whether it finished, runtime, output
path, and any error. If it fails, quote the error and stop. Do not edit
the Julia source to get past it.
```

---

## J3 — Three paper scenarios

```
[SHARED PREAMBLE]

Task J3 only. Read J2.md first. If J2 did not finish, stop.

Run the other two paper scenarios with the same fixed settings as J2,
changing only the switch named in diagnostics/GATE0_JULIA_PROMPTS.md:

1. production_anomalies = FAOsince-2005
2. that anomaly plus export_restrictions = 2007-2011

Keep the J2 baseline output. Do not rerun it unless J2 produced no file.

Write diagnostics/gate0_julia/J3.md with the three output paths, runtimes,
and whether each run finished. Do not score them yet. Do not change
parameters between runs.
```

---

## J4 — Compare with the author NetCDF

```
[SHARED PREAMBLE]

Task J4 only. This is the Gate 0 test. Read J1.md and J3.md first.

Compare the three local runs with the three author NetCDF files in data
v3 (baseline, production failure, production failure plus export
restrictions). Use the same years, regions, and variables the author
files contain. Report prices, production, consumption, and stocks.

Write diagnostics/gate0_julia/J4.md:
- what matches
- what does not, with the size of the gap
- whether you can call this a reproduction of the published wheat run

Do not retune parameters to shrink a gap. Do not compare with the Python
host in sheaf/agrimate/ except to label that host as a different program.
A failed match stays a failed match.
```

---

## J5 — Python caller

```
[SHARED PREAMBLE]

Task J5 only. Read J4.md first. If J3 never produced three output files,
stop.

Add one Python script, scripts/run_agrimate_paper.py, that:
- calls the Julia 1.6.5 binary under Rosetta
- uses the unpacked paper project and AGRIMATE_INPUT_ROOT
- runs one named scenario: baseline, harvest, or harvest_restrictions
- prints the output path and does not reimplement the market

Document the command at the top of the script. Run the baseline through
the script once and confirm the output matches the J2 file.

Do not change Julia source. Do not import sheaf.agrimate or
sheaf.dynamic_crop. Write diagnostics/gate0_julia/J5.md with the command
and the check.
```

---

## J6 — Point the docs at this host

```
[SHARED PREAMBLE]

Task J6 only. Do this only if J4.md says the wheat run reproduces the
author output and you have been told to accept it. If J4 did not pass,
stop and leave the docs alone.

Update diagnostics/GATE0_CONTRACT.md, diagnostics/DEVELOPMENT.md,
AGENTS.md, and .cursor/rules/gate0-agrimate.mdc so Gate 0 means: the
published Agrimate Julia code, Julia 1.6.5, Zenodo 14022004 and data v3
14870541, invoked by scripts/run_agrimate_paper.py.

State plainly that sheaf/agrimate/ is the paused Python rewrite and is
not the host. Leave G1 and G2 blocked. Do not describe them as started.
Do not delete code in this prompt.
```

---

## J7 — GitHub cleanup

```
[SHARED PREAMBLE]

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
