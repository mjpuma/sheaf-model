# J8 — published Agrimate code with the author's region parameters

Prepared 2026-10-02. **Startup check passed. The three long runs are
pending.** No score is reported here.

## Purpose

J4 found that the reconstructed region parameters are far from the
values the author code calibrated. ψ (target stock-to-use) is higher in 9
of the 11 key regions, for example USA 0.56 against 0.29. A_d* is 2–9× the
author's for most exporters. J8 isolates that gap. The published code runs
on the author's own region ψ, A_d* and A_c*, and every other input stays the
reconstructed one. This is an input-alignment experiment, not a retune.
Nothing is fitted. The values come straight from the author's output files.
Julia source and `Params` defaults are unchanged. This is not a
reproduction of the published run. The other inputs still differ (see
below).

## How the parameters reach the model

`simulate()` (src/simulation.jl, lines 104–124) reads
`parameters_baseline=2007-2009_crop=wheat_source=empirical.csv` because the
`Params` defaults for ψ, A_d_star and A_c_star are all `:empirical`. Columns
STU, A_d and A_c map to ψ, A_d_star and A_c_star. A_c also comes from this
file. `generate_empirical_params` (src/preprocess.jl, lines 74–110) fills
blank cells with the regional median, then the global median. It then takes
the consumption-weighted mean over each region's countries. The weights
are the country Consumption column of the unaggregated food-balance file.
The mean is rounded to 4 digits. `initialize_model` puts that value on each
region's consumer, with ψ multiplied by N_year. The unscaled region value is
written to the output NetCDF as `ψ`, `A_d_star` and `A_c_star`.

If every country in a region carries the same value v, the weighted mean is
v whatever the weights, including zero weights, as long as the region's
total consumption is positive. The author values are stored at 4 digits, so
the rounding gives them back exactly.

## What was copied from the author files

- `ψ`, `A_d_star` and `A_c_star` (dimension `region`, unitless, 28 regions)
  were read from the three wheat files in Zenodo data v3
  `hindcasting_analysis/raw_data/`. They are identical in all three
  scenarios (baseline, harvest, harvest + restrictions).
- `scripts/export_agrimate_author_params.jl` writes those values and the
  AgrimateEU28 + Egypt area→region map that `simulate()` builds to
  `agrimate-2025/j8_author_params/`.
- `scripts/build_agrimate_authorparams_inputs.py` writes
  `agrimate-equal-sales-penalty/data/agrimate_input_authorparams/`:
  - Six CSVs are byte copies of `data/agrimate_input/`: food balance, trade
    flows, harvest distributions, anomalies, trends and restrictions.
  - The parameters file has the same columns and rows (256 areas). Each
    area carries its region's author STU, A_d and A_c.
  - All 256 areas map to a region and every region has positive total
    consumption, so no area was left unmatched. The 138 blank STU/A_d cells
    of the reconstructed file are now filled with the region value.
- `data/agrimate_input/`, `data/netcdf/` and `data/agrimate_cache/` were not
  touched. Output goes to the new `agrimate-equal-sales-penalty/data_authorparams/`.
  `simulate()` puts both `netcdf/` and `agrimate_cache/` under `outputroot`.

## Startup check (t_max = 0)

`agrimate-2025/run_j8_authorparams_tmax0.jl` ran the Nash initialization
and returned. It took 2.5 min and exited 0. Its NetCDF was compared with
the author baseline file by `scripts/check_agrimate_authorparams_t0.jl`.

| Variable | max abs diff, J8 vs author | J2 (reconstructed) vs author |
|---|---|---|
| ψ | **0** | 0.27 |
| A_d_star | **0** | 0.454 |
| A_c_star | **0** | 0.196 |

All 28 regions match exactly. Key regions, author = J8 (J2 in brackets):

| Region | ψ | A_d* | A_c* |
|---|---|---|---|
| USA | 0.2909 (0.5612) | 0.0099 (0.0915) | 0.0644 (0.1500) |
| EU-28 | 0.1097 (0.1335) | 0.0124 (0.0714) | 0.1346 (0.1500) |
| Russia | 0.1124 (0.2570) | 0.0208 (0.0528) | 0.2797 (0.2500) |
| Ukraine | 0.1691 (0.2065) | 0.0344 (0.0548) | 0.4156 (0.4000) |
| Kazakhstan | 0.6327 (0.5789) | 0.0282 (0.0536) | 0.4460 (0.2500) |
| Argentina | 0.4163 (0.3541) | 0.0069 (0.0512) | 0.2827 (0.2500) |
| Australia | 0.5648 (0.6204) | 0.0132 (0.0573) | 0.0932 (0.1500) |
| Canada | 0.6371 (0.8547) | 0.0085 (0.0718) | 0.0914 (0.1500) |
| India | 0.0759 (0.1568) | 0.1035 (0.0539) | 0.2979 (0.4000) |
| China | 0.3708 (0.4349) | 0.0204 (0.0587) | 0.2171 (0.2500) |
| Egypt | 0.2294 (0.3093) | 0.1919 (0.2726) | 0.3361 (0.4000) |

## Remaining baseline gap (t = 0, vs author baseline file)

Annual sums of the 24-step baseline, thousand tonnes. Storages are the
annual mean.

| Region | Harvest J8 / A | Consumption J8 / A | Producer storage J8 / A | Consumer storage J8 / A (J2) |
|---|---|---|---|---|
| USA | 56,161 / 58,428 (−3.9 %) | 31,190 / 33,987 (−8.2 %) | 19,465 / 18,510 (+5.2 %) | 9,073 / 9,887 (17,504) |
| EU-28 | 134,523 / 129,125 (+4.2 %) | 123,218 / 119,417 (+3.2 %) | 54,794 / 43,066 (+27.2 %) | 13,517 / 13,100 (16,450) |
| Russia | 53,331 / 57,204 (−6.8 %) | 38,542 / 43,838 (−12.1 %) | 19,471 / 20,279 (−4.0 %) | 4,332 / 4,927 (9,905) |
| Argentina | 12,750 / 12,167 (+4.8 %) | 5,583 / 4,247 (+31.5 %) | 3,467 / 2,620 (+32.3 %) | 2,324 / 1,768 (1,977) |
| Canada | 24,682 / 23,495 (+5.1 %) | 7,295 / 7,427 (−1.8 %) | 9,110 / 6,345 (+43.6 %) | 4,648 / 4,732 (6,235) |
| India | 69,789 / 78,123 (−10.7 %) | 74,928 / 78,276 (−4.3 %) | 25,757 / 28,542 (−9.8 %) | 5,687 / 5,941 (11,749) |
| Egypt | 7,116 / 7,962 (−10.6 %) | 16,774 / 16,280 (+3.0 %) | 1,678 / 2,281 (−26.4 %) | 3,848 / 3,735 (5,188) |
| World | 632,149 / 631,646 (+0.1 %) | 632,149 / 631,646 (+0.1 %) | 224,577 / 203,948 (+10.1 %) | 134,918 / 134,419 (167,104) |

- **Consumer storage now matches up to the consumption gap.** It is ψ ×
  consumption, so with the author ψ the regional error equals the regional
  consumption error. The world total is +0.4 %, against +24 % in J2.
- **Baseline harvest, sales, demand, transactions, producer storage, the
  foreign-sales share, α_domestic and the baseline price are bit-identical
  to J2.** The parameters do not enter them. Baseline consumption moves by
  at most 11 kt per step through the consumer price (A_c), and its annual
  sums are unchanged to the thousand tonnes. The gap to the author is the
  food-balance, trade-flow and harvest-calendar gap from `INPUTS.md`:
  regional harvests are off by up to ±11 %, consumption by up to 31 %
  (Argentina), and world producer storage is +10 % (EU-28 +27 %, Canada
  +44 %). Producer storage depends on the harvest calendar.
- The baseline price is unchanged (1.0003 vs author 1.0002). The
  baseline consumer price differs by up to 0.019, against 0.021 in J2.
- Not addressed by J8: the different restricting regions (J4 data problem
  2), the Middle Africa producer (problem 3), code identity and wall time
  (problem 5).

## Long runs (pending)

The parent session launches these. Each wrapper mirrors `run_j3b.sh`:

- `agrimate-2025/run_j8_baseline.sh` → `run_j8_authorparams_baseline.jl`
- `agrimate-2025/run_j8_harvest.sh` → `run_j8_authorparams_harvest.jl`
- `agrimate-2025/run_j8_harvest_restrictions.sh` → `run_j8_authorparams_harvest_restrictions.jl`

Each `.jl` matches its J2/J3 runner except for `inputroot`
(`data/agrimate_input_authorparams`) and `outputroot`
(`data_authorparams`). Logs and timestamps go to `agrimate-2025/j8_<name>.{log,start,end}`.
The baseline run will overwrite the t_max = 0 NetCDF in
`data_authorparams/netcdf/`. A copy is kept at
`agrimate-2025/j8_author_params/tmax0_baseline.nc`. Generated output is
not committed. Scoring against the author files, J4-style, follows once the
runs finish.
