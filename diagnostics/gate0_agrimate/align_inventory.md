# A1 — 14022004 wheat control flow vs host (inspect-only)

Not implemented. Not a pin. Not a freeze. Not an αI retune. Not G1.
`wheat_params()` stay αI=3.2, ζ=0, N_for months=3 (host `n_for` = 6 steps,
same as `AgrimateModel.jl` `N_for = 3*(N_year÷12)`). USDA stays
`prepare_wheat`. 0 `*.jl` in `sheaf/`.

Tree read this session: Zenodo 14022004 `agrimate-model.zip`
(md5 `2adbf06e20d3200f646099f0aa10a1b1`), unpacked under `/tmp` only.
Folder `agrimate-equal-sales-penalty`. `two_markets=true`,
`ε_d_adjust=false`, `equal_constraint=false`. Line numbers match T2
(D.22 `producer.jl` 452–464; x1 fixed `producer_optimization.jl` 67–72).
Not copied.

## Loop (not a transcription)

Author `step!` (`model.jl` 55–82), after `initialize_model_run` fills
expected harvests (`run.jl` 67–78): every producer does harvest, export
restriction, then sales against **last step’s** demand requests; then
every producer does policy on **future** sales; then every producer
communicates prices and D.22; then every consumer delivers, consumes,
enqueues purchases, and procures the next requests.

Host `AgrimateSim.run` (`model.py` 283–417): harvest, Jacobi plan using
`last_ask`, D.7 offer from **this** step’s ship, `fulfill_sales`, D.22,
Ndel queue, `p_w`, T* arrival, CES (writes `last_ask`), consume.
“Plan on last requests, then new requests” matches. Clearing, the
communicated price, and the share update do not.

D.22 and the solver **algorithm** are reused from T2 / the live host.
They are not re-ranked.

## Inventory

| mechanism | author file:line | host file:line | class | implement-now |
|---|---|---|---|---|
| init | `initialization.jl` 216–259 (`equilibrate_producers!`, `storage = baseline_storage`); `simulation.jl` 98–102 food-balance + trade | `optimize.py` 425–452 closed-form Nash; `model.py` 236 `S_p=0`; `wheat_data.py` 125–268 USDA C.1 | **D** | no |
| harvest expectation | `expected_harvests.jl` 3–26: raw harvest at `t`, blend on `t+n` with `w(n)`; plan `H=vcat(harvest, expected)` `producer.jl` 120 | `equations.py` 13–34 same `w`; `model.py` 290–313 applies `w(1)` to **current** `harvest_at(t)` and plans length `N_year` | **D** | no |
| x1 lock | `producer.jl` 116–117 `min(D, H+S)`, domestic first; ι floor 69–77 | `optimize.py` 92–139 `demand_x1_from_ask`; called `model.py` 320–322 on `last_ask` | **H** | no |
| supplier programme | `producer_optimization.jl` 67–85 (x1 fixed, current profit = `revenue_curve`), 97–108 availability, 333–355 SLSQP `2N` / `maxtime=60` / uniform `x_init`; `producer.jl` 160 domestic others | `optimize.py` 275–422 x1-fixed scipy SLSQP on fractions, D.7 on the locked step (`208`), free block `N−1`, `plan_maxiter=40`, no domestic others | **D** | no |
| transactions | `producer.jl` 271–307 and 560–588: prorate each request by sales/demand; foreign × `(1−Δ)`; price = reservation | `equations.py` 68–77 `fulfill_sales` (domestic first, then XI×(1−Δ)); `wheat_data.py` 271–277 T* shares; `model.py` 365–390 | **D** | **yes (1)** |
| purchaser CES | algebra `consumer.jl` 355–371 (`ε_d_adjust=false`, `AgrimateModel.jl` 74); shares `consumer.jl` 228–239 `a* × expected_sales/X_avg`; offers `producer.jl` 398–424 then `consumer.jl` 197–201 | algebra `equations.py` 113–138; shares fixed `model.py` 266–268 `T*`; offers are same-step D.7 `model.py` 351–357, 392–407 | **D** | **yes (2)** |
| consumer | `consumer.jl` 18–43, 135–158; `household_budget` `initialization.jl` 390–394 | `equations.py` 153–172; `model.py` 408–415. Same CES shape at p=1; scale is `C*` not the calibrated household budget | **H** | no |
| delivery / Ndel | `consumer.jl` 10–16, 45–57: queue length `N_del=2` of **all** purchases at transaction price; domestic waits | `model.py` 241–247, 377–390: `n_del=2` of exporter XI and D.7 offers; domestic `sold_d` consumed the same step | **D** | no |
| D.22 | `producer.jl` 451–465 vector+shift of `optimal_sales_foreign[3:end]`; weight `AgrimateModel.jl` 110 | `d22.py` 76–109; called `model.py` 371–376. T2 rows 1–6, now live. Not a freeze | **H** | no |
| world price | `plot.jl` 905–942: non-domestic `transaction quantity × transaction price`, volume-weighted. Recorder `observation.jl` 222–245; average `postprocess.jl` 53–76 | `model.py` 41–63 and 383–387: XI-weighted **lagged D.7 offers**. Not that transaction index | **D** | no |
| observation | `run.jl` 45–61 `observe!` after `step!`; bilateral transaction price/quantity `observation.jl` 222–245 | `model.py` 249–258, 433–447: `price_index` path only. No bilateral transactions | **G** | no |

FAO food-balance inputs vs USDA C.1 are **E** on the init row (Bar A
contract). Do not switch `prepare_wheat`.

## Ranked implement-now (at most three)

1. **Transactions.** The wheat sale is a prorata of last period’s
   requests (`determine_transactions_two_markets`), and that bilateral
   `(q, p)` is what `plot_wm_price_timeseries` aggregates. The host
   clips a plan and routes XI by baseline T*. Class D (host E.1
   choice), sourced law the host does not do.
2. **Purchaser CES, the part that is not already D.30a.** Share update
   and the offer are `expected_price_{domestic,foreign}` from **next-step**
   planned sales (`communication_step!`), not a same-step D.7 of shipped
   XI, and not a frozen T* column. Do not retune σ or ε_d. Do not turn
   on `ε_d_adjust` (author wheat default is false; single `determine_demands`).
3. No third. World price and delivery payload **follow** row 1; scoring
   a new index before transactions exist would invent a series.
   Supplier leftovers (horizon `N_hor+1`, `revenue_curve` on the locked
   step, domestic `x_oth`, quantity inequalities, uniform `x_init`,
   `maxtime=60`) stay labelled from T2 / `rt_solver.md`. They are not
   ranked above the clearing loop. `plan_maxiter` stays 40.

Confidence **95–100%** on the file:line rows (same zip the T2 lines
cite). Confidence **80–95%** on the ranking (clearing before another
NLP fragment). G0-P stays **not accepted**. Do not start G1.
