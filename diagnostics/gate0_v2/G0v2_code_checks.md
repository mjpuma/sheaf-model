# Gate 0 v2 — is the new host working? (wheat, published inputs)

Host: PIK `develop-substitution-claude` snapshot (`agrimate` commit `2807556`,
no code edits), `maxtime = 60`, baseline 2007–2009, AgrimateEU28 + Egypt.
Driver `diagnostics/gate0_v2/gate0_4crop.jl`; outputs and logs under
`agrimate/data/gate0_v2/`. Reference for scoring is the published author
NetCDF (`score_gate0.py LOCAL REF`).

## 1. Branch test suite — G, 85–95 %

`src/AgrimateModel/test/runtests.jl` does not run as shipped. Its own
`src/AgrimateModel/Manifest.toml` pins older packages (e.g. DataStructures
0.18.10 vs 0.18.20 in the top-level Manifest the model runs with) and is not
installed. Run instead in a throwaway copy of the top-level environment
(`/tmp/agrimate_testenv`, test imports declared, no resolve), file by file:

| test file | result |
|---|---|
| `agents/consumer.jl` | 36 / 36 pass |
| `agents/supplier.jl` | 29 pass, 1 fail, 18 error; aborts at line 105 |
| `agents/supplier_optimization.jl` | load error: `storage_hold_back` not assigned |
| `agents.jl` | 12 pass, 5 fail, 5 error |
| `model.jl`, `run.jl` | load error: `α_adj` is `nothing` in test params |
| `AgrimateModel.jl` | `InputData` constructor signature changed |

Every error traced is the test calling an older API (`determine_transactions`
gained an `export_restriction` argument; test fixtures lack newer parameters).
The `agents.jl` value failures follow from earlier errors in the same set.
No failure points at the model; equally, the suite gives no assurance beyond
the consumer module.

## 2. Bookkeeping on `wheat_t312_published` — H, 95–100 %

Residuals at the 4-decimal NetCDF precision:

- supplier storage: S(t) − S(t−1) − harvest(t) + sales(t): ≤ 1e-4 kt
- consumer storage: C(t) − C(t−1) − delivery(t) + consumption(t): ≤ 1e-4 kt
- sales = Σ transactions over buyers: ≤ 4e-4 kt
- delivery(t) = purchases(t−2) per buyer: ≤ 3e-4 kt (same lag in old host and author file)
- consumption = realized; rationing loss = desired − realized: exact / 1e-4
- no negative storage, harvest, sales, delivery, consumption; traded prices 0.07–1000

Two output conventions (not errors): the new host stores `transaction
quantity` as (time, buyer, seller), the old host and author file as (time,
seller, buyer). `sales` ≠ `sales domestic` + `sales foreign` by up to
3520 kt; the author file shows the same (3523 kt), so those two variables are
not a split of realized sales.

## 3. Undisturbed run — H (inherited behaviour), 90 %

No anomalies, no restrictions. Prices do not stay near 1 and stocks do not
repeat the baseline cycle: year-end stocks fall 332.4 → 317.5 Mt over
2000–2004 and settle at 315.4–315.6 Mt from 2008; annual mean price rises
0.99 → 1.10 and settles; seasonal range settles at 0.94–1.39. The published
author run has the same spin-up over 2000–2004 (before its shocks): stocks
332.3 → 317.2 Mt, seasonal price ranges equal to ours within 0.008. So the
initial baseline is not a stationary point of the published model (E); the
new host reproduces that rather than introducing it.

## 4. Consumer-split invariance — C, 80–95 %

Same published wheat inputs, crisis scenario, via consumer files:
`one` (one consumer, A_c from the parameters file, share 1) and `two` (two
identical consumers, same A_c, shares 0.5/0.5).

At the consumer level the split is exact: c1 = c2 and c1 + c2 = total at
every step. Region trajectories are not identical:

- one vs two: baseline totals differ in the last stored digit; US demand
  differs by 0.003 kt of 1398 kt at step 1; differences then grow.
- default path vs `one`: identical at 4 decimals through step 10, first
  difference at step 11 (Rest of Central Asia). The empirical path rounds
  A_c to 4 digits; the consumer-file path does not.

Effect on the J10 measures (reference = published author file):

| run | 2007/08 | 2010/11 | peak | worst stock gap |
|---|---:|---:|---:|---:|
| default (one consumer, parameters file) | 1.3527 | 1.2127 | 2.1898 | +0.508 % (2011) |
| `one` (consumer files) | 1.3509 | 1.2119 | 2.1987 | −0.227 % (2011) |
| `two` (two half consumers) | 1.3602 | 1.2141 | 2.2120 | +0.524 % (2011) |

Three setups that are the same model up to float rounding spread by 0.009
on the 2007/08 ratio, 0.022 on the peak, and 0.75 pp on 2011 stocks. Each
misses a different bar. The ±0.01 ratio bars and the ±0.5 % stock bar are
about the width of this sensitivity, so a single run passing or missing one
of them is weak evidence about the code.

## 5. Repeatability under load — H, 95 %

Three copies of the crisis run in parallel (`load1–3`), 178 s each, same as
idle. All numeric variables identical to the idle reference run and to the
earlier repeat. No sign of the 60 s cap binding; solver return-code
instrumentation not needed.
