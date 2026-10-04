# J9 — published Agrimate code with the author's export restrictions

Prepared 2026-10-03. **Run pending.** Only the harvest + restrictions
scenario will be rerun.

## Purpose

J4 and J8 restrict a different set of regions from the author's run: 7
local against 10 author, with 5 in common (J4 data problem 2). J9 tests
whether the published code reproduces the author's wheat run once it is
given the author's own per-region restriction series. It builds on J8,
which already uses the author's region ψ, A_d* and A_c*. This is an
input-alignment experiment, not a retune. The values come straight from
the author's output file, and nothing is fitted. The Julia source and the
`Params` defaults are unchanged. Gate 1 and Gate 2 are not touched.

Source: `export restriction` (dimensions time × region) in the author's
`agrimate_baseline=2007-2009_export_restrictions=2007-2011_extra_regions=(Egypt=EGY)_production_anomalies=FAOsince-2005_regions=AgrimateEU28_start=2000-01-01.nc`
(Zenodo data v3, `hindcasting_analysis/raw_data/`).

## How restrictions reach the model

`simulate()` (src/simulation.jl, lines 252–274) and src/preprocess.jl:

1. **Country file to region rows.** `aggregate_export_restrictions`
   (lines 113–201) reads the country CSV (`Exporter,From,To,Value`). Each
   row's Value is multiplied by
   `export_fraction = export_area / export_region`. `export_area` is the
   country's exports to areas outside its region, taken from the
   unaggregated trade-flow file. `export_region` is the region's exports to
   other regions, taken from the aggregated and inferred flows. If the
   region exports nothing, the fraction is 0. Rows with value 0 are dropped.
   The input Value itself is never clipped, so a row value above 1 is
   allowed.
2. **Overlaps.** Within each region, the From/To dates split time into
   sub-periods. Overlapping rows are **summed** in each sub-period. Equal
   neighbours are merged, and the final value is **capped at 1**
   (`min.(final_values, 1.)`).
3. **Dates to steps.** `date_to_timestep` (lines 503–508) uses
   `n = floor((doy − 0.5) · 24 / 365) + 1`, where doy is the day of year in
   the non-leap year 2001. It then sets `t = (year − 2000) · 24 + n`
   (start 2000-01-01, 24 steps per year). Step n of a year runs from day
   `(n − 1) · 365/24 + 0.5` to day `n · 365/24 + 0.5`, which is 15–16 days.
   Step 1 is 1–15 January. A Feb 29 endpoint throws an error, because
   `Date(2001, 2, 29)` does not exist.
4. **Intervals to steps.** A row covers whole steps `t(From) … t(To)`,
   inclusive. A row that touches only part of a step still sets the whole
   step. `generate_export_restriction_dict` fills `(t, region) → value` row
   by row. If two rows touch the same step, the later row in the sorted
   list overwrites the earlier one. It is neither a sum nor a maximum.
5. **To the model and the output.** With the defaults `pol_hor = true` and
   `two_markets = true`, `export_restriction_step!` puts `dict[(t, region)]`
   (or 0) in `export_restrictions[1]`. `sales_step!` copies it to
   `producer.export_restriction`, which cuts foreign deliveries by that
   share. `observe_producers!` writes it to the output as
   `export restriction`, and the value is rounded to 4 digits
   (simulation.jl, line 296). **So the output variable is the aggregated
   input value at each step, rounded to 4 digits.** It is not the export
   tax factor.

One quirk: if two rows for the same region are day-adjacent (one ends on
day d and the next starts on day d + 1), the overlap resolver emits an
extra `From > To` row with the summed value. J4's Argentina rows show this
(value 1.0). That extra row has the same From as the next row, so the next
row overwrites its single step and the extra row has no effect. The J9
builder leaves a one-day gap between rows anyway.

### Check on the J4 run

`scripts/check_agrimate_restriction_mapping.jl` runs steps 1–4 with the
paper's own functions on `data/agrimate_input/` and compares the result
with `export restriction` in `data/netcdf/<harvest + restr>.nc`. All 7
restricted regions match at every one of the 312 steps after rounding to 4
digits, with no mismatched steps. Before rounding, the largest difference
is 4.2e−5 (China: 0.7 × fraction 0.9705 = 0.679358, output 0.6794).

## What was built

`scripts/build_agrimate_authorrestr_inputs.jl` writes
`agrimate-equal-sales-penalty/data/agrimate_input_authorrestr/`:

- Six CSVs and `README.txt` are byte copies of
  `data/agrimate_input_authorparams/` (checked with `cmp`): food balance,
  trade flows, harvest distributions, anomalies, trends and parameters.
- `export-restrictions_crop=wheat_source=2007-2011.csv` is new. For each
  region the author restricted, the builder picks the area with the
  largest export fraction under our trade inputs. The fraction comes from
  `aggregate_export_restrictions` itself. The builder writes one row per
  constant run of the author series, with `Value = v_author / fraction`.
  From is the first day of the run's first step. To is the day before the
  last day of its last step.

| Region | Area used | Export fraction | Author max | Runs (rows) | Steps > 0 |
|---|---|---|---|---|---|
| Ukraine | UKR | 1.0000 | 0.95 | 1 | 21 |
| Argentina | ARG | 1.0000 | 0.95 | 3 | 60 |
| Eastern Africa | MUS | 0.8188 | 0.9381 | 1 | 52 |
| Rest of Southern Asia | — | 0 (no outside exports) | 0.3453 | **not matched** | 25 |
| Kazakhstan | KAZ | 1.0000 | 0.95 | 2 | 15 |
| Rest of Europe | BLR | 0.5584 | 0.4633 | 3 | 44 |
| Rest of Western Asia | ARE | 0.8365 | 0.5171 | 1 | 25 |
| Pakistan | PAK | 1.0000 | 0.95 | 1 | 65 |
| Russia | RUS | 1.0000 | 0.95 | 2 | 87 |
| China | CHN | 0.9705 | 0.50 | 1 | 28 |

The file (15 rows):

```
Exporter,From,To,Value
UKR,2007-05-18,2008-03-31,0.9500000000000001
ARG,2007-01-01,2008-01-14,0.5
ARG,2008-04-02,2008-05-01,0.5
ARG,2008-05-03,2009-09-15,0.95
MUS,2008-01-31,2010-03-31,1.1456874150223424
KAZ,2008-01-31,2008-03-16,0.5
KAZ,2008-03-18,2008-09-15,0.95
BLR,2007-08-02,2008-05-16,0.6778491591648178
BLR,2008-05-18,2008-05-31,0.8297160249433556
BLR,2008-06-02,2009-05-31,0.15186686577853778
ARE,2008-07-18,2009-07-31,0.6181731910727309
PAK,2008-03-18,2010-11-30,0.9500000000000003
RUS,2008-01-31,2010-07-16,0.5
RUS,2010-07-18,2011-09-15,0.95
CHN,2008-01-01,2009-03-01,0.5151921606591309
```

MUS (Mauritius) is the largest outside exporter of Eastern Africa in the
reconstructed FAOSTAT trade file. Its row value of 1.146 is above 1, but
the code caps only the scaled regional value, which is 0.9381. Values such
as 0.9500000000000001 come from fractions that are 1 only up to floating
point.

**Rest of Southern Asia cannot be matched without changing the trade
inputs.** That region is AFG, BGD, BTN, IRN, LKA, MDV and NPL. The
reconstructed trade-flow file has no rows with any of them as origin. The
food balance still lists small exports (IRN 67 kt, LKA 186 kt, NPL 6 kt).
So `export_region = 0`, every row gets fraction 0, and the code drops it.
The author's trade data must have had Rest of Southern Asia exports to
other regions. The author series is 0.3453 at steps 201–225 (May 2008 to
May 2009). In the J9 run this region stays unrestricted. Our inputs give it
no foreign baseline sales, so we expect the missing restriction to have
little effect, but this has not been tested.

## Verification (no long run)

The same check script, run on `data/agrimate_input_authorrestr/` against
the author file:

| Region | Steps > 0, author / ours | Max abs diff (raw) | Mismatched steps |
|---|---|---|---|
| Ukraine, Eastern Africa, Kazakhstan, Rest of Europe, Rest of Western Asia, Pakistan, Russia, China | identical | 0 | none |
| Argentina | 60 / 60 | 2.2e−16 | none |
| Rest of Southern Asia | 25 / 0 | 0.3453 | 201–225 (all 25) |

Nine of ten regions are exact at all 312 steps after the 4-digit output
rounding. Before rounding, the worst difference is 2.2e−16. Across all
regions, the maximum absolute difference is 0.3453, and all of it is the
unmatched Rest of Southern Asia.

## Run (pending)

- Runner: `agrimate-2025/run_j9_authorrestr_harvest_restrictions.jl`. It is
  the J8 harvest + restrictions runner with `inputroot =
  data/agrimate_input_authorrestr` and `outputroot = data_authorrestr`.
- Wrapper: `agrimate-2025/run_j9.sh`. It mirrors
  `run_j8_harvest_restrictions.sh` and logs to
  `agrimate-2025/j9_harvest_restrictions.{log,start,end}`.
- `data/agrimate_input*`, `data/netcdf/` and `data_authorparams/` are not
  touched. The new output, including a cold `agrimate_cache/`, goes to
  `agrimate-equal-sales-penalty/data_authorrestr/`. Generated output is not
  committed.
- After the run, score with `scripts/compare_agrimate_julia_runs.jl`:
  `J4_LOCAL_DIR=…/data_authorparams/netcdf/` keeps the J8 baseline and
  harvest files, and `J4_RESTR_LOCAL=../../data_authorrestr/netcdf/<harvest + restr filename>`
  points to the J9 file (the path is relative to `J4_LOCAL_DIR`).

Gate 0 is not accepted by this note.
