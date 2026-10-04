# J9 — published Agrimate code with the author's export restrictions

Prepared 2026-10-03, run and scored 2026-10-04. **Not a reproduction.**
The author's own restriction series, carried into the simulation exactly
for 9 of their 10 regions, closes **none** of the price gap and **none**
of the stock gap. The 07/08 and 10/11 price ratios move slightly further
from the author than J8's. See "Results" at the end. Only the
harvest + restrictions scenario was rerun; baseline and harvest are J8's.

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

## Run

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

The run finished `exit=0`, no `ERROR` lines, 13 chunks, 312 steps.

| Run | Start (UTC) | End (UTC) | Wall |
|---|---|---|---|
| Harvest + restrictions | 2026-10-04 03:38:01 | 2026-10-04 17:45:31 | 14 h 07 m |

## Results

Three scripts were run read-only under Julia 1.6.5 (Rosetta) from the
paper project. Their output is in `agrimate-2025/j9_compare/`, which does
not overwrite `j4b_compare/` or `j8_compare/`. Generated output is not
committed.

- `scripts/check_agrimate_j9_restrictions.jl` → `j9_restriction_check.md`
- `scripts/compare_agrimate_julia_runs.jl` with
  `J4_LOCAL_DIR=…/data_authorparams/netcdf/` and `J4_RESTR_LOCAL` pointing
  at the J9 file → `j9_vs_author.md`. Same metrics, same windows and the
  same world-price definition as J4 and J8, so the numbers are directly
  comparable. Prices are divided by **each run's own 2000–2005 mean**.
- `scripts/diagnose_agrimate_j9_gaps.jl` → `j9_gap_diagnosis.md`

Because only harvest + restrictions was rerun, the baseline and harvest
columns of `j9_vs_author.md` are the J8 files and repeat J8's numbers.

### 1. Did the restrictions carry through?

Yes. `export restriction` in the J9 output equals the author's at every
one of the 312 steps for 9 of the 10 regions, exactly, after the 4-digit
output rounding. Same region order, same time axis, same shape.

| Region | Steps > 0, L / A | Max L / A | Max abs diff | Differing steps |
|---|---|---|---|---|
| Ukraine | 21 / 21 | 0.9500 / 0.9500 | **0** | 0 |
| Argentina | 60 / 60 | 0.9500 / 0.9500 | **0** | 0 |
| Eastern Africa | 52 / 52 | 0.9381 / 0.9381 | **0** | 0 |
| Kazakhstan | 15 / 15 | 0.9500 / 0.9500 | **0** | 0 |
| Rest of Europe | 44 / 44 | 0.4633 / 0.4633 | **0** | 0 |
| Rest of Western Asia | 25 / 25 | 0.5171 / 0.5171 | **0** | 0 |
| Pakistan | 65 / 65 | 0.9500 / 0.9500 | **0** | 0 |
| Russia | 87 / 87 | 0.9500 / 0.9500 | **0** | 0 |
| China | 28 / 28 | 0.5000 / 0.5000 | **0** | 0 |
| Rest of Southern Asia | 0 / 25 | 0.0000 / 0.3453 | **0.3453** | 201–225 |

Overall max abs diff 0.3453, at step 201 (2008-05-09) in Rest of Southern
Asia. Excluding that region the max is exactly 0. Differing cells: 25 of
8736. First and last active step also match region by region. This is the
outcome predicted by the pre-run check: the one region our trade file
gives no extra-regional exports cannot be restricted, and everything else
is a clean copy. The input build and the aggregation path are therefore
not a source of the residual gap.

### 2. Headline table: J4 vs J8 vs J9 vs author

Harvest + restrictions unless noted. L is local, A is author. J4 is the
reconstructed run, J8 adds the author's ψ / A_d* / A_c*, J9 adds the
author's restrictions on top of J8.

| Quantity | J4 | J8 | J9 | Author |
|---|---|---|---|---|
| Price ratio 07/08 (÷ own 2000–05 mean) | 1.277 | 1.288 | **1.253** | 1.361 |
| Price ratio 10/11 | 1.149 | 1.155 | **1.105** | 1.219 |
| Peak WM price (month) | 1.736 (2008-05) | 1.764 (2008-05) | **1.767 (2008-06)** | 2.223 (2008-05) |
| WM price, May 2008 | 1.736 | 1.764 | 1.754 | 2.223 |
| Restriction add-on, 07/08 (restr ÷ harvest) | +10.6 % | +10.9 % | **+7.8 %** | +9.3 % |
| Restriction add-on, 10/11 | +12.4 % | +12.8 % | **+7.9 %** | +11.8 % |
| Monthly price correlation L,A (all) | 0.852 | 0.858 | 0.847 | — |
| Monthly price correlation L,A (2005–12) | 0.845 | 0.849 | 0.826 | — |
| Mean abs price level gap | 9.2 % | 9.1 % | 8.3 % | — |
| World stocks, end 2008 (Mt) | 425.9 (+33.4 %) | 391.0 (+22.4 %) | **391.7 (+22.7 %)** | 319.3 |
| World stocks, end 2012 (Mt) | 397.8 (+35.6 %) | 364.3 (+24.2 %) | **367.8 (+25.4 %)** | 293.3 |
| World production 2008 (Mt) | 666.0 (+0.7 %) | 666.0 (+0.7 %) | 666.0 (+0.7 %) | 661.3 |
| World consumption 2008 (Mt) | 616.2 (+0.8 %) | 618.1 (+1.1 %) | 618.6 (+1.2 %) | 611.5 |
| Trade, calibrated baseline (Mt/yr) | 130.7 (+13.0 %) | 130.7 (+13.0 %) | 130.7 (+13.0 %) | 115.7 |
| Trade, realised 07/08 exports (Mt) | 128.9 (+9.6 %) | 129.9 (+10.4 %) | 128.3 (+9.0 %) | 117.6 |
| Restricted regions | 7 (5 shared) | 7 (5 shared) | **9 exact of 10** | 10 |
| Restricted region-steps | 499 | 499 | 397 | 422 |

How much each alignment step closed, as a share of the J4 gap to the
author:

| Gap | J4 → J8 (author parameters) | J8 → J9 (author restrictions) |
|---|---|---|
| World stocks, end 2008 | **33 % closed** | **−1 % (slightly wider)** |
| Price ratio 07/08 | 13 % closed | **−42 % (wider)** |
| Price ratio 10/11 | 9 % closed | **−71 % (wider)** |
| Peak WM price | 6 % closed | 1 % closed |

Production has no gap to close (+0.7 %) and consumption none worth
closing (+1.2 %). Both are set by the reconstructed food-balance and
anomaly files, which J8 and J9 do not touch.

The J9 restriction add-on is the first apples-to-apples test of the
restriction mechanism: identical restriction input, identical code,
different pre-existing state. Our run transmits **+7.8 %** against the
author's **+9.3 %** in 07/08, and **+7.9 %** against **+11.8 %** in
10/11. J4 and J8 looked closer on this line (+10.6 / +12.4 %) only
because their reconstructed AMIS file restricted more regions for longer
— 499 region-steps against the author's 422, and through 2011-12 for
Argentina, China and Ukraine. Replacing it with the author's own series
removes that over-restriction and exposes a mechanism that is weaker than
the author's, not stronger.

The peak month also moves, from 2008-05 to 2008-06. This is a near-tie,
not a regime change: the local May value is 1.754 and June 1.767, 0.7 %
apart. The "same peak month" agreement reported in J4 and J8 is not
robust at this margin.

### 3. Where the residual gap sits

From `j9_gap_diagnosis.md`. The world price over a window is
P = Σ w_p p̄_p, where w_p is a producer's share of window export volume
and p̄_p its export-weighted mean price, so the local-minus-author gap
splits into a volume-share term and a price term. (This pools the window
by volume, so it gives 1.222 rather than the scorer's equal-weight
monthly mean of 1.250. Both are reported from the same arrays.)

**Price, Jul 2007 – Jun 2008: local 1.222, author 1.347, gap −0.125.**

| Producer | Vol share L / A | Mean export price L / A | Contribution | of which volume | of which price |
|---|---|---|---|---|---|
| USA | 0.234 / 0.255 | 1.295 / 1.451 | −0.067 | −0.031 | −0.037 |
| Argentina | 0.051 / 0.092 | 1.095 / 1.213 | −0.056 | −0.050 | −0.006 |
| Russia | 0.108 / 0.129 | 1.246 / 1.423 | −0.050 | −0.031 | −0.019 |
| Australia | 0.075 / 0.030 | 1.222 / 1.422 | +0.050 | +0.065 | −0.015 |
| EU-28 | 0.169 / 0.136 | 1.198 / 1.267 | +0.030 | +0.042 | −0.012 |
| Canada | 0.113 / 0.118 | 1.277 / 1.404 | −0.022 | −0.008 | −0.014 |
| Kazakhstan | 0.046 / 0.058 | 1.033 / 1.129 | −0.018 | −0.014 | −0.004 |
| Pakistan | 0.016 / 0.000 | 1.047 / — | +0.017 | 0.000 | +0.017 |
| China | 0.051 / 0.063 | 1.182 / 1.217 | −0.016 | −0.014 | −0.002 |
| **All 28** | 1.000 / 1.000 | 1.222 / 1.347 | **−0.125** | **−0.041** | **−0.084** |

Two thirds of the gap (−0.084) is a **level** effect that is not specific
to any region: every large exporter's own mean export price is 5–14 %
below the author's (USA 1.295 vs 1.451, Russia 1.246 vs 1.423, Australia
1.222 vs 1.422, Canada 1.277 vs 1.404). The remaining third (−0.041) is
**composition**: we ship too little from Argentina (5.1 % vs 9.2 % of
world exports), Russia and the USA, and too much from Australia (7.5 % vs
3.0 %), the EU-28 and Pakistan.

Running the same decomposition on the 2000–2005 window gives a gap of
−0.055 with no shock present at all, so **44 % of the 07/08 price gap is
the baseline price-level drift** J4 already flagged: the author's
transaction price climbs to ≈1.08 by 2003 and ours stays near 1.00. Only
−0.070 of the gap is specific to the crisis.

Attributing the 07/08 ratio shortfall in logs (local 1.253 vs author
1.361):

| Channel | Local | Author | Share of the shortfall |
|---|---|---|---|
| Baseline price level (baseline ÷ pre) | 1.013 | 1.035 | 26 % |
| Harvest shock (harvest ÷ baseline) | 1.133 | 1.185 | **54 %** |
| Restrictions (restr ÷ harvest) | 1.078 | 1.093 | 17 % |
| Residual (window means of ratios ≠ ratio of window means) | | | 3 % |

**The harvest-shock channel, not the restriction channel, is the largest
single source of the remaining price gap.**

**Stocks, end 2008: local 391.7 Mt, author 319.3 Mt, gap +72.4 Mt.**

| Region | Stocks L / A (kt) | Gap kt | Gap % | Share of world gap |
|---|---|---|---|---|
| EU-28 | 78,191 / 59,691 | +18,500 | +31 % | **26 %** |
| China | 71,423 / 61,003 | +10,420 | +17 % | 14 % |
| Argentina | 14,195 / 4,055 | +10,139 | +250 % | 14 % |
| India | 13,720 / 5,140 | +8,580 | +167 % | 12 % |
| Australia | 15,897 / 7,866 | +8,032 | +102 % | 11 % |
| Pakistan | 11,462 / 6,032 | +5,429 | +90 % | 8 % |
| Rest of Southern Asia | 9,712 / 6,596 | +3,116 | +47 % | 4 % |
| Ukraine | 14,229 / 11,548 | +2,681 | +23 % | 4 % |
| Turkey | 5,541 / 3,306 | +2,234 | +68 % | 3 % |
| Canada | 18,872 / 16,639 | +2,234 | +13 % | 3 % |
| **Top 10** | | **+71,365** | | **99 %** |

Ten regions carry 99 % of the world stock gap, and six of them (EU-28,
China, Argentina, India, Australia, Pakistan) carry 85 %. These are the
regions where the reconstructed food-balance and trade-flow tables are
furthest from the author's: Argentina baseline consumption is +72 %,
India harvest −11 % and consumption −12 %, EU-28 producer storage +27 %,
Canada +44 % (`J8_authorparams.md`, `INPUTS.md`). With ψ now equal to the
author's, the stock gap is what the quantity inputs imply, and the
restriction set does not move it (+22.4 % in J8, +22.7 % in J9). Note
also that Rest of Southern Asia is +47 % over the author at end 2008 —
the direction expected from leaving it unrestricted — but it is 4 % of
the world gap, so the one unmatched region does not explain the result.

### 4. Verdict

**This is not a reproduction of the published wheat run.** It is the
published Agrimate code, running on the author's region parameters and
the author's export-restriction series, with every other input a SHEAF
reconstruction. The input alignment is now demonstrably exact on both
fronts (max |ψ L−A| = 0.000 in J8; max |restriction L−A| = 0 outside one
region here), and the published magnitudes are still not reproduced:
stocks +23 %, the 07/08 price ratio 1.25 against 1.36, the 10/11 ratio
1.11 against 1.22, and a combined peak of 1.77 against 2.22.

The two alignment steps have now bracketed the problem. The author's
calibrated parameters explain about a third of the stock gap and none of
the price gap. The author's restrictions explain none of either, and on
the price ratios they move the run slightly further away. What is left is
in the reconstructed quantity inputs — the food balance, the bilateral
trade flows, the harvest calendar and the harvest-anomaly file — none of
which the author published. Nothing was retuned. A failed match stays a
failed match.

Classification and confidence, per `CLAUDE.md`:

| Conclusion | Class | Confidence |
|---|---|---|
| The author restriction series reaches the simulation unchanged for 9 of 10 regions (max abs diff 0; Rest of Southern Asia 0.3453 because our trade file gives it no extra-regional exports). The input builder and `aggregate_export_restrictions` are not a source of error here. | **H** | 95–100 % — directly reproduced from both NetCDFs |
| J9 is not a reproduction of the published wheat run. Levels are off by the margins tabulated above. | **F** | 95–100 % — directly reproduced |
| Aligning the restriction set closes none of the stock gap (+22.4 % → +22.7 %) and widens the 07/08 and 10/11 price ratios (1.288 → 1.253, 1.155 → 1.105). | **F** | 95–100 % — directly reproduced |
| The closer restriction add-on in J4/J8 (+10.6 / +12.4 %) was an artefact of over-restriction in the reconstructed AMIS file (499 region-steps vs 422, three regions active to 2011-12). With the author's own series the mechanism transmits less than theirs, not more. | **F** | 80–95 % — strong evidence (the two runs differ only in the restriction file), but no separate counterfactual was run |
| The residual 07/08 price gap is ≈54 % harvest-shock channel, ≈26 % baseline price level, ≈17 % restriction channel. | **F** | 80–95 % — the log attribution is approximate; window means of ratios leave a 3 % residual |
| The residual stock gap is concentrated in six regions (EU-28, China, Argentina, India, Australia, Pakistan = 85 %) and tracks the reconstructed food-balance and trade-flow gaps, not ψ and not the restrictions. | **F** | 80–95 % — strong implementation evidence; the author input tables are unpublished, so the causal link to them cannot be closed |
| The "same peak month" agreement is not robust: local May 2008 = 1.754 and June = 1.767, a 0.7 % margin, and the peak moves to June in J9. | **C** | 80–95 % — directly reproduced, but whether the margin is solver noise or structure was not separately tested |

Open items unchanged from J4: the Middle Africa producer (problem 3),
code identity and the 100–500× wall-time gap (problem 5). J4 problem 2
(different restricting regions) is now resolved for 9 of 10 regions and
shown not to be the cause of the gap.

Gate 0 is not accepted by this note.
