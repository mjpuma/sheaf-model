# Development plan

**Current phase:** Gate 0 wheat, Agrimate-faithful host (`sheaf/agrimate/`).
Gate 1 and Gate 2 are **blocked**. They stay blocked until Gate 0 is
vetted at a **publishable** level: source-faithful, numerically reliable,
and equal or better than Agrimate on Agrimate’s own wheat targets.

That sequencing is the lesson from the last cycle. Shipping substitution
and a policy sketch on an unpublishable market was a mistake. Do not
repeat it.

Canonical contract: [`GATE0_CONTRACT.md`](GATE0_CONTRACT.md).
Spec map: [`GATE0_SPEC_MATRIX.md`](GATE0_SPEC_MATRIX.md).
Pasteable one-prompt-per-session list: [`GATE0_PROMPTS.md`](GATE0_PROMPTS.md)
(P0–P12 done). Post-P12 R-queue: [`GATE0_REPRO_PROMPTS.md`](GATE0_REPRO_PROMPTS.md)
(**exhausted**). Post-R development: [`GATE0_NEXT_PROMPTS.md`](GATE0_NEXT_PROMPTS.md);
next paste [`GATE0_REPRO_DISPATCH.md`](GATE0_REPRO_DISPATCH.md) (**S6 done**; G0-P **not accepted**; T1–T3 done; D.22 and solver **implemented**; next **leave labelled** in [`GATE0_CONTINUE.md`](GATE0_CONTINUE.md)).
Red team: [`GATE0_REDTEAM.md`](GATE0_REDTEAM.md). Data:
[`GATE0_DATA.md`](GATE0_DATA.md).
This file is the living queue.

## What “publishable Gate 0” means

Agrimate (Kuhla, Kubiczek & Otto 2025, *Ecol. Econ.* 231:108546) is the
bar, not the legacy SHEAF ask/scarcity scores. For **wheat**:

1. **Source fidelity.** Supplier, purchaser, consumer, storage, restrictions,
   timing, and world-price *definition* match the paper/supplement (or an
   approved departure record). Equation-to-code review, not a prompt.
2. **Numerical reliability.** Supplier plans converge. Constraint residuals
   are small. Failed solves are counted and rare enough that they do not
   set the price path. No fill-target, calm pin, scarcity blend, or rival
   markup to make a test pass.
3. **Undisturbed dynamics.** After spin-up, seasonal repeating behaviour
   as Agrimate describes. Not a flat pinned world price.
4. **Reference reproduction.** Same wheat case, data vintage, parameters,
   and output definitions as closely as access allows. If Zenodo
   14022004 / 10688435 are in hand, compare to author series (Fig. 4 and
   regional supply/consumption/stocks). If they are not, say
   “independent implementation,” not “replication.”
5. **Historical performance.** Price *levels and seasonal paths*, not only
   a correlation. Crisis hike ratios *and* quiet-year levels. Stocks,
   consumption, and trade where Agrimate or USDA/FAO report them.
6. **Controlled experiments.** Harvest-only vs harvest+restrictions, as in
   Agrimate’s three scenarios. Domestic vs international responses.

**Pass rule:** items 1–3 must hold before we spend time judging 5.
Item 5 is judged against Agrimate’s published wheat results, not against
legacy SHEAF. A worse Pink-Sheet fit during debugging does **not** restore
L1–L8 (`GATE0_DEPARTURES.md`).

**Wheat only.** Maize and rice are later Agrimate-style single-crop
applications. Do not accept them with inherited wheat knobs, and do not
use them to wave Gate 0 through.

Gate 0 is **not** currently at the publication bar. **G0-N and G0-S are met**
against retrieved author code. **G0-U is the three-scenario validation
workflow** (`diagnostics/GATE0_VALIDATION.md`): undisturbed / harvest-only /
harvest+AMIS, scoring prices **and** supply/stocks. Pink-Sheet scoring stays
G0-H. G1/G2 stay blocked. The only SHEAF differentiator versus an Agrimate
copy (including the Bai/Wada/Puma copy) is that G1 substitution and G2
government games will be added **after** G0-P.

## Sequence (do not skip)

| Stage | Work | Exit |
|---|---|---|
| **G0-N** | Make the supplier programme numerically solvent on the 24-step wheat year. Record residual, runtime, and when the inverse-demand floor binds. | **Feasible** on 2003–11 (failed/fallback 0; residual 0; offer-floor 0). Unconverged scipy **1743/5832** on harvest+AMIS is labelled N5 (`solver.md`); not first-order stationary. Pink-Sheet scoring is G0-H. |
| **G0-S** | Close source gaps that change economics: C.1 ISO list, D.8 vs F.1, ζ0, D.1b, E.27 support, FAOSTAT Food Balance vs USDA (A1–A6). Retrieve Zenodo code/data if available. Unsent questions: `GATE0_AGRIMATE_BRIEF.md`. | **Met for retrieved code.** 27-region C.1 wheat list, author params, p_sto, x_min penalty, E.27, D.1 weights. β/τ_P labelled unused on wheat path (P3). D.30a formula wired (P4); author x1=demand labelled. Raw FAOSTAT FBSH vendored (R6 obtain); labelled host reconstruction of wheat_food_balance_fao.csv (not bit-identical; not adopted); A1 USDA default. Fig. 4 zip unpacked (P7); not a replication. |
| **G0-U** | Undisturbed / harvest-only / harvest+AMIS. Accounting identities. Score prices **and** USDA supply/stocks. Ukraine / Eastern Africa mechanism panels. OAT diagnostic without retuning. Protocol: `GATE0_VALIDATION.md`. | Three-scenario report in `diagnostics/gate0_agrimate/`; documented seasonal baseline; material balance. |
| **G0-H** | 2006–11 wheat hindcast vs Pink Sheet **and** vs Agrimate Fig. 4 / regional tables if author output exists. Report levels, paths, hike ratios, stocks, consumption, trade. | **P8–P11 done:** `hindcast.md` sourced shortfall; `regional.md` named-node vs PSD; `faostat_fb.md` — raw FBSH vendored; labelled reconstruction at `data/food_balances/` (not adopted); A1 left, USDA default. `pulse.md` 8-run 2008 prescribed-Δ (Ukraine/Russia × {0.5,1.0} × {6,12}m) is clean; not Bai's 36; not G2. |
| **G0-P** | Gate 0 note at publication standard (methods, data, hindcast, limits). No substitution, no government game. | **Note written, not accepted.** `diagnostics/gate0_agrimate/methods.md` is the market-section offer. Items 3 and 5 fail. G1 stays blocked. |
| **G1** | Cross-crop substitution (wheat/rice/maize), distinct from Agrimate origin CES. Disabled G1 recovers G0. | Identity test + spillover experiments. No σ* fit to 2008. |
| **G2** | Government restriction game, distinct from supplier oligopoly and from AMIS/E.4. Disabled G2 recovers E.4 Agrimate. | Mechanism tests on the *accepted* G0 host. Train/hold-out if estimated. |

G1 and G2 each need an approved departure record before code
(`GATE0_DEPARTURES.md`, `GATE0_EXTENSION_PLAN.md`). Assistant-generated
ideas and leftover `dynamic_coupled` / `dynamic_policy` code are **not**
approval.

## Hard stops

- Do not implement or retune Gate 1 (`sheaf/dynamic_coupled.py`) or Gate 2
  (`sheaf/dynamic_policy.py`) while any G0-N…G0-P box is open.
- Do not treat legacy `diagnostics/gate0_*_report.md` or the Overleaf
  ask/scarcity deck as evidence about the new host.
- Do not move maize/rice onto the new host as an acceptance target.
- Do not “fix” unforced prices by pinning them to the 2006 mean.
- Dead-end artifacts (legacy red-team scratch, uncommitted Overleaf WIP
  on the old map) stay in `archive/` or uncommitted. Do not resurrect them
  as the market.

## Now (G0-U)

1. **G0-N (done).** Always-feasible supplier plan; reference run solvent.
2. **G0-S (done against retrieved code).** Zenodo 14022004 in hand. Wheat
   C.1 is 27 author names; params follow `AgrimateParams`; p_sto and x_min
   penalty; E.27 and D.1 from author. Unresolved labelled in
   `GATE0_AGRIMATE_BRIEF.md`. Data 10688435 unpacked for Fig. 4 (P7).
3. **G0-U (this).** Three-scenario runner `scripts/run_agrimate_validation.py`.
   Bai/Wada/Puma workflow structure (scenarios, prices+stocks+supply,
   mechanism panels, OAT). Author defaults unchanged (αI=3.2, not Bai's 10).
   G1/G2 recorded as later recovery tests, not implemented.
   First 2003–11 run is in `diagnostics/gate0_agrimate/` (AMIS Δ now binds:
   491 region-steps; harvest vs harvest+AMIS no longer identical). Undisturbed
   still drifts (annual-mean ratio 1.63); Pink-Sheet corr remains negative.
   That is a G0-H score, not a reason to restore L1–L8. G0-U exit is the
   **workflow**, not publication-quality hindcast. **R-science is exhausted.**
   Remaining gaps are labelled (item-3 wander, A7 cannot-set, A1 USDA).
   **S1 implemented** A8 member-sum. **S2 labelled** item 3 at 1.444
   (no sourced D.22; freeze not adopted). **S3** re-scored FBSH vs
   member-sum USDA (China H 1.00; moy 20.1×→33.0×; not adopted).
   **S4** A7 inventory (Egypt not invented). **S5** re-scored Fig. 4 /
   hindcast on the S1 CSVs (hike ×3.71, last/first 1.444, unconverged
   2304/5832). Items 1–3 still fail. G0-P **not accepted**. **T1–T3
   done** (Julia inspect; D.22 labelled not adopted; FAO-since-2005 +
   AgrimateEU28+Egypt arrays labelled not adopted, not C.1). Do not
   start G1. Next paste **stay not-accepted**
   (`GATE0_CONTINUE.md`), not G1, not R8.
4. Single-scenario smoke remains `python scripts/run_agrimate_wheat.py`.
5. **P1 (done).** Step identities on 2006 harvest+AMIS.
6. **P2 (done).** Delivery bug: lagged XI was credited to the *exporter*
   as consumer inflow. T* now routes XI to importers. Stocks/who-eats are
   fixed; world-price 1.63 ratio is unchanged (p_w is on XI, not on who
   receives it). Writeup: `diagnostics/gate0_agrimate/undisturbed.md`.
   Remaining non-periodic xd/xi split is labelled, not pinned.
7. **P3 (done).** β=0.05 / τ_P=0.2 exist in author params and are
   computed in `sales_step!`, but the wheat `two_markets` path pins
   `P_loc=1` in the optimizer and offer prices. Host left unwired
   (`GATE0_DEPARTURES` S3, `GATE0_AGRIMATE_BRIEF` item 6).
8. **P4 (done).** D.30a is on the wheat path (`determine_demands`,
   `ε_d_adjust=false`). Host nested CES matches; A_d=1 recovers D.30.
   Inflow still T*+domestic; author x1=demand is labelled (S4).
9. **P5 (done).** Unconverged = 1743/5832 on harvest+AMIS: feasible,
   residual 0, scipy `success=False` (maxiter + ABNORMAL). Tighter
   maxiter moves prices, but 200 vs 400 disagree as much as 40 vs 400.
   Default `plan_maxiter=40` kept. Writeup: `diagnostics/gate0_agrimate/solver.md`.
10. **P6 (done).** Short harvest+AMIS 2006–08 OAT. αI and low p_sto move
    the 2008 hike; Bai αI=10 raises it and blows pidx_max. εc and σ do not
    move world price (S4). `wheat_params()` unchanged (αI=3.2).
    CSV: `diagnostics/gate0_agrimate/score_sensitivity.csv`.
11. **P7 (done).** Zenodo 10688435 `data.zip` fetched (md5
    `2f3809c66e78b72b3c74971051f89529`). Fig. 4 series scored in
    `diagnostics/gate0_agrimate/fig4.md`. Independent implementation,
    **not a replication**: author baseline last/first=1.004 vs host 1.63
    (P2 unexplained); harvest+AMIS hike ×1.62 author vs ×4.54 host;
    Fig. 4 executable is AgrimateEU28+Egypt, FAO anomalies, α_foreign=3.5,
    ζ=1, N_for=6, git `old-demand-dynamics`. Host `AgrimateParams` unchanged.
12. **P8 (done).** G0-H hindcast note: `diagnostics/gate0_agrimate/hindcast.md`.
    Explicit sourced shortfall vs Agrimate Fig. 4, not a retune. 2006 level
    $65 vs Pink $213; hike ×4.54 vs Agrimate ×1.62 vs Pink ×1.88; seasonal
    max/min ~18× vs Agrimate 1.45× vs Pink 1.07× (Sep 2007 $2.8 vs $342).
    Production corr +0.795 vs USDA. Stock level **1.58×** USDA after P2
    (prompt's ~3× was the echo bug). AMIS adds May 2008, not the 2007
    spike. Bai αI=10 not adopted. `wheat_params()` unchanged.
13. **P9 (done).** Regional USDA: `diagnostics/gate0_agrimate/regional.md`.
    Named exporters + Eastern Africa vs `psd_regional_annual()` 2006–11.
    Single-row nodes match production *means*; China/EA were 0.50× / 0.10×
    because `prepare_wheat` `groupby.mean()`s members (A8, labelled in P9).
    **S1 implemented** member-sum. No xmin/p_sto fit. `wheat_params()` unchanged.
14. **P10 (done).** FAOSTAT Food Balance arrays are **not** in
    `data/faostat_network/` (the path named in the prompt: E0 trade only).
    FoodTradeNetwork P0/R0 are 2015–21 averages, not 2006–11 FB. A1 left.
    USDA stays default. R6 obtain later vendored raw FBSH under
    `data/faostat_fb/`; author cleaned still absent; still no parallel
    `WheatData`. Writeup: `diagnostics/gate0_agrimate/faostat_fb.md`.
15. **P11 (done).** Prescribed-Δ 8-run on harvest-anomaly wheat, 2008:
    Ukraine and Russia × {0.5, 1.0} × {6, 12} months vs harvest-only.
    `restriction_pulse` (AMIS-style Δ, not a government best-response).
    Slice is **clean**: failed=0, production identical, Δ on one exporter,
    Δ=1.0/12m zeros that exporter's XI; Δ=0.5/12m halves it. 6-month
    Jan–Jun pulses miss NH harvest (Jul–Sep). World price 0.99–1.01×
    harvest-only. Not expanded to Bai's 36-run 2020 grid. Not G2.
    `wheat_params()` unchanged. Writeup:
    `diagnostics/gate0_agrimate/pulse.md`.
16. **P12 (done).** G0-P methods note: `diagnostics/gate0_agrimate/methods.md`.
    Independent Agrimate copy; not a Fig. 4 replication; no substitution;
    no government game. **Recommend reject** as the SHEAF market section
    (item 3 undisturbed 1.63 vs author 1.004; item 5 hike ×4.54 vs
    Agrimate ×1.62 vs Pink ×1.88). `wheat_params()` unchanged. G1/G2
    stay blocked until a later G0-P acceptance. Do not start G1 from
    this note.
17. **R1 (done).** Full-mode red team + data cookbook:
    `diagnostics/GATE0_REDTEAM.md`, `diagnostics/GATE0_DATA.md`.
    Items 3 and 5 still fail; tests lock honesty not Fig. 4 match;
    fetch does not download Zenodo or FAO FB. Adaptive queue:
    `GATE0_REPRO_PROMPTS.md` (exhausted). Living next-paste:
    `GATE0_REPRO_DISPATCH.md` (**S3**; `GATE0_NEXT_PROMPTS.md`).
18. **R2 (done).** `fig4_experiment_params()` is αI=3.5, ζ=1, N_for=6.
    FAO/EU28/start-2000 cannot-set. Short 2006–08 harvest+AMIS: moy
    26.8×→13.3× (drop ≥2); hike ×2.31→×2.22 (barely). Unconverged
    611→553 / 1944, failed=0. `wheat_params()` unchanged.
    Writeup: `diagnostics/gate0_agrimate/fig4_config.md`.
19. **R3–R7, R9, R10 (done).** World-price identity; item-3 characterisation
    (`qoth_freeze` 1.019, not adopted); x1=demand default off; raw FBSH
    vendored, parallel WheatData not adopted; A8 mean-vs-sum labelled
    (China 0.50× / EA 0.10×, USDA stocks). **S1 implemented** member-sum.
    Fig. 4 knobs scored, not adopted. G0-P still **not accepted**.
20. **R-science exhausted.** First-match table has nowhere to go without
    breaking hard stops (R11 forbidden; freeze not sourced; FAO/EU28
    cannot-set; labelled-off experiments did not move live items 1–3).
    Remaining gaps after S3: A7 cannot-set (A1 left USDA; item 3 labelled
    1.444; FBSH parallel not adopted).
21. **S1 (done).** `prepare_wheat` 2007–09 baseline is member-sum then
    mean (same as `psd_regional_annual()`). USDA `ending_stocks` only.
    Never FAO ΔS. China H 56.4→112.7, Eastern Africa 0.33→3.31, USA
    1.00. `wheat_params()` stay 14022004. Next paste **S2**.
22. **S2 (done).** Member-sum host undisturbed last/first **1.444** vs
    author **1.004** (pre-S1 1.630). Still >1.1. No sourced D.22
    variant (0 `*.jl` in tree). `freeze_q_oth` stays diagnostic,
    default off, not a `wheat_params()` field. Not adopted. Not a pin.
    Writeup: `diagnostics/gate0_agrimate/item3.md`. Next paste **S3**.
23. **S3 (done).** Re-scored raw FBSH H/C vs S1 member-sum USDA on
    2006–08 harvest+AMIS. China H 112.7 vs 112.3 (ratio 1.00); EA 0.99.
    moy 20.1× → 33.0× (worsened). Items 1–3 did not improve. Psi USDA
    (`ending_stocks`); 5074 is ΔS, not S. Author cleaned FB was still
    absent at S3. **Not adopted.** USDA stays `prepare_wheat` default.
    Writeup: `diagnostics/gate0_agrimate/s3_fbsh.md`. Next paste **S4**.
24. **Author FB reconstruction.** Labelled host
    `data/food_balances/wheat_food_balance_fao.csv` from sourced
    `impute_food_balance_fao` (FBSH 2006–11 + QCL + TCL). Not
    bit-identical to Kuhla's unpublished local CSV. Not rebalanced.
    **Not adopted** as `prepare_wheat`. Egypt remains a FAOSTAT area
    row, not a C.1 node. Writeup: `diagnostics/gate0_agrimate/author_fb.md`.
    Next paste still **S4** (EU28+Egypt / start-2000 still cannot-set).
25. **S4 (done).** A7 cannot-set inventory. Fig. 4 knobs already on
    `fig4_experiment_params()`. Host reconstruction of
    `wheat_food_balance_fao.csv` labelled, **not adopted**. Parallel
    AgrimateEU28+Egypt name list labelled from NetCDF `region_list`
    (`s4_a7.md`); **not** C.1. Egypt not invented. `wheat_params()`
    stay αI=3.2. Still cannot-set: start 2000, FAO-since-2005 inputs,
    Julia, bit-identical author FB. Next paste **S5**.
26. **S5 (done).** Re-scored hike, quiet-year, moy max/min, and
    undisturbed last/first from the S1 three-scenario CSVs against
    `author_fig4/` and Pink Sheet. Not R11 (NLP not re-run).
    harvest+AMIS hike ×3.71 vs author ×1.62 vs Pink ×1.88; 2006 mean
    $81.5 vs Pink $213.5; last/first 1.444 vs author 1.004;
    unconverged 2304/5832. Items 1–3 did **not** newly pass. G0-P
    stays **not accepted**. `wheat_params()` unchanged. Do not start
    G1. Next paste **stay not-accepted** (not S6).
27. **S6 (done).** G0-P methods v2 from S1–S5 CSVs. Still **not
    accepted** (last/first 1.444; hike ×3.71; unconverged 2304/5832).
    `wheat_params()` unchanged. Do not start G1. Continuation:
    `GATE0_CONTINUE.md` **T1** (obtain-or-leave 14022004 Julia).
28. **T1 (done).** Obtained GitLab paper repo
    (`https://gitlab.pik-potsdam.de/agrimate/agrimate`,
    `f2de9655`, 41 `*.jl`) and inspected Zenodo 14022004
    `agrimate-equal-sales-penalty` zip (`79951111`, 32 `*.jl`) under
    `/tmp`. **Not copied** into `sheaf/agrimate/` (still 0 `*.jl`).
    Wheat D.22 **differs** (author: horizon vector + shift of planned
    foreign sales; host: scalar EMA of realized XI; weight 1/12
    matches). Solver **differs** (NLopt LD_SLSQP vs L-BFGS-B). No
    freeze in author. `wheat_params()` unchanged. Do not start G1.
    Next paste **T2**.
29. **T2 (done).** Labelled sourced D.22 / solver delta (equation,
    file, line) in `t2_delta.md`. Author wheat: horizon vector+shift of
    planned `optimal_sales_foreign[3:end]` (`producer.jl` 452–464);
    NLopt `:LD_SLSQP` with current x1 fixed (`producer_optimization.jl`
    68–72, 280). Host: scalar EMA of realized XI (`model.py` 347–349);
    L-BFGS-B (`optimize.py` 256–258). Weight 1/12 matches. **No freeze**
    in author. **Not implemented.** `wheat_params()` unchanged. Do not
    start G1. Next paste **T3**.
30. **T3 (done).** Obtained compact FAO-since-2005 annual relative
    anomalies (2000–11, years before 2005 zeroed) and the sourced
    AgrimateEU28 YAML + Egypt=EGY extra ISO map from GitLab
    (`t3_fig4_inputs/`; daily 4.7 MB files not vendored; 0 `*.jl`
    copied). **Not adopted.** Egypt not invented on C.1. USDA stays
    `prepare_wheat`. `wheat_params()` unchanged. GitLab FB left (md5
    differs from the host reconstruction). Still cannot-set: start
    2000 live window, old-demand-dynamics, FAO as WheatData. Do not
    start G1. Next paste **stay not-accepted**.
31. **Stay not-accepted (this).** T-queue exhausted. G0-P **still not
    accepted** (last/first 1.444; hike ×3.71; unconverged 2304/5832).
    T1–T3 labelled, not adopted. Methods note reaffirmed. Do not
    start G1. Next paste **stay not-accepted**.
32. **D.22 (done).** Implemented sourced wheat D.22 as independent
    Python (`sheaf/agrimate/d22.py`): horizon vector + shift of
    *planned* foreign sales. Not a freeze. Not a pin. Not a Julia
    copy. `wheat_params()` unchanged. S1 three-scenario CSVs not
    clobbered. Last/first **0.772** vs author **1.004** (S1 snapshot
    1.444). Two-sided repeating still fails; quiet-year USD ~$456 vs
    S1 $46. Unconverged 1986/5832. Next paste **solver**.
33. **Solver (this).** Independent Python of sourced 14022004 wheat
    programme: current x1 locked to last CES requests (domestic
    first, ι·X_avg per-step floor); scipy SLSQP on remaining
    fractions. Not NLopt/Julia. Not a freeze. Not a pin. Not an αI
    retune. `plan_maxiter` stays 40. R5 `x1_from_demand` stays
    default off. S1 three-scenario CSVs not clobbered. Last/first
    **0.812** vs author **1.004** (D.22 0.772; S1 1.444). Two-sided
    [1/1.1, 1.1] still fails; quiet-year USD ~$305 vs S1 $46.
    Unconverged 1091/5832; failed 0. Next paste **leave labelled**
    (exact Fig. 4 later). Do not start G1.

Reference command:

```bash
python -m pytest tests/agrimate -q
PYTHONPATH=. python scripts/run_agrimate_validation.py
```

Solver smoke (one harvest+AMIS path):

```bash
PYTHONPATH=. python scripts/run_agrimate_wheat.py
```

Legacy (labelled, not the bar):

```bash
python scripts/score_legacy_crop.py --crop wheat
```

## Prior cycle (legacy ask/scarcity host) — closed

The 2026-08 characterization (A1–A5, red-team, Potsdam note) documented the
**old** sequential map. It is useful as a record of why that map is not
Agrimate. It is not a Gate 0 publication path.

- Artifacts: `diagnostics/gate0_prep/`, `diagnostics/redteam/`,
  `archive/legacy-gate0/`, `overleaf/gate0_discussion/`
- Code: `sheaf/legacy/`, `sheaf/dynamic_crop.py` (Gate 1 still imports this
  copy; do not extend it)

Parked, not next:

| Layer | Status |
|---|---|
| Gate 1 isoelastic substitution | Blocked until G0-P |
| Gate 2 Headey-clock actions | Blocked until G0-P, then G1 identity |
| Annual SPE `sheaf.annual` | Parked |
| `dynamic_grains.py` | Paused |
