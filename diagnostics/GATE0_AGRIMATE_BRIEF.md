# Note for the Agrimate team (not sent)

Zenodo 14022004 (author code) retrieved 2026-09-16. Data 10688435
unpacked 2026-09-18 (Fig. 4 series only; zip not vendored).

Closed from the executable model (not guessed):

1. **αI, τ:** author code uses α_foreign=3.2 and τ=0.1 (F.1), not Tbl. D.8 3.5 / 0.2. Host follows code; D.8 retained as `wheat_table_d8_defaults()`.
2. **ζ:** author `ζ=0` turns *on* the x_min quadratic penalty (`ζ=1` disables it). Not a storage-cost coefficient. `p_sto=0.1` per year is the storage cost.
3. **C.1 wheat:** `AgrimateRegionsWheat` is **27** names (Egypt in Northern Africa, Mexico in Central America, Pakistan and Turkey singles, no RoW). Paper text said 28.
4. **E.27:** `duration_in_s=1.2` means `s = duration/1.2`, support `|d−dmid|≤s`. Printed `|d−dmid|≤1.2` was OCR.
5. **D.1:** `w = 1/(1+exp((n−N_for)/(0.17 τ_for)))` with N_for=3 months, τ_for=0.2 yr. Near-term realised.
6. **β=0.05 / τ_P=0.2:** present in `AgrimateParams` and computed in
   `sales_step!`, but **not used on the wheat executable path**. Defaults
   `two_markets=true`, `pl_opt=false` are never overridden. Two-market
   optimizer is passed `P_loc_domestic = P_loc_foreign = 1` (live factors
   commented out). Domestic/foreign targets are hardcoded to 1, so those
   factors stay at the init value 1. Combined `P_loc_tgt = P (D_tot/X̂)^β`
   is logged only. Host leaves `beta_loc` / `tau_p` unwired (matches the
   wheat path; not a guessed local-price rule).
7. **D.30a:** wheat uses it. `ε_d_adjust=false` so `determine_demands`
   (single ε_d=1/α=1/3, A_d, B) not the two-market ε_d split. Host formula
   matches; A_d not refit. Inflow still T* by default. R5 labelled
   `x1_from_demand` (Ndel-lagged requests as arrive; default off; not
   adopted).
8. **FAOSTAT Food Balances vs USDA (P10):** not in
   `data/faostat_network/` (E0 trade only). FoodTradeNetwork P0/R0 are
   2015–21 averages, not 2006–11 annual FB. A1 left; USDA default.
9. **Fig. 4 executable (P7):** published series used `AgrimateEU28` + Egypt
   extra, FAO anomalies since 2005, start 2000, `α_foreign=3.5`, `ζ=1.0`,
   `N_for=6`, gitcommit `old-demand-dynamics-150-gbfc02cb-dirty`. Host
   stays on 14022004 wheat defaults. Comparison labelled; not a retune.

Recorded, not a question for Agrimate: Bai/Wada/Puma copy uses α_foreign=10
as a 2017–25 fit. Host keeps author 3.2. Their finding that one parameter
set cannot fit both 2008 and 2022 is a G0-H question, not a split-calibration
of this 2006–11 run.

## Open (2026-09-21) — for the Agrimate team

Independent Python host (`sheaf/agrimate/`) of 14022004 wheat. D.22
vector+shift and x1-fixed SLSQP are live. Undisturbed 2006–11
last/first is 0.812; month-of-year max/min is ~2374×. We have been
scoring that against Fig. 4 baseline last/first 1.004 / moy 1.32×.
Red team: that Fig. 4 series is a different experiment (A7). These
are the questions that close Bar A vs Bar B. Not a retune request.

10. **Which git produced Fig. 4d?** Confirm `old-demand-dynamics-150-gbfc02cb-dirty`
    versus 14022004 `agrimate-equal-sales-penalty` (`two_markets=true`).
    If they differ, Fig. 4 last/first 1.004 is not the 14022004 twin.
11. **What quantity is plotted as world price in Fig. 4d?** Bilateral
    international transaction price (`plot_wm_price_timeseries`) versus
    an XI-weighted mix of regional D.7 offers? File:line if easy.
12. **Can you share a 14022004 wheat undisturbed monthly world-price
    series** (27 `AgrimateRegionsWheat`, α_foreign=3.2, ζ=0, N_for=3,
    no FAO anomalies, no AMIS), 2006–11? Last/first and month-of-year
    max/min on *that* series is the Bar A comparator. Fig. 4 NetCDF
    is Bar B.
13. **On that 14022004 undisturbed path, is last/first ≈ 1 and moy
    O(1) expected?** If yes, our 0.812 / 2374× is still a host bug
    relative to the wheat executable. If no, item 3 against Fig. 4
    1.004 was the wrong bar.
14. **World-price units.** Is the Fig. 4 index 1 at Nash/baseline, and
    is a USD scale applied outside the model? Host uses 2006 Pink mean
    as a unit scale `p0`, not a path pin.

Do not need from the team: permission to freeze D.22, pin 2006, or
set α_foreign=10. Those stay off.
