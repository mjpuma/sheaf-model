# J8 — published Agrimate code with the author's region parameters

Prepared 2026-10-02, scored 2026-10-03. **Not a reproduction.** The author
parameters close about a third of the J4 stock gap. They close almost none
of the price-spike gap. See "Results" at the end.

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

## Long runs

Each wrapper mirrors `run_j3b.sh`:

- `agrimate-2025/run_j8_baseline.sh` → `run_j8_authorparams_baseline.jl`
- `agrimate-2025/run_j8_harvest.sh` → `run_j8_authorparams_harvest.jl`
- `agrimate-2025/run_j8_harvest_restrictions.sh` → `run_j8_authorparams_harvest_restrictions.jl`

Each `.jl` matches its J2/J3 runner except for `inputroot`
(`data/agrimate_input_authorparams`) and `outputroot`
(`data_authorparams`). Logs and timestamps go to `agrimate-2025/j8_<name>.{log,start,end}`.
The baseline run will overwrite the t_max = 0 NetCDF in
`data_authorparams/netcdf/`. A copy is kept at
`agrimate-2025/j8_author_params/tmax0_baseline.nc`. Generated output is
not committed.

All three finished with `exit=0`, no `ERROR` lines, 13 chunks, 312 steps.

| Run | Start (UTC) | End (UTC) | Wall |
|---|---|---|---|
| Baseline | 2026-10-02 22:12:11 | 2026-10-03 16:50:46 | 18 h 39 m |
| Harvest | 2026-10-02 21:07:19 | 2026-10-03 16:48:25 | 19 h 41 m |
| Harvest + restrictions | 2026-10-02 22:06:58 | 2026-10-03 14:52:32 | 16 h 46 m |

There were launch problems. A blocked tool call still started a second
baseline and a second harvest + restrictions process. Both baseline copies
were killed, and one clean baseline was started at 22:12Z. The duplicate
harvest + restrictions copy exited about 3 min in. Its wrapper wrote a stale
`.end` stamp, later overwritten, and the first minutes of
`j8_harvest_restrictions.log` are interleaved. The NetCDF is unaffected
because `simulate()` rewrites the whole file after every 24-step chunk.

## Results

`scripts/compare_agrimate_julia_runs.jl` was run with
`J4_LOCAL_DIR=…/data_authorparams/netcdf/`. Its output is in
`agrimate-2025/j8_compare/j8_vs_author.md`, beside a fresh J4 run in
`j4_vs_author.md`. The metrics and the world-price definition are the same
as J4. The world price is the export-weighted monthly transaction price on
cross-border flows.

All three J8 files have 312 steps and 28 regions, the same region order and
time axis as the author files, and finite key variables. ψ, A_d* and A_c*
equal the author values exactly (max |ψ L−A| = 0.000). J8 harvests equal the
J4 harvests, because the harvest inputs are the same.

### Headline numbers

L is local, A is author. Price ratios are against each run's own 2000–05 mean.

| Quantity | J4 | J8 | Author | Share of the J4 gap closed |
|---|---|---|---|---|
| World stocks, baseline, 2007–09 mean (Mt) | 411.0 (+30.2 %) | 378.9 (+20.1 %) | 315.6 | about 1/3 |
| World stocks, end 2008, harvest (Mt) | 419.0 (+35.1 %) | 385.1 (+24.2 %) | 310.1 | about 1/3 |
| World stocks, end 2008, harvest + restr (Mt) | 425.9 (+33.4 %) | 391.0 (+22.4 %) | 319.3 | about 1/3 |
| Stocks ÷ consumption, end 2012, baseline | 0.650 | 0.599 | 0.499 | 1/3 |
| World consumption, baseline (Mt/yr) | 632.2 | 632.2 | 631.8 | no gap to close |
| Price ratio 07/08, harvest | 1.148 | 1.154 | 1.232 | 7 % |
| Price ratio 10/11, harvest | 1.020 | 1.022 | 1.086 | 3 % |
| Price ratio 07/08, harvest + restr | 1.277 | 1.288 | 1.361 | 13 % |
| Price ratio 10/11, harvest + restr | 1.149 | 1.155 | 1.219 | 9 % |
| Peak price, harvest + restr (both 2008-05) | 1.736 | 1.764 | 2.223 | 6 % |
| Harvest effect, 07/08 (harvest ÷ baseline) | 1.129 | 1.133 | 1.185 | 7 % |
| Restriction add-on, 07/08 / 10/11 | +10.6 / +12.4 % | +10.9 / +12.8 % | +9.3 / +11.8 % | already close, moved slightly away |
| Monthly price correlation with A, harvest + restr | 0.852 | 0.858 | — | unchanged |
| Price level, 2000–05 mean | 0.999 | 0.998 | 1.059 | none |

### Key regions, baseline run, 2007–09 means (stocks in kt)

| Region | Stocks J4 | J8 | A | Consumption J8 vs A |
|---|---|---|---|---|
| USA | 41,592 (+38 %) | 33,115 (+10 %) | 30,225 | −6.8 % |
| EU-28 | 81,214 (+34 %) | 78,334 (+30 %) | 60,431 | +3.9 % |
| Russia | 35,717 (+25 %) | 30,139 (+5 %) | 28,694 | −11.3 % |
| Ukraine | 11,924 (+20 %) | 11,472 (+15 %) | 9,973 | 0.0 % |
| Argentina | 9,378 (+412 %) | 9,709 (+430 %) | 1,833 | +71.6 % |
| India | 20,361 (+215 %) | 14,443 (+124 %) | 6,461 | −12.2 % |
| China | 76,984 (+11 %) | 70,092 (+1 %) | 69,138 | −0.4 % |
| Egypt | 6,749 (+16 %) | 5,406 (−7 %) | 5,807 | +4.5 % |

### Verdict

This is **not a reproduction** of the published wheat run. It is the
published code run on the author's region parameters, with every other
input reconstructed. The parameters explain:

- **About a third of the stock gap.** World stocks fall from +30 % to +20 %
  above the author. USA, Russia, China and Egypt stocks are now within 10 %.
- **Almost none of the price gap.** The 2007/08 harvest spike is still about
  a third smaller than the author's (×1.154 against ×1.232). There is still
  almost no 2010/11 harvest spike (×1.022 against ×1.086). The peak with both
  shocks is 1.76 against 2.22.
- **None of the price-level drift.** The author baseline price rises from
  0.99 to about 1.08 by 2003 and stays there. The local price stays near 1.0.
  Their 2000–05 baseline harvest and consumption match ours to 0.1–2 %, so
  the drift comes from something the parameters do not touch.

Remaining gaps and likely causes. None is fitted here.

1. **Food balance and trade.** Baseline international trade is 13 % above
   the author's (130.7 against 115.7 Mt/yr). Argentina consumption is
   +72 %, which gives +430 % Argentine stocks. India is −11 % in harvest and
   −12 % in consumption. EU-28 producer storage is +27 % and Canada +44 %.
   These come from the reconstructed food-balance, trade-flow and
   harvest-calendar files (`INPUTS.md`). The author tables were not published.
2. **The harvest shock itself.** The regional shock sizes differ from the
   author's, even though world harvest per year matches to 0.7–3 %. For
   2007–08, Australia is −13.5 % against −31.7 % and Kazakhstan +4.6 %
   against +15.9 %. For 2010–11, Russia is −5.6 % against −11.7 % and
   Argentina +23.1 % against −18.5 %. A smaller drop in key exporters fits
   the smaller spikes. The anomaly file is ours (USDA minus a LOWESS trend).
   The author's FAOsince-2005 file is not public.
3. **The restricted-region set.** It is still 7 local against 10 author,
   with 5 in common (J4 problem 2).
4. **Code identity and package drift** (J4 problem 5). The author runs took
   1–3 min each. These took 17–20 h.

Gate 0 is not accepted. Whether a run of the published code on
reconstructed inputs, with these gaps, is good enough is the user's
decision.
