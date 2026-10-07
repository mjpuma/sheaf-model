# SHEAF

<p align="center">
  <img src="assets/SHEAF_Model_logo.png" width="260" alt="SHEAF Model logo — a wheat ear, rice panicle, and corn cob bound together in a green ring">
</p>

> **sheaf** &nbsp;/ʃiːf/&nbsp;
> — *(agriculture)* a bundle of cereal stalks bound together after the harvest;
> — *(mathematics)* a structure that consistently glues locally defined data into a coherent global whole.

**S**ubstitution, **H**eterogeneous agents, **E**quilibrium, **A**nd **F**ragility:
a country-level, multi-commodity, game-theoretic network model of global grain
trade. It sits in the TWIST → Agrimate lineage. Those models already do storage
(and Agrimate already does a trade network). SHEAF exists because two
first-order pieces of crisis dynamics are still missing:

1. **Strategy.** Exporters restrict in a crisis, and those restrictions move
   world prices. Agrimate takes the restriction schedule as given. SHEAF’s
   destination is an *endogenous* export-restriction game among governments.
2. **Substitution.** Wheat, rice, and maize are linked on the demand side.
   Single-commodity models wall each grain off.

Both sit on Agrimate’s **24-step-per-year** market. Gate 0 is both switches
off (AMIS diary, one crop). Gate 1 is substitution on. Gate 2 is the
restriction game (types slow, actions on that same clock;
[`diagnostics/GAME_CLOCK.md`](diagnostics/GAME_CLOCK.md)). **Gate 1 and Gate 2
stay off until Gate 0 is accepted.**

The Gate 0 host is the **published Julia Agrimate code**, vendored at
[`agrimate_julia/`](agrimate_julia/) (Kuhla, Kubiczek, Puma, and Otto 2025;
Zenodo [10.5281/zenodo.14022004](https://doi.org/10.5281/zenodo.14022004);
CC-BY 4.0). Python here is drivers, input generation, scoring, and plots.

## Gate 0 status

The published code, given the authors’ own calibration, **reproduces their
published wheat run**
([`diagnostics/gate0_julia/J10_authorbaseline.md`](diagnostics/gate0_julia/J10_authorbaseline.md)).
The 2007/08 world-price ratio is 1.359 against their 1.361, 2010/11 is 1.213
against 1.219, the May 2008 peak is 2.216 against 2.223, monthly prices
correlate at 1.000, and end-of-year stocks are within 0.5 % every year
2000–2012.

![J10: SHEAF run of the published code versus Kuhla et al. 2025](figures/gate0_j10_vs_author.png)

*Wheat, harvest shocks plus export restrictions, on the authors’ own
calibration. Grey is the published NetCDF; red is our run of the published
code. The authors did not publish their input tables; J10 inverts their
output arrays back into the CSVs the code reads. That is a verification of
the code path. Reconstructing those tables from USDA / FAOSTAT / AMIS (J4,
J8, J9) ran the same code and did **not** reproduce the published
magnitudes — stocks +23 %, 2007/08 ratio 1.25 versus 1.36 — so public-data
reproducibility remains an open limitation.*

Gate 0 is **not** accepted yet — that is your call
([`diagnostics/DEVELOPMENT.md`](diagnostics/DEVELOPMENT.md) stage G0-P).

The tree immediately before this layout is tagged
[`pre-reorg-20261007`](https://github.com/mjpuma/sheaf-model/releases/tag/pre-reorg-20261007).

## Cite

Kuhla, K., Kubiczek, P., Puma, M. J., & Otto, C. (2025). Agrimate: a
process-based model of global annual and intra-annual agricultural market
dynamics. *Ecological Economics*, 231, 108546.
https://doi.org/10.1016/j.ecolecon.2025.108546

Source snapshot used here: Kubiczek et al., Zenodo
[10.5281/zenodo.14022004](https://doi.org/10.5281/zenodo.14022004), folder
`agrimate-equal-sales-penalty`, CC-BY 4.0. SHA-256 of the zip is in
[`agrimate_julia/UPSTREAM.md`](agrimate_julia/UPSTREAM.md). Every SHEAF edit
to that source is listed there.

## Layout

```
agrimate_julia/     vendored Agrimate (do not Pkg.update)
drivers/            launch, score, J-series checkers
inputs/             input builders and USDA/FAOSTAT/AMIS readers
  from_paper.py     invert the author NetCDF (J10)
  from_data.py      reconstruct from public data (J4)
  pipelines/        data_usda.py, data_faostat.py
  generated/        written CSVs (gitignored)
plots/              figure scripts
data/               raw USDA / FAOSTAT / AMIS / calendars
diagnostics/gate0_julia/   J0–J10 evidence
```

## Parameterize

Agrimate’s own parameterization lives in
`agrimate_julia/src/preprocess.jl`
(`aggregate_areas`, `infer_trade_flows`, `generate_empirical_params`,
`aggregate_harvest_distributions`, `generate_baseline_harvests`,
`apply_cutoffs_to_trade_network`, restriction aggregation). New scenarios
should call those, not reimplement them. Our Python only has to write the
seven CSVs those functions already consume:

| CSV | Role |
|---|---|
| `food-balance_*.csv` | regional production, consumption, imports |
| `trade-flows_*.csv` | country-level bilateral flows |
| `harvest-distributions_*.csv` | 365 daily harvest shares |
| `harvest-anomalies_*.csv`, `harvest-trends_*.csv` | harvest forcing |
| `parameters_*.csv` | ψ, A_d*, A_c* |
| `export-restrictions_*.csv` | country intervals `Exporter, From, To, Value` |

Two builders:

```bash
# Author calibration (reproduces the published wheat run; needs their NetCDF)
python inputs/from_paper.py

# Public-data reconstruction (USDA PSD, FAOSTAT E0, AMIS). Runs the model;
# does not reproduce the published magnitudes.
PYTHONPATH=. python inputs/from_data.py
```

`from_data.py` reads `inputs/pipelines/data_usda.py` and
`data_faostat.py`. Region maps come from
`agrimate_julia/src/regions.jl`.

## Run

Julia **1.6.5** only. On Apple Silicon the Intel build runs under Rosetta.
Do not `Pkg.update()` / `Pkg.resolve()`.

```bash
# Default: wheat, 2007–2009 baseline, AgrimateEU28 + Egypt, 312 steps
python drivers/run.py --anomalies --restrictions --t-max 312

# Score a NetCDF against the author wheat file (same metrics as J4/J8/J9/J10)
python drivers/score.py path/to/output.nc

# Figure
python plots/j10_vs_author.py
```

Set `AGRIMATE_JULIA` if the 1.6.5 binary is not at the default path
(`/Users/mjp38/GitHub/agrimate-2025/julia/julia-1.6.5/bin/julia`).
`AGRIMATE_INPUT` / `AGRIMATE_OUTPUT` override the CSV and NetCDF roots.

A full 312-step wheat run is serial (one NLopt solve per producer per
step) and takes on the order of 12–20 hours of awake time, longer through
the 2010–11 window.

## What this is not

- The Python rewrite formerly in `sheaf/agrimate/` is gone. Restore it from
  tag `pre-reorg-20261007` if you need it.
- Do not implement Gate 1 substitution or Gate 2 government games until
  stage G0-P is accepted.
- Do not retune Agrimate economics or parameters to the Pink Sheet.
